"""
Script para debuggear la estructura HTML de SUNAT
"""
import asyncio
from playwright.async_api import async_playwright
from app.utils.playwright_helper import get_browser_launch_options

async def debug_sunat_structure():
    print("🔍 Iniciando debug de estructura HTML de SUNAT...")
    
    async with async_playwright() as p:
        try:
            launch_options = get_browser_launch_options(headless=True)
            browser = await p.chromium.launch(**launch_options)
            
            context = await browser.new_context(
                viewport={'width': 1280, 'height': 720},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            
            page = await context.new_page()
            
            # Navegar a SUNAT
            sunat_url = "https://e-consultaruc.sunat.gob.pe/cl-ti-itmrconsruc/FrameCriterioBusquedaWeb.jsp"
            print(f"🌐 Navegando a: {sunat_url}")
            
            await page.goto(sunat_url, timeout=60000, wait_until='domcontentloaded')
            print("✅ Navegación exitosa")
            
            # Esperar que la página cargue completamente
            await page.wait_for_timeout(5000)
            
            # Obtener HTML completo
            html_content = await page.content()
            print(f"📄 Tamaño del HTML: {len(html_content)} caracteres")
            
            # Buscar todos los inputs
            print("\n🔍 TODOS LOS INPUTS EN LA PÁGINA:")
            inputs = await page.query_selector_all('input')
            for i, input_elem in enumerate(inputs):
                try:
                    input_id = await input_elem.get_attribute('id')
                    input_name = await input_elem.get_attribute('name')
                    input_type = await input_elem.get_attribute('type')
                    input_value = await input_elem.get_attribute('value')
                    input_placeholder = await input_elem.get_attribute('placeholder')
                    
                    print(f"  Input {i+1}: id='{input_id}' name='{input_name}' type='{input_type}' value='{input_value}' placeholder='{input_placeholder}'")
                except:
                    print(f"  Input {i+1}: Error al obtener atributos")
            
            # Buscar todos los botones
            print("\n🔘 TODOS LOS BOTONES EN LA PÁGINA:")
            buttons = await page.query_selector_all('button, input[type="button"], input[type="submit"]')
            for i, button in enumerate(buttons):
                try:
                    button_id = await button.get_attribute('id')
                    button_name = await button.get_attribute('name')
                    button_value = await button.get_attribute('value')
                    button_text = await button.inner_text() if await button.inner_text() else ""
                    
                    print(f"  Button {i+1}: id='{button_id}' name='{button_name}' value='{button_value}' text='{button_text.strip()}'")
                except:
                    print(f"  Button {i+1}: Error al obtener atributos")
            
            # Buscar formas específicas
            print("\n📋 ELEMENTOS CON 'ruc' EN ID O NAME:")
            ruc_elements = await page.query_selector_all('[id*="ruc"], [name*="ruc"], [id*="RUC"], [name*="RUC"]')
            for i, elem in enumerate(ruc_elements):
                try:
                    tag_name = await elem.evaluate('el => el.tagName')
                    elem_id = await elem.get_attribute('id')
                    elem_name = await elem.get_attribute('name')
                    print(f"  RUC Element {i+1}: {tag_name} id='{elem_id}' name='{elem_name}'")
                except:
                    print(f"  RUC Element {i+1}: Error al obtener atributos")
            
            # Mostrar porción del HTML en el body
            body_content = await page.inner_text('body')
            print(f"\n📄 PRIMEROS 1000 CARACTERES DEL CONTENIDO:")
            print(body_content[:1000])
            
            print("\n✅ Debug completado exitosamente")
            
        except Exception as e:
            print(f"❌ Error durante debug: {e}")
            
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_sunat_structure())