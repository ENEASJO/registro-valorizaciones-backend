"""
Endpoints para gestión de obras
"""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime

from app.services.obra_service_neon import ObraServiceNeon
from app.models.obra import ObraCreate, ObraUpdate, ObraResponse, ESTADOS_OBRA
from app.utils.exceptions import ValidationException

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/obras",
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
        
        obra_creada = await ObraServiceNeon.crear_obra(obra_data)
        
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
        obra = await ObraServiceNeon.obtener_obra_por_id(obra_id)
        
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
        obra = await ObraServiceNeon.obtener_obra_por_codigo(codigo)
        
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
        logger.info(f"🎯 [ENDPOINT] Listar obras llamado con empresa_id={empresa_id}, estado={estado}, limit={limit}, offset={offset}")

        obras = await ObraServiceNeon.listar_obras(
            empresa_id=empresa_id,
            estado=estado,
            limit=limit,
            offset=offset
        )

        logger.info(f"✅ [ENDPOINT] Obtenidas {len(obras)} obras del servicio")

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
        logger.error(f"❌ [ENDPOINT] Error listando obras: {str(e)}")
        logger.error(f"❌ [ENDPOINT] Tipo: {type(e).__name__}")
        import traceback
        logger.error(f"❌ [ENDPOINT] Traceback: {traceback.format_exc()}")
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
        obra_actualizada = await ObraServiceNeon.actualizar_obra(obra_id, obra_update)
        
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
        obra = await ObraServiceNeon.obtener_obra_por_id(obra_id)
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
        
        success = await ObraServiceNeon.eliminar_obra(obra_id)
        
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

@router.get("/test-db-connection", summary="Test database connection")
async def test_db_connection():
    """Test simple para verificar conexión a base de datos"""
    try:
        from app.core.database import database

        logger.info("🧪 [TEST] Iniciando test de conexión a base de datos")

        # Test 1: Verificar si está conectado
        is_connected = database.is_connected
        logger.info(f"🧪 [TEST] database.is_connected = {is_connected}")

        # Test 2: Query simple
        query = "SELECT 1 as test"
        result = await database.fetch_one(query=query)
        logger.info(f"🧪 [TEST] Query simple exitoso: {result}")

        # Test 3: Contar obras
        count_query = "SELECT COUNT(*) as total FROM obras"
        count_result = await database.fetch_one(query=count_query)
        logger.info(f"🧪 [TEST] Count obras: {count_result}")

        return {
            "success": True,
            "tests": {
                "is_connected": is_connected,
                "simple_query": dict(result) if result else None,
                "obras_count": dict(count_result) if count_result else None
            },
            "message": "Tests completados exitosamente",
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"❌ [TEST] Error en test: {str(e)}")
        import traceback
        logger.error(f"❌ [TEST] Traceback: {traceback.format_exc()}")
        return JSONResponse(
            status_code=500,
            content={
                "error": True,
                "message": f"Error en test: {str(e)}",
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