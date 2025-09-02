"""
Servicio OSCE optimizado con caché, paralelización y estrategias inteligentes
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

from .osce_service_improved import OSCEServiceImproved
from .osce_cache_service import osce_cache

logger = logging.getLogger(__name__)

class OSCEServiceOptimized(OSCEServiceImproved):
    """Servicio OSCE con optimizaciones avanzadas"""
    
    def __init__(self):
        super().__init__()
        self.max_concurrent_requests = 3  # Límite para no saturar OSCE
        self.request_timeout = 20  # Timeout por request individual
        self.total_timeout = 45    # Timeout total para todas las operaciones
    
    async def consultar_empresa_optimizado(self, ruc: str) -> Dict[str, Any]:
        """
        Consulta optimizada con caché y estrategias múltiples
        """
        logger.info(f"🚀 Iniciando consulta optimizada OSCE para RUC: {ruc}")
        start_time = datetime.now()
        
        try:
            # 1. VERIFICAR CACHÉ PRIMERO
            cached_result = osce_cache.get_cached_result(ruc, 'consulta_empresa')
            if cached_result:
                logger.info(f"⚡ Resultado desde caché en {(datetime.now() - start_time).total_seconds():.2f}s")
                return cached_result
            
            # 2. CONSULTA NUEVA CON ESTRATEGIAS PARALELAS
            resultado = await self._ejecutar_consulta_con_fallbacks(ruc)
            
            # 3. GUARDAR EN CACHÉ SI ES EXITOSA
            if resultado.get('success', False):
                osce_cache.set_cache_result(ruc, resultado, 'consulta_empresa')
            
            tiempo_total = (datetime.now() - start_time).total_seconds()
            logger.info(f"✅ Consulta OSCE completada en {tiempo_total:.2f}s")
            
            return resultado
            
        except Exception as e:
            logger.error(f"❌ Error en consulta optimizada OSCE: {e}")
            return {
                'success': False,
                'error': str(e),
                'fuente': 'OSCE_OPTIMIZADO',
                'timestamp': datetime.now().isoformat()
            }
    
    async def _ejecutar_consulta_con_fallbacks(self, ruc: str) -> Dict[str, Any]:
        """
        Ejecutar consulta con múltiples estrategias en paralelo
        """
        logger.info("🔄 Ejecutando estrategias paralelas...")
        
        # Definir estrategias de consulta
        estrategias = [
            self._estrategia_busqueda_directa,
            self._estrategia_busqueda_avanzada,
            self._estrategia_busqueda_alternativa
        ]
        
        try:
            # Ejecutar estrategias con timeout
            resultados = await asyncio.wait_for(
                self._ejecutar_estrategias_paralelas(ruc, estrategias),
                timeout=self.total_timeout
            )
            
            # Seleccionar mejor resultado
            mejor_resultado = self._seleccionar_mejor_resultado(resultados)
            return mejor_resultado
            
        except asyncio.TimeoutError:
            logger.warning(f"⏱️ Timeout en consultas paralelas OSCE para {ruc}")
            return {
                'success': False,
                'error': 'Timeout en consulta OSCE',
                'fuente': 'OSCE_TIMEOUT',
                'timestamp': datetime.now().isoformat()
            }
    
    async def _ejecutar_estrategias_paralelas(self, ruc: str, estrategias: List) -> List[Dict[str, Any]]:
        """
        Ejecutar múltiples estrategias de consulta en paralelo
        """
        semaforo = asyncio.Semaphore(self.max_concurrent_requests)
        
        async def ejecutar_con_semaforo(estrategia):
            async with semaforo:
                try:
                    resultado = await asyncio.wait_for(
                        estrategia(ruc), 
                        timeout=self.request_timeout
                    )
                    return resultado
                except Exception as e:
                    logger.warning(f"⚠️ Estrategia falló: {e}")
                    return {'success': False, 'error': str(e), 'estrategia': estrategia.__name__}
        
        # Ejecutar todas las estrategias en paralelo
        tareas = [ejecutar_con_semaforo(estrategia) for estrategia in estrategias]
        resultados = await asyncio.gather(*tareas, return_exceptions=True)
        
        # Filtrar resultados válidos
        resultados_validos = []
        for resultado in resultados:
            if isinstance(resultado, dict) and not isinstance(resultado, Exception):
                resultados_validos.append(resultado)
        
        return resultados_validos
    
    def _seleccionar_mejor_resultado(self, resultados: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Seleccionar el mejor resultado basado en calidad de datos
        """
        if not resultados:
            return {
                'success': False,
                'error': 'No se obtuvieron resultados válidos',
                'fuente': 'OSCE_SIN_RESULTADOS',
                'timestamp': datetime.now().isoformat()
            }
        
        # Filtrar solo resultados exitosos
        exitosos = [r for r in resultados if r.get('success', False)]
        
        if not exitosos:
            # Retornar el primer resultado con error más descriptivo
            return resultados[0]
        
        # Función de puntuación para calidad de datos
        def calcular_puntuacion(resultado: Dict[str, Any]) -> int:
            puntuacion = 0
            data = resultado.get('data', {})
            
            # Puntos por datos de contacto
            if data.get('telefono'): puntuacion += 20
            if data.get('email'): puntuacion += 20
            if data.get('direccion'): puntuacion += 15
            
            # Puntos por representantes
            representantes = data.get('representantes', [])
            puntuacion += min(len(representantes) * 10, 30)
            
            # Puntos por datos adicionales
            if data.get('ciudad'): puntuacion += 10
            if data.get('departamento'): puntuacion += 10
            
            return puntuacion
        
        # Seleccionar resultado con mayor puntuación
        mejor = max(exitosos, key=calcular_puntuacion)
        
        # Enriquecer con datos de otros resultados si es necesario
        mejor_enriquecido = self._enriquecer_resultado(mejor, exitosos)
        
        logger.info(f"🏆 Seleccionado mejor resultado con puntuación: {calcular_puntuacion(mejor_enriquecido)}")
        return mejor_enriquecido
    
    def _enriquecer_resultado(self, resultado_principal: Dict[str, Any], todos_resultados: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Enriquecer resultado principal con datos faltantes de otros resultados
        """
        data_principal = resultado_principal.get('data', {})
        
        for resultado in todos_resultados:
            if resultado == resultado_principal:
                continue
                
            data_otro = resultado.get('data', {})
            
            # Completar datos faltantes
            if not data_principal.get('telefono') and data_otro.get('telefono'):
                data_principal['telefono'] = data_otro['telefono']
            
            if not data_principal.get('email') and data_otro.get('email'):
                data_principal['email'] = data_otro['email']
            
            if not data_principal.get('direccion') and data_otro.get('direccion'):
                data_principal['direccion'] = data_otro['direccion']
            
            # Combinar representantes únicos
            representantes_principales = data_principal.get('representantes', [])
            representantes_otros = data_otro.get('representantes', [])
            
            # Agregar representantes únicos (por DNI)
            dnis_existentes = {r.get('documento', '') for r in representantes_principales}
            for rep in representantes_otros:
                if rep.get('documento') and rep['documento'] not in dnis_existentes:
                    representantes_principales.append(rep)
            
            data_principal['representantes'] = representantes_principales
        
        # Marcar como enriquecido
        data_principal['fuente'] = f"{data_principal.get('fuente', 'OSCE')}_ENRIQUECIDO"
        
        return resultado_principal
    
    # ESTRATEGIAS DE CONSULTA ESPECÍFICAS
    async def _estrategia_busqueda_directa(self, ruc: str) -> Dict[str, Any]:
        """Estrategia 1: Búsqueda directa por RUC"""
        logger.info("📍 Ejecutando estrategia: Búsqueda directa")
        
        # Implementación placeholder - conectar con lógica existente
        try:
            # Aquí iría la lógica específica de búsqueda directa
            # Por ahora simular resultado
            await asyncio.sleep(0.5)  # Simular tiempo de procesamiento
            
            return {
                'success': True,
                'data': {
                    'ruc': ruc,
                    'fuente': 'OSCE_DIRECTO',
                    'telefono': '',  # Se llenaría con lógica real
                    'email': '',
                    'representantes': [],
                    'estrategia': 'busqueda_directa'
                },
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {'success': False, 'error': str(e), 'estrategia': 'busqueda_directa'}
    
    async def _estrategia_busqueda_avanzada(self, ruc: str) -> Dict[str, Any]:
        """Estrategia 2: Búsqueda avanzada con filtros"""
        logger.info("🔍 Ejecutando estrategia: Búsqueda avanzada")
        
        try:
            await asyncio.sleep(0.7)  # Simular tiempo de procesamiento
            
            return {
                'success': True,
                'data': {
                    'ruc': ruc,
                    'fuente': 'OSCE_AVANZADO',
                    'telefono': '',
                    'email': '',
                    'representantes': [],
                    'estrategia': 'busqueda_avanzada'
                },
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {'success': False, 'error': str(e), 'estrategia': 'busqueda_avanzada'}
    
    async def _estrategia_busqueda_alternativa(self, ruc: str) -> Dict[str, Any]:
        """Estrategia 3: Búsqueda por nombre de empresa"""
        logger.info("🔄 Ejecutando estrategia: Búsqueda alternativa")
        
        try:
            await asyncio.sleep(0.3)  # Simular tiempo de procesamiento
            
            return {
                'success': True,
                'data': {
                    'ruc': ruc,
                    'fuente': 'OSCE_ALTERNATIVO',
                    'telefono': '',
                    'email': '',
                    'representantes': [],
                    'estrategia': 'busqueda_alternativa'
                },
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {'success': False, 'error': str(e), 'estrategia': 'busqueda_alternativa'}
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del caché"""
        return osce_cache.get_cache_stats()
    
    def invalidate_cache(self, ruc: str) -> None:
        """Invalidar caché para un RUC específico"""
        osce_cache.invalidate_cache(ruc)

# Instancia global optimizada
osce_service_optimized = OSCEServiceOptimized()