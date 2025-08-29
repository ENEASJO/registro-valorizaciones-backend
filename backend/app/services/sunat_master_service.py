"""
Servicio maestro SUNAT que combina el servicio robusto con fallback
Garantiza obtener datos reales cuando es posible, con fallback confiable
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum

from app.models.ruc import EmpresaInfo
from app.services.sunat_service_robust import sunat_service_robust, SunatErrorType
from app.services.sunat_fallback_service import sunat_fallback_service
from app.utils.validators import validate_ruc

logger = logging.getLogger(__name__)


class SunatStrategy(Enum):
    """Estrategias de consulta SUNAT"""
    ROBUST_ONLY = "robust_only"
    FALLBACK_ONLY = "fallback_only"
    ROBUST_WITH_FALLBACK = "robust_with_fallback"
    SMART_SELECTION = "smart_selection"


class SUNATMasterService:
    """Servicio maestro que combina scraping robusto con fallback confiable"""
    
    def __init__(self):
        self.default_strategy = SunatStrategy.ROBUST_WITH_FALLBACK
        self.error_counts = {}  # Contador de errores por tipo
        self.last_successful_method = {}  # Último método exitoso por RUC
        self.performance_stats = {
            "robust_success": 0,
            "robust_failures": 0,
            "fallback_used": 0,
            "total_queries": 0
        }
    
    async def consultar_empresa(self, ruc: str, strategy: Optional[SunatStrategy] = None) -> EmpresaInfo:
        """Consulta empresa usando la estrategia especificada o la por defecto"""
        if not validate_ruc(ruc):
            raise ValueError(f"RUC inválido: {ruc}")
        
        strategy = strategy or self.default_strategy
        self.performance_stats["total_queries"] += 1
        
        logger.info(f"🎯 MASTER SUNAT - Consultando RUC: {ruc} (Estrategia: {strategy.value})")
        
        start_time = datetime.now()
        
        try:
            if strategy == SunatStrategy.ROBUST_ONLY:
                return await self._consultar_robust_only(ruc)
            
            elif strategy == SunatStrategy.FALLBACK_ONLY:
                return await self._consultar_fallback_only(ruc)
            
            elif strategy == SunatStrategy.ROBUST_WITH_FALLBACK:
                return await self._consultar_robust_with_fallback(ruc)
            
            elif strategy == SunatStrategy.SMART_SELECTION:
                return await self._consultar_smart_selection(ruc)
            
            else:
                raise ValueError(f"Estrategia no válida: {strategy}")
                
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"❌ Error final en consulta MASTER para RUC {ruc}: {str(e)} (Tiempo: {execution_time:.2f}s)")
            raise Exception(f"Error en consulta SUNAT MASTER: {str(e)}")
    
    async def _consultar_robust_only(self, ruc: str) -> EmpresaInfo:
        """Consulta usando solo el servicio robusto"""
        logger.info(f"🔧 Usando solo servicio robusto para RUC: {ruc}")
        
        try:
            empresa = await sunat_service_robust.consultar_empresa(ruc)
            self.performance_stats["robust_success"] += 1
            self._update_successful_method(ruc, "robust")
            
            # Marcar datos como obtenidos de fuente real
            self._mark_as_real_data(empresa, "SUNAT_ROBUST")
            
            logger.info(f"✅ Consulta robusta exitosa para RUC: {ruc}")
            return empresa
            
        except Exception as e:
            self.performance_stats["robust_failures"] += 1
            self._count_error("robust", str(e))
            
            logger.error(f"❌ Servicio robusto falló para RUC {ruc}: {str(e)}")
            raise Exception(f"Error en servicio robusto: {str(e)}")
    
    async def _consultar_fallback_only(self, ruc: str) -> EmpresaInfo:
        """Consulta usando solo el servicio de fallback"""
        logger.info(f"🔄 Usando solo servicio fallback para RUC: {ruc}")
        
        try:
            empresa = await sunat_fallback_service.consultar_empresa_fallback(ruc)
            self.performance_stats["fallback_used"] += 1
            self._update_successful_method(ruc, "fallback")
            
            # Marcar datos como fallback
            self._mark_as_fallback_data(empresa, "SUNAT_FALLBACK")
            
            logger.info(f"✅ Consulta fallback exitosa para RUC: {ruc}")
            return empresa
            
        except Exception as e:
            logger.error(f"❌ Servicio fallback falló para RUC {ruc}: {str(e)}")
            raise Exception(f"Error en servicio fallback: {str(e)}")
    
    async def _consultar_robust_with_fallback(self, ruc: str) -> EmpresaInfo:
        """Consulta robusta con fallback automático"""
        logger.info(f"🎯 Usando servicio robusto con fallback para RUC: {ruc}")
        
        # Intentar primero el servicio robusto
        try:
            logger.info(f"🔧 Intentando servicio robusto...")
            empresa = await sunat_service_robust.consultar_empresa(ruc)
            
            self.performance_stats["robust_success"] += 1
            self._update_successful_method(ruc, "robust")
            self._mark_as_real_data(empresa, "SUNAT_ROBUST")
            
            logger.info(f"✅ Servicio robusto exitoso para RUC: {ruc}")
            return empresa
            
        except Exception as robust_error:
            self.performance_stats["robust_failures"] += 1
            self._count_error("robust", str(robust_error))
            
            logger.warning(f"⚠️ Servicio robusto falló, intentando fallback para RUC {ruc}: {str(robust_error)}")
            
            # Usar fallback
            try:
                logger.info(f"🔄 Activando fallback...")
                empresa = await sunat_fallback_service.consultar_empresa_fallback(ruc)
                
                self.performance_stats["fallback_used"] += 1
                self._update_successful_method(ruc, "fallback")
                self._mark_as_fallback_data(empresa, "SUNAT_FALLBACK_AUTO")
                
                logger.info(f"✅ Fallback exitoso para RUC: {ruc}")
                return empresa
                
            except Exception as fallback_error:
                logger.error(f"❌ Tanto robusto como fallback fallaron para RUC {ruc}")
                logger.error(f"   Robust error: {str(robust_error)}")
                logger.error(f"   Fallback error: {str(fallback_error)}")
                
                raise Exception(f"Error completo: Robust({str(robust_error)}) + Fallback({str(fallback_error)})")
    
    async def _consultar_smart_selection(self, ruc: str) -> EmpresaInfo:
        """Selección inteligente basada en historial de errores y RUC"""
        logger.info(f"🧠 Usando selección inteligente para RUC: {ruc}")
        
        # Verificar si hay datos locales para este RUC
        if sunat_fallback_service.tiene_datos_locales(ruc):
            logger.info(f"💾 RUC {ruc} encontrado en base local - usando fallback directo")
            return await self._consultar_fallback_only(ruc)
        
        # Verificar último método exitoso para este RUC
        if ruc in self.last_successful_method:
            last_method = self.last_successful_method[ruc]
            logger.info(f"📚 Último método exitoso para RUC {ruc}: {last_method}")
            
            if last_method == "robust":
                # Intentar robusto primero
                return await self._consultar_robust_with_fallback(ruc)
            else:
                # Usar fallback directo
                return await self._consultar_fallback_only(ruc)
        
        # Análisis de tasa de errores recientes
        robust_error_rate = self._get_error_rate("robust")
        
        if robust_error_rate > 0.7:  # Si más del 70% de errores en robusto
            logger.info(f"⚠️ Alta tasa de errores en robusto ({robust_error_rate:.2%}), usando fallback directo")
            return await self._consultar_fallback_only(ruc)
        
        # Por defecto, usar robusto con fallback
        return await self._consultar_robust_with_fallback(ruc)
    
    def _mark_as_real_data(self, empresa: EmpresaInfo, source: str) -> None:
        """Marca los datos como obtenidos de fuente real"""
        # Agregar metadatos para indicar que son datos reales
        if hasattr(empresa, '_metadata'):
            empresa._metadata['source'] = source
            empresa._metadata['is_real_data'] = True
        else:
            empresa._metadata = {
                'source': source,
                'is_real_data': True,
                'obtained_at': datetime.now().isoformat()
            }
    
    def _mark_as_fallback_data(self, empresa: EmpresaInfo, source: str) -> None:
        """Marca los datos como obtenidos de fallback"""
        if hasattr(empresa, '_metadata'):
            empresa._metadata['source'] = source
            empresa._metadata['is_real_data'] = False
        else:
            empresa._metadata = {
                'source': source,
                'is_real_data': False,
                'obtained_at': datetime.now().isoformat()
            }
    
    def _update_successful_method(self, ruc: str, method: str) -> None:
        """Actualiza el último método exitoso para un RUC"""
        self.last_successful_method[ruc] = method
        
        # Limpiar historial si es muy grande
        if len(self.last_successful_method) > 1000:
            # Mantener solo los últimos 500
            items = list(self.last_successful_method.items())[-500:]
            self.last_successful_method = dict(items)
    
    def _count_error(self, service: str, error_msg: str) -> None:
        """Cuenta errores por servicio"""
        key = f"{service}_errors"
        if key not in self.error_counts:
            self.error_counts[key] = []
        
        self.error_counts[key].append({
            'timestamp': datetime.now(),
            'message': error_msg[:100]  # Limitar tamaño
        })
        
        # Mantener solo errores de las últimas 24 horas
        cutoff = datetime.now().timestamp() - 86400  # 24 horas
        self.error_counts[key] = [
            error for error in self.error_counts[key] 
            if error['timestamp'].timestamp() > cutoff
        ]
    
    def _get_error_rate(self, service: str) -> float:
        """Calcula la tasa de errores reciente para un servicio"""
        key = f"{service}_errors"
        if key not in self.error_counts:
            return 0.0
        
        recent_errors = len(self.error_counts[key])
        
        # Calcular basado en total de intentos recientes
        if service == "robust":
            recent_attempts = self.performance_stats["robust_success"] + self.performance_stats["robust_failures"]
        else:
            recent_attempts = max(recent_errors, 1)  # Evitar división por cero
        
        if recent_attempts == 0:
            return 0.0
        
        return recent_errors / recent_attempts
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de rendimiento"""
        total = self.performance_stats["total_queries"]
        
        stats = {
            **self.performance_stats,
            "robust_success_rate": (
                self.performance_stats["robust_success"] / max(
                    self.performance_stats["robust_success"] + self.performance_stats["robust_failures"], 1
                )
            ),
            "fallback_usage_rate": (
                self.performance_stats["fallback_used"] / max(total, 1)
            ),
            "error_rates": {
                service: self._get_error_rate(service.replace('_errors', ''))
                for service in self.error_counts.keys()
            }
        }
        
        return stats
    
    def reset_stats(self) -> None:
        """Reinicia estadísticas"""
        self.error_counts.clear()
        self.last_successful_method.clear()
        self.performance_stats = {
            "robust_success": 0,
            "robust_failures": 0,
            "fallback_used": 0,
            "total_queries": 0
        }
        logger.info("📊 Estadísticas reiniciadas")
    
    async def health_check(self) -> Dict[str, Any]:
        """Verifica el estado de todos los servicios"""
        health = {
            "timestamp": datetime.now().isoformat(),
            "services": {},
            "performance": self.get_performance_stats()
        }
        
        # Test rápido del servicio fallback
        try:
            test_ruc = "20600074114"  # RUC de prueba en base local
            await sunat_fallback_service.consultar_empresa_fallback(test_ruc)
            health["services"]["fallback"] = "healthy"
        except Exception as e:
            health["services"]["fallback"] = f"error: {str(e)[:50]}"
        
        # El servicio robusto no se puede probar rápidamente
        health["services"]["robust"] = "available"
        
        return health


# Instancia singleton del servicio maestro
sunat_master_service = SUNATMasterService()