"""
Endpoints para gestión de obras con integración MEF Invierte
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import date, datetime
from app.services.obras_mef_service import obras_mef_service
from app.services.mef_invierte_service import consultar_cui_mef

router = APIRouter()


# Modelos Pydantic
class DatosContrato(BaseModel):
    numero_contrato: str
    fecha_contrato: date
    plazo_ejecucion_dias: int
    monto_contratado: float


class Ubicacion(BaseModel):
    tipo: str  # zona_urbana, centro_poblado, caserio
    nombre_ubicacion: str
    direccion_especifica: Optional[str] = None
    coordenadas: Optional[dict] = None


class ObraCreate(BaseModel):
    cui: str
    importar_mef: bool = True
    datos_mef: Optional[dict] = None
    codigo_interno: Optional[str] = None
    contrato: DatosContrato
    ubicacion: Ubicacion
    estado_obra: str = "registrada"
    contratista_ruc: Optional[str] = None
    contratista_nombre: Optional[str] = None
    supervisor_ruc: Optional[str] = None
    supervisor_nombre: Optional[str] = None
    observaciones: Optional[str] = None


class ObraUpdate(BaseModel):
    codigo_interno: Optional[str] = None
    contrato: Optional[DatosContrato] = None
    ubicacion: Optional[Ubicacion] = None
    estado_obra: Optional[str] = None
    contratista_ruc: Optional[str] = None
    contratista_nombre: Optional[str] = None
    supervisor_ruc: Optional[str] = None
    supervisor_nombre: Optional[str] = None
    observaciones: Optional[str] = None


@router.post("/", response_model=dict)
async def crear_obra(obra: ObraCreate):
    """Crea una nueva obra, importando datos de MEF si es necesario"""
    try:
        # Si importar_mef es True, consultar MEF
        datos_mef = obra.datos_mef
        if obra.importar_mef and not datos_mef:
            # Consultar datos de MEF
            mef_response = await consultar_cui_mef(obra.cui)
            if mef_response.get("success"):
                datos_mef = mef_response.get("data")
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"No se pudieron obtener datos de MEF: {mef_response.get('message')}"
                )

        if not datos_mef:
            raise HTTPException(
                status_code=400,
                detail="Se requieren datos MEF para crear la obra"
            )

        # Extraer coordenadas si existen
        coords = obra.ubicacion.coordenadas or {}
        latitud = coords.get("latitud")
        longitud = coords.get("longitud")

        # Crear obra
        obra_creada = await obras_mef_service.crear_obra(
            cui=obra.cui,
            datos_mef=datos_mef,
            contrato_numero=obra.contrato.numero_contrato,
            contrato_fecha=obra.contrato.fecha_contrato,
            contrato_plazo_dias=obra.contrato.plazo_ejecucion_dias,
            contrato_monto=obra.contrato.monto_contratado,
            ubicacion_tipo=obra.ubicacion.tipo,
            ubicacion_nombre=obra.ubicacion.nombre_ubicacion,
            ubicacion_direccion=obra.ubicacion.direccion_especifica,
            ubicacion_latitud=latitud,
            ubicacion_longitud=longitud,
            estado_obra=obra.estado_obra,
            codigo_interno=obra.codigo_interno,
            contratista_ruc=obra.contratista_ruc,
            contratista_nombre=obra.contratista_nombre,
            supervisor_ruc=obra.supervisor_ruc,
            supervisor_nombre=obra.supervisor_nombre,
            observaciones=obra.observaciones,
        )

        return {"status": "success", "data": obra_creada}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=dict)
async def listar_obras(
    estado_obra: Optional[str] = Query(None),
    ubicacion_tipo: Optional[str] = Query(None),
    busqueda: Optional[str] = Query(None),
    limit: int = Query(100, le=500),
    offset: int = Query(0, ge=0)
):
    """Lista obras con filtros opcionales"""
    try:
        obras = await obras_mef_service.listar_obras(
            estado_obra=estado_obra,
            ubicacion_tipo=ubicacion_tipo,
            busqueda=busqueda,
            limit=limit,
            offset=offset
        )

        return {"status": "success", "data": obras}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/estadisticas", response_model=dict)
async def obtener_estadisticas():
    """Obtiene estadísticas generales de obras"""
    try:
        stats = await obras_mef_service.obtener_estadisticas()
        return stats

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{obra_id}", response_model=dict)
async def obtener_obra(obra_id: str):
    """Obtiene una obra por su ID"""
    try:
        obra = await obras_mef_service.obtener_obra_por_id(obra_id)

        if not obra:
            raise HTTPException(status_code=404, detail="Obra no encontrada")

        return {"status": "success", "data": obra}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cui/{cui}", response_model=dict)
async def obtener_obra_por_cui(cui: str):
    """Obtiene una obra por su CUI"""
    try:
        obra = await obras_mef_service.obtener_obra_por_cui(cui)

        if not obra:
            raise HTTPException(status_code=404, detail="Obra no encontrada")

        return {"status": "success", "data": obra}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{obra_id}", response_model=dict)
async def actualizar_obra(obra_id: str, obra_update: ObraUpdate):
    """Actualiza una obra existente"""
    try:
        # Construir diccionario de campos a actualizar
        campos = {}

        if obra_update.codigo_interno is not None:
            campos["codigo_interno"] = obra_update.codigo_interno

        if obra_update.contrato:
            campos["contrato_numero"] = obra_update.contrato.numero_contrato
            campos["contrato_fecha"] = obra_update.contrato.fecha_contrato
            campos["contrato_plazo_dias"] = obra_update.contrato.plazo_ejecucion_dias
            campos["contrato_monto"] = obra_update.contrato.monto_contratado

        if obra_update.ubicacion:
            campos["ubicacion_tipo"] = obra_update.ubicacion.tipo
            campos["ubicacion_nombre"] = obra_update.ubicacion.nombre_ubicacion
            campos["ubicacion_direccion"] = obra_update.ubicacion.direccion_especifica
            if obra_update.ubicacion.coordenadas:
                coords = obra_update.ubicacion.coordenadas
                campos["ubicacion_latitud"] = coords.get("latitud")
                campos["ubicacion_longitud"] = coords.get("longitud")

        if obra_update.estado_obra is not None:
            campos["estado_obra"] = obra_update.estado_obra

        if obra_update.contratista_ruc is not None:
            campos["contratista_ruc"] = obra_update.contratista_ruc

        if obra_update.contratista_nombre is not None:
            campos["contratista_nombre"] = obra_update.contratista_nombre

        if obra_update.supervisor_ruc is not None:
            campos["supervisor_ruc"] = obra_update.supervisor_ruc

        if obra_update.supervisor_nombre is not None:
            campos["supervisor_nombre"] = obra_update.supervisor_nombre

        if obra_update.observaciones is not None:
            campos["observaciones"] = obra_update.observaciones

        obra_actualizada = await obras_mef_service.actualizar_obra(obra_id, **campos)

        if not obra_actualizada:
            raise HTTPException(status_code=404, detail="Obra no encontrada")

        return {"status": "success", "data": obra_actualizada}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{obra_id}/actualizar-mef", response_model=dict)
async def actualizar_datos_mef(obra_id: str):
    """Actualiza los datos MEF de una obra consultando nuevamente el servicio MEF"""
    try:
        # Obtener obra actual
        obra = await obras_mef_service.obtener_obra_por_id(obra_id)

        if not obra:
            raise HTTPException(status_code=404, detail="Obra no encontrada")

        # Consultar datos actualizados de MEF
        cui = obra.get("cui")
        mef_response = await consultar_cui_mef(cui)

        if not mef_response.get("success"):
            raise HTTPException(
                status_code=400,
                detail=f"No se pudieron obtener datos de MEF: {mef_response.get('message')}"
            )

        datos_mef = mef_response.get("data")

        # Actualizar obra con nuevos datos MEF
        obra_actualizada = await obras_mef_service.actualizar_datos_mef(obra_id, datos_mef)

        return {"status": "success", "data": obra_actualizada}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{obra_id}", response_model=dict)
async def eliminar_obra(obra_id: str):
    """Elimina una obra"""
    try:
        success = await obras_mef_service.eliminar_obra(obra_id)

        if not success:
            raise HTTPException(status_code=404, detail="Obra no encontrada")

        return {"status": "success", "message": "Obra eliminada exitosamente"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
