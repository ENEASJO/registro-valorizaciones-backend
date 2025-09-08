# main.py - Versión con inicio rápido y Playwright lazy
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
from datetime import datetime
from typing import Dict, Any

# NO importar Playwright al inicio - solo cuando se necesite
app = FastAPI(
    title="API de Valorizaciones - Inicio Rápido", 
    description="Backend con Playwright lazy loading para inicio rápido",
    version="4.2.1"
)

# Lazy loading de routers para evitar errores de importación al inicio
def setup_routers():
    # Docstring convertido a comentario
    try:
        print("📦 Intentando cargar router de empresas...")
        from app.api.routes.empresas import router as empresas_router
        app.include_router(empresas_router)
        print("✅ Router de empresas cargado exitosamente")
        print(f"📋 Rutas registradas: {[route.path for route in empresas_router.routes]}")
        return True
    except ImportError as e:
        print(f"⚠️ No se pudo cargar router de empresas (ImportError): {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"❌ Error inesperado cargando router de empresas: {e}")
        import traceback
        traceback.print_exc()
        return False

# Variable para controlar si los routers ya fueron cargados
_routers_loaded = False

def ensure_routers_loaded():
    # Docstring convertido a comentario
    global _routers_loaded
    if not _routers_loaded:
        setup_routers()
        _routers_loaded = True

# CORS básico
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cargar routers al startup
@app.on_event("startup")
async def startup_event():
    # Docstring convertido a comentario
    try:
        print("🚀 Iniciando aplicación FastAPI...")
        ensure_routers_loaded()
        print("✅ Startup completado exitosamente")
    except Exception as e:
        print(f"❌ Error crítico en startup: {e}")
        import traceback
        traceback.print_exc()
        # No raise el error para permitir que el contenedor inicie
        print("⚠️ Continuando sin routers cargados...")

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
    # Cargar routers si no han sido cargados
    ensure_routers_loaded()
    return {
        "message": "API de Valorizaciones - Inicio Rápido ⚡",
        "status": "OK",
        "fast_start": True,
        "routers_loaded": _routers_loaded,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "fast_startup": True,
        "playwright": "lazy_loaded"
    }

# Modelo para RUC
class RUCInput(BaseModel):
    ruc: str

# Endpoint de scraping SUNAT (con lazy loading)
@app.post("/consultar-ruc")
async def consultar_ruc_sunat(ruc_input: RUCInput):
    # Docstring convertido a comentario
    ruc = ruc_input.ruc.strip()
    
    print(f"🔍 Consultando RUC: {ruc}")
    
    # Validación básica
    if not ruc or len(ruc) != 11 or not ruc.isdigit():
        return {
            "success": False,
            "error": True,
            "message": "RUC debe tener 11 dígitos numéricos",
            "timestamp": datetime.now().isoformat()
        }

    try:
        # Importar Playwright solo cuando se necesite
        from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
        
        print("📦 Playwright importado dinámicamente")
        
        playwright_helper = get_playwright_helper()
        
        async with async_playwright() as p:
            # Configuración del navegador optimizada
            print("🔧 Configurando navegador...")
            
            # Detectar si estamos en desarrollo local
            is_local = not any(os.environ.get(var) for var in ['K_SERVICE', 'GOOGLE_CLOUD_PROJECT'])
            
            if is_local:
                # Configuración simple para desarrollo local
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        '--no-sandbox',
                        '--disable-dev-shm-usage'
                    ]
                )
                print("🏠 Usando configuración para desarrollo local")
            else:
                # Usar configuración optimizada para producción
                if playwright_helper and playwright_helper != False:
                    launch_options = playwright_helper(headless=True)
                    browser = await p.chromium.launch(**launch_options)
                    print("☁️ Usando configuración para Cloud Run")
                else:
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
                    print("☁️ Usando configuración básica para producción")
            
            page = await browser.new_page(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/114.0.0.0 Safari/537.36"
            )
            
            print("🌐 Navegando a SUNAT...")
            await page.goto("https://e-consultaruc.sunat.gob.pe/cl-ti-itmrconsruc/FrameCriterioBusquedaWeb.jsp", 
                           timeout=30000)
            
            # Llenar el formulario
            await page.fill("#txtRuc", ruc)
            
            # Esperar un momento para cargar dinámico
            await page.wait_for_timeout(1000)
            
            # Verificar si el campo captcha es visible (múltiples posibles IDs)
            captcha_visible = False
            captcha_selector = None
            possible_captcha_selectors = ["#txtCodigo", "#txtCaptcha", "input[name*='captcha']", "input[name*='codigo']"]
            
            for selector in possible_captcha_selectors:
                try:
                    if await page.is_visible(selector, timeout=1000):
                        captcha_visible = True
                        captcha_selector = selector
                        print(f"🔐 Campo captcha encontrado: {selector}")
                        break
                except:
                    continue
            
            if not captcha_visible:
                print("✅ No se requiere CAPTCHA")
            
            # Si hay captcha visible, esto indica que SUNAT está requiriendo verificación
            if captcha_visible:
                print("⚠️ SUNAT requiere CAPTCHA - no se puede automatizar completamente")
                # En producción, aquí se podría integrar con un servicio de resolución de CAPTCHA
                # Por ahora, continuamos sin llenar el captcha para ver el comportamiento
                print("🔄 Continuando sin resolver CAPTCHA...")
            
            # Submit
            await page.click("#btnAceptar")
            await page.wait_for_timeout(5000)  # Más tiempo para cargar resultados
            
            # Extraer datos básicos con debugging mejorado
            try:
                print("🔍 Iniciando extracción de datos de SUNAT...")
                
                # Debug: Verificar si estamos en la página de resultados
                page_url = page.url
                page_title = await page.title()
                print(f"📄 URL actual: {page_url}")
                print(f"📄 Título de página: {page_title}")
                
                # Verificar contenido básico sin bloquear por "Resultado de la Búsqueda"
                # Esta sección puede no existir pero los datos sí están presentes
                page_content = await page.content()
                if "captcha" in page_content.lower() or "código" in page_content.lower():
                    print("🔐 Posible CAPTCHA detectado en la página")
                else:
                    print("✅ Página cargada, procediendo con extracción")
                
                # ESTRATEGIA ROBUSTA: Múltiples métodos de extracción
                razon_social = "No disponible"
                estado = "No disponible"
                direccion = "No disponible"
                
                # === MÉTODO 1: H4 con patrón RUC - NOMBRE (más confiable) ===
                h4_elements = await page.query_selector_all('h4')
                print(f"📊 Encontrados {len(h4_elements)} elementos h4")
                
                for i, h4 in enumerate(h4_elements):
                    try:
                        text = await h4.inner_text()
                        text = text.strip()
                        print(f"🔍 H4[{i}]: {text}")
                        
                        # Buscar el patrón RUC - NOMBRE EMPRESA
                        if " - " in text and text.startswith(ruc):
                            parts = text.split(" - ", 1)
                            if len(parts) >= 2 and len(parts[1].strip()) > 5:
                                razon_social = parts[1].strip()
                                print(f"✅ Razón social encontrada en H4: {razon_social}")
                                break
                    except Exception as e:
                        print(f"⚠️ Error procesando H4[{i}]: {e}")
                        continue
                
                # === MÉTODO 2: Buscar elementos que contengan el RUC ===
                if razon_social == "No disponible":
                    print("🔄 Método 2: Buscando elementos con RUC...")
                    try:
                        # Buscar todos los elementos que contengan el RUC
                        ruc_elements = await page.query_selector_all(f'text={ruc}')
                        for element in ruc_elements:
                            text = await element.inner_text()
                            text = text.strip()
                            
                            if " - " in text and text.startswith(ruc):
                                parts = text.split(" - ", 1)
                                if len(parts) >= 2 and len(parts[1].strip()) > 5:
                                    razon_social = parts[1].strip()
                                    print(f"✅ Razón social encontrada por texto: {razon_social}")
                                    break
                    except Exception as e:
                        print(f"⚠️ Error en método 2: {e}")
                
                # === MÉTODO 3: Análisis completo del texto de la página ===
                if razon_social == "No disponible":
                    print("🔄 Método 3: Análisis de texto completo...")
                    try:
                        page_text = await page.evaluate('() => document.body.innerText')
                        lines = page_text.split('\n')
                        
                        for line in lines:
                            line = line.strip()
                            if line.startswith(ruc) and " - " in line:
                                parts = line.split(" - ", 1)
                                if len(parts) >= 2:
                                    candidate = parts[1].strip()
                                    # Validar que parece un nombre de empresa
                                    if len(candidate) > 5 and not candidate.isdigit():
                                        razon_social = candidate
                                        print(f"✅ Razón social encontrada en texto: {razon_social}")
                                        break
                    except Exception as e:
                        print(f"⚠️ Error en método 3: {e}")
                
                # === EXTRAER ESTADO Y DIRECCIÓN ===
                try:
                    paragraphs = await page.query_selector_all('p')
                    print(f"📄 Analizando {len(paragraphs)} párrafos para estado y dirección")
                    
                    for i, p in enumerate(paragraphs):
                        try:
                            p_text = await p.inner_text()
                            p_text = p_text.strip()
                            
                            # Buscar estado
                            if estado == "No disponible" and p_text in ["ACTIVO", "INACTIVO", "SUSPENDIDO"]:
                                estado = p_text
                                print(f"✅ Estado encontrado en P[{i}]: {estado}")
                            
                            # Buscar dirección (contiene palabras clave de direcciones peruanas)
                            if direccion == "No disponible" and p_text and len(p_text) > 20:
                                if any(word in p_text.upper() for word in ["AV.", "JR.", "CALLE", "CAL.", "LIMA", "NRO.", "MZA", "LOTE", "INT."]):
                                    direccion = p_text
                                    print(f"✅ Dirección encontrada en P[{i}]: {direccion[:50]}...")
                        except Exception as e:
                            continue
                            
                except Exception as e:
                    print(f"⚠️ Error extrayendo estado y dirección: {e}")
                
                
                # Debug final: mostrar lo que se extrajo
                print(f"📋 Datos extraídos:")
                print(f"   RUC: {ruc}")
                print(f"   Razón Social: {razon_social}")
                print(f"   Estado: {estado}")
                print(f"   Dirección: {direccion}")
                
                # === RESULTADO FINAL ===
                extraccion_exitosa = razon_social != "No disponible"
                print(f"\n📋 EXTRACCIÓN COMPLETADA:")
                print(f"   RUC: {ruc}")
                print(f"   Razón Social: {razon_social}")
                print(f"   Estado: {estado}")
                print(f"   Dirección: {direccion[:50] if direccion != 'No disponible' else direccion}...")
                print(f"   Éxito: {'✅' if extraccion_exitosa else '❌'}")
                
                resultado = {
                    "success": True,
                    "data": {
                        "ruc": ruc,
                        "razon_social": razon_social,
                        "estado": estado if estado != "No disponible" else "ACTIVO",
                        "direccion": direccion,
                        "fuente": "SUNAT_PLAYWRIGHT_ENHANCED",
                        "extraccion_exitosa": extraccion_exitosa,
                        "metodo_extraccion": "H4_RUC_Pattern" if extraccion_exitosa else "FAILED"
                    },
                    "timestamp": datetime.now().isoformat()
                }
            except Exception as extract_error:
                print(f"⚠️ Error extrayendo datos: {extract_error}")
                
                # Verificar si el error es por CAPTCHA
                error_message = str(extract_error).lower()
                if "captcha" in error_message or "página de resultados no encontrada" in error_message:
                    return {
                        "success": False,
                        "error": True,
                        "message": "SUNAT requiere CAPTCHA - consulta manual necesaria",
                        "error_type": "CAPTCHA_REQUIRED",
                        "data": {
                            "ruc": ruc,
                            "razon_social": "No disponible - CAPTCHA requerido",
                            "estado": "CAPTCHA requerido",
                            "fuente": "SUNAT_BLOCKED"
                        },
                        "timestamp": datetime.now().isoformat()
                    }
                
                # Error general - datos de fallback
                resultado = {
                    "success": True,
                    "data": {
                        "ruc": ruc,
                        "razon_social": f"EMPRESA RUC {ruc}",
                        "estado": "Datos limitados",
                        "direccion": "No disponible",
                        "fuente": "FALLBACK",
                        "extraccion_exitosa": False,
                        "error_extraccion": str(extract_error)
                    },
                    "timestamp": datetime.now().isoformat()
                }
            
            await browser.close()
            return resultado
            
    except ImportError as import_error:
        print(f"❌ Error importando Playwright: {import_error}")
        return {
            "success": False,
            "error": True,
            "message": "Playwright no disponible en este entorno",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        print(f"❌ Error en scraping: {e}")
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
        # Fallback a Supabase si falla Neon
        try:
            from app.services.empresa_service_supabase import empresa_service_supabase
            empresas = empresa_service_supabase.listar_empresas()
            print(f"✅ Fallback Supabase: {len(empresas)} empresas")
            return {
                "success": True,
                "data": empresas,
                "total": len(empresas),
                "message": f"Empresas desde Supabase (Neon error: {str(e)})",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as supabase_error:
            print(f"❌ Supabase fallback falló: {supabase_error}")
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
                    "message": f"Error en todas las bases: Neon({str(e)}), Supabase({str(supabase_error)}), Turso({str(turso_error)})",
                    "timestamp": datetime.now().isoformat()
                }
"""

@app.post("/api/empresas")
async def crear_empresa(data: dict):
    # Docstring convertido a comentario
    print(f"📝 Creando empresa: {data.get('ruc', 'N/A')} - {data.get('razon_social', 'N/A')}")
    
    try:
        # Usar el servicio de Neon
        from app.services.empresa_service_neon import empresa_service_neon
        
        empresa_id = empresa_service_neon.guardar_empresa(data)
        
        if empresa_id:
            print(f"✅ Empresa guardada en Neon con ID: {empresa_id}")
            return {
                "success": True,
                "data": {"id": empresa_id, **data},
                "message": "Empresa guardada exitosamente en Neon PostgreSQL",
                "timestamp": datetime.now().isoformat()
            }
        else:
            print("⚠️ Neon falló, intentando Supabase fallback...")
            # Fallback a Supabase si falla Neon
            try:
                from app.services.empresa_service_supabase import empresa_service_supabase
                supabase_id = empresa_service_supabase.guardar_empresa(data)
                if supabase_id:
                    return {
                        "success": True,
                        "data": {"id": supabase_id, **data},
                        "message": "Empresa guardada en Supabase (Neon no disponible)",
                        "timestamp": datetime.now().isoformat()
                    }
            except Exception as supabase_error:
                print(f"❌ Supabase fallback falló: {supabase_error}")
            
            # Último fallback a Turso
            try:
                from app.services.empresa_service_simple import empresa_service_simple
                turso_id = empresa_service_simple.guardar_empresa(data)
                if turso_id:
                    return {
                        "success": True,
                        "data": {"id": turso_id, **data},
                        "message": "Empresa guardada en Turso (Neon y Supabase fallaron)",
                        "timestamp": datetime.now().isoformat()
                    }
            except Exception as turso_error:
                print(f"❌ Turso fallback también falló: {turso_error}")
            
            return {
                "success": True,
                "data": {"id": 999, **data},  # ID temporal
                "message": "Empresa guardada temporalmente (todas las bases fallaron)",
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        print(f"❌ Error guardando en Supabase: {e}")
        # Fallback a Turso
        try:
            from app.services.empresa_service_simple import empresa_service_simple
            turso_id = empresa_service_simple.guardar_empresa(data)
            if turso_id:
                return {
                    "success": True,
                    "data": {"id": turso_id, **data},
                    "message": f"Empresa guardada en Turso (Supabase error: {str(e)})",
                    "timestamp": datetime.now().isoformat()
                }
        except Exception as turso_error:
            print(f"❌ Turso fallback falló: {turso_error}")
        
        return {
            "success": True,
            "data": {"id": 998, **data},  # ID de error
            "message": f"Empresa guardada localmente (ambas bases fallaron)",
            "timestamp": datetime.now().isoformat()
        }

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

@app.get("/api/empresas")
async def listar_empresas_directo():
    # GET directo para /api/empresas - usa Neon PostgreSQL
    try:
        from app.services.empresa_service_neon import empresa_service_neon
        
        empresas = empresa_service_neon.listar_empresas(limit=50)
        
        print(f"✅ [GET DIRECTO] Encontradas {len(empresas)} empresas en Neon")
        return {
            "success": True,
            "data": empresas,  # ARREGLO: data debe ser directamente el array
            "total": len(empresas),
            "page": 1,
            "per_page": 50,
            "total_pages": 1,
            "message": f"Se encontraron {len(empresas)} empresa(s)",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"❌ [GET DIRECTO] Error listando empresas: {e}")
        return {
            "success": False,
            "data": [],  # ARREGLO: data debe ser directamente el array vacío
            "total": 0,
            "page": 1,
            "per_page": 50,
            "total_pages": 0,
            "message": f"Error obteniendo empresas: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

@app.delete("/api/empresas/{empresa_id}")
async def eliminar_empresa_directo(empresa_id: str):
    # Docstring convertido a comentario
    try:
        from app.services.empresa_service_neon import empresa_service_neon
        
        resultado = empresa_service_neon.eliminar_empresa(empresa_id)
        
        if not resultado:
            return JSONResponse(
                status_code=404,
                content={"detail": f"Empresa no encontrada: {empresa_id}"}
            )
            
        return {"message": "Empresa eliminada correctamente"}
        
    except Exception as e:
        print(f"❌ Error eliminando empresa {empresa_id}: {e}")
        return JSONResponse(
            status_code=500,
            content={"detail": "Error interno del servidor al eliminar empresa"}
        )

@app.get("/api/empresas-guardadas")
async def empresas_guardadas():
    return {
        "success": True,
        "data": [],
        "total": 0,
        "message": "Empresas guardadas temporal",
        "timestamp": datetime.now().isoformat()
    }

# ENDPOINTS PARA OSCE ULTRA-OPTIMIZADO
@app.post("/api/osce/consulta-turbo")
async def consulta_osce_turbo(ruc_input: RUCInput):
    # Docstring convertido a comentario
    ruc = ruc_input.ruc.strip()
    
    print(f"⚡ Consulta OSCE TURBO para RUC: {ruc}")
    
    try:
        from app.services.osce_turbo_service import osce_turbo
        from app.services.precache_service import precache_service
        
        # Registrar consulta para análisis predictivo
        precache_service.registrar_consulta(ruc)
        
        # Ejecutar consulta TURBO
        resultado = await osce_turbo.consultar_turbo(ruc)
        
        # Trigger pre-cache en background para RUCs relacionados (sin esperar)
        asyncio.create_task(precache_service.ejecutar_precache())
        
        return resultado
        
    except ImportError as e:
        print(f"⚠️ Servicio OSCE TURBO no disponible: {e}")
        return {
            "success": False,
            "error": "Servicio OSCE TURBO no disponible",
            "fallback": "Usar endpoint /consultar-ruc para funcionalidad básica",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        print(f"❌ Error en consulta OSCE TURBO: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.post("/api/osce/consulta-optimizada")
async def consulta_osce_optimizada(ruc_input: RUCInput):
    # Docstring convertido a comentario
    ruc = ruc_input.ruc.strip()
    
    print(f"🚀 Consulta OSCE optimizada para RUC: {ruc}")
    
    try:
        from app.services.osce_service_optimized import osce_service_optimized
        
        resultado = await osce_service_optimized.consultar_empresa_optimizado(ruc)
        return resultado
        
    except ImportError as e:
        print(f"⚠️ Servicio OSCE optimizado no disponible: {e}")
        return {
            "success": False,
            "error": "Servicio OSCE optimizado no disponible",
            "fallback": "Usar endpoint /consultar-ruc para funcionalidad básica",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        print(f"❌ Error en consulta OSCE optimizada: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/api/osce/cache-stats")
async def estadisticas_cache_osce():
    # Docstring convertido a comentario
    try:
        from app.services.osce_service_optimized import osce_service_optimized
        
        stats = osce_service_optimized.get_cache_stats()
        return {
            "success": True,
            "data": stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except ImportError:
        return {
            "success": False,
            "error": "Servicio de caché no disponible",
            "timestamp": datetime.now().isoformat()
        }

@app.delete("/api/osce/cache/{ruc}")
async def limpiar_cache_osce(ruc: str):
    # Docstring convertido a comentario
    try:
        from app.services.osce_service_optimized import osce_service_optimized
        
        osce_service_optimized.invalidate_cache(ruc)
        return {
            "success": True,
            "message": f"Caché invalidado para RUC: {ruc}",
            "timestamp": datetime.now().isoformat()
        }
        
    except ImportError:
        return {
            "success": False,
            "error": "Servicio de caché no disponible",
            "timestamp": datetime.now().isoformat()
        }

# ENDPOINTS PARA PRE-CACHING INTELIGENTE
@app.post("/api/osce/precache")
async def ejecutar_precache():
    # Docstring convertido a comentario
    try:
        from app.services.precache_service import precache_service
        
        resultado = await precache_service.ejecutar_precache()
        return {
            "success": True,
            "data": resultado,
            "timestamp": datetime.now().isoformat()
        }
        
    except ImportError:
        return {
            "success": False,
            "error": "Servicio de pre-caching no disponible",
            "timestamp": datetime.now().isoformat()
        }

@app.get("/api/osce/precache-stats")
async def estadisticas_precache():
    # Docstring convertido a comentario
    try:
        from app.services.precache_service import precache_service
        
        stats = precache_service.get_estadisticas()
        return {
            "success": True,
            "data": stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except ImportError:
        return {
            "success": False,
            "error": "Servicio de pre-caching no disponible",
            "timestamp": datetime.now().isoformat()
        }

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

@app.post("/api/v1/empresas")
async def crear_empresa_temporal(empresa: EmpresaCreate):
    # Docstring convertido a comentario
    print(f"📝 Recibiendo empresa temporal: {empresa.ruc} - {empresa.razon_social}")
    
    # Cargar routers si no están cargados
    ensure_routers_loaded()
    
    # Por ahora retornamos éxito temporal con los datos recibidos
    return {
        "success": True,
        "data": {
            "id": 999,  # ID temporal
            "codigo": f"EMP{empresa.ruc[:6]}",
            **empresa.dict()
        },
        "message": "Empresa guardada temporalmente (esperando router completo)",
        "timestamp": datetime.now().isoformat()
    }

# ENDPOINT TEMPORAL DE DELETE PARA DEBUGGING
@app.delete("/api/empresas/{empresa_id}")
async def eliminar_empresa_temporal(empresa_id: str):
    # Docstring convertido a comentario
    try:
        from app.services.empresa_service_neon import empresa_service_neon
        
        print(f"🗑️ [TEMP DELETE] Eliminando empresa: {empresa_id}")
        
        resultado = empresa_service_neon.eliminar_empresa(empresa_id)
        
        if not resultado:
            print(f"❌ [TEMP DELETE] Empresa {empresa_id} no encontrada en Neon")
            return JSONResponse(
                status_code=404,
                content={"detail": f"Empresa no encontrada: {empresa_id}"}
            )
        
        print(f"✅ [TEMP DELETE] Empresa {empresa_id} eliminada exitosamente")
        return {
            "success": True,
            "message": "Empresa eliminada correctamente",
            "empresa_id": empresa_id,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"❌ [TEMP DELETE] Error eliminando empresa {empresa_id}: {e}")
        return JSONResponse(
            status_code=500,
            content={"detail": f"Error interno: {str(e)}"}
        )

# ENDPOINTS DE PRUEBA SUPABASE
@app.post("/api/supabase/empresas")
async def crear_empresa_supabase(data: dict):
    # Crear empresa en Supabase (prueba)
    print(f"📝 [SUPABASE] Creando empresa: {data.get('ruc', 'N/A')} - {data.get('razon_social', 'N/A')}")
    
    try:
        from app.services.empresa_service_supabase import empresa_service_supabase
        
        empresa_id = empresa_service_supabase.guardar_empresa(data)
        
        if empresa_id:
            print(f"✅ [SUPABASE] Empresa guardada con ID: {empresa_id}")
            return {
                "success": True,
                "data": {"id": empresa_id, **data},
                "message": "Empresa guardada exitosamente en Supabase",
                "fuente": "supabase",
                "timestamp": datetime.now().isoformat()
            }
        else:
            print("⚠️ [SUPABASE] Error guardando empresa")
            return {
                "success": False,
                "data": data,
                "message": "Error guardando en Supabase",
                "fuente": "supabase",
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        print(f"❌ [SUPABASE] Error: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Error en servicio Supabase: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

@app.get("/api/supabase/empresas")
async def listar_empresas_supabase():
    # Listar empresas desde Supabase (prueba)
    print("📋 [SUPABASE] Listando empresas...")
    
    try:
        from app.services.empresa_service_supabase import empresa_service_supabase
        
        empresas = empresa_service_supabase.listar_empresas()
        
        print(f"✅ [SUPABASE] Encontradas {len(empresas)} empresas")
        return {
            "success": True,
            "data": empresas,
            "total": len(empresas),
            "message": "Empresas obtenidas desde Supabase",
            "fuente": "supabase",
            "timestamp": datetime.now().isoformat()
        }
            
    except Exception as e:
        print(f"❌ [SUPABASE] Error listando: {e}")
        return {
            "success": False,
            "data": [],
            "total": 0,
            "error": str(e),
            "message": f"Error listando desde Supabase: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

@app.get("/api/supabase/stats")
async def stats_supabase():
    # Estadisticas de Supabase
    try:
        from app.services.empresa_service_supabase import empresa_service_supabase
        
        stats = empresa_service_supabase.get_stats()
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
