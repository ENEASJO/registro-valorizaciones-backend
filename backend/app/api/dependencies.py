"""
Dependencias de FastAPI
"""
from typing import Optional
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)
security = HTTPBearer(auto_error=False)


async def get_current_settings():
    """Dependency para obtener configuración actual"""
    return settings


async def validate_api_key(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> bool:
    """
    Validar API key (para futuro uso)
    
    Args:
        credentials: Credenciales de autorización
        
    Returns:
        bool: True si es válido
        
    Raises:
        HTTPException: Si la API key no es válida
    """
    # Por ahora no hay validación de API key
    # En el futuro se puede implementar autenticación aquí
    return True


async def rate_limit_check(request: Request) -> bool:
    """
    Verificar límite de velocidad (rate limiting)
    
    Args:
        request: Request HTTP
        
    Returns:
        bool: True si está dentro del límite
        
    Raises:
        HTTPException: Si excede el límite
    """
    # Por ahora no hay rate limiting implementado
    # En el futuro se puede usar Redis o memoria para tracking
    client_ip = request.client.host
    logger.debug(f"Rate limit check for IP: {client_ip}")
    
    return True


async def log_request(request: Request) -> None:
    """
    Loggear información de la request
    
    Args:
        request: Request HTTP
    """
    client_ip = request.client.host
    method = request.method
    url = str(request.url)
    user_agent = request.headers.get("user-agent", "Unknown")
    
    logger.info(f"Request: {method} {url} from {client_ip} - {user_agent}")


async def validate_content_type(request: Request) -> bool:
    """
    Validar content type para requests POST/PUT
    
    Args:
        request: Request HTTP
        
    Returns:
        bool: True si es válido
        
    Raises:
        HTTPException: Si el content type no es válido
    """
    if request.method in ["POST", "PUT", "PATCH"]:
        content_type = request.headers.get("content-type", "")
        
        if not content_type.startswith("application/json"):
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail="Content-Type debe ser application/json"
            )
    
    return True