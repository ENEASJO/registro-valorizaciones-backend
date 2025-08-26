"""
Modelos SQLAlchemy para el sistema de notificaciones WhatsApp
Base de datos: Turso (SQLite)
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, TIMESTAMP, DECIMAL, Date, ForeignKey, Time
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime, date, time
from enum import Enum

from app.core.database import Base

# =====================================================================
# ENUMERACIONES PARA VALIDACIÓN
# =====================================================================

class EventoTrigger(str, Enum):
    RECIBIDA = "RECIBIDA"
    EN_REVISION = "EN_REVISION"
    OBSERVADA = "OBSERVADA"
    APROBADA = "APROBADA"
    RECHAZADA = "RECHAZADA"

class EstadoNotificacion(str, Enum):
    PENDIENTE = "PENDIENTE"
    PROGRAMADA = "PROGRAMADA"
    ENVIANDO = "ENVIANDO"
    ENVIADA = "ENVIADA"
    ENTREGADA = "ENTREGADA"
    LEIDA = "LEIDA"
    ERROR = "ERROR"
    CANCELADA = "CANCELADA"
    EXPIRADA = "EXPIRADA"

class TipoContacto(str, Enum):
    CONTRATISTA = "CONTRATISTA"
    COORDINADOR_INTERNO = "COORDINADOR_INTERNO"

class TipoDestinatario(str, Enum):
    CONTRATISTA = "CONTRATISTA"
    COORDINADOR_INTERNO = "COORDINADOR_INTERNO"
    AMBOS = "AMBOS"

class TipoEnvio(str, Enum):
    INMEDIATO = "INMEDIATO"
    PROGRAMADO = "PROGRAMADO"

# =====================================================================
# MODELOS DE BASE DE DATOS
# =====================================================================

class WhatsAppConfiguracionHorariosDB(Base):
    """Configuración de horarios laborables para envío de notificaciones"""
    __tablename__ = "whatsapp_configuracion_horarios"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False, unique=True)
    descripcion = Column(Text, nullable=True)
    
    # Configuración de días laborables (JSON string)
    dias_laborables = Column(Text, nullable=False, default='["LUNES","MARTES","MIERCOLES","JUEVES","VIERNES"]')
    
    # Horarios de envío
    hora_inicio_envios = Column(Time, nullable=False, default=time(8, 0))
    hora_fin_envios = Column(Time, nullable=False, default=time(18, 0))
    
    # Configuración adicional
    zona_horaria = Column(String(50), nullable=False, default='America/Lima')
    reintentos_maximos = Column(Integer, nullable=False, default=3)
    intervalo_reintento_minutos = Column(Integer, nullable=False, default=30)
    
    # Estado
    activo = Column(Boolean, nullable=False, default=True)
    
    # Auditoría
    created_at = Column(TIMESTAMP, nullable=False, default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, nullable=False, default=func.current_timestamp(), onupdate=func.current_timestamp())
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)
    
    # Relaciones
    contactos = relationship("WhatsAppContactosDB", back_populates="horario_configuracion")
    notificaciones = relationship("WhatsAppNotificacionesDB", back_populates="horario_configuracion")

class WhatsAppPlantillasMensajesDB(Base):
    """Plantillas de mensajes personalizables para diferentes eventos"""
    __tablename__ = "whatsapp_plantillas_mensajes"
    
    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(50), nullable=False, unique=True)
    nombre = Column(String(200), nullable=False)
    descripcion = Column(Text, nullable=True)
    
    # Configuración de eventos
    evento_trigger = Column(String(50), nullable=False)
    estado_valorizacion = Column(String(50), nullable=False)
    tipo_destinatario = Column(String(50), nullable=False)
    
    # Contenido del mensaje
    asunto = Column(String(255), nullable=True)
    mensaje_texto = Column(Text, nullable=False)
    mensaje_html = Column(Text, nullable=True)
    
    # Variables disponibles (JSON string)
    variables_disponibles = Column(Text, default='["obra_nombre","empresa_razon_social","valorizacion_numero","valorizacion_periodo","estado_anterior","estado_actual","fecha_cambio","monto_total","observaciones"]')
    
    # Configuración de envío
    es_inmediato = Column(Boolean, nullable=False, default=True)
    requiere_confirmacion = Column(Boolean, nullable=False, default=False)
    prioridad = Column(Integer, nullable=False, default=5)  # 1=Alta, 5=Media, 10=Baja
    
    # Estado
    activo = Column(Boolean, nullable=False, default=True)
    
    # Auditoría
    created_at = Column(TIMESTAMP, nullable=False, default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, nullable=False, default=func.current_timestamp(), onupdate=func.current_timestamp())
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)
    
    # Relaciones
    notificaciones = relationship("WhatsAppNotificacionesDB", back_populates="plantilla")

class WhatsAppContactosDB(Base):
    """Contactos WhatsApp para notificaciones"""
    __tablename__ = "whatsapp_contactos"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Relaciones con entidades existentes
    empresa_id = Column(Integer, ForeignKey("empresas.id", ondelete="CASCADE"), nullable=True)
    obra_id = Column(Integer, nullable=True)  # Asumo que no hay tabla obras aún
    usuario_id = Column(Integer, nullable=True)  # Para coordinadores internos
    
    # Datos del contacto
    nombre = Column(String(255), nullable=False)
    cargo = Column(String(100), nullable=True)
    telefono = Column(String(20), nullable=False)
    email = Column(String(100), nullable=True)
    
    # Configuración del contacto
    tipo_contacto = Column(String(50), nullable=False)
    es_principal = Column(Boolean, nullable=False, default=False)
    
    # Configuración de notificaciones
    recibe_notificaciones = Column(Boolean, nullable=False, default=True)
    eventos_suscritos = Column(Text, default='["RECIBIDA","EN_REVISION","OBSERVADA","APROBADA","RECHAZADA"]')  # JSON array
    horario_configuracion_id = Column(Integer, ForeignKey("whatsapp_configuracion_horarios.id"), default=1)
    
    # Estados
    activo = Column(Boolean, nullable=False, default=True)
    verificado = Column(Boolean, nullable=False, default=False)
    
    # Auditoría
    created_at = Column(TIMESTAMP, nullable=False, default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, nullable=False, default=func.current_timestamp(), onupdate=func.current_timestamp())
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)
    
    # Relaciones
    empresa = relationship("EmpresaDB", foreign_keys=[empresa_id])
    horario_configuracion = relationship("WhatsAppConfiguracionHorariosDB", back_populates="contactos")
    notificaciones = relationship("WhatsAppNotificacionesDB", back_populates="contacto")

class WhatsAppNotificacionesDB(Base):
    """Tabla principal de notificaciones WhatsApp"""
    __tablename__ = "whatsapp_notificaciones"
    
    id = Column(Integer, primary_key=True, index=True)
    codigo_notificacion = Column(String(50), nullable=False, unique=True)
    
    # Relaciones
    valorizacion_id = Column(Integer, nullable=False)  # Asumo que hay tabla valorizaciones
    plantilla_id = Column(Integer, ForeignKey("whatsapp_plantillas_mensajes.id"), nullable=False)
    contacto_id = Column(Integer, ForeignKey("whatsapp_contactos.id"), nullable=False)
    horario_configuracion_id = Column(Integer, ForeignKey("whatsapp_configuracion_horarios.id"), default=1)
    
    # Información del evento
    evento_trigger = Column(String(50), nullable=False)
    estado_anterior = Column(String(50), nullable=True)
    estado_actual = Column(String(50), nullable=False)
    fecha_evento = Column(TIMESTAMP, nullable=False, default=func.current_timestamp())
    
    # Contenido del mensaje (renderizado)
    asunto_renderizado = Column(String(500), nullable=True)
    mensaje_renderizado = Column(Text, nullable=False)
    variables_utilizadas = Column(Text, nullable=True)  # JSON con variables y valores
    
    # Configuración de envío
    tipo_envio = Column(String(20), nullable=False, default='INMEDIATO')
    fecha_programada = Column(TIMESTAMP, nullable=True)
    prioridad = Column(Integer, nullable=False, default=5)
    
    # Estado de la notificación
    estado = Column(String(20), nullable=False, default='PENDIENTE')
    fecha_cambio_estado = Column(TIMESTAMP, nullable=False, default=func.current_timestamp())
    
    # Información de envío
    fecha_envio = Column(TIMESTAMP, nullable=True)
    fecha_entrega = Column(TIMESTAMP, nullable=True)
    fecha_lectura = Column(TIMESTAMP, nullable=True)
    
    # Manejo de errores y reintentos
    intentos_envio = Column(Integer, nullable=False, default=0)
    max_reintentos = Column(Integer, nullable=False, default=3)
    ultimo_error = Column(Text, nullable=True)
    fecha_ultimo_error = Column(TIMESTAMP, nullable=True)
    
    # Información técnica WhatsApp
    whatsapp_message_id = Column(String(100), nullable=True)
    whatsapp_status = Column(String(50), nullable=True)
    whatsapp_timestamp = Column(TIMESTAMP, nullable=True)
    metadata_whatsapp = Column(Text, nullable=True)  # JSON
    
    # Auditoría
    created_at = Column(TIMESTAMP, nullable=False, default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, nullable=False, default=func.current_timestamp(), onupdate=func.current_timestamp())
    created_by = Column(Integer, nullable=True)
    
    # Relaciones
    plantilla = relationship("WhatsAppPlantillasMensajesDB", back_populates="notificaciones")
    contacto = relationship("WhatsAppContactosDB", back_populates="notificaciones")
    horario_configuracion = relationship("WhatsAppConfiguracionHorariosDB", back_populates="notificaciones")
    historial = relationship("WhatsAppHistorialNotificacionesDB", back_populates="notificacion", cascade="all, delete-orphan")

class WhatsAppHistorialNotificacionesDB(Base):
    """Historial de cambios de estado de notificaciones"""
    __tablename__ = "whatsapp_historial_notificaciones"
    
    id = Column(Integer, primary_key=True, index=True)
    notificacion_id = Column(Integer, ForeignKey("whatsapp_notificaciones.id", ondelete="CASCADE"), nullable=False)
    
    # Información del cambio
    estado_anterior = Column(String(20), nullable=True)
    estado_nuevo = Column(String(20), nullable=False)
    fecha_cambio = Column(TIMESTAMP, nullable=False, default=func.current_timestamp())
    
    # Detalles del cambio
    motivo_cambio = Column(String(100), nullable=True)
    descripcion_cambio = Column(Text, nullable=True)
    codigo_error = Column(String(50), nullable=True)
    mensaje_error = Column(Text, nullable=True)
    
    # Información técnica
    metadata_cambio = Column(Text, nullable=True)  # JSON
    
    # Auditoría
    created_at = Column(TIMESTAMP, nullable=False, default=func.current_timestamp())
    created_by = Column(Integer, nullable=True)
    
    # Relaciones
    notificacion = relationship("WhatsAppNotificacionesDB", back_populates="historial")

class WhatsAppMetricasDiariasDB(Base):
    """Métricas y estadísticas diarias del sistema"""
    __tablename__ = "whatsapp_metricas_diarias"
    
    id = Column(Integer, primary_key=True, index=True)
    fecha_metrica = Column(Date, nullable=False, unique=True)
    
    # Contadores por estado
    total_pendientes = Column(Integer, nullable=False, default=0)
    total_enviadas = Column(Integer, nullable=False, default=0)
    total_entregadas = Column(Integer, nullable=False, default=0)
    total_leidas = Column(Integer, nullable=False, default=0)
    total_errores = Column(Integer, nullable=False, default=0)
    total_canceladas = Column(Integer, nullable=False, default=0)
    
    # Contadores por tipo de evento
    total_recibidas = Column(Integer, nullable=False, default=0)
    total_en_revision = Column(Integer, nullable=False, default=0)
    total_observadas = Column(Integer, nullable=False, default=0)
    total_aprobadas = Column(Integer, nullable=False, default=0)
    total_rechazadas = Column(Integer, nullable=False, default=0)
    
    # Métricas de rendimiento
    tiempo_promedio_envio_segundos = Column(Integer, nullable=True)
    tiempo_promedio_entrega_segundos = Column(Integer, nullable=True)
    tasa_exito_porcentaje = Column(DECIMAL(5, 2), nullable=True)
    tasa_error_porcentaje = Column(DECIMAL(5, 2), nullable=True)
    
    # Auditoría
    created_at = Column(TIMESTAMP, nullable=False, default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, nullable=False, default=func.current_timestamp(), onupdate=func.current_timestamp())

# =====================================================================
# MODELOS PYDANTIC PARA API
# =====================================================================

class WhatsAppConfiguracionHorariosBase(BaseModel):
    """Modelo base para configuración de horarios"""
    nombre: str = Field(..., max_length=100)
    descripcion: Optional[str] = None
    dias_laborables: List[str] = Field(default=["LUNES","MARTES","MIERCOLES","JUEVES","VIERNES"])
    hora_inicio_envios: time = Field(default=time(8, 0))
    hora_fin_envios: time = Field(default=time(18, 0))
    zona_horaria: str = Field(default="America/Lima", max_length=50)
    reintentos_maximos: int = Field(default=3, ge=1, le=10)
    intervalo_reintento_minutos: int = Field(default=30, ge=5, le=1440)
    activo: bool = True

class WhatsAppConfiguracionHorariosCreate(WhatsAppConfiguracionHorariosBase):
    """Modelo para crear configuración de horarios"""
    pass

class WhatsAppConfiguracionHorariosResponse(WhatsAppConfiguracionHorariosBase):
    """Modelo de respuesta para configuración de horarios"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class WhatsAppPlantillaMensajeBase(BaseModel):
    """Modelo base para plantillas de mensajes"""
    codigo: str = Field(..., max_length=50)
    nombre: str = Field(..., max_length=200)
    descripcion: Optional[str] = None
    evento_trigger: EventoTrigger
    estado_valorizacion: str = Field(..., max_length=50)
    tipo_destinatario: TipoDestinatario
    asunto: Optional[str] = Field(None, max_length=255)
    mensaje_texto: str
    mensaje_html: Optional[str] = None
    variables_disponibles: List[str] = Field(default=[
        "obra_nombre", "empresa_razon_social", "valorizacion_numero", 
        "valorizacion_periodo", "estado_anterior", "estado_actual", 
        "fecha_cambio", "monto_total", "observaciones"
    ])
    es_inmediato: bool = True
    requiere_confirmacion: bool = False
    prioridad: int = Field(default=5, ge=1, le=10)
    activo: bool = True

    @validator('codigo')
    def validate_codigo(cls, v):
        return v.upper().strip()

class WhatsAppPlantillaMensajeCreate(WhatsAppPlantillaMensajeBase):
    """Modelo para crear plantilla de mensaje"""
    pass

class WhatsAppPlantillaMensajeResponse(WhatsAppPlantillaMensajeBase):
    """Modelo de respuesta para plantilla de mensaje"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class WhatsAppContactoBase(BaseModel):
    """Modelo base para contactos WhatsApp"""
    empresa_id: Optional[int] = None
    obra_id: Optional[int] = None
    usuario_id: Optional[int] = None
    nombre: str = Field(..., max_length=255)
    cargo: Optional[str] = Field(None, max_length=100)
    telefono: str = Field(..., max_length=20)
    email: Optional[str] = Field(None, max_length=100)
    tipo_contacto: TipoContacto
    es_principal: bool = False
    recibe_notificaciones: bool = True
    eventos_suscritos: List[EventoTrigger] = Field(default=[
        EventoTrigger.RECIBIDA, EventoTrigger.EN_REVISION, 
        EventoTrigger.OBSERVADA, EventoTrigger.APROBADA, EventoTrigger.RECHAZADA
    ])
    horario_configuracion_id: int = 1
    activo: bool = True
    verificado: bool = False

    @validator('telefono')
    def validate_telefono(cls, v):
        # Remover espacios y caracteres especiales, mantener solo dígitos
        telefono_limpio = ''.join(filter(str.isdigit, v))
        if len(telefono_limpio) < 9:
            raise ValueError('El teléfono debe tener al menos 9 dígitos')
        return telefono_limpio

class WhatsAppContactoCreate(WhatsAppContactoBase):
    """Modelo para crear contacto WhatsApp"""
    pass

class WhatsAppContactoResponse(WhatsAppContactoBase):
    """Modelo de respuesta para contacto WhatsApp"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    # Información relacionada
    empresa_razon_social: Optional[str] = None
    
    class Config:
        from_attributes = True

class WhatsAppNotificacionBase(BaseModel):
    """Modelo base para notificaciones"""
    valorizacion_id: int
    plantilla_id: int
    contacto_id: int
    evento_trigger: EventoTrigger
    estado_anterior: Optional[str] = None
    estado_actual: str
    tipo_envio: TipoEnvio = TipoEnvio.INMEDIATO
    fecha_programada: Optional[datetime] = None
    prioridad: int = Field(default=5, ge=1, le=10)

class WhatsAppNotificacionCreate(WhatsAppNotificacionBase):
    """Modelo para crear notificación"""
    pass

class WhatsAppNotificacionResponse(WhatsAppNotificacionBase):
    """Modelo de respuesta para notificación"""
    id: int
    codigo_notificacion: str
    fecha_evento: datetime
    asunto_renderizado: Optional[str] = None
    mensaje_renderizado: str
    estado: EstadoNotificacion
    fecha_cambio_estado: datetime
    fecha_envio: Optional[datetime] = None
    fecha_entrega: Optional[datetime] = None
    fecha_lectura: Optional[datetime] = None
    intentos_envio: int
    max_reintentos: int
    ultimo_error: Optional[str] = None
    whatsapp_message_id: Optional[str] = None
    whatsapp_status: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    # Información relacionada
    contacto_nombre: Optional[str] = None
    contacto_telefono: Optional[str] = None
    plantilla_nombre: Optional[str] = None
    
    class Config:
        from_attributes = True

class WhatsAppNotificacionListResponse(BaseModel):
    """Modelo de respuesta para lista de notificaciones"""
    notificaciones: List[WhatsAppNotificacionResponse]
    total: int
    pagina: int
    limite: int
    total_paginas: int

class WhatsAppEstadisticasResponse(BaseModel):
    """Modelo de respuesta para estadísticas"""
    fecha: date
    total_notificaciones: int
    total_enviadas: int
    total_entregadas: int
    total_leidas: int
    total_errores: int
    tasa_exito_porcentaje: float
    tiempo_promedio_envio_minutos: Optional[float] = None
    
    # Por evento
    por_evento: Dict[str, int] = {}
    
    # Por estado
    por_estado: Dict[str, int] = {}

# =====================================================================
# CONSTANTES
# =====================================================================

EVENTOS_VALIDOS = [
    "RECIBIDA", "EN_REVISION", "OBSERVADA", "APROBADA", "RECHAZADA"
]

ESTADOS_NOTIFICACION_VALIDOS = [
    "PENDIENTE", "PROGRAMADA", "ENVIANDO", "ENVIADA", 
    "ENTREGADA", "LEIDA", "ERROR", "CANCELADA", "EXPIRADA"
]

TIPOS_CONTACTO_VALIDOS = [
    "CONTRATISTA", "COORDINADOR_INTERNO"
]

VARIABLES_PLANTILLA_DISPONIBLES = [
    "obra_nombre", "empresa_razon_social", "valorizacion_numero",
    "valorizacion_periodo", "estado_anterior", "estado_actual",
    "fecha_cambio", "monto_total", "observaciones", "contacto_nombre"
]