"""
Endpoints para consulta MEF Invierte
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, Any
import logging

from app.models.mef_invierte import MEFInvierteInput, ProyectoMEFInvierte, ErrorResponseMEF
from app.services.mef_invierte_service import scrape_mef_invierte
from app.utils.exceptions import BaseAppException

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/mef-invierte",
    tags=["MEF Invierte"],
    responses={
        400: {"model": ErrorResponseMEF, "description": "Error de validación"},
        404: {"model": ErrorResponseMEF, "description": "Proyecto no encontrado en MEF Invierte"},
        500: {"model": ErrorResponseMEF, "description": "Error interno del servidor"},
    }
)


@router.post(
    "/consultar",
    response_model=Dict[str, Any],
    summary="Consultar proyecto en MEF Invierte por CUI",
    description="Consulta información completa de un proyecto de inversión en MEF Invierte incluyendo el Formato N°08-C",
    response_description="Información completa del proyecto"
)
async def consultar_proyecto_mef(mef_input: MEFInvierteInput) -> Dict[str, Any]:
    """
    Consulta información completa de proyecto por CUI en MEF Invierte

    - **cui**: Código Único de Inversión (7-10 dígitos)

    Retorna:
    - Datos de resultados de búsqueda
    - Datos generales de ejecución
    - Lista de modificaciones
    - Formato N°08-C completo con:
      - Encabezado (fecha registro, etapa, estado)
      - Datos generales del proyecto
      - Sección A: Datos de Formulación y Evaluación
        - Responsabilidad funcional
        - Articulación con el PMI
        - Institucionalidad (OPMI, UF, UEI, UEP)
      - Sección B: Datos de Ejecución
        - Programación de la ejecución
        - Modificaciones durante la ejecución
      - Costos finales actualizados
    """
    try:
        logger.info(f"Iniciando consulta MEF Invierte para CUI: {mef_input.cui}")

        # Ejecutar scraping
        resultado = await scrape_mef_invierte(mef_input.cui)

        logger.info(f"Consulta MEF Invierte exitosa para CUI {mef_input.cui}")

        return resultado

    except NotImplementedError as e:
        logger.error(f"Error de implementación: {str(e)}")
        raise HTTPException(
            status_code=501,
            detail={
                "error": True,
                "message": "Funcionalidad no implementada",
                "details": str(e),
                "cui": mef_input.cui,
                "fuente": "MEF Invierte"
            }
        )

    except BaseAppException as e:
        logger.error(f"Error de aplicación consultando MEF Invierte CUI {mef_input.cui}: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail={
                "error": True,
                "message": e.message,
                "details": e.details,
                "cui": mef_input.cui,
                "fuente": "MEF Invierte"
            }
        )

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
    response_model=Dict[str, Any],
    summary="Consultar proyecto en MEF Invierte por CUI (GET)",
    description="Consulta información completa de un proyecto de inversión en MEF Invierte usando CUI via GET",
    response_description="Información completa del proyecto"
)
async def consultar_proyecto_mef_get(cui: str) -> Dict[str, Any]:
    """
    Consulta información completa de proyecto por CUI en MEF Invierte (método GET)

    - **cui**: CUI en la URL

    Retorna la misma información que el endpoint POST
    """
    try:
        # Crear objeto MEFInvierteInput para validación
        mef_input = MEFInvierteInput(cui=cui)

        # Usar la misma lógica del endpoint POST
        return await consultar_proyecto_mef(mef_input)

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
            "Consulta de información de proyectos por CUI",
            "Extracción de datos de resultado de búsqueda",
            "Extracción de lista de modificaciones",
            "Extracción completa del Formato N°08-C",
            "Datos de Formulación y Evaluación",
            "Datos de Ejecución",
            "Costos actualizados",
            "Resolución automática de captcha con OCR"
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
        "description": "API para consultar información detallada de proyectos de inversión en MEF Invierte por CUI",
        "endpoints": {
            "POST /api/v1/mef-invierte/consultar": "Consultar proyecto por CUI (POST)",
            "GET /api/v1/mef-invierte/consultar/{cui}": "Consultar proyecto por CUI (GET)",
            "GET /api/v1/mef-invierte/health": "Verificar estado del servicio",
            "GET /api/v1/mef-invierte/info": "Información del API"
        },
        "features": {
            "datos_resultado": "Extrae datos de la tabla de resultados de búsqueda",
            "datos_ejecucion": "Extrae datos generales de ejecución y modificaciones",
            "formato_08c": "Extrae información completa del Formato N°08-C",
            "auto_captcha": "Resolución automática de captcha con OCR (requiere pytesseract)"
        },
        "data_sources": {
            "primary": "MEF Invierte - Ministerio de Economía y Finanzas",
            "url": "https://ofi5.mef.gob.pe/invierte/consultapublica/consultainversiones"
        },
        "formato_08c_sections": {
            "encabezado": "Título, fecha de registro, etapa, estado",
            "datos_generales": "CUI, nombre de la inversión",
            "seccion_a": {
                "responsabilidad_funcional": "Función, división, grupo, sector",
                "pmi": "Articulación con el PMI, brechas, contribución",
                "institucionalidad": "OPMI, UF, UEI, UEP"
            },
            "seccion_b": {
                "programacion_ejecucion": "Subtotales, expediente técnico, supervisión, liquidación",
                "modificaciones": "Lista de modificaciones durante la ejecución"
            },
            "costos_finales": "Costo actualizado, control concurrente, controversias, total"
        },
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc"
        },
        "requirements": {
            "pytesseract": "Necesario para resolución automática de captcha",
            "pillow": "Necesario para procesamiento de imagen del captcha"
        }
    }
