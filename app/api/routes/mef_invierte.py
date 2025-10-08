"""
Endpoints para consulta MEF Invierte (Banco de Inversiones)
Sistema del Ministerio de Economía y Finanzas

ARQUITECTURA:
- Endpoint PROTEGIDO (solo IP autorizada): Hace scraping real y actualiza BD
- Endpoint PÚBLICO (todos): Consulta datos cacheados en BD (rápido)
"""
from fastapi import APIRouter, HTTPException, Request
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
import logging
import os
from databases import Database

from app.services.mef_invierte_service import consultar_cui_mef, consultar_cui_mef_con_nombre

logger = logging.getLogger(__name__)

# IPs autorizadas para hacer scraping real (solo administrador)
ADMIN_IPS = [ip.strip() for ip in os.getenv("ADMIN_IPS", "127.0.0.1").split(",")]
logger.info(f"IPs autorizadas para scraping MEF: {ADMIN_IPS}")

# Conexión a base de datos
DATABASE_URL = os.getenv("NEON_DATABASE_URL")
database = Database(DATABASE_URL) if DATABASE_URL else None


class MEFInvierteInput(BaseModel):
    """Input para consulta MEF Invierte"""
    cui: str = Field(..., description="Código Único de Inversiones (CUI)", example="2595080")


class MEFInvierteSearchInput(BaseModel):
    """Input para búsqueda en MEF Invierte"""
    cui: Optional[str] = Field(None, description="Código Único de Inversiones (opcional)", example="2595080")
    nombre: Optional[str] = Field(None, description="Nombre o descripción de la inversión (opcional)", example="CONSTRUCCION")


router = APIRouter(
    prefix="/api/v1/mef-invierte",
    tags=["MEF Invierte"],
    responses={
        400: {"description": "Error de validación"},
        403: {"description": "No autorizado - Solo administradores pueden hacer scraping"},
        404: {"description": "Inversión no encontrada en MEF Invierte"},
        408: {"description": "Timeout en la consulta"},
        500: {"description": "Error interno del servidor"},
    }
)


@router.post(
    "/actualizar",
    summary="[ADMIN] Actualizar datos MEF haciendo scraping real",
    description="⚠️ ENDPOINT PROTEGIDO - Solo IP autorizada. Hace scraping real y actualiza BD.",
    response_description="Datos actualizados desde MEF Invierte"
)
async def actualizar_mef_scraping(mef_input: MEFInvierteInput, request: Request) -> Dict[str, Any]:
    """
    🔒 ENDPOINT PROTEGIDO - Solo administrador con IP autorizada

    Hace scraping REAL a MEF Invierte y actualiza/crea datos en BD.
    Usado cuando:
    - Creas una obra nueva (primera vez)
    - Actualizas una obra existente (detectar ampliaciones, modificaciones)

    ⚠️ IMPORTANTE: Este endpoint solo funciona desde IPs autorizadas (tu PC).
    Otros usuarios recibirán error 403.

    - **cui**: Código Único de Inversiones (ejemplo: "2595080")

    Retorna:
    - Datos completos scraped desde MEF
    - Confirmación de guardado en BD
    - Timestamp de actualización
    """
    # Obtener IP real del cliente (considerando proxies/load balancers)
    client_ip = request.headers.get("X-Forwarded-For", request.headers.get("X-Real-IP", request.client.host))
    if "," in client_ip:
        client_ip = client_ip.split(",")[0].strip()  # Primera IP en la cadena

    # Verificar IP autorizada
    if client_ip not in ADMIN_IPS:
        logger.warning(f"Intento de scraping MEF desde IP no autorizada: {client_ip}")
        raise HTTPException(
            status_code=403,
            detail={
                "error": True,
                "message": "Scraping MEF solo disponible para administradores",
                "info": "Este endpoint hace scraping real y solo funciona desde IPs autorizadas",
                "client_ip": client_ip,
                "contact": "Contacta al administrador del sistema"
            }
        )

    try:
        logger.info(f"[ADMIN SCRAPING] Iniciando scraping MEF desde IP autorizada {client_ip} para CUI: {mef_input.cui}")

        # Hacer scraping REAL (funciona porque es tu IP residencial)
        resultado = await consultar_cui_mef(mef_input.cui)

        if not resultado.get("success"):
            logger.warning(f"[ADMIN SCRAPING] No se encontró inversión para CUI {mef_input.cui}")
            raise HTTPException(
                status_code=404,
                detail={
                    "error": True,
                    "message": resultado.get("error", "No se encontró información en MEF"),
                    "cui": mef_input.cui,
                    "fuente": "MEF Invierte"
                }
            )

        # Guardar/actualizar en base de datos
        if database:
            try:
                # Verificar si ya existe una obra con este CUI
                obra_existente = await database.fetch_one(
                    "SELECT id FROM obras WHERE cui = :cui",
                    {"cui": mef_input.cui}
                )

                if obra_existente:
                    # Actualizar obra existente
                    await database.execute(
                        """
                        UPDATE obras
                        SET
                            datos_mef = :datos_mef,
                            fecha_actualizacion_mef = NOW()
                        WHERE cui = :cui
                        """,
                        {
                            "cui": mef_input.cui,
                            "datos_mef": str(resultado)  # Convertir dict a JSON string
                        }
                    )
                    logger.info(f"[ADMIN SCRAPING] Datos MEF actualizados en BD para CUI {mef_input.cui}")
                    db_action = "updated"
                else:
                    logger.info(f"[ADMIN SCRAPING] CUI {mef_input.cui} no tiene obra asociada aún. Solo retornando datos.")
                    db_action = "not_saved"

            except Exception as db_error:
                logger.error(f"[ADMIN SCRAPING] Error guardando en BD: {str(db_error)}")
                # No fallar si hay error de BD, igual retornar los datos
                db_action = "error"
        else:
            logger.warning("[ADMIN SCRAPING] Base de datos no configurada")
            db_action = "no_database"

        logger.info(f"[ADMIN SCRAPING] Scraping MEF exitoso para CUI {mef_input.cui}")

        return {
            **resultado,
            "admin_info": {
                "scraped_from_ip": client_ip,
                "database_action": db_action,
                "message": "Datos scraped exitosamente desde MEF Invierte"
            }
        }

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"[ADMIN SCRAPING] Error inesperado: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": True,
                "message": "Error al hacer scraping MEF",
                "details": str(e),
                "cui": mef_input.cui
            }
        )


@router.get(
    "/consultar/{cui}",
    summary="[PÚBLICO] Consultar datos MEF desde caché",
    description="Consulta datos MEF ya scraped y guardados en BD (RÁPIDO, para todos los usuarios)",
    response_description="Datos MEF desde caché"
)
async def consultar_mef_cache(cui: str) -> Dict[str, Any]:
    """
    📖 ENDPOINT PÚBLICO - Para todos los usuarios

    Consulta datos MEF que fueron previamente scraped y guardados en BD.
    NO hace scraping, solo lee de la base de datos (súper rápido).

    Usado cuando:
    - Usuarios consultan obras existentes
    - Frontend muestra datos de obras

    - **cui**: Código Único de Inversiones en la URL (ejemplo: "2595080")

    Retorna:
    - Datos MEF guardados en BD
    - Fecha de última actualización
    - Si no existe, mensaje para solicitar al admin
    """
    try:
        if not database:
            raise HTTPException(
                status_code=500,
                detail={
                    "error": True,
                    "message": "Base de datos no configurada"
                }
            )

        logger.info(f"[CONSULTA CACHE] Buscando datos MEF para CUI: {cui}")

        # Buscar en base de datos
        obra = await database.fetch_one(
            """
            SELECT
                datos_mef,
                fecha_actualizacion_mef,
                nombre,
                codigo
            FROM obras
            WHERE cui = :cui
            """,
            {"cui": cui}
        )

        if not obra or not obra['datos_mef']:
            logger.warning(f"[CONSULTA CACHE] No se encontraron datos MEF para CUI {cui}")
            raise HTTPException(
                status_code=404,
                detail={
                    "error": True,
                    "found": False,
                    "message": "CUI no encontrado en la base de datos",
                    "cui": cui,
                    "info": "Este CUI no ha sido scraped aún. Solicita al administrador actualizar los datos.",
                    "hint": "El administrador debe usar el endpoint /actualizar para obtener los datos"
                }
            )

        logger.info(f"[CONSULTA CACHE] Datos MEF encontrados para CUI {cui}")

        return {
            "success": True,
            "found": True,
            "cui": cui,
            "data": obra['datos_mef'],
            "obra_info": {
                "nombre": obra['nombre'],
                "codigo": obra['codigo']
            },
            "cache_info": {
                "ultima_actualizacion": str(obra['fecha_actualizacion_mef']) if obra['fecha_actualizacion_mef'] else None,
                "fuente": "Base de datos (caché)",
                "message": "Datos leídos desde caché (sin scraping)"
            }
        }

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"[CONSULTA CACHE] Error inesperado: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": True,
                "message": "Error al consultar datos MEF",
                "details": str(e),
                "cui": cui
            }
        )


@router.post(
    "/consultar",
    summary="[LEGACY] Consultar inversión MEF (POST)",
    description="⚠️ DEPRECATED - Usa /actualizar (admin) o /consultar/{cui} (público) en su lugar",
    response_description="Información completa de la inversión"
)
async def consultar_inversion_mef(mef_input: MEFInvierteInput, request: Request) -> Dict[str, Any]:
    """
    ⚠️ ENDPOINT LEGACY - Mantenido por compatibilidad

    Redirige a:
    - /actualizar si es IP de admin (hace scraping)
    - /consultar/{cui} si es usuario normal (lee caché)
    """
    # Obtener IP real del cliente (considerando proxies/load balancers)
    client_ip = request.headers.get("X-Forwarded-For", request.headers.get("X-Real-IP", request.client.host))
    if "," in client_ip:
        client_ip = client_ip.split(",")[0].strip()

    if client_ip in ADMIN_IPS:
        logger.info(f"[LEGACY] Redirigiendo a /actualizar para IP admin: {client_ip}")
        return await actualizar_mef_scraping(mef_input, request)
    else:
        logger.info(f"[LEGACY] Redirigiendo a /consultar para IP pública: {client_ip}")
        return await consultar_mef_cache(mef_input.cui)


@router.post(
    "/buscar",
    summary="Buscar inversiones en MEF Invierte",
    description="Busca inversiones por CUI y/o nombre en el Banco de Inversiones de MEF",
    response_description="Lista de inversiones encontradas"
)
async def buscar_inversiones_mef(search_input: MEFInvierteSearchInput) -> Dict[str, Any]:
    """
    Busca inversiones por CUI y/o nombre en MEF Invierte

    - **cui**: Código Único de Inversiones (opcional)
    - **nombre**: Nombre o descripción de la inversión (opcional)

    Al menos uno de los dos parámetros debe proporcionarse.

    Retorna:
    - Lista de inversiones que coinciden con los criterios
    - Cada inversión incluye toda la información disponible
    """
    try:
        if not search_input.cui and not search_input.nombre:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": True,
                    "message": "Debe proporcionar al menos un CUI o nombre para buscar",
                    "fuente": "MEF Invierte"
                }
            )

        logger.info(f"Iniciando búsqueda MEF Invierte - CUI: {search_input.cui}, Nombre: {search_input.nombre}")

        resultado = await consultar_cui_mef_con_nombre(
            cui=search_input.cui,
            nombre=search_input.nombre
        )

        if resultado.get("success"):
            logger.info(f"Búsqueda MEF Invierte exitosa: {resultado.get('count', 0)} resultados")
            return resultado
        else:
            logger.warning("No se encontraron resultados en búsqueda MEF Invierte")
            raise HTTPException(
                status_code=404,
                detail={
                    "error": True,
                    "message": resultado.get("error", "No se encontraron resultados"),
                    "cui": search_input.cui,
                    "nombre": search_input.nombre,
                    "fuente": "MEF Invierte"
                }
            )

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Error inesperado en búsqueda MEF Invierte: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": True,
                "message": "Error interno del servidor",
                "details": str(e),
                "fuente": "MEF Invierte"
            }
        )


@router.get(
    "/health",
    summary="Verificar estado del servicio MEF Invierte",
    description="Endpoint para verificar que el servicio MEF Invierte está funcionando correctamente",
    tags=["Health"]
)
async def health_check_mef(request: Request) -> Dict[str, Any]:
    """Verificar estado del servicio MEF Invierte"""
    db_status = "connected" if database else "not_configured"

    # Debug: obtener IP del cliente
    client_ip = request.headers.get("X-Forwarded-For", request.headers.get("X-Real-IP", request.client.host))
    if "," in client_ip:
        client_ip = client_ip.split(",")[0].strip()

    return {
        "status": "healthy",
        "message": "Servicio de consulta MEF Invierte funcionando correctamente",
        "service": "mef-invierte-api",
        "version": "2.0.0",
        "architecture": "cache-first with protected scraping",
        "database": db_status,
        "debug": {
            "your_ip": client_ip,
            "admin_ips_loaded": ADMIN_IPS,
            "is_authorized": client_ip in ADMIN_IPS
        },
        "features": [
            "Consulta rápida desde caché (todos los usuarios)",
            "Scraping protegido por IP (solo administrador)",
            "Detección de ampliaciones y modificaciones",
            "Actualización bajo demanda"
        ]
    }


@router.get(
    "/info",
    summary="Información del API MEF Invierte",
    description="Información detallada sobre el API de consulta MEF Invierte",
    tags=["Info"]
)
async def api_info_mef() -> Dict[str, Any]:
    """Información del API MEF Invierte"""
    return {
        "name": "API Consultor MEF Invierte v2.0",
        "version": "2.0.0",
        "description": "API para consultar información de inversiones públicas con arquitectura de caché",
        "architecture": {
            "type": "cache-first",
            "description": "Consultas rápidas desde BD con scraping protegido para actualizaciones",
            "admin_only_scraping": True,
            "public_cache_access": True
        },
        "endpoints": {
            "POST /api/v1/mef-invierte/actualizar": "🔒 [ADMIN] Hacer scraping real y actualizar BD",
            "GET /api/v1/mef-invierte/consultar/{cui}": "📖 [PÚBLICO] Consultar datos desde caché",
            "POST /api/v1/mef-invierte/consultar": "⚠️ [LEGACY] Redirige según IP",
            "POST /api/v1/mef-invierte/buscar": "Buscar inversiones por CUI y/o nombre",
            "GET /api/v1/mef-invierte/health": "Verificar estado del servicio",
            "GET /api/v1/mef-invierte/info": "Información del API"
        },
        "workflow": {
            "admin": [
                "1. Crear/editar obra",
                "2. Llamar POST /actualizar con CUI",
                "3. Sistema hace scraping real (funciona solo desde IP autorizada)",
                "4. Datos se guardan/actualizan en BD",
                "5. Todos los usuarios pueden consultar estos datos"
            ],
            "users": [
                "1. Consultar obra existente",
                "2. Llamar GET /consultar/{cui}",
                "3. Sistema retorna datos desde caché (súper rápido)",
                "4. Si no existe, solicitar al admin actualizar"
            ]
        },
        "data_sources": {
            "primary": "MEF Invierte - Banco de Inversiones",
            "organization": "Ministerio de Economía y Finanzas",
            "url": "https://ofi5.mef.gob.pe/invierte/consultapublica/consultainversiones"
        },
        "notes": {
            "ip_restriction": "Scraping real solo funciona desde IPs autorizadas (datacenter IPs bloqueadas por MEF)",
            "performance": "Consultas desde caché <100ms, scraping real ~30-60 segundos",
            "updates": "Administrador decide cuándo actualizar cada CUI (detecta ampliaciones, modificaciones)"
        }
    }


# Startup: conectar base de datos
@router.on_event("startup")
async def startup():
    if database:
        await database.connect()
        logger.info("[MEF INVIERTE] Conectado a base de datos")


# Shutdown: desconectar base de datos
@router.on_event("shutdown")
async def shutdown():
    if database:
        await database.disconnect()
        logger.info("[MEF INVIERTE] Desconectado de base de datos")
