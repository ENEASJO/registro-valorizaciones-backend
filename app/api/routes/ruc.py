"""
Endpoints para consulta de RUC
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Dict, Any
import logging

from app.models.ruc import RUCInput, EmpresaInfo, ErrorResponse
from app.services.sunat_service import sunat_service
from app.utils.response_handler import response_handler
from app.utils.exceptions import BaseAppException

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1",
    tags=["RUC"],
    responses={
        400: {"model": ErrorResponse, "description": "Error de validación"},
        404: {"model": ErrorResponse, "description": "RUC no encontrado"},
        408: {"model": ErrorResponse, "description": "Timeout en la consulta"},
        500: {"model": ErrorResponse, "description": "Error interno del servidor"},
    }
)


@router.post(
    "/buscar",
    response_model=EmpresaInfo,
    summary="Buscar empresa por RUC",
    description="Consulta información de una empresa en SUNAT usando su RUC",
    response_description="Información completa de la empresa incluyendo representantes legales"
)
async def buscar_empresa(ruc_input: RUCInput) -> EmpresaInfo:
    """
    Buscar información de empresa por RUC en SUNAT
    
    - **ruc**: RUC de 11 dígitos de la empresa a consultar
    
    Retorna:
    - Información básica de la empresa (RUC, razón social)
    - Lista completa de representantes legales
    - Total de representantes encontrados
    """
    try:
        logger.info(f"Iniciando consulta para RUC: {ruc_input.ruc}")
        
        # Consultar empresa usando el servicio
        empresa_info = await sunat_service.consultar_empresa(ruc_input.ruc)
        
        logger.info(f"Consulta exitosa para RUC {ruc_input.ruc}: {empresa_info.total_representantes} representantes")
        
        return empresa_info
        
    except BaseAppException as e:
        logger.error(f"Error de aplicación consultando RUC {ruc_input.ruc}: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail={
                "error": True,
                "message": e.message,
                "details": e.details
            }
        )
    
    except Exception as e:
        logger.error(f"Error inesperado consultando RUC {ruc_input.ruc}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": True,
                "message": "Error interno del servidor",
                "details": "Ha ocurrido un error inesperado durante la consulta"
            }
        )


@router.get(
    "/health",
    summary="Verificar estado del servicio",
    description="Endpoint para verificar que el servicio está funcionando correctamente",
    tags=["Health"]
)
async def health_check() -> Dict[str, Any]:
    """Verificar estado del servicio"""
    return {
        "status": "healthy",
        "message": "Servicio de consulta RUC funcionando correctamente",
        "service": "ruc-api",
        "version": "1.0.0"
    }


@router.get(
    "/",
    summary="Información del API",
    description="Información básica sobre el API de consulta RUC",
    tags=["Info"]
)
async def api_info() -> Dict[str, Any]:
    """Información del API"""
    return {
        "name": "API Consultor RUC SUNAT",
        "version": "1.0.0",
        "description": "API para consultar información de empresas en SUNAT por RUC",
        "endpoints": {
            "POST /api/v1/buscar": "Buscar empresa por RUC",
            "GET /api/v1/health": "Verificar estado del servicio",
            "GET /api/v1/": "Información del API"
        },
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc"
        }
    }