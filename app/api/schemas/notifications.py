"""
Schemas Pydantic optimizados para la API de notificaciones WhatsApp
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, validator, EmailStr
from enum import Enum

from app.models.whatsapp_notifications import (
    EventoTrigger, EstadoNotificacion, TipoEnvio, TipoContacto
)

# =====================================================================
# SCHEMAS BASE
# =====================================================================

class TimestampMixin(BaseModel):
    """Mixin para campos de timestamp"""
    created_at: Optional[datetime] = Field(None, description="Fecha de creación")
    updated_at: Optional[datetime] = Field(None, description="Fecha de actualización")

class CursorPagination(BaseModel):
    """Paginación basada en cursor para mejor performance"""
    cursor: Optional[str] = Field(
        None, 
        description="Cursor para paginación (ID del último elemento)",
        example="eyJpZCI6MTIzLCJ0cyI6IjIwMjUtMDEtMjNUMTI6MDA6MDBaIn0="
    )
    limit: int = Field(
        20, 
        ge=1, 
        le=100, 
        description="Cantidad de elementos por página",
        example=20
    )
    
class OffsetPagination(BaseModel):
    """Paginación tradicional por offset"""
    page: int = Field(1, ge=1, description="Número de página", example=1)
    limit: int = Field(20, ge=1, le=100, description="Elementos por página", example=20)

# =====================================================================
# REQUEST SCHEMAS
# =====================================================================

class NotificationCreateRequest(BaseModel):
    """Schema para crear notificaciones"""
    valorizacion_id: int = Field(
        ..., 
        gt=0, 
        description="ID de la valorización",
        example=123
    )
    evento_trigger: EventoTrigger = Field(
        ...,
        description="Evento que dispara la notificación",
        example=EventoTrigger.RECIBIDA
    )
    estado_actual: str = Field(
        ..., 
        min_length=1, 
        max_length=50,
        description="Estado actual de la valorización",
        example="PENDIENTE"
    )
    estado_anterior: Optional[str] = Field(
        None,
        max_length=50,
        description="Estado anterior de la valorización",
        example="BORRADOR"
    )
    tipo_envio: TipoEnvio = Field(
        TipoEnvio.PROGRAMADO,
        description="Tipo de envío de la notificación",
        example=TipoEnvio.INMEDIATO
    )
    notas: Optional[str] = Field(
        None,
        max_length=500,
        description="Notas adicionales para la notificación",
        example="Notificación urgente por cambio de estado"
    )
    
    @validator('notas')
    def validate_notas(cls, v):
        if v is not None:
            # Sanitizar HTML y caracteres especiales
            return v.strip()
        return v

class NotificationFilters(BaseModel):
    """Filtros avanzados para listar notificaciones"""
    estado: Optional[EstadoNotificacion] = Field(
        None,
        description="Filtrar por estado de notificación",
        example=EstadoNotificacion.ENVIADA
    )
    evento: Optional[EventoTrigger] = Field(
        None,
        description="Filtrar por evento trigger",
        example=EventoTrigger.APROBADA
    )
    valorizacion_id: Optional[int] = Field(
        None,
        gt=0,
        description="Filtrar por ID de valorización",
        example=123
    )
    empresa_id: Optional[int] = Field(
        None,
        gt=0,
        description="Filtrar por ID de empresa",
        example=456
    )
    contacto_id: Optional[int] = Field(
        None,
        gt=0,
        description="Filtrar por ID de contacto",
        example=789
    )
    fecha_desde: Optional[date] = Field(
        None,
        description="Fecha desde (YYYY-MM-DD)",
        example="2025-01-01"
    )
    fecha_hasta: Optional[date] = Field(
        None,
        description="Fecha hasta (YYYY-MM-DD)",
        example="2025-01-23"
    )
    telefono: Optional[str] = Field(
        None,
        pattern=r'^\+?\d{8,15}$',
        description="Filtrar por número de teléfono",
        example="+51987654321"
    )
    
    @validator('fecha_hasta')
    def validate_date_range(cls, v, values):
        if v and 'fecha_desde' in values and values['fecha_desde']:
            if v < values['fecha_desde']:
                raise ValueError('fecha_hasta debe ser mayor o igual a fecha_desde')
        return v

class NotificationStatusUpdate(BaseModel):
    """Schema para actualizar estado de notificación"""
    estado: EstadoNotificacion = Field(
        ...,
        description="Nuevo estado de la notificación",
        example=EstadoNotificacion.ENTREGADA
    )
    motivo: Optional[str] = Field(
        None,
        max_length=200,
        description="Motivo del cambio de estado",
        example="Confirmación de entrega por webhook"
    )
    
class TestMessageRequest(BaseModel):
    """Schema para envío de mensaje de prueba"""
    phone_number: str = Field(
        ...,
        pattern=r'^\+?\d{8,15}$',
        description="Número de teléfono en formato internacional",
        example="+51987654321"
    )
    message: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Mensaje de prueba a enviar",
        example="Mensaje de prueba para validar configuración"
    )
    
    @validator('phone_number')
    def normalize_phone_number(cls, v):
        # Normalizar número telefónico
        v = v.strip().replace(' ', '').replace('-', '')
        if not v.startswith('+'):
            v = '+' + v
        return v

class BulkNotificationRequest(BaseModel):
    """Schema para envío masivo de notificaciones"""
    valorizacion_ids: List[int] = Field(
        ...,
        min_items=1,
        max_items=100,
        description="Lista de IDs de valorizaciones",
        example=[123, 456, 789]
    )
    evento_trigger: EventoTrigger = Field(
        ...,
        description="Evento que dispara las notificaciones"
    )
    estado_actual: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Estado actual de las valorizaciones"
    )
    tipo_envio: TipoEnvio = Field(
        TipoEnvio.PROGRAMADO,
        description="Tipo de envío"
    )
    
    @validator('valorizacion_ids')
    def validate_unique_ids(cls, v):
        if len(v) != len(set(v)):
            raise ValueError('Los IDs de valorización deben ser únicos')
        return v

# =====================================================================
# RESPONSE SCHEMAS
# =====================================================================

class ContactInfo(BaseModel):
    """Información de contacto en respuestas"""
    id: int = Field(..., description="ID del contacto", example=1)
    nombre: str = Field(..., description="Nombre del contacto", example="Juan Pérez")
    telefono: str = Field(..., description="Teléfono del contacto", example="+51987654321")
    tipo_contacto: TipoContacto = Field(..., description="Tipo de contacto")
    empresa_nombre: Optional[str] = Field(None, description="Nombre de la empresa", example="ACME Corp")

class TemplateInfo(BaseModel):
    """Información de plantilla en respuestas"""
    id: int = Field(..., description="ID de la plantilla", example=1)
    codigo: str = Field(..., description="Código de la plantilla", example="NOTIF_RECIBIDA")
    nombre: str = Field(..., description="Nombre de la plantilla", example="Notificación Recibida")

class NotificationResponse(TimestampMixin):
    """Schema de respuesta para notificaciones"""
    id: int = Field(..., description="ID de la notificación", example=1)
    valorizacion_id: int = Field(..., description="ID de la valorización", example=123)
    evento_trigger: EventoTrigger = Field(..., description="Evento trigger")
    estado: EstadoNotificacion = Field(..., description="Estado actual")
    estado_anterior: Optional[str] = Field(None, description="Estado anterior")
    mensaje_enviado: Optional[str] = Field(None, description="Mensaje enviado")
    fecha_programada: Optional[datetime] = Field(None, description="Fecha programada de envío")
    fecha_enviada: Optional[datetime] = Field(None, description="Fecha real de envío")
    fecha_entregada: Optional[datetime] = Field(None, description="Fecha de entrega")
    fecha_leida: Optional[datetime] = Field(None, description="Fecha de lectura")
    whatsapp_message_id: Optional[str] = Field(None, description="ID del mensaje en WhatsApp")
    error_message: Optional[str] = Field(None, description="Mensaje de error si existe")
    reintentos: int = Field(0, description="Número de reintentos realizados")
    
    # Información relacionada
    contacto: ContactInfo = Field(..., description="Información del contacto")
    plantilla: TemplateInfo = Field(..., description="Información de la plantilla")

class NotificationListResponse(BaseModel):
    """Schema de respuesta para lista de notificaciones"""
    items: List[NotificationResponse] = Field(..., description="Lista de notificaciones")
    total: int = Field(..., description="Total de elementos", example=150)
    page: int = Field(..., description="Página actual", example=1)
    limit: int = Field(..., description="Elementos por página", example=20)
    total_pages: int = Field(..., description="Total de páginas", example=8)
    has_next: bool = Field(..., description="Tiene página siguiente", example=True)
    has_previous: bool = Field(..., description="Tiene página anterior", example=False)
    next_cursor: Optional[str] = Field(None, description="Cursor para página siguiente")

class MetricsResponse(BaseModel):
    """Schema de respuesta para métricas"""
    fecha_inicio: date = Field(..., description="Fecha de inicio del período")
    fecha_fin: date = Field(..., description="Fecha de fin del período")
    
    # Totales generales
    total_notificaciones: int = Field(..., description="Total de notificaciones", example=1500)
    total_enviadas: int = Field(..., description="Total enviadas", example=1450)
    total_entregadas: int = Field(..., description="Total entregadas", example=1400)
    total_leidas: int = Field(..., description="Total leídas", example=1200)
    total_errores: int = Field(..., description="Total con errores", example=50)
    
    # Tasas de éxito
    tasa_envio_porcentaje: float = Field(..., description="% de envío exitoso", example=96.67)
    tasa_entrega_porcentaje: float = Field(..., description="% de entrega", example=93.33)
    tasa_lectura_porcentaje: float = Field(..., description="% de lectura", example=80.0)
    tasa_error_porcentaje: float = Field(..., description="% de errores", example=3.33)
    
    # Métricas por evento
    por_evento: Dict[str, int] = Field(
        ..., 
        description="Distribución por evento",
        example={
            "RECIBIDA": 500,
            "EN_REVISION": 300,
            "APROBADA": 400,
            "RECHAZADA": 200,
            "OBSERVADA": 100
        }
    )
    
    # Métricas por estado
    por_estado: Dict[str, int] = Field(
        ...,
        description="Distribución por estado",
        example={
            "ENVIADA": 1450,
            "ENTREGADA": 1400,
            "LEIDA": 1200,
            "ERROR": 50
        }
    )
    
    # Métricas de tiempo
    tiempo_promedio_entrega_minutos: Optional[float] = Field(
        None,
        description="Tiempo promedio de entrega en minutos",
        example=2.5
    )

class DailyMetricsResponse(BaseModel):
    """Schema para métricas diarias"""
    fecha: date = Field(..., description="Fecha de las métricas")
    total_enviadas: int = Field(..., description="Total enviadas en el día")
    total_entregadas: int = Field(..., description="Total entregadas en el día")
    total_leidas: int = Field(..., description="Total leídas en el día")
    total_errores: int = Field(..., description="Total con errores en el día")
    tasa_exito_porcentaje: float = Field(..., description="% de éxito en el día")
    tiempo_promedio_envio_minutos: Optional[float] = Field(
        None, description="Tiempo promedio de envío en minutos"
    )
    
    por_evento: Dict[str, int] = Field(..., description="Distribución por evento")

class HealthCheckResponse(BaseModel):
    """Schema para health check"""
    status: str = Field(..., description="Estado del servicio", example="healthy")
    timestamp: datetime = Field(..., description="Timestamp del check")
    version: str = Field(..., description="Versión de la API", example="1.0.0")
    database: str = Field(..., description="Estado de la base de datos", example="connected")
    whatsapp_api: str = Field(..., description="Estado de WhatsApp API", example="connected")
    scheduler: str = Field(..., description="Estado del scheduler", example="running")
    
    # Métricas básicas
    uptime_seconds: int = Field(..., description="Tiempo de actividad en segundos")
    total_notifications_today: int = Field(..., description="Total de notificaciones hoy")
    pending_notifications: int = Field(..., description="Notificaciones pendientes")
    failed_notifications_last_hour: int = Field(..., description="Fallidas en la última hora")

class APIUsageResponse(BaseModel):
    """Schema para métricas de uso de API"""
    endpoint: str = Field(..., description="Endpoint consultado")
    method: str = Field(..., description="Método HTTP")
    total_requests: int = Field(..., description="Total de requests")
    avg_response_time_ms: float = Field(..., description="Tiempo promedio de respuesta (ms)")
    success_rate_percentage: float = Field(..., description="Tasa de éxito (%)")
    last_24h_requests: int = Field(..., description="Requests en las últimas 24h")
    rate_limit_hits: int = Field(..., description="Veces que se alcanzó rate limit")

class BulkOperationResponse(BaseModel):
    """Schema para operaciones masivas"""
    total_requested: int = Field(..., description="Total solicitado")
    total_processed: int = Field(..., description="Total procesado")
    total_success: int = Field(..., description="Total exitoso")
    total_errors: int = Field(..., description="Total con errores")
    
    # Detalles por elemento
    results: List[Dict[str, Any]] = Field(
        ..., 
        description="Resultados detallados por elemento"
    )
    
    # Errores comunes
    error_summary: Dict[str, int] = Field(
        {},
        description="Resumen de tipos de errores"
    )

# =====================================================================
# RESPONSE WRAPPERS
# =====================================================================

class APIResponse(BaseModel):
    """Wrapper estándar para todas las respuestas de la API"""
    success: bool = Field(..., description="Indica si la operación fue exitosa")
    message: str = Field(..., description="Mensaje descriptivo")
    data: Optional[Any] = Field(None, description="Datos de la respuesta")
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp de la respuesta")
    request_id: Optional[str] = Field(None, description="ID único de la petición")

class ErrorResponse(BaseModel):
    """Schema para respuestas de error"""
    success: bool = Field(False, description="Siempre false para errores")
    error: str = Field(..., description="Tipo de error")
    message: str = Field(..., description="Mensaje de error")
    details: Optional[Dict[str, Any]] = Field(None, description="Detalles adicionales del error")
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp del error")
    request_id: Optional[str] = Field(None, description="ID único de la petición")