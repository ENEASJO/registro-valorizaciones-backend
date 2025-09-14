"""
API endpoints para el sistema de notificaciones WhatsApp
"""

import json
import logging
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func

from app.core.database import get_db
from app.models.whatsapp_notifications import (
    WhatsAppNotificacionesDB, WhatsAppContactosDB, WhatsAppPlantillasMensajesDB,
    WhatsAppConfiguracionHorariosDB, WhatsAppMetricasDiariasDB,
    WhatsAppNotificacionCreate, WhatsAppNotificacionResponse,
    WhatsAppContactoCreate, WhatsAppContactoResponse,
    WhatsAppPlantillaMensajeCreate, WhatsAppPlantillaMensajeResponse,
    WhatsAppNotificacionListResponse, WhatsAppEstadisticasResponse,
    EventoTrigger, EstadoNotificacion, TipoEnvio
)
from app.services.notification_service import notification_service
from app.services.whatsapp_service import whatsapp_service
from app.services.scheduler_service import scheduler_service
from app.utils.exceptions import ValidationError, NotificationError, WhatsAppError
from app.utils.response_handler import success_response, error_response

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/notifications", tags=["Notificaciones WhatsApp"])

# =====================================================================
# ENDPOINTS PRINCIPALES DE NOTIFICACIONES
# =====================================================================

@router.post("/", response_model=Dict[str, Any])
async def create_notification(
    notification_data: WhatsAppNotificacionCreate,
    db: Session = Depends(get_db)
):
    """
    Crear notificación manual de WhatsApp
    
    Permite crear y enviar una notificación específica manualmente
    """
    try:
        # Validar que existan los registros relacionados
        plantilla = db.query(WhatsAppPlantillasMensajesDB).filter(
            and_(
                WhatsAppPlantillasMensajesDB.id == notification_data.plantilla_id,
                WhatsAppPlantillasMensajesDB.activo == True
            )
        ).first()
        
        if not plantilla:
            raise ValidationError("Plantilla no encontrada o inactiva")
        
        contacto = db.query(WhatsAppContactosDB).filter(
            and_(
                WhatsAppContactosDB.id == notification_data.contacto_id,
                WhatsAppContactosDB.activo == True
            )
        ).first()
        
        if not contacto:
            raise ValidationError("Contacto no encontrado o inactivo")
        
        # Crear notificaciones usando el servicio
        notificaciones = await notification_service.create_notification(
            db=db,
            valorizacion_id=notification_data.valorizacion_id,
            evento_trigger=notification_data.evento_trigger,
            estado_actual=notification_data.estado_actual,
            estado_anterior=notification_data.estado_anterior,
            envio_inmediato=(notification_data.tipo_envio == TipoEnvio.INMEDIATO)
        )
        
        return success_response(
            data={
                "notificaciones_creadas": len(notificaciones),
                "notificaciones": notificaciones
            },
            message=f"Notificación creada exitosamente"
        )
        
    except (ValidationError, NotificationError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creando notificación: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.get("/", response_model=WhatsAppNotificacionListResponse)
async def list_notifications(
    pagina: int = Query(1, ge=1, description="Número de página"),
    limite: int = Query(20, ge=1, le=100, description="Elementos por página"),
    estado: Optional[str] = Query(None, description="Filtrar por estado"),
    evento: Optional[str] = Query(None, description="Filtrar por evento"),
    valorizacion_id: Optional[int] = Query(None, description="Filtrar por ID de valorización"),
    fecha_desde: Optional[date] = Query(None, description="Fecha desde (YYYY-MM-DD)"),
    fecha_hasta: Optional[date] = Query(None, description="Fecha hasta (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """
    Listar notificaciones con filtros y paginación
    """
    try:
        # Construir query base
        query = db.query(WhatsAppNotificacionesDB).join(WhatsAppContactosDB).join(
            WhatsAppPlantillasMensajesDB
        )
        
        # Aplicar filtros
        if estado:
            query = query.filter(WhatsAppNotificacionesDB.estado == estado)
        
        if evento:
            query = query.filter(WhatsAppNotificacionesDB.evento_trigger == evento)
        
        if valorizacion_id:
            query = query.filter(WhatsAppNotificacionesDB.valorizacion_id == valorizacion_id)
        
        if fecha_desde:
            fecha_inicio = datetime.combine(fecha_desde, datetime.min.time())
            query = query.filter(WhatsAppNotificacionesDB.created_at >= fecha_inicio)
        
        if fecha_hasta:
            fecha_fin = datetime.combine(fecha_hasta, datetime.max.time())
            query = query.filter(WhatsAppNotificacionesDB.created_at <= fecha_fin)
        
        # Obtener total de registros
        total = query.count()
        
        # Aplicar paginación
        offset = (pagina - 1) * limite
        notificaciones = query.order_by(
            desc(WhatsAppNotificacionesDB.created_at)
        ).offset(offset).limit(limite).all()
        
        # Formatear respuesta
        notificaciones_response = []
        for notif in notificaciones:
            notificaciones_response.append(
                WhatsAppNotificacionResponse(
                    **notif.__dict__,
                    contacto_nombre=notif.contacto.nombre,
                    contacto_telefono=notif.contacto.telefono,
                    plantilla_nombre=notif.plantilla.nombre
                )
            )
        
        total_paginas = (total + limite - 1) // limite
        
        return WhatsAppNotificacionListResponse(
            notificaciones=notificaciones_response,
            total=total,
            pagina=pagina,
            limite=limite,
            total_paginas=total_paginas
        )
        
    except Exception as e:
        logger.error(f"Error listando notificaciones: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.put("/{notification_id}/status", response_model=Dict[str, Any])
async def update_notification_status(
    notification_id: int,
    nuevo_estado: EstadoNotificacion,
    motivo: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Actualizar el estado de una notificación manualmente
    """
    try:
        notification = db.query(WhatsAppNotificacionesDB).filter(
            WhatsAppNotificacionesDB.id == notification_id
        ).first()
        
        if not notification:
            raise HTTPException(status_code=404, detail="Notificación no encontrada")
        
        estado_anterior = notification.estado
        notification.estado = nuevo_estado.value
        notification.fecha_cambio_estado = datetime.now()
        
        # Registrar cambio en historial si el servicio está disponible
        # (implementado en notification_service._update_notification_status)
        
        db.commit()
        
        return success_response(
            data={
                "id": notification_id,
                "estado_anterior": estado_anterior,
                "estado_nuevo": nuevo_estado.value,
                "fecha_cambio": datetime.now().isoformat()
            },
            message="Estado actualizado exitosamente"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error actualizando estado de notificación {notification_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

# =====================================================================
# ENDPOINTS DE MÉTRICAS Y ESTADÍSTICAS
# =====================================================================

@router.get("/metrics", response_model=WhatsAppEstadisticasResponse)
async def get_notification_metrics(
    fecha_inicio: Optional[date] = Query(None, description="Fecha inicio (default: hace 7 días)"),
    fecha_fin: Optional[date] = Query(None, description="Fecha fin (default: hoy)"),
    db: Session = Depends(get_db)
):
    """
    Obtener métricas y estadísticas de notificaciones
    """
    try:
        # Establecer fechas por defecto
        if not fecha_inicio:
            fecha_inicio = (datetime.now() - timedelta(days=7)).date()
        if not fecha_fin:
            fecha_fin = datetime.now().date()
        
        # Obtener métricas usando el servicio
        fecha_inicio_dt = datetime.combine(fecha_inicio, datetime.min.time())
        fecha_fin_dt = datetime.combine(fecha_fin, datetime.max.time())
        
        metrics = await notification_service.get_notification_metrics(
            db, fecha_inicio_dt, fecha_fin_dt
        )
        
        return WhatsAppEstadisticasResponse(
            fecha=fecha_fin,
            total_notificaciones=metrics["totales"]["total"],
            total_enviadas=metrics["totales"]["enviadas"],
            total_entregadas=metrics["totales"]["entregadas"],
            total_leidas=metrics["totales"]["leidas"],
            total_errores=metrics["totales"]["errores"],
            tasa_exito_porcentaje=metrics["tasas"]["exito_porcentaje"],
            por_evento=metrics["por_evento"],
            por_estado={}  # Se puede expandir según necesidades
        )
        
    except Exception as e:
        logger.error(f"Error obteniendo métricas: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.get("/metrics/daily", response_model=List[Dict[str, Any]])
async def get_daily_metrics(
    fecha_inicio: Optional[date] = Query(None, description="Fecha inicio"),
    fecha_fin: Optional[date] = Query(None, description="Fecha fin"),
    db: Session = Depends(get_db)
):
    """
    Obtener métricas diarias calculadas automáticamente
    """
    try:
        # Establecer fechas por defecto
        if not fecha_inicio:
            fecha_inicio = (datetime.now() - timedelta(days=30)).date()
        if not fecha_fin:
            fecha_fin = datetime.now().date()
        
        # Obtener métricas diarias
        metricas = db.query(WhatsAppMetricasDiariasDB).filter(
            and_(
                WhatsAppMetricasDiariasDB.fecha_metrica >= fecha_inicio,
                WhatsAppMetricasDiariasDB.fecha_metrica <= fecha_fin
            )
        ).order_by(WhatsAppMetricasDiariasDB.fecha_metrica).all()
        
        # Formatear respuesta
        result = []
        for metrica in metricas:
            result.append({
                "fecha": metrica.fecha_metrica.isoformat(),
                "total_enviadas": metrica.total_enviadas,
                "total_entregadas": metrica.total_entregadas,
                "total_leidas": metrica.total_leidas,
                "total_errores": metrica.total_errores,
                "tasa_exito_porcentaje": float(metrica.tasa_exito_porcentaje or 0),
                "tasa_error_porcentaje": float(metrica.tasa_error_porcentaje or 0),
                "tiempo_promedio_envio_minutos": (
                    metrica.tiempo_promedio_envio_segundos / 60 
                    if metrica.tiempo_promedio_envio_segundos else None
                ),
                "por_evento": {
                    "recibidas": metrica.total_recibidas,
                    "en_revision": metrica.total_en_revision,
                    "observadas": metrica.total_observadas,
                    "aprobadas": metrica.total_aprobadas,
                    "rechazadas": metrica.total_rechazadas
                }
            })
        
        return success_response(data=result)
        
    except Exception as e:
        logger.error(f"Error obteniendo métricas diarias: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

# =====================================================================
# ENDPOINTS DE PRUEBA Y ADMINISTRACIÓN
# =====================================================================

@router.post("/test", response_model=Dict[str, Any])
async def send_test_message(
    phone_number: str,
    message: str,
    db: Session = Depends(get_db)
):
    """
    Enviar mensaje de prueba para validar configuración
    """
    try:
        # Validar número telefónico
        is_valid, formatted_phone, error = whatsapp_service.validate_phone_number(phone_number)
        
        if not is_valid:
            raise ValidationError(f"Número telefónico inválido: {error}")
        
        # Enviar mensaje de prueba
        result = await whatsapp_service.send_message_with_retry(
            formatted_phone,
            f"[PRUEBA] {message}\n\nMensaje de prueba enviado el {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        )
        
        if result.get("success"):
            return success_response(
                data={
                    "phone_number": formatted_phone,
                    "message_id": result.get("message_id"),
                    "status": "sent"
                },
                message="Mensaje de prueba enviado exitosamente"
            )
        else:
            raise WhatsAppError(result.get("error", "Error desconocido"))
        
    except (ValidationError, WhatsAppError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error enviando mensaje de prueba: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.post("/process-pending", response_model=Dict[str, Any])
async def process_pending_notifications(
    limit: int = Query(50, ge=1, le=200, description="Máximo de notificaciones a procesar"),
    db: Session = Depends(get_db)
):
    """
    Forzar procesamiento de notificaciones pendientes (endpoint de administración)
    """
    try:
        stats = await notification_service.send_pending_notifications(db, limit)
        
        return success_response(
            data=stats,
            message=f"Procesamiento completado: {stats['processed']} notificaciones"
        )
        
    except Exception as e:
        logger.error(f"Error procesando notificaciones pendientes: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.get("/scheduler/status", response_model=Dict[str, Any])
async def get_scheduler_status():
    """
    Obtener estado del scheduler de tareas en background
    """
    try:
        status_info = scheduler_service.get_scheduler_status()
        return success_response(data=status_info)
        
    except Exception as e:
        logger.error(f"Error obteniendo estado del scheduler: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.post("/scheduler/calculate-metrics", response_model=Dict[str, Any])
async def calculate_metrics_manually(
    fecha: Optional[date] = Query(None, description="Fecha para calcular métricas (default: hoy)"),
    db: Session = Depends(get_db)
):
    """
    Forzar cálculo de métricas para una fecha específica
    """
    try:
        result = await scheduler_service.force_metrics_calculation(db, fecha)
        
        if result["success"]:
            return success_response(
                data=result,
                message=f"Métricas calculadas para {result['fecha']}"
            )
        else:
            raise HTTPException(status_code=400, detail=result["error"])
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculando métricas: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

# =====================================================================
# WEBHOOK DE WHATSAPP
# =====================================================================

@router.get("/webhook")
async def verify_webhook(
    request: Request
):
    """
    Verificación de webhook de WhatsApp (GET)
    """
    try:
        params = request.query_params
        mode = params.get("hub.mode")
        token = params.get("hub.verify_token")
        challenge = params.get("hub.challenge")
        
        if mode and token and challenge:
            challenge_response = await whatsapp_service.verify_webhook(mode, token, challenge)
            
            if challenge_response:
                return JSONResponse(
                    content=challenge_response, 
                    media_type="text/plain",
                    status_code=200
                )
        
        raise HTTPException(status_code=403, detail="Webhook verification failed")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verificando webhook: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.post("/webhook")
async def handle_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Manejo de webhook de WhatsApp (POST)
    """
    try:
        payload = await request.json()
        logger.info(f"Webhook recibido: {json.dumps(payload, indent=2)}")
        
        # Procesar eventos del webhook
        result = await notification_service.process_webhook_updates(db, payload)
        
        return JSONResponse(
            content={"status": "processed", "events": result["processed_events"]},
            status_code=200
        )
        
    except Exception as e:
        logger.error(f"Error procesando webhook: {str(e)}")
        # WhatsApp requiere respuesta 200 para evitar reintentos
        return JSONResponse(
            content={"status": "error", "message": "Internal error"},
            status_code=200
        )

# =====================================================================
# ENDPOINTS DE CONFIGURACIÓN (CONTACTOS Y PLANTILLAS)
# =====================================================================

@router.get("/contacts", response_model=List[WhatsAppContactoResponse])
async def list_contacts(
    activo: Optional[bool] = Query(None, description="Filtrar por estado activo"),
    tipo: Optional[str] = Query(None, description="Filtrar por tipo de contacto"),
    empresa_id: Optional[int] = Query(None, description="Filtrar por empresa"),
    db: Session = Depends(get_db)
):
    """
    Listar contactos de WhatsApp
    """
    try:
        query = db.query(WhatsAppContactosDB)
        
        if activo is not None:
            query = query.filter(WhatsAppContactosDB.activo == activo)
        
        if tipo:
            query = query.filter(WhatsAppContactosDB.tipo_contacto == tipo)
            
        if empresa_id:
            query = query.filter(WhatsAppContactosDB.empresa_id == empresa_id)
        
        contactos = query.order_by(WhatsAppContactosDB.nombre).all()
        
        result = []
        for contacto in contactos:
            contacto_data = WhatsAppContactoResponse(**contacto.__dict__)
            if contacto.empresa:
                contacto_data.empresa_razon_social = contacto.empresa.razon_social
            result.append(contacto_data)
        
        return result
        
    except Exception as e:
        logger.error(f"Error listando contactos: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.get("/templates", response_model=List[WhatsAppPlantillaMensajeResponse])
async def list_templates(
    activo: Optional[bool] = Query(None, description="Filtrar por estado activo"),
    evento: Optional[str] = Query(None, description="Filtrar por evento"),
    db: Session = Depends(get_db)
):
    """
    Listar plantillas de mensajes
    """
    try:
        query = db.query(WhatsAppPlantillasMensajesDB)
        
        if activo is not None:
            query = query.filter(WhatsAppPlantillasMensajesDB.activo == activo)
        
        if evento:
            query = query.filter(WhatsAppPlantillasMensajesDB.evento_trigger == evento)
        
        plantillas = query.order_by(WhatsAppPlantillasMensajesDB.nombre).all()
        
        return [WhatsAppPlantillaMensajeResponse(**plantilla.__dict__) for plantilla in plantillas]
        
    except Exception as e:
        logger.error(f"Error listando plantillas: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")