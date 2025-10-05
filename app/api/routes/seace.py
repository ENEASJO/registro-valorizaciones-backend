"""
Endpoints para consulta SEACE (Sistema Electrónico de Contrataciones del Estado)
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, Any
import logging

from app.models.seace import SEACEInput, ObraSEACE, ErrorResponseSEACE
from app.services.seace_service import seace_service
from app.utils.exceptions import BaseAppException

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/seace",
    tags=["SEACE"],
    responses={
        400: {"model": ErrorResponseSEACE, "description": "Error de validación"},
        404: {"model": ErrorResponseSEACE, "description": "Obra no encontrada en SEACE"},
        408: {"model": ErrorResponseSEACE, "description": "Timeout en la consulta"},
        500: {"model": ErrorResponseSEACE, "description": "Error interno del servidor"},
    }
)


@router.post(
    "/consultar",
    response_model=ObraSEACE,
    summary="Consultar obra en SEACE por CUI y año",
    description="Consulta información detallada de una obra en SEACE usando CUI y año de convocatoria",
    response_description="Información completa de la obra incluyendo nomenclatura, normativa, descripción y monto"
)
async def consultar_obra_seace(seace_input: SEACEInput) -> ObraSEACE:
    """
    Consulta información completa de obra por CUI y año en SEACE

    - **cui**: Código Único de Inversión (7-10 dígitos)
    - **anio**: Año de la convocatoria (2000-2100)

    Retorna:
    - Nomenclatura del proceso
    - Normativa aplicable
    - Objeto de contratación
    - Descripción del objeto
    - Monto contractual
    - Información adicional (entidad convocante, fecha de publicación, etc.)
    """
    try:
        logger.info(f"Iniciando consulta SEACE para CUI: {seace_input.cui}, Año: {seace_input.anio}")

        # Consultar obra usando el servicio SEACE
        obra_info = await seace_service.consultar_obra(seace_input.cui, seace_input.anio)

        logger.info(f"Consulta SEACE exitosa para CUI {seace_input.cui}: {obra_info.nomenclatura}")

        return obra_info

    except BaseAppException as e:
        logger.error(f"Error de aplicación consultando SEACE CUI {seace_input.cui}: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail={
                "error": True,
                "message": e.message,
                "details": e.details,
                "cui": seace_input.cui,
                "anio": seace_input.anio,
                "fuente": "SEACE"
            }
        )

    except Exception as e:
        logger.error(f"Error inesperado consultando SEACE CUI {seace_input.cui}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": True,
                "message": "Error interno del servidor",
                "details": "Ha ocurrido un error inesperado durante la consulta SEACE",
                "cui": seace_input.cui,
                "anio": seace_input.anio,
                "fuente": "SEACE"
            }
        )


@router.get(
    "/consultar/{cui}/{anio}",
    response_model=ObraSEACE,
    summary="Consultar obra en SEACE por CUI y año (GET)",
    description="Consulta información detallada de una obra en SEACE usando CUI y año via GET",
    response_description="Información completa de la obra"
)
async def consultar_obra_seace_get(cui: str, anio: int) -> ObraSEACE:
    """
    Consulta información completa de obra por CUI y año en SEACE (método GET)

    - **cui**: CUI en la URL
    - **anio**: Año de la convocatoria en la URL

    Retorna la misma información que el endpoint POST
    """
    try:
        # Crear objeto SEACEInput para validación
        seace_input = SEACEInput(cui=cui, anio=anio)

        # Usar la misma lógica del endpoint POST
        return await consultar_obra_seace(seace_input)

    except Exception as e:
        logger.error(f"Error en consulta GET SEACE para CUI {cui}, Año {anio}: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail={
                "error": True,
                "message": f"Error en consulta SEACE: {str(e)}",
                "cui": cui,
                "anio": anio,
                "fuente": "SEACE"
            }
        )


@router.get(
    "/health",
    summary="Verificar estado del servicio SEACE",
    description="Endpoint para verificar que el servicio SEACE está funcionando correctamente",
    tags=["Health"]
)
async def health_check_seace() -> Dict[str, Any]:
    """Verificar estado del servicio SEACE"""
    return {
        "status": "healthy",
        "message": "Servicio de consulta SEACE funcionando correctamente",
        "service": "seace-api",
        "version": "1.0.0",
        "features": [
            "Consulta de información de obras por CUI y año",
            "Extracción de nomenclatura",
            "Extracción de normativa aplicable",
            "Extracción de objeto de contratación",
            "Extracción de descripción del objeto",
            "Extracción de monto contractual",
            "Información de entidad convocante",
            "Fecha de publicación"
        ]
    }


@router.get(
    "/info",
    summary="Información del API SEACE",
    description="Información detallada sobre el API de consulta SEACE",
    tags=["Info"]
)
async def api_info_seace() -> Dict[str, Any]:
    """Información del API SEACE"""
    return {
        "name": "API Consultor SEACE",
        "version": "1.0.0",
        "description": "API para consultar información detallada de obras en SEACE por CUI y año",
        "endpoints": {
            "POST /api/v1/seace/consultar": "Consultar obra por CUI y año (POST)",
            "GET /api/v1/seace/consultar/{cui}/{anio}": "Consultar obra por CUI y año (GET)",
            "GET /api/v1/seace/health": "Verificar estado del servicio",
            "GET /api/v1/seace/info": "Información del API"
        },
        "features": {
            "basic_info": "Extrae información básica de la obra (nomenclatura, normativa, objeto)",
            "description": "Extrae descripción completa del objeto de contratación",
            "amount": "Extrae monto contractual (VR/VE/Cuantía)",
            "additional_data": "Entidad convocante, fecha de publicación, tipo de compra"
        },
        "data_sources": {
            "primary": "SEACE - Sistema Electrónico de Contrataciones del Estado",
            "url": "https://prod2.seace.gob.pe/seacebus-uiwd-pub/buscadorPublico/buscadorPublico.xhtml"
        },
        "response_format": {
            "nomenclatura": "Nomenclatura del proceso",
            "normativa_aplicable": "Ley aplicable (Ley N° 30225 o Ley N° 32069)",
            "objeto_contratacion": "Objeto de contratación (Obra, Bien, Servicio, etc.)",
            "descripcion": "Descripción completa del objeto",
            "monto_contractual": "Monto en soles",
            "cui": "CUI consultado",
            "anio": "Año de la convocatoria",
            "numero_convocatoria": "Número de convocatoria",
            "entidad_convocante": "Nombre de la entidad convocante",
            "fecha_publicacion": "Fecha y hora de publicación",
            "tipo_compra": "Tipo de compra o selección",
            "fuente": "SEACE"
        },
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc"
        }
    }
