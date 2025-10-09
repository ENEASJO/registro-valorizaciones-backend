from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from app.services.plantel_service_neon import (
    obtener_plantel_por_obra,
    agregar_profesional,
    actualizar_profesional,
    eliminar_profesional,
    obtener_catalogo_cargos
)

router = APIRouter(
    prefix="/plantel",
    tags=["Plantel Profesional"],
)


class ProfesionalCreate(BaseModel):
    obra_id: str
    nombres: str
    apellidos: str
    cargo_categoria: str
    cargo_tecnico: str


class ProfesionalUpdate(BaseModel):
    nombres: Optional[str] = None
    apellidos: Optional[str] = None
    cargo_categoria: Optional[str] = None
    cargo_tecnico: Optional[str] = None


@router.get("/cargos", summary="Obtener catálogo de cargos técnicos")
def listar_cargos() -> Dict[str, Any]:
    """
    Obtiene el catálogo completo de categorías y cargos técnicos disponibles.
    """
    try:
        catalogo = obtener_catalogo_cargos()
        return {
            "status": "success",
            "data": catalogo
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error al obtener catálogo de cargos: {str(e)}"
        }


@router.get("/obra/{obra_id}", summary="Obtener plantel de una obra")
def listar_plantel_obra(obra_id: str) -> Dict[str, Any]:
    """
    Obtiene todos los profesionales del plantel de una obra específica.
    """
    try:
        plantel = obtener_plantel_por_obra(obra_id)
        return {
            "status": "success",
            "data": plantel
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error al obtener plantel: {str(e)}"
        }


@router.post("/", summary="Agregar profesional al plantel")
def crear_profesional(profesional: ProfesionalCreate) -> Dict[str, Any]:
    """
    Agrega un nuevo profesional al plantel de una obra.
    """
    try:
        nuevo_profesional = agregar_profesional(
            obra_id=profesional.obra_id,
            nombres=profesional.nombres,
            apellidos=profesional.apellidos,
            cargo_categoria=profesional.cargo_categoria,
            cargo_tecnico=profesional.cargo_tecnico
        )

        if nuevo_profesional:
            return {
                "status": "success",
                "data": nuevo_profesional
            }
        else:
            raise HTTPException(status_code=500, detail="No se pudo crear el profesional")

    except Exception as e:
        return {
            "status": "error",
            "message": f"Error al crear profesional: {str(e)}"
        }


@router.put("/{profesional_id}", summary="Actualizar profesional del plantel")
def modificar_profesional(profesional_id: str, profesional: ProfesionalUpdate) -> Dict[str, Any]:
    """
    Actualiza los datos de un profesional del plantel.
    """
    try:
        profesional_actualizado = actualizar_profesional(
            profesional_id=profesional_id,
            nombres=profesional.nombres,
            apellidos=profesional.apellidos,
            cargo_categoria=profesional.cargo_categoria,
            cargo_tecnico=profesional.cargo_tecnico
        )

        if profesional_actualizado:
            return {
                "status": "success",
                "data": profesional_actualizado
            }
        else:
            raise HTTPException(status_code=404, detail="Profesional no encontrado")

    except Exception as e:
        return {
            "status": "error",
            "message": f"Error al actualizar profesional: {str(e)}"
        }


@router.delete("/{profesional_id}", summary="Eliminar profesional del plantel")
def borrar_profesional(profesional_id: str) -> Dict[str, Any]:
    """
    Elimina (desactiva) un profesional del plantel.
    """
    try:
        eliminado = eliminar_profesional(profesional_id)

        if eliminado:
            return {
                "status": "success",
                "message": "Profesional eliminado correctamente"
            }
        else:
            raise HTTPException(status_code=404, detail="Profesional no encontrado")

    except Exception as e:
        return {
            "status": "error",
            "message": f"Error al eliminar profesional: {str(e)}"
        }
