from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any

from app.core.database import get_db
from app.models.ubicacion import UbicacionDB

router = APIRouter(
    prefix="/ubicaciones",
    tags=["Ubicaciones"],
)

@router.get("/", summary="Listar ubicaciones")
async def listar_ubicaciones(
    tipo: Optional[str] = Query(None, description="Filtrar por tipo: CENTRO_POBLADO o CASERIO"),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    stmt = select(UbicacionDB).where(UbicacionDB.activo == True)
    if tipo:
        stmt = stmt.where(UbicacionDB.tipo == tipo)
    stmt = stmt.order_by(UbicacionDB.tipo.asc(), UbicacionDB.nombre.asc())

    result = await db.execute(stmt)
    rows: List[UbicacionDB] = result.scalars().all()

    data = [
        {
            "id": r.id,
            "nombre": r.nombre,
            "tipo": r.tipo,
            "departamento": r.departamento,
            "provincia": r.provincia,
            "distrito": r.distrito,
        }
        for r in rows
    ]
    return {"success": True, "data": data}

@router.get("/agrupadas", summary="Listar ubicaciones agrupadas por tipo")
async def listar_ubicaciones_agrupadas(
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    stmt = select(UbicacionDB).where(UbicacionDB.activo == True).order_by(UbicacionDB.nombre.asc())
    result = await db.execute(stmt)
    rows: List[UbicacionDB] = result.scalars().all()

    centros = [r.nombre for r in rows if (r.tipo or '').upper() == 'CENTRO_POBLADO']
    caserios = [r.nombre for r in rows if (r.tipo or '').upper() == 'CASERIO']

    return {
        "success": True,
        "data": {
            "centros_poblados": centros,
            "caserios": caserios,
            "total": len(rows)
        }
    }
