"""
Servicio de Pre-Caching Inteligente para OSCE
Pre-carga datos de empresas frecuentemente consultadas
"""
import asyncio
import logging
from typing import Dict, List, Set, Any
from datetime import datetime, timedelta
from collections import defaultdict
import json

from .osce_cache_service import osce_cache
from .osce_turbo_service import osce_turbo

logger = logging.getLogger(__name__)

class PreCacheService:
    """Servicio de pre-caching inteligente"""
    
    def __init__(self):
        # Estadísticas de consultas para predicción
        self.consultas_recientes: Dict[str, int] = defaultdict(int)  # RUC -> frecuencia
        self.ultimas_consultas: List[str] = []  # Historial de RUCs
        self.rucs_populares: Set[str] = set()  # RUCs más consultados
        
        # Configuración
        self.max_historial = 100
        self.umbral_popularidad = 3  # Consultas mínimas para ser "popular"
        self.intervalo_precache = 300  # 5 minutos entre pre-cachings
        
        # Control de pre-caching
        self.precaching_activo = False
        self.ultima_ejecucion = None
        
        # RUCs típicos de empresas constructoras (pre-seed)
        self.rucs_constructoras_comunes = {
            # Empresas grandes conocidas
            "20100070970",  # GRAÑA Y MONTERO
            "20100017491",  # COSAPI
            "20325218579",  # JJC CONTRATISTAS
            "20508565934",  # CONTRATISTAS ASOCIADOS
            "20600074114",  # CONSTRUCTORA E INGENIERIA V & Z (del ejemplo)
            # Se puede expandir con más RUCs comunes de la región
        }
    
    def registrar_consulta(self, ruc: str) -> None:
        """Registrar una consulta para análisis de patrones"""
        # Actualizar frecuencia
        self.consultas_recientes[ruc] += 1
        
        # Mantener historial limitado
        self.ultimas_consultas.append(ruc)
        if len(self.ultimas_consultas) > self.max_historial:
            ruc_antiguo = self.ultimas_consultas.pop(0)
            self.consultas_recientes[ruc_antiguo] -= 1
            if self.consultas_recientes[ruc_antiguo] <= 0:
                del self.consultas_recientes[ruc_antiguo]
        
        # Actualizar RUCs populares
        if self.consultas_recientes[ruc] >= self.umbral_popularidad:
            self.rucs_populares.add(ruc)
        
        logger.info(f"📊 Consulta registrada: {ruc} (frecuencia: {self.consultas_recientes[ruc]})")
    
    def get_rucs_para_precache(self) -> List[str]:
        """Obtener lista de RUCs candidatos para pre-caching"""
        candidatos = set()
        
        # 1. RUCs populares por frecuencia
        rucs_frecuentes = [ruc for ruc, freq in self.consultas_recientes.items() 
                          if freq >= self.umbral_popularidad]
        candidatos.update(rucs_frecuentes[:10])  # Top 10 más frecuentes
        
        # 2. RUCs consultados recientemente
        rucs_recientes = list(set(self.ultimas_consultas[-20:]))  # Últimos 20 únicos
        candidatos.update(rucs_recientes)
        
        # 3. RUCs de constructoras comunes (pre-seed)
        candidatos.update(self.rucs_constructoras_comunes)
        
        # 4. Patrones predictivos (RUCs similares a los consultados)
        rucs_similares = self._predecir_rucs_similares()
        candidatos.update(rucs_similares[:5])
        
        return list(candidatos)
    
    def _predecir_rucs_similares(self) -> List[str]:
        """Predecir RUCs similares basado en patrones"""
        if not self.ultimas_consultas:
            return []
        
        # Análisis de patrones en RUCs recientes
        rucs_similares = []
        
        for ruc in self.ultimas_consultas[-5:]:  # Últimos 5 RUCs
            try:
                # Generar variaciones de RUCs similares (empresas del mismo grupo/región)
                prefijo = ruc[:8]  # Primeros 8 dígitos (a menudo región/tipo)
                
                # Generar algunos RUCs similares en el rango
                base_num = int(ruc)
                for offset in [-50, -25, -10, 10, 25, 50]:
                    ruc_similar = str(base_num + offset)
                    if len(ruc_similar) == 11:  # Validar longitud
                        rucs_similares.append(ruc_similar)
                        
            except (ValueError, IndexError):
                continue
        
        return rucs_similares[:5]  # Máximo 5 similares
    
    async def ejecutar_precache(self) -> Dict[str, Any]:
        """Ejecutar proceso de pre-caching"""
        if self.precaching_activo:
            logger.info("⚠️ Pre-caching ya en ejecución, omitiendo")
            return {"status": "skipped", "razon": "ya_ejecutando"}
        
        # Verificar intervalo
        if self.ultima_ejecucion:
            tiempo_transcurrido = (datetime.now() - self.ultima_ejecucion).total_seconds()
            if tiempo_transcurrido < self.intervalo_precache:
                return {"status": "skipped", "razon": "intervalo_no_cumplido", "tiempo_restante": self.intervalo_precache - tiempo_transcurrido}
        
        logger.info("🚀 Iniciando pre-caching inteligente")
        self.precaching_activo = True
        inicio = datetime.now()
        
        try:
            # Obtener candidatos para pre-cache
            rucs_candidatos = self.get_rucs_para_precache()
            logger.info(f"📋 Pre-caching para {len(rucs_candidatos)} RUCs candidatos")
            
            # Filtrar RUCs que NO están en caché
            rucs_faltantes = []
            for ruc in rucs_candidatos:
                if not osce_cache.get_cached_result(ruc, 'consulta_empresa'):
                    rucs_faltantes.append(ruc)
            
            logger.info(f"⚡ {len(rucs_faltantes)} RUCs necesitan pre-caching")
            
            if not rucs_faltantes:
                return {
                    "status": "completed",
                    "rucs_procesados": 0,
                    "razon": "todos_en_cache",
                    "tiempo_total": (datetime.now() - inicio).total_seconds()
                }
            
            # Ejecutar pre-caching en lotes pequeños para no saturar
            resultados = {"exitosos": 0, "fallidos": 0, "errores": []}
            
            # Procesar en lotes de 3 para no saturar OSCE
            for i in range(0, len(rucs_faltantes), 3):
                lote = rucs_faltantes[i:i+3]
                
                # Pre-cache en paralelo para el lote
                tareas = [self._precache_ruc(ruc) for ruc in lote]
                resultados_lote = await asyncio.gather(*tareas, return_exceptions=True)
                
                # Procesar resultados del lote
                for j, resultado in enumerate(resultados_lote):
                    if isinstance(resultado, Exception):
                        resultados["fallidos"] += 1
                        resultados["errores"].append(f"{lote[j]}: {str(resultado)}")
                    elif resultado:
                        resultados["exitosos"] += 1
                    else:
                        resultados["fallidos"] += 1
                
                # Pausa pequeña entre lotes
                await asyncio.sleep(2)
            
            tiempo_total = (datetime.now() - inicio).total_seconds()
            logger.info(f"✅ Pre-caching completado en {tiempo_total:.2f}s: {resultados['exitosos']} exitosos, {resultados['fallidos']} fallidos")
            
            return {
                "status": "completed",
                "rucs_procesados": len(rucs_faltantes),
                "exitosos": resultados["exitosos"],
                "fallidos": resultados["fallidos"],
                "tiempo_total": tiempo_total,
                "errores": resultados["errores"][:5]  # Solo primeros 5 errores
            }
            
        except Exception as e:
            logger.error(f"❌ Error en pre-caching: {e}")
            return {
                "status": "error",
                "error": str(e),
                "tiempo_total": (datetime.now() - inicio).total_seconds()
            }
        
        finally:
            self.precaching_activo = False
            self.ultima_ejecucion = datetime.now()
    
    async def _precache_ruc(self, ruc: str) -> bool:
        """Pre-cachear un RUC específico"""
        try:
            logger.info(f"💾 Pre-caching RUC: {ruc}")
            
            # Usar servicio TURBO para máxima velocidad
            resultado = await osce_turbo.consultar_turbo(ruc)
            
            if resultado.get('success', False):
                # Guardar en caché con TTL extendido para pre-cache
                osce_cache.set_cache_result(ruc, resultado, 'consulta_empresa')
                logger.info(f"✅ Pre-cache exitoso: {ruc}")
                return True
            else:
                logger.warning(f"⚠️ Pre-cache sin datos: {ruc}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error pre-cache {ruc}: {e}")
            return False
    
    def get_estadisticas(self) -> Dict[str, Any]:
        """Obtener estadísticas del pre-caching"""
        return {
            "consultas_totales": len(self.ultimas_consultas),
            "rucs_unicos": len(self.consultas_recientes),
            "rucs_populares": len(self.rucs_populares),
            "precaching_activo": self.precaching_activo,
            "ultima_ejecucion": self.ultima_ejecucion.isoformat() if self.ultima_ejecucion else None,
            "top_rucs": dict(sorted(self.consultas_recientes.items(), key=lambda x: x[1], reverse=True)[:10]),
            "rucs_candidatos": len(self.get_rucs_para_precache())
        }
    
    async def precache_automatico_startup(self):
        """Pre-cache automático al inicio (RUCs de constructoras comunes)"""
        logger.info("🔄 Ejecutando pre-cache automático de startup...")
        
        # Pre-cachear solo constructoras comunes al inicio
        for ruc in list(self.rucs_constructoras_comunes)[:5]:  # Solo 5 al inicio
            if not osce_cache.get_cached_result(ruc, 'consulta_empresa'):
                await self._precache_ruc(ruc)
                await asyncio.sleep(3)  # Pausa entre consultas

# Instancia global
precache_service = PreCacheService()