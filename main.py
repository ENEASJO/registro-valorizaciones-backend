# main.py - Versión con inicio rápido y Playwright lazy
from fastapi import FastAPI, Request
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import random
from datetime import datetime
from typing import Dict, Any

# NO importar Playwright al inicio - solo cuando se necesite
app = FastAPI(
    title="API de Valorizaciones - Inicio Rápido", 
    description="Backend con Playwright lazy loading para inicio rápido",
    version="4.2.1"
)

# Cargar router de empresas completo
try:
    print("📦 Cargando router de empresas completo...")
    from app.api.routes.empresas import router as empresas_router
    app.include_router(empresas_router)
    print("✅ Router de empresas completo cargado exitosamente")
except Exception as e:
    print(f"❌ Error cargando router de empresas completo: {e}")
    import traceback
    traceback.print_exc()

# Cargar router de debug
try:
    print("📦 Cargando router de debug...")
    from app.api.routes.debug_logs import router as debug_router
    app.include_router(debug_router, prefix="/api")
    print("✅ Router de debug cargado exitosamente")
except Exception as e:
    print(f"❌ Error cargando router de debug: {e}")
    import traceback
    traceback.print_exc()

# Cargar router de ubicaciones (San Marcos)
try:
    print("📦 Cargando router de ubicaciones...")
    from app.api.routes.ubicaciones import router as ubicaciones_router
    app.include_router(ubicaciones_router)
    print("✅ Router de ubicaciones cargado exitosamente")
except Exception as e:
    print(f"⚠️ No se pudo cargar router de ubicaciones: {e}")
    import traceback
    traceback.print_exc()

# Cargar router de debug para empresas
try:
    print("📦 Cargando router de debug de empresas...")
    from app.api.routes.debug_empresa import router as debug_empresa_router
    app.include_router(debug_empresa_router)
    print("✅ Router de debug de empresas cargado exitosamente")
except Exception as e:
    print(f"❌ Error cargando router de debug de empresas: {e}")
    import traceback
    traceback.print_exc()

# Middleware para manejar headers de proxy (Cloud Run) - DEBE ESTAR ANTES DE CORS
# Temporalmente desactivado para solucionar error 500
enable_proxy_middleware = os.environ.get('ENABLE_PROXY_MIDDLEWARE', 'true').lower() == 'true'
if enable_proxy_middleware:
    try:
        from app.middleware.proxy_headers import ProxyHeadersMiddleware
        app.add_middleware(ProxyHeadersMiddleware)
        print("✅ Proxy headers middleware configurado para Cloud Run")
    except Exception as e:
        print(f"⚠️ No se pudo cargar middleware de proxy headers: {e}")
else:
    print("ℹ️ Proxy headers middleware deshabilitado")

# CORS básico - DEBE ESTAR DESPUÉS DEL MIDDLEWARE DE PROXY
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Evento de startup
@app.on_event("startup")
async def startup_event():
    # Docstring convertido a comentario
    try:
        print("🚀 Iniciando aplicación FastAPI...")
        print("✅ Startup completado exitosamente")
    except Exception as e:
        print(f"❌ Error crítico en startup: {e}")
        import traceback
        traceback.print_exc()

# Variable global para Playwright helper (lazy loading)
_playwright_helper = None

def get_playwright_helper():
    # Docstring convertido a comentario
    global _playwright_helper
    if _playwright_helper is None:
        try:
            from app.utils.playwright_helper import get_browser_launch_options
            _playwright_helper = get_browser_launch_options
            print("🌐 Playwright helper cargado dinámicamente")
        except ImportError:
            _playwright_helper = False
            print("⚠️ Playwright helper no disponible")
    return _playwright_helper

# Endpoints que arrancan inmediatamente
@app.get("/")
async def root():
    return {
        "message": "API de Valorizaciones - Inicio Rápido ⚡",
        "status": "OK",
        "fast_start": True,
        "routers_loaded": True,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "fast_startup": True,
        "playwright": "lazy_loaded"
    }

@app.get("/debug/headers")
async def debug_headers(request: Request):
    """Debug endpoint to check headers and proxy handling"""
    return {
        "url": str(request.url),
        "scheme": request.url.scheme,
        "headers": dict(request.headers),
        "client": {
            "host": request.client.host if request.client else None,
            "port": request.client.port if request.client else None
        },
        "scope_scheme": request.scope.get("scheme"),
        "proxy_handled": request.headers.get("x-proxy-handled") == "true"
    }

# Modelo para RUC
class RUCInput(BaseModel):
    ruc: str

# Endpoint de scraping SUNAT (con lazy loading)
@app.post("/consultar-ruc")
async def consultar_ruc_sunat(ruc_input: RUCInput):
    """Endpoint para consultar RUC usando el servicio SUNAT mejorado"""
    print(f"🔍 [IMPROVED] Consultando RUC: {ruc_input.ruc}")

    # Validación básica
    ruc = ruc_input.ruc.strip()
    if not ruc or len(ruc) != 11 or not ruc.isdigit():
        return {
            "success": False,
            "error": True,
            "message": "RUC inválido. Debe tener 11 dígitos",
            "timestamp": datetime.now().isoformat()
        }

    try:
        # Usar el servicio mejorado
        from app.services.sunat_service_improved import sunat_service_improved

        # Consultar usando el servicio mejorado
        empresa_info = await sunat_service_improved.consultar_empresa_completa(ruc)

        # Convertir a formato de respuesta
        return {
            "success": True,
            "data": {
                "ruc": empresa_info.ruc,
                "razon_social": empresa_info.razon_social,
                "estado": empresa_info.estado,
                "direccion": empresa_info.domicilio_fiscal,
                "representantes": [
                    {
                        "nombre": rep.nombre,
                        "cargo": rep.cargo,
                        "tipo_doc": rep.tipo_doc,
                        "numero_doc": rep.numero_doc,
                        "fecha_desde": rep.fecha_desde
                    }
                    for rep in empresa_info.representantes
                ],
                "total_representantes": empresa_info.total_representantes,
                "fuente": "SUNAT_IMPROVED",
                "extraccion_exitosa": True
            },
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        print(f"❌ Error en consulta SUNAT mejorada: {e}")
        return {
            "success": False,
            "error": True,
            "message": f"Error consultando SUNAT: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

# Endpoint GET consolidado SUNAT + OSCE (funcionalidad completa restaurada)
@app.get("/consulta-ruc-consolidada/{ruc}")
async def consultar_ruc_consolidado(ruc: str):
    # Docstring convertido a comentario
    print(f"🔍 Iniciando consulta consolidada para RUC: {ruc}")
    
    # Validación básica
    if not ruc or len(ruc) != 11 or not ruc.isdigit():
        return {
            "success": False,
            "error": True,
            "message": "RUC debe tener 11 dígitos numéricos",
            "timestamp": datetime.now().isoformat()
        }
    
    try:
        # Importar el servicio de consolidación dinámicamente
        from app.services.consolidation_service import ConsolidationService
        
        print("📦 Servicio de consolidación importado dinámicamente")
        
        # Crear instancia del servicio
        consolidation_service = ConsolidationService()
        
        # Consultar datos consolidados
        resultado_consolidado = await consolidation_service.consultar_consolidado(ruc)
        
        print("✅ Consulta consolidada completada exitosamente")
        
        # If SUNAT data is missing from consolidation, use fallback
        if not resultado_consolidado.razon_social or not resultado_consolidado.fuentes_consultadas or "SUNAT" not in resultado_consolidado.fuentes_consultadas:
            print("🔄 SUNAT data missing from consolidation, using fallback...")
            try:
                # Get SUNAT data directly
                ruc_input = RUCInput(ruc=ruc)
                resultado_sunat = await consultar_ruc_sunat(ruc_input)
                
                if resultado_sunat.get("success") and "data" in resultado_sunat:
                    sunat_data = resultado_sunat["data"]
                    # Merge SUNAT data with consolidation result
                    return {
                        "success": True,
                        "data": {
                            "ruc": ruc,
                            "razon_social": sunat_data.get("razon_social", resultado_consolidado.razon_social),
                            "estado": sunat_data.get("estado", resultado_consolidado.registro.estado_sunat if resultado_consolidado.registro else "ACTIVO"),
                            "direccion": sunat_data.get("direccion", resultado_consolidado.contacto.direccion if resultado_consolidado.contacto else ""),
                            "departamento": resultado_consolidado.contacto.departamento if resultado_consolidado.contacto else "",
                            "provincia": resultado_consolidado.contacto.ciudad if resultado_consolidado.contacto else "",
                            "distrito": "",
                            "fuentes": list(set((resultado_consolidado.fuentes_consultadas or []) + ["SUNAT"])),
                            "representantes": [
                                {
                                    "nombre": miembro.nombre,
                                    "cargo": miembro.cargo,
                                    "documento": miembro.numero_documento,
                                    "fuente": miembro.fuente
                                } for miembro in resultado_consolidado.miembros
                            ] if resultado_consolidado.miembros else [],
                            "contactos": [
                                {
                                    "telefono": resultado_consolidado.contacto.telefono if resultado_consolidado.contacto else "",
                                    "email": resultado_consolidado.contacto.email if resultado_consolidado.contacto else "",
                                    "fuente": "CONSOLIDADO"
                                }
                            ] if resultado_consolidado.contacto and (resultado_consolidado.contacto.telefono or resultado_consolidado.contacto.email) else [],
                            "consolidacion_exitosa": True,
                            "fuente": "CONSOLIDADO_SUNAT_OSCE_ENHANCED"
                        },
                        "timestamp": datetime.now().isoformat()
                    }
            except Exception as fallback_error:
                print(f"⚠️ Fallback SUNAT también falló: {fallback_error}")
        
        # Return original consolidation result
        return {
            "success": True,
            "data": {
                "ruc": resultado_consolidado.ruc,
                "razon_social": resultado_consolidado.razon_social,
                "estado": resultado_consolidado.registro.estado_sunat if resultado_consolidado.registro else "No disponible",
                "direccion": resultado_consolidado.contacto.direccion if resultado_consolidado.contacto else "",
                "departamento": resultado_consolidado.contacto.departamento if resultado_consolidado.contacto else "",
                "provincia": resultado_consolidado.contacto.ciudad if resultado_consolidado.contacto else "",
                "distrito": "",
                "fuentes": resultado_consolidado.fuentes_consultadas,
                "representantes": [
                    {
                        "nombre": miembro.nombre,
                        "cargo": miembro.cargo,
                        "documento": miembro.numero_documento,
                        "fuente": miembro.fuente
                    } for miembro in resultado_consolidado.miembros
                ] if resultado_consolidado.miembros else [],
                "contactos": [
                    {
                        "telefono": resultado_consolidado.contacto.telefono if resultado_consolidado.contacto else "",
                        "email": resultado_consolidado.contacto.email if resultado_consolidado.contacto else "",
                        "fuente": "CONSOLIDADO"
                    }
                ] if resultado_consolidado.contacto and (resultado_consolidado.contacto.telefono or resultado_consolidado.contacto.email) else [],
                "consolidacion_exitosa": True,
                "fuente": "CONSOLIDADO_SUNAT_OSCE"
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except ImportError as import_error:
        print(f"⚠️ Error importando servicio de consolidación: {import_error}")
        # Fallback al endpoint SUNAT simple si no está disponible la consolidación
        ruc_input = RUCInput(ruc=ruc)
        resultado_simple = await consultar_ruc_sunat(ruc_input)
        resultado_simple["data"]["fuente"] = "SUNAT_FALLBACK"
        return resultado_simple
        
    except Exception as e:
        print(f"❌ Error en consulta consolidada: {e}")
        return {
            "success": False,
            "error": True,
            "message": f"Error en consulta consolidada: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

# Test de Playwright (lazy loading)
@app.get("/debug/playwright-test")
async def test_playwright():
    # Docstring convertido a comentario
    try:
        from playwright.async_api import async_playwright
        print("📦 Playwright importado para test")
        
        playwright_helper = get_playwright_helper()
        
        async with async_playwright() as p:
            if playwright_helper and playwright_helper != False:
                launch_options = playwright_helper(headless=True)
                browser = await p.chromium.launch(**launch_options)
            else:
                browser = await p.chromium.launch(headless=True)
            
            page = await browser.new_page()
            await page.goto("data:text/html,<html><body><h1>Playwright Test OK</h1></body></html>")
            title = await page.title()
            await browser.close()
            
            return {
                "success": True,
                "message": "Playwright funciona correctamente",
                "test_result": f"Title: {title}",
                "lazy_loading": True,
                "timestamp": datetime.now().isoformat()
            }
    except ImportError as import_error:
        return {
            "success": False,
            "error": True,
            "message": f"Playwright no disponible: {import_error}",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "success": False,
            "error": True,
            "message": f"Error en Playwright: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

# Endpoints básicos necesarios para el frontend (arrancan inmediatamente)
# NOTA: Estos endpoints están comentados porque ahora el router de empresas maneja estas rutas
"""
@app.get("/api/empresas")
async def listar_empresas():
    # Listar empresas desde Neon PostgreSQL
    print("📋 Listando empresas desde Neon...")
    
    try:
        from app.services.empresa_service_neon import empresa_service_neon
        
        empresas = empresa_service_neon.listar_empresas()
        
        print(f"✅ Encontradas {len(empresas)} empresas en Neon")
        return {
            "success": True,
            "data": empresas,
            "total": len(empresas),
            "message": "Empresas obtenidas desde Neon PostgreSQL",
            "timestamp": datetime.now().isoformat()
        }
            
    except Exception as e:
        print(f"❌ Error listando desde Neon: {e}")
        # # Fallback a Supabase si falla Neon - DESHABILITADO
        # try:
        #     print(f"✅ Fallback Supabase: {len(empresas)} empresas")
        #     return {
        #         "success": True,
        #         "data": empresas,
        #         "total": len(empresas),
        #         "message": f"Empresas desde Supabase (Neon error: {str(e)})",
        #         "timestamp": datetime.now().isoformat()
        #     }
            # Último fallback a Turso
            try:
                from app.services.empresa_service_simple import empresa_service_simple
                empresas = empresa_service_simple.listar_empresas()
                print(f"✅ Fallback Turso final: {len(empresas)} empresas")
                return {
                    "success": True,
                    "data": empresas,
                    "total": len(empresas),
                    "message": f"Empresas desde Turso (Neon y Supabase fallaron)",
                    "timestamp": datetime.now().isoformat()
                }
            except Exception as turso_error:
                print(f"❌ Todos los fallbacks fallaron: {turso_error}")
                return {
                    "success": True,
                    "data": [],
                    "total": 0,
                    "timestamp": datetime.now().isoformat()
                }
"""


@app.get("/obras")
async def listar_obras():
    return {
        "success": True,
        "data": [],
        "message": "Endpoint obras temporal",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/obras")
async def crear_obra(data: dict):
    return {
        "success": True,
        "data": {"id": 1, **data},
        "message": "Obra creada (temporal)",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/valorizaciones")
async def listar_valorizaciones():
    return {
        "success": True,
        "data": [],
        "message": "Endpoint valorizaciones temporal",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/valorizaciones")
async def crear_valorizacion(data: dict):
    return {
        "success": True,
        "data": {"id": 1, **data},
        "message": "Valorización creada (temporal)",
        "timestamp": datetime.now().isoformat()
    }


# ELIMINADO: Endpoint DELETE duplicado para evitar conflictos con el router

@app.get("/api/empresas-guardadas")
async def empresas_guardadas():
    return {
        "success": True,
        "data": [],
        "total": 0,
        "message": "Empresas guardadas temporal",
        "timestamp": datetime.now().isoformat()
    }

# ELIMINADO: Endpoints experimentales de OSCE (turbo, optimizado, cache, precache)
# Usar solo: /consultar-ruc-consolidada/{ruc} para funcionalidad completa

# Endpoint temporal para empresas mientras se activa el router
class EmpresaCreate(BaseModel):
    ruc: str
    razon_social: str
    dni: str = None
    tipo_empresa: str
    email: str = None
    telefono: str = None
    direccion: str = None
    representante_legal: str = None
    estado: str = "ACTIVO"


# ELIMINADO: Endpoint DELETE temporal duplicado - usar solo el del router

# ENDPOINT DE PRUEBA: Consolidación con representantes mejorada
@app.post("/api/test/consolidacion-mejorada")
async def test_consolidacion_mejorada(ruc_input: RUCInput):
    """Endpoint de prueba para la consolidación mejorada con representantes"""
    ruc = ruc_input.ruc.strip()
    
    print(f"🧪 TESTING: Consolidación mejorada para RUC: {ruc}")
    
    try:
        from app.services.consolidation_service import consolidation_service
        
        # Probar la consolidación mejorada
        resultado_consolidado = await consolidation_service.consultar_consolidado(ruc)
        
        # Convertir a diccionario para respuesta
        return {
            "success": True,
            "data": {
                "ruc": resultado_consolidado.ruc,
                "razon_social": resultado_consolidado.razon_social,
                "estado": resultado_consolidado.registro.estado_sunat if resultado_consolidado.registro else "No disponible",
                "fuentes_consultadas": resultado_consolidado.fuentes_consultadas,
                "fuentes_con_errores": resultado_consolidado.fuentes_con_errores,
                "consolidacion_exitosa": resultado_consolidado.consolidacion_exitosa,
                "total_miembros": len(resultado_consolidado.miembros),
                "miembros_detalle": [
                    {
                        "nombre": miembro.nombre,
                        "cargo": miembro.cargo,
                        "documento": miembro.numero_documento,
                        "tipo_documento": miembro.tipo_documento,
                        "fuente": miembro.fuente,
                        "participacion": miembro.participacion,
                        "fecha_desde": miembro.fecha_desde,
                        "detalles_matching": miembro.fuentes_detalle if hasattr(miembro, 'fuentes_detalle') else None
                    } for miembro in resultado_consolidado.miembros
                ],
                "contacto": {
                    "domicilio_fiscal": resultado_consolidado.contacto.domicilio_fiscal if resultado_consolidado.contacto else "",
                    "telefono": resultado_consolidado.contacto.telefono if resultado_consolidado.contacto else "",
                    "email": resultado_consolidado.contacto.email if resultado_consolidado.contacto else "",
                    "direccion": resultado_consolidado.contacto.direccion if resultado_consolidado.contacto else "",
                    "ciudad": resultado_consolidado.contacto.ciudad if resultado_consolidado.contacto else "",
                    "departamento": resultado_consolidado.contacto.departamento if resultado_consolidado.contacto else ""
                },
                "especialidades": resultado_consolidado.especialidades,
                "capacidad_contratacion": resultado_consolidado.capacidad_contratacion,
                "vigencia": resultado_consolidado.vigencia,
                "observaciones": resultado_consolidado.observaciones
            },
            "mensaje": f"Consolidación completada exitosamente - {len(resultado_consolidado.miembros)} miembros únicos",
            "timestamp": datetime.now().isoformat()
        }
        
    except ImportError as e:
        print(f"⚠️ Error importando servicio de consolidación: {e}")
        return {
            "success": False,
            "error": "Servicio de consolidación no disponible",
            "message": f"ImportError: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        print(f"❌ Error en consolidación mejorada: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Error en consolidación: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

# # ENDPOINTS DE PRUEBA SUPABASE - DESHABILITADOS
#     # Crear empresa en Supabase (prueba)
#     print(f"📝 [SUPABASE] Creando empresa: {data.get('ruc', 'N/A')} - {data.get('razon_social', 'N/A')}")
#     
#     try:
#         
#         
#         if empresa_id:
#             print(f"✅ [SUPABASE] Empresa guardada con ID: {empresa_id}")
#             return {
#                 "success": True,
#                 "data": {"id": empresa_id, **data},
#                 "message": "Empresa guardada exitosamente en Supabase",
#                 "timestamp": datetime.now().isoformat()
#             }
#         else:
#             print("⚠️ [SUPABASE] Error guardando empresa")
#             return {
#                 "success": False,
#                 "data": data,
#                 "message": "Error guardando en Supabase",
#                 "timestamp": datetime.now().isoformat()
#             }
#             
#     except Exception as e:
#         print(f"❌ [SUPABASE] Error: {e}")
#         return {
#             "success": False,
#             "error": str(e),
#             "message": f"Error en servicio Supabase: {str(e)}",
#             "timestamp": datetime.now().isoformat()
#         }
# 
#     # Listar empresas desde Supabase (prueba)
#     print("📋 [SUPABASE] Listando empresas...")
#     
#     try:
#         
#         
#         print(f"✅ [SUPABASE] Encontradas {len(empresas)} empresas")
#         return {
#             "success": True,
#             "data": empresas,
#             "total": len(empresas),
#             "message": "Empresas obtenidas desde Supabase",
#             "timestamp": datetime.now().isoformat()
#         }
#             
#     except Exception as e:
#         print(f"❌ [SUPABASE] Error listando: {e}")
#         return {
#             "success": False,
#             "data": [],
#             "total": 0,
#             "error": str(e),
#             "message": f"Error listando desde Supabase: {str(e)}",
#             "timestamp": datetime.now().isoformat()
#         }
# 
#     # Estadisticas de Supabase
#     try:
#         
#         return {
#             "success": True,
#             "data": stats,
#             "timestamp": datetime.now().isoformat()
#         }
#     except Exception as e:
#         return {
#             "success": False,
#             "error": str(e),
#             "timestamp": datetime.now().isoformat()
#         }

# Endpoint temporal para ejecutar esquema SQL (eliminar después de usar)
@app.post("/ejecutar-esquema-temporal")
async def ejecutar_esquema_temporal():
    """Endpoint temporal para ejecutar el esquema SQL de Neon"""
    try:
        from app.services.empresa_service_neon import empresa_service_neon
        
        # Leer el esquema SQL
        import os
        schema_path = os.path.join(os.path.dirname(__file__), 'sql', 'empresas_schema.sql')
        
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        
        # Dividir el esquema en instrucciones individuales
        statements = [stmt.strip() for stmt in schema_sql.split(';') if stmt.strip() and not stmt.strip().startswith('--')]
        
        # Ejecutar cada instrucción
        resultados = []
        for i, statement in enumerate(statements):
            try:
                # Usar el servicio de Neon para ejecutar la instrucción
                # Esto es un workaround - normalmente usaríamos execute_raw directamente
                result = empresa_service_neon._execute_query(statement + ';')
                resultados.append(f"✅ Instrucción {i+1}: Ejecutada correctamente")
            except Exception as e:
                resultados.append(f"⚠️  Instrucción {i+1}: {str(e)}")
        
        return {
            "success": True,
            "message": "Esquema ejecutado (parcialmente)",
            "resultados": resultados,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Error ejecutando esquema: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }
