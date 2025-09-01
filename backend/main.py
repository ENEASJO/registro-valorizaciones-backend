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

# CORS básico
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Variable global para Playwright helper (lazy loading)
_playwright_helper = None

def get_playwright_helper():
    """Cargar Playwright helper solo cuando se necesite"""
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
    """Consultar RUC en SUNAT usando Playwright (carga lazy)"""
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
    """Consulta consolidada de SUNAT + OSCE - FUNCIONALIDAD COMPLETA"""
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
    """Endpoint para probar que Playwright funcione básicamente"""
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
@app.get("/api/empresas")
async def listar_empresas():
    return {
        "success": True,
        "data": [],
        "total": 0,
        "message": "Endpoint empresas temporal",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/empresas")
async def crear_empresa(data: dict):
    return {
        "success": True,
        "data": {"id": 1, **data},
        "message": "Empresa creada (temporal)",
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

@app.get("/api/empresas-guardadas")
async def empresas_guardadas():
    return {
        "success": True,
        "data": [],
        "total": 0,
        "message": "Empresas guardadas temporal",
        "timestamp": datetime.now().isoformat()
    }