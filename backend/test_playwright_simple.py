"""
Script simple para diagnosticar el problema de Playwright con SUNAT
"""
import asyncio
from playwright.async_api import async_playwright
from app.utils.playwright_helper import get_browser_launch_options
from app.core.config import settings

async def test_sunat_simple():
    print("🔍 Iniciando prueba simple de SUNAT con Playwright...")
    
    async with async_playwright() as p:
        try:
            launch_options = get_browser_launch_options(headless=True)
            print(f"✅ Launch options: {launch_options}")
            
            browser = await p.chromium.launch(**launch_options)
            print("✅ Browser creado exitosamente")
            
            try:
                context = await browser.new_context(
                    viewport={'width': 1280, 'height': 720},
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
                print("✅ Context creado exitosamente")
                
                page = await context.new_page()
                print("✅ Page creada exitosamente")
                
                # Intentar navegar a SUNAT
                sunat_url = "https://e-consultaruc.sunat.gob.pe/cl-ti-itmrconsruc/FrameCriterioBusquedaWeb.jsp"
                print(f"🌐 Navegando a: {sunat_url}")
                
                await page.goto(sunat_url, timeout=60000, wait_until='domcontentloaded')
                print("✅ Navegación exitosa")
                
                # Verificar que la página se cargó
                title = await page.title()
                print(f"📄 Title de la página: {title}")
                
                # Buscar el campo RUC
                await page.wait_for_selector('#txtRuc', timeout=10000)
                print("✅ Campo RUC encontrado")
                
                # Llenar el campo
                await page.fill('#txtRuc', '20600074114')
                print("✅ Campo RUC llenado")
                
                # Hacer clic en buscar
                await page.click('#btnAceptar')
                print("✅ Botón de búsqueda clickeado")
                
                # Esperar un poco
                await page.wait_for_timeout(5000)
                print("✅ Espera completada")
                
                # Obtener contenido básico
                content = await page.inner_text('body')
                print(f"📄 Primeros 300 caracteres del contenido:")
                print(content[:300])
                
                print("✅ Prueba EXITOSA - SUNAT funcionó correctamente")
                
            except Exception as e:
                print(f"❌ Error en operaciones de página: {e}")
                
            finally:
                await browser.close()
                print("✅ Browser cerrado correctamente")
                
        except Exception as e:
            print(f"❌ Error creando browser: {e}")

if __name__ == "__main__":
    asyncio.run(test_sunat_simple())