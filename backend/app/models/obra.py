"""
Modelos Pydantic para obras de construcción
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime, date
from decimal import Decimal

class ObraBase(BaseModel):
    """Modelo base para obras"""
    codigo: Optional[str] = Field("", title="Código de Obra", max_length=50)
    nombre: str = Field(..., title="Nombre de la Obra", min_length=1, max_length=500)
    descripcion: Optional[str] = Field(None, title="Descripción")
    empresa_id: int = Field(..., title="ID de la Empresa Ejecutora")
    cliente: Optional[str] = Field(None, title="Cliente/Propietario", max_length=255)
    
    # Ubicación
    ubicacion: Optional[str] = Field(None, title="Ubicación de la Obra")
    distrito: Optional[str] = Field(None, title="Distrito", max_length=100)
    provincia: Optional[str] = Field(None, title="Provincia", max_length=100)
    departamento: Optional[str] = Field(None, title="Departamento", max_length=100)
    ubigeo: Optional[str] = Field(None, title="Código UBIGEO", max_length=6)
    
    # Características técnicas
    modalidad_ejecucion: Optional[str] = Field(None, title="Modalidad de Ejecución", max_length=50)
    sistema_contratacion: Optional[str] = Field(None, title="Sistema de Contratación", max_length=50)
    tipo_obra: Optional[str] = Field(None, title="Tipo de Obra", max_length=100)
    
    # Montos
    monto_contractual: Optional[Decimal] = Field(None, title="Monto Contractual", ge=0)
    monto_adicionales: Optional[Decimal] = Field(0, title="Monto de Adicionales", ge=0)
    monto_total: Optional[Decimal] = Field(None, title="Monto Total", ge=0)
    
    # Fechas y plazos
    fecha_inicio: Optional[date] = Field(None, title="Fecha de Inicio")
    fecha_fin_contractual: Optional[date] = Field(None, title="Fecha de Fin Contractual")
    fecha_fin_real: Optional[date] = Field(None, title="Fecha de Fin Real")
    plazo_contractual: Optional[int] = Field(None, title="Plazo Contractual (días)", ge=0)
    plazo_total: Optional[int] = Field(None, title="Plazo Total (días)", ge=0)
    
    # Estado
    estado_obra: str = Field("PLANIFICADA", title="Estado de la Obra", max_length=50)
    porcentaje_avance: Optional[Decimal] = Field(0, title="Porcentaje de Avance", ge=0, le=100)
    observaciones: Optional[str] = Field(None, title="Observaciones")

    @validator('codigo')
    def validate_codigo(cls, v):
        if v:
            return v.strip().upper()
        return ""
    
    @validator('nombre')
    def validate_nombre(cls, v):
        if not v or not v.strip():
            raise ValueError("Nombre es requerido")
        return v.strip()
    
    @validator('monto_total', always=True)
    def calculate_monto_total(cls, v, values):
        if 'monto_contractual' in values and 'monto_adicionales' in values:
            contractual = values['monto_contractual'] or 0
            adicionales = values['monto_adicionales'] or 0
            return contractual + adicionales
        return v

class ObraCreate(ObraBase):
    """Modelo para crear obra"""
    pass

class ObraUpdate(BaseModel):
    """Modelo para actualizar obra"""
    nombre: Optional[str] = Field(None, min_length=1, max_length=500)
    descripcion: Optional[str] = None
    cliente: Optional[str] = Field(None, max_length=255)
    ubicacion: Optional[str] = None
    distrito: Optional[str] = Field(None, max_length=100)
    provincia: Optional[str] = Field(None, max_length=100)
    departamento: Optional[str] = Field(None, max_length=100)
    modalidad_ejecucion: Optional[str] = Field(None, max_length=50)
    sistema_contratacion: Optional[str] = Field(None, max_length=50)
    tipo_obra: Optional[str] = Field(None, max_length=100)
    monto_contractual: Optional[Decimal] = Field(None, ge=0)
    monto_adicionales: Optional[Decimal] = Field(None, ge=0)
    fecha_inicio: Optional[date] = None
    fecha_fin_contractual: Optional[date] = None
    fecha_fin_real: Optional[date] = None
    plazo_contractual: Optional[int] = Field(None, ge=0)
    plazo_total: Optional[int] = Field(None, ge=0)
    estado_obra: Optional[str] = Field(None, max_length=50)
    porcentaje_avance: Optional[Decimal] = Field(None, ge=0, le=100)
    observaciones: Optional[str] = None

class ObraResponse(ObraBase):
    """Modelo de respuesta para obra"""
    id: int
    activo: bool
    created_at: datetime
    updated_at: datetime
    version: int
    
    # Información adicional calculada
    dias_transcurridos: Optional[int] = None
    dias_restantes: Optional[int] = None
    avance_programado: Optional[Decimal] = None
    
    class Config:
        from_attributes = True

class ObraListResponse(BaseModel):
    """Modelo de respuesta para lista de obras"""
    obras: List[ObraResponse]
    total: int
    pagina: int
    limite: int
    total_paginas: int

# Estados válidos para obras
ESTADOS_OBRA = [
    "PLANIFICADA",
    "EN_PROCESO", 
    "PARALIZADA",
    "SUSPENDIDA",
    "TERMINADA",
    "LIQUIDADA",
    "CANCELADA"
]

# Modalidades de ejecución
MODALIDADES_EJECUCION = [
    "ADMINISTRACION_DIRECTA",
    "CONTRATA",
    "CONCESION",
    "ASOCIACION_PUBLICO_PRIVADA"
]

# Sistemas de contratación
SISTEMAS_CONTRATACION = [
    "SUMA_ALZADA",
    "PRECIOS_UNITARIOS",
    "ESQUEMA_MIXTO",
    "COSTO_MAS_PORCENTAJE"
]