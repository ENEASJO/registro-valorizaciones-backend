"""
Endpoints para gestión de valorizaciones
"""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime

# from app.services.valorizacion_service_turso import ValorizacionServiceTurso
# TODO: Migrar a servicio Neon cuando esté disponible
from app.models.valorizacion import ValorizacionCreate, ValorizacionUpdate, ESTADOS_VALORIZACION, TIPOS_VALORIZACION
from app.utils.exceptions import ValidationException

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/valorizaciones",
    tags=["Valorizaciones"],
    responses={
        400: {"description": "Error de validación"},
        404: {"description": "Valorización no encontrada"},
        409: {"description": "Conflicto - Valorización ya existe"},
        500: {"description": "Error interno del servidor"},
    }
)

@router.post("/", summary="Crear nueva valorización")
async def crear_valorizacion(val_data: ValorizacionCreate) -> Dict[str, Any]:
    """
    Crear una nueva valorización
    
    - **codigo**: Se genera automáticamente basado en la obra
    - **obra_id**: ID de la obra (requerido)
    - **numero_valorizacion**: Número de valorización para la obra (requerido)
    - **periodo**: Período YYYY-MM (requerido)
    - **fecha_inicio**: Fecha de inicio del período (requerido)
    - **fecha_fin**: Fecha de fin del período (requerido)
    - **monto_ejecutado**: Monto ejecutado en el período
    """
    try:
        logger.info(f"🔄 Creando nueva valorización para obra {val_data.obra_id}")
        
        val_creada = await ValorizacionServiceTurso.crear_valorizacion(val_data)
        
        respuesta = {
            "success": True,
            "message": "Valorización creada exitosamente",
            "data": val_creada,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"✅ Valorización creada exitosamente: {val_creada['codigo']}")
        return respuesta
        
    except ValueError as e:
        logger.error(f"❌ Error de validación: {str(e)}")
        return JSONResponse(
            status_code=409,
            content={
                "error": True,
                "success": False,
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )
        
    except ValidationException as e:
        logger.error(f"❌ Error de validación: {str(e)}")
        return JSONResponse(
            status_code=400,
            content={
                "error": True,
                "success": False,
                "message": f"Error de validación: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
        )
    
    except Exception as e:
        logger.error(f"❌ Error creando valorización: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "error": True,
                "success": False,
                "message": f"Error interno del servidor: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
        )

@router.get("/{val_id}", summary="Obtener valorización por ID")
async def obtener_valorizacion(val_id: int) -> Dict[str, Any]:
    """
    Obtener una valorización específica por su ID
    """
    try:
        valorizacion = await ValorizacionServiceTurso.obtener_valorizacion_por_id(val_id)
        
        if not valorizacion:
            return JSONResponse(
                status_code=404,
                content={
                    "error": True,
                    "success": False,
                    "message": f"Valorización con ID {val_id} no encontrada",
                    "timestamp": datetime.now().isoformat()
                }
            )
        
        return {
            "success": True,
            "data": valorizacion,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo valorización {val_id}: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "error": True,
                "success": False,
                "message": f"Error interno del servidor: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
        )

@router.get("/codigo/{codigo}", summary="Obtener valorización por código")
async def obtener_valorizacion_por_codigo(codigo: str) -> Dict[str, Any]:
    """
    Obtener una valorización específica por su código
    """
    try:
        valorizacion = await ValorizacionServiceTurso.obtener_valorizacion_por_codigo(codigo)
        
        if not valorizacion:
            return JSONResponse(
                status_code=404,
                content={
                    "error": True,
                    "success": False,
                    "message": f"Valorización con código {codigo} no encontrada",
                    "timestamp": datetime.now().isoformat()
                }
            )
        
        return {
            "success": True,
            "data": valorizacion,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo valorización {codigo}: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "error": True,
                "success": False,
                "message": f"Error interno del servidor: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
        )

@router.get("/", summary="Listar valorizaciones")
async def listar_valorizaciones(
    obra_id: Optional[int] = Query(None, description="Filtrar por obra"),
    periodo: Optional[str] = Query(None, description="Filtrar por período (YYYY-MM)"),
    estado: Optional[str] = Query(None, description="Filtrar por estado"),
    limit: int = Query(50, ge=1, le=100, description="Límite de resultados"),
    offset: int = Query(0, ge=0, description="Offset para paginación")
) -> Dict[str, Any]:
    """
    Listar valorizaciones con filtros opcionales
    
    - **obra_id**: Filtrar por obra específica
    - **periodo**: Filtrar por período (formato YYYY-MM)
    - **estado**: Filtrar por estado de valorización
    - **limit**: Número máximo de resultados (1-100)
    - **offset**: Número de registros a saltar
    """
    try:
        valorizaciones = await ValorizacionServiceTurso.listar_valorizaciones(
            obra_id=obra_id,
            periodo=periodo,
            estado=estado,
            limit=limit,
            offset=offset
        )
        
        return {
            "success": True,
            "data": {
                "valorizaciones": valorizaciones,
                "total": len(valorizaciones),
                "limit": limit,
                "offset": offset
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error listando valorizaciones: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "error": True,
                "success": False,
                "message": f"Error interno del servidor: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
        )

@router.get("/obra/{obra_id}/resumen", summary="Resumen de valorizaciones por obra")
async def obtener_resumen_obra(obra_id: int) -> Dict[str, Any]:
    """
    Obtener resumen de todas las valorizaciones de una obra
    """
    try:
        resumen = await ValorizacionServiceTurso.obtener_resumen_por_obra(obra_id)
        
        return {
            "success": True,
            "data": resumen,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo resumen obra {obra_id}: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "error": True,
                "success": False,
                "message": f"Error interno del servidor: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
        )

@router.put("/{val_id}", summary="Actualizar valorización")
async def actualizar_valorizacion(val_id: int, val_update: ValorizacionUpdate) -> Dict[str, Any]:
    """
    Actualizar una valorización existente
    """
    try:
        val_actualizada = await ValorizacionServiceTurso.actualizar_valorizacion(val_id, val_update)
        
        if not val_actualizada:
            return JSONResponse(
                status_code=404,
                content={
                    "error": True,
                    "success": False,
                    "message": f"Valorización con ID {val_id} no encontrada",
                    "timestamp": datetime.now().isoformat()
                }
            )
        
        return {
            "success": True,
            "message": "Valorización actualizada exitosamente",
            "data": val_actualizada,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error actualizando valorización {val_id}: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "error": True,
                "success": False,
                "message": f"Error interno del servidor: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
        )

@router.delete("/{val_id}", summary="Eliminar valorización")
async def eliminar_valorizacion(val_id: int) -> Dict[str, Any]:
    """
    Eliminar una valorización (soft delete)
    """
    try:
        # Verificar que existe
        valorizacion = await ValorizacionServiceTurso.obtener_valorizacion_por_id(val_id)
        if not valorizacion:
            return JSONResponse(
                status_code=404,
                content={
                    "error": True,
                    "success": False,
                    "message": f"Valorización con ID {val_id} no encontrada",
                    "timestamp": datetime.now().isoformat()
                }
            )
        
        success = await ValorizacionServiceTurso.eliminar_valorizacion(val_id)
        
        if success:
            return {
                "success": True,
                "message": f"Valorización {valorizacion['codigo']} eliminada exitosamente",
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise Exception("No se pudo eliminar la valorización")
            
    except Exception as e:
        logger.error(f"❌ Error eliminando valorización {val_id}: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "error": True,
                "success": False,
                "message": f"Error interno del servidor: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
        )

@router.get("/estados/opciones", summary="Obtener estados disponibles")
async def obtener_estados_valorizacion() -> Dict[str, Any]:
    """
    Obtener lista de estados válidos para valorizaciones
    """
    return {
        "success": True,
        "data": {
            "estados": ESTADOS_VALORIZACION,
            "descripcion": {
                "BORRADOR": "Valorización en preparación",
                "PRESENTADA": "Valorización presentada al cliente",
                "EN_REVISION": "Valorización bajo revisión",
                "OBSERVADA": "Valorización con observaciones",
                "APROBADA": "Valorización aprobada",
                "PAGADA": "Valorización pagada",
                "ANULADA": "Valorización anulada"
            }
        },
        "timestamp": datetime.now().isoformat()
    }

@router.get("/tipos/opciones", summary="Obtener tipos disponibles")
async def obtener_tipos_valorizacion() -> Dict[str, Any]:
    """
    Obtener lista de tipos válidos para valorizaciones
    """
    return {
        "success": True,
        "data": {
            "tipos": TIPOS_VALORIZACION,
            "descripcion": {
                "MENSUAL": "Valorización mensual regular",
                "QUINCENAL": "Valorización quincenal",
                "ADICIONAL": "Valorización de trabajos adicionales",
                "FINAL": "Valorización final de obra",
                "LIQUIDACION": "Valorización de liquidación"
            }
        },
        "timestamp": datetime.now().isoformat()
    }