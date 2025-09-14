"""
Servicio de gestión de notificaciones WhatsApp
Maneja la creación, programación y envío de notificaciones
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import uuid

import pytz
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc

from app.core.database import get_db
from app.models.whatsapp_notifications import (
    WhatsAppNotificacionesDB, WhatsAppContactosDB, WhatsAppPlantillasMensajesDB,
    WhatsAppConfiguracionHorariosDB, WhatsAppHistorialNotificacionesDB,
    WhatsAppMetricasDiariasDB, EventoTrigger, EstadoNotificacion, TipoEnvio
)
from app.services.whatsapp_service import whatsapp_service
from app.utils.exceptions import ValidationError, NotificationError

logger = logging.getLogger(__name__)

class NotificationService:
    """Servicio principal para gestión de notificaciones WhatsApp"""
    
    def __init__(self):
        self.whatsapp_service = whatsapp_service
    
    async def create_notification(
        self,
        db: Session,
        valorizacion_id: int,
        evento_trigger: EventoTrigger,
        estado_actual: str,
        estado_anterior: Optional[str] = None,
        variables_extra: Optional[Dict[str, Any]] = None,
        envio_inmediato: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Crea notificaciones automáticas para un evento de valorización
        
        Args:
            db: Sesión de base de datos
            valorizacion_id: ID de la valorización
            evento_trigger: Evento que dispara la notificación
            estado_actual: Estado actual de la valorización
            estado_anterior: Estado anterior (opcional)
            variables_extra: Variables adicionales para la plantilla
            envio_inmediato: Si enviar inmediatamente o programar
            
        Returns:
            Lista de notificaciones creadas
        """
        try:
            # Buscar plantillas activas para este evento
            plantillas = db.query(WhatsAppPlantillasMensajesDB).filter(
                and_(
                    WhatsAppPlantillasMensajesDB.evento_trigger == evento_trigger.value,
                    WhatsAppPlantillasMensajesDB.estado_valorizacion == estado_actual,
                    WhatsAppPlantillasMensajesDB.activo == True
                )
            ).all()
            
            if not plantillas:
                logger.info(f"No hay plantillas activas para evento {evento_trigger} - estado {estado_actual}")
                return []
            
            notificaciones_creadas = []
            
            for plantilla in plantillas:
                # Buscar contactos para esta plantilla
                contactos = await self._get_contacts_for_template(db, plantilla, valorizacion_id)
                
                for contacto in contactos:
                    try:
                        # Crear notificación individual
                        notification_data = await self._create_individual_notification(
                            db, plantilla, contacto, valorizacion_id, 
                            evento_trigger, estado_actual, estado_anterior,
                            variables_extra, envio_inmediato
                        )
                        notificaciones_creadas.append(notification_data)
                        
                    except Exception as e:
                        logger.error(f"Error creando notificación para contacto {contacto.id}: {str(e)}")
                        continue
            
            db.commit()
            logger.info(f"Creadas {len(notificaciones_creadas)} notificaciones para evento {evento_trigger}")
            return notificaciones_creadas
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error creando notificaciones: {str(e)}")
            raise NotificationError(f"Error creando notificaciones: {str(e)}")
    
    async def _get_contacts_for_template(
        self,
        db: Session,
        plantilla: WhatsAppPlantillasMensajesDB,
        valorizacion_id: int
    ) -> List[WhatsAppContactosDB]:
        """
        Obtiene contactos que deben recibir notificaciones para una plantilla
        
        Args:
            db: Sesión de base de datos
            plantilla: Plantilla de mensaje
            valorizacion_id: ID de la valorización
            
        Returns:
            Lista de contactos
        """
        # TODO: Aquí necesitarías obtener la información de la valorización
        # para determinar la empresa_id correspondiente
        # Por ahora, simulamos que tenemos esta información
        
        # Filtros base para contactos activos
        filters = [
            WhatsAppContactosDB.activo == True,
            WhatsAppContactosDB.recibe_notificaciones == True
        ]
        
        # Filtrar por tipo de destinatario
        if plantilla.tipo_destinatario == "CONTRATISTA":
            filters.append(WhatsAppContactosDB.tipo_contacto == "CONTRATISTA")
        elif plantilla.tipo_destinatario == "COORDINADOR_INTERNO":
            filters.append(WhatsAppContactosDB.tipo_contacto == "COORDINADOR_INTERNO")
        # Si es "AMBOS", no filtrar por tipo
        
        # Filtrar por eventos suscritos (JSON contains)
        # TODO: Implementar filtro JSON más robusto
        filters.append(
            WhatsAppContactosDB.eventos_suscritos.like(f'%"{plantilla.evento_trigger}"%')
        )
        
        contactos = db.query(WhatsAppContactosDB).filter(and_(*filters)).all()
        
        # Filtrar contactos que ya tienen configuración de horarios
        contactos_validos = []
        for contacto in contactos:
            # Validar número telefónico
            is_valid, formatted_phone, error = self.whatsapp_service.validate_phone_number(contacto.telefono)
            if is_valid:
                contactos_validos.append(contacto)
            else:
                logger.warning(f"Contacto {contacto.id} con número inválido: {error}")
        
        return contactos_validos
    
    async def _create_individual_notification(
        self,
        db: Session,
        plantilla: WhatsAppPlantillasMensajesDB,
        contacto: WhatsAppContactosDB,
        valorizacion_id: int,
        evento_trigger: EventoTrigger,
        estado_actual: str,
        estado_anterior: Optional[str],
        variables_extra: Optional[Dict[str, Any]],
        envio_inmediato: bool
    ) -> Dict[str, Any]:
        """
        Crea una notificación individual
        """
        # Generar código único para la notificación
        codigo_notificacion = f"WA-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        
        # Preparar variables para renderizar el mensaje
        variables = await self._prepare_template_variables(
            db, valorizacion_id, contacto, estado_actual, estado_anterior, variables_extra
        )
        
        # Renderizar mensaje
        mensaje_renderizado = self.whatsapp_service.render_message_template(
            plantilla.mensaje_texto, variables
        )
        
        asunto_renderizado = None
        if plantilla.asunto:
            asunto_renderizado = self.whatsapp_service.render_message_template(
                plantilla.asunto, variables
            )
        
        # Determinar fecha de programación
        fecha_programada = None
        tipo_envio = TipoEnvio.INMEDIATO
        
        if not envio_inmediato or not plantilla.es_inmediato:
            fecha_programada = await self._calculate_scheduled_time(db, contacto.horario_configuracion_id)
            tipo_envio = TipoEnvio.PROGRAMADO
        
        # Crear registro en base de datos
        notification_db = WhatsAppNotificacionesDB(
            codigo_notificacion=codigo_notificacion,
            valorizacion_id=valorizacion_id,
            plantilla_id=plantilla.id,
            contacto_id=contacto.id,
            horario_configuracion_id=contacto.horario_configuracion_id,
            evento_trigger=evento_trigger.value,
            estado_anterior=estado_anterior,
            estado_actual=estado_actual,
            fecha_evento=datetime.now(),
            asunto_renderizado=asunto_renderizado,
            mensaje_renderizado=mensaje_renderizado,
            variables_utilizadas=json.dumps(variables),
            tipo_envio=tipo_envio.value,
            fecha_programada=fecha_programada,
            prioridad=plantilla.prioridad,
            estado=EstadoNotificacion.PENDIENTE.value if envio_inmediato else EstadoNotificacion.PROGRAMADA.value
        )
        
        db.add(notification_db)
        db.flush()  # Para obtener el ID
        
        # Crear entrada inicial en historial
        historial = WhatsAppHistorialNotificacionesDB(
            notificacion_id=notification_db.id,
            estado_anterior=None,
            estado_nuevo=notification_db.estado,
            motivo_cambio="Notificación creada",
            descripcion_cambio=f"Notificación creada para evento {evento_trigger.value}"
        )
        db.add(historial)
        
        return {
            "id": notification_db.id,
            "codigo_notificacion": codigo_notificacion,
            "contacto_nombre": contacto.nombre,
            "contacto_telefono": contacto.telefono,
            "mensaje": mensaje_renderizado[:100] + "..." if len(mensaje_renderizado) > 100 else mensaje_renderizado,
            "estado": notification_db.estado,
            "fecha_programada": fecha_programada
        }
    
    async def _prepare_template_variables(
        self,
        db: Session,
        valorizacion_id: int,
        contacto: WhatsAppContactosDB,
        estado_actual: str,
        estado_anterior: Optional[str],
        variables_extra: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Prepara variables para renderizar plantillas de mensaje
        """
        # Variables base
        variables = {
            "contacto_nombre": contacto.nombre,
            "contacto_cargo": contacto.cargo or "",
            "estado_actual": estado_actual,
            "estado_anterior": estado_anterior or "",
            "fecha_cambio": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "valorizacion_id": valorizacion_id
        }
        
        # TODO: Aquí deberías obtener datos reales de la valorización
        # Por ahora usamos datos simulados
        variables.update({
            "obra_nombre": f"Obra #{valorizacion_id}",
            "empresa_razon_social": contacto.empresa.razon_social if contacto.empresa else "Empresa",
            "valorizacion_numero": f"VAL-{valorizacion_id:06d}",
            "valorizacion_periodo": datetime.now().strftime("%m/%Y"),
            "monto_total": "0.00",
            "observaciones": ""
        })
        
        # Agregar variables extras si las hay
        if variables_extra:
            variables.update(variables_extra)
        
        return variables
    
    async def _calculate_scheduled_time(
        self, 
        db: Session, 
        horario_configuracion_id: int
    ) -> datetime:
        """
        Calcula la próxima fecha/hora de envío según configuración de horarios
        """
        config = db.query(WhatsAppConfiguracionHorariosDB).filter(
            WhatsAppConfiguracionHorariosDB.id == horario_configuracion_id
        ).first()
        
        if not config:
            # Si no hay configuración, enviar en 5 minutos
            return datetime.now() + timedelta(minutes=5)
        
        try:
            tz = pytz.timezone(config.zona_horaria)
            now = datetime.now(tz)
            
            # Parsear días laborables
            dias_laborables = json.loads(config.dias_laborables)
            nombres_dias = ["LUNES", "MARTES", "MIERCOLES", "JUEVES", "VIERNES", "SABADO", "DOMINGO"]
            dias_laborables_numeros = [nombres_dias.index(dia) for dia in dias_laborables if dia in nombres_dias]
            
            # Encontrar el próximo día laborable
            dias_a_sumar = 0
            while True:
                fecha_candidata = now + timedelta(days=dias_a_sumar)
                if fecha_candidata.weekday() in dias_laborables_numeros:
                    # Verificar si es hoy y aún estamos en horario
                    if dias_a_sumar == 0:
                        hora_fin = datetime.combine(fecha_candidata.date(), config.hora_fin_envios)
                        hora_fin = tz.localize(hora_fin)
                        if now < hora_fin:
                            # Podemos enviar hoy, usar hora de inicio si aún no hemos llegado
                            hora_inicio = datetime.combine(fecha_candidata.date(), config.hora_inicio_envios)
                            hora_inicio = tz.localize(hora_inicio)
                            return max(now + timedelta(minutes=5), hora_inicio).replace(tzinfo=None)
                    else:
                        # Enviar mañana en hora de inicio
                        hora_inicio = datetime.combine(fecha_candidata.date(), config.hora_inicio_envios)
                        return tz.localize(hora_inicio).replace(tzinfo=None)
                
                dias_a_sumar += 1
                if dias_a_sumar > 7:  # Evitar loop infinito
                    break
            
            # Fallback: enviar en 5 minutos
            return datetime.now() + timedelta(minutes=5)
            
        except Exception as e:
            logger.error(f"Error calculando fecha programada: {str(e)}")
            return datetime.now() + timedelta(minutes=5)
    
    async def send_pending_notifications(self, db: Session, limit: int = 100) -> Dict[str, Any]:
        """
        Procesa y envía notificaciones pendientes
        
        Args:
            db: Sesión de base de datos
            limit: Máximo número de notificaciones a procesar
            
        Returns:
            Dict con estadísticas del procesamiento
        """
        # Obtener notificaciones pendientes ordenadas por prioridad y fecha
        notifications = db.query(WhatsAppNotificacionesDB).join(
            WhatsAppContactosDB
        ).filter(
            and_(
                WhatsAppNotificacionesDB.estado.in_([EstadoNotificacion.PENDIENTE.value, EstadoNotificacion.PROGRAMADA.value]),
                WhatsAppContactosDB.activo == True,
                WhatsAppNotificacionesDB.intentos_envio < WhatsAppNotificacionesDB.max_reintentos,
                or_(
                    WhatsAppNotificacionesDB.fecha_programada.is_(None),
                    WhatsAppNotificacionesDB.fecha_programada <= datetime.now()
                )
            )
        ).order_by(
            WhatsAppNotificacionesDB.prioridad.asc(),
            WhatsAppNotificacionesDB.fecha_programada.asc()
        ).limit(limit).all()
        
        stats = {
            "processed": 0,
            "sent": 0,
            "failed": 0,
            "deferred": 0
        }
        
        for notification in notifications:
            stats["processed"] += 1
            
            try:
                # Verificar si estamos en horario laboral para esta notificación
                if not await self._should_send_now(db, notification):
                    stats["deferred"] += 1
                    continue
                
                # Actualizar estado a "enviando"
                await self._update_notification_status(
                    db, notification, EstadoNotificacion.ENVIANDO, 
                    "Iniciando envío de mensaje"
                )
                
                # Validar y formatear número telefónico
                is_valid, formatted_phone, error = self.whatsapp_service.validate_phone_number(
                    notification.contacto.telefono
                )
                
                if not is_valid:
                    await self._handle_notification_error(
                        db, notification, f"Número telefónico inválido: {error}"
                    )
                    stats["failed"] += 1
                    continue
                
                # Enviar mensaje
                result = await self.whatsapp_service.send_message_with_retry(
                    formatted_phone,
                    notification.mensaje_renderizado
                )
                
                if result.get("success"):
                    # Éxito
                    notification.whatsapp_message_id = result.get("message_id")
                    notification.fecha_envio = datetime.now()
                    notification.whatsapp_status = "sent"
                    notification.metadata_whatsapp = json.dumps(result.get("response", {}))
                    
                    await self._update_notification_status(
                        db, notification, EstadoNotificacion.ENVIADA,
                        "Mensaje enviado exitosamente"
                    )
                    
                    stats["sent"] += 1
                    logger.info(f"Notificación {notification.codigo_notificacion} enviada exitosamente")
                    
                else:
                    # Error en el envío
                    await self._handle_notification_error(
                        db, notification, result.get("error", "Error desconocido")
                    )
                    stats["failed"] += 1
                
            except Exception as e:
                logger.error(f"Error procesando notificación {notification.id}: {str(e)}")
                await self._handle_notification_error(db, notification, str(e))
                stats["failed"] += 1
        
        db.commit()
        return stats
    
    async def _should_send_now(self, db: Session, notification: WhatsAppNotificacionesDB) -> bool:
        """
        Verifica si una notificación debe enviarse ahora según horarios
        """
        # Si es envío inmediato y de alta prioridad, enviar siempre
        if notification.tipo_envio == TipoEnvio.INMEDIATO.value and notification.prioridad <= 2:
            return True
        
        # Verificar horarios laborables según configuración del contacto
        config = notification.horario_configuracion
        if not config or not config.activo:
            return True  # Si no hay configuración, enviar
        
        try:
            tz = pytz.timezone(config.zona_horaria)
            now = datetime.now(tz)
            
            # Verificar día laborable
            dias_laborables = json.loads(config.dias_laborables)
            nombres_dias = ["LUNES", "MARTES", "MIERCOLES", "JUEVES", "VIERNES", "SABADO", "DOMINGO"]
            if nombres_dias[now.weekday()] not in dias_laborables:
                return False
            
            # Verificar horario
            current_time = now.time()
            return config.hora_inicio_envios <= current_time <= config.hora_fin_envios
            
        except Exception as e:
            logger.error(f"Error verificando horarios para notificación {notification.id}: {str(e)}")
            return True  # En caso de error, permitir envío
    
    async def _update_notification_status(
        self,
        db: Session,
        notification: WhatsAppNotificacionesDB,
        nuevo_estado: EstadoNotificacion,
        motivo: str
    ):
        """
        Actualiza el estado de una notificación y registra en historial
        """
        estado_anterior = notification.estado
        notification.estado = nuevo_estado.value
        notification.fecha_cambio_estado = datetime.now()
        
        # Registrar en historial
        historial = WhatsAppHistorialNotificacionesDB(
            notificacion_id=notification.id,
            estado_anterior=estado_anterior,
            estado_nuevo=nuevo_estado.value,
            motivo_cambio=motivo,
            fecha_cambio=datetime.now()
        )
        db.add(historial)
    
    async def _handle_notification_error(
        self,
        db: Session,
        notification: WhatsAppNotificacionesDB,
        error_message: str
    ):
        """
        Maneja errores en notificaciones
        """
        notification.intentos_envio += 1
        notification.ultimo_error = error_message
        notification.fecha_ultimo_error = datetime.now()
        
        if notification.intentos_envio >= notification.max_reintentos:
            await self._update_notification_status(
                db, notification, EstadoNotificacion.ERROR,
                f"Máximo de reintentos alcanzado: {error_message}"
            )
        else:
            await self._update_notification_status(
                db, notification, EstadoNotificacion.PENDIENTE,
                f"Error en intento {notification.intentos_envio}: {error_message}"
            )
    
    async def process_webhook_updates(
        self,
        db: Session,
        webhook_payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Procesa actualizaciones recibidas via webhook de WhatsApp
        """
        events = self.whatsapp_service.parse_webhook_payload(webhook_payload)
        processed_count = 0
        
        for event in events:
            if event["type"] == "message_status":
                message_id = event.get("message_id")
                status = event.get("status")
                
                if message_id and status:
                    # Buscar notificación por message_id
                    notification = db.query(WhatsAppNotificacionesDB).filter(
                        WhatsAppNotificacionesDB.whatsapp_message_id == message_id
                    ).first()
                    
                    if notification:
                        await self._update_notification_from_webhook(db, notification, event)
                        processed_count += 1
        
        db.commit()
        return {"processed_events": processed_count}
    
    async def _update_notification_from_webhook(
        self,
        db: Session,
        notification: WhatsAppNotificacionesDB,
        event: Dict[str, Any]
    ):
        """
        Actualiza notificación basada en evento de webhook
        """
        status = event.get("status")
        timestamp = event.get("timestamp")
        
        # Mapear estados de WhatsApp a nuestros estados
        status_mapping = {
            "sent": EstadoNotificacion.ENVIADA,
            "delivered": EstadoNotificacion.ENTREGADA,
            "read": EstadoNotificacion.LEIDA,
            "failed": EstadoNotificacion.ERROR
        }
        
        new_status = status_mapping.get(status)
        if not new_status:
            return
        
        # Actualizar timestamps correspondientes
        if status == "delivered" and not notification.fecha_entrega:
            notification.fecha_entrega = datetime.fromtimestamp(int(timestamp))
        elif status == "read" and not notification.fecha_lectura:
            notification.fecha_lectura = datetime.fromtimestamp(int(timestamp))
        
        # Actualizar estado si es progresivo
        current_status = notification.estado
        if self._should_update_status(current_status, new_status.value):
            await self._update_notification_status(
                db, notification, new_status,
                f"Actualización via webhook: {status}"
            )
            
            notification.whatsapp_status = status
            notification.whatsapp_timestamp = datetime.fromtimestamp(int(timestamp))
    
    def _should_update_status(self, current: str, new: str) -> bool:
        """
        Determina si se debe actualizar el estado (solo permite progresión)
        """
        status_order = [
            EstadoNotificacion.PENDIENTE.value,
            EstadoNotificacion.PROGRAMADA.value,
            EstadoNotificacion.ENVIANDO.value,
            EstadoNotificacion.ENVIADA.value,
            EstadoNotificacion.ENTREGADA.value,
            EstadoNotificacion.LEIDA.value
        ]
        
        try:
            current_index = status_order.index(current)
            new_index = status_order.index(new)
            return new_index > current_index
        except ValueError:
            return False
    
    async def get_notification_metrics(
        self,
        db: Session,
        fecha_inicio: Optional[datetime] = None,
        fecha_fin: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Obtiene métricas de notificaciones para un período
        """
        if not fecha_inicio:
            fecha_inicio = datetime.now() - timedelta(days=7)
        if not fecha_fin:
            fecha_fin = datetime.now()
        
        # Consultas base
        base_query = db.query(WhatsAppNotificacionesDB).filter(
            WhatsAppNotificacionesDB.created_at.between(fecha_inicio, fecha_fin)
        )
        
        # Contadores por estado
        total = base_query.count()
        enviadas = base_query.filter(WhatsAppNotificacionesDB.estado == EstadoNotificacion.ENVIADA.value).count()
        entregadas = base_query.filter(WhatsAppNotificacionesDB.estado == EstadoNotificacion.ENTREGADA.value).count()
        leidas = base_query.filter(WhatsAppNotificacionesDB.estado == EstadoNotificacion.LEIDA.value).count()
        errores = base_query.filter(WhatsAppNotificacionesDB.estado == EstadoNotificacion.ERROR.value).count()
        
        # Métricas por evento
        eventos_stats = db.query(
            WhatsAppNotificacionesDB.evento_trigger,
            func.count().label('total')
        ).filter(
            WhatsAppNotificacionesDB.created_at.between(fecha_inicio, fecha_fin)
        ).group_by(WhatsAppNotificacionesDB.evento_trigger).all()
        
        # Calcular tasas
        tasa_exito = (enviadas + entregadas + leidas) / total * 100 if total > 0 else 0
        tasa_entrega = entregadas / enviadas * 100 if enviadas > 0 else 0
        tasa_lectura = leidas / entregadas * 100 if entregadas > 0 else 0
        
        return {
            "periodo": {
                "inicio": fecha_inicio.isoformat(),
                "fin": fecha_fin.isoformat()
            },
            "totales": {
                "total": total,
                "enviadas": enviadas,
                "entregadas": entregadas,
                "leidas": leidas,
                "errores": errores
            },
            "tasas": {
                "exito_porcentaje": round(tasa_exito, 2),
                "entrega_porcentaje": round(tasa_entrega, 2),
                "lectura_porcentaje": round(tasa_lectura, 2)
            },
            "por_evento": {evento: total for evento, total in eventos_stats}
        }

# Instancia global del servicio
notification_service = NotificationService()