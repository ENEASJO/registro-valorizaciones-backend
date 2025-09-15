"""
API endpoints para gestión de empresas (usando Neon)
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, status
from datetime import datetime
import re
import logging

logger = logging.getLogger(__name__)

# Lazy import para evitar problemas de importación circular
from app.models.empresa import (
    EmpresaCreateSchema,
    EmpresaResponse,
    EmpresaListResponse,
    RepresentanteResponse
)

router = APIRouter(prefix="/empresas", tags=["empresas"])

# Servicio Neon se importará bajo demanda (lazy loading)
def get_empresa_service():
    """Obtener instancia del servicio de Neon de forma lazy"""
    from app.services.empresa_service_neon import empresa_service_neon
    return empresa_service_neon

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
    """Convertir diccionario de empresa de Neon a EmpresaResponse"""

    # Obtener representantes del diccionario o inicializar vacío
    representantes = empresa_dict.get('representantes', [])
    representantes_response = []

    for rep in representantes:
        representantes_response.append(RepresentanteResponse(
            id=rep.get('id', '0'),
            nombre=rep.get('nombre', ''),
            cargo=rep.get('cargo', ''),
            numero_documento=rep.get('numero_documento', ''),
            tipo_documento=rep.get('tipo_documento', 'DNI'),
            fuente=rep.get('fuente'),
            participacion=rep.get('participacion'),
            fecha_desde=rep.get('fecha_desde') if isinstance(rep.get('fecha_desde'), datetime) else (datetime.fromisoformat(rep.get('fecha_desde')) if rep.get('fecha_desde') else None),
            es_principal=rep.get('es_principal', False),
            estado=rep.get('estado', 'ACTIVO'),
            created_at=rep.get('created_at') if isinstance(rep.get('created_at'), datetime) else (datetime.fromisoformat(rep.get('created_at')) if rep.get('created_at') else datetime.now())
        ))

    return EmpresaResponse(
        id=str(empresa_dict.get('id', '0')),
        codigo=empresa_dict.get('codigo', ''),
        ruc=empresa_dict.get('ruc', ''),
        razon_social=empresa_dict.get('razon_social', ''),
        nombre_comercial=empresa_dict.get('nombre_comercial'),
        email=empresa_dict.get('email'),
        telefono=empresa_dict.get('telefono'),
        celular=empresa_dict.get('telefono'),  # Map telefono to celular for frontend compatibility
        direccion=empresa_dict.get('direccion'),
        representante_legal=empresa_dict.get('representante_legal'),
        dni_representante=empresa_dict.get('dni_representante'),
        estado=empresa_dict.get('estado', 'ACTIVO'),
        tipo_empresa=empresa_dict.get('tipo_empresa', 'SAC'),
        categoria_contratista=empresa_dict.get('categoria_contratista'),
        especialidades=empresa_dict.get('especialidades', []),
        representantes=representantes_response,
        total_representantes=len(representantes_response),
        activo=bool(empresa_dict.get('activo', True)),
        created_at=empresa_dict.get('created_at') if isinstance(empresa_dict.get('created_at'), datetime) else (datetime.fromisoformat(empresa_dict.get('created_at')) if empresa_dict.get('created_at') else datetime.now()),
        updated_at=empresa_dict.get('updated_at') if isinstance(empresa_dict.get('updated_at'), datetime) else (datetime.fromisoformat(empresa_dict.get('updated_at')) if empresa_dict.get('updated_at') else datetime.now())
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
        
        # Verificar si ya existe (usando servicio Neon)
        empresa_service = get_empresa_service()
        empresa_existente = empresa_service.obtener_empresa_por_ruc(empresa_data.ruc)
        if empresa_existente:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe una empresa con RUC {empresa_data.ruc}. Por favor, busque la empresa existente o actualícela si es necesario."
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
        
        # CAMBIO: Crear empresa en Neon PostgreSQL
        
        # Preparar datos para Neon
        empresa_data_neon = {
            'ruc': empresa_data.ruc,
            'razon_social': empresa_data.razon_social,
            'email': empresa_data.email or '',
            'telefono': empresa_data.celular or '',
            'direccion': empresa_data.direccion or '',
            'representante_legal': representante_principal.nombre,
            'dni_representante': representante_principal.numero_documento,
            'estado': 'ACTIVO',
            'tipo_empresa': 'SAC',
            'categoria_contratista': empresa_data.categoria_contratista
        }
        
        empresa_service = get_empresa_service()
        empresa_id = empresa_service.guardar_empresa(empresa_data_neon)

        if not empresa_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error creando empresa en la base de datos"
            )

        # Guardar TODOS los representantes en la tabla representantes_legales
        representantes_guardados = []
        for i, representante in enumerate(empresa_data.representantes):
            # Preparar datos del representante para guardar_representante
            representante_data = {
                'nombre': representante.nombre,
                'cargo': representante.cargo,
                'tipo_documento': representante.tipo_documento,
                'numero_documento': representante.numero_documento,
                'participacion': representante.participacion if hasattr(representante, 'participacion') else None,
                'fuente': representante.fuente or 'MANUAL',
                'es_principal': i == empresa_data.representante_principal_id,
                'activo': representante.activo if hasattr(representante, 'activo') else True
            }

            # Guardar el representante
            representante_id = empresa_service.guardar_representante(empresa_id, representante_data)

            if representante_id:
                representantes_guardados.append({
                    'id': representante_id,
                    'nombre': representante.nombre,
                    'cargo': representante.cargo,
                    'numero_documento': representante.numero_documento,
                    'tipo_documento': representante.tipo_documento,
                    'fuente': representante.fuente,
                    'es_principal': i == empresa_data.representante_principal_id,
                    'activo': representante.activo if hasattr(representante, 'activo') else True,
                    'created_at': datetime.now()
                })
                logger.info(f"✅ Representante guardado: {representante.nombre} para empresa {empresa_id}")
            else:
                logger.error(f"❌ Error guardando representante: {representante.nombre}")

        # Obtener empresa creada con todos sus representantes para retornar
        empresa_creada = empresa_service.obtener_empresa_por_ruc(empresa_data.ruc)
        if not empresa_creada:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error obteniendo empresa creada"
            )

        # Asegurar que la respuesta incluya todos los representantes guardados
        if representantes_guardados:
            empresa_creada['representantes'] = representantes_guardados
            empresa_creada['total_representantes'] = len(representantes_guardados)

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
        # Buscar empresa por ID (usando servicio Neon)
        empresas = get_empresa_service().listar_empresas(limit=1000)
        empresa = next((e for e in empresas if e.get('id') == str(empresa_id)), None)
        
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
        
        empresa = get_empresa_service().obtener_empresa_por_ruc(ruc)
        
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
    estado: Optional[str] = Query(None, description="Filtrar por estado"),
    categoria: Optional[str] = Query(None, description="Filtrar por categoría: EJECUTORA o SUPERVISORA")
):
    """Listar empresas con filtros y paginación usando Neon PostgreSQL"""
    try:
        # Calcular offset
        offset = (page - 1) * per_page
        
        # CAMBIO: Usar Neon en lugar de Turso
        
        empresas_raw = get_empresa_service().listar_empresas(limit=per_page * 5)
        
        # Filtrar por búsqueda si se especifica
        if search:
            search_lower = search.lower()
            empresas_raw = [
                emp for emp in empresas_raw 
                if (search_lower in emp.get('razon_social', '').lower() or 
                    search_lower in emp.get('ruc', ''))
            ]
        
        # Filtrar por estado si se especifica
        if estado:
            empresas_raw = [e for e in empresas_raw if e.get('estado', '').upper() == estado.upper()]
        
        # Filtrar por categoría si se especifica
        if categoria:
            categoria_upper = categoria.upper()
            if categoria_upper in ['EJECUTORA', 'SUPERVISORA']:
                empresas_raw = [e for e in empresas_raw if e.get('categoria_contratista', '').upper() == categoria_upper]
        
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

@router.get("/debug/detailed-error", response_model=Dict[str, Any])
async def debug_detailed_error():
    """Endpoint para depurar error detallado"""
    try:
        from app.services.empresa_service_neon import empresa_service_neon
        import traceback

        # Probar obtener empresas y convertirlas igual que el endpoint principal
        empresas_raw = empresa_service_neon.listar_empresas(limit=1)

        # Probar la conversión que causa el error
        empresas_response = []
        for empresa in empresas_raw:
            try:
                empresa_response = convertir_empresa_dict_a_response(empresa)
                empresas_response.append(empresa_response)
            except Exception as conv_error:
                return {
                    "success": False,
                    "error": f"Error en conversión: {str(conv_error)}",
                    "error_type": type(conv_error).__name__,
                    "empresa_data": empresa,
                    "traceback": traceback.format_exc()
                }

        return {
            "success": True,
            "message": "No error occurred",
            "empresas_count": len(empresas_response),
            "traceback": None
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "traceback": traceback.format_exc(),
            "full_error": f"Error interno del servidor: {str(e)}"
        }

@router.get("/debug/test-connection", response_model=Dict[str, Any])
async def debug_test_connection():
    """Endpoint temporal para probar la conexión y consulta directa"""
    try:
        from app.services.empresa_service_neon import empresa_service_neon

        # Probar conexión
        with empresa_service_neon._get_connection() as conn:
            with conn.cursor() as cursor:
                # Contar empresas
                cursor.execute("SELECT COUNT(*) as total FROM empresas;")
                count_result = cursor.fetchone()
                total = count_result['total']

                # Obtener empresas
                cursor.execute("SELECT id, ruc, razon_social FROM empresas ORDER BY created_at DESC LIMIT 5;")
                empresas = cursor.fetchall()

                return {
                    "success": True,
                    "data": {
                        "total_empresas": total,
                        "empresas": [
                            {
                                "id": str(emp['id']),
                                "ruc": emp['ruc'],
                                "razon_social": emp['razon_social']
                            }
                            for emp in empresas
                        ],
                        "connection_string": empresa_service_neon.connection_string[:50] + "..."
                    },
                    "message": f"Conexión exitosa. Encontradas {total} empresas."
                }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Error en la conexión"
        }

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

@router.delete("/{empresa_id}")
async def eliminar_empresa(
    empresa_id: str
):
    """Eliminar empresa usando el servicio Neon PostgreSQL (consistente con GET/LIST)"""
    try:
        logger.info(f"🗑️ [ROUTER] Recibida petición DELETE para empresa: {empresa_id}")
        
        # FIJO: Usar el mismo servicio que usa GET/LIST (Neon PostgreSQL)
        
        resultado = get_empresa_service().eliminar_empresa(empresa_id)
        
        if not resultado:
            logger.warning(f"❌ [ROUTER] Empresa no encontrada: {empresa_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Empresa no encontrada: {empresa_id}"
            )
        
        logger.info(f"✅ [ROUTER] Empresa eliminada exitosamente: {empresa_id}")
        return {
            "success": True,
            "message": "Empresa eliminada correctamente",
            "empresa_id": empresa_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [ROUTER] Error eliminando empresa {empresa_id}: {e}")
        import traceback
        logger.error(f"❌ [ROUTER] Traceback: {traceback.format_exc()}")
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
        # Buscar empresa por ID (usando servicio Neon)
        empresas = get_empresa_service().listar_empresas(limit=1000)
        empresa = next((e for e in empresas if e.get('id') == str(empresa_id)), None)
        
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
        
        empresa_existente = get_empresa_service().obtener_empresa_por_ruc(ruc)
        
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

# Endpoints para filtrado por categoría
@router.get("/ejecutoras", response_model=Dict[str, Any])
async def listar_empresas_ejecutoras(
    page: int = Query(1, ge=1, description="Número de página"),
    per_page: int = Query(20, ge=1, le=100, description="Elementos por página"),
    search: Optional[str] = Query(None, description="Buscar por razón social, RUC o representante")
):
    """Listar empresas ejecutoras únicamente"""
    try:
        # Calcular offset
        offset = (page - 1) * per_page
        
        # Usar Neon PostgreSQL
        
        empresas_raw = get_empresa_service().listar_empresas(limit=per_page * 5)
        
        # Filtrar por categoría EJECUTORA
        empresas_raw = [emp for emp in empresas_raw if emp.get('categoria_contratista') == 'EJECUTORA']
        
        # Filtrar por búsqueda si se especifica
        if search:
            search_lower = search.lower()
            empresas_raw = [
                emp for emp in empresas_raw 
                if (search_lower in emp.get('razon_social', '').lower() or 
                    search_lower in emp.get('ruc', ''))
            ]
        
        # Aplicar paginación manual
        total = len(empresas_raw)
        empresas_raw = empresas_raw[offset:offset + per_page]
        
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
            "message": f"Se encontraron {total} empresa(s) ejecutoras"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )

@router.get("/supervisoras", response_model=Dict[str, Any])
async def listar_empresas_supervisoras(
    page: int = Query(1, ge=1, description="Número de página"),
    per_page: int = Query(20, ge=1, le=100, description="Elementos por página"),
    search: Optional[str] = Query(None, description="Buscar por razón social, RUC o representante")
):
    """Listar empresas supervisoras únicamente"""
    try:
        # Calcular offset
        offset = (page - 1) * per_page
        
        # Usar Neon PostgreSQL
        
        empresas_raw = get_empresa_service().listar_empresas(limit=per_page * 5)
        
        # Filtrar por categoría SUPERVISORA
        empresas_raw = [emp for emp in empresas_raw if emp.get('categoria_contratista') == 'SUPERVISORA']
        
        # Filtrar por búsqueda si se especifica
        if search:
            search_lower = search.lower()
            empresas_raw = [
                emp for emp in empresas_raw 
                if (search_lower in emp.get('razon_social', '').lower() or 
                    search_lower in emp.get('ruc', ''))
            ]
        
        # Aplicar paginación manual
        total = len(empresas_raw)
        empresas_raw = empresas_raw[offset:offset + per_page]
        
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
            "message": f"Se encontraron {total} empresa(s) supervisoras"
        }
        
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
        # Obtener estadísticas directamente del servicio Neon
        stats = get_empresa_service().get_stats()
        
        if "error" in stats:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error obteniendo estadísticas: {stats['error']}"
            )
        
        # Obtener algunas empresas para análisis adicional (usando servicio Neon)
        empresas = get_empresa_service().listar_empresas(limit=1000)
        
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