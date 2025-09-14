"""
Middleware de Caching inteligente para la API de notificaciones
Implementa múltiples estrategias de cache con invalidación automática
"""

import json
import hashlib
import asyncio
from typing import Dict, Optional, Any, List, Tuple
from datetime import datetime, timedelta
from functools import wraps

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import redis.asyncio as redis
from redis.exceptions import RedisError

from app.core.config import settings

# =====================================================================
# CONFIGURACIÓN DE CACHE
# =====================================================================

class CacheConfig:
    """Configuración de cache por endpoint y tipo de dato"""
    
    # TTL por endpoint (en segundos)
    ENDPOINT_TTL = {
        # Métricas y estadísticas - cache más largo
        "GET:/api/notifications/metrics": 300,  # 5 minutos
        "GET:/api/notifications/metrics/daily": 600,  # 10 minutos
        
        # Listas con paginación - cache medio
        "GET:/api/notifications": 120,  # 2 minutos
        "GET:/api/notifications/contacts": 300,  # 5 minutos
        "GET:/api/notifications/templates": 600,  # 10 minutos
        
        # Datos específicos - cache corto
        "GET:/api/notifications/scheduler/status": 60,  # 1 minuto
        
        # Health checks - cache muy corto
        "GET:/api/health": 30,  # 30 segundos
    }
    
    # Configuración de invalidación
    INVALIDATION_PATTERNS = {
        # Cuando se crea/actualiza una notificación
        "notifications_write": [
            "GET:/api/notifications*",
            "GET:/api/notifications/metrics*"
        ],
        
        # Cuando se actualizan contactos o plantillas
        "config_write": [
            "GET:/api/notifications/contacts*",
            "GET:/api/notifications/templates*"
        ]
    }
    
    # Cache condicional basado en parámetros
    CONDITIONAL_CACHE = {
        "GET:/api/notifications": {
            "cache_if": lambda params: len(params) <= 3,  # Solo si pocos filtros
            "ttl_multiplier": lambda params: 0.5 if "fecha_desde" in params else 1.0
        }
    }

class SmartCache:
    """Sistema de cache inteligente con múltiples estrategias"""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client
        self.local_cache = {}  # L1 Cache (memoria local)
        self.cache_stats = {
            "hits": 0,
            "misses": 0,
            "redis_errors": 0
        }
        self.max_local_cache_size = 1000
    
    async def init_redis(self) -> Optional[redis.Redis]:
        """Inicializar conexión a Redis (L2 Cache)"""
        try:
            if not self.redis_client:
                self.redis_client = redis.from_url(
                    getattr(settings, 'REDIS_URL', 'redis://localhost:6379'),
                    decode_responses=True,
                    socket_timeout=2,
                    socket_connect_timeout=2
                )
                await self.redis_client.ping()
            return self.redis_client
        except Exception:
            return None
    
    def _generate_cache_key(
        self,
        endpoint: str,
        method: str,
        query_params: Dict[str, Any],
        headers: Dict[str, str]
    ) -> str:
        """Generar clave única para cache"""
        
        # Incluir parámetros relevantes para caching
        cache_data = {
            "endpoint": endpoint,
            "method": method,
            "params": sorted(query_params.items()),
            # Incluir headers que afecten la respuesta
            "user_context": headers.get("Authorization", "")[:50] if headers.get("Authorization") else "",
            "accept_language": headers.get("Accept-Language", "es"),
        }
        
        # Crear hash reproducible
        cache_string = json.dumps(cache_data, sort_keys=True)
        return f"api_cache:{hashlib.md5(cache_string.encode()).hexdigest()}"
    
    def _should_cache_request(
        self,
        method: str,
        endpoint: str,
        query_params: Dict[str, Any],
        headers: Dict[str, str]
    ) -> Tuple[bool, int]:
        """Determinar si la request debe ser cacheada y por cuánto tiempo"""
        
        # Solo cachear métodos GET
        if method != "GET":
            return False, 0
        
        # Verificar si el endpoint está en la configuración
        endpoint_key = f"{method}:{endpoint}"
        if endpoint_key not in CacheConfig.ENDPOINT_TTL:
            return False, 0
        
        base_ttl = CacheConfig.ENDPOINT_TTL[endpoint_key]
        
        # Aplicar cache condicional
        if endpoint_key in CacheConfig.CONDITIONAL_CACHE:
            condition_config = CacheConfig.CONDITIONAL_CACHE[endpoint_key]
            
            # Verificar condición
            if "cache_if" in condition_config:
                if not condition_config["cache_if"](query_params):
                    return False, 0
            
            # Aplicar multiplicador de TTL
            if "ttl_multiplier" in condition_config:
                multiplier = condition_config["ttl_multiplier"](query_params)
                base_ttl = int(base_ttl * multiplier)
        
        # No cachear requests con parámetros de tiempo muy específicos
        if "timestamp" in query_params or "random" in query_params:
            return False, 0
        
        # No cachear si hay headers que indican contenido dinámico
        if headers.get("Cache-Control") == "no-cache":
            return False, 0
        
        return True, base_ttl
    
    async def get_cached_response(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Obtener respuesta del cache (L1 -> L2)"""
        
        # Intentar L1 Cache (memoria local) primero
        if cache_key in self.local_cache:
            cached_data = self.local_cache[cache_key]
            if cached_data["expires_at"] > datetime.now().timestamp():
                self.cache_stats["hits"] += 1
                return cached_data["data"]
            else:
                # Limpiar entrada expirada
                del self.local_cache[cache_key]
        
        # Intentar L2 Cache (Redis)
        try:
            redis_client = await self.init_redis()
            if redis_client:
                cached_json = await redis_client.get(cache_key)
                if cached_json:
                    cached_data = json.loads(cached_json)
                    
                    # Almacenar en L1 para siguientes requests
                    self._store_local_cache(cache_key, cached_data, ttl=300)  # 5 min en L1
                    
                    self.cache_stats["hits"] += 1
                    return cached_data
        
        except RedisError:
            self.cache_stats["redis_errors"] += 1
        
        self.cache_stats["misses"] += 1
        return None
    
    async def store_cached_response(
        self,
        cache_key: str,
        data: Dict[str, Any],
        ttl: int
    ):
        """Almacenar respuesta en cache (L1 + L2)"""
        
        # Preparar datos para cache
        cache_data = {
            "data": data,
            "cached_at": datetime.now().isoformat(),
            "ttl": ttl
        }
        
        # Almacenar en L1 Cache
        self._store_local_cache(cache_key, data, ttl)
        
        # Almacenar en L2 Cache (Redis)
        try:
            redis_client = await self.init_redis()
            if redis_client:
                await redis_client.setex(
                    cache_key,
                    ttl,
                    json.dumps(cache_data, default=str)
                )
        except RedisError:
            self.cache_stats["redis_errors"] += 1
    
    def _store_local_cache(self, cache_key: str, data: Any, ttl: int):
        """Almacenar en cache local con límite de tamaño"""
        
        # Limpiar cache si está muy grande
        if len(self.local_cache) >= self.max_local_cache_size:
            self._cleanup_local_cache()
        
        expires_at = datetime.now().timestamp() + min(ttl, 300)  # Max 5 min en L1
        
        self.local_cache[cache_key] = {
            "data": data,
            "expires_at": expires_at
        }
    
    def _cleanup_local_cache(self):
        """Limpiar entries expirados del cache local"""
        current_time = datetime.now().timestamp()
        
        expired_keys = [
            key for key, value in self.local_cache.items()
            if value["expires_at"] <= current_time
        ]
        
        for key in expired_keys:
            del self.local_cache[key]
        
        # Si aún está muy grande, remover los más antiguos
        if len(self.local_cache) >= self.max_local_cache_size:
            sorted_items = sorted(
                self.local_cache.items(),
                key=lambda x: x[1]["expires_at"]
            )
            
            # Mantener solo la mitad más reciente
            keep_count = self.max_local_cache_size // 2
            keys_to_remove = [item[0] for item in sorted_items[:-keep_count]]
            
            for key in keys_to_remove:
                del self.local_cache[key]
    
    async def invalidate_pattern(self, pattern: str):
        """Invalidar cache por patrón"""
        
        # Invalidar L1 Cache
        keys_to_remove = []
        for key in self.local_cache:
            if self._match_pattern(key, pattern):
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.local_cache[key]
        
        # Invalidar L2 Cache (Redis)
        try:
            redis_client = await self.init_redis()
            if redis_client:
                # Buscar keys que coincidan con el patrón
                redis_pattern = pattern.replace("*", "*")
                keys = await redis_client.keys(f"api_cache:*{redis_pattern}*")
                if keys:
                    await redis_client.delete(*keys)
        except RedisError:
            pass
    
    def _match_pattern(self, cache_key: str, pattern: str) -> bool:
        """Verificar si una clave coincide con un patrón"""
        import fnmatch
        return fnmatch.fnmatch(cache_key, f"*{pattern}*")
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del cache"""
        total_requests = self.cache_stats["hits"] + self.cache_stats["misses"]
        hit_rate = (self.cache_stats["hits"] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "hits": self.cache_stats["hits"],
            "misses": self.cache_stats["misses"],
            "hit_rate_percentage": round(hit_rate, 2),
            "redis_errors": self.cache_stats["redis_errors"],
            "local_cache_size": len(self.local_cache),
            "total_requests": total_requests
        }

class CacheMiddleware(BaseHTTPMiddleware):
    """Middleware de cache para FastAPI"""
    
    def __init__(self, app, redis_client: Optional[redis.Redis] = None):
        super().__init__(app)
        self.cache = SmartCache(redis_client)
    
    def _normalize_endpoint(self, path: str) -> str:
        """Normalizar path para cache"""
        # Reemplazar IDs numéricos con placeholder para cache
        import re
        normalized = re.sub(r'/\d+(/|$)', '/*/\\1', path)
        return normalized.rstrip('/')
    
    def _extract_query_params(self, request: Request) -> Dict[str, Any]:
        """Extraer parámetros de query relevantes para cache"""
        params = dict(request.query_params)
        
        # Excluir parámetros que no deberían afectar el cache
        exclude_params = {"_", "timestamp", "cache_buster", "random"}
        return {k: v for k, v in params.items() if k not in exclude_params}
    
    async def dispatch(self, request: Request, call_next):
        """Procesar request con cache inteligente"""
        
        # Normalizar endpoint
        endpoint = self._normalize_endpoint(request.url.path)
        method = request.method
        query_params = self._extract_query_params(request)
        headers = dict(request.headers)
        
        # Verificar si debe cachearse
        should_cache, ttl = self.cache._should_cache_request(
            method, endpoint, query_params, headers
        )
        
        if not should_cache:
            return await call_next(request)
        
        # Generar clave de cache
        cache_key = self.cache._generate_cache_key(
            endpoint, method, query_params, headers
        )
        
        # Intentar obtener del cache
        cached_response = await self.cache.get_cached_response(cache_key)
        
        if cached_response:
            # Crear respuesta desde cache
            response = JSONResponse(
                content=cached_response,
                status_code=200
            )
            
            # Agregar headers de cache
            response.headers["X-Cache"] = "HIT"
            response.headers["X-Cache-Key"] = cache_key
            
            return response
        
        # No encontrado en cache, procesar request
        response = await call_next(request)
        
        # Solo cachear respuestas exitosas
        if response.status_code == 200:
            try:
                # Leer contenido de la respuesta
                response_body = b""
                async for chunk in response.body_iterator:
                    response_body += chunk
                
                # Parse JSON
                response_data = json.loads(response_body.decode())
                
                # Almacenar en cache
                await self.cache.store_cached_response(cache_key, response_data, ttl)
                
                # Recrear respuesta
                new_response = JSONResponse(
                    content=response_data,
                    status_code=response.status_code,
                    headers=dict(response.headers)
                )
                
                # Agregar headers de cache
                new_response.headers["X-Cache"] = "MISS"
                new_response.headers["X-Cache-TTL"] = str(ttl)
                
                return new_response
                
            except (json.JSONDecodeError, UnicodeDecodeError):
                # Si no se puede parsear, devolver respuesta original
                pass
        
        # Agregar header indicando que no se cacheó
        response.headers["X-Cache"] = "SKIP"
        return response

# =====================================================================
# DECORADORES DE CACHE
# =====================================================================

def cache_response(ttl: int = 300, key_prefix: str = ""):
    """
    Decorador para cachear respuestas de funciones específicas
    
    Args:
        ttl: Tiempo de vida en segundos
        key_prefix: Prefijo para la clave de cache
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generar clave única basada en argumentos
            cache_key = f"{key_prefix}:{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Intentar obtener del cache
            # (implementación específica según contexto)
            
            # Si no está en cache, ejecutar función
            result = await func(*args, **kwargs)
            
            # Almacenar en cache
            # (implementación específica)
            
            return result
        
        return wrapper
    return decorator

def invalidate_cache_on_write(patterns: List[str]):
    """
    Decorador para invalidar cache automáticamente en operaciones de escritura
    
    Args:
        patterns: Lista de patrones de cache a invalidar
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Ejecutar función
            result = await func(*args, **kwargs)
            
            # Invalidar patrones de cache
            cache = SmartCache()
            for pattern in patterns:
                await cache.invalidate_pattern(pattern)
            
            return result
        
        return wrapper
    return decorator

# =====================================================================
# UTILIDADES DE CACHE
# =====================================================================

async def warm_up_cache(endpoints: List[str], redis_client: Optional[redis.Redis] = None):
    """Pre-cargar cache con endpoints frecuentemente utilizados"""
    
    cache = SmartCache(redis_client)
    
    # Simular requests para endpoints populares
    popular_requests = [
        {"endpoint": "/api/notifications", "params": {"limit": 20}},
        {"endpoint": "/api/notifications/metrics", "params": {}},
        {"endpoint": "/api/notifications/contacts", "params": {"activo": True}},
        {"endpoint": "/api/notifications/templates", "params": {"activo": True}},
    ]
    
    for req in popular_requests:
        cache_key = cache._generate_cache_key(
            req["endpoint"], "GET", req["params"], {}
        )
        
        # Pre-cargar si no existe
        cached = await cache.get_cached_response(cache_key)
        if not cached:
            # Aquí se haría el request real y se cachearía
            pass

async def get_cache_statistics(redis_client: Optional[redis.Redis] = None) -> Dict[str, Any]:
    """Obtener estadísticas completas del sistema de cache"""
    
    cache = SmartCache(redis_client)
    basic_stats = cache.get_stats()
    
    # Estadísticas adicionales de Redis
    redis_stats = {}
    try:
        redis_client = await cache.init_redis()
        if redis_client:
            info = await redis_client.info()
            redis_stats = {
                "redis_memory_used": info.get("used_memory_human", "Unknown"),
                "redis_connected_clients": info.get("connected_clients", 0),
                "redis_total_commands": info.get("total_commands_processed", 0),
            }
    except Exception:
        redis_stats = {"redis_status": "unavailable"}
    
    return {
        **basic_stats,
        **redis_stats,
        "timestamp": datetime.now().isoformat()
    }