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
    version="3.5.0"
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
            # Configuración del navegador
            if playwright_helper and playwright_helper != False:
                launch_options = playwright_helper(headless=True)
                browser = await p.chromium.launch(**launch_options)
            else:
                # Configuración básica para Cloud Run
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
            
            # Verificar si el campo captcha es visible (cambió de #txtCaptcha a #txtCodigo)
            captcha_visible = False
            try:
                captcha_visible = await page.is_visible("#txtCodigo", timeout=2000)
                print(f"🔐 Campo captcha visible: {captcha_visible}")
            except:
                print("⚠️ No se pudo verificar visibilidad del captcha")
            
            # Llenar captcha solo si está visible
            if captcha_visible:
                await page.fill("#txtCodigo", "")  # Captcha vacío (necesitarías resolver captcha real)
                print("🔐 Campo captcha llenado")
            
            # Submit
            await page.click("#btnAceptar")
            await page.wait_for_timeout(5000)  # Más tiempo para cargar resultados
            
            # Extraer datos básicos
            try:
                # Múltiples selectores para obtener la razón social
                razon_social = "No disponible"
                possible_selectors = [".normal", "td.normal", ".descripcion", "strong", "b"]
                
                for selector in possible_selectors:
                    try:
                        elements = await page.query_selector_all(selector)
                        for element in elements:
                            text = await element.inner_text()
                            if text and len(text.strip()) > 10:  # Filtrar texto con contenido
                                razon_social = text.strip()
                                print(f"✅ Razón social encontrada con selector {selector}: {razon_social}")
                                break
                        if razon_social != "No disponible":
                            break
                    except:
                        continue
                
                resultado = {
                    "success": True,
                    "data": {
                        "ruc": ruc,
                        "razon_social": razon_social,
                        "estado": "Encontrado",
                        "fuente": "SUNAT_PLAYWRIGHT"
                    },
                    "timestamp": datetime.now().isoformat()
                }
            except Exception as extract_error:
                print(f"⚠️ Error extrayendo datos: {extract_error}")
                # Datos de fallback
                resultado = {
                    "success": True,
                    "data": {
                        "ruc": ruc,
                        "razon_social": f"EMPRESA RUC {ruc}",
                        "estado": "Datos limitados",
                        "fuente": "FALLBACK"
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

# Endpoint GET para compatibilidad con frontend (redirige a POST)
@app.get("/consulta-ruc-consolidada/{ruc}")
async def consultar_ruc_get(ruc: str):
    """Endpoint GET para compatibilidad - redirige al endpoint POST"""
    # Crear el objeto RUCInput internamente
    ruc_input = RUCInput(ruc=ruc)
    # Llamar al endpoint POST existente
    return await consultar_ruc_sunat(ruc_input)

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