"""
Servicio de programación y procesamiento de tareas en background
Maneja el envío programado de notificaciones y tareas de mantenimiento
"""

import asyncio
import logging
from datetime import datetime, timedelta, date
from typing import Dict, Any, Optional
import json

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc

from app.core.database import get_db
from app.core.config import settings
from app.models.whatsapp_notifications import (
    WhatsAppNotificacionesDB, WhatsAppMetricasDiariasDB,
    EstadoNotificacion, EventoTrigger
)
from app.services.notification_service import notification_service

logger = logging.getLogger(__name__)

class SchedulerService:
    """Servicio para manejo de tareas programadas y background"""
    
    def __init__(self):
        self.is_running = False
        self.tasks = {}
        self.notification_service = notification_service
    
    async def start_scheduler(self):
        """Inicia el programador de tareas en background"""
        if self.is_running:
            logger.warning("Scheduler ya está ejecutándose")
            return
        
        if not settings.BACKGROUND_TASKS_ENABLED:
            logger.info("Tareas en background deshabilitadas por configuración")
            return
        
        self.is_running = True
        logger.info("Iniciando scheduler de tareas en background")
        
        # Programar tareas principales
        self.tasks['notification_processor'] = asyncio.create_task(
            self._run_notification_processor()
        )
        self.tasks['metrics_calculator'] = asyncio.create_task(
            self._run_metrics_calculator()
        )
        self.tasks['cleanup_old_data'] = asyncio.create_task(
            self._run_cleanup_task()
        )
        
        logger.info(f"Scheduler iniciado con {len(self.tasks)} tareas")
    
    async def stop_scheduler(self):
        """Detiene el programador de tareas"""
        if not self.is_running:
            return
        
        logger.info("Deteniendo scheduler de tareas...")
        self.is_running = False
        
        # Cancelar todas las tareas
        for task_name, task in self.tasks.items():
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    logger.info(f"Tarea {task_name} cancelada")
        
        self.tasks.clear()
        logger.info("Scheduler detenido")
    
    async def _run_notification_processor(self):
        """
        Tarea principal: procesa notificaciones pendientes
        Se ejecuta cada X segundos según configuración
        """
        while self.is_running:
            try:
                db = next(get_db())
                
                # Procesar notificaciones pendientes
                stats = await self.notification_service.send_pending_notifications(db, limit=50)
                
                if stats["processed"] > 0:
                    logger.info(
                        f"Procesadas {stats['processed']} notificaciones: "
                        f"{stats['sent']} enviadas, {stats['failed']} fallidas, "
                        f"{stats['deferred']} diferidas"
                    )
                
                db.close()
                
            except Exception as e:
                logger.error(f"Error en notification_processor: {str(e)}")
            
            # Esperar intervalo configurado
            await asyncio.sleep(settings.BACKGROUND_TASKS_INTERVAL_SECONDS)
    
    async def _run_metrics_calculator(self):
        """
        Tarea de cálculo de métricas diarias
        Se ejecuta cada 4 horas
        """
        while self.is_running:
            try:
                db = next(get_db())
                
                # Calcular métricas para ayer y hoy
                await self._calculate_daily_metrics(db, date.today() - timedelta(days=1))
                await self._calculate_daily_metrics(db, date.today())
                
                db.close()
                
            except Exception as e:
                logger.error(f"Error en metrics_calculator: {str(e)}")
            
            # Esperar 4 horas
            await asyncio.sleep(4 * 3600)
    
    async def _run_cleanup_task(self):
        """
        Tarea de limpieza de datos antiguos
        Se ejecuta cada 24 horas
        """
        while self.is_running:
            try:
                db = next(get_db())
                
                # Limpiar notificaciones muy antiguas (más de 90 días)
                cleanup_stats = await self._cleanup_old_notifications(db)
                
                if cleanup_stats["deleted"] > 0:
                    logger.info(f"Limpieza completada: {cleanup_stats}")
                
                db.close()
                
            except Exception as e:
                logger.error(f"Error en cleanup_task: {str(e)}")
            
            # Esperar 24 horas
            await asyncio.sleep(24 * 3600)
    
    async def _calculate_daily_metrics(self, db: Session, fecha_metrica: date):
        """
        Calcula y guarda métricas diarias para una fecha específica
        
        Args:
            db: Sesión de base de datos
            fecha_metrica: Fecha para la cual calcular métricas
        """
        try:
            # Verificar si ya existen métricas para esta fecha
            existing_metrics = db.query(WhatsAppMetricasDiariasDB).filter(
                WhatsAppMetricasDiariasDB.fecha_metrica == fecha_metrica
            ).first()
            
            # Fecha de inicio y fin para la consulta
            fecha_inicio = datetime.combine(fecha_metrica, datetime.min.time())
            fecha_fin = fecha_inicio + timedelta(days=1)
            
            # Consultas base para el día
            base_query = db.query(WhatsAppNotificacionesDB).filter(
                and_(
                    WhatsAppNotificacionesDB.created_at >= fecha_inicio,
                    WhatsAppNotificacionesDB.created_at < fecha_fin
                )
            )
            
            # Contadores por estado
            total_pendientes = base_query.filter(
                WhatsAppNotificacionesDB.estado == EstadoNotificacion.PENDIENTE.value
            ).count()
            
            total_enviadas = base_query.filter(
                WhatsAppNotificacionesDB.estado.in_([
                    EstadoNotificacion.ENVIADA.value,
                    EstadoNotificacion.ENTREGADA.value,
                    EstadoNotificacion.LEIDA.value
                ])
            ).count()
            
            total_entregadas = base_query.filter(
                WhatsAppNotificacionesDB.estado.in_([
                    EstadoNotificacion.ENTREGADA.value,
                    EstadoNotificacion.LEIDA.value
                ])
            ).count()
            
            total_leidas = base_query.filter(
                WhatsAppNotificacionesDB.estado == EstadoNotificacion.LEIDA.value
            ).count()
            
            total_errores = base_query.filter(
                WhatsAppNotificacionesDB.estado == EstadoNotificacion.ERROR.value
            ).count()
            
            total_canceladas = base_query.filter(
                WhatsAppNotificacionesDB.estado == EstadoNotificacion.CANCELADA.value
            ).count()
            
            # Contadores por tipo de evento
            eventos_counts = db.query(
                WhatsAppNotificacionesDB.evento_trigger,
                func.count().label('total')
            ).filter(
                and_(
                    WhatsAppNotificacionesDB.created_at >= fecha_inicio,
                    WhatsAppNotificacionesDB.created_at < fecha_fin
                )
            ).group_by(WhatsAppNotificacionesDB.evento_trigger).all()
            
            # Inicializar contadores de eventos
            eventos_dict = {evento.value: 0 for evento in EventoTrigger}
            for evento, count in eventos_counts:
                eventos_dict[evento] = count
            
            # Calcular métricas de rendimiento
            total_notificaciones = base_query.count()
            
            # Tiempo promedio de envío (desde creación hasta envío)
            tiempo_promedio_envio = None
            if total_enviadas > 0:
                enviadas_con_tiempo = db.query(
                    func.avg(
                        func.julianday(WhatsAppNotificacionesDB.fecha_envio) - 
                        func.julianday(WhatsAppNotificacionesDB.created_at)
                    ) * 86400  # Convertir días a segundos
                ).filter(
                    and_(
                        WhatsAppNotificacionesDB.created_at >= fecha_inicio,
                        WhatsAppNotificacionesDB.created_at < fecha_fin,
                        WhatsAppNotificacionesDB.fecha_envio.isnot(None)
                    )
                ).scalar()
                
                if enviadas_con_tiempo:
                    tiempo_promedio_envio = int(enviadas_con_tiempo)
            
            # Tiempo promedio de entrega (desde envío hasta entrega)
            tiempo_promedio_entrega = None
            if total_entregadas > 0:
                entregadas_con_tiempo = db.query(
                    func.avg(
                        func.julianday(WhatsAppNotificacionesDB.fecha_entrega) - 
                        func.julianday(WhatsAppNotificacionesDB.fecha_envio)
                    ) * 86400  # Convertir días a segundos
                ).filter(
                    and_(
                        WhatsAppNotificacionesDB.created_at >= fecha_inicio,
                        WhatsAppNotificacionesDB.created_at < fecha_fin,
                        WhatsAppNotificacionesDB.fecha_entrega.isnot(None),
                        WhatsAppNotificacionesDB.fecha_envio.isnot(None)
                    )
                ).scalar()
                
                if entregadas_con_tiempo:
                    tiempo_promedio_entrega = int(entregadas_con_tiempo)
            
            # Calcular tasas de éxito y error
            tasa_exito_porcentaje = 0.0
            tasa_error_porcentaje = 0.0
            
            if total_notificaciones > 0:
                tasa_exito_porcentaje = (total_enviadas / total_notificaciones) * 100
                tasa_error_porcentaje = (total_errores / total_notificaciones) * 100
            
            # Crear o actualizar métricas
            if existing_metrics:
                # Actualizar métricas existentes
                existing_metrics.total_pendientes = total_pendientes
                existing_metrics.total_enviadas = total_enviadas
                existing_metrics.total_entregadas = total_entregadas
                existing_metrics.total_leidas = total_leidas
                existing_metrics.total_errores = total_errores
                existing_metrics.total_canceladas = total_canceladas
                existing_metrics.total_recibidas = eventos_dict.get('RECIBIDA', 0)
                existing_metrics.total_en_revision = eventos_dict.get('EN_REVISION', 0)
                existing_metrics.total_observadas = eventos_dict.get('OBSERVADA', 0)
                existing_metrics.total_aprobadas = eventos_dict.get('APROBADA', 0)
                existing_metrics.total_rechazadas = eventos_dict.get('RECHAZADA', 0)
                existing_metrics.tiempo_promedio_envio_segundos = tiempo_promedio_envio
                existing_metrics.tiempo_promedio_entrega_segundos = tiempo_promedio_entrega
                existing_metrics.tasa_exito_porcentaje = round(tasa_exito_porcentaje, 2)
                existing_metrics.tasa_error_porcentaje = round(tasa_error_porcentaje, 2)
                existing_metrics.updated_at = datetime.now()
            else:
                # Crear nuevas métricas
                new_metrics = WhatsAppMetricasDiariasDB(
                    fecha_metrica=fecha_metrica,
                    total_pendientes=total_pendientes,
                    total_enviadas=total_enviadas,
                    total_entregadas=total_entregadas,
                    total_leidas=total_leidas,
                    total_errores=total_errores,
                    total_canceladas=total_canceladas,
                    total_recibidas=eventos_dict.get('RECIBIDA', 0),
                    total_en_revision=eventos_dict.get('EN_REVISION', 0),
                    total_observadas=eventos_dict.get('OBSERVADA', 0),
                    total_aprobadas=eventos_dict.get('APROBADA', 0),
                    total_rechazadas=eventos_dict.get('RECHAZADA', 0),
                    tiempo_promedio_envio_segundos=tiempo_promedio_envio,
                    tiempo_promedio_entrega_segundos=tiempo_promedio_entrega,
                    tasa_exito_porcentaje=round(tasa_exito_porcentaje, 2),
                    tasa_error_porcentaje=round(tasa_error_porcentaje, 2)
                )
                db.add(new_metrics)
            
            db.commit()
            logger.info(f"Métricas calculadas para {fecha_metrica}: {total_notificaciones} notificaciones")
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error calculando métricas para {fecha_metrica}: {str(e)}")
    
    async def _cleanup_old_notifications(self, db: Session, days_to_keep: int = 90) -> Dict[str, int]:
        """
        Limpia notificaciones y datos antiguos
        
        Args:
            db: Sesión de base de datos
            days_to_keep: Días de retención de datos
            
        Returns:
            Dict con estadísticas de limpieza
        """
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        stats = {"deleted": 0, "archived": 0}
        
        try:
            # Eliminar notificaciones muy antiguas que ya están procesadas
            old_notifications = db.query(WhatsAppNotificacionesDB).filter(
                and_(
                    WhatsAppNotificacionesDB.created_at < cutoff_date,
                    WhatsAppNotificacionesDB.estado.in_([
                        EstadoNotificacion.ENVIADA.value,
                        EstadoNotificacion.ENTREGADA.value,
                        EstadoNotificacion.LEIDA.value,
                        EstadoNotificacion.ERROR.value,
                        EstadoNotificacion.CANCELADA.value
                    ])
                )
            ).all()
            
            # Antes de eliminar, podríamos archivar información importante
            for notification in old_notifications:
                # Aquí se podría implementar lógica de archivado
                # Por ejemplo, guardar en otra tabla o exportar a archivo
                stats["archived"] += 1
            
            # Eliminar notificaciones (el historial se elimina por cascada)
            deleted_count = db.query(WhatsAppNotificacionesDB).filter(
                and_(
                    WhatsAppNotificacionesDB.created_at < cutoff_date,
                    WhatsAppNotificacionesDB.estado.in_([
                        EstadoNotificacion.ENVIADA.value,
                        EstadoNotificacion.ENTREGADA.value,
                        EstadoNotificacion.LEIDA.value,
                        EstadoNotificacion.ERROR.value,
                        EstadoNotificacion.CANCELADA.value
                    ])
                )
            ).delete(synchronize_session=False)
            
            stats["deleted"] = deleted_count
            
            # Limpiar métricas diarias muy antiguas (más de 1 año)
            old_metrics_date = datetime.now() - timedelta(days=365)
            deleted_metrics = db.query(WhatsAppMetricasDiariasDB).filter(
                WhatsAppMetricasDiariasDB.fecha_metrica < old_metrics_date.date()
            ).delete(synchronize_session=False)
            
            db.commit()
            
            logger.info(f"Limpieza completada: {deleted_count} notificaciones, {deleted_metrics} métricas eliminadas")
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error en limpieza de datos: {str(e)}")
        
        return stats
    
    async def process_scheduled_notifications(self, db: Session) -> Dict[str, int]:
        """
        Procesa notificaciones programadas que ya pueden enviarse
        
        Args:
            db: Sesión de base de datos
            
        Returns:
            Dict con estadísticas de procesamiento
        """
        # Esta funcionalidad ya está incluida en send_pending_notifications
        # pero la dejamos por separado para poder ser llamada manualmente
        return await self.notification_service.send_pending_notifications(db, limit=100)
    
    async def retry_failed_notifications(self, db: Session, hours_ago: int = 2) -> Dict[str, int]:
        """
        Reintenta notificaciones fallidas recientes
        
        Args:
            db: Sesión de base de datos  
            hours_ago: Horas hacia atrás para buscar notificaciones fallidas
            
        Returns:
            Dict con estadísticas de reintentos
        """
        cutoff_time = datetime.now() - timedelta(hours=hours_ago)
        
        # Buscar notificaciones con errores recientes que aún pueden reintentarse
        failed_notifications = db.query(WhatsAppNotificacionesDB).filter(
            and_(
                WhatsAppNotificacionesDB.estado == EstadoNotificacion.ERROR.value,
                WhatsAppNotificacionesDB.fecha_ultimo_error > cutoff_time,
                WhatsAppNotificacionesDB.intentos_envio < WhatsAppNotificacionesDB.max_reintentos
            )
        ).all()
        
        stats = {"processed": 0, "retried": 0}
        
        for notification in failed_notifications:
            try:
                # Resetear a pendiente para que el processor lo tome
                notification.estado = EstadoNotificacion.PENDIENTE.value
                notification.fecha_cambio_estado = datetime.now()
                
                stats["processed"] += 1
                
            except Exception as e:
                logger.error(f"Error reintentando notificación {notification.id}: {str(e)}")
        
        db.commit()
        return stats
    
    def get_scheduler_status(self) -> Dict[str, Any]:
        """
        Obtiene el estado actual del scheduler
        
        Returns:
            Dict con información del estado
        """
        return {
            "is_running": self.is_running,
            "active_tasks": len([t for t in self.tasks.values() if not t.done()]),
            "total_tasks": len(self.tasks),
            "task_status": {
                name: "running" if not task.done() else "completed"
                for name, task in self.tasks.items()
            }
        }
    
    async def force_metrics_calculation(self, db: Session, fecha: Optional[date] = None) -> Dict[str, Any]:
        """
        Fuerza el cálculo de métricas para una fecha específica
        
        Args:
            db: Sesión de base de datos
            fecha: Fecha para calcular (default: hoy)
            
        Returns:
            Dict con resultado del cálculo
        """
        if fecha is None:
            fecha = date.today()
        
        try:
            await self._calculate_daily_metrics(db, fecha)
            return {
                "success": True,
                "message": f"Métricas calculadas para {fecha}",
                "fecha": fecha.isoformat()
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "fecha": fecha.isoformat()
            }

# Instancia global del servicio
scheduler_service = SchedulerService()