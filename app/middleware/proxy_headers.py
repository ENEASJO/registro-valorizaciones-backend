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
    Simplified middleware to handle proxy headers in Cloud Run
    
    This middleware:
    1. Detects X-Forwarded-Proto header and updates request scheme
    2. Prevents HTTPS redirect loops in proxy environments
    """
    
    def __init__(self, app):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next):
        """
        Process request and handle proxy headers
        """
        try:
            # Only handle X-Forwarded-Proto for HTTPS redirects
            forwarded_proto = request.headers.get("x-forwarded-proto", "").lower()
            
            # Update request scheme based on X-Forwarded-Proto
            if forwarded_proto == "https":
                request.scope["scheme"] = "https"
            
            # Process the request
            response = await call_next(request)
            
            return response
            
        except Exception as e:
            # If middleware fails, continue without proxy handling
            print(f"⚠️ Proxy headers middleware error: {e}")
            return await call_next(request)


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