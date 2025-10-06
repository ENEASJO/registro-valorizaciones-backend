"""
Endpoints para consulta SEACE (Sistema Electrónico de Contrataciones del Estado)
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Dict, Any
import logging
import asyncio

from app.models.seace import SEACEInput, ObraSEACE, ErrorResponseSEACE
from app.services.seace_service import seace_service
from app.services.job_manager import job_manager, JobStatus
from app.utils.exceptions import BaseAppException

logger = logging.getLogger(__name__)


async def process_seace_job(job_id: str, cui: str, anio: int):
    """Procesa un job de SEACE en segundo plano"""
    try:
        logger.info(f"Iniciando procesamiento de job {job_id} para CUI {cui}, año {anio}")
        job_manager.update_status(job_id, JobStatus.RUNNING)

        # Ejecutar scraping
        resultado = await seace_service.consultar_obra(cui, anio)

        # Guardar resultado
        job_manager.set_result(job_id, resultado)
        logger.info(f"Job {job_id} completado exitosamente")

    except BaseAppException as e:
        logger.error(f"Error de aplicación en job {job_id}: {str(e)}")
        job_manager.set_error(job_id, e.message, e.details)

    except Exception as e:
        logger.error(f"Error inesperado en job {job_id}: {str(e)}")
        job_manager.set_error(job_id, "Error inesperado", str(e))

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
    "/consultar-async",
    summary="Iniciar consulta asíncrona de obra en SEACE",
    description="Crea un job para consultar información de una obra en SEACE. Retorna un job_id para consultar el estado.",
    response_description="ID del job creado"
)
async def consultar_obra_seace_async(seace_input: SEACEInput, background_tasks: BackgroundTasks) -> Dict[str, Any]:
    """
    Inicia una consulta asíncrona de obra en SEACE

    - **cui**: Código Único de Inversión (7-10 dígitos)
    - **anio**: Año de la convocatoria (2000-2100)

    Retorna:
    - job_id: ID del job para consultar el estado
    - status: Estado inicial del job (pending)
    - message: Mensaje informativo
    """
    try:
        # Crear job
        job_id = job_manager.create_job(seace_input.cui, seace_input.anio)

        # Iniciar procesamiento en segundo plano
        background_tasks.add_task(process_seace_job, job_id, seace_input.cui, seace_input.anio)

        logger.info(f"Job {job_id} creado para CUI {seace_input.cui}, año {seace_input.anio}")

        return {
            "job_id": job_id,
            "status": "pending",
            "message": f"Consulta iniciada para CUI {seace_input.cui}, año {seace_input.anio}",
            "check_status_url": f"/api/v1/seace/job/{job_id}"
        }

    except Exception as e:
        logger.error(f"Error creando job para CUI {seace_input.cui}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": True,
                "message": "Error al crear job de consulta",
                "details": str(e)
            }
        )


@router.get(
    "/job/{job_id}",
    summary="Consultar estado de un job de SEACE",
    description="Obtiene el estado y resultado de un job de consulta SEACE",
    response_description="Estado del job y resultado si está completado"
)
async def get_job_status(job_id: str) -> Dict[str, Any]:
    """
    Consulta el estado de un job de SEACE

    - **job_id**: ID del job a consultar

    Retorna:
    - job_id: ID del job
    - status: Estado actual (pending, running, completed, failed)
    - result: Resultado de la consulta (solo si status=completed)
    - error: Mensaje de error (solo si status=failed)
    """
    job = job_manager.get_job(job_id)

    if not job:
        raise HTTPException(
            status_code=404,
            detail={
                "error": True,
                "message": f"Job {job_id} no encontrado",
                "details": "El job no existe o ha expirado"
            }
        )

    response = {
        "job_id": job.job_id,
        "status": job.status.value,
        "cui": job.cui,
        "anio": job.anio,
        "created_at": job.created_at.isoformat()
    }

    if job.started_at:
        response["started_at"] = job.started_at.isoformat()

    if job.completed_at:
        response["completed_at"] = job.completed_at.isoformat()

    if job.status == JobStatus.COMPLETED and job.result:
        response["result"] = job.result.dict()

    if job.status == JobStatus.FAILED:
        response["error"] = job.error
        if job.error_details:
            response["error_details"] = job.error_details

    return response


@router.post(
    "/consultar",
    response_model=ObraSEACE,
    summary="Consultar obra en SEACE por CUI y año (síncrono)",
    description="Consulta información detallada de una obra en SEACE. ADVERTENCIA: Puede exceder timeout de 30s. Usar /consultar-async para operaciones confiables.",
    response_description="Información completa de la obra"
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
