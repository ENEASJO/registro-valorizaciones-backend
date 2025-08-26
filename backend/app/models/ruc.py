"""
Modelos Pydantic para el sistema de consulta RUC
"""
from typing import List, Optional
from pydantic import BaseModel, Field, validator
import re


class RUCInput(BaseModel):
    """Modelo para la entrada de consulta RUC"""
    ruc: str = Field(
        ...,
        title="RUC",
        description="Registro Único de Contribuyentes - debe tener 11 dígitos",
        min_length=11,
        max_length=11,
        example="20123456789"
    )

    @validator('ruc')
    def validate_ruc_format(cls, v):
        """Validar que el RUC tenga formato correcto"""
        if not v:
            raise ValueError("RUC es requerido")
        
        # Remover espacios en blanco
        v = v.strip()
        
        # Verificar que solo contenga dígitos
        if not re.match(r'^\d{11}$', v):
            raise ValueError("RUC debe contener exactamente 11 dígitos numéricos")
        
        # Validar que comience con dígitos válidos (10 para persona natural, 20 para persona jurídica)
        primeros_dos_digitos = v[:2]
        if primeros_dos_digitos not in ['10', '20']:
            raise ValueError("RUC debe comenzar con 10 (persona natural) o 20 (persona jurídica)")
        
        return v

    class Config:
        schema_extra = {
            "example": {
                "ruc": "20123456789"
            }
        }


class RepresentanteLegal(BaseModel):
    """Modelo para representante legal de una empresa"""
    tipo_doc: Optional[str] = Field(
        default="-",
        title="Tipo de Documento",
        description="Tipo de documento de identidad",
        example="DNI"
    )
    numero_doc: Optional[str] = Field(
        default="-",
        title="Número de Documento",
        description="Número del documento de identidad",
        example="12345678"
    )
    nombre: str = Field(
        ...,
        title="Nombre Completo",
        description="Nombre completo del representante legal",
        min_length=1,
        example="JUAN CARLOS PEREZ LOPEZ"
    )
    cargo: Optional[str] = Field(
        default="",
        title="Cargo",
        description="Cargo o función del representante",
        example="GERENTE GENERAL"
    )
    fecha_desde: Optional[str] = Field(
        default="",
        title="Fecha Desde",
        description="Fecha de inicio en el cargo",
        example="01/01/2020"
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
            "DOCUMENTO", "REPRESENTANTE", "LEGAL", "DESDE"
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
                "tipo_doc": "DNI",
                "numero_doc": "12345678",
                "nombre": "JUAN CARLOS PEREZ LOPEZ",
                "cargo": "GERENTE GENERAL",
                "fecha_desde": "01/01/2020"
            }
        }


class EmpresaInfo(BaseModel):
    """Modelo para la información completa de una empresa"""
    ruc: str = Field(
        ...,
        title="RUC",
        description="Registro Único de Contribuyentes",
        example="20123456789"
    )
    razon_social: Optional[str] = Field(
        default="",
        title="Razón Social",
        description="Razón social de la empresa",
        example="EMPRESA EJEMPLO S.A.C."
    )
    domicilio_fiscal: Optional[str] = Field(
        default="",
        title="Domicilio Fiscal",
        description="Domicilio fiscal registrado en SUNAT",
        example="AV. EXAMPLE 123, DISTRICT - PROVINCE - DEPARTMENT"
    )
    representantes: List[RepresentanteLegal] = Field(
        default_factory=list,
        title="Representantes Legales",
        description="Lista de representantes legales de la empresa"
    )
    total_representantes: int = Field(
        default=0,
        title="Total de Representantes",
        description="Número total de representantes legales encontrados",
        ge=0,
        example=2
    )

    @validator('total_representantes', always=True)
    def sync_total_representantes(cls, v, values):
        """Sincronizar el total con la longitud de la lista de representantes"""
        representantes = values.get('representantes', [])
        return len(representantes)

    class Config:
        schema_extra = {
            "example": {
                "ruc": "20123456789",
                "razon_social": "EMPRESA EJEMPLO S.A.C.",
                "domicilio_fiscal": "AV. EXAMPLE 123, DISTRICT - PROVINCE - DEPARTMENT",
                "representantes": [
                    {
                        "tipo_doc": "DNI",
                        "numero_doc": "12345678",
                        "nombre": "JUAN CARLOS PEREZ LOPEZ",
                        "cargo": "GERENTE GENERAL",
                        "fecha_desde": "01/01/2020"
                    }
                ],
                "total_representantes": 1
            }
        }


class ErrorResponse(BaseModel):
    """Modelo para respuestas de error"""
    error: bool = Field(default=True, title="Error")
    message: str = Field(..., title="Mensaje de Error")
    details: Optional[str] = Field(default=None, title="Detalles del Error")
    
    class Config:
        schema_extra = {
            "example": {
                "error": True,
                "message": "RUC no válido",
                "details": "El RUC debe contener exactamente 11 dígitos"
            }
        }