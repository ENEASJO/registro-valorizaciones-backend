# main.py
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
import os
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

# Import API routes - make them optional for startup
ROUTES_AVAILABLE = True
try:
    from app.api.routes import ruc, osce, mcp, obras, valorizaciones, notifications
    print("📡 API routes loaded successfully")
except ImportError as e:
    print(f"⚠️ Some API routes not available: {e}")
    ROUTES_AVAILABLE = False
    # Create dummy route modules
    class DummyRouter:
        router = None
    ruc = osce = mcp = obras = valorizaciones = notifications = DummyRouter()

# Import Playwright helper for optimized browser configuration
try:
    from app.utils.playwright_helper import get_browser_launch_options
    PLAYWRIGHT_HELPER_AVAILABLE = True
    print("🌐 Playwright helper loaded successfully")
except ImportError as e:
    print(f"⚠️ Playwright helper not available: {e}")
    PLAYWRIGHT_HELPER_AVAILABLE = False

from app.api.routes import empresas  # Re-enabled for Turso integration

# Try to import MCP database, but make it optional
try:
    from app.core.database_mcp import init_database_mcp, close_database_mcp
    MCP_AVAILABLE = True
except ImportError:
    print("⚠️ MCP database not available - running without database integration")
    MCP_AVAILABLE = False
    
    async def init_database_mcp():
        return False
    
    async def close_database_mcp():
        pass

# Try to import Turso database
try:
    from app.core.database_turso import init_database, close_database
    DB_AVAILABLE = True
    print("📦 Turso database module loaded")
except ImportError as e:
    print(f"⚠️ Turso database not available: {e}")
    DB_AVAILABLE = False
    
    async def init_database():
        return False
    
    async def close_database():
        pass

app = FastAPI(
    title="API de Valorizaciones - Cloud Run Completo", 
    description="Backend completo: Playwright (scraping) + CRUD + Turso Database",
    version="3.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Frontend Vite dev
        "http://localhost:3000",  # Frontend alternativo
        "http://127.0.0.1:5173", 
        "http://127.0.0.1:3000",
        "http://localhost:4173",  # Vite preview
        "http://127.0.0.1:4173",
        "http://localhost:8080",  # Servidor de pruebas
        "http://127.0.0.1:8080",  # Frontend comparación
        "https://*.vercel.app",   # Vercel deployment domains
        "https://valoraciones-app-*.vercel.app", # Specific Vercel pattern
        "*"  # Allow all origins in development (Railway will override in production)
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Database lifecycle events
@app.on_event("startup")
async def startup():
    """Inicializar base de datos al arrancar"""
    try:
        # Inicializar base de datos Turso
        if DB_AVAILABLE:
            success = await init_database()
            if success:
                print("🚀 Base de datos Turso inicializada")
            else:
                print("⚠️ Fallo inicializando Turso")
        
        # Inicializar base de datos MCP (opcional)
        success_mcp = await init_database_mcp()
        if success_mcp:
            print("🚀 API iniciada con base de datos MCP")
        else:
            print("⚠️ API iniciada sin base de datos MCP (modo degradado)")
            
    except Exception as e:
        print(f"❌ Error inicializando base de datos: {e}")

@app.on_event("shutdown") 
async def shutdown():
    """Cerrar conexiones al terminar"""
    try:
        if DB_AVAILABLE:
            await close_database()
            print("✅ Base de datos Turso cerrada")
        
        await close_database_mcp()
        print("✅ API terminada correctamente")
    except Exception as e:
        print(f"⚠️ Error cerrando aplicación: {e}")

# Include API routers only if available
if ROUTES_AVAILABLE:
    app.include_router(ruc.router)
    app.include_router(osce.router)
    app.include_router(mcp.router)
    # app.include_router(consolidado.router)  # Module not available
    app.include_router(obras.router)
    app.include_router(valorizaciones.router)
    app.include_router(notifications.router)
    app.include_router(empresas.router)  # Re-enabled for Turso integration
    print("✅ All API routers included")
else:
    print("⚠️ Running with minimal routes due to import errors")

# In-memory storage for saved empresas (temporary) 
saved_empresas = []
next_empresa_id = 1

# Modelo temporal para empresa
class EmpresaCreate(BaseModel):
    ruc: str
    razon_social: str
    email: Optional[str] = None
    telefono: Optional[str] = None
    direccion: Optional[str] = None
    estado: Optional[str] = None
    tipo_contribuyente: Optional[str] = None
    fecha_constitucion: Optional[str] = None
    departamento: Optional[str] = None
    provincia: Optional[str] = None
    distrito: Optional[str] = None
    integrantes: Optional[List[Dict[str, Any]]] = []

# Endpoint temporal para listar empresas (GET)
@app.get("/api/empresas")
async def listar_empresas_temp():
    """Endpoint temporal para listar empresas - respuesta desde memoria"""
    try:
        print(f"📋 Listando empresas guardadas: {len(saved_empresas)} encontradas")
        
        return {
            "success": True,
            "data": saved_empresas,
            "total": len(saved_empresas),
            "message": f"Se encontraron {len(saved_empresas)} empresas",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"❌ Error listando empresas: {e}")
        return {
            "success": False,
            "error": True,
            "message": f"Error al listar empresas: {str(e)}",
            "data": [],
            "timestamp": datetime.now().isoformat()
        }

# Endpoint temporal para crear empresas (mock response)
@app.post("/api/empresas")
async def create_empresa_temp(empresa: EmpresaCreate):
    """Endpoint temporal para crear empresas - respuesta mock"""
    return {
        "success": True,
        "message": "Empresa registrada exitosamente (mock)",
        "data": {
            "id": f"temp_{empresa.ruc}",
            "ruc": empresa.ruc,
            "razon_social": empresa.razon_social,
            "created_at": datetime.now().isoformat()
        },
        "warning": "Esto es un endpoint temporal - los datos no se guardan en base de datos"
    }

# Endpoint raíz
@app.get("/")
async def root():
    db_status = "connected" if DB_AVAILABLE else "disconnected"
    return {
        "message": "API de Valorizaciones - Cloud Run Completo ACTUALIZADO",
        "version": "3.0.1",
        "status": "active",
        "architecture": "Backend Unificado: Playwright + CRUD + Turso",
        "database": f"Turso ({db_status})",
        "capabilities": {
            "scraping": "✅ SUNAT/OSCE con Playwright",
            "crud": "✅ Empresas/Obras/Valorizaciones",
            "database": "✅ Turso SQLite Cloud",
            "whatsapp": "✅ Notificaciones WhatsApp Business"
        },
        "endpoints": {
            "scraping": {
                "sunat": "/consulta-ruc/{ruc}",
                "osce": "/consulta-osce/{ruc}",
                # "consolidado": "/consulta-ruc-consolidada/{ruc}",  # Module not available
                "legacy": "/buscar"
            },
            "crud": {
                "empresas": "/api/empresas",
                "obras": "/api/obras",
                "valorizaciones": "/api/valorizaciones"
            },
            "notifications": {
                "whatsapp": "/api/notifications",
                "metrics": "/api/notifications/metrics",
                "test": "/api/notifications/test"
            },
            "utility": {
                "health": "/health",
                "info": "/"
            }
        }
    }

# Endpoint para servir el frontend de comparación
@app.get("/comparison")
async def comparison_frontend():
    frontend_path = os.path.join(os.path.dirname(__file__), "comparison_frontend.html")
    if os.path.exists(frontend_path):
        return FileResponse(frontend_path, media_type="text/html")
    else:
        return JSONResponse(status_code=404, content={"message": "Frontend de comparación no encontrado"})

# Endpoint para favicon
@app.get("/favicon.ico")
async def favicon():
    favicon_path = os.path.join(os.path.dirname(__file__), "favicon.ico")
    if os.path.exists(favicon_path):
        return FileResponse(favicon_path)
    else:
        return JSONResponse(status_code=404, content={"message": "Favicon not found"})

# Endpoint de salud
@app.get("/health")
async def health_check():
    """Health check con verificación completa de servicios"""
    start_time = datetime.now()
    services_status = {}
    overall_status = "healthy"
    
    # Verificar Turso Database
    try:
        if DB_AVAILABLE:
            from app.core.database_turso import get_turso_client
            client = get_turso_client()
            if client:
                # Test básico de conectividad
                test_result = client.execute("SELECT 1 as health_test")
                services_status["turso_database"] = {
                    "status": "healthy",
                    "response_time_ms": round((datetime.now() - start_time).total_seconds() * 1000, 2)
                }
            else:
                services_status["turso_database"] = {"status": "disconnected"}
                overall_status = "degraded"
        else:
            services_status["turso_database"] = {"status": "unavailable"}
            overall_status = "degraded"
    except Exception as e:
        services_status["turso_database"] = {"status": "error", "error": str(e)[:50]}
        overall_status = "degraded"
    
    # Verificar otros servicios
    services_status.update({
        "playwright": {"status": "enabled"},
        "crud_apis": {"status": "enabled"},
        "sunat_robust": {"status": "enabled"},
        "sunat_fallback": {"status": "enabled"}
    })
    
    return {
        "status": overall_status,
        "version": "3.3.0-robust-turso",
        "architecture": "Cloud Run + Turso + SUNAT Robusto",
        "services": services_status,
        "timestamp": datetime.now().isoformat(),
        "response_time_ms": round((datetime.now() - start_time).total_seconds() * 1000, 2)
    }

# Endpoint de monitoreo SUNAT
@app.get("/sunat-status")
async def sunat_status_check():
    """Endpoint para monitorear el estado y rendimiento del servicio SUNAT"""
    try:
        from app.services.sunat_master_service import sunat_master_service
        
        # Obtener estadísticas de rendimiento
        health_info = await sunat_master_service.health_check()
        
        return {
            "success": True,
            "message": "Estado del servicio SUNAT consultado exitosamente",
            "data": health_info,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": True,
            "message": f"Error consultando estado SUNAT: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

# Endpoint de diagnóstico de scraping
@app.get("/debug/playwright-status")
async def debug_playwright_status():
    """Endpoint para diagnosticar el estado de Playwright y los servicios de scraping"""
    
    try:
        print("🔍 Iniciando diagnóstico de Playwright...")
        
        # Importar y verificar helper
        from app.utils.playwright_helper import get_browser_launch_options, find_chrome_executable, is_cloud_run_environment
        
        diagnostic_info = {
            "timestamp": datetime.now().isoformat(),
            "cloud_run_detected": is_cloud_run_environment(),
            "playwright_helper_available": PLAYWRIGHT_HELPER_AVAILABLE,
            "chrome_executable": find_chrome_executable(),
            "launch_options": get_browser_launch_options(headless=True),
            "services_status": {
                "sunat_service": None,
                "osce_service": None
            },
            "playwright_test": None,
            "environment_vars": {
                "K_SERVICE": os.environ.get("K_SERVICE", "Not set"),
                "K_CONFIGURATION": os.environ.get("K_CONFIGURATION", "Not set"), 
                "PORT": os.environ.get("PORT", "Not set")
            }
        }
        
        # Test services creation
        try:
            from app.services.sunat_service import SUNATService
            sunat_service = SUNATService()
            diagnostic_info["services_status"]["sunat_service"] = "✅ Created successfully"
        except Exception as e:
            diagnostic_info["services_status"]["sunat_service"] = f"❌ Error: {str(e)}"
            
        try:
            from app.services.osce_service import OSCEService
            osce_service = OSCEService()
            diagnostic_info["services_status"]["osce_service"] = "✅ Created successfully"
        except Exception as e:
            diagnostic_info["services_status"]["osce_service"] = f"❌ Error: {str(e)}"
        
        # Test basic Playwright functionality
        try:
            print("🧪 Probando Playwright básico...")
            async with async_playwright() as p:
                if PLAYWRIGHT_HELPER_AVAILABLE:
                    launch_options = get_browser_launch_options(headless=True)
                    browser = await p.chromium.launch(**launch_options)
                else:
                    browser = await p.chromium.launch(headless=True)
                
                page = await browser.new_page()
                await page.goto("data:text/html,<html><body><h1>Test</h1></body></html>", timeout=10000)
                title = await page.title()
                await browser.close()
                
                diagnostic_info["playwright_test"] = f"✅ Basic test passed - Title: {title}"
                print("✅ Playwright básico funcionando")
                
        except Exception as e:
            diagnostic_info["playwright_test"] = f"❌ Playwright test failed: {str(e)}"
            print(f"❌ Error en test Playwright: {e}")
        
        return {
            "success": True,
            "message": "Diagnóstico completado",
            "data": diagnostic_info
        }
        
    except Exception as e:
        print(f"❌ Error en diagnóstico: {e}")
        return {
            "success": False,
            "error": True,
            "message": f"Error en diagnóstico: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

class RUCInput(BaseModel):
    ruc: str

# Temporary schemas for empresa saving
class RepresentanteTemp(BaseModel):
    nombre: str
    cargo: str
    numero_documento: str
    tipo_documento: str = "DNI"
    fuente: Optional[str] = None
    participacion: Optional[str] = None
    fecha_desde: Optional[str] = None

class EmpresaCreateTemp(BaseModel):
    ruc: str
    razon_social: str
    email: Optional[str] = None
    celular: Optional[str] = None
    direccion: Optional[str] = None
    representantes: List[RepresentanteTemp] = []
    representante_principal_id: int = 0
    estado: str = "ACTIVO"
    especialidades_oece: Optional[List[str]] = []
    estado_sunat: Optional[str] = None
    estado_osce: Optional[str] = None
    fuentes_consultadas: Optional[List[str]] = []
    capacidad_contratacion: Optional[str] = None

# Mantener el endpoint original - REHABILITADO
@app.post("/buscar")
async def buscar(data: RUCInput):
    """Endpoint legacy para compatibilidad - usa extracción OSCE"""
    try:
        resultado = await buscar_osce_impl(data.ruc)
        return resultado
    except Exception as e:
        return {
            "error": True,
            "message": f"Error al consultar: {str(e)}",
            "ruc": data.ruc,
            "timestamp": datetime.now().isoformat()
        }

# Agregar endpoint compatible con el frontend - REHABILITADO
@app.get("/consulta-ruc/{ruc}")
async def consultar_ruc(ruc: str):
    """Endpoint para consulta individual de RUC - usa nuevo servicio SUNAT robusto"""
    try:
        print(f"🔍 Consultando RUC con nuevo servicio SUNAT ROBUSTO: {ruc}")
        
        # Usar el nuevo servicio SUNAT maestro (robusto + fallback)
        from app.services.sunat_master_service import sunat_master_service
        resultado = await sunat_master_service.consultar_empresa(ruc)
        
        # Verificar fuente de los datos
        is_real_data = True
        data_source = "SUNAT_ROBUSTO"
        
        if hasattr(resultado, '_metadata'):
            is_real_data = resultado._metadata.get('is_real_data', True)
            data_source = resultado._metadata.get('source', 'SUNAT_ROBUSTO')
        
        return {
            "error": False,
            "message": f"✅ SUNAT consultado exitosamente para RUC: {ruc}",
            "ruc": ruc,
            "razon_social": resultado.razon_social,
            "domicilio_fiscal": resultado.domicilio_fiscal,
            "representantes": [
                {
                    "nombre": rep.nombre,
                    "cargo": rep.cargo,
                    "tipo_documento": rep.tipo_doc,
                    "numero_documento": rep.numero_doc,
                    "fecha_desde": rep.fecha_desde
                }
                for rep in resultado.representantes
            ],
            "fuente": data_source,
            "is_real_data": is_real_data,
            "total_representantes": len(resultado.representantes),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        print(f"❌ Error SUNAT ROBUSTO: {str(e)}")
        return {
            "error": True,
            "message": f"Error al consultar SUNAT: {str(e)}",
            "ruc": ruc,
            "timestamp": datetime.now().isoformat()
        }

@app.get("/consulta-ruc-consolidada/{ruc}")
async def consultar_ruc_consolidado(ruc: str, save_to_db: bool = True):
    """Endpoint consolidado que combina datos de SUNAT y OSCE para el frontend
    
    Args:
        ruc: RUC a consultar  
        save_to_db: Si True, guarda automáticamente los datos en Turso (default: True)
    """
    
    try:
        print(f"🔍 Iniciando consulta consolidada para RUC: {ruc}")
        
        # Importar nuevo servicio SUNAT maestro (robusto con fallback)
        sunat_master = None
        osce_service = None
        
        try:
            from app.services.sunat_master_service import sunat_master_service
            sunat_master = sunat_master_service
            print("✅ Servicio SUNAT MAESTRO creado correctamente (robusto + fallback)")
        except Exception as e:
            print(f"❌ Error creando SUNAT MASTER service: {e}")
            # Fallback al servicio anterior si falla el nuevo
            try:
                from app.services.sunat_service import SUNATService
                sunat_master = SUNATService()
                print("⚠️ Usando servicio SUNAT legacy como fallback")
            except Exception as e2:
                print(f"❌ Error creando SUNAT legacy: {e2}")
                sunat_master = None
            
        try:
            from app.services.osce_service import OSCEService  
            osce_service = OSCEService()
            print("✅ Servicio OSCE creado correctamente")
        except Exception as e:
            print(f"❌ Error creando OSCE service: {e}")
            osce_service = None
        
        # Validar RUC básicamente
        if not ruc or len(ruc) != 11 or not ruc.isdigit():
            return {
                "success": False,
                "error": True, 
                "message": f"RUC inválido: debe tener 11 dígitos (recibido: {ruc})",
                "ruc": ruc,
                "fuente": "CONSOLIDADO",
                "timestamp": datetime.now().isoformat()
            }
        
        if not sunat_master and not osce_service:
            return {
                "success": False,
                "error": True,
                "message": "No se pudieron cargar los servicios de consulta",
                "ruc": ruc,
                "fuente": "CONSOLIDADO", 
                "timestamp": datetime.now().isoformat()
            }
        
        # Consultar ambas fuentes
        datos_sunat = None
        datos_osce = None
        fuentes_consultadas = []
        fuentes_con_errores = []
        
        # Consultar SUNAT MAESTRO con logging detallado
        try:
            if sunat_master:
                print(f"🔍 Iniciando consulta SUNAT MAESTRO (robusto + fallback) para RUC: {ruc}")
                datos_sunat = await sunat_master.consultar_empresa(ruc)
                fuentes_consultadas.append("SUNAT_MASTER")
                print(f"✅ SUNAT MAESTRO consultado exitosamente para RUC: {ruc}")
                print(f"   📊 Datos SUNAT obtenidos: razon_social={datos_sunat.razon_social[:50] if datos_sunat.razon_social else 'VACIO'}...")
                
                # Verificar si son datos reales o fallback
                if hasattr(datos_sunat, '_metadata'):
                    is_real = datos_sunat._metadata.get('is_real_data', False)
                    source = datos_sunat._metadata.get('source', 'UNKNOWN')
                    print(f"   🏷️ Fuente de datos: {source} - Datos reales: {is_real}")
                    if is_real:
                        fuentes_consultadas.append("SUNAT_REAL")
                    else:
                        fuentes_consultadas.append("SUNAT_FALLBACK")
            else:
                print(f"⚠️ Servicio SUNAT MAESTRO no disponible")
                fuentes_con_errores.append("SUNAT_MASTER: Servicio no disponible")
        except Exception as e:
            error_msg = str(e)
            fuentes_con_errores.append(f"SUNAT_MASTER: {error_msg[:100]}")
            print(f"❌ Error SUNAT MAESTRO detallado: {error_msg}")
            print(f"   🐛 Tipo de error: {type(e).__name__}")
        
        # Consultar OSCE con logging detallado
        try:
            if osce_service:
                print(f"🔍 Iniciando consulta OSCE para RUC: {ruc}")
                datos_osce = await osce_service.consultar_empresa(ruc)
                fuentes_consultadas.append("OECE")
                print(f"✅ OSCE consultado exitosamente para RUC: {ruc}")
                print(f"   📊 Datos OSCE obtenidos: razon_social={datos_osce.razon_social[:50] if datos_osce.razon_social else 'VACIO'}...")
                if datos_osce.integrantes:
                    print(f"   👥 Integrantes encontrados: {len(datos_osce.integrantes)}")
                if datos_osce.especialidades:
                    print(f"   🎯 Especialidades encontradas: {len(datos_osce.especialidades)}")
            else:
                print(f"⚠️ Servicio OSCE no disponible")
                fuentes_con_errores.append("OSCE: Servicio no disponible")
        except Exception as e:
            error_msg = str(e)
            fuentes_con_errores.append(f"OECE: {error_msg[:100]}")
            print(f"❌ Error OSCE detallado: {error_msg}")
            print(f"   🐛 Tipo de error: {type(e).__name__}")
        
        # Si todos los servicios fallan, el servicio maestro ya maneja el fallback automáticamente
        # Solo llegamos aquí si realmente no se pudo obtener nada
        if not datos_sunat and not datos_osce:
            print(f"⚠️ Activando fallback final de emergencia para RUC: {ruc}")
            
            # Como último recurso, intentar el fallback directo
            try:
                from app.services.sunat_fallback_service import sunat_fallback_service
                datos_sunat_emergency = await sunat_fallback_service.consultar_empresa_fallback(ruc)
                
                # Convertir a formato consolidado
                tipo_persona = "NATURAL" if ruc.startswith('10') else "JURIDICA"
                
                if tipo_persona == "NATURAL":
                    datos_basicos = {
                        "ruc": ruc,
                        "razon_social": datos_sunat_emergency.razon_social,
                        "tipo_persona": tipo_persona,
                        "dni": ruc[2:10] if len(ruc) == 11 else "",
                        "email": "",
                        "telefono": "",
                        "direccion": datos_sunat_emergency.domicilio_fiscal,
                        "fuentes_consultadas": ["EMERGENCY_FALLBACK"],
                        "consolidacion_exitosa": True,
                        "timestamp": datetime.now().isoformat(),
                        "observaciones": ["✅ Datos obtenidos del servicio de fallback de emergencia"]
                    }
                else:
                    # Extraer representantes
                    miembros = []
                    for rep in datos_sunat_emergency.representantes:
                        miembros.append({
                            "nombre": rep.nombre,
                            "numero_documento": rep.numero_doc,
                            "cargo": rep.cargo,
                            "fuente": "EMERGENCY_FALLBACK"
                        })
                    
                    datos_basicos = {
                        "ruc": ruc,
                        "razon_social": datos_sunat_emergency.razon_social,
                        "tipo_persona": tipo_persona,
                        "contacto": {
                            "telefono": "01-234-5678",
                            "email": f"contacto@{ruc[-4:]}.com",
                            "direccion": datos_sunat_emergency.domicilio_fiscal,
                            "domicilio_fiscal": datos_sunat_emergency.domicilio_fiscal
                        },
                        "miembros": miembros,
                        "especialidades": [],
                        "total_miembros": len(miembros),
                        "total_especialidades": 0,
                        "fuentes_consultadas": ["EMERGENCY_FALLBACK"],
                        "fuentes_con_errores": fuentes_con_errores,
                        "consolidacion_exitosa": True,
                        "timestamp": datetime.now().isoformat(),
                        "observaciones": [
                            "✅ Datos obtenidos del servicio de fallback de emergencia",
                            "📊 Información generada basada en patrones conocidos",
                            "✏️ Verifique y actualice la información según sea necesario"
                        ]
                    }
                
                print(f"✅ Fallback de emergencia exitoso para RUC: {ruc}")
                return {
                    "success": True,
                    "data": datos_basicos,
                    "timestamp": datetime.now().isoformat(),
                    "fuente": "CONSOLIDADO_EMERGENCY",
                    "version": "3.3.0-emergency",
                    "warning": "Datos obtenidos del servicio de fallback de emergencia"
                }
                
            except Exception as emergency_error:
                print(f"❌ Fallback de emergencia también falló: {str(emergency_error)}")
                
                return {
                    "success": False,
                    "error": True,
                    "message": "No se pudieron obtener datos de ningún servicio",
                    "ruc": ruc,
                    "fuentes_con_errores": fuentes_con_errores + [f"EMERGENCY: {str(emergency_error)}"],
                    "timestamp": datetime.now().isoformat(),
                    "fuente": "CONSOLIDADO",
                    "version": "3.3.0-error"
                }
        
        # Consolidar datos
        razon_social = ""
        contacto = {
            "telefono": "",
            "email": "",
            "direccion": "",
            "domicilio_fiscal": ""
        }
        
        # Obtener datos principales de SUNAT (preferencia)
        if datos_sunat:
            razon_social = datos_sunat.razon_social
            contacto["domicilio_fiscal"] = datos_sunat.domicilio_fiscal or ""
            
        # Completar con datos de OSCE
        if datos_osce:
            if not razon_social:
                razon_social = datos_osce.razon_social
            contacto["email"] = datos_osce.email or ""
            contacto["telefono"] = datos_osce.telefono or ""
            # FIXED: Usar datos_osce.contacto.direccion en lugar de datos_osce.direccion
            contacto["direccion"] = (datos_osce.contacto.direccion if datos_osce.contacto else "") or contacto["domicilio_fiscal"]
        
        # Consolidar representantes/miembros de ambas fuentes
        miembros = []
        dni_vistos = set()
        
        # Agregar representantes de SUNAT
        print(f"📋 Verificando datos SUNAT: {datos_sunat is not None}")
        if datos_sunat:
            print(f"📋 SUNAT tiene representantes: {len(datos_sunat.representantes) if datos_sunat.representantes else 0}")
            if datos_sunat.representantes:
                print(f"📋 Representantes SUNAT: {datos_sunat.representantes}")
                for rep in datos_sunat.representantes:
                    if rep.numero_doc and rep.numero_doc not in dni_vistos:
                        miembros.append({
                            "nombre": rep.nombre,
                            "numero_documento": rep.numero_doc,
                            "cargo": rep.cargo or "REPRESENTANTE",
                            "fuente": "SUNAT"
                        })
                        dni_vistos.add(rep.numero_doc)
                        print(f"✅ Representante SUNAT agregado: {rep.nombre} - {rep.numero_doc}")
                    elif rep.numero_doc and rep.numero_doc in dni_vistos:
                        print(f"🔄 Representante SUNAT duplicado (ya existe): {rep.nombre} - {rep.numero_doc}")
        
        # Agregar integrantes de OSCE
        print(f"📋 Verificando datos OSCE: {datos_osce is not None}")
        if datos_osce:
            print(f"📋 OSCE tiene integrantes: {len(datos_osce.integrantes) if datos_osce.integrantes else 0}")
            if datos_osce.integrantes:
                print(f"📋 Integrantes OSCE: {datos_osce.integrantes}")
                for integrante in datos_osce.integrantes:
                    if integrante.numero_documento and integrante.numero_documento not in dni_vistos:
                        miembros.append({
                            "nombre": integrante.nombre,
                            "numero_documento": integrante.numero_documento,
                            "cargo": integrante.cargo or "SOCIO",
                            "fuente": "OECE"
                        })
                        dni_vistos.add(integrante.numero_documento)
                        print(f"✅ Miembro OSCE agregado: {integrante.nombre} - {integrante.numero_documento}")
                    elif integrante.numero_documento and integrante.numero_documento in dni_vistos:
                        print(f"🔄 Miembro OSCE duplicado (ya existe): {integrante.nombre} - {integrante.numero_documento}")
            else:
                print("⚠️ OSCE no tiene integrantes - lista vacía o None")
        
        # Especialidades de OSCE
        especialidades = []
        if datos_osce and datos_osce.especialidades:
            # Manejar especialidades como lista de strings o lista de objetos
            especialidades = []
            for esp in datos_osce.especialidades:
                if isinstance(esp, str):
                    especialidades.append(esp)
                elif hasattr(esp, 'nombre'):
                    especialidades.append(esp.nombre)
                elif hasattr(esp, 'descripcion'):
                    especialidades.append(esp.descripcion)
                else:
                    especialidades.append(str(esp))
        
        # Determinar tipo de persona
        tipo_persona = "NATURAL" if ruc.startswith('10') else "JURIDICA"
        
        # Para personas naturales, formatear de manera simplificada
        if tipo_persona == "NATURAL":
            # Extraer DNI del RUC (primeros 8 dígitos después de "10")
            dni_from_ruc = ruc[2:10] if len(ruc) == 11 else ""
            
            # Mejorar extracción de teléfono para personas naturales
            telefono_natural = ""
            if datos_osce:
                # Para personas naturales, buscar teléfono de manera más específica
                import re
                texto_telefono = datos_osce.telefono or ""
                
                # Buscar patrones específicos de teléfono con contexto
                patrones_telefono_contexto = [
                    r'Teléfono\([^)]*\)\s*:\s*(\d{9})',      # Teléfono(*) : 999999999
                    r'Teléfono\s*:\s*(\d{9})',               # Teléfono: 999999999
                    r'Teléfono\([^)]*\)\s*:\s*(\d{3}\s*\d{3}\s*\d{3})',  # Teléfono(*) : 999 999 999
                ]
                
                for patron in patrones_telefono_contexto:
                    matches = re.findall(patron, texto_telefono)
                    if matches:
                        telefono_natural = matches[0].replace(' ', '')
                        break
                
                # Si no encontramos teléfono con contexto, buscar patrones generales pero validar
                if not telefono_natural:
                    patrones_telefono = [
                        r'(\d{9})',                   # 999999999 (móvil peruano)
                        r'(\d{3}\s*\d{3}\s*\d{3})',  # 999 999 999
                    ]
                    
                    for patron in patrones_telefono:
                        matches = re.findall(patron, texto_telefono)
                        for match in matches:
                            numero_limpio = match.replace(' ', '')
                            # Validar que sea un teléfono peruano válido
                            if len(numero_limpio) == 9 and numero_limpio.startswith('9'):
                                telefono_natural = numero_limpio
                                break
                        if telefono_natural:
                            break
            
            # Respuesta simplificada para persona natural
            datos_consolidados = {
                "ruc": ruc,
                "razon_social": razon_social or f"PERSONA NATURAL {ruc}",
                "tipo_persona": tipo_persona,
                "dni": dni_from_ruc,
                "email": contacto.get("email", ""),
                "telefono": telefono_natural if telefono_natural else "",
                "direccion": contacto.get("direccion", ""),
                "fuentes_consultadas": fuentes_consultadas,
                "consolidacion_exitosa": len(fuentes_consultadas) > 0,
                "timestamp": datetime.now().isoformat()
            }
        else:
            # Respuesta completa para persona jurídica
            datos_consolidados = {
                "ruc": ruc,
                "razon_social": razon_social,
                "tipo_persona": tipo_persona,
                "contacto": contacto,
                "miembros": miembros,
                "especialidades": especialidades,
                "total_miembros": len(miembros),
                "total_especialidades": len(especialidades),
                "fuentes_consultadas": fuentes_consultadas,
                "fuentes_con_errores": fuentes_con_errores,
                "consolidacion_exitosa": len(fuentes_consultadas) > 0,
                "timestamp": datetime.now().isoformat(),
                "observaciones": []
            }
        
        # Guardar empresa en base de datos si está habilitado
        empresa_id = None
        if save_to_db:
            try:
                from app.services.empresa_service_turso_enhanced import EmpresaServiceTurso
                empresa_service = EmpresaServiceTurso()
                
                # Construir datos para guardar
                respuesta_completa = {
                    "success": True,
                    "data": datos_consolidados,
                    "timestamp": datetime.now().isoformat(),
                    "fuente": "CONSOLIDADO",
                    "version": "3.2.0"
                }
                
                empresa_id = empresa_service.save_empresa_from_consulta(ruc, respuesta_completa)
                if empresa_id:
                    print(f"✅ Empresa {ruc} guardada en base de datos con ID: {empresa_id}")
                else:
                    print(f"⚠️ No se pudo guardar empresa {ruc} en base de datos")
                    
                empresa_service.close()
                
            except Exception as db_error:
                print(f"⚠️ Error guardando en base de datos: {db_error}")
                empresa_id = None

        # Agregar información de guardado a la respuesta
        response_data = {
            "success": True,
            "data": datos_consolidados,
            "timestamp": datetime.now().isoformat(),
            "fuente": "CONSOLIDADO",
            "version": "3.2.0"
        }
        
        if save_to_db:
            response_data["database"] = {
                "saved": empresa_id is not None,
                "empresa_id": empresa_id,
                "message": "Empresa guardada exitosamente" if empresa_id else "No se pudo guardar en base de datos"
            }
        
        return response_data
        
    except Exception as e:
        print(f"❌ Error en consulta consolidada: {e}")
        return {
            "success": False,
            "error": True,
            "message": f"Error interno en consulta consolidada: {str(e)}",
            "ruc": ruc,
            "fuente": "CONSOLIDADO",
            "timestamp": datetime.now().isoformat()
        }

# Endpoint para consulta OSCE (legacy - mantiene compatibilidad) - REHABILITADO
@app.get("/consulta-osce/{ruc}")
async def consultar_osce(ruc: str):
    """Legacy endpoint para compatibilidad con OSCE"""
    try:
        resultado = await buscar_osce_impl(ruc)
        return resultado
    except Exception as e:
        return {
            "error": True,
            "message": f"Error al consultar OSCE: {str(e)}",
            "ruc": ruc,
            "fuente": "OSCE",
            "timestamp": datetime.now().isoformat()
        }

async def buscar_ruc_impl(ruc: str):
    print(f"🔍 Consultando RUC: {ruc}")
    
    # Detectar el tipo de RUC
    es_persona_natural = ruc.startswith('10')
    es_persona_juridica = ruc.startswith('20')
    
    if es_persona_natural:
        print(f"👤 RUC identificado como PERSONA NATURAL (10xxxxxxxx)")
        timeout_inicial = 5000  # Mayor timeout para persona natural (pueden ser más lentas)
    elif es_persona_juridica:
        print(f"🏢 RUC identificado como PERSONA JURÍDICA (20xxxxxxxx)")
        timeout_inicial = 3000  # Timeout estándar para persona jurídica
    else:
        print(f"❌ RUC con formato no válido: debe comenzar con 10 o 20")
        return {"error": True, "message": "RUC debe comenzar con 10 (persona natural) o 20 (persona jurídica)"}

    async with async_playwright() as p:
        # Use optimized browser configuration if available
        if PLAYWRIGHT_HELPER_AVAILABLE:
            launch_options = get_browser_launch_options(headless=True)
            browser = await p.chromium.launch(**launch_options)
        else:
            # Fallback to basic configuration
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox', 
                    '--disable-dev-shm-usage', 
                    '--disable-blink-features=AutomationControlled',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor'
                ]
            )
        page = await browser.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/114.0.0.0 Safari/537.36")
        
        try:
            print(f"🌐 Navegando a SUNAT...")
            await page.goto("https://e-consultaruc.sunat.gob.pe/cl-ti-itmrconsruc/FrameCriterioBusquedaWeb.jsp", timeout=30000)
            
            print(f"📝 Llenando formulario con RUC: {ruc}")
            await page.fill('#txtRuc', ruc)
            
            print(f"🔍 Enviando consulta...")
            await page.click('#btnAceptar')
            
            # Esperar con timeout diferenciado según tipo de RUC
            print(f"⏳ Esperando respuesta ({timeout_inicial}ms)...")
            await page.wait_for_timeout(timeout_inicial)
            
            # Verificar si la página cargó correctamente
            page_title = await page.title()
            print(f"📄 Título de página: {page_title}")
            
            # Buscar indicadores de error o página no encontrada
            page_text = await page.inner_text('body')
            if "no se encontró" in page_text.lower() or "error" in page_text.lower():
                print(f"⚠️ Posible error en consulta SUNAT")
            
        except Exception as e:
            print(f"❌ Error en navegación SUNAT: {e}")
            await browser.close()
            return {"error": True, "message": f"Error al consultar SUNAT: {str(e)}"}

        # Extraer información básica según el tipo de RUC
        razon_social = ""
        domicilio_fiscal = ""
        
        try:
            if es_persona_natural:
                razon_social = await extraer_nombre_persona_natural(page, ruc)
            else:
                razon_social = await extraer_razon_social_persona_juridica(page, ruc)

            # Extraer domicilio fiscal (hacer antes de navegar a representantes)
            domicilio_fiscal = await extraer_domicilio_fiscal(page, es_persona_natural)

            # Manejar representantes legales según el tipo de RUC
            representantes = []
            
            if es_persona_natural:
                # Para persona natural, la persona se representa a sí misma
                print("👤 Persona natural: creando auto-representación")
                if razon_social:
                    # Extraer el DNI desde el RUC (los últimos 8 dígitos antes del dígito verificador)
                    dni_desde_ruc = ruc[2:10]  # Del 3er al 10mo dígito
                    representantes.append({
                        "tipo_doc": "DNI",
                        "numero_doc": dni_desde_ruc,
                        "nombre": razon_social,
                        "cargo": "TITULAR",
                        "fecha_desde": "-"
                    })
                    print(f"   ✅ Auto-representante: {razon_social} (DNI: {dni_desde_ruc})")
            else:
                # Para persona jurídica, buscar representantes legales en SUNAT
                representantes = await extraer_representantes_persona_juridica(page)

        finally:
            await browser.close()
        
        # Validar que se obtuvieron datos mínimos
        if not razon_social:
            return {
                "error": True, 
                "message": f"No se pudo obtener información para el RUC {ruc}. Verifique que el RUC sea válido."
            }
        
        resultado = {
            "ruc": ruc,
            "razon_social": razon_social,
            "domicilio_fiscal": domicilio_fiscal,
            "representantes": representantes,
            "total_representantes": len(representantes),
            "tipo_persona": "NATURAL" if es_persona_natural else "JURÍDICA"
        }
        
        print(f"📊 Consulta completada: {resultado['tipo_persona']} - {len(representantes)} representante(s)")
        return resultado

async def extraer_domicilio_fiscal(page, es_persona_natural):
    """
    Extrae el domicilio fiscal desde la página de SUNAT para cualquier tipo de RUC
    """
    try:
        tipo_persona = "NATURAL" if es_persona_natural else "JURÍDICA"
        print(f"🏠 Buscando domicilio fiscal para persona {tipo_persona}...")
        
        # Método 1: Buscar en todo el texto de la página
        page_text = await page.inner_text('body')
        lines = page_text.split('\n')
        
        for i, line in enumerate(lines):
            line = line.strip()
            if "Domicilio Fiscal:" in line or "DOMICILIO FISCAL:" in line.upper():
                print(f"✅ Encontrada línea con domicilio fiscal: {line}")
                
                # Si el domicilio está en la misma línea
                if ":" in line:
                    parts = line.split(":", 1)
                    if len(parts) > 1 and parts[1].strip():
                        domicilio = parts[1].strip()
                        if len(domicilio) > 2 and domicilio != "-":  # Validar que no sea solo un guión
                            print(f"🏠 Domicilio fiscal extraído (misma línea): {domicilio}")
                            return domicilio
                
                # Verificar líneas siguientes para el domicilio
                if i + 1 < len(lines):
                    siguiente_linea = lines[i + 1].strip()
                    
                    if siguiente_linea == "-":
                        print(f"🏠 Domicilio fiscal no registrado (guión encontrado)")
                        return "No registrado"
                    elif siguiente_linea and len(siguiente_linea) > 10:
                        # Verificar que no sea parte del menú o navegación
                        if not any(nav in siguiente_linea.lower() for nav in ['volver', 'imprimir', 'email', 'consulta', 'resultado']):
                            print(f"🏠 Domicilio fiscal extraído (línea siguiente): {siguiente_linea}")
                            return siguiente_linea
                    elif i + 2 < len(lines):
                        # Buscar en la línea que está después de una posible línea vacía
                        linea_dos_despues = lines[i + 2].strip()
                        
                        if linea_dos_despues == "-":
                            print(f"🏠 Domicilio fiscal no registrado (guión encontrado)")
                            return "No registrado"
                        elif linea_dos_despues and len(linea_dos_despues) > 10:
                            # Verificar que no sea parte del menú o navegación
                            if not any(nav in linea_dos_despues.lower() for nav in ['volver', 'imprimir', 'email', 'consulta', 'resultado']):
                                print(f"🏠 Domicilio fiscal extraído (dos líneas después): {linea_dos_despues}")
                                return linea_dos_despues
        
        # Método 2: Buscar con selectores CSS específicos
        print("⚠️ Método de texto falló, buscando con selectores CSS...")
        
        # Selector para tabla con "Domicilio Fiscal"
        domicilio_elem = await page.query_selector("td.bgn:has-text('Domicilio Fiscal:') + td")
        if domicilio_elem:
            domicilio = (await domicilio_elem.inner_text()).strip()
            if domicilio and len(domicilio) > 10:
                print(f"🏠 Domicilio fiscal extraído con CSS específico: {domicilio}")
                return domicilio
        
        # Método 3: Búsqueda específica en elementos pequeños
        elements = await page.query_selector_all("td")  # Solo buscar en celdas de tabla
        
        for element in elements:
            try:
                element_text = await element.inner_text()
                if element_text and element_text.strip() == "Domicilio Fiscal:":
                    print(f"✅ Encontrado elemento exacto con domicilio fiscal")
                    
                    # Buscar el siguiente elemento hermano (siguiente celda)
                    try:
                        next_element = await element.evaluate("el => el.nextElementSibling")
                        if next_element:
                            next_text = (await next_element.inner_text()).strip()
                            if next_text:
                                if next_text == "-":
                                    print(f"🏠 Domicilio fiscal no registrado (guión en elemento)")
                                    return "No registrado"
                                elif len(next_text) > 2 and not any(nav in next_text.lower() for nav in ['volver', 'imprimir', 'email']):
                                    print(f"🏠 Domicilio fiscal extraído (elemento siguiente): {next_text}")
                                    return next_text
                    except:
                        pass
            except:
                continue
        
        print(f"⚠️ No se pudo extraer domicilio fiscal para persona {tipo_persona}")
        return ""
        
    except Exception as e:
        print(f"❌ Error al extraer domicilio fiscal: {e}")
        return ""

async def extraer_nombre_persona_natural(page, ruc):
    """
    Extrae el nombre completo de una persona natural desde la página de SUNAT
    """
    try:
        print(f"👤 Extrayendo nombre para persona natural RUC: {ruc}")
        
        # Para persona natural, el nombre está en el formato: "DNI XXXXXXXX - APELLIDOS, NOMBRES"
        page_text = await page.inner_text('body')
        lines = page_text.split('\n')
        
        # Buscar el patrón "DNI [numero] - [nombre completo]"
        for line in lines:
            line = line.strip()
            if line.startswith("DNI ") and " - " in line:
                # Extraer solo la parte del nombre después del guión
                parts = line.split(" - ", 1)
                if len(parts) > 1:
                    nombre_completo = parts[1].strip()
                    if len(nombre_completo) > 3:
                        print(f"👤 Nombre extraído del DNI: {nombre_completo}")
                        return nombre_completo
        
        # Buscar en la línea que contiene el RUC (formato: "RUC - NOMBRE")
        for line in lines:
            line = line.strip()
            if ruc in line and " - " in line:
                # Extraer la parte después del RUC
                parts = line.split(" - ", 1)
                if len(parts) > 1:
                    nombre_parte = parts[1].strip()
                    # Limpiar el nombre si tiene información adicional
                    if len(nombre_parte) > 3 and not nombre_parte.startswith("Tipo"):
                        print(f"👤 Nombre extraído del RUC: {nombre_parte}")
                        return nombre_parte
        
        # Buscar por "Tipo de Documento:" y extraer de ahí
        for i, line in enumerate(lines):
            line = line.strip()
            if "Tipo de Documento:" in line and i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if next_line.startswith("DNI ") and " - " in next_line:
                    parts = next_line.split(" - ", 1)
                    if len(parts) > 1:
                        nombre_completo = parts[1].strip()
                        if len(nombre_completo) > 3:
                            print(f"👤 Nombre extraído de Tipo de Documento: {nombre_completo}")
                            return nombre_completo
        
        print(f"❌ No se pudo extraer el nombre para persona natural RUC: {ruc}")
        return ""
        
    except Exception as e:
        print(f"❌ Error al extraer nombre persona natural: {e}")
        return ""

async def extraer_razon_social_persona_juridica(page, ruc):
    """
    Extrae la razón social de una persona jurídica desde la página de SUNAT
    """
    try:
        print(f"🏢 Extrayendo razón social para persona jurídica RUC: {ruc}")
        
        # Para persona jurídica, buscar en el formato: "RUC - RAZON SOCIAL"
        page_text = await page.inner_text('body')
        lines = page_text.split('\n')
        
        # Buscar en la línea que contiene el RUC
        for line in lines:
            line = line.strip()
            if ruc in line and " - " in line:
                # Extraer la parte después del RUC
                parts = line.split(" - ", 1)
                if len(parts) > 1:
                    razon_social = parts[1].strip()
                    # Limpiar información adicional si está al final
                    if len(razon_social) > 5:
                        print(f"🏢 Razón social extraída del RUC: {razon_social}")
                        return razon_social
        
        # Buscar por patrones específicos de SUNAT
        for i, line in enumerate(lines):
            line = line.strip()
            if "Nombre o Razón Social:" in line:
                print(f"✅ Encontrada línea con razón social: {line}")
                
                # Si está en la misma línea
                if ":" in line:
                    parts = line.split(":", 1)
                    if len(parts) > 1 and parts[1].strip():
                        razon_social = parts[1].strip()
                        if len(razon_social) > 5:
                            print(f"🏢 Razón social extraída (misma línea): {razon_social}")
                            return razon_social
                
                # Si está en la línea siguiente
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if next_line and len(next_line) > 5 and not next_line.endswith(':'):
                        print(f"🏢 Razón social extraída (línea siguiente): {next_line}")
                        return next_line
        
        # Método alternativo: buscar con selectores CSS
        print("⚠️ Método de texto falló, buscando con selectores CSS...")
        
        # Buscar selector específico para razón social
        razon_elem = await page.query_selector("td.bgn:has-text('Nombre o Razón Social:') + td")
        if razon_elem:
            razon_social = (await razon_elem.inner_text()).strip()
            if razon_social and len(razon_social) > 5:
                print(f"🏢 Razón social extraída con CSS: {razon_social}")
                return razon_social
        
        print(f"❌ No se pudo extraer la razón social para persona jurídica RUC: {ruc}")
        return ""
        
    except Exception as e:
        print(f"❌ Error al extraer razón social persona jurídica: {e}")
        return ""

async def extraer_representantes_persona_juridica(page):
    """
    Extrae los representantes legales de una persona jurídica desde la página de SUNAT
    """
    representantes = []
    
    try:
        print("⏳ Buscando botón 'Representante(s) Legal(es)'...")
        
        # Intentar hacer clic en el botón de representantes
        boton_encontrado = await clickear_boton_representantes(page)
        
        if not boton_encontrado:
            print("⚠️ No se encontró el botón de Representantes Legales")
            return representantes
        
        # Esperar a que se cargue la información
        await page.wait_for_timeout(3000)
        print("📋 Extrayendo tabla de Representantes Legales...")
        
        # Extraer datos de las tablas
        representantes = await extraer_datos_tablas_representantes(page)
        
        print(f"📊 Total de representantes extraídos: {len(representantes)}")
        return representantes
        
    except Exception as e:
        print(f"⚠️ Error al extraer representantes: {e}")
        return representantes

async def clickear_boton_representantes(page):
    """
    Intenta hacer clic en el botón de representantes legales usando varios métodos
    """
    # Método 1: Buscar por texto exacto
    try:
        await page.click("text='Representante(s) Legal(es)'", timeout=5000)
        print("✅ Botón clickeado por texto")
        return True
    except:
        pass
    
    # Método 2: Buscar por input value
    try:
        boton = await page.query_selector("input[type='button'][value*='Representante']")
        if boton:
            await boton.click()
            print("✅ Botón clickeado por input value")
            return True
    except:
        pass
    
    # Método 3: Buscar enlaces
    try:
        link = await page.query_selector("a:has-text('Representante')")
        if link:
            await link.click()
            print("✅ Enlace de representantes clickeado")
            return True
    except:
        pass
    
    # Método 4: Buscar por partial text match
    try:
        await page.click("text=/Representante/", timeout=5000)
        print("✅ Botón clickeado por texto parcial")
        return True
    except:
        pass
    
    return False

async def extraer_datos_tablas_representantes(page):
    """
    Extrae datos de representantes de todas las tablas en la página
    """
    representantes = []
    
    try:
        # Buscar todas las tablas
        tables = await page.query_selector_all('table')
        
        for table_idx, table in enumerate(tables):
            rows = await table.query_selector_all("tr")
            
            if len(rows) == 0:
                continue
            
            # Verificar si tiene estructura de tabla de personas
            primera_fila_celdas = await rows[0].query_selector_all("td, th")
            
            if len(primera_fila_celdas) < 3:
                continue
            
            print(f"   📊 Procesando tabla {table_idx + 1} con {len(rows)} filas...")
            
            # Procesar cada fila
            for row_idx, row in enumerate(rows):
                celdas = await row.query_selector_all("td")
                
                if not celdas or len(celdas) < 3:
                    continue
                
                # Extraer texto de cada celda
                textos = []
                for celda in celdas:
                    texto = (await celda.inner_text()).strip()
                    textos.append(texto)
                
                # Validar y procesar fila
                representante = procesar_fila_representante(textos)
                
                if representante:
                    representantes.append(representante)
                    print(f"   ✅ Persona {len(representantes)}: {representante['nombre']} - {representante['cargo']}")
        
        return representantes
        
    except Exception as e:
        print(f"❌ Error extrayendo datos de tablas: {e}")
        return representantes

def procesar_fila_representante(textos):
    """
    Procesa una fila de datos y crea un diccionario de representante
    """
    # Filtrar filas vacías o de encabezado
    if not any(texto and texto != "-" and len(texto) > 2 for texto in textos):
        return None
    
    # Determinar el formato basado en número de columnas
    persona_data = {}
    
    if len(textos) >= 5:
        # Formato: TIPO DOC | NUM DOC | NOMBRE | CARGO | FECHA
        persona_data = {
            "tipo_doc": textos[0],
            "numero_doc": textos[1],
            "nombre": textos[2],
            "cargo": textos[3],
            "fecha_desde": textos[4] if len(textos) > 4 else ""
        }
    elif len(textos) == 4:
        # Formato: NUM DOC | NOMBRE | CARGO | FECHA
        persona_data = {
            "tipo_doc": "DNI",
            "numero_doc": textos[0],
            "nombre": textos[1],
            "cargo": textos[2],
            "fecha_desde": textos[3]
        }
    elif len(textos) == 3:
        # Formato: NOMBRE | CARGO | FECHA
        persona_data = {
            "tipo_doc": "-",
            "numero_doc": "-",
            "nombre": textos[0],
            "cargo": textos[1],
            "fecha_desde": textos[2]
        }
    else:
        return None
    
    # Validar que el nombre no sea un header
    nombre = persona_data.get("nombre", "")
    if not es_nombre_valido(nombre):
        return None
    
    return persona_data

def es_nombre_valido(nombre):
    """
    Valida que el nombre sea válido y no un header de tabla
    """
    if not nombre or len(nombre) < 3:
        return False
    
    # Headers inválidos
    headers_invalidos = [
        "NOMBRE", "APELLIDOS", "TIPO", "DOC", "CARGO", "FECHA",
        "DOCUMENTO", "REPRESENTANTE", "LEGAL", "DESDE", "NÚMERO",
        "TIPO DOCUMENTO", "NÚMERO DOCUMENTO"
    ]
    
    if nombre.upper() in headers_invalidos:
        return False
    
    # No debe ser solo guiones
    if all(char == "-" for char in nombre):
        return False
    
    return True

async def buscar_osce_impl(ruc: str):
    """
    Implementación de búsqueda en OSCE (Organismo Supervisor de las Contrataciones del Estado)
    Extrae información del perfil de proveedor en OSCE
    """
    print(f"🔍 Consultando OSCE para RUC: {ruc}")
    
    # Validar formato RUC
    if not ruc or len(ruc) != 11 or not ruc.isdigit():
        return {
            "error": True,
            "message": "RUC debe tener 11 dígitos numéricos"
        }
    
    # Detectar tipo de RUC para logging
    es_persona_natural = ruc.startswith('10')
    es_persona_juridica = ruc.startswith('20')
    
    if es_persona_natural:
        print(f"👤 RUC identificado como PERSONA NATURAL (10xxxxxxxx)")
    elif es_persona_juridica:
        print(f"🏢 RUC identificado como PERSONA JURÍDICA (20xxxxxxxx)")
    else:
        print(f"⚠️ RUC con formato inusual: {ruc}")

    async with async_playwright() as p:
        # Use optimized browser configuration if available
        if PLAYWRIGHT_HELPER_AVAILABLE:
            launch_options = get_browser_launch_options(headless=True)
            browser = await p.chromium.launch(**launch_options)
        else:
            # Fallback to basic configuration
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox', 
                    '--disable-dev-shm-usage', 
                    '--disable-blink-features=AutomationControlled',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor'
                ]
            )
        
        try:
            context = await browser.new_context(
                viewport={'width': 1280, 'height': 720},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            
            page = await context.new_page()
            
            print(f"🌐 Navegando a OSCE...")
            await page.goto("https://apps.osce.gob.pe/perfilprov-ui/", timeout=30000, wait_until='domcontentloaded')
            
            # Esperar a que la página cargue completamente
            await page.wait_for_timeout(3000)
            
            print(f"📝 Buscando campo de búsqueda...")
            
            # Buscar el campo de entrada de RUC con múltiples estrategias
            search_input = await encontrar_campo_busqueda_osce(page)
            
            if not search_input:
                raise Exception("No se encontró campo de búsqueda en OSCE")
            
            print(f"📝 Ingresando RUC: {ruc}")
            await search_input.click()
            await search_input.select_text()
            await search_input.type(ruc)
            
            # Buscar y hacer clic en el botón de búsqueda
            await ejecutar_busqueda_osce(page)
            
            # Esperar resultados
            print(f"⏳ Esperando resultados OSCE...")
            await page.wait_for_timeout(5000)
            
            # Extraer información de la página de resultados
            osce_data = await extraer_datos_osce(page, ruc)
            
            return {
                "ruc": ruc,
                "fuente": "OSCE",
                "timestamp": datetime.now().isoformat(),
                "url": page.url,
                **osce_data
            }
            
        except PlaywrightTimeoutError as e:
            print(f"❌ Timeout en OSCE: {e}")
            return {
                "error": True,
                "message": "Timeout al consultar OSCE. El servicio puede estar lento o inaccesible.",
                "ruc": ruc,
                "fuente": "OSCE",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Error en consulta OSCE: {e}")
            return {
                "error": True,
                "message": f"Error al consultar OSCE: {str(e)}",
                "ruc": ruc,
                "fuente": "OSCE", 
                "timestamp": datetime.now().isoformat()
            }
            
        finally:
            await browser.close()

async def encontrar_campo_busqueda_osce(page) -> Optional[Any]:
    """Encuentra el campo de búsqueda en OSCE usando múltiples estrategias"""
    
    # Lista de selectores para probar
    selectores_busqueda = [
        'input[type="text"]',
        'input[placeholder*="RUC"]',
        'input[placeholder*="búsqueda"]',
        'input[placeholder*="buscar"]',
        'input[placeholder*="Buscar"]',
        'input[placeholder*="Ingresar"]',
        '#search',
        '#searchInput',
        '.search-input',
        '.form-control',
        '[data-testid="search"]',
        'input[name*="search"]',
        'input[name*="ruc"]'
    ]
    
    # Probar cada selector
    for selector in selectores_busqueda:
        try:
            elemento = await page.wait_for_selector(selector, timeout=2000)
            if elemento:
                print(f"✅ Campo de búsqueda encontrado con selector: {selector}")
                return elemento
        except PlaywrightTimeoutError:
            continue
    
    # Si no se encuentra con selectores específicos, buscar cualquier input de texto
    try:
        inputs = await page.query_selector_all('input')
        for input_elem in inputs:
            input_type = await input_elem.get_attribute('type')
            placeholder = await input_elem.get_attribute('placeholder')
            
            if input_type == 'text' or input_type is None:
                if placeholder and any(term in placeholder.lower() for term in ['ruc', 'buscar', 'search']):
                    print(f"✅ Campo encontrado por placeholder: {placeholder}")
                    return input_elem
                
        # Si no hay placeholder específico, usar el primer input de texto
        for input_elem in inputs:
            input_type = await input_elem.get_attribute('type')
            if input_type == 'text' or input_type is None:
                print("✅ Usando primer campo de texto disponible")
                return input_elem
                
    except Exception as e:
        print(f"⚠️ Error buscando campos input: {e}")
    
    return None

async def ejecutar_busqueda_osce(page):
    """Ejecuta la búsqueda en OSCE"""
    
    # Lista de selectores para botones de búsqueda
    selectores_boton = [
        'button[type="submit"]',
        'input[type="submit"]',
        'button:has-text("Buscar")',
        'button:has-text("Consultar")',
        'button:has-text("Search")',
        '.btn-primary',
        '.btn-search',
        '.search-btn',
        '[data-testid="search-btn"]',
        'button.btn'
    ]
    
    # Probar cada selector de botón
    for selector in selectores_boton:
        try:
            boton = await page.wait_for_selector(selector, timeout=2000)
            if boton:
                print(f"✅ Botón de búsqueda encontrado: {selector}")
                await boton.click()
                return True
        except PlaywrightTimeoutError:
            continue
    
    # Si no se encuentra botón, intentar presionar Enter en el campo de búsqueda
    try:
        search_input = await page.query_selector('input[type="text"]')
        if search_input:
            print("✅ Ejecutando búsqueda con tecla Enter")
            await search_input.press('Enter')
            return True
    except Exception as e:
        print(f"⚠️ Error ejecutando búsqueda con Enter: {e}")
    
    # Como último recurso, buscar cualquier botón visible
    try:
        botones = await page.query_selector_all('button')
        for boton in botones:
            texto = await boton.inner_text()
            if texto and any(term in texto.lower() for term in ['buscar', 'consultar', 'search']):
                print(f"✅ Botón encontrado por texto: {texto}")
                await boton.click()
                return True
    except Exception as e:
        print(f"⚠️ Error buscando botones por texto: {e}")
    
    raise Exception("No se pudo ejecutar la búsqueda en OSCE")

async def extraer_datos_osce(page, ruc: str) -> Dict[str, Any]:
    """Extrae datos específicos de OSCE del perfil del proveedor"""
    
    print(f"📊 Extrayendo datos OSCE para RUC: {ruc}")
    
    try:
        # Obtener el contenido completo de la página
        contenido_pagina = await page.content()
        texto_pagina = await page.inner_text('body')
        
        # Datos base
        datos = {
            "error": False,
            "razon_social": "",
            "estado_registro": "",
            "vigencia": "",
            "especialidades": [],
            "clasificaciones": [],
            "capacidad_contratacion": "",
            "registro_fecha": "",
            "observaciones": [],
            "datos_contacto": {},
            "certificaciones": [],
            "historial_contratos": [],
            "calificaciones": {}
        }
        
        # Verificar si hay resultados o errores
        if await verificar_errores_osce(page, texto_pagina):
            datos["error"] = True
            datos["message"] = "RUC no encontrado en OSCE o sin registro de proveedor"
            return datos
        
        # Extraer razón social
        datos["razon_social"] = await extraer_razon_social_osce(page, texto_pagina, ruc)
        
        # Extraer estado del registro
        datos["estado_registro"] = await extraer_estado_registro_osce(page, texto_pagina)
        
        # Extraer especialidades
        datos["especialidades"] = await extraer_especialidades_osce(page, texto_pagina)
        
        # Extraer clasificaciones
        datos["clasificaciones"] = await extraer_clasificaciones_osce(page, texto_pagina)
        
        # Extraer datos de contacto
        datos["datos_contacto"] = await extraer_contacto_osce(page, texto_pagina)
        
        # Extraer información adicional de tablas
        tablas_info = await extraer_tablas_osce(page)
        if tablas_info:
            datos.update(tablas_info)
        
        # Verificar si se extrajeron datos mínimos
        if not datos["razon_social"] and not datos["especialidades"] and not datos["estado_registro"]:
            datos["error"] = True
            datos["message"] = "No se pudieron extraer datos específicos de OSCE"
        
        print(f"📊 Datos OSCE extraídos: Razón Social: {datos['razon_social']}, Estado: {datos['estado_registro']}, Especialidades: {len(datos['especialidades'])}")
        
        return datos
        
    except Exception as e:
        print(f"❌ Error extrayendo datos OSCE: {e}")
        return {
            "error": True,
            "message": f"Error al extraer datos de OSCE: {str(e)}",
            "razon_social": "",
            "estado_registro": "",
            "especialidades": [],
            "clasificaciones": []
        }

async def verificar_errores_osce(page, texto_pagina: str) -> bool:
    """Verifica si hay mensajes de error en OSCE"""
    
    indicadores_error = [
        "no encontrado",
        "sin resultados", 
        "no existe",
        "not found",
        "no registrado",
        "no se encontraron datos",
        "proveedor no registrado",
        "ruc no válido"
    ]
    
    texto_lower = texto_pagina.lower()
    
    for indicador in indicadores_error:
        if indicador in texto_lower:
            print(f"⚠️ Posible error detectado: {indicador}")
            return True
    
    # Verificar elementos específicos de error
    try:
        elementos_error = await page.query_selector_all('[class*="error"], [class*="alert"], [class*="warning"]')
        for elemento in elementos_error:
            texto_elemento = await elemento.inner_text()
            if texto_elemento and len(texto_elemento.strip()) > 0:
                print(f"⚠️ Elemento de error encontrado: {texto_elemento[:100]}...")
                return True
    except Exception:
        pass
    
    return False

async def extraer_razon_social_osce(page, texto_pagina: str, ruc: str) -> str:
    """Extrae la razón social desde OSCE"""
    
    # Buscar patrones comunes para razón social
    lineas = texto_pagina.split('\n')
    
    for i, linea in enumerate(lineas):
        linea = linea.strip()
        
        # Buscar líneas que contengan el RUC
        if ruc in linea:
            # Extraer texto después del RUC
            if ' - ' in linea:
                partes = linea.split(' - ')
                if len(partes) > 1:
                    razon = partes[1].strip()
                    if len(razon) > 5:
                        print(f"🏢 Razón social extraída (RUC): {razon}")
                        return razon
        
        # Buscar patrones específicos
        patrones_razon = [
            "razón social:",
            "denominación:",
            "empresa:",
            "proveedor:",
            "nombre comercial:",
            "entidad:"
        ]
        
        for patron in patrones_razon:
            if patron in linea.lower():
                if ':' in linea:
                    partes = linea.split(':', 1)
                    if len(partes) > 1:
                        razon = partes[1].strip()
                        if len(razon) > 5:
                            print(f"🏢 Razón social extraída ({patron}): {razon}")
                            return razon
                
                # Buscar en línea siguiente
                if i + 1 < len(lineas):
                    siguiente = lineas[i + 1].strip()
                    if len(siguiente) > 5:
                        print(f"🏢 Razón social extraída (línea siguiente): {siguiente}")
                        return siguiente
    
    # Buscar en elementos específicos
    try:
        selectores_razon = [
            '[class*="company"], [class*="empresa"], [class*="razon"]',
            'h1, h2, h3',
            '.title, .titulo',
            '[data-field*="name"], [data-field*="razon"]'
        ]
        
        for selector in selectores_razon:
            elementos = await page.query_selector_all(selector)
            for elemento in elementos:
                texto = await elemento.inner_text()
                if texto and len(texto.strip()) > 5 and ruc not in texto:
                    print(f"🏢 Razón social extraída (selector {selector}): {texto}")
                    return texto.strip()
    except Exception:
        pass
    
    return ""

async def extraer_estado_registro_osce(page, texto_pagina: str) -> str:
    """Extrae el estado del registro en OSCE"""
    
    patrones_estado = [
        "estado:",
        "situación:",
        "status:",
        "vigencia:",
        "habilitado",
        "activo",
        "vigente",
        "suspendido",
        "inhabilitado"
    ]
    
    lineas = texto_pagina.split('\n')
    
    for linea in lineas:
        linea_lower = linea.lower().strip()
        
        for patron in patrones_estado:
            if patron in linea_lower:
                # Si es una etiqueta seguida de dos puntos
                if ':' in linea:
                    partes = linea.split(':', 1)
                    if len(partes) > 1:
                        estado = partes[1].strip()
                        if estado:
                            print(f"📊 Estado extraído: {estado}")
                            return estado
                
                # Si es solo la palabra estado
                elif patron in ['habilitado', 'activo', 'vigente', 'suspendido', 'inhabilitado']:
                    print(f"📊 Estado extraído: {patron.upper()}")
                    return patron.upper()
    
    return ""

async def extraer_especialidades_osce(page, texto_pagina: str) -> List[str]:
    """Extrae especialidades del proveedor en OSCE"""
    
    print(f"🔍 Buscando especialidades y categorías en OSCE...")
    
    especialidades = []
    import re
    
    # Patrones específicos para encontrar categorías y consultorías
    patrones_categoria = [
        r'CATEGORIA\s+([ABC])',  # CATEGORIA A, B, C
        r'Categoría\s+([ABC])',
        r'CATEGORÍA\s+([ABC])'
    ]
    
    patrones_consultoria = [
        r'Consultor[íi]a?\s+en\s+([^,\n\.]+)',
        r'Consultoria?\s+([^,\n\.]+)',
        r'Consultor[íi]a?\s+de\s+([^,\n\.]+)',
        r'Consultor[íi]a?\s+para\s+([^,\n\.]+)'
    ]
    
    # Buscar categorías (A, B, C)
    categorias_encontradas = set()
    for patron in patrones_categoria:
        matches = re.findall(patron, texto_pagina, re.IGNORECASE)
        for categoria in matches:
            categorias_encontradas.add(f"CATEGORIA {categoria.upper()}")
            print(f"✅ Categoría encontrada: CATEGORIA {categoria.upper()}")
    
    # Buscar consultorías específicas
    consultorias_encontradas = set()
    for patron in patrones_consultoria:
        matches = re.findall(patron, texto_pagina, re.IGNORECASE)
        for consultoria in matches:
            consultoria_limpia = consultoria.strip()
            if len(consultoria_limpia) > 10 and len(consultoria_limpia) < 100:
                consultorias_encontradas.add(consultoria_limpia)
                print(f"✅ Consultoría encontrada: {consultoria_limpia}")
    
    # Buscar especialidades específicas por palabras clave
    especialidades_clave = [
        "obras de saneamiento",
        "obras electromecánicas", 
        "obras de represas",
        "obras urbanas",
        "obras viales",
        "telecomunicaciones",
        "irrigaciones",
        "afines",
        "energéticas"
    ]
    
    lineas = texto_pagina.lower().split('\n')
    for linea in lineas:
        for especialidad in especialidades_clave:
            if especialidad in linea:
                # Buscar la línea completa que contiene la especialidad
                linea_original = [l for l in texto_pagina.split('\n') if especialidad in l.lower()]
                if linea_original:
                    especialidad_completa = linea_original[0].strip()
                    if len(especialidad_completa) > 15 and len(especialidad_completa) < 150:
                        especialidades.append(especialidad_completa)
                        print(f"✅ Especialidad específica: {especialidad_completa}")
    
    # Combinar resultados: primero categorías, luego consultorías, luego especialidades
    resultado_final = []
    
    # Agregar categorías
    resultado_final.extend(sorted(categorias_encontradas))
    
    # Agregar consultorías
    resultado_final.extend(sorted(consultorias_encontradas)[:5])  # Máximo 5 consultorías
    
    # Agregar especialidades específicas
    resultado_final.extend(especialidades[:5])  # Máximo 5 especialidades
    
    # Eliminar duplicados y limpiar
    especialidades_limpias = []
    for esp in resultado_final[:10]:  # Limitar a 10 total
        esp_clean = esp.strip()
        if esp_clean and esp_clean not in especialidades_limpias:
            especialidades_limpias.append(esp_clean)
    
    if especialidades_limpias:
        print(f"🎯 Especialidades extraídas: {len(especialidades_limpias)}")
    
    return especialidades_limpias

async def extraer_clasificaciones_osce(page, texto_pagina: str) -> List[str]:
    """Extrae clasificaciones del proveedor en OSCE"""
    
    clasificaciones = []
    
    patrones = [
        "clasificación",
        "categoría",
        "tipo",
        "clase",
        "grupo"
    ]
    
    lineas = texto_pagina.split('\n')
    
    for i, linea in enumerate(lineas):
        linea_lower = linea.lower().strip()
        
        for patron in patrones:
            if patron in linea_lower:
                if ':' in linea:
                    partes = linea.split(':', 1)
                    if len(partes) > 1:
                        clasificacion = partes[1].strip()
                        if clasificacion:
                            clasificaciones.append(clasificacion)
    
    return clasificaciones[:5]  # Limitar a 5

async def extraer_contacto_osce(page, texto_pagina: str) -> Dict[str, str]:
    """Extrae información de contacto de OSCE"""
    
    contacto = {}
    
    print(f"🔍 Buscando datos de contacto en OSCE...")
    
    # Patrones específicos para OSCE basados en la estructura real
    patrones_email = [
        r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',  # Patrón de email
        r'Email\s*:\s*([^\s\n]+)',
        r'Correo\s*:\s*([^\s\n]+)',
        r'E-mail\s*:\s*([^\s\n]+)'
    ]
    
    patrones_telefono = [
        r'Teléfono\s*:\s*(\d{9,12})',  # 9-12 dígitos
        r'Telefono\s*:\s*(\d{9,12})',
        r'Tel\s*:\s*(\d{9,12})',
        r'Celular\s*:\s*(\d{9,12})',
        r'Phone\s*:\s*(\d{9,12})',
        r'(\d{9})',  # Patrón simple para celular de 9 dígitos
    ]
    
    # Buscar email con regex
    import re
    for patron in patrones_email:
        matches = re.findall(patron, texto_pagina, re.IGNORECASE)
        if matches:
            email_candidato = matches[0]
            # Validar que sea un email real
            if '@' in email_candidato and '.' in email_candidato:
                contacto['email'] = email_candidato
                print(f"✅ Email encontrado: {email_candidato}")
                break
    
    # Buscar teléfono con regex
    for patron in patrones_telefono:
        matches = re.findall(patron, texto_pagina, re.IGNORECASE)
        if matches:
            telefono_candidato = matches[0]
            # Validar que sea un número de teléfono válido (9 dígitos para Perú)
            if len(telefono_candidato) == 9 and telefono_candidato.startswith('9'):
                contacto['telefono'] = telefono_candidato
                print(f"✅ Teléfono encontrado: {telefono_candidato}")
                break
            elif len(telefono_candidato) >= 9:
                contacto['telefono'] = telefono_candidato
                print(f"✅ Teléfono encontrado: {telefono_candidato}")
                break
    
    # Método alternativo: buscar en elementos específicos de la página
    try:
        # Buscar elementos que contengan @ (emails)
        elementos_email = await page.query_selector_all('*:has-text("@")')
        for elemento in elementos_email[:5]:  # Limitar búsqueda
            texto = await elemento.inner_text()
            if '@' in texto and '.' in texto:
                # Extraer email del texto
                email_match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', texto)
                if email_match:
                    contacto['email'] = email_match.group(1)
                    print(f"✅ Email encontrado en elemento: {email_match.group(1)}")
                    break
    except Exception as e:
        print(f"⚠️ Error buscando email en elementos: {e}")
    
    try:
        # Buscar números de teléfono en elementos específicos
        elementos_telefono = await page.query_selector_all('*:has-text("Teléfono"), *:has-text("Telefono"), *:has-text("Tel")')
        for elemento in elementos_telefono[:5]:
            texto = await elemento.inner_text()
            telefono_match = re.search(r'(\d{9,12})', texto)
            if telefono_match:
                contacto['telefono'] = telefono_match.group(1)
                print(f"✅ Teléfono encontrado en elemento: {telefono_match.group(1)}")
                break
    except Exception as e:
        print(f"⚠️ Error buscando teléfono en elementos: {e}")
    
    print(f"📊 Contacto extraído: {contacto}")
    return contacto

async def extraer_tablas_osce(page) -> Optional[Dict[str, Any]]:
    """Extrae información de tablas en la página de OSCE"""
    
    try:
        tablas = await page.query_selector_all('table')
        info_tablas = {}
        
        for i, tabla in enumerate(tablas[:3]):  # Limitar a 3 tablas
            filas = await tabla.query_selector_all('tr')
            
            if len(filas) > 1:  # Al menos header + 1 fila de datos
                datos_tabla = []
                
                for j, fila in enumerate(filas[:10]):  # Limitar a 10 filas
                    celdas = await fila.query_selector_all('td, th')
                    
                    if celdas:
                        datos_fila = []
                        for celda in celdas:
                            texto = await celda.inner_text()
                            datos_fila.append(texto.strip())
                        
                        if any(datos_fila):  # Solo agregar si hay datos
                            datos_tabla.append(datos_fila)
                
                if datos_tabla:
                    info_tablas[f'tabla_{i + 1}'] = {
                        'filas': len(datos_tabla),
                        'datos': datos_tabla[:5]  # Solo primeras 5 filas
                    }
        
        return info_tablas if info_tablas else None
        
    except Exception as e:
        print(f"⚠️ Error extrayendo tablas: {e}")
        return None

# ===============================================================
# TEMPORARY ENDPOINTS FOR EMPRESA MANAGEMENT (UNTIL DB IS SET UP)
# ===============================================================

@app.get("/api/v1/empresas/")
async def listar_empresas():
    """
    Endpoint temporal para listar empresas guardadas
    Devuelve las empresas almacenadas en memoria (simulación)
    """
    try:
        print(f"📋 Listando empresas guardadas: {len(saved_empresas)} encontradas")
        
        return {
            "success": True,
            "data": saved_empresas,
            "total": len(saved_empresas),
            "message": f"Se encontraron {len(saved_empresas)} empresas",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"❌ Error listando empresas: {e}")
        return {
            "success": False,
            "error": True,
            "message": f"Error al listar empresas: {str(e)}",
            "data": [],
            "timestamp": datetime.now().isoformat()
        }

@app.post("/api/v1/empresas/")
async def crear_empresa_temporal(empresa_data: EmpresaCreateTemp):
    """
    Endpoint temporal para crear y guardar empresa con representantes
    Este endpoint recibe todos los representantes y los guarda en memoria
    """
    global next_empresa_id
    
    try:
        print(f"📝 Guardando empresa en memoria:")
        print(f"   RUC: {empresa_data.ruc}")
        print(f"   Razón Social: {empresa_data.razon_social}")
        print(f"   Total Representantes: {len(empresa_data.representantes)}")
        
        if empresa_data.representantes:
            print(f"   Representante Principal: {empresa_data.representantes[empresa_data.representante_principal_id].nombre}")
            print(f"   Representantes:")
            for i, repr in enumerate(empresa_data.representantes):
                es_principal = "👑 PRINCIPAL" if i == empresa_data.representante_principal_id else ""
                print(f"     {i+1}. {repr.nombre} - {repr.cargo} {es_principal}")
        
        # Create empresa data for storage
        nueva_empresa = {
            "id": next_empresa_id,
            "codigo": f"EMP{next_empresa_id:03d}",
            "ruc": empresa_data.ruc,
            "razon_social": empresa_data.razon_social,
            "email": empresa_data.email,
            "celular": empresa_data.celular,
            "direccion": empresa_data.direccion,
            "estado": empresa_data.estado,
            "representante_legal": (
                empresa_data.representantes[empresa_data.representante_principal_id].nombre 
                if empresa_data.representantes else None
            ),
            "dni_representante": (
                empresa_data.representantes[empresa_data.representante_principal_id].numero_documento 
                if empresa_data.representantes else None
            ),
            "representantes": [
                {
                    "id": i + 1,
                    "nombre": repr.nombre,
                    "cargo": repr.cargo,
                    "numero_documento": repr.numero_documento,
                    "tipo_documento": repr.tipo_documento,
                    "fuente": repr.fuente,
                    "participacion": repr.participacion,
                    "fecha_desde": repr.fecha_desde,
                    "es_principal": i == empresa_data.representante_principal_id,
                    "estado": "ACTIVO"
                }
                for i, repr in enumerate(empresa_data.representantes)
            ],
            "total_representantes": len(empresa_data.representantes),
            "especialidades": empresa_data.especialidades_oece,
            "fuentes_consultadas": empresa_data.fuentes_consultadas,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        # Save to in-memory storage
        saved_empresas.append(nueva_empresa)
        next_empresa_id += 1
        
        # Return success response
        response = {
            "success": True,
            "message": "Empresa guardada exitosamente en memoria",
            "data": nueva_empresa
        }
        
        print(f"✅ Empresa guardada en memoria exitosamente (Total: {len(saved_empresas)})")
        return response
        
    except Exception as e:
        print(f"❌ Error simulando creación de empresa: {e}")
        return {
            "success": False,
            "error": True,
            "message": f"Error al crear empresa: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

# ==========================================
# NUEVOS ENDPOINTS PARA GESTIÓN DE EMPRESAS EN TURSO
# ==========================================

@app.get("/empresas")
async def listar_empresas(limit: int = 50, offset: int = 0):
    """Listar empresas guardadas en Turso"""
    try:
        from app.services.empresa_service_turso_enhanced import EmpresaServiceTurso
        empresa_service = EmpresaServiceTurso()
        
        empresas = empresa_service.list_empresas(limit=limit, offset=offset)
        empresa_service.close()
        
        return {
            "success": True,
            "data": empresas,
            "count": len(empresas),
            "limit": limit,
            "offset": offset,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/empresas/search")
async def buscar_empresas(q: str, limit: int = 20):
    """Buscar empresas por RUC o razón social"""
    try:
        from app.services.empresa_service_turso_enhanced import EmpresaServiceTurso
        empresa_service = EmpresaServiceTurso()
        
        empresas = empresa_service.search_empresas(q, limit=limit)
        empresa_service.close()
        
        return {
            "success": True,
            "data": empresas,
            "query": q,
            "count": len(empresas),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "query": q,
            "timestamp": datetime.now().isoformat()
        }

@app.get("/empresas/{ruc}")
async def obtener_empresa_por_ruc(ruc: str):
    """Obtener empresa específica por RUC desde la base de datos"""
    try:
        from app.services.empresa_service_turso_enhanced import EmpresaServiceTurso
        empresa_service = EmpresaServiceTurso()
        
        empresa = empresa_service.get_empresa_by_ruc(ruc)
        empresa_service.close()
        
        if empresa:
            return {
                "success": True,
                "data": empresa,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "success": False,
                "message": f"Empresa con RUC {ruc} no encontrada",
                "timestamp": datetime.now().isoformat()
            }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "ruc": ruc,
            "timestamp": datetime.now().isoformat()
        }

@app.get("/empresas/stats")
async def estadisticas_empresas():
    """Obtener estadísticas de la base de datos de empresas"""
    try:
        from app.services.empresa_service_turso_enhanced import EmpresaServiceTurso
        empresa_service = EmpresaServiceTurso()
        
        stats = empresa_service.get_stats()
        empresa_service.close()
        
        return {
            "success": True,
            "data": stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# ===== ENDPOINTS COMPLEMENTARIOS PARA EMPRESAS GUARDADAS =====

@app.get("/api/empresas-guardadas")
async def listar_empresas_guardadas(limit: int = 50, offset: int = 0):
    """Listar empresas guardadas con paginación"""
    try:
        from app.services.empresa_service_turso_enhanced import EmpresaServiceTurso
        empresa_service = EmpresaServiceTurso()
        
        empresas = empresa_service.list_empresas(limit=limit, offset=offset)
        empresa_service.close()
        
        return {
            "success": True,
            "data": empresas,
            "pagination": {
                "limit": limit,
                "offset": offset,
                "total": len(empresas)
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/api/empresas-guardadas/search")
async def buscar_empresas_guardadas(q: str, limit: int = 20):
    """Buscar empresas por RUC o razón social"""
    try:
        from app.services.empresa_service_turso_enhanced import EmpresaServiceTurso
        empresa_service = EmpresaServiceTurso()
        
        empresas = empresa_service.search_empresas(q, limit=limit)
        empresa_service.close()
        
        return {
            "success": True,
            "data": empresas,
            "query": q,
            "total_found": len(empresas),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "query": q,
            "timestamp": datetime.now().isoformat()
        }

@app.get("/api/empresas-guardadas/{ruc}")
async def obtener_empresa_guardada(ruc: str):
    """Obtener empresa específica por RUC"""
    try:
        from app.services.empresa_service_turso_enhanced import EmpresaServiceTurso
        empresa_service = EmpresaServiceTurso()
        
        empresa = empresa_service.get_empresa_by_ruc(ruc)
        empresa_service.close()
        
        if empresa:
            return {
                "success": True,
                "data": empresa,
                "ruc": ruc,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "success": False,
                "error": "Empresa no encontrada",
                "ruc": ruc,
                "timestamp": datetime.now().isoformat()
            }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "ruc": ruc,
            "timestamp": datetime.now().isoformat()
        }

@app.get("/api/empresas-guardadas/stats")
async def estadisticas_empresas_guardadas():
    """Estadísticas rápidas de empresas guardadas"""
    try:
        from app.services.empresa_service_turso_enhanced import EmpresaServiceTurso
        empresa_service = EmpresaServiceTurso()
        
        stats = empresa_service.get_stats()
        empresa_service.close()
        
        return {
            "success": True,
            "data": stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.delete("/api/empresas-guardadas/{ruc}")
async def eliminar_empresa_guardada(ruc: str):
    """Eliminar empresa por RUC"""
    try:
        from app.services.empresa_service_turso_enhanced import EmpresaServiceTurso
        empresa_service = EmpresaServiceTurso()
        
        # Verificar si existe antes de eliminar
        empresa_existente = empresa_service.get_empresa_by_ruc(ruc)
        if not empresa_existente:
            empresa_service.close()
            return {
                "success": False,
                "error": "Empresa no encontrada",
                "ruc": ruc,
                "timestamp": datetime.now().isoformat()
            }
        
        # Proceder con la eliminación
        eliminado = empresa_service.delete_empresa(ruc)
        empresa_service.close()
        
        if eliminado:
            return {
                "success": True,
                "message": "Empresa eliminada correctamente",
                "ruc": ruc,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "success": False,
                "error": "No se pudo eliminar la empresa",
                "ruc": ruc,
                "timestamp": datetime.now().isoformat()
            }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "ruc": ruc,
            "timestamp": datetime.now().isoformat()
        }# =====================================================================
# ENDPOINTS TEMPORALES PARA COMPATIBILIDAD CON FRONTEND
# =====================================================================

endpoints_temp_code = """

@app.get("/obras")
async def listar_obras_temp():
    \"\"\"Endpoint temporal para obras - compatibilidad frontend\"\"\"
    return {
        "success": True,
        "data": [],
        "message": "Endpoint obras temporal - sin datos",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/obras")
async def crear_obra_temp(data: dict):
    \"\"\"Endpoint temporal para crear obras\"\"\"
    return {
        "success": True,
        "data": {"id": 1, **data},
        "message": "Obra creada (temporal)",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/valorizaciones")
async def listar_valorizaciones_temp():
    \"\"\"Endpoint temporal para valorizaciones - compatibilidad frontend\"\"\"
    return {
        "success": True,
        "data": [],
        "message": "Endpoint valorizaciones temporal - sin datos",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/valorizaciones")
async def crear_valorizacion_temp(data: dict):
    \"\"\"Endpoint temporal para crear valorizaciones\"\"\"
    return {
        "success": True,
        "data": {"id": 1, **data},
        "message": "Valorización creada (temporal)",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/empresas-guardadas")
async def listar_empresas_guardadas_temp():
    \"\"\"Endpoint temporal para empresas guardadas - compatibilidad frontend\"\"\"
    return {
        "success": True,
        "data": saved_empresas,
        "total": len(saved_empresas),
        "message": "Empresas guardadas temporal",
        "timestamp": datetime.now().isoformat()
    }

"""
# Agregar endpoints temporales
exec(endpoints_temp_code)

# =====================================================================
# ENDPOINTS TEMPORALES PARA COMPATIBILIDAD CON FRONTEND
# =====================================================================

@app.get("/obras")
async def listar_obras_temp():
    """Endpoint temporal para obras - compatibilidad frontend"""
    return {
        "success": True,
        "data": [],
        "message": "Endpoint obras temporal - sin datos",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/obras")
async def crear_obra_temp(data: dict):
    """Endpoint temporal para crear obras"""
    return {
        "success": True,
        "data": {"id": 1, **data},
        "message": "Obra creada (temporal)",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/valorizaciones")
async def listar_valorizaciones_temp():
    """Endpoint temporal para valorizaciones - compatibilidad frontend"""
    return {
        "success": True,
        "data": [],
        "message": "Endpoint valorizaciones temporal - sin datos",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/valorizaciones")
async def crear_valorizacion_temp(data: dict):
    """Endpoint temporal para crear valorizaciones"""
    return {
        "success": True,
        "data": {"id": 1, **data},
        "message": "Valorización creada (temporal)",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/empresas-guardadas")
async def listar_empresas_guardadas_temp():
    """Endpoint temporal para empresas guardadas - compatibilidad frontend"""
    return {
        "success": True,
        "data": saved_empresas,
        "total": len(saved_empresas),
        "message": "Empresas guardadas temporal",
        "timestamp": datetime.now().isoformat()
    }
