"""
Middleware para integración automática de notificaciones WhatsApp
con el sistema de valorizaciones existente
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.whatsapp_notifications import EventoTrigger
from app.services.notification_service import notification_service
from app.utils.exceptions import NotificationError

logger = logging.getLogger(__name__)

class NotificationMiddleware:
    """
    Middleware para crear notificaciones automáticas cuando cambian 
    los estados de las valorizaciones
    """
    
    def __init__(self):
        self.notification_service = notification_service
        # Mapeo de estados de valorización a eventos de notificación
        self.estado_evento_mapping = {
            "PRESENTADA": EventoTrigger.RECIBIDA,
            "EN_REVISION": EventoTrigger.EN_REVISION,
            "OBSERVADA": EventoTrigger.OBSERVADA,
            "APROBADA": EventoTrigger.APROBADA,
            "ANULADA": EventoTrigger.RECHAZADA,
            "RECHAZADA": EventoTrigger.RECHAZADA
        }
    
    async def on_valorizacion_status_change(
        self,
        valorizacion_id: int,
        estado_anterior: Optional[str],
        estado_nuevo: str,
        empresa_id: Optional[int] = None,
        obra_id: Optional[int] = None,
        monto_total: Optional[float] = None,
        observaciones: Optional[str] = None,
        usuario_modificacion_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Maneja el cambio de estado de una valorización y crea notificaciones automáticas
        
        Args:
            valorizacion_id: ID de la valorización
            estado_anterior: Estado anterior de la valorización
            estado_nuevo: Estado nuevo de la valorización
            empresa_id: ID de la empresa (opcional)
            obra_id: ID de la obra (opcional)
            monto_total: Monto total de la valorización (opcional)
            observaciones: Observaciones del cambio (opcional)
            usuario_modificacion_id: ID del usuario que hizo el cambio (opcional)
            
        Returns:
            Dict con resultado de la creación de notificaciones
        """
        try:
            # Verificar si el cambio de estado debe generar notificaciones
            evento_trigger = self.estado_evento_mapping.get(estado_nuevo)
            
            if not evento_trigger:
                logger.info(f"Estado {estado_nuevo} no requiere notificaciones automáticas")
                return {
                    "notificaciones_creadas": 0,
                    "mensaje": "Estado no requiere notificaciones"
                }
            
            # Obtener sesión de base de datos
            db = next(get_db())
            
            try:
                # Preparar variables adicionales para las plantillas
                variables_extra = {
                    "empresa_id": empresa_id,
                    "obra_id": obra_id,
                    "monto_total": f"{monto_total:.2f}" if monto_total else "0.00",
                    "observaciones": observaciones or "",
                    "usuario_cambio_id": usuario_modificacion_id
                }
                
                # Obtener información adicional de la valorización si es posible
                # TODO: Integrar con el servicio de valorizaciones existente
                variables_extra.update(
                    await self._enrich_valorizacion_data(
                        db, valorizacion_id, empresa_id, obra_id
                    )
                )
                
                # Crear notificaciones automáticas
                notificaciones = await self.notification_service.create_notification(
                    db=db,
                    valorizacion_id=valorizacion_id,
                    evento_trigger=evento_trigger,
                    estado_actual=estado_nuevo,
                    estado_anterior=estado_anterior,
                    variables_extra=variables_extra,
                    envio_inmediato=await self._should_send_immediately(estado_nuevo)
                )
                
                logger.info(
                    f"Creadas {len(notificaciones)} notificaciones para valorización {valorizacion_id} "
                    f"(estado: {estado_anterior} -> {estado_nuevo})"
                )
                
                return {
                    "notificaciones_creadas": len(notificaciones),
                    "notificaciones": notificaciones,
                    "evento_trigger": evento_trigger.value,
                    "mensaje": "Notificaciones creadas exitosamente"
                }
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error creando notificaciones automáticas: {str(e)}")
            return {
                "notificaciones_creadas": 0,
                "error": str(e),
                "mensaje": "Error creando notificaciones"
            }
    
    async def _enrich_valorizacion_data(
        self,
        db: Session,
        valorizacion_id: int,
        empresa_id: Optional[int],
        obra_id: Optional[int]
    ) -> Dict[str, Any]:
        """
        Enriquece los datos de la valorización con información adicional
        
        TODO: Integrar con los servicios existentes de valorizaciones, empresas y obras
        """
        variables_extra = {}
        
        try:
            # Obtener información de empresa
            if empresa_id:
                # TODO: Usar el servicio de empresas existente
                # empresa = await empresa_service.get_empresa(empresa_id)
                # variables_extra["empresa_razon_social"] = empresa.razon_social
                variables_extra["empresa_razon_social"] = f"Empresa {empresa_id}"
            
            # Obtener información de obra  
            if obra_id:
                # TODO: Usar el servicio de obras existente
                # obra = await obra_service.get_obra(obra_id)
                # variables_extra["obra_nombre"] = obra.nombre
                variables_extra["obra_nombre"] = f"Obra {obra_id}"
            
            # Generar número de valorización
            variables_extra["valorizacion_numero"] = f"VAL-{valorizacion_id:06d}"
            variables_extra["valorizacion_periodo"] = datetime.now().strftime("%m/%Y")
            
        except Exception as e:
            logger.error(f"Error enriqueciendo datos de valorización: {str(e)}")
            # Usar valores por defecto en caso de error
            variables_extra.update({
                "empresa_razon_social": "Empresa",
                "obra_nombre": "Obra",
                "valorizacion_numero": f"VAL-{valorizacion_id:06d}",
                "valorizacion_periodo": datetime.now().strftime("%m/%Y")
            })
        
        return variables_extra
    
    async def _should_send_immediately(self, estado_nuevo: str) -> bool:
        """
        Determina si las notificaciones para un estado deben enviarse inmediatamente
        """
        # Estados críticos que requieren notificación inmediata
        estados_inmediatos = ["OBSERVADA", "RECHAZADA", "ANULADA", "APROBADA"]
        return estado_nuevo in estados_inmediatos
    
    def create_trigger_function(self) -> str:
        """
        Genera función helper para ser llamada desde otros servicios
        
        Returns:
            str: Nombre de la función a importar
        """
        return "notify_valorizacion_change"

# Función helper para ser llamada desde otros servicios
async def notify_valorizacion_change(
    valorizacion_id: int,
    estado_anterior: Optional[str],
    estado_nuevo: str,
    **kwargs
) -> Dict[str, Any]:
    """
    Función helper para crear notificaciones desde otros servicios
    
    Esta función puede ser importada y llamada desde los servicios de valorizaciones
    existentes cuando ocurra un cambio de estado.
    
    Ejemplo de uso:
    ```python
    from app.services.notification_middleware import notify_valorizacion_change
    
    # En el servicio de valorizaciones, después de cambiar el estado:
    await notify_valorizacion_change(
        valorizacion_id=123,
        estado_anterior="EN_REVISION",
        estado_nuevo="APROBADA",
        empresa_id=456,
        monto_total=50000.0
    )
    ```
    """
    middleware = NotificationMiddleware()
    return await middleware.on_valorizacion_status_change(
        valorizacion_id=valorizacion_id,
        estado_anterior=estado_anterior,
        estado_nuevo=estado_nuevo,
        **kwargs
    )

# Decorador para servicios existentes
def notify_on_status_change(func):
    """
    Decorador para servicios de valorización existentes
    
    Ejemplo de uso:
    ```python
    from app.services.notification_middleware import notify_on_status_change
    
    class ValorizacionService:
        @notify_on_status_change
        async def update_status(self, valorizacion_id, nuevo_estado, **kwargs):
            # Lógica existente del servicio
            old_status = self.get_current_status(valorizacion_id)
            result = self.update_valorizacion_status(valorizacion_id, nuevo_estado)
            
            # El decorador automáticamente llamará a las notificaciones
            # usando los parámetros retornados
            return {
                "valorizacion_id": valorizacion_id,
                "estado_anterior": old_status,
                "estado_nuevo": nuevo_estado,
                "success": True,
                **kwargs
            }
    ```
    """
    async def wrapper(*args, **kwargs):
        try:
            # Ejecutar función original
            result = await func(*args, **kwargs)
            
            # Si el resultado contiene información de cambio de estado, crear notificaciones
            if (isinstance(result, dict) and 
                "valorizacion_id" in result and 
                "estado_nuevo" in result and
                result.get("success", False)):
                
                notification_result = await notify_valorizacion_change(
                    valorizacion_id=result["valorizacion_id"],
                    estado_anterior=result.get("estado_anterior"),
                    estado_nuevo=result["estado_nuevo"],
                    empresa_id=result.get("empresa_id"),
                    obra_id=result.get("obra_id"),
                    monto_total=result.get("monto_total"),
                    observaciones=result.get("observaciones"),
                    usuario_modificacion_id=result.get("usuario_modificacion_id")
                )
                
                # Agregar información de notificaciones al resultado
                result["notificaciones"] = notification_result
            
            return result
            
        except Exception as e:
            logger.error(f"Error en decorador de notificaciones: {str(e)}")
            # Continuar con el resultado original si hay error en notificaciones
            return await func(*args, **kwargs)
    
    return wrapper

class NotificationEventHandler:
    """
    Handler de eventos para integración con sistemas externos
    """
    
    @staticmethod
    async def handle_valorizacion_created(event_data: Dict[str, Any]):
        """Maneja evento de creación de valorización"""
        # Por ahora no crear notificaciones para creación
        pass
    
    @staticmethod
    async def handle_valorizacion_updated(event_data: Dict[str, Any]):
        """Maneja evento de actualización de valorización"""
        if "estado_anterior" in event_data and "estado_nuevo" in event_data:
            return await notify_valorizacion_change(**event_data)
    
    @staticmethod
    async def handle_valorizacion_deleted(event_data: Dict[str, Any]):
        """Maneja evento de eliminación de valorización"""
        # TODO: Implementar cancelación de notificaciones pendientes
        pass

# Instancia global del middleware
notification_middleware = NotificationMiddleware()