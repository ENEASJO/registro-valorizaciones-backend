"""
Test final para SUNAT - evitando el cierre del browser
"""
import asyncio
from playwright.async_api import async_playwright
from app.utils.playwright_helper import get_browser_launch_options

async def test_sunat_no_wait():
    print("🔍 Probando SUNAT sin wait_for_timeout...")
    
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
            print("✅ SUNAT - Navegación exitosa")
            
            # Obtener titulo inmediatamente sin esperar
            title = await page.title()
            print(f"📄 SUNAT Title: {title}")
            
            # Intentar obtener contenido inmediatamente
            try:
                content = await page.inner_text('body')
                print(f"📄 SUNAT contenido OK (primeros 100 chars): {content[:100]}")
            except Exception as e:
                print(f"❌ Error obteniendo contenido: {e}")
            
            # Buscar el campo RUC inmediatamente
            try:
                ruc_field = await page.query_selector('#txtRuc')
                if ruc_field:
                    print("✅ Campo #txtRuc encontrado")
                else:
                    print("❌ Campo #txtRuc no encontrado")
                    
                    # Buscar alternativos
                    inputs = await page.query_selector_all('input[type="text"]')
                    print(f"📝 Encontrados {len(inputs)} campos de texto")
                    
            except Exception as e:
                print(f"❌ Error buscando campo RUC: {e}")
            
            print("✅ Test SUNAT completado")
            
        except Exception as e:
            print(f"❌ Error SUNAT: {e}")
            
        finally:
            await browser.close()

async def test_sunat_wait_load_state():
    print("\n🔍 Probando SUNAT con wait_for_load_state...")
    
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
            print("✅ SUNAT - Navegación exitosa")
            
            # Usar wait_for_load_state en lugar de wait_for_timeout
            await page.wait_for_load_state('networkidle')
            print("✅ SUNAT - Network idle")
            
            title = await page.title()
            print(f"📄 SUNAT Title: {title}")
            
            # Buscar el campo RUC
            try:
                await page.wait_for_selector('#txtRuc', timeout=10000)
                print("✅ Campo #txtRuc encontrado con wait_for_selector")
                
                # Intentar llenar el campo
                await page.fill('#txtRuc', '20600074114')
                print("✅ Campo #txtRuc llenado")
                
                # Intentar hacer clic en buscar
                await page.click('#btnAceptar')
                print("✅ Botón búsqueda clickeado")
                
            except Exception as e:
                print(f"❌ Error con campo RUC: {e}")
            
            print("✅ Test SUNAT con load_state completado")
            
        except Exception as e:
            print(f"❌ Error SUNAT load_state: {e}")
            
        finally:
            await browser.close()

async def main():
    await test_sunat_no_wait()
    await test_sunat_wait_load_state()

if __name__ == "__main__":
    asyncio.run(main())