"""
API endpoints para gestión de empresas
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.core.database import get_db_session
from app.services.empresa_service import EmpresaService
from app.models.empresa import (
    EmpresaCreateSchema,
    EmpresaResponse,
    EmpresaListResponse
)

router = APIRouter(prefix="/api/v1/empresas", tags=["empresas"])

@router.post("/", response_model=EmpresaResponse, status_code=status.HTTP_201_CREATED)
async def crear_empresa(
    empresa_data: EmpresaCreateSchema,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Crear nueva empresa con todos sus representantes
    
    Este endpoint:
    1. Crea la empresa con los datos básicos
    2. Guarda TODOS los representantes obtenidos de SUNAT/OECE
    3. Marca cual es el representante principal
    4. Asigna el representante principal como representante legal de la empresa
    """
    try:
        # Validar RUC
        if not EmpresaService.validar_ruc(empresa_data.ruc):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="RUC inválido. Debe tener 11 dígitos y comenzar con 10 o 20"
            )
        
        # Validar que tenga al menos un representante
        if not empresa_data.representantes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Debe proporcionar al menos un representante"
            )
        
        # Validar índice de representante principal
        if (empresa_data.representante_principal_id < 0 or 
            empresa_data.representante_principal_id >= len(empresa_data.representantes)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Índice de representante principal inválido"
            )
        
        # Crear empresa
        nueva_empresa = await EmpresaService.crear_empresa_con_representantes(
            session=db,
            empresa_data=empresa_data,
            created_by=1  # TODO: Obtener de autenticación
        )
        
        return nueva_empresa
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )

@router.get("/{empresa_id}", response_model=EmpresaResponse)
async def obtener_empresa(
    empresa_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """Obtener empresa por ID con todos sus representantes"""
    try:
        empresa = await EmpresaService.obtener_empresa_por_id(db, empresa_id)
        
        if not empresa:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Empresa no encontrada"
            )
        
        return empresa
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )

@router.get("/ruc/{ruc}", response_model=EmpresaResponse)
async def obtener_empresa_por_ruc(
    ruc: str,
    db: AsyncSession = Depends(get_db_session)
):
    """Obtener empresa por RUC con todos sus representantes"""
    try:
        if not EmpresaService.validar_ruc(ruc):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="RUC inválido"
            )
        
        empresa = await EmpresaService.obtener_empresa_por_ruc(db, ruc)
        
        if not empresa:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Empresa no encontrada con el RUC proporcionado"
            )
        
        return empresa
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )

@router.get("/", response_model=Dict[str, Any])
async def listar_empresas(
    page: int = Query(1, ge=1, description="Número de página"),
    per_page: int = Query(20, ge=1, le=100, description="Elementos por página"),
    search: Optional[str] = Query(None, description="Buscar por razón social, RUC o representante"),
    estado: Optional[str] = Query(None, description="Filtrar por estado"),
    db: AsyncSession = Depends(get_db_session)
):
    """Listar empresas con filtros y paginación"""
    try:
        resultado = await EmpresaService.listar_empresas(
            session=db,
            page=page,
            per_page=per_page,
            search=search,
            estado=estado
        )
        
        return {
            "success": True,
            "data": resultado,
            "message": f"Se encontraron {resultado['total']} empresa(s)"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )

@router.put("/{empresa_id}", response_model=EmpresaResponse)
async def actualizar_empresa(
    empresa_id: int,
    empresa_data: Dict[str, Any],
    db: AsyncSession = Depends(get_db_session)
):
    """Actualizar datos de empresa existente"""
    try:
        empresa_actualizada = await EmpresaService.actualizar_empresa(
            session=db,
            empresa_id=empresa_id,
            empresa_data=empresa_data,
            updated_by=1  # TODO: Obtener de autenticación
        )
        
        if not empresa_actualizada:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Empresa no encontrada"
            )
        
        return empresa_actualizada
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )

@router.delete("/{empresa_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_empresa(
    empresa_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """Eliminar empresa (eliminación lógica)"""
    try:
        eliminada = await EmpresaService.eliminar_empresa(
            session=db,
            empresa_id=empresa_id,
            deleted_by=1  # TODO: Obtener de autenticación
        )
        
        if not eliminada:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Empresa no encontrada"
            )
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )

@router.get("/{empresa_id}/representantes", response_model=List[Dict[str, Any]])
async def obtener_representantes_empresa(
    empresa_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """Obtener solo los representantes de una empresa"""
    try:
        empresa = await EmpresaService.obtener_empresa_por_id(db, empresa_id)
        
        if not empresa:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Empresa no encontrada"
            )
        
        return {
            "success": True,
            "data": {
                "empresa_id": empresa.id,
                "razon_social": empresa.razon_social,
                "representantes": empresa.representantes,
                "total_representantes": len(empresa.representantes),
                "representante_principal": next(
                    (repr for repr in empresa.representantes if repr.es_principal),
                    None
                )
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )

@router.post("/validar-ruc")
async def validar_ruc(
    ruc_data: Dict[str, str],
    db: AsyncSession = Depends(get_db_session)
):
    """Validar si un RUC ya está registrado"""
    try:
        ruc = ruc_data.get("ruc")
        if not ruc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="RUC es requerido"
            )
        
        if not EmpresaService.validar_ruc(ruc):
            return {
                "success": False,
                "valid": False,
                "message": "RUC inválido. Debe tener 11 dígitos y comenzar con 10 o 20"
            }
        
        empresa_existente = await EmpresaService.obtener_empresa_por_ruc(db, ruc)
        
        return {
            "success": True,
            "valid": True,
            "ruc": ruc,
            "exists": empresa_existente is not None,
            "message": (
                "RUC ya registrado en el sistema" if empresa_existente 
                else "RUC disponible para registro"
            ),
            "empresa": empresa_existente.dict() if empresa_existente else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )

# Endpoint para estadísticas
@router.get("/stats/summary")
async def obtener_estadisticas_empresas(
    db: AsyncSession = Depends(get_db_session)
):
    """Obtener estadísticas generales de empresas"""
    try:
        # Obtener todas las empresas para estadísticas básicas
        resultado = await EmpresaService.listar_empresas(
            session=db, 
            page=1, 
            per_page=10000  # Obtener todas para estadísticas
        )
        
        empresas = resultado["empresas"]
        total = resultado["total"]
        
        # Calcular estadísticas
        activas = len([e for e in empresas if e.estado == "ACTIVO"])
        inactivas = len([e for e in empresas if e.estado == "INACTIVO"])
        
        # Estadísticas por tipo
        tipos = {}
        for empresa in empresas:
            tipo = empresa.tipo_empresa
            tipos[tipo] = tipos.get(tipo, 0) + 1
        
        # Estadísticas por categoría
        categorias = {}
        for empresa in empresas:
            if empresa.categoria_contratista:
                cat = empresa.categoria_contratista
                categorias[cat] = categorias.get(cat, 0) + 1
        
        return {
            "success": True,
            "data": {
                "total_empresas": total,
                "activas": activas,
                "inactivas": inactivas,
                "por_tipo": tipos,
                "por_categoria": categorias,
                "ultima_actualizacion": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo estadísticas: {str(e)}"
        )