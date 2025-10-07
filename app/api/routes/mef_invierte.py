"""
Endpoints para consulta MEF Invierte (Banco de Inversiones)
Sistema del Ministerio de Economía y Finanzas
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
import logging

from app.services.mef_invierte_service import consultar_cui_mef, consultar_cui_mef_con_nombre

logger = logging.getLogger(__name__)


class MEFInvierteInput(BaseModel):
    """Input para consulta MEF Invierte"""
    cui: str = Field(..., description="Código Único de Inversiones (CUI)", example="2595080")


class MEFInvierteSearchInput(BaseModel):
    """Input para búsqueda en MEF Invierte"""
    cui: Optional[str] = Field(None, description="Código Único de Inversiones (opcional)", example="2595080")
    nombre: Optional[str] = Field(None, description="Nombre o descripción de la inversión (opcional)", example="CONSTRUCCION")


router = APIRouter(
    prefix="/api/v1/mef-invierte",
    tags=["MEF Invierte"],
    responses={
        400: {"description": "Error de validación"},
        404: {"description": "Inversión no encontrada en MEF Invierte"},
        408: {"description": "Timeout en la consulta"},
        500: {"description": "Error interno del servidor"},
    }
)


@router.post(
    "/consultar",
    summary="Consultar inversión en MEF Invierte por CUI",
    description="Consulta información detallada de una inversión pública por su CUI en el Banco de Inversiones de MEF",
    response_description="Información completa de la inversión"
)
async def consultar_inversion_mef(mef_input: MEFInvierteInput) -> Dict[str, Any]:
    """
    Consulta información completa de una inversión por CUI en MEF Invierte

    - **cui**: Código Único de Inversiones (ejemplo: "2595080")

    Retorna:
    - Código de idea
    - Código único de inversiones (CUI)
    - Código SNIP
    - Estado de la inversión
    - Nombre de la inversión
    - Tipo de formato (IOARR, etc.)
    - Situación (APROBADO, VIABLE, etc.)
    - Costo de inversión viable/aprobado
    - Costo de inversión actualizado
    - Indicadores de fichas disponibles (ejecución, seguimiento)
    """
    try:
        logger.info(f"Iniciando consulta MEF Invierte para CUI: {mef_input.cui}")

        resultado = await consultar_cui_mef(mef_input.cui)

        if resultado.get("success"):
            logger.info(f"Consulta MEF Invierte exitosa para CUI {mef_input.cui}")
            return resultado
        else:
            logger.warning(f"No se encontró inversión para CUI {mef_input.cui}")
            raise HTTPException(
                status_code=404,
                detail={
                    "error": True,
                    "message": resultado.get("error", "No se encontró información"),
                    "cui": mef_input.cui,
                    "fuente": "MEF Invierte"
                }
            )

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Error inesperado consultando MEF Invierte CUI {mef_input.cui}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": True,
                "message": "Error interno del servidor",
                "details": str(e),
                "cui": mef_input.cui,
                "fuente": "MEF Invierte"
            }
        )


@router.get(
    "/consultar/{cui}",
    summary="Consultar inversión en MEF Invierte por CUI (GET)",
    description="Consulta información detallada de una inversión pública usando CUI via GET",
    response_description="Información completa de la inversión"
)
async def consultar_inversion_mef_get(cui: str) -> Dict[str, Any]:
    """
    Consulta información completa de una inversión por CUI en MEF Invierte (método GET)

    - **cui**: CUI en la URL (ejemplo: "2595080")

    Retorna la misma información que el endpoint POST
    """
    try:
        mef_input = MEFInvierteInput(cui=cui)
        return await consultar_inversion_mef(mef_input)

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Error en consulta GET MEF Invierte para CUI {cui}: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail={
                "error": True,
                "message": f"Error en consulta MEF Invierte: {str(e)}",
                "cui": cui,
                "fuente": "MEF Invierte"
            }
        )


@router.post(
    "/buscar",
    summary="Buscar inversiones en MEF Invierte",
    description="Busca inversiones por CUI y/o nombre en el Banco de Inversiones de MEF",
    response_description="Lista de inversiones encontradas"
)
async def buscar_inversiones_mef(search_input: MEFInvierteSearchInput) -> Dict[str, Any]:
    """
    Busca inversiones por CUI y/o nombre en MEF Invierte

    - **cui**: Código Único de Inversiones (opcional)
    - **nombre**: Nombre o descripción de la inversión (opcional)

    Al menos uno de los dos parámetros debe proporcionarse.

    Retorna:
    - Lista de inversiones que coinciden con los criterios
    - Cada inversión incluye toda la información disponible
    """
    try:
        if not search_input.cui and not search_input.nombre:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": True,
                    "message": "Debe proporcionar al menos un CUI o nombre para buscar",
                    "fuente": "MEF Invierte"
                }
            )

        logger.info(f"Iniciando búsqueda MEF Invierte - CUI: {search_input.cui}, Nombre: {search_input.nombre}")

        resultado = await consultar_cui_mef_con_nombre(
            cui=search_input.cui,
            nombre=search_input.nombre
        )

        if resultado.get("success"):
            logger.info(f"Búsqueda MEF Invierte exitosa: {resultado.get('count', 0)} resultados")
            return resultado
        else:
            logger.warning("No se encontraron resultados en búsqueda MEF Invierte")
            raise HTTPException(
                status_code=404,
                detail={
                    "error": True,
                    "message": resultado.get("error", "No se encontraron resultados"),
                    "cui": search_input.cui,
                    "nombre": search_input.nombre,
                    "fuente": "MEF Invierte"
                }
            )

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Error inesperado en búsqueda MEF Invierte: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": True,
                "message": "Error interno del servidor",
                "details": str(e),
                "fuente": "MEF Invierte"
            }
        )


@router.get(
    "/health",
    summary="Verificar estado del servicio MEF Invierte",
    description="Endpoint para verificar que el servicio MEF Invierte está funcionando correctamente",
    tags=["Health"]
)
async def health_check_mef() -> Dict[str, Any]:
    """Verificar estado del servicio MEF Invierte"""
    return {
        "status": "healthy",
        "message": "Servicio de consulta MEF Invierte funcionando correctamente",
        "service": "mef-invierte-api",
        "version": "1.0.0",
        "features": [
            "Consulta de inversiones públicas por CUI",
            "Búsqueda por nombre de inversión",
            "Extracción de código de idea",
            "Extracción de código SNIP",
            "Estado y situación de la inversión",
            "Costos viable y actualizado",
            "Información de fichas disponibles"
        ]
    }


@router.get(
    "/info",
    summary="Información del API MEF Invierte",
    description="Información detallada sobre el API de consulta MEF Invierte",
    tags=["Info"]
)
async def api_info_mef() -> Dict[str, Any]:
    """Información del API MEF Invierte"""
    return {
        "name": "API Consultor MEF Invierte",
        "version": "1.0.0",
        "description": "API para consultar información de inversiones públicas en el Banco de Inversiones de MEF",
        "endpoints": {
            "POST /api/v1/mef-invierte/consultar": "Consultar inversión por CUI (POST)",
            "GET /api/v1/mef-invierte/consultar/{cui}": "Consultar inversión por CUI (GET)",
            "POST /api/v1/mef-invierte/buscar": "Buscar inversiones por CUI y/o nombre",
            "GET /api/v1/mef-invierte/health": "Verificar estado del servicio",
            "GET /api/v1/mef-invierte/info": "Información del API"
        },
        "features": {
            "basic_info": "Extrae información básica de la inversión (código idea, CUI, SNIP)",
            "status": "Estado actual de la inversión (ACTIVO, etc.)",
            "costs": "Costos viable/aprobado y actualizado",
            "format": "Tipo de formato (IOARR, etc.)",
            "situation": "Situación de la inversión (APROBADO, VIABLE, etc.)",
            "documents": "Indicadores de fichas de ejecución y seguimiento disponibles"
        },
        "data_sources": {
            "primary": "MEF Invierte - Banco de Inversiones",
            "organization": "Ministerio de Economía y Finanzas",
            "url": "https://ofi5.mef.gob.pe/invierte/consultapublica/consultainversiones"
        },
        "response_format": {
            "codigo_idea": "Código de idea de inversión",
            "cui": "Código Único de Inversiones",
            "codigo_snip": "Código SNIP (Sistema Nacional de Inversión Pública)",
            "estado": "Estado de la inversión (ACTIVO, etc.)",
            "nombre": "Nombre completo de la inversión",
            "tipo_formato": "Tipo de formato (IOARR, etc.)",
            "situacion": "Situación (APROBADO, VIABLE, etc.)",
            "costo_viable": "Costo de inversión viable/aprobado (S/)",
            "costo_actualizado": "Costo de inversión actualizado (S/)",
            "tiene_ficha_ejecucion": "Indica si tiene ficha de ejecución disponible",
            "tiene_ficha_seguimiento": "Indica si tiene ficha de seguimiento disponible",
            "fuente": "MEF Invierte"
        },
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc"
        },
        "notes": {
            "captcha": "El servicio maneja automáticamente el CAPTCHA de la página",
            "performance": "Consultas más rápidas que SEACE (15-20 segundos típicamente)",
            "reliability": "No tiene bloqueo de navegadores headless como SEACE"
        }
    }
