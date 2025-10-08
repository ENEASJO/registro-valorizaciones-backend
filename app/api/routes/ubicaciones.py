from fastapi import APIRouter, Query
from typing import Optional, Dict, Any
from app.services.ubicacion_service_neon import obtener_ubicaciones_agrupadas, obtener_ubicaciones

router = APIRouter(
    prefix="/ubicaciones",
    tags=["Ubicaciones"],
)

@router.get("/", summary="Listar ubicaciones")
def listar_ubicaciones(
    tipo: Optional[str] = Query(None, description="Filtrar por tipo: CENTRO_POBLADO o CASERIO")
) -> Dict[str, Any]:
    """
    Lista todas las ubicaciones, opcionalmente filtradas por tipo.
    """
    try:
        ubicaciones = obtener_ubicaciones(tipo=tipo)
        return {"success": True, "data": ubicaciones}
    except Exception as e:
        return {"success": False, "message": f"Error al obtener ubicaciones: {str(e)}"}

@router.get("/agrupadas", summary="Listar ubicaciones agrupadas por tipo")
def listar_ubicaciones_agrupadas() -> Dict[str, Any]:
    """
    Lista ubicaciones agrupadas por tipo (urbana, centro_poblado, caserio).
    """
    try:
        ubicaciones = obtener_ubicaciones_agrupadas()
        return {
            "status": "success",
            "data": ubicaciones
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error al obtener ubicaciones: {str(e)}"
        }
