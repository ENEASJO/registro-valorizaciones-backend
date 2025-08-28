"""
Servicio SUNAT con configuración stealth anti-detección
"""
import logging
from typing import List, Optional, Dict, Any
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

from app.models.ruc import EmpresaInfo, RepresentanteLegal
from app.core.config import settings
from app.utils.validators import validate_ruc

logger = logging.getLogger(__name__)


class SUNATServiceStealth:
    """Servicio SUNAT con configuración stealth para evitar detección"""
    
    def __init__(self):
        self.base_url = "https://e-consultaruc.sunat.gob.pe/cl-ti-itmrconsruc/FrameCriterioBusquedaWeb.jsp"
        self.timeout = 60000
        self.search_timeout = 15000
        
    def _get_stealth_browser_options(self):
        """Obtener opciones stealth para evitar detección"""
        return {
            'headless': True,
            'args': [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--no-first-run',
                '--no-zygote',
                '--disable-gpu',
                '--disable-web-security',
                '--disable-extensions',
                '--disable-plugins',
                '--disable-background-timer-throttling',
                '--disable-backgrounding-occluded-windows',
                '--disable-renderer-backgrounding',
                '--disable-blink-features=AutomationControlled',
                '--disable-ipc-flooding-protection',
                '--disable-component-extensions-with-background-pages',
                '--disable-default-apps',
                '--disable-features=VizDisplayCompositor',
                # Anti-detección adicional
                '--disable-extensions-http-throttling',
                '--disable-client-side-phishing-detection',
                '--disable-sync',
                '--no-default-browser-check',
                '--no-pings',
                '--disable-translate',
                '--disable-background-networking'
            ]
        }
    
    async def consultar_empresa(self, ruc: str) -> EmpresaInfo:
        """Consultar información completa de una empresa por RUC"""
        if not validate_ruc(ruc):
            raise ValueError(f"RUC inválido: {ruc}")
        
        logger.info(f"🔍 SUNAT STEALTH - Consultando RUC: {ruc}")
        
        async with async_playwright() as p:
            launch_options = self._get_stealth_browser_options()
            browser = await p.chromium.launch(**launch_options)
            
            try:
                # Context con configuración stealth
                context = await browser.new_context(
                    viewport={'width': 1366, 'height': 768},
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    java_script_enabled=True,
                    accept_downloads=False,
                    ignore_https_errors=True,
                    extra_http_headers={
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                        'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'DNT': '1',
                        'Connection': 'keep-alive',
                        'Upgrade-Insecure-Requests': '1',
                    }
                )
                
                page = await context.new_page()
                
                # Script stealth para ocultar automation
                await page.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined,
                    });
                    
                    window.chrome = {
                        runtime: {},
                    };
                    
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => [1, 2, 3, 4, 5],
                    });
                    
                    Object.defineProperty(navigator, 'languages', {
                        get: () => ['es-ES', 'es'],
                    });
                """)
                
                # Navegar con pausa natural
                logger.info("🌐 Navegando a SUNAT...")
                await page.goto(self.base_url, timeout=self.timeout, wait_until='load')
                
                # Espera simulando comportamiento humano
                import random
                await page.wait_for_timeout(random.randint(2000, 4000))
                
                # Ejecutar búsqueda
                await self._ejecutar_busqueda_stealth(page, ruc)
                
                # Extraer datos
                razon_social = await self._obtener_razon_social_stealth(page, ruc)
                domicilio_fiscal = await self._obtener_domicilio_fiscal_stealth(page, ruc)
                representantes = []  # Por ahora, enfocarnos en razón social
                
                resultado = EmpresaInfo(
                    ruc=ruc,
                    razon_social=razon_social,
                    domicilio_fiscal=domicilio_fiscal,
                    representantes=representantes
                )
                
                logger.info(f"✅ SUNAT STEALTH - Consulta exitosa para RUC {ruc}")
                return resultado
                
            except PlaywrightTimeoutError as e:
                logger.error(f"⏰ Timeout SUNAT STEALTH para RUC {ruc}: {str(e)}")
                raise Exception(f"Timeout al consultar SUNAT: {str(e)}")
                
            except Exception as e:
                logger.error(f"❌ Error SUNAT STEALTH para RUC {ruc}: {str(e)}")
                raise Exception(f"Error al consultar SUNAT: {str(e)}")
                
            finally:
                try:
                    await browser.close()
                except:
                    pass
    
    async def _ejecutar_busqueda_stealth(self, page, ruc: str):
        """Ejecutar búsqueda con comportamiento humano simulado"""
        try:
            logger.info(f"🔍 Buscando campo RUC...")
            
            # Esperar que aparezca el campo RUC con timeout largo
            await page.wait_for_selector('#txtRuc', timeout=self.search_timeout)
            logger.info("✅ Campo RUC encontrado")
            
            # Simular tipeo humano
            await page.click('#txtRuc')
            await page.wait_for_timeout(500)
            
            # Limpiar campo y escribir lentamente
            await page.fill('#txtRuc', '')
            await page.wait_for_timeout(300)
            
            for char in ruc:
                await page.type('#txtRuc', char, delay=100)  # Tipeo lento
            
            await page.wait_for_timeout(1000)
            
            # Buscar botón de aceptar
            await page.wait_for_selector('#btnAceptar', timeout=self.search_timeout)
            await page.click('#btnAceptar')
            logger.info("✅ Búsqueda iniciada")
            
            # Esperar respuesta con timeout largo
            await page.wait_for_timeout(8000)
            
        except Exception as e:
            logger.error(f"❌ Error en búsqueda stealth: {str(e)}")
            raise
    
    async def _obtener_razon_social_stealth(self, page, ruc: str) -> str:
        """Obtener razón social con método stealth"""
        try:
            logger.info(f"📝 Extrayendo razón social para RUC: {ruc}")
            
            # Esperar a que cargue el contenido
            await page.wait_for_load_state('networkidle', timeout=self.timeout)
            
            # Debug: obtener contenido de la página
            content = await page.inner_text('body')
            print(f"🔍 DEBUG STEALTH: Contenido parcial: {content[:500]}")
            
            # Método 1: Selectores CSS específicos
            selectores = [
                "td.bgn:has-text('Nombre o Razón Social:') + td",
                "td:has-text('Nombre o Razón Social:') + td",
                "td.bgn:has-text('Razón Social:') + td",
                "td:has-text('Razón Social:') + td",
                "[class*='razon']",
                "[id*='razon']"
            ]
            
            for selector in selectores:
                try:
                    element = await page.wait_for_selector(selector, timeout=5000)
                    if element:
                        text = (await element.inner_text()).strip()
                        if text and len(text) > 5 and not text.startswith(('Nombre', 'Razón')):
                            logger.info(f"📝 Razón social encontrada: {text}")
                            return text
                except:
                    continue
            
            # Método 2: Buscar en texto completo
            lines = content.split('\\n')
            for line in lines:
                # Formato RUC - RAZÓN SOCIAL
                if ruc in line and ' - ' in line:
                    parts = line.split(' - ', 1)
                    if len(parts) > 1:
                        razon = parts[1].strip()
                        if len(razon) > 5:
                            logger.info(f"📝 Razón social extraída: {razon}")
                            return razon
                
                # Líneas con indicadores de razón social
                if 'Razón Social:' in line or 'Nombre o Razón Social:' in line:
                    if ':' in line:
                        razon = line.split(':', 1)[1].strip()
                        if len(razon) > 5:
                            logger.info(f"📝 Razón social extraída: {razon}")
                            return razon
            
            # Método 3: Buscar línea específica con formato "RUC - RAZÓN SOCIAL"
            for line in lines:
                line = line.strip()
                if line.startswith(ruc + ' - '):
                    razon = line.replace(ruc + ' - ', '').strip()
                    if len(razon) > 5:
                        logger.info(f"📝 Razón social limpia encontrada: {razon}")
                        return razon
            
            # Método 4: Buscar nombre de empresa típico
            for line in lines:
                line = line.strip()
                if (len(line) > 10 and 
                    any(keyword in line.upper() for keyword in ['S.A.', 'S.R.L.', 'E.I.R.L.', 'S.A.C.', 'SOCIEDAD', 'EMPRESA', 'CORPORACION', 'COMPAÑIA']) and
                    ruc not in line and
                    not any(exclude in line.upper() for exclude in ['TIPO', 'FECHA', 'ESTADO', 'CONDICION', 'COMERCIAL'])):
                    logger.info(f"📝 Posible razón social encontrada: {line}")
                    return line
            
            raise Exception(f"No se pudo encontrar razón social para RUC {ruc}")
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo razón social stealth: {str(e)}")
            raise
    
    async def _obtener_domicilio_fiscal_stealth(self, page, ruc: str) -> str:
        """Obtener domicilio fiscal con método stealth"""
        try:
            logger.info(f"🏠 Extrayendo domicilio fiscal para RUC: {ruc}")
            
            content = await page.inner_text('body')
            lines = content.split('\\n')
            
            for i, line in enumerate(lines):
                if 'Domicilio Fiscal:' in line:
                    # Buscar en la misma línea
                    if ':' in line:
                        domicilio = line.split(':', 1)[1].strip()
                        # Limpiar datos adicionales
                        if 'Sistema Emisión' in domicilio:
                            domicilio = domicilio.split('Sistema Emisión')[0].strip()
                        if len(domicilio) > 15 and domicilio != '-':
                            logger.info(f"🏠 Domicilio fiscal encontrado: {domicilio}")
                            return domicilio
                    
                    # Buscar en líneas siguientes
                    if i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        # Limpiar posibles líneas extras
                        if 'Sistema' in next_line or 'Actividad' in next_line:
                            continue
                        if len(next_line) > 15 and next_line != '-':
                            logger.info(f"🏠 Domicilio fiscal encontrado: {next_line}")
                            return next_line
            
            return "No disponible"
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo domicilio fiscal stealth: {str(e)}")
            return "No disponible"


# Instancia singleton del servicio stealth
sunat_service_stealth = SUNATServiceStealth()