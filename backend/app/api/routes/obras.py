"""
Endpoints para gestión de obras
"""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime

from app.services.obra_service_turso import ObraServiceTurso
from app.models.obra import ObraCreate, ObraUpdate, ObraResponse, ESTADOS_OBRA
from app.utils.exceptions import ValidationException

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/obras",
    tags=["Obras"],
    responses={
        400: {"description": "Error de validación"},
        404: {"description": "Obra no encontrada"},
        409: {"description": "Conflicto - Obra ya existe"},
        500: {"description": "Error interno del servidor"},
    }
)

@router.post("/", summary="Crear nueva obra")
async def crear_obra(obra_data: ObraCreate) -> Dict[str, Any]:
    """
    Crear una nueva obra
    
    - **codigo**: Se genera automáticamente
    - **nombre**: Nombre de la obra (requerido)
    - **empresa_id**: ID de la empresa ejecutora (requerido)
    - **cliente**: Cliente o propietario
    - **ubicacion**: Ubicación de la obra
    - **monto_contractual**: Monto contractual inicial
    """
    try:
        logger.info(f"🔄 Creando nueva obra: {obra_data.nombre}")
        
        obra_creada = await ObraServiceTurso.crear_obra(obra_data)
        
        respuesta = {
            "success": True,
            "message": "Obra creada exitosamente",
            "data": obra_creada,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"✅ Obra creada exitosamente: {obra_creada['codigo']}")
        return respuesta
        
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
        logger.error(f"❌ Error creando obra: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "error": True,
                "success": False,
                "message": f"Error interno del servidor: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
        )

@router.get("/{obra_id}", summary="Obtener obra por ID")
async def obtener_obra(obra_id: int) -> Dict[str, Any]:
    """
    Obtener una obra específica por su ID
    """
    try:
        obra = await ObraServiceTurso.obtener_obra_por_id(obra_id)
        
        if not obra:
            return JSONResponse(
                status_code=404,
                content={
                    "error": True,
                    "success": False,
                    "message": f"Obra con ID {obra_id} no encontrada",
                    "timestamp": datetime.now().isoformat()
                }
            )
        
        return {
            "success": True,
            "data": obra,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo obra {obra_id}: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "error": True,
                "success": False,
                "message": f"Error interno del servidor: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
        )

@router.get("/codigo/{codigo}", summary="Obtener obra por código")
async def obtener_obra_por_codigo(codigo: str) -> Dict[str, Any]:
    """
    Obtener una obra específica por su código
    """
    try:
        obra = await ObraServiceTurso.obtener_obra_por_codigo(codigo)
        
        if not obra:
            return JSONResponse(
                status_code=404,
                content={
                    "error": True,
                    "success": False,
                    "message": f"Obra con código {codigo} no encontrada",
                    "timestamp": datetime.now().isoformat()
                }
            )
        
        return {
            "success": True,
            "data": obra,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo obra {codigo}: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "error": True,
                "success": False,
                "message": f"Error interno del servidor: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
        )

@router.get("/", summary="Listar obras")
async def listar_obras(
    empresa_id: Optional[int] = Query(None, description="Filtrar por empresa"),
    estado: Optional[str] = Query(None, description="Filtrar por estado"),
    limit: int = Query(50, ge=1, le=100, description="Límite de resultados"),
    offset: int = Query(0, ge=0, description="Offset para paginación")
) -> Dict[str, Any]:
    """
    Listar obras con filtros opcionales
    
    - **empresa_id**: Filtrar por empresa ejecutora
    - **estado**: Filtrar por estado de obra
    - **limit**: Número máximo de resultados (1-100)
    - **offset**: Número de registros a saltar
    """
    try:
        obras = await ObraServiceTurso.listar_obras(
            empresa_id=empresa_id,
            estado=estado,
            limit=limit,
            offset=offset
        )
        
        return {
            "success": True,
            "data": {
                "obras": obras,
                "total": len(obras),
                "limit": limit,
                "offset": offset
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error listando obras: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "error": True,
                "success": False,
                "message": f"Error interno del servidor: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
        )

@router.put("/{obra_id}", summary="Actualizar obra")
async def actualizar_obra(obra_id: int, obra_update: ObraUpdate) -> Dict[str, Any]:
    """
    Actualizar una obra existente
    """
    try:
        obra_actualizada = await ObraServiceTurso.actualizar_obra(obra_id, obra_update)
        
        if not obra_actualizada:
            return JSONResponse(
                status_code=404,
                content={
                    "error": True,
                    "success": False,
                    "message": f"Obra con ID {obra_id} no encontrada",
                    "timestamp": datetime.now().isoformat()
                }
            )
        
        return {
            "success": True,
            "message": "Obra actualizada exitosamente",
            "data": obra_actualizada,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error actualizando obra {obra_id}: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "error": True,
                "success": False,
                "message": f"Error interno del servidor: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
        )

@router.delete("/{obra_id}", summary="Eliminar obra")
async def eliminar_obra(obra_id: int) -> Dict[str, Any]:
    """
    Eliminar una obra (soft delete)
    """
    try:
        # Verificar que existe
        obra = await ObraServiceTurso.obtener_obra_por_id(obra_id)
        if not obra:
            return JSONResponse(
                status_code=404,
                content={
                    "error": True,
                    "success": False,
                    "message": f"Obra con ID {obra_id} no encontrada",
                    "timestamp": datetime.now().isoformat()
                }
            )
        
        success = await ObraServiceTurso.eliminar_obra(obra_id)
        
        if success:
            return {
                "success": True,
                "message": f"Obra {obra['codigo']} eliminada exitosamente",
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise Exception("No se pudo eliminar la obra")
            
    except Exception as e:
        logger.error(f"❌ Error eliminando obra {obra_id}: {str(e)}")
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
async def obtener_estados_obra() -> Dict[str, Any]:
    """
    Obtener lista de estados válidos para obras
    """
    return {
        "success": True,
        "data": {
            "estados": ESTADOS_OBRA,
            "descripcion": {
                "PLANIFICADA": "Obra en fase de planificación",
                "EN_PROCESO": "Obra en ejecución",
                "PARALIZADA": "Obra temporalmente detenida",
                "SUSPENDIDA": "Obra suspendida por decisión administrativa",
                "TERMINADA": "Obra físicamente terminada",
                "LIQUIDADA": "Obra terminada y liquidada",
                "CANCELADA": "Obra cancelada"
            }
        },
        "timestamp": datetime.now().isoformat()
    }