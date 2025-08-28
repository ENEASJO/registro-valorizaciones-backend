"""
Servicio SUNAT con extracción limpia y específica
"""
import logging
import re
from typing import List, Optional, Dict, Any
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

from app.models.ruc import EmpresaInfo, RepresentanteLegal
from app.core.config import settings
from app.utils.validators import validate_ruc

logger = logging.getLogger(__name__)


class SUNATServiceClean:
    """Servicio SUNAT con extracción de datos limpios y específicos"""
    
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
        
        logger.info(f"🔍 SUNAT CLEAN - Consultando RUC: {ruc}")
        
        async with async_playwright() as p:
            launch_options = self._get_stealth_browser_options()
            browser = await p.chromium.launch(**launch_options)
            
            try:
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
                
                # Script stealth
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
                
                # Navegar y ejecutar búsqueda
                await page.goto(self.base_url, timeout=self.timeout, wait_until='load')
                
                import random
                await page.wait_for_timeout(random.randint(2000, 4000))
                
                await self._ejecutar_busqueda_stealth(page, ruc)
                
                # Extraer datos con limpieza
                datos_crudos = await page.inner_text('body')
                datos_limpios = self._extraer_datos_limpios(datos_crudos, ruc)
                
                resultado = EmpresaInfo(
                    ruc=ruc,
                    razon_social=datos_limpios['razon_social'],
                    domicilio_fiscal=datos_limpios['domicilio_fiscal'],
                    representantes=[]  # Por ahora enfocados en datos básicos
                )
                
                logger.info(f"✅ SUNAT CLEAN - Consulta exitosa para RUC {ruc}")
                return resultado
                
            except PlaywrightTimeoutError as e:
                logger.error(f"⏰ Timeout SUNAT CLEAN para RUC {ruc}: {str(e)}")
                raise Exception(f"Timeout al consultar SUNAT: {str(e)}")
                
            except Exception as e:
                logger.error(f"❌ Error SUNAT CLEAN para RUC {ruc}: {str(e)}")
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
            
            await page.wait_for_selector('#txtRuc', timeout=self.search_timeout)
            logger.info("✅ Campo RUC encontrado")
            
            # Simular tipeo humano
            await page.click('#txtRuc')
            await page.wait_for_timeout(500)
            await page.fill('#txtRuc', '')
            await page.wait_for_timeout(300)
            
            for char in ruc:
                await page.type('#txtRuc', char, delay=100)
            
            await page.wait_for_timeout(1000)
            
            await page.wait_for_selector('#btnAceptar', timeout=self.search_timeout)
            await page.click('#btnAceptar')
            logger.info("✅ Búsqueda iniciada")
            
            await page.wait_for_timeout(8000)
            
        except Exception as e:
            logger.error(f"❌ Error en búsqueda stealth: {str(e)}")
            raise
    
    def _extraer_datos_limpios(self, contenido: str, ruc: str) -> Dict[str, str]:
        """Extraer datos específicos y limpios del contenido HTML"""
        logger.info("🧹 Limpiando y extrayendo datos específicos...")
        
        datos = {
            'razon_social': '',
            'domicilio_fiscal': ''
        }
        
        lineas = contenido.split('\n')
        
        # Extraer razón social
        datos['razon_social'] = self._extraer_razon_social_limpia(lineas, ruc)
        
        # Extraer domicilio fiscal
        datos['domicilio_fiscal'] = self._extraer_domicilio_fiscal_limpio(lineas)
        
        return datos
    
    def _extraer_razon_social_limpia(self, lineas: List[str], ruc: str) -> str:
        """Extraer solo la razón social limpia"""
        
        # Método 1: Buscar línea que empiece con RUC - NOMBRE
        for linea in lineas:
            linea = linea.strip()
            if linea.startswith(f"{ruc} - "):
                razon = linea.replace(f"{ruc} - ", "").strip()
                if len(razon) > 3:
                    logger.info(f"📝 Razón social extraída (método RUC-NOMBRE): {razon}")
                    return razon
        
        # Método 2: Buscar después de "Razón Social:" o "Nombre o Razón Social:"
        for i, linea in enumerate(lineas):
            if "Nombre o Razón Social:" in linea or "Razón Social:" in linea:
                # En la misma línea
                if ":" in linea:
                    razon = linea.split(":", 1)[1].strip()
                    if len(razon) > 3 and not razon.startswith(("Tipo", "SOCIEDAD")):
                        logger.info(f"📝 Razón social extraída (método etiqueta): {razon}")
                        return razon
                
                # En la siguiente línea
                if i + 1 < len(lineas):
                    siguiente = lineas[i + 1].strip()
                    if (len(siguiente) > 3 and 
                        not siguiente.startswith(("Tipo", "Nombre", "RUC", "SOCIEDAD")) and
                        not siguiente in ["-", "ACTIVO", "HABIDO"]):
                        logger.info(f"📝 Razón social extraída (línea siguiente): {siguiente}")
                        return siguiente
        
        # Método 3: Buscar nombres típicos de empresas
        for linea in lineas:
            linea = linea.strip()
            # Buscar líneas que contengan terminaciones típicas de empresas
            if (len(linea) > 10 and 
                any(terminacion in linea.upper() for terminacion in [
                    'S.A.C.', 'S.A.', 'S.R.L.', 'E.I.R.L.', 'SOCIEDAD ANONIMA', 
                    'SOCIEDAD COMERCIAL', 'EMPRESA', 'CORPORACION', 'COMPAÑIA'
                ]) and
                ruc not in linea and
                not any(excluir in linea.upper() for excluir in [
                    'TIPO', 'FECHA', 'ESTADO', 'CONDICION', 'COMERCIAL:', 'INSCRIPCION'
                ])):
                logger.info(f"📝 Razón social extraída (método empresa típica): {linea}")
                return linea
        
        logger.warning("⚠️ No se pudo extraer razón social limpia")
        return "No disponible"
    
    def _extraer_domicilio_fiscal_limpio(self, lineas: List[str]) -> str:
        """Extraer solo el domicilio fiscal limpio"""
        
        for i, linea in enumerate(lineas):
            if "Domicilio Fiscal:" in linea:
                # En la misma línea
                if ":" in linea:
                    domicilio = linea.split(":", 1)[1].strip()
                    if len(domicilio) > 15 and domicilio != "-":
                        # Limpiar texto adicional
                        domicilio = self._limpiar_domicilio(domicilio)
                        if domicilio and len(domicilio) > 15:
                            logger.info(f"🏠 Domicilio extraído (misma línea): {domicilio}")
                            return domicilio
                
                # En líneas siguientes
                for j in range(i + 1, min(i + 5, len(lineas))):  # Buscar en las próximas 4 líneas
                    siguiente = lineas[j].strip()
                    
                    if (len(siguiente) > 15 and 
                        siguiente != "-" and
                        not any(excluir in siguiente.upper() for excluir in [
                            'SISTEMA', 'ACTIVIDAD', 'COMERCIO', 'CONTABILIDAD', 'MANUAL',
                            'COMPROBANTE', 'EMISION', 'ELECTRONICA'
                        ])):
                        
                        domicilio = self._limpiar_domicilio(siguiente)
                        if domicilio and len(domicilio) > 15:
                            logger.info(f"🏠 Domicilio extraído (línea {j-i}): {domicilio}")
                            return domicilio
        
        logger.warning("⚠️ No se pudo extraer domicilio fiscal limpio")
        return "No disponible"
    
    def _limpiar_domicilio(self, domicilio: str) -> str:
        """Limpiar el domicilio fiscal de texto adicional"""
        # Remover texto que aparece después del domicilio
        separadores = [
            'Sistema Emisión', 'Actividad Comercio', 'Sistema Contabilidad',
            'Actividad(es) Económica', 'Comprobantes de Pago', 'Emisor electrónico'
        ]
        
        domicilio_limpio = domicilio
        for sep in separadores:
            if sep in domicilio_limpio:
                domicilio_limpio = domicilio_limpio.split(sep)[0].strip()
        
        # Remover saltos de línea y espacios extra
        domicilio_limpio = re.sub(r'\n+', ' ', domicilio_limpio)
        domicilio_limpio = re.sub(r'\s+', ' ', domicilio_limpio).strip()
        
        return domicilio_limpio


# Instancia singleton del servicio clean
sunat_service_clean = SUNATServiceClean()