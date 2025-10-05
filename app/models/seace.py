"""
Modelos para datos de SEACE (Sistema Electrónico de Contrataciones del Estado)
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class SEACEInput(BaseModel):
    """Modelo para la entrada de búsqueda en SEACE"""
    cui: str = Field(..., description="Código Único de Inversión", min_length=7, max_length=10)
    anio: int = Field(..., description="Año de la convocatoria", ge=2000, le=2100)

    class Config:
        json_schema_extra = {
            "example": {
                "cui": "2595080",
                "anio": 2024
            }
        }


class ObraSEACE(BaseModel):
    """Modelo para información de obra extraída de SEACE"""
    # Información básica
    nomenclatura: str = Field(..., description="Nomenclatura del proceso")
    numero_contrato: Optional[str] = Field(None, description="Número de contrato (Tipo de documento)")
    normativa_aplicable: str = Field(..., description="Normativa aplicable (Ley)")
    objeto_contratacion: str = Field(..., description="Objeto de contratación")
    descripcion: str = Field(..., description="Descripción del objeto")
    monto_contractual: float = Field(..., description="Monto contractual (VR/VE/Cuantía)")

    # Información adicional
    cui: str = Field(..., description="CUI consultado")
    anio: int = Field(..., description="Año de la convocatoria")
    numero_convocatoria: Optional[str] = Field(None, description="Número de convocatoria")
    entidad_convocante: Optional[str] = Field(None, description="Entidad convocante")
    fecha_publicacion: Optional[str] = Field(None, description="Fecha y hora de publicación")
    tipo_compra: Optional[str] = Field(None, description="Tipo de compra o selección")

    # Metadatos
    fuente: str = Field(default="SEACE", description="Fuente de los datos")
    fecha_consulta: Optional[datetime] = Field(default_factory=datetime.now, description="Fecha de consulta")

    class Config:
        json_schema_extra = {
            "example": {
                "nomenclatura": "AS-SM-167-2024-MDSM/CS-1",
                "numero_contrato": "167-2024-MDSM/GM",
                "normativa_aplicable": "Ley N° 30225 - Ley de Contrataciones del Estado",
                "objeto_contratacion": "Obra",
                "descripcion": "CONTRATACION DE LA EJECUCION DE LA OBRA: CONSTRUCCION DE MURO DE CONTENCION...",
                "monto_contractual": 640251.96,
                "cui": "2595080",
                "anio": 2024,
                "numero_convocatoria": "1",
                "entidad_convocante": "MUNICIPALIDAD DISTRITAL DE SAN MARCOS",
                "fecha_publicacion": "14/05/2024 20:38",
                "tipo_compra": "Por la Entidad",
                "fuente": "SEACE"
            }
        }


class ErrorResponseSEACE(BaseModel):
    """Modelo para respuestas de error"""
    error: bool = True
    message: str
    details: Optional[str] = None
    cui: Optional[str] = None
    anio: Optional[int] = None
    fuente: str = "SEACE"

    class Config:
        json_schema_extra = {
            "example": {
                "error": True,
                "message": "No se encontraron resultados para el CUI proporcionado",
                "details": "Verifique que el CUI y el año sean correctos",
                "cui": "2595080",
                "anio": 2024,
                "fuente": "SEACE"
            }
        }
