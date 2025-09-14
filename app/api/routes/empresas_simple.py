"""
API endpoints simplificados para gestión de empresas (usando Neon directamente)
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, status
from datetime import datetime
import re
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/empresas", tags=["empresas"])

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

@router.get("/")
async def listar_empresas():
    """Listar empresas usando Neon PostgreSQL"""
    try:
        logger.info("🔍 Iniciando listar_empresas desde empresas_simple.py")
        empresa_service = get_empresa_service()
        logger.info("🔍 Servicio obtenido, llamando a listar_empresas...")
        empresas = empresa_service.listar_empresas(limit=100)
        logger.info(f"📋 Se obtuvieron {len(empresas)} empresas del servicio")

        return {
            "success": True,
            "data": {
                "empresas": empresas,
                "total": len(empresas)
            },
            "message": f"Se encontraron {len(empresas)} empresa(s)"
        }

    except Exception as e:
        logger.error(f"❌ Error listando empresas: {e}")
        import traceback
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )

@router.get("/debug/connection")
async def debug_connection():
    """Endpoint para depurar la conexión a la base de datos"""
    try:
        logger.info("🔍 [DEBUG] Iniciando prueba de conexión...")
        from app.services.empresa_service_neon import empresa_service_neon

        # Probar conexión básica
        with empresa_service_neon._get_connection() as conn:
            with conn.cursor() as cursor:
                # Probar consulta simple
                cursor.execute("SELECT 1 as test;")
                test_result = cursor.fetchone()
                logger.info(f"🔍 [DEBUG] Conexión básica: {test_result}")

                # Contar empresas
                cursor.execute("SELECT COUNT(*) as total FROM empresas;")
                count_result = cursor.fetchone()
                total = count_result['total']
                logger.info(f"🔍 [DEBUG] Total de empresas según consulta directa: {total}")

                # Obtener empresas si hay alguna
                if total > 0:
                    cursor.execute("SELECT id, ruc, razon_social FROM empresas ORDER BY created_at DESC LIMIT 2;")
                    empresas = cursor.fetchall()
                    logger.info(f"🔍 [DEBUG] Primeras empresas: {len(empresas)}")

                    return {
                        "success": True,
                        "data": {
                            "connection_test": "OK",
                            "total_empresas": total,
                            "empresas_encontradas": [
                                {
                                    "id": str(emp['id']),
                                    "ruc": emp['ruc'],
                                    "razon_social": emp['razon_social']
                                }
                                for emp in empresas
                            ],
                            "connection_string": empresa_service_neon.connection_string[:50] + "..."
                        },
                        "message": f"Conexión exitosa. Hay {total} empresas en la base de datos."
                    }
                else:
                    return {
                        "success": True,
                        "data": {
                            "connection_test": "OK",
                            "total_empresas": 0,
                            "empresas_encontradas": [],
                            "connection_string": empresa_service_neon.connection_string[:50] + "..."
                        },
                        "message": "Conexión exitosa pero no hay empresas en la base de datos."
                    }

    except Exception as e:
        logger.error(f"❌ [DEBUG] Error en prueba de conexión: {e}")
        import traceback
        logger.error(f"❌ [DEBUG] Traceback: {traceback.format_exc()}")
        return {
            "success": False,
            "error": str(e),
            "message": "Error en la conexión a la base de datos"
        }

@router.get("/{empresa_id}")
async def obtener_empresa(empresa_id: str):
    """Obtener empresa por ID o RUC"""
    try:
        empresa_service = get_empresa_service()
        
        # Intentar obtener por RUC primero
        if validar_ruc(empresa_id):
            empresa = empresa_service.obtener_empresa_por_ruc(empresa_id)
        else:
            # Buscar por ID en todas las empresas
            empresas = empresa_service.listar_empresas(limit=1000)
            empresa = next((e for e in empresas if e.get('id') == empresa_id), None)
        
        if not empresa:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Empresa no encontrada"
            )
        
        return {
            "success": True,
            "data": empresa,
            "message": "Empresa encontrada"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error obteniendo empresa {empresa_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )

@router.post("/")
async def crear_empresa(empresa_data: Dict[str, Any]):
    """Crear nueva empresa usando Neon"""
    try:
        # Validar RUC
        ruc = empresa_data.get('ruc')
        if not validar_ruc(ruc):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="RUC inválido. Debe tener 11 dígitos y comenzar con 10 o 20"
            )
        
        # Verificar si ya existe
        empresa_service = get_empresa_service()
        empresa_existente = empresa_service.obtener_empresa_por_ruc(ruc)
        if empresa_existente:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe una empresa con este RUC"
            )
        
        # Crear empresa
        empresa_id = empresa_service.guardar_empresa(empresa_data)
        
        if not empresa_id or empresa_id == "neon-success":
            # Verificar si la empresa fue creada a pesar de no recibir ID
            empresa_creada = empresa_service.obtener_empresa_por_ruc(ruc)
            if empresa_creada:
                return {
                    "success": True,
                    "data": empresa_creada,
                    "message": "Empresa creada correctamente"
                }
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Error creando empresa en la base de datos"
                )
        
        # Obtener empresa creada
        empresa_creada = empresa_service.obtener_empresa_por_ruc(ruc)
        
        return {
            "success": True,
            "data": empresa_creada,
            "message": "Empresa creada correctamente"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error creando empresa: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )

@router.delete("/{empresa_id}")
async def eliminar_empresa(empresa_id: str):
    """Eliminar empresa usando Neon"""
    try:
        logger.info(f"🗑️ [ROUTER] Recibida petición DELETE para empresa: {empresa_id}")
        
        empresa_service = get_empresa_service()
        resultado = empresa_service.eliminar_empresa(empresa_id)
        
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor al eliminar empresa"
        )

@router.get("/stats/summary")
async def obtener_estadisticas_empresas():
    """Obtener estadísticas generales de empresas"""
    try:
        empresa_service = get_empresa_service()
        stats = empresa_service.get_stats()
        
        if "error" in stats:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error obteniendo estadísticas: {stats['error']}"
            )
        
        return {
            "success": True,
            "data": stats,
            "message": "Estadísticas obtenidas correctamente"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error obteniendo estadísticas: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )