"""
Modelos Pydantic para el sistema consolidado de consulta RUC
Combina datos de SUNAT y OSCE en un modelo unificado
"""
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, validator
from datetime import datetime
import re

from .ruc import RepresentanteLegal
from .osce import IntegranteOSCE, EspecialidadOSCE


class MiembroConsolidado(BaseModel):
    """Modelo unificado para miembros/integrantes de empresa (SUNAT + OSCE)"""
    nombre: str = Field(
        ...,
        title="Nombre Completo",
        description="Nombre completo del miembro",
        min_length=1,
        example="JUAN CARLOS PEREZ LOPEZ"
    )
    cargo: Optional[str] = Field(
        default="",
        title="Cargo",
        description="Cargo o función del miembro",
        example="SOCIO / GERENTE GENERAL"
    )
    tipo_documento: Optional[str] = Field(
        default="",
        title="Tipo de Documento",
        description="Tipo de documento de identidad",
        example="DNI"
    )
    numero_documento: Optional[str] = Field(
        default="",
        title="Número de Documento",
        description="Número del documento de identidad",
        example="12345678"
    )
    participacion: Optional[str] = Field(
        default="",
        title="Participación",
        description="Porcentaje de participación en la empresa",
        example="50%"
    )
    fecha_desde: Optional[str] = Field(
        default="",
        title="Fecha Desde",
        description="Fecha de inicio en el cargo",
        example="01/01/2020"
    )
    fuente: str = Field(
        ...,
        title="Fuente de Datos",
        description="Origen de los datos (SUNAT, OSCE, AMBOS)",
        example="AMBOS"
    )
    fuentes_detalle: Dict[str, Any] = Field(
        default_factory=dict,
        title="Detalle de Fuentes",
        description="Información específica de cada fuente"
    )

    @validator('nombre')
    def validate_nombre(cls, v):
        """Validar que el nombre no esté vacío y tenga formato válido"""
        if not v or not v.strip():
            raise ValueError("Nombre es requerido")
        
        v = v.strip()
        
        # Validar longitud mínima
        if len(v) < 3:
            raise ValueError("Nombre debe tener al menos 3 caracteres")
        
        return v.upper()

    class Config:
        schema_extra = {
            "example": {
                "nombre": "JUAN CARLOS PEREZ LOPEZ",
                "cargo": "SOCIO / GERENTE GENERAL",
                "tipo_documento": "DNI",
                "numero_documento": "12345678",
                "participacion": "50%",
                "fecha_desde": "01/01/2020",
                "fuente": "AMBOS",
                "fuentes_detalle": {
                    "sunat": {"cargo": "GERENTE GENERAL", "fecha_desde": "01/01/2020"},
                    "osce": {"cargo": "SOCIO", "participacion": "50%"}
                }
            }
        }


class ContactoConsolidado(BaseModel):
    """Modelo unificado para información de contacto"""
    telefono: Optional[str] = Field(
        default="",
        title="Teléfono",
        description="Número de teléfono principal (prioridad: OSCE > SUNAT)",
        example="+51 XX XXXXXXX"
    )
    email: Optional[str] = Field(
        default="",
        title="Email",
        description="Correo electrónico principal (prioridad: OSCE > SUNAT)",
        example="contacto@empresa.com"
    )
    direccion: Optional[str] = Field(
        default="",
        title="Dirección",
        description="Dirección física completa",
        example="AV. PRINCIPAL 123, LIMA"
    )
    domicilio_fiscal: Optional[str] = Field(
        default="",
        title="Domicilio Fiscal",
        description="Domicilio fiscal según SUNAT",
        example="AV. PRINCIPAL 123, LIMA"
    )
    ciudad: Optional[str] = Field(
        default="",
        title="Ciudad",
        description="Ciudad donde se ubica la empresa",
        example="LIMA"
    )
    departamento: Optional[str] = Field(
        default="",
        title="Departamento",
        description="Departamento donde se ubica la empresa",
        example="LIMA"
    )

    @validator('email')
    def validate_email(cls, v):
        """Validar formato básico de email"""
        if v and '@' in v:
            if not re.match(r'^[^@]+@[^@]+\.[^@]+$', v):
                raise ValueError("Formato de email no válido")
        return v

    class Config:
        schema_extra = {
            "example": {
                "telefono": "+51 XX XXXXXXX",
                "email": "contacto@empresa.com",
                "direccion": "AV. PRINCIPAL 123, LIMA",
                "domicilio_fiscal": "AV. PRINCIPAL 123, LIMA",
                "ciudad": "LIMA",
                "departamento": "LIMA"
            }
        }


class RegistroConsolidado(BaseModel):
    """Información de registro en diferentes sistemas"""
    sunat: Dict[str, Any] = Field(
        default_factory=dict,
        title="Datos SUNAT",
        description="Información específica de SUNAT"
    )
    osce: Dict[str, Any] = Field(
        default_factory=dict,
        title="Datos OSCE",
        description="Información específica de OSCE"
    )
    estado_sunat: Optional[str] = Field(
        default="",
        title="Estado en SUNAT",
        description="Estado del registro en SUNAT",
        example="ACTIVO"
    )
    estado_osce: Optional[str] = Field(
        default="",
        title="Estado en OSCE",
        description="Estado del registro en OSCE",
        example="HABILITADO"
    )


class EmpresaConsolidada(BaseModel):
    """Modelo consolidado que combina información de SUNAT y OSCE"""
    ruc: str = Field(
        ...,
        title="RUC",
        description="Registro Único de Contribuyentes",
        example="20606881666"
    )
    razon_social: str = Field(
        ...,
        title="Razón Social",
        description="Razón social oficial (prioridad: SUNAT)",
        example="EMPRESA EJEMPLO S.A.C."
    )
    tipo_persona: Optional[str] = Field(
        default="",
        title="Tipo de Persona",
        description="NATURAL o JURIDICA según RUC",
        example="JURIDICA"
    )
    
    # Información de contacto consolidada
    contacto: ContactoConsolidado = Field(
        default_factory=ContactoConsolidado,
        title="Información de Contacto Consolidada",
        description="Datos de contacto combinados de ambas fuentes"
    )
    
    # Miembros consolidados (SUNAT representantes + OSCE integrantes)
    miembros: List[MiembroConsolidado] = Field(
        default_factory=list,
        title="Miembros Consolidados",
        description="Lista unificada de representantes/integrantes sin duplicados"
    )
    
    # Especialidades (solo OSCE)
    especialidades: List[str] = Field(
        default_factory=list,
        title="Especialidades",
        description="Lista de especialidades registradas en OSCE"
    )
    especialidades_detalle: List[EspecialidadOSCE] = Field(
        default_factory=list,
        title="Especialidades Detalladas",
        description="Información detallada de especialidades OSCE"
    )
    
    # Información de registro consolidada
    registro: RegistroConsolidado = Field(
        default_factory=RegistroConsolidado,
        title="Información de Registro",
        description="Estados y datos de registro en ambos sistemas"
    )
    
    # Metadatos de consolidación
    total_miembros: int = Field(
        default=0,
        title="Total de Miembros",
        description="Número total de miembros únicos",
        ge=0
    )
    total_especialidades: int = Field(
        default=0,
        title="Total de Especialidades",
        description="Número total de especialidades",
        ge=0
    )
    fuentes_consultadas: List[str] = Field(
        default_factory=list,
        title="Fuentes Consultadas",
        description="Lista de sistemas consultados exitosamente"
    )
    fuentes_con_errores: List[str] = Field(
        default_factory=list,
        title="Fuentes con Errores",
        description="Lista de sistemas que presentaron errores"
    )
    capacidad_contratacion: Optional[str] = Field(
        default="",
        title="Capacidad de Contratación",
        description="Capacidad máxima de contratación (OSCE)",
        example="S/ 1,000,000"
    )
    vigencia: Optional[str] = Field(
        default="",
        title="Vigencia",
        description="Periodo de vigencia del registro",
        example="2024-12-31"
    )
    
    # Información técnica
    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        title="Timestamp",
        description="Fecha y hora de la consulta"
    )
    consolidacion_exitosa: bool = Field(
        default=True,
        title="Consolidación Exitosa",
        description="Indica si la consolidación fue exitosa"
    )
    observaciones: List[str] = Field(
        default_factory=list,
        title="Observaciones",
        description="Notas sobre la consolidación de datos"
    )

    @validator('total_miembros', always=True)
    def sync_total_miembros(cls, v, values):
        """Sincronizar el total con la longitud de la lista de miembros"""
        miembros = values.get('miembros', [])
        return len(miembros)

    @validator('total_especialidades', always=True)
    def sync_total_especialidades(cls, v, values):
        """Sincronizar el total con la longitud de la lista de especialidades"""
        especialidades = values.get('especialidades', [])
        return len(especialidades)

    @validator('tipo_persona', always=True)
    def determine_tipo_persona(cls, v, values):
        """Determinar tipo de persona basado en RUC"""
        ruc = values.get('ruc', '')
        if ruc.startswith('10'):
            return 'NATURAL'
        elif ruc.startswith('20'):
            return 'JURIDICA'
        return v

    class Config:
        schema_extra = {
            "example": {
                "ruc": "20606881666",
                "razon_social": "EMPRESA EJEMPLO S.A.C.",
                "tipo_persona": "JURIDICA",
                "contacto": {
                    "telefono": "+51 XX XXXXXXX",
                    "email": "contacto@empresa.com",
                    "direccion": "AV. PRINCIPAL 123, LIMA",
                    "domicilio_fiscal": "AV. PRINCIPAL 123, LIMA"
                },
                "miembros": [
                    {
                        "nombre": "JUAN CARLOS PEREZ LOPEZ",
                        "cargo": "SOCIO / GERENTE GENERAL",
                        "tipo_documento": "DNI",
                        "numero_documento": "12345678",
                        "fuente": "AMBOS"
                    }
                ],
                "especialidades": [
                    "Construcción de edificaciones",
                    "Consultoría en ingeniería"
                ],
                "registro": {
                    "estado_sunat": "ACTIVO",
                    "estado_osce": "HABILITADO"
                },
                "total_miembros": 1,
                "total_especialidades": 2,
                "fuentes_consultadas": ["SUNAT", "OSCE"],
                "fuentes_con_errores": [],
                "consolidacion_exitosa": True
            }
        }


class ErrorConsolidado(BaseModel):
    """Modelo para respuestas de error del sistema consolidado"""
    error: bool = Field(default=True, title="Error")
    message: str = Field(..., title="Mensaje de Error")
    details: Optional[str] = Field(default=None, title="Detalles del Error")
    ruc: Optional[str] = Field(default=None, title="RUC consultado")
    fuentes_intentadas: List[str] = Field(
        default_factory=list,
        title="Fuentes Intentadas",
        description="Lista de sistemas que se intentaron consultar"
    )
    fuentes_exitosas: List[str] = Field(
        default_factory=list,
        title="Fuentes Exitosas",
        description="Lista de sistemas consultados exitosamente"
    )
    datos_parciales: Optional[EmpresaConsolidada] = Field(
        default=None,
        title="Datos Parciales",
        description="Datos obtenidos de fuentes exitosas (si los hay)"
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        title="Timestamp"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "error": True,
                "message": "Error parcial en consolidación",
                "details": "SUNAT respondió correctamente, OSCE presentó timeout",
                "ruc": "20606881666",
                "fuentes_intentadas": ["SUNAT", "OSCE"],
                "fuentes_exitosas": ["SUNAT"],
                "datos_parciales": None
            }
        }