"""
Middleware de Rate Limiting para la API de notificaciones
Implementa diferentes estrategias de rate limiting por endpoint y cliente
"""

import time
import json
import asyncio
from typing import Dict, Optional, Tuple, Any
from functools import wraps
from datetime import datetime, timedelta

from fastapi import HTTPException, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import redis.asyncio as redis
from redis.exceptions import RedisError

from app.core.config import settings
from app.api.schemas.notifications import ErrorResponse

# =====================================================================
# CONFIGURACIÓN DE RATE LIMITING
# =====================================================================

class RateLimitConfig:
    """Configuración de rate limiting por endpoint"""
    
    # Rate limits por endpoint (requests por minuto)
    ENDPOINT_LIMITS = {
        # Endpoints de consulta - más permisivos
        "GET:/api/notifications": 100,
        "GET:/api/notifications/metrics": 60,
        "GET:/api/notifications/metrics/daily": 60,
        "GET:/api/notifications/contacts": 80,
        "GET:/api/notifications/templates": 80,
        
        # Endpoints de escritura - más restrictivos
        "POST:/api/notifications": 30,
        "PUT:/api/notifications/*/status": 50,
        "POST:/api/notifications/test": 10,
        "POST:/api/notifications/process-pending": 5,
        "POST:/api/notifications/bulk": 5,
        
        # Endpoints administrativos - muy restrictivos
        "POST:/api/notifications/scheduler/calculate-metrics": 2,
        
        # Webhook - sin límite (manejado por WhatsApp)
        "GET:/api/notifications/webhook": 1000,
        "POST:/api/notifications/webhook": 1000,
    }
    
    # Rate limits globales por cliente
    GLOBAL_LIMITS = {
        "requests_per_minute": 200,
        "requests_per_hour": 10000,
        "requests_per_day": 100000
    }
    
    # Burst limits (ráfagas cortas)
    BURST_LIMITS = {
        "requests_per_second": 20,
        "window_seconds": 1
    }

class RedisRateLimiter:
    """Rate limiter basado en Redis con múltiples estrategias"""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client
        self.local_cache = {}  # Fallback cuando Redis no está disponible
        self.cache_cleanup_interval = 300  # 5 minutos
        self.last_cleanup = time.time()
    
    async def init_redis(self) -> Optional[redis.Redis]:
        """Inicializar conexión a Redis"""
        try:
            if not self.redis_client:
                self.redis_client = redis.from_url(
                    getattr(settings, 'REDIS_URL', 'redis://localhost:6379'),
                    decode_responses=True,
                    socket_timeout=1,
                    socket_connect_timeout=1
                )
                # Test connection
                await self.redis_client.ping()
            return self.redis_client
        except Exception:
            return None
    
    async def is_rate_limited(
        self, 
        client_id: str, 
        endpoint: str, 
        method: str,
        limit: int,
        window_seconds: int = 60
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Verificar si el cliente está rate limited
        
        Returns:
            (is_limited, metadata)
        """
        key = f"rate_limit:{client_id}:{method}:{endpoint}"
        current_time = int(time.time())
        window_start = current_time - window_seconds
        
        try:
            redis_client = await self.init_redis()
            
            if redis_client:
                return await self._redis_rate_limit(
                    redis_client, key, current_time, window_start, limit, window_seconds
                )
            else:
                return await self._local_rate_limit(
                    key, current_time, window_start, limit, window_seconds
                )
                
        except RedisError:
            # Fallback a cache local si Redis falla
            return await self._local_rate_limit(
                key, current_time, window_start, limit, window_seconds
            )
    
    async def _redis_rate_limit(
        self, 
        redis_client: redis.Redis,
        key: str,
        current_time: int,
        window_start: int,
        limit: int,
        window_seconds: int
    ) -> Tuple[bool, Dict[str, Any]]:
        """Rate limiting usando Redis con sliding window"""
        
        # Usar pipeline para atomicidad
        pipe = redis_client.pipeline()
        
        # Limpiar requests antiguos
        pipe.zremrangebyscore(key, 0, window_start)
        
        # Contar requests actuales
        pipe.zcard(key)
        
        # Agregar request actual
        pipe.zadd(key, {str(current_time): current_time})
        
        # Establecer TTL
        pipe.expire(key, window_seconds)
        
        results = await pipe.execute()
        current_count = results[1] + 1  # +1 por la request actual
        
        # Calcular metadata
        reset_time = current_time + window_seconds
        remaining = max(0, limit - current_count)
        
        metadata = {
            "limit": limit,
            "remaining": remaining,
            "reset_time": reset_time,
            "window_seconds": window_seconds,
            "current_count": current_count
        }
        
        return current_count > limit, metadata
    
    async def _local_rate_limit(
        self,
        key: str,
        current_time: int,
        window_start: int,
        limit: int,
        window_seconds: int
    ) -> Tuple[bool, Dict[str, Any]]:
        """Rate limiting usando cache local (fallback)"""
        
        # Cleanup periódico
        if current_time - self.last_cleanup > self.cache_cleanup_interval:
            await self._cleanup_local_cache(current_time)
            self.last_cleanup = current_time
        
        # Inicializar entrada si no existe
        if key not in self.local_cache:
            self.local_cache[key] = []
        
        # Limpiar requests antiguos
        self.local_cache[key] = [
            ts for ts in self.local_cache[key] if ts > window_start
        ]
        
        # Agregar request actual
        self.local_cache[key].append(current_time)
        
        current_count = len(self.local_cache[key])
        reset_time = current_time + window_seconds
        remaining = max(0, limit - current_count)
        
        metadata = {
            "limit": limit,
            "remaining": remaining,
            "reset_time": reset_time,
            "window_seconds": window_seconds,
            "current_count": current_count
        }
        
        return current_count > limit, metadata
    
    async def _cleanup_local_cache(self, current_time: int):
        """Limpiar cache local de entradas expiradas"""
        cutoff_time = current_time - 3600  # 1 hora atrás
        
        to_remove = []
        for key in self.local_cache:
            self.local_cache[key] = [
                ts for ts in self.local_cache[key] if ts > cutoff_time
            ]
            if not self.local_cache[key]:
                to_remove.append(key)
        
        for key in to_remove:
            del self.local_cache[key]

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware de rate limiting para FastAPI"""
    
    def __init__(self, app, redis_client: Optional[redis.Redis] = None):
        super().__init__(app)
        self.limiter = RedisRateLimiter(redis_client)
        self.config = RateLimitConfig()
    
    def _get_client_id(self, request: Request) -> str:
        """Obtener identificador único del cliente"""
        # Priorizar header de autenticación si existe
        auth_header = request.headers.get("Authorization")
        if auth_header:
            return f"auth_{hash(auth_header)}"
        
        # API Key si está disponible
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return f"apikey_{api_key}"
        
        # User Agent + IP como fallback
        user_agent = request.headers.get("User-Agent", "unknown")
        client_ip = self._get_client_ip(request)
        return f"ip_{client_ip}_{hash(user_agent)}"
    
    def _get_client_ip(self, request: Request) -> str:
        """Obtener IP real del cliente considerando proxies"""
        # Headers de proxy más comunes
        for header in ["X-Forwarded-For", "X-Real-IP", "X-Client-IP"]:
            if header in request.headers:
                ip = request.headers[header].split(',')[0].strip()
                if ip and ip != "unknown":
                    return ip
        
        return request.client.host if request.client else "unknown"
    
    def _get_endpoint_key(self, request: Request) -> str:
        """Generar clave del endpoint para rate limiting"""
        method = request.method
        path = request.url.path
        
        # Normalizar paths con parámetros
        if "/api/notifications/" in path:
            # Reemplazar IDs numéricos con placeholder
            import re
            path = re.sub(r'/\d+(/|$)', '/*/\\1', path)
            path = path.rstrip('/')
        
        return f"{method}:{path}"
    
    def _should_skip_rate_limit(self, request: Request) -> bool:
        """Determinar si saltarse el rate limiting"""
        # Saltar para health checks
        if request.url.path.endswith("/health"):
            return True
        
        # Saltar para requests internos
        user_agent = request.headers.get("User-Agent", "")
        if "internal-service" in user_agent.lower():
            return True
        
        # Saltar si viene de localhost (desarrollo)
        client_ip = self._get_client_ip(request)
        if client_ip in ["127.0.0.1", "localhost", "::1"]:
            if getattr(settings, 'DEBUG', False):
                return True
        
        return False
    
    async def dispatch(self, request: Request, call_next):
        """Procesar request con rate limiting"""
        
        # Saltar rate limiting si es necesario
        if self._should_skip_rate_limit(request):
            return await call_next(request)
        
        start_time = time.time()
        client_id = self._get_client_id(request)
        endpoint_key = self._get_endpoint_key(request)
        
        # Obtener límites para este endpoint
        endpoint_limit = self.config.ENDPOINT_LIMITS.get(
            endpoint_key, 
            self.config.GLOBAL_LIMITS["requests_per_minute"]
        )
        
        try:
            # Verificar rate limit del endpoint específico
            is_limited, metadata = await self.limiter.is_rate_limited(
                client_id, endpoint_key, request.method, endpoint_limit
            )
            
            if is_limited:
                return self._create_rate_limit_response(metadata)
            
            # Verificar burst protection
            burst_limited, burst_metadata = await self.limiter.is_rate_limited(
                client_id, 
                "burst", 
                "ALL",
                self.config.BURST_LIMITS["requests_per_second"],
                self.config.BURST_LIMITS["window_seconds"]
            )
            
            if burst_limited:
                return self._create_rate_limit_response(burst_metadata, "Burst limit exceeded")
            
            # Procesar request
            response = await call_next(request)
            
            # Agregar headers de rate limiting
            self._add_rate_limit_headers(response, metadata)
            
            # Calcular tiempo de respuesta
            response_time = (time.time() - start_time) * 1000
            response.headers["X-Response-Time"] = f"{response_time:.2f}ms"
            
            return response
            
        except Exception as e:
            # Log error pero no bloquear requests
            print(f"Rate limiting error: {e}")
            response = await call_next(request)
            return response
    
    def _create_rate_limit_response(
        self, 
        metadata: Dict[str, Any], 
        message: str = "Rate limit exceeded"
    ) -> JSONResponse:
        """Crear respuesta de rate limit excedido"""
        
        error_response = ErrorResponse(
            error="rate_limit_exceeded",
            message=message,
            details={
                "limit": metadata["limit"],
                "remaining": metadata["remaining"],
                "reset_time": metadata["reset_time"],
                "window_seconds": metadata["window_seconds"]
            }
        )
        
        headers = {
            "X-RateLimit-Limit": str(metadata["limit"]),
            "X-RateLimit-Remaining": str(metadata["remaining"]),
            "X-RateLimit-Reset": str(metadata["reset_time"]),
            "X-RateLimit-Window": str(metadata["window_seconds"]),
            "Retry-After": str(metadata["window_seconds"])
        }
        
        return JSONResponse(
            status_code=429,
            content=error_response.dict(),
            headers=headers
        )
    
    def _add_rate_limit_headers(
        self, 
        response: Response, 
        metadata: Dict[str, Any]
    ):
        """Agregar headers de rate limiting a respuesta exitosa"""
        response.headers["X-RateLimit-Limit"] = str(metadata["limit"])
        response.headers["X-RateLimit-Remaining"] = str(metadata["remaining"])
        response.headers["X-RateLimit-Reset"] = str(metadata["reset_time"])
        response.headers["X-RateLimit-Window"] = str(metadata["window_seconds"])

# =====================================================================
# DECORADOR PARA RATE LIMITING ESPECÍFICO
# =====================================================================

def rate_limit(
    requests_per_minute: int = 60,
    per: str = "ip",  # "ip", "user", "api_key"
    skip_if: Optional[callable] = None
):
    """
    Decorador para aplicar rate limiting específico a endpoints
    
    Args:
        requests_per_minute: Límite de requests por minuto
        per: Criterio de agrupación ("ip", "user", "api_key")
        skip_if: Función para determinar cuándo saltar el rate limiting
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Obtener request del contexto
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request:
                # Si no hay request, ejecutar sin rate limiting
                return await func(*args, **kwargs)
            
            # Verificar si saltarse el rate limiting
            if skip_if and await skip_if(request):
                return await func(*args, **kwargs)
            
            # Aplicar rate limiting...
            # (implementación específica según necesidades)
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator

# =====================================================================
# UTILIDADES
# =====================================================================

async def get_rate_limit_stats(
    client_id: str,
    redis_client: Optional[redis.Redis] = None
) -> Dict[str, Any]:
    """Obtener estadísticas de rate limiting para un cliente"""
    
    limiter = RedisRateLimiter(redis_client)
    stats = {}
    
    config = RateLimitConfig()
    current_time = int(time.time())
    
    for endpoint, limit in config.ENDPOINT_LIMITS.items():
        key = f"rate_limit:{client_id}:{endpoint}"
        
        try:
            _, metadata = await limiter.is_rate_limited(
                client_id, endpoint, "GET", limit, test_only=True
            )
            
            stats[endpoint] = {
                "limit": metadata["limit"],
                "remaining": metadata["remaining"],
                "current_count": metadata["current_count"],
                "reset_time": metadata["reset_time"]
            }
            
        except Exception:
            stats[endpoint] = {
                "limit": limit,
                "remaining": limit,
                "current_count": 0,
                "reset_time": current_time + 60
            }
    
    return stats