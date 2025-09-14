"""
Modelos Pydantic para el sistema de consulta OSCE
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
import re


class IntegranteOSCE(BaseModel):
    """Modelo para integrante/miembro de empresa en OSCE"""
    nombre: str = Field(
        ...,
        title="Nombre Completo",
        description="Nombre completo del integrante",
        min_length=1,
        example="JUAN CARLOS PEREZ LOPEZ"
    )
    cargo: Optional[str] = Field(
        default="",
        title="Cargo",
        description="Cargo o función del integrante",
        example="SOCIO"
    )
    participacion: Optional[str] = Field(
        default="",
        title="Participación",
        description="Porcentaje de participación o responsabilidad",
        example="50%"
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

    @validator('nombre')
    def validate_nombre(cls, v):
        """Validar que el nombre no esté vacío y tenga formato válido"""
        if not v or not v.strip():
            raise ValueError("Nombre es requerido")
        
        v = v.strip()
        
        # Validar que no sea un header de tabla
        headers_invalidos = [
            "NOMBRE", "APELLIDOS", "TIPO", "DOC", "CARGO", "FECHA",
            "DOCUMENTO", "INTEGRANTE", "MIEMBRO", "SOCIO", "PARTICIPACION"
        ]
        
        if v.upper() in headers_invalidos:
            raise ValueError("Nombre no puede ser un header de tabla")
        
        # Validar longitud mínima
        if len(v) < 3:
            raise ValueError("Nombre debe tener al menos 3 caracteres")
        
        return v.upper()

    class Config:
        schema_extra = {
            "example": {
                "nombre": "JUAN CARLOS PEREZ LOPEZ",
                "cargo": "SOCIO",
                "participacion": "50%",
                "tipo_documento": "DNI",
                "numero_documento": "12345678"
            }
        }


class EspecialidadOSCE(BaseModel):
    """Modelo para especialidad de empresa en OSCE"""
    codigo: Optional[str] = Field(
        default="",
        title="Código",
        description="Código de la especialidad",
        example="E001"
    )
    descripcion: str = Field(
        ...,
        title="Descripción",
        description="Descripción de la especialidad",
        example="Construcción de edificaciones"
    )
    categoria: Optional[str] = Field(
        default="",
        title="Categoría",
        description="Categoría de la especialidad",
        example="Construcción"
    )
    vigencia: Optional[str] = Field(
        default="",
        title="Vigencia",
        description="Estado de vigencia de la especialidad",
        example="VIGENTE"
    )

    class Config:
        schema_extra = {
            "example": {
                "codigo": "E001",
                "descripcion": "Construcción de edificaciones",
                "categoria": "Construcción",
                "vigencia": "VIGENTE"
            }
        }


class ContactoOSCE(BaseModel):
    """Modelo para información de contacto de empresa en OSCE"""
    telefono: Optional[str] = Field(
        default="",
        title="Teléfono",
        description="Número de teléfono de la empresa",
        example="+51 XX XXXXXXX"
    )
    email: Optional[str] = Field(
        default="",
        title="Email",
        description="Correo electrónico de la empresa",
        example="contacto@empresa.com"
    )
    direccion: Optional[str] = Field(
        default="",
        title="Dirección",
        description="Dirección física de la empresa",
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
            # Validación básica de email
            if not re.match(r'^[^@]+@[^@]+\.[^@]+$', v):
                raise ValueError("Formato de email no válido")
        return v

    class Config:
        schema_extra = {
            "example": {
                "telefono": "+51 XX XXXXXXX",
                "email": "contacto@empresa.com",
                "direccion": "AV. PRINCIPAL 123, LIMA",
                "ciudad": "LIMA",
                "departamento": "LIMA"
            }
        }


class EmpresaOSCE(BaseModel):
    """Modelo para la información completa de una empresa en OSCE"""
    ruc: str = Field(
        ...,
        title="RUC",
        description="Registro Único de Contribuyentes",
        example="20486130718"
    )
    fuente: str = Field(
        default="OSCE",
        title="Fuente",
        description="Sistema fuente de los datos",
        example="OSCE"
    )
    razon_social: Optional[str] = Field(
        default="",
        title="Razón Social",
        description="Razón social de la empresa",
        example="ORE INGENIEROS SRL"
    )
    estado_registro: Optional[str] = Field(
        default="",
        title="Estado de Registro",
        description="Estado del registro en OSCE",
        example="HABILITADO"
    )
    telefono: Optional[str] = Field(
        default="",
        title="Teléfono",
        description="Número de teléfono principal",
        example="+51 XX XXXXXXX"
    )
    email: Optional[str] = Field(
        default="",
        title="Email",
        description="Correo electrónico principal",
        example="contacto@empresa.com"
    )
    especialidades: List[str] = Field(
        default_factory=list,
        title="Especialidades",
        description="Lista de especialidades de la empresa"
    )
    especialidades_detalle: List[EspecialidadOSCE] = Field(
        default_factory=list,
        title="Especialidades Detalladas",
        description="Lista detallada de especialidades con códigos y categorías"
    )
    integrantes: List[IntegranteOSCE] = Field(
        default_factory=list,
        title="Integrantes",
        description="Lista de integrantes/socios de la empresa"
    )
    contacto: ContactoOSCE = Field(
        default_factory=ContactoOSCE,
        title="Información de Contacto",
        description="Información completa de contacto"
    )
    vigencia: Optional[str] = Field(
        default="",
        title="Vigencia",
        description="Periodo de vigencia del registro",
        example="2024-12-31"
    )
    capacidad_contratacion: Optional[str] = Field(
        default="",
        title="Capacidad de Contratación",
        description="Capacidad máxima de contratación",
        example="S/ 1,000,000"
    )
    fecha_registro: Optional[str] = Field(
        default="",
        title="Fecha de Registro",
        description="Fecha de registro en OSCE",
        example="2020-01-15"
    )
    total_especialidades: int = Field(
        default=0,
        title="Total de Especialidades",
        description="Número total de especialidades registradas",
        ge=0
    )
    total_integrantes: int = Field(
        default=0,
        title="Total de Integrantes",
        description="Número total de integrantes registrados",
        ge=0
    )
    observaciones: List[str] = Field(
        default_factory=list,
        title="Observaciones",
        description="Lista de observaciones o notas adicionales"
    )

    @validator('total_especialidades', always=True)
    def sync_total_especialidades(cls, v, values):
        """Sincronizar el total con la longitud de la lista de especialidades"""
        especialidades = values.get('especialidades', [])
        return len(especialidades)

    @validator('total_integrantes', always=True)
    def sync_total_integrantes(cls, v, values):
        """Sincronizar el total con la longitud de la lista de integrantes"""
        integrantes = values.get('integrantes', [])
        return len(integrantes)

    class Config:
        schema_extra = {
            "example": {
                "ruc": "20486130718",
                "fuente": "OSCE",
                "razon_social": "ORE INGENIEROS SRL",
                "estado_registro": "HABILITADO",
                "telefono": "+51 XX XXXXXXX",
                "email": "contacto@empresa.com",
                "especialidades": [
                    "Construcción de edificaciones",
                    "Consultoría en ingeniería",
                    "Supervisión de obras"
                ],
                "integrantes": [
                    {
                        "nombre": "PERSONA 1",
                        "cargo": "SOCIO",
                        "participacion": "50%"
                    }
                ],
                "total_especialidades": 3,
                "total_integrantes": 1,
                "vigencia": "2024-12-31",
                "capacidad_contratacion": "S/ 1,000,000"
            }
        }


class ErrorResponseOSCE(BaseModel):
    """Modelo para respuestas de error de OSCE"""
    error: bool = Field(default=True, title="Error")
    message: str = Field(..., title="Mensaje de Error")
    details: Optional[str] = Field(default=None, title="Detalles del Error")
    ruc: Optional[str] = Field(default=None, title="RUC consultado")
    fuente: str = Field(default="OSCE", title="Fuente")
    
    class Config:
        schema_extra = {
            "example": {
                "error": True,
                "message": "RUC no encontrado en OSCE",
                "details": "El RUC consultado no tiene registro de proveedor en OSCE",
                "ruc": "20486130718",
                "fuente": "OSCE"
            }
        }