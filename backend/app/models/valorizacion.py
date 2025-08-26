"""
Modelos Pydantic para valorizaciones de obra
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime, date
from decimal import Decimal

class ValorizacionBase(BaseModel):
    """Modelo base para valorizaciones"""
    codigo: Optional[str] = Field("", title="Código de Valorización", max_length=50)
    obra_id: int = Field(..., title="ID de la Obra")
    numero_valorizacion: int = Field(..., title="Número de Valorización", ge=1)
    periodo: str = Field(..., title="Período (YYYY-MM)", max_length=20)
    
    # Fechas
    fecha_inicio: date = Field(..., title="Fecha de Inicio del Período")
    fecha_fin: date = Field(..., title="Fecha de Fin del Período")
    fecha_presentacion: Optional[date] = Field(None, title="Fecha de Presentación")
    fecha_aprobacion: Optional[date] = Field(None, title="Fecha de Aprobación")
    
    # Tipo
    tipo_valorizacion: str = Field("MENSUAL", title="Tipo de Valorización", max_length=50)
    
    # Montos principales
    monto_ejecutado: Decimal = Field(0, title="Monto Ejecutado en el Período", ge=0)
    monto_materiales: Optional[Decimal] = Field(0, title="Monto de Materiales", ge=0)
    monto_mano_obra: Optional[Decimal] = Field(0, title="Monto de Mano de Obra", ge=0)
    monto_equipos: Optional[Decimal] = Field(0, title="Monto de Equipos", ge=0)
    monto_subcontratos: Optional[Decimal] = Field(0, title="Monto de Subcontratos", ge=0)
    monto_gastos_generales: Optional[Decimal] = Field(0, title="Gastos Generales", ge=0)
    monto_utilidad: Optional[Decimal] = Field(0, title="Utilidad", ge=0)
    igv: Optional[Decimal] = Field(0, title="IGV", ge=0)
    monto_total: Decimal = Field(0, title="Monto Total de la Valorización", ge=0)
    
    # Avances
    porcentaje_avance_periodo: Optional[Decimal] = Field(0, title="% Avance del Período", ge=0, le=100)
    porcentaje_avance_acumulado: Optional[Decimal] = Field(0, title="% Avance Acumulado", ge=0, le=100)
    
    # Estado
    estado_valorizacion: str = Field("BORRADOR", title="Estado de la Valorización", max_length=50)
    observaciones: Optional[str] = Field(None, title="Observaciones")
    
    # Datos técnicos (JSON)
    archivos_adjuntos: Optional[List[Dict[str, Any]]] = Field(None, title="Archivos Adjuntos")
    metrado_ejecutado: Optional[List[Dict[str, Any]]] = Field(None, title="Metrados Ejecutados")
    partidas_ejecutadas: Optional[List[Dict[str, Any]]] = Field(None, title="Partidas Ejecutadas")

    @validator('codigo')
    def validate_codigo(cls, v):
        if v:
            return v.strip().upper()
        return ""
    
    @validator('periodo')
    def validate_periodo(cls, v):
        if not v or not v.strip():
            raise ValueError("Período es requerido")
        # Validar formato YYYY-MM
        import re
        if not re.match(r'^\d{4}-\d{2}$', v.strip()):
            raise ValueError("Período debe tener formato YYYY-MM")
        return v.strip()
    
    @validator('fecha_fin')
    def validate_fechas(cls, v, values):
        if 'fecha_inicio' in values and v < values['fecha_inicio']:
            raise ValueError("Fecha fin debe ser posterior a fecha inicio")
        return v
    
    @validator('monto_total', always=True)
    def calculate_monto_total(cls, v, values):
        # Auto calcular monto total si no se proporciona
        if v == 0 and 'monto_ejecutado' in values:
            ejecutado = values.get('monto_ejecutado', 0)
            gastos = values.get('monto_gastos_generales', 0)
            utilidad = values.get('monto_utilidad', 0) 
            igv = values.get('igv', 0)
            return ejecutado + gastos + utilidad + igv
        return v

class ValorizacionCreate(ValorizacionBase):
    """Modelo para crear valorización"""
    pass

class ValorizacionUpdate(BaseModel):
    """Modelo para actualizar valorización"""
    fecha_presentacion: Optional[date] = None
    fecha_aprobacion: Optional[date] = None
    monto_ejecutado: Optional[Decimal] = Field(None, ge=0)
    monto_materiales: Optional[Decimal] = Field(None, ge=0)
    monto_mano_obra: Optional[Decimal] = Field(None, ge=0)
    monto_equipos: Optional[Decimal] = Field(None, ge=0)
    monto_subcontratos: Optional[Decimal] = Field(None, ge=0)
    monto_gastos_generales: Optional[Decimal] = Field(None, ge=0)
    monto_utilidad: Optional[Decimal] = Field(None, ge=0)
    igv: Optional[Decimal] = Field(None, ge=0)
    porcentaje_avance_periodo: Optional[Decimal] = Field(None, ge=0, le=100)
    porcentaje_avance_acumulado: Optional[Decimal] = Field(None, ge=0, le=100)
    estado_valorizacion: Optional[str] = Field(None, max_length=50)
    observaciones: Optional[str] = None
    archivos_adjuntos: Optional[List[Dict[str, Any]]] = None
    metrado_ejecutado: Optional[List[Dict[str, Any]]] = None
    partidas_ejecutadas: Optional[List[Dict[str, Any]]] = None

class ValorizacionResponse(ValorizacionBase):
    """Modelo de respuesta para valorización"""
    id: int
    activo: bool
    created_at: datetime
    updated_at: datetime
    version: int
    
    # Información adicional de la obra
    obra_nombre: Optional[str] = None
    obra_codigo: Optional[str] = None
    empresa_razon_social: Optional[str] = None
    
    class Config:
        from_attributes = True

class ValorizacionListResponse(BaseModel):
    """Modelo de respuesta para lista de valorizaciones"""
    valorizaciones: List[ValorizacionResponse]
    total: int
    pagina: int
    limite: int
    total_paginas: int

class ResumenValorizacion(BaseModel):
    """Resumen de valorización por obra"""
    obra_id: int
    obra_nombre: str
    total_valorizaciones: int
    monto_total_ejecutado: Decimal
    porcentaje_avance_total: Decimal
    ultima_valorizacion: Optional[date] = None
    estado_actual: str

# Estados válidos para valorizaciones
ESTADOS_VALORIZACION = [
    "BORRADOR",
    "PRESENTADA",
    "EN_REVISION",
    "OBSERVADA", 
    "APROBADA",
    "PAGADA",
    "ANULADA"
]

# Tipos de valorización
TIPOS_VALORIZACION = [
    "MENSUAL",
    "QUINCENAL", 
    "ADICIONAL",
    "FINAL",
    "LIQUIDACION"
]