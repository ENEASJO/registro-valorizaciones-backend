"""
Servicio de caché optimizado para consultas OSCE
"""
import json
import hashlib
import time
from typing import Dict, Optional, Any
from datetime import datetime, timedelta

class OSCECacheService:
    """Cache inteligente para optimizar consultas OSCE"""
    
    def __init__(self):
        # Cache en memoria para desarrollo/testing
        # En producción se debería usar Redis
        self._cache: Dict[str, Dict[str, Any]] = {}
        
        # Configuración de TTL (Time To Live)
        self.ttl_config = {
            'consulta_empresa': 3600,      # 1 hora para datos de empresa
            'representantes': 7200,        # 2 horas para representantes (cambian poco)
            'contacto': 1800,              # 30 min para datos de contacto (pueden cambiar)
            'consorcios': 86400,           # 24 horas para consorcios (muy estables)
        }
    
    def _generate_cache_key(self, ruc: str, consulta_tipo: str = 'general') -> str:
        """Generar clave única para caché"""
        key_data = f"osce:{consulta_tipo}:{ruc}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get_cached_result(self, ruc: str, consulta_tipo: str = 'general') -> Optional[Dict[str, Any]]:
        """Obtener resultado desde caché si es válido"""
        cache_key = self._generate_cache_key(ruc, consulta_tipo)
        
        if cache_key not in self._cache:
            return None
        
        cached_item = self._cache[cache_key]
        
        # Verificar TTL
        ttl_seconds = self.ttl_config.get(consulta_tipo, 3600)
        expiry_time = cached_item['timestamp'] + ttl_seconds
        
        if time.time() > expiry_time:
            # Cache expirado
            del self._cache[cache_key]
            return None
        
        print(f"✅ Cache HIT para {ruc} ({consulta_tipo})")
        return cached_item['data']
    
    def set_cache_result(self, ruc: str, data: Dict[str, Any], consulta_tipo: str = 'general') -> None:
        """Guardar resultado en caché"""
        cache_key = self._generate_cache_key(ruc, consulta_tipo)
        
        self._cache[cache_key] = {
            'data': data,
            'timestamp': time.time(),
            'ruc': ruc,
            'tipo': consulta_tipo
        }
        
        print(f"💾 Cache SET para {ruc} ({consulta_tipo})")
    
    def invalidate_cache(self, ruc: str, consulta_tipo: Optional[str] = None) -> None:
        """Invalidar caché específico o todos los tipos para un RUC"""
        if consulta_tipo:
            cache_key = self._generate_cache_key(ruc, consulta_tipo)
            if cache_key in self._cache:
                del self._cache[cache_key]
                print(f"🗑️ Cache invalidado para {ruc} ({consulta_tipo})")
        else:
            # Invalidar todos los tipos para este RUC
            keys_to_remove = []
            for key, item in self._cache.items():
                if item['ruc'] == ruc:
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del self._cache[key]
            
            print(f"🗑️ Cache completo invalidado para {ruc}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Estadísticas del caché"""
        total_entries = len(self._cache)
        entries_by_type = {}
        
        for item in self._cache.values():
            tipo = item['tipo']
            entries_by_type[tipo] = entries_by_type.get(tipo, 0) + 1
        
        return {
            'total_entries': total_entries,
            'entries_by_type': entries_by_type,
            'ttl_config': self.ttl_config,
            'cache_size_mb': len(str(self._cache)) / (1024 * 1024)
        }
    
    def cleanup_expired(self) -> int:
        """Limpiar entradas expiradas del caché"""
        current_time = time.time()
        expired_keys = []
        
        for key, item in self._cache.items():
            ttl_seconds = self.ttl_config.get(item['tipo'], 3600)
            expiry_time = item['timestamp'] + ttl_seconds
            
            if current_time > expiry_time:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self._cache[key]
        
        if expired_keys:
            print(f"🧹 Limpiadas {len(expired_keys)} entradas expiradas del caché")
        
        return len(expired_keys)

# Instancia global del caché
osce_cache = OSCECacheService()