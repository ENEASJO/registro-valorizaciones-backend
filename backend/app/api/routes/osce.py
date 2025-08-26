"""
Endpoints para consulta OSCE (Organismo Supervisor de las Contrataciones del Estado)
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Dict, Any
import logging

from app.models.ruc import RUCInput
from app.models.osce import EmpresaOSCE, ErrorResponseOSCE
from app.services.osce_service import osce_service
from app.utils.response_handler import response_handler
from app.utils.exceptions import BaseAppException

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/osce",
    tags=["OSCE"],
    responses={
        400: {"model": ErrorResponseOSCE, "description": "Error de validación"},
        404: {"model": ErrorResponseOSCE, "description": "RUC no encontrado en OSCE"},
        408: {"model": ErrorResponseOSCE, "description": "Timeout en la consulta"},
        500: {"model": ErrorResponseOSCE, "description": "Error interno del servidor"},
    }
)


@router.post(
    "/consultar",
    response_model=EmpresaOSCE,
    summary="Consultar empresa en OSCE por RUC",
    description="Consulta información detallada de una empresa en OSCE usando su RUC",
    response_description="Información completa de la empresa incluyendo contacto, especialidades e integrantes"
)
async def consultar_empresa_osce(ruc_input: RUCInput) -> EmpresaOSCE:
    """
    Consulta información completa de empresa por RUC en OSCE
    
    - **ruc**: RUC de 11 dígitos de la empresa a consultar
    
    Retorna:
    - Información básica de la empresa (RUC, razón social, estado)
    - Información de contacto (teléfono, email, dirección)
    - Lista detallada de especialidades
    - Lista de integrantes/socios de la empresa
    - Datos de vigencia y capacidad de contratación
    """
    try:
        logger.info(f"Iniciando consulta OSCE para RUC: {ruc_input.ruc}")
        
        # Consultar empresa usando el servicio OSCE
        empresa_info = await osce_service.consultar_empresa(ruc_input.ruc)
        
        logger.info(f"Consulta OSCE exitosa para RUC {ruc_input.ruc}: {empresa_info.total_especialidades} especialidades, {empresa_info.total_integrantes} integrantes")
        
        return empresa_info
        
    except BaseAppException as e:
        logger.error(f"Error de aplicación consultando OSCE RUC {ruc_input.ruc}: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail={
                "error": True,
                "message": e.message,
                "details": e.details,
                "ruc": ruc_input.ruc,
                "fuente": "OSCE"
            }
        )
    
    except Exception as e:
        logger.error(f"Error inesperado consultando OSCE RUC {ruc_input.ruc}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": True,
                "message": "Error interno del servidor",
                "details": "Ha ocurrido un error inesperado durante la consulta OSCE",
                "ruc": ruc_input.ruc,
                "fuente": "OSCE"
            }
        )


@router.get(
    "/consultar/{ruc}",
    response_model=EmpresaOSCE,
    summary="Consultar empresa en OSCE por RUC (GET)",
    description="Consulta información detallada de una empresa en OSCE usando su RUC via GET",
    response_description="Información completa de la empresa incluyendo contacto, especialidades e integrantes"
)
async def consultar_empresa_osce_get(ruc: str) -> EmpresaOSCE:
    """
    Consulta información completa de empresa por RUC en OSCE (método GET)
    
    - **ruc**: RUC de 11 dígitos en la URL
    
    Retorna la misma información que el endpoint POST
    """
    try:
        # Crear objeto RUCInput para validación
        ruc_input = RUCInput(ruc=ruc)
        
        # Usar la misma lógica del endpoint POST
        return await consultar_empresa_osce(ruc_input)
        
    except Exception as e:
        logger.error(f"Error en consulta GET OSCE para RUC {ruc}: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail={
                "error": True,
                "message": f"Error en consulta OSCE: {str(e)}",
                "ruc": ruc,
                "fuente": "OSCE"
            }
        )


@router.get(
    "/health",
    summary="Verificar estado del servicio OSCE",
    description="Endpoint para verificar que el servicio OSCE está funcionando correctamente",
    tags=["Health"]
)
async def health_check_osce() -> Dict[str, Any]:
    """Verificar estado del servicio OSCE"""
    return {
        "status": "healthy",
        "message": "Servicio de consulta OSCE funcionando correctamente",
        "service": "osce-api",
        "version": "1.0.0",
        "features": [
            "Consulta de información básica de empresa",
            "Extracción de información de contacto (teléfono, email)",
            "Listado detallado de especialidades",
            "Información de integrantes/socios",
            "Datos de vigencia y capacidad de contratación",
            "Navegación a perfiles detallados"
        ]
    }


@router.get(
    "/info",
    summary="Información del API OSCE",
    description="Información detallada sobre el API de consulta OSCE",
    tags=["Info"]
)
async def api_info_osce() -> Dict[str, Any]:
    """Información del API OSCE"""
    return {
        "name": "API Consultor OSCE",
        "version": "1.0.0",
        "description": "API para consultar información detallada de empresas en OSCE por RUC",
        "endpoints": {
            "POST /api/v1/osce/consultar": "Consultar empresa por RUC (POST)",
            "GET /api/v1/osce/consultar/{ruc}": "Consultar empresa por RUC (GET)",
            "GET /api/v1/osce/health": "Verificar estado del servicio",
            "GET /api/v1/osce/info": "Información del API"
        },
        "features": {
            "basic_info": "Extrae información básica de la empresa (RUC, razón social, estado)",
            "contact_info": "Extrae teléfono, email y dirección de contacto",
            "specialties": "Lista detallada de especialidades con códigos y categorías",
            "members": "Información de integrantes, socios y representantes",
            "additional_data": "Vigencia, capacidad de contratación, fechas de registro"
        },
        "data_sources": {
            "primary": "OSCE - Organismo Supervisor de las Contrataciones del Estado",
            "url": "https://apps.osce.gob.pe/perfilprov-ui/"
        },
        "response_format": {
            "ruc": "RUC de la empresa consultada",
            "fuente": "OSCE",
            "razon_social": "Razón social de la empresa",
            "estado_registro": "Estado del registro (HABILITADO, SUSPENDIDO, etc.)",
            "telefono": "Número de teléfono principal",
            "email": "Correo electrónico principal",
            "especialidades": "Array de especialidades como strings",
            "especialidades_detalle": "Array de especialidades con códigos y detalles",
            "integrantes": "Array de integrantes/socios con sus datos",
            "contacto": "Objeto con información completa de contacto",
            "total_especialidades": "Número total de especialidades",
            "total_integrantes": "Número total de integrantes"
        },
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc"
        }
    }