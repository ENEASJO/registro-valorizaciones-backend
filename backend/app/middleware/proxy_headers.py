"""
Middleware to handle proxy headers in Cloud Run environment
Fixes HTTPS redirect issues by properly handling X-Forwarded headers
"""

import os
from typing import Dict, Any
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import RedirectResponse
import urllib.parse


class ProxyHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle proxy headers and fix scheme issues in Cloud Run
    
    This middleware:
    1. Detects X-Forwarded-Proto header and updates request.url.scheme
    2. Handles X-Forwarded-Host and X-Forwarded-Port
    3. Prevents HTTPS redirect loops in proxy environments
    """
    
    def __init__(self, app):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next):
        """
        Process request and handle proxy headers
        """
        # Store original headers for debugging
        original_scheme = request.url.scheme
        forwarded_proto = request.headers.get("x-forwarded-proto", "").lower()
        forwarded_host = request.headers.get("x-forwarded-host", "")
        forwarded_port = request.headers.get("x-forwarded-port", "")
        
        # Update request scheme based on X-Forwarded-Proto
        if forwarded_proto in ("https", "http"):
            # This is the key fix - update the perceived scheme
            request.scope["scheme"] = forwarded_proto
        
        # Update host if forwarded
        if forwarded_host:
            # Parse the original URL components
            parsed_url = urllib.parse.urlparse(str(request.url))
            
            # Reconstruct the URL with the forwarded host
            new_netloc = forwarded_host
            if forwarded_port and forwarded_port != ("443" if forwarded_proto == "https" else "80"):
                new_netloc += f":{forwarded_port}"
            
            # Update the request URL components
            new_url = parsed_url._replace(
                scheme=forwarded_proto,
                netloc=new_netloc
            )
            
            # Update the request scope
            request.scope["path"] = new_url.path
            request.scope["query_string"] = new_url.query.encode()
            request.scope["headers"] = [
                (k.encode(), v.encode()) 
                for k, v in request.headers.items()
                if k.lower() not in ["host", "x-forwarded-host", "x-forwarded-port", "x-forwarded-proto"]
            ] + [
                (b"host", forwarded_host.encode()),
                (b"x-forwarded-host", forwarded_host.encode()),
                (b"x-forwarded-port", forwarded_port.encode()),
                (b"x-forwarded-proto", forwarded_proto.encode()),
            ]
        
        # Add debugging headers (remove in production)
        request.headers["x-original-scheme"] = original_scheme
        request.headers["x-detected-scheme"] = forwarded_proto or original_scheme
        
        # Process the request
        response = await call_next(request)
        
        # Add header to indicate proxy handling (solo en desarrollo para no interferir con CORS)
        if not os.environ.get('PRODUCTION', 'false').lower() == 'true':
            response.headers["x-proxy-handled"] = "true"
        
        return response


class HTTPSRedirectMiddleware(BaseHTTPMiddleware):
    """
    Middleware to force HTTPS redirects (disabled by default in Cloud Run)
    
    This middleware is only needed if you want to force HTTPS in environments
    where you have direct SSL termination control.
    """
    
    def __init__(self, app, enabled: bool = False):
        super().__init__(app)
        self.enabled = enabled
    
    async def dispatch(self, request: Request, call_next):
        """
        Only redirect if HTTPS is required and we're not behind a proxy
        """
        if not self.enabled:
            return await call_next(request)
        
        # Don't redirect if we're behind a proxy (Cloud Run handles this)
        if request.headers.get("x-forwarded-proto") == "https":
            return await call_next(request)
        
        # Only redirect if the request is HTTP and not from a proxy
        if request.url.scheme == "http" and not request.headers.get("x-forwarded-for"):
            # Redirect to HTTPS
            https_url = request.url.replace(scheme="https")
            return RedirectResponse(url=str(https_url), status_code=307)
        
        return await call_next(request)