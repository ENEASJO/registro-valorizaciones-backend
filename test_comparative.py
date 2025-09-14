"""
Test comparativo entre OSCE y SUNAT
"""
import asyncio
from playwright.async_api import async_playwright
from app.utils.playwright_helper import get_browser_launch_options

async def test_osce():
    print("🔍 Probando OSCE...")
    
    async with async_playwright() as p:
        try:
            launch_options = get_browser_launch_options(headless=True)
            browser = await p.chromium.launch(**launch_options)
            
            context = await browser.new_context(
                viewport={'width': 1280, 'height': 720},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            
            page = await context.new_page()
            
            # Test OSCE
            osce_url = "https://apps.osce.gob.pe/perfilprov-ui/"
            print(f"🌐 Navegando a OSCE: {osce_url}")
            
            await page.goto(osce_url, timeout=60000, wait_until='domcontentloaded')
            print("✅ OSCE - Navegación exitosa")
            
            await page.wait_for_timeout(3000)
            
            title = await page.title()
            print(f"📄 OSCE Title: {title}")
            
            # Buscar campos de entrada
            inputs = await page.query_selector_all('input[type="text"]')
            print(f"📝 OSCE encontró {len(inputs)} campos de texto")
            
            print("✅ OSCE funcionó correctamente")
            
        except Exception as e:
            print(f"❌ Error OSCE: {e}")
            
        finally:
            await browser.close()

async def test_sunat_minimal():
    print("\n🔍 Probando SUNAT con configuración mínima...")
    
    async with async_playwright() as p:
        try:
            # Configuración mínima sin argumentos extra
            browser = await p.chromium.launch(headless=True)
            print("✅ Browser creado con configuración mínima")
            
            context = await browser.new_context()
            page = await context.new_page()
            
            # Test SUNAT
            sunat_url = "https://e-consultaruc.sunat.gob.pe/cl-ti-itmrconsruc/FrameCriterioBusquedaWeb.jsp"
            print(f"🌐 Navegando a SUNAT: {sunat_url}")
            
            await page.goto(sunat_url, timeout=60000)
            print("✅ SUNAT - Navegación exitosa (configuración mínima)")
            
            await page.wait_for_timeout(3000)
            
            title = await page.title()
            print(f"📄 SUNAT Title: {title}")
            
            # Intentar obtener contenido básico
            content = await page.inner_text('body')
            print(f"📄 SUNAT contenido (primeros 200 chars): {content[:200]}")
            
            print("✅ SUNAT funcionó con configuración mínima")
            
        except Exception as e:
            print(f"❌ Error SUNAT mínimo: {e}")
            
        finally:
            await browser.close()

async def test_sunat_optimized():
    print("\n🔍 Probando SUNAT con configuración optimizada...")
    
    async with async_playwright() as p:
        try:
            launch_options = get_browser_launch_options(headless=True)
            browser = await p.chromium.launch(**launch_options)
            
            context = await browser.new_context(
                viewport={'width': 1280, 'height': 720},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            
            page = await context.new_page()
            
            # Test SUNAT
            sunat_url = "https://e-consultaruc.sunat.gob.pe/cl-ti-itmrconsruc/FrameCriterioBusquedaWeb.jsp"
            print(f"🌐 Navegando a SUNAT: {sunat_url}")
            
            await page.goto(sunat_url, timeout=60000, wait_until='domcontentloaded')
            print("✅ SUNAT - Navegación exitosa (optimizada)")
            
            await page.wait_for_timeout(3000)
            
            title = await page.title()
            print(f"📄 SUNAT Title: {title}")
            
            print("✅ SUNAT funcionó con configuración optimizada")
            
        except Exception as e:
            print(f"❌ Error SUNAT optimizada: {e}")
            
        finally:
            await browser.close()

async def main():
    await test_osce()
    await test_sunat_minimal()
    await test_sunat_optimized()

if __name__ == "__main__":
    asyncio.run(main())