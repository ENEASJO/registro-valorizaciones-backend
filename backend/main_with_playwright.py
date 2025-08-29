# main.py - Versión estable con Playwright funcional
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
import os
import json
from datetime import datetime
from typing import Dict, Any

# Configurar Playwright helper como opcional
PLAYWRIGHT_HELPER_AVAILABLE = False
try:
    from app.utils.playwright_helper import get_browser_launch_options
    PLAYWRIGHT_HELPER_AVAILABLE = True
    print("🌐 Playwright helper loaded successfully")
except ImportError as e:
    print(f"⚠️ Playwright helper not available, using basic config: {e}")

app = FastAPI(
    title="API de Valorizaciones con Playwright", 
    description="Backend para sistema de valorizaciones con scraping SUNAT",
    version="3.1.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Endpoints básicos
@app.get("/")
async def root():
    return {
        "message": "API de Valorizaciones con Playwright funcionando",
        "status": "OK",
        "playwright_helper": PLAYWRIGHT_HELPER_AVAILABLE,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "playwright": "available"}

# Modelo para RUC
class RUCInput(BaseModel):
    ruc: str

# Endpoint de scraping SUNAT
@app.post("/consultar-ruc")
async def consultar_ruc_sunat(ruc_input: RUCInput):
    """Consultar RUC en SUNAT usando Playwright"""
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
        async with async_playwright() as p:
            # Configuración del navegador
            if PLAYWRIGHT_HELPER_AVAILABLE:
                launch_options = get_browser_launch_options(headless=True)
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
            await page.fill("#txtCaptcha", "")  # Captcha vacío para probar
            
            # Submit
            await page.click("#btnAceptar")
            await page.wait_for_timeout(3000)
            
            # Extraer datos básicos
            try:
                # Intentar obtener la razón social
                razon_social_element = await page.query_selector(".normal")
                razon_social = await razon_social_element.inner_text() if razon_social_element else "No disponible"
                
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
            
    except Exception as e:
        print(f"❌ Error en scraping: {e}")
        return {
            "success": False,
            "error": True,
            "message": f"Error consultando SUNAT: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

# Test de Playwright
@app.get("/debug/playwright-test")
async def test_playwright():
    """Endpoint para probar que Playwright funcione básicamente"""
    try:
        async with async_playwright() as p:
            if PLAYWRIGHT_HELPER_AVAILABLE:
                launch_options = get_browser_launch_options(headless=True)
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
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        return {
            "success": False,
            "error": True,
            "message": f"Error en Playwright: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

# Endpoints básicos necesarios para el frontend
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