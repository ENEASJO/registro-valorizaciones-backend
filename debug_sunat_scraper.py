#!/usr/bin/env python3
"""
Debug SUNAT Scraper - Comprehensive debugging tool
Analyzes exactly what SUNAT returns to fix selector issues

This script will:
1. Take screenshots after form submission
2. Save HTML content for analysis  
3. Log all h4, paragraph, and table elements
4. Test different wait strategies
5. Provide detailed debugging output
"""

import asyncio
import os
from datetime import datetime
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
import json
import re

class SUNATDebugger:
    def __init__(self):
        self.base_url = "https://e-consultaruc.sunat.gob.pe/cl-ti-itmrconsruc/FrameCriterioBusquedaWeb.jsp"
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        self.timeout = 60000
        self.debug_dir = "/tmp/sunat_debug"
        
        # Create debug directory
        os.makedirs(self.debug_dir, exist_ok=True)
        
    async def debug_ruc_extraction(self, ruc: str):
        """
        Comprehensive debug analysis of RUC extraction from SUNAT
        """
        print(f"\n🔍 INICIANDO DEBUG COMPLETO PARA RUC: {ruc}")
        print(f"📁 Archivos de debug se guardarán en: {self.debug_dir}")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        async with async_playwright() as p:
            # Use headless=False for local debugging, headless=True for production
            is_local = not any(os.environ.get(var) for var in ['K_SERVICE', 'GOOGLE_CLOUD_PROJECT'])
            headless = not is_local  # Show browser locally, hide in production
            
            browser = await p.chromium.launch(
                headless=headless,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-web-security'
                ]
            )
            
            try:
                page = await browser.new_page(
                    user_agent=self.user_agent,
                    viewport={'width': 1280, 'height': 720}
                )
                
                # Enable console logging
                page.on("console", lambda msg: print(f"🖥️ Console: {msg.text}"))
                page.on("pageerror", lambda error: print(f"❌ Page Error: {error}"))
                
                print("\n=== PASO 1: NAVEGACIÓN INICIAL ===")
                print(f"🌐 Navegando a: {self.base_url}")
                
                await page.goto(self.base_url, timeout=self.timeout, wait_until='domcontentloaded')
                await page.wait_for_timeout(2000)
                
                # Screenshot inicial
                await page.screenshot(path=f"{self.debug_dir}/01_pagina_inicial_{ruc}_{timestamp}.png", full_page=True)
                print(f"📸 Screenshot inicial guardado")
                
                print("\n=== PASO 2: LLENADO DE FORMULARIO ===")
                print(f"📝 Llenando RUC: {ruc}")
                
                await page.fill("#txtRuc", ruc)
                await page.wait_for_timeout(1000)
                
                # Check for CAPTCHA
                captcha_present = await self._check_captcha(page)
                if captcha_present:
                    print("🔐 CAPTCHA detectado - esto podría causar problemas")
                
                print("🔄 Enviando formulario...")
                await page.click("#btnAceptar")
                
                print("\n=== PASO 3: ESPERANDO RESULTADOS ===")
                
                # Wait with different strategies
                await self._wait_for_results(page, ruc)
                
                # Screenshot después del submit
                await page.screenshot(path=f"{self.debug_dir}/02_despues_submit_{ruc}_{timestamp}.png", full_page=True)
                print(f"📸 Screenshot después de submit guardado")
                
                print("\n=== PASO 4: ANÁLISIS DE CONTENIDO ===")
                
                # Save complete HTML
                html_content = await page.content()
                with open(f"{self.debug_dir}/03_html_completo_{ruc}_{timestamp}.html", 'w', encoding='utf-8') as f:
                    f.write(html_content)
                print(f"💾 HTML completo guardado")
                
                # Get page text
                page_text = await page.evaluate('() => document.body.innerText')
                with open(f"{self.debug_dir}/04_texto_pagina_{ruc}_{timestamp}.txt", 'w', encoding='utf-8') as f:
                    f.write(page_text)
                print(f"📄 Texto de página guardado")
                
                print("\n=== PASO 5: ANÁLISIS DETALLADO DE ELEMENTOS ===")
                
                debug_info = await self._analyze_page_elements(page, ruc)
                
                # Save debug info as JSON
                with open(f"{self.debug_dir}/05_debug_info_{ruc}_{timestamp}.json", 'w', encoding='utf-8') as f:
                    json.dump(debug_info, f, indent=2, ensure_ascii=False)
                print(f"🔍 Información de debug guardada")
                
                print("\n=== PASO 6: EXTRACCIÓN USANDO MÚLTIPLES ESTRATEGIAS ===")
                
                extraction_results = await self._test_extraction_strategies(page, ruc)
                
                # Save extraction results
                with open(f"{self.debug_dir}/06_extraccion_resultados_{ruc}_{timestamp}.json", 'w', encoding='utf-8') as f:
                    json.dump(extraction_results, f, indent=2, ensure_ascii=False)
                print(f"⚗️ Resultados de extracción guardados")
                
                print("\n=== RESUMEN DE DEBUG ===")
                print(f"📁 Archivos generados en: {self.debug_dir}")
                print(f"🔍 Total de estrategias exitosas: {len([r for r in extraction_results['strategies'] if r['success']])}")
                
                # Return the best result found
                best_result = self._find_best_extraction_result(extraction_results)
                
                print(f"\n✅ MEJOR RESULTADO ENCONTRADO:")
                print(f"   Estrategia: {best_result['strategy']}")
                print(f"   Razón Social: {best_result['razon_social']}")
                print(f"   Éxito: {best_result['success']}")
                
                return {
                    "ruc": ruc,
                    "debug_dir": self.debug_dir,
                    "timestamp": timestamp,
                    "best_result": best_result,
                    "all_results": extraction_results,
                    "captcha_detected": captcha_present
                }
                
            finally:
                await browser.close()
    
    async def _check_captcha(self, page):
        """Check if CAPTCHA is present on the page"""
        captcha_selectors = [
            "#txtCodigo", "#txtCaptcha", 
            "input[name*='captcha']", "input[name*='codigo']",
            "img[src*='captcha']", "img[src*='codigo']"
        ]
        
        for selector in captcha_selectors:
            try:
                if await page.is_visible(selector, timeout=1000):
                    print(f"🔐 CAPTCHA encontrado: {selector}")
                    return True
            except:
                continue
        
        return False
    
    async def _wait_for_results(self, page, ruc):
        """Wait for results using different strategies"""
        print("⏳ Estrategia 1: Esperar por domcontentloaded...")
        try:
            await page.wait_for_load_state('domcontentloaded', timeout=10000)
            print("✅ domcontentloaded completado")
        except PlaywrightTimeoutError:
            print("⚠️ Timeout en domcontentloaded")
        
        print("⏳ Estrategia 2: Esperar por networkidle...")
        try:
            await page.wait_for_load_state('networkidle', timeout=10000)
            print("✅ networkidle completado")
        except PlaywrightTimeoutError:
            print("⚠️ Timeout en networkidle")
        
        print("⏳ Estrategia 3: Esperar por elemento específico...")
        try:
            await page.wait_for_selector('h4, .bgn, table', timeout=5000)
            print("✅ Elementos básicos encontrados")
        except PlaywrightTimeoutError:
            print("⚠️ No se encontraron elementos básicos")
        
        print("⏳ Estrategia 4: Espera fija...")
        await page.wait_for_timeout(5000)
        print("✅ Espera fija completada")
    
    async def _analyze_page_elements(self, page, ruc):
        """Analyze all relevant elements on the page"""
        debug_info = {
            "url": page.url,
            "title": await page.title(),
            "h4_elements": [],
            "paragraph_elements": [],
            "table_elements": [],
            "form_elements": [],
            "ruc_containing_elements": []
        }
        
        print("🔍 Analizando elementos H4...")
        h4_elements = await page.query_selector_all('h4')
        for i, h4 in enumerate(h4_elements):
            text = await h4.inner_text()
            debug_info["h4_elements"].append({
                "index": i,
                "text": text.strip(),
                "contains_ruc": ruc in text
            })
            print(f"   H4[{i}]: {text.strip()}")
        
        print("🔍 Analizando elementos de párrafo...")
        p_elements = await page.query_selector_all('p')
        for i, p in enumerate(p_elements):
            text = await p.inner_text()
            if text.strip():  # Only non-empty paragraphs
                debug_info["paragraph_elements"].append({
                    "index": i,
                    "text": text.strip(),
                    "contains_ruc": ruc in text
                })
                print(f"   P[{i}]: {text.strip()[:100]}{'...' if len(text) > 100 else ''}")
        
        print("🔍 Analizando tablas...")
        table_elements = await page.query_selector_all('table')
        for i, table in enumerate(table_elements):
            rows = await table.query_selector_all('tr')
            table_data = []
            
            for row in rows:
                cells = await row.query_selector_all('td, th')
                row_data = []
                for cell in cells:
                    cell_text = await cell.inner_text()
                    row_data.append(cell_text.strip())
                if any(row_data):  # Only non-empty rows
                    table_data.append(row_data)
            
            if table_data:
                debug_info["table_elements"].append({
                    "index": i,
                    "rows": table_data,
                    "contains_ruc": any(ruc in str(row) for row in table_data)
                })
                print(f"   Tabla[{i}]: {len(table_data)} filas")
        
        print("🔍 Buscando todos los elementos que contienen el RUC...")
        # Find all elements containing the RUC
        ruc_elements = await page.query_selector_all(f'text={ruc}')
        for i, element in enumerate(ruc_elements):
            try:
                text = await element.inner_text()
                tag_name = await element.evaluate('el => el.tagName')
                debug_info["ruc_containing_elements"].append({
                    "index": i,
                    "tag": tag_name,
                    "text": text.strip(),
                    "full_line": text.strip()
                })
                print(f"   RUC Element[{i}] ({tag_name}): {text.strip()}")
            except:
                continue
        
        return debug_info
    
    async def _test_extraction_strategies(self, page, ruc):
        """Test multiple extraction strategies"""
        strategies = []
        
        # Strategy 1: H4 with RUC pattern
        print("\n🧪 Estrategia 1: Buscar en H4 con patrón RUC")
        result1 = await self._strategy_h4_ruc_pattern(page, ruc)
        strategies.append({"name": "H4_RUC_Pattern", **result1})
        
        # Strategy 2: Text search in all elements
        print("🧪 Estrategia 2: Búsqueda de texto en todos los elementos")
        result2 = await self._strategy_text_search(page, ruc)
        strategies.append({"name": "Text_Search", **result2})
        
        # Strategy 3: Table-based extraction
        print("🧪 Estrategia 3: Extracción basada en tablas")
        result3 = await self._strategy_table_extraction(page, ruc)
        strategies.append({"name": "Table_Extraction", **result3})
        
        # Strategy 4: CSS selector combinations
        print("🧪 Estrategia 4: Combinaciones de selectores CSS")
        result4 = await self._strategy_css_selectors(page, ruc)
        strategies.append({"name": "CSS_Selectors", **result4})
        
        # Strategy 5: Page text analysis
        print("🧪 Estrategia 5: Análisis completo del texto de la página")
        result5 = await self._strategy_full_text_analysis(page, ruc)
        strategies.append({"name": "Full_Text_Analysis", **result5})
        
        return {"strategies": strategies}
    
    async def _strategy_h4_ruc_pattern(self, page, ruc):
        """Strategy 1: Look for H4 elements with RUC pattern"""
        try:
            h4_elements = await page.query_selector_all('h4')
            
            for h4 in h4_elements:
                text = await h4.inner_text()
                text = text.strip()
                
                if " - " in text and text.startswith(ruc):
                    parts = text.split(" - ", 1)
                    if len(parts) >= 2:
                        razon_social = parts[1].strip()
                        print(f"   ✅ Encontrado en H4: {razon_social}")
                        return {
                            "success": True,
                            "razon_social": razon_social,
                            "method": "H4 direct match",
                            "element": text
                        }
            
            return {"success": False, "razon_social": "No encontrado", "method": "H4 search failed"}
            
        except Exception as e:
            return {"success": False, "razon_social": "Error", "error": str(e)}
    
    async def _strategy_text_search(self, page, ruc):
        """Strategy 2: Search for RUC pattern in all text elements"""
        try:
            # Search for elements containing RUC followed by dash
            ruc_pattern = f'{ruc} - '
            elements_with_pattern = await page.query_selector_all(f'text=/{re.escape(ruc_pattern)}/')
            
            for element in elements_with_pattern:
                text = await element.inner_text()
                if " - " in text:
                    parts = text.split(" - ", 1)
                    if len(parts) >= 2 and parts[1].strip():
                        razon_social = parts[1].strip()
                        print(f"   ✅ Encontrado por búsqueda de texto: {razon_social}")
                        return {
                            "success": True,
                            "razon_social": razon_social,
                            "method": "Text pattern search",
                            "element": text
                        }
            
            return {"success": False, "razon_social": "No encontrado", "method": "Text search failed"}
            
        except Exception as e:
            return {"success": False, "razon_social": "Error", "error": str(e)}
    
    async def _strategy_table_extraction(self, page, ruc):
        """Strategy 3: Extract from table structures"""
        try:
            tables = await page.query_selector_all('table')
            
            for table in tables:
                rows = await table.query_selector_all('tr')
                
                for row in rows:
                    cells = await row.query_selector_all('td, th')
                    
                    for cell in cells:
                        text = await cell.inner_text()
                        text = text.strip()
                        
                        if " - " in text and text.startswith(ruc):
                            parts = text.split(" - ", 1)
                            if len(parts) >= 2:
                                razon_social = parts[1].strip()
                                print(f"   ✅ Encontrado en tabla: {razon_social}")
                                return {
                                    "success": True,
                                    "razon_social": razon_social,
                                    "method": "Table cell extraction",
                                    "element": text
                                }
            
            return {"success": False, "razon_social": "No encontrado", "method": "Table search failed"}
            
        except Exception as e:
            return {"success": False, "razon_social": "Error", "error": str(e)}
    
    async def _strategy_css_selectors(self, page, ruc):
        """Strategy 4: Try various CSS selector combinations"""
        selectors = [
            "td.bgn:has-text('Nombre o Razón Social:') + td",
            "td:has-text('Nombre o Razón Social:') + td",
            "td.bgn:has-text('Razón Social:') + td",
            "td:has-text('Razón Social:') + td",
            ".datos-empresa .razon-social",
            ".empresa-info .nombre",
            ".resultado .empresa",
            "span:has-text('Nombre o Razón Social:') ~ span",
            "div:has-text('Nombre o Razón Social:') ~ div"
        ]
        
        try:
            for i, selector in enumerate(selectors):
                try:
                    element = await page.wait_for_selector(selector, timeout=2000)
                    if element:
                        text = await element.inner_text()
                        text = text.strip()
                        if text and len(text) > 5:
                            print(f"   ✅ Encontrado con selector {i}: {text}")
                            return {
                                "success": True,
                                "razon_social": text,
                                "method": f"CSS selector: {selector}",
                                "element": text
                            }
                except PlaywrightTimeoutError:
                    continue
                except Exception:
                    continue
            
            return {"success": False, "razon_social": "No encontrado", "method": "CSS selectors failed"}
            
        except Exception as e:
            return {"success": False, "razon_social": "Error", "error": str(e)}
    
    async def _strategy_full_text_analysis(self, page, ruc):
        """Strategy 5: Analyze complete page text"""
        try:
            page_text = await page.evaluate('() => document.body.innerText')
            lines = page_text.split('\n')
            
            # Method 1: Look for lines starting with RUC
            for line in lines:
                line = line.strip()
                if line.startswith(ruc) and " - " in line:
                    parts = line.split(" - ", 1)
                    if len(parts) >= 2:
                        razon_social = parts[1].strip()
                        # Validate it looks like a company name
                        if len(razon_social) > 5 and not razon_social.isdigit():
                            print(f"   ✅ Encontrado en análisis completo (método 1): {razon_social}")
                            return {
                                "success": True,
                                "razon_social": razon_social,
                                "method": "Full text analysis - direct RUC line",
                                "element": line
                            }
            
            # Method 2: Look for labels followed by company names
            for i, line in enumerate(lines):
                if 'Nombre o Razón Social:' in line or 'Razón Social:' in line:
                    # Check same line
                    if ':' in line:
                        parts = line.split(':', 1)
                        if len(parts) > 1 and parts[1].strip():
                            razon_social = parts[1].strip()
                            if len(razon_social) > 5:
                                print(f"   ✅ Encontrado en análisis completo (método 2a): {razon_social}")
                                return {
                                    "success": True,
                                    "razon_social": razon_social,
                                    "method": "Full text analysis - label same line",
                                    "element": line
                                }
                    
                    # Check next line
                    if i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        if next_line and len(next_line) > 5 and not next_line.startswith(('Nombre', 'RUC', 'Tipo')):
                            print(f"   ✅ Encontrado en análisis completo (método 2b): {next_line}")
                            return {
                                "success": True,
                                "razon_social": next_line,
                                "method": "Full text analysis - label next line",
                                "element": f"{line} -> {next_line}"
                            }
            
            return {"success": False, "razon_social": "No encontrado", "method": "Full text analysis failed"}
            
        except Exception as e:
            return {"success": False, "razon_social": "Error", "error": str(e)}
    
    def _find_best_extraction_result(self, extraction_results):
        """Find the best extraction result from all strategies"""
        successful_strategies = [s for s in extraction_results["strategies"] if s["success"]]
        
        if not successful_strategies:
            return {
                "strategy": "None",
                "razon_social": "No disponible",
                "success": False,
                "method": "All strategies failed"
            }
        
        # Prefer specific strategies in order
        strategy_priority = [
            "H4_RUC_Pattern",
            "Text_Search", 
            "Table_Extraction",
            "CSS_Selectors",
            "Full_Text_Analysis"
        ]
        
        for preferred in strategy_priority:
            for strategy in successful_strategies:
                if strategy["name"] == preferred:
                    return {
                        "strategy": strategy["name"],
                        "razon_social": strategy["razon_social"],
                        "success": True,
                        "method": strategy["method"]
                    }
        
        # Return first successful if no preferred found
        first_successful = successful_strategies[0]
        return {
            "strategy": first_successful["name"],
            "razon_social": first_successful["razon_social"],
            "success": True,
            "method": first_successful["method"]
        }


async def main():
    """Main function to run the SUNAT debugger"""
    import sys
    
    if len(sys.argv) != 2:
        print("❌ Uso: python debug_sunat_scraper.py <RUC>")
        print("   Ejemplo: python debug_sunat_scraper.py 20100070970")
        return
    
    ruc = sys.argv[1].strip()
    
    if len(ruc) != 11 or not ruc.isdigit():
        print(f"❌ RUC inválido: {ruc}")
        print("   Debe tener exactamente 11 dígitos numéricos")
        return
    
    debugger = SUNATDebugger()
    result = await debugger.debug_ruc_extraction(ruc)
    
    print(f"\n🎯 RESULTADO FINAL:")
    print(f"   RUC: {result['ruc']}")
    print(f"   Mejor estrategia: {result['best_result']['strategy']}")
    print(f"   Razón Social: {result['best_result']['razon_social']}")
    print(f"   Éxito: {'✅' if result['best_result']['success'] else '❌'}")
    print(f"   CAPTCHA detectado: {'Sí' if result['captcha_detected'] else 'No'}")
    print(f"\n📁 Archivos de debug en: {result['debug_dir']}")
    
    return result


if __name__ == "__main__":
    asyncio.run(main())