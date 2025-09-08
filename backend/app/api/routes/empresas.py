"""
API endpoints para gestión de empresas (usando Turso)
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, status
from datetime import datetime
import re

from app.services.empresa_service_turso_enhanced import EmpresaServiceTurso
from app.models.empresa import (
    EmpresaCreateSchema,
    EmpresaResponse,
    EmpresaListResponse,
    RepresentanteResponse
)

router = APIRouter(prefix="/api/v1/empresas", tags=["empresas"])

# Instancia del servicio Turso
empresa_service = EmpresaServiceTurso()

def validar_ruc(ruc: str) -> bool:
    """Validar formato de RUC"""
    if not ruc or len(ruc) != 11:
        return False
    if not ruc.isdigit():
        return False
    if not (ruc.startswith('10') or ruc.startswith('20')):
        return False
    return True

def convertir_empresa_dict_a_response(empresa_dict: Dict[str, Any]) -> EmpresaResponse:
    """Convertir diccionario de empresa de Turso a EmpresaResponse"""
    return EmpresaResponse(
        id=empresa_dict.get('id', 0),
        codigo=empresa_dict.get('codigo', ''),
        ruc=empresa_dict.get('ruc', ''),
        razon_social=empresa_dict.get('razon_social', ''),
        nombre_comercial=empresa_dict.get('nombre_comercial'),
        email=empresa_dict.get('email'),
        telefono=empresa_dict.get('telefono'),
        celular=empresa_dict.get('celular'),
        direccion=empresa_dict.get('direccion'),
        representante_legal=empresa_dict.get('representante_legal'),
        dni_representante=empresa_dict.get('dni_representante'),
        estado=empresa_dict.get('estado', 'ACTIVO'),
        tipo_empresa=empresa_dict.get('tipo_empresa', 'SAC'),
        categoria_contratista=empresa_dict.get('categoria_contratista'),
        especialidades=empresa_dict.get('especialidades', []),
        representantes=[],  # Por ahora vacío, se puede extender
        total_representantes=0,
        activo=bool(empresa_dict.get('activo', True)),
        created_at=datetime.fromisoformat(empresa_dict.get('created_at', datetime.now().isoformat())),
        updated_at=datetime.fromisoformat(empresa_dict.get('updated_at', datetime.now().isoformat()))
    )

@router.post("/", response_model=EmpresaResponse, status_code=status.HTTP_201_CREATED)
async def crear_empresa(
    empresa_data: EmpresaCreateSchema
):
    """
    Crear nueva empresa con todos sus representantes usando Turso
    
    Este endpoint:
    1. Valida el RUC y los representantes
    2. Crea la empresa en Turso
    3. Retorna la empresa creada
    """
    try:
        # Validar RUC
        if not validar_ruc(empresa_data.ruc):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="RUC inválido. Debe tener 11 dígitos y comenzar con 10 o 20"
            )
        
        # Verificar si ya existe
        empresa_existente = empresa_service.get_empresa_by_ruc(empresa_data.ruc)
        if empresa_existente:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe una empresa con este RUC"
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
        
        # Preparar datos para crear empresa
        representante_principal = empresa_data.representantes[empresa_data.representante_principal_id]
        
        datos_empresa = {
            'data': {
                'razon_social': empresa_data.razon_social,
                'contacto': {
                    'email': empresa_data.email or '',
                    'telefono': empresa_data.celular or '',
                    'direccion': empresa_data.direccion or ''
                },
                'miembros': [{
                    'nombre': representante_principal.nombre,
                    'numero_documento': representante_principal.numero_documento,
                    'cargo': representante_principal.cargo
                }]
            }
        }
        
        # Crear empresa en Turso
        empresa_id = empresa_service.save_empresa_from_consulta(
            ruc=empresa_data.ruc,
            datos_consulta=datos_empresa
        )
        
        if not empresa_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error creando empresa en la base de datos"
            )
        
        # Obtener empresa creada para retornar
        empresa_creada = empresa_service.get_empresa_by_ruc(empresa_data.ruc)
        if not empresa_creada:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error obteniendo empresa creada"
            )
        
        return convertir_empresa_dict_a_response(empresa_creada)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )

@router.get("/{empresa_id}", response_model=EmpresaResponse)
async def obtener_empresa(
    empresa_id: int
):
    """Obtener empresa por ID usando Turso"""
    try:
        # Por ahora, listar todas y filtrar por ID
        # En una implementación más completa se haría una consulta directa por ID
        empresas = empresa_service.list_empresas(limit=1000)
        empresa = next((e for e in empresas if e.get('id') == empresa_id), None)
        
        if not empresa:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Empresa no encontrada"
            )
        
        return convertir_empresa_dict_a_response(empresa)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )

@router.get("/ruc/{ruc}", response_model=EmpresaResponse)
async def obtener_empresa_por_ruc(
    ruc: str
):
    """Obtener empresa por RUC usando Turso"""
    try:
        if not validar_ruc(ruc):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="RUC inválido"
            )
        
        empresa = empresa_service.get_empresa_by_ruc(ruc)
        
        if not empresa:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Empresa no encontrada con el RUC proporcionado"
            )
        
        return convertir_empresa_dict_a_response(empresa)
        
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
    estado: Optional[str] = Query(None, description="Filtrar por estado")
):
    """Listar empresas con filtros y paginación usando Turso"""
    try:
        # Calcular offset
        offset = (page - 1) * per_page
        
        # Si hay búsqueda, usar el método de búsqueda
        if search:
            empresas_raw = empresa_service.search_empresas(search, limit=per_page * 5)  # Más resultados para filtrar
        else:
            empresas_raw = empresa_service.list_empresas(limit=per_page * 5, offset=offset)
        
        # Filtrar por estado si se especifica
        if estado:
            empresas_raw = [e for e in empresas_raw if e.get('estado', '').upper() == estado.upper()]
        
        # Aplicar paginación manual si fue búsqueda
        if search:
            total = len(empresas_raw)
            empresas_raw = empresas_raw[offset:offset + per_page]
        else:
            # Para listado normal, asumir que puede haber más
            total = len(empresas_raw) + (per_page if len(empresas_raw) == per_page else 0)
        
        # Convertir a formato de respuesta
        empresas = [convertir_empresa_dict_a_response(emp) for emp in empresas_raw]
        
        resultado = {
            "empresas": empresas,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page
        }
        
        return {
            "success": True,
            "data": resultado,
            "message": f"Se encontraron {total} empresa(s)"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )

@router.put("/{empresa_id}", response_model=EmpresaResponse)
async def actualizar_empresa(
    empresa_id: int,
    empresa_data: Dict[str, Any]
):
    """Actualizar datos de empresa existente (No implementado en Turso)"""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Actualización de empresas no implementada en la versión Turso"
    )

@router.delete("/{empresa_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_empresa(
    empresa_id: str
):
    """Eliminar empresa desde Neon PostgreSQL"""
    try:
        from app.services.empresa_service_neon import empresa_service_neon
        
        resultado = empresa_service_neon.eliminar_empresa(empresa_id)
        
        if not resultado:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Empresa no encontrada: {empresa_id}"
            )
            
        return {"message": "Empresa eliminada correctamente"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error eliminando empresa {empresa_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor al eliminar empresa"
        )

@router.get("/{empresa_id}/representantes", response_model=Dict[str, Any])
async def obtener_representantes_empresa(
    empresa_id: int
):
    """Obtener solo los representantes de una empresa usando Turso"""
    try:
        # Buscar empresa por ID
        empresas = empresa_service.list_empresas(limit=1000)
        empresa = next((e for e in empresas if e.get('id') == empresa_id), None)
        
        if not empresa:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Empresa no encontrada"
            )
        
        # Por ahora, usar los datos del representante legal como único representante
        representantes = []
        if empresa.get('representante_legal') and empresa.get('dni_representante'):
            representantes.append({
                "id": 1,
                "nombre": empresa.get('representante_legal'),
                "cargo": "Representante Legal",
                "numero_documento": empresa.get('dni_representante'),
                "tipo_documento": "DNI",
                "es_principal": True,
                "estado": "ACTIVO"
            })
        
        return {
            "success": True,
            "data": {
                "empresa_id": empresa.get('id'),
                "razon_social": empresa.get('razon_social'),
                "representantes": representantes,
                "total_representantes": len(representantes),
                "representante_principal": representantes[0] if representantes else None
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
async def validar_ruc_endpoint(
    ruc_data: Dict[str, str]
):
    """Validar si un RUC ya está registrado usando Turso"""
    try:
        ruc = ruc_data.get("ruc")
        if not ruc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="RUC es requerido"
            )
        
        if not validar_ruc(ruc):
            return {
                "success": False,
                "valid": False,
                "message": "RUC inválido. Debe tener 11 dígitos y comenzar con 10 o 20"
            }
        
        empresa_existente = empresa_service.get_empresa_by_ruc(ruc)
        
        return {
            "success": True,
            "valid": True,
            "ruc": ruc,
            "exists": empresa_existente is not None,
            "message": (
                "RUC ya registrado en el sistema" if empresa_existente 
                else "RUC disponible para registro"
            ),
            "empresa": convertir_empresa_dict_a_response(empresa_existente).dict() if empresa_existente else None
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
async def obtener_estadisticas_empresas():
    """Obtener estadísticas generales de empresas usando Turso"""
    try:
        # Obtener estadísticas directamente del servicio
        stats = empresa_service.get_stats()
        
        if "error" in stats:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error obteniendo estadísticas: {stats['error']}"
            )
        
        # Obtener algunas empresas para análisis adicional
        empresas = empresa_service.list_empresas(limit=1000)
        
        # Estadísticas por tipo
        tipos = {}
        for empresa in empresas:
            tipo = empresa.get('tipo_empresa', 'UNKNOWN')
            tipos[tipo] = tipos.get(tipo, 0) + 1
        
        # Estadísticas por categoría
        categorias = {}
        for empresa in empresas:
            cat = empresa.get('categoria_contratista')
            if cat:
                categorias[cat] = categorias.get(cat, 0) + 1
        
        return {
            "success": True,
            "data": {
                "total_empresas": stats.get('total_empresas', 0),
                "activas": stats.get('empresas_por_estado', {}).get('ACTIVO', 0),
                "inactivas": stats.get('empresas_por_estado', {}).get('INACTIVO', 0),
                "empresas_recientes_24h": stats.get('empresas_recientes_24h', 0),
                "por_tipo": tipos,
                "por_categoria": categorias,
                "por_estado": stats.get('empresas_por_estado', {}),
                "ultima_actualizacion": stats.get('timestamp', datetime.now().isoformat())
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo estadísticas: {str(e)}"
        )