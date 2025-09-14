"""
Configuración de seguridad optimizada para la API de notificaciones WhatsApp
Implementa múltiples capas de seguridad para producción
"""

import secrets
import hashlib
import hmac
import time
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from urllib.parse import urlparse

from fastapi import HTTPException, Request, Response, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.sessions import SessionMiddleware

import jwt
from passlib.context import CryptContext
from pydantic import BaseSettings

# =====================================================================
# CONFIGURACIÓN DE SEGURIDAD
# =====================================================================

class SecuritySettings(BaseSettings):
    """Configuración de seguridad centralizada"""
    
    # JWT Configuration
    JWT_SECRET_KEY: str = secrets.token_urlsafe(32)
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_EXPIRE_DAYS: int = 7
    
    # API Keys Configuration
    API_KEY_LENGTH: int = 32
    API_KEY_PREFIX: str = "wn_"  # WhatsApp Notifications prefix
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REDIS_URL: str = "redis://localhost:6379"
    
    # CORS Configuration
    CORS_ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001", 
        "https://valoraciones.empresa.com",
        "https://dashboard.empresa.com"
    ]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOWED_METHODS: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    CORS_ALLOWED_HEADERS: List[str] = [
        "Accept",
        "Accept-Language", 
        "Content-Language",
        "Content-Type",
        "Authorization",
        "X-API-Key",
        "X-Request-ID",
        "X-Forwarded-For"
    ]
    
    # Trusted Hosts
    TRUSTED_HOSTS: List[str] = [
        "localhost",
        "127.0.0.1",
        "valoraciones.empresa.com",
        "api.valoraciones.empresa.com"
    ]
    
    # Security Headers
    SECURITY_HEADERS_ENABLED: bool = True
    HSTS_MAX_AGE: int = 31536000  # 1 year
    
    # Content Security Policy
    CSP_DEFAULT_SRC: str = "'self'"
    CSP_SCRIPT_SRC: str = "'self' 'unsafe-inline'"
    CSP_STYLE_SRC: str = "'self' 'unsafe-inline'"
    CSP_IMG_SRC: str = "'self' data: https:"
    
    # Webhook Security
    WEBHOOK_SECRET_TOKEN: str = secrets.token_urlsafe(32)
    WEBHOOK_VERIFY_SSL: bool = True
    WEBHOOK_TIMEOUT_SECONDS: int = 30
    
    # Session Security
    SESSION_SECRET_KEY: str = secrets.token_urlsafe(32)
    SESSION_COOKIE_SECURE: bool = True
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SAMESITE: str = "strict"
    
    class Config:
        env_prefix = "SECURITY_"

# Instancia global de configuración
security_settings = SecuritySettings()

# =====================================================================
# UTILIDADES CRIPTOGRÁFICAS
# =====================================================================

# Contexto para hashing de passwords
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hash seguro de password"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verificar password contra hash"""
    return pwd_context.verify(plain_password, hashed_password)

def generate_api_key() -> str:
    """Generar API key segura"""
    random_part = secrets.token_urlsafe(security_settings.API_KEY_LENGTH)
    return f"{security_settings.API_KEY_PREFIX}{random_part}"

def hash_api_key(api_key: str) -> str:
    """Hash de API key para almacenamiento seguro"""
    return hashlib.sha256(api_key.encode()).hexdigest()

def verify_api_key(api_key: str, stored_hash: str) -> bool:
    """Verificar API key contra hash almacenado"""
    return hmac.compare_digest(hash_api_key(api_key), stored_hash)

# =====================================================================
# MANEJO DE JWT TOKENS
# =====================================================================

class JWTHandler:
    """Manejador de tokens JWT optimizado"""
    
    def __init__(self):
        self.secret_key = security_settings.JWT_SECRET_KEY
        self.algorithm = security_settings.JWT_ALGORITHM
        self.expire_minutes = security_settings.JWT_EXPIRE_MINUTES
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Crear token de acceso JWT"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.expire_minutes)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        })
        
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    def create_refresh_token(self, data: dict) -> str:
        """Crear token de refresh JWT"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=security_settings.JWT_REFRESH_EXPIRE_DAYS)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        })
        
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    def decode_token(self, token: str) -> dict:
        """Decodificar y validar token JWT"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Verificar que no haya expirado
            if payload.get("exp", 0) < time.time():
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token expirado"
                )
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expirado"
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido"
            )
    
    def refresh_access_token(self, refresh_token: str) -> str:
        """Renovar token de acceso usando refresh token"""
        payload = self.decode_token(refresh_token)
        
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token de refresh inválido"
            )
        
        # Crear nuevo access token
        new_payload = {
            "sub": payload.get("sub"),
            "user_id": payload.get("user_id"),
            "permissions": payload.get("permissions", [])
        }
        
        return self.create_access_token(new_payload)

# Instancia global del handler JWT
jwt_handler = JWTHandler()

# =====================================================================
# MIDDLEWARE DE SEGURIDAD PERSONALIZADO
# =====================================================================

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware para agregar headers de seguridad"""
    
    def __init__(self, app):
        super().__init__(app)
        self.security_headers = self._get_security_headers()
    
    def _get_security_headers(self) -> Dict[str, str]:
        """Generar headers de seguridad estándar"""
        csp_policy = (
            f"default-src {security_settings.CSP_DEFAULT_SRC}; "
            f"script-src {security_settings.CSP_SCRIPT_SRC}; "
            f"style-src {security_settings.CSP_STYLE_SRC}; "
            f"img-src {security_settings.CSP_IMG_SRC}; "
            f"object-src 'none'; "
            f"base-uri 'self'; "
            f"form-action 'self'; "
            f"frame-ancestors 'none';"
        )
        
        return {
            # Prevenir XSS
            "X-XSS-Protection": "1; mode=block",
            
            # Prevenir clickjacking
            "X-Frame-Options": "DENY",
            
            # Prevenir MIME type sniffing
            "X-Content-Type-Options": "nosniff",
            
            # Content Security Policy
            "Content-Security-Policy": csp_policy,
            
            # Referrer Policy
            "Referrer-Policy": "strict-origin-when-cross-origin",
            
            # HSTS (solo en HTTPS)
            "Strict-Transport-Security": f"max-age={security_settings.HSTS_MAX_AGE}; includeSubDomains; preload",
            
            # Permissions Policy
            "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
            
            # Server header (ocultar información)
            "Server": "API-Server/1.0"
        }
    
    async def dispatch(self, request: Request, call_next):
        """Procesar request y agregar headers de seguridad"""
        response = await call_next(request)
        
        if security_settings.SECURITY_HEADERS_ENABLED:
            # Agregar headers de seguridad
            for header, value in self.security_headers.items():
                # Solo agregar HSTS en HTTPS
                if header == "Strict-Transport-Security" and request.url.scheme != "https":
                    continue
                response.headers[header] = value
            
            # Headers específicos por tipo de respuesta
            if response.headers.get("content-type", "").startswith("application/json"):
                response.headers["X-Content-Type-Options"] = "nosniff"
        
        return response

class IPWhitelistMiddleware(BaseHTTPMiddleware):
    """Middleware para control de acceso por IP"""
    
    def __init__(self, app, whitelisted_ips: List[str] = None, enabled: bool = False):
        super().__init__(app)
        self.whitelisted_ips = set(whitelisted_ips or [])
        self.enabled = enabled
    
    def _get_client_ip(self, request: Request) -> str:
        """Obtener IP real del cliente considerando proxies"""
        # Headers de proxy más comunes
        for header in ["X-Forwarded-For", "X-Real-IP", "X-Client-IP"]:
            if header in request.headers:
                ip = request.headers[header].split(',')[0].strip()
                if ip and ip != "unknown":
                    return ip
        
        return request.client.host if request.client else "unknown"
    
    async def dispatch(self, request: Request, call_next):
        """Verificar IP contra whitelist"""
        if not self.enabled:
            return await call_next(request)
        
        client_ip = self._get_client_ip(request)
        
        # Permitir IPs locales en desarrollo
        local_ips = {"127.0.0.1", "localhost", "::1"}
        if client_ip in local_ips:
            return await call_next(request)
        
        # Verificar whitelist
        if self.whitelisted_ips and client_ip not in self.whitelisted_ips:
            return Response(
                content="Access denied: IP not whitelisted",
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        return await call_next(request)

# =====================================================================
# VALIDADORES DE WEBHOOK
# =====================================================================

class WebhookValidator:
    """Validador de webhooks de WhatsApp"""
    
    def __init__(self, secret_token: str = None):
        self.secret_token = secret_token or security_settings.WEBHOOK_SECRET_TOKEN
    
    def validate_signature(self, payload: bytes, signature: str) -> bool:
        """Validar signature del webhook"""
        if not signature:
            return False
        
        # WhatsApp usa HMAC-SHA256
        expected_signature = hmac.new(
            self.secret_token.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        # Comparación segura contra timing attacks
        return hmac.compare_digest(f"sha256={expected_signature}", signature)
    
    def validate_timestamp(self, timestamp: str, tolerance_seconds: int = 300) -> bool:
        """Validar timestamp del webhook (prevenir replay attacks)"""
        try:
            webhook_time = int(timestamp)
            current_time = int(time.time())
            
            return abs(current_time - webhook_time) <= tolerance_seconds
        except (ValueError, TypeError):
            return False

# =====================================================================
# AUTENTICACIÓN Y AUTORIZACIÓN
# =====================================================================

class APIKeyValidator:
    """Validador de API Keys"""
    
    def __init__(self):
        # En producción, esto vendría de base de datos
        self.valid_api_keys = {
            "wn_development_key_12345": {
                "user_id": "dev_user",
                "permissions": ["read", "write"],
                "rate_limit": 1000
            }
        }
    
    def validate_api_key(self, api_key: str) -> Dict[str, Any]:
        """Validar API key y retornar información del usuario"""
        if api_key in self.valid_api_keys:
            return self.valid_api_keys[api_key]
        return None

# Security scheme para FastAPI
security_scheme = HTTPBearer(auto_error=False)

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme)
) -> Dict[str, Any]:
    """Obtener usuario actual desde token JWT o API Key"""
    
    if not credentials:
        return {
            "user_id": "anonymous",
            "client_type": "anonymous",
            "permissions": ["read"]
        }
    
    token = credentials.credentials
    
    # Intentar como JWT token primero
    try:
        payload = jwt_handler.decode_token(token)
        return {
            "user_id": payload.get("user_id", "unknown"),
            "client_type": "jwt",
            "permissions": payload.get("permissions", ["read"]),
            "token_type": payload.get("type", "access")
        }
    except HTTPException:
        pass
    
    # Intentar como API Key
    api_validator = APIKeyValidator()
    api_key_info = api_validator.validate_api_key(token)
    
    if api_key_info:
        return {
            "user_id": api_key_info["user_id"],
            "client_type": "api_key",
            "permissions": api_key_info["permissions"],
            "rate_limit": api_key_info.get("rate_limit", 100)
        }
    
    # Token inválido
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

def require_permissions(required_permissions: List[str]):
    """Decorador para requerir permisos específicos"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Obtener user_context de kwargs
            user_context = kwargs.get('user_context', {})
            user_permissions = user_context.get('permissions', [])
            
            # Verificar permisos
            if not any(perm in user_permissions for perm in required_permissions):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions. Required: {required_permissions}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# =====================================================================
# CONFIGURACIÓN DE MIDDLEWARE PARA FASTAPI
# =====================================================================

def setup_security_middleware(app):
    """Configurar todos los middleware de seguridad"""
    
    # Session middleware
    app.add_middleware(
        SessionMiddleware,
        secret_key=security_settings.SESSION_SECRET_KEY,
        https_only=security_settings.SESSION_COOKIE_SECURE,
        same_site=security_settings.SESSION_COOKIE_SAMESITE
    )
    
    # Security headers middleware
    app.add_middleware(SecurityHeadersMiddleware)
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=security_settings.CORS_ALLOWED_ORIGINS,
        allow_credentials=security_settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=security_settings.CORS_ALLOWED_METHODS,
        allow_headers=security_settings.CORS_ALLOWED_HEADERS,
        expose_headers=["X-Request-ID", "X-RateLimit-Remaining", "X-Total-Count"]
    )
    
    # Trusted hosts middleware
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=security_settings.TRUSTED_HOSTS
    )
    
    # IP whitelist middleware (disabled by default)
    app.add_middleware(
        IPWhitelistMiddleware,
        whitelisted_ips=[],
        enabled=False
    )

# =====================================================================
# UTILIDADES DE SEGURIDAD ADICIONALES
# =====================================================================

def sanitize_input(input_str: str) -> str:
    """Sanitizar input de usuario"""
    if not input_str:
        return ""
    
    # Remover caracteres peligrosos
    dangerous_chars = ['<', '>', '"', "'", '&', '\\', '/', ';']
    for char in dangerous_chars:
        input_str = input_str.replace(char, '')
    
    # Limitar longitud
    return input_str[:1000].strip()

def validate_phone_number_security(phone: str) -> Tuple[bool, str]:
    """Validación de seguridad para números telefónicos"""
    if not phone:
        return False, "Número telefónico requerido"
    
    # Remover caracteres no numéricos excepto +
    clean_phone = ''.join(c for c in phone if c.isdigit() or c == '+')
    
    # Validaciones básicas
    if len(clean_phone) < 8 or len(clean_phone) > 15:
        return False, "Longitud de número telefónico inválida"
    
    if clean_phone.startswith('+') and len(clean_phone) < 10:
        return False, "Número internacional inválido"
    
    return True, clean_phone

def log_security_event(event_type: str, details: Dict[str, Any], request: Request = None):
    """Log de eventos de seguridad"""
    import logging
    
    security_logger = logging.getLogger("security")
    
    log_data = {
        "event_type": event_type,
        "timestamp": datetime.utcnow().isoformat(),
        "details": details
    }
    
    if request:
        log_data.update({
            "ip": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("User-Agent", ""),
            "endpoint": str(request.url.path),
            "method": request.method
        })
    
    security_logger.warning(f"Security event: {event_type}", extra=log_data)