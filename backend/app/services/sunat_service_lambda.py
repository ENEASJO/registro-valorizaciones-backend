"""
Servicio SUNAT optimizado para AWS Lambda Container
Versión especializada para web scraping en entorno serverless
"""
import asyncio
import os
from typing import List, Optional, Dict, Any
from playwright.async_api import async_playwright, Browser, Page, TimeoutError
import logging

from app.models.ruc import EmpresaInfo, RepresentanteLegal
from app.utils.validators import validate_ruc

# Importar configuración Lambda si está disponible
try:
    from lambda_config import (
        LambdaPlaywrightConfig, 
        SUNATScrapingConfig,
        LambdaOptimizations
    )
    LAMBDA_CONFIG_AVAILABLE = True
except ImportError:
    LAMBDA_CONFIG_AVAILABLE = False

logger = logging.getLogger(__name__)


class SUNATServiceLambda:
    """Servicio SUNAT optimizado para AWS Lambda Container"""
    
    def __init__(self):
        self.base_url = SUNATScrapingConfig.BASE_URL if LAMBDA_CONFIG_AVAILABLE else "https://e-consultaruc.sunat.gob.pe/cl-ti-itmrconsruc/FrameCriterioBusquedaWeb.jsp"
        
        # Configuración según ambiente
        if os.getenv('AWS_LAMBDA_FUNCTION_NAME'):
            self.is_lambda = True
            self.timeout = int(os.getenv('SUNAT_TIMEOUT', '20000'))
            self.browser_config = LambdaPlaywrightConfig.get_browser_config() if LAMBDA_CONFIG_AVAILABLE else self._get_basic_config()
        else:
            self.is_lambda = False
            self.timeout = 30000
            self.browser_config = self._get_basic_config()
        
        logger.info(f"🔧 SUNAT Service inicializado - Lambda: {self.is_lambda}")
        
    def _get_basic_config(self):
        """Configuración básica sin Lambda optimizations"""
        return {
            "headless": True,
            "args": ['--no-sandbox', '--disable-dev-shm-usage']
        }
        
    async def consultar_empresa(self, ruc: str) -> EmpresaInfo:
        """
        Consultar información completa de una empresa por RUC
        Versión optimizada para Lambda
        """
        # Validar RUC
        if not validate_ruc(ruc):
            raise ValueError(f"RUC inválido: {ruc}")
        
        logger.info(f"🔍 [Lambda-SUNAT] Consultando RUC: {ruc}")
        
        # Configuración específica por tipo de RUC
        config = SUNATScrapingConfig.get_extraction_config(ruc) if LAMBDA_CONFIG_AVAILABLE else {
            "es_persona_natural": ruc.startswith('10'),
            "timeout_navigation": 15000,
            "timeout_after_submit": 3000,
            "retry_attempts": 2
        }
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(**self.browser_config)
            
            try:
                # Crear contexto optimizado
                if LAMBDA_CONFIG_AVAILABLE:
                    context = await browser.new_context(**LambdaPlaywrightConfig.get_context_config())
                else:
                    context = await browser.new_context(
                        user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                    )
                
                page = await context.new_page()
                
                if LAMBDA_CONFIG_AVAILABLE:
                    page_config = LambdaPlaywrightConfig.get_page_config()
                    page.set_default_navigation_timeout(page_config["default_navigation_timeout"])
                    page.set_default_timeout(page_config["default_timeout"])
                else:
                    page.set_default_timeout(self.timeout)
                
                # Obtener información con reintentos
                for attempt in range(config["retry_attempts"]):
                    try:
                        # Obtener información básica
                        razon_social = await self._obtener_razon_social_optimizada(page, ruc, config)
                        
                        # Obtener domicilio fiscal
                        domicilio_fiscal = await self._obtener_domicilio_fiscal_optimizada(page, config)
                        
                        # Obtener representantes legales
                        representantes = await self._obtener_representantes_legales_optimizada(page, config)
                        
                        resultado = EmpresaInfo(
                            ruc=ruc,
                            razon_social=razon_social,
                            domicilio_fiscal=domicilio_fiscal,
                            representantes=representantes
                        )
                        
                        logger.info(f"📊 [Lambda-SUNAT] Consulta exitosa para RUC {ruc}: {len(representantes)} representantes")
                        return resultado
                        
                    except Exception as e:
                        logger.warning(f"⚠️ [Lambda-SUNAT] Intento {attempt + 1} falló para RUC {ruc}: {str(e)}")
                        if attempt == config["retry_attempts"] - 1:
                            raise
                        await asyncio.sleep(1)  # Breve pausa entre reintentos
                        
            except Exception as e:
                logger.error(f"❌ [Lambda-SUNAT] Error consultando RUC {ruc}: {str(e)}")
                
                # Screenshot para debug solo en desarrollo
                if os.getenv("DEBUG", "false").lower() == "true":
                    try:
                        await page.screenshot(path=f"/tmp/error_sunat_{ruc}.png")
                        logger.info(f"📸 Screenshot guardado: /tmp/error_sunat_{ruc}.png")
                    except:
                        pass
                        
                raise
                
            finally:
                try:
                    await context.close()
                except:
                    pass
                await browser.close()
    
    async def _obtener_razon_social_optimizada(self, page: Page, ruc: str, config: Dict) -> str:
        """Obtener razón social con optimizaciones para Lambda"""
        try:
            # Navegar con timeout específico
            await page.goto(self.base_url, timeout=config["timeout_navigation"])
            
            # Llenar formulario
            await page.fill('#txtRuc', ruc)
            await page.click('#btnAceptar')
            await page.wait_for_timeout(config["timeout_after_submit"])
            
            # Extraer según tipo de persona
            if config["es_persona_natural"]:
                return await self._extraer_nombre_persona_natural(page, ruc)
            else:
                return await self._extraer_razon_social_persona_juridica(page, ruc)
                
        except Exception as e:
            logger.error(f"❌ [Lambda-SUNAT] Error obteniendo razón social: {str(e)}")
            return ""
    
    async def _obtener_domicilio_fiscal_optimizada(self, page: Page, config: Dict) -> str:
        """Obtener domicilio fiscal optimizado"""
        try:
            # Método optimizado usando texto completo de la página
            page_text = await page.inner_text('body')
            lines = page_text.split('\n')
            
            patterns = SUNATScrapingConfig.TEXT_PATTERNS["domicilio_fiscal"] if LAMBDA_CONFIG_AVAILABLE else ["Domicilio Fiscal:", "DOMICILIO FISCAL:"]
            
            for i, line in enumerate(lines):
                line = line.strip()
                if any(pattern in line for pattern in patterns):
                    logger.info(f"✅ Encontrada línea con domicilio fiscal: {line}")
                    
                    # Si el domicilio está en la misma línea
                    if ":" in line:
                        parts = line.split(":", 1)
                        if len(parts) > 1 and parts[1].strip():
                            domicilio = parts[1].strip()
                            if len(domicilio) > 2 and domicilio != "-":
                                return domicilio
                    
                    # Buscar en líneas siguientes
                    for offset in [1, 2]:
                        if i + offset < len(lines):
                            siguiente_linea = lines[i + offset].strip()
                            if siguiente_linea == "-":
                                return "No registrado"
                            elif siguiente_linea and len(siguiente_linea) > 10:
                                if not any(nav in siguiente_linea.lower() for nav in ['volver', 'imprimir', 'email', 'consulta', 'resultado']):
                                    return siguiente_linea
            
            return ""
            
        except Exception as e:
            logger.error(f"❌ [Lambda-SUNAT] Error obteniendo domicilio fiscal: {str(e)}")
            return ""
    
    async def _obtener_representantes_legales_optimizada(self, page: Page, config: Dict) -> List[RepresentanteLegal]:
        """Obtener representantes legales optimizado para Lambda"""
        representantes = []
        
        try:
            # Para personas naturales, crear representante basado en el RUC
            if config["es_persona_natural"]:
                page_text = await page.inner_text('body')
                nombre = await self._extraer_nombre_desde_texto(page_text)
                
                if nombre:
                    ruc = await self._extraer_ruc_desde_url(page)
                    dni = ruc[2:10] if len(ruc) >= 11 else ""
                    
                    representante = RepresentanteLegal(
                        tipo_doc="DNI",
                        numero_doc=dni,
                        nombre=nombre,
                        cargo="TITULAR",
                        fecha_desde="-"
                    )
                    representantes.append(representante)
                
                return representantes
            
            # Para personas jurídicas, buscar botón de representantes
            logger.info("🔍 [Lambda-SUNAT] Buscando representantes legales...")
            
            boton_encontrado = await self._clickear_boton_representantes_optimizado(page)
            
            if not boton_encontrado:
                logger.warning("⚠️ [Lambda-SUNAT] No se encontró botón de representantes")
                return representantes
            
            await page.wait_for_timeout(3000)
            representantes = await self._extraer_datos_tablas_optimizado(page)
            
            logger.info(f"📊 [Lambda-SUNAT] Total representantes extraídos: {len(representantes)}")
            return representantes
            
        except Exception as e:
            logger.error(f"⚠️ [Lambda-SUNAT] Error extrayendo representantes: {str(e)}")
            return representantes
    
    async def _clickear_boton_representantes_optimizado(self, page: Page) -> bool:
        """Clickear botón de representantes con múltiples estrategias"""
        strategies = [
            ("text", "text='Representante(s) Legal(es)'"),
            ("input", "input[type='button'][value*='Representante']"),
            ("link", "a:has-text('Representante')")
        ]
        
        for strategy_name, selector in strategies:
            try:
                await page.click(selector, timeout=5000)
                logger.info(f"✅ [Lambda-SUNAT] Botón clickeado con estrategia: {strategy_name}")
                return True
            except:
                continue
        
        return False
    
    async def _extraer_datos_tablas_optimizado(self, page: Page) -> List[RepresentanteLegal]:
        """Extraer datos de tablas con optimizaciones Lambda"""
        representantes = []
        
        try:
            tables = await page.query_selector_all('table')
            
            for table_idx, table in enumerate(tables):
                rows = await table.query_selector_all("tr")
                
                if len(rows) == 0:
                    continue
                
                # Verificar estructura de tabla
                primera_fila_celdas = await rows[0].query_selector_all("td, th")
                if len(primera_fila_celdas) < 3:
                    continue
                
                # Procesar filas
                for row in rows:
                    celdas = await row.query_selector_all("td")
                    if not celdas or len(celdas) < 3:
                        continue
                    
                    textos = []
                    for celda in celdas:
                        texto = (await celda.inner_text()).strip()
                        textos.append(texto)
                    
                    representante = self._procesar_fila_representante_optimizada(textos)
                    if representante:
                        representantes.append(representante)
            
            return representantes
            
        except Exception as e:
            logger.error(f"❌ [Lambda-SUNAT] Error extrayendo datos de tablas: {str(e)}")
            return representantes
    
    def _procesar_fila_representante_optimizada(self, textos: List[str]) -> Optional[RepresentanteLegal]:
        """Procesar fila de representante con validaciones mejoradas"""
        # Filtrar filas vacías
        if not any(texto and texto != "-" and len(texto) > 2 for texto in textos):
            return None
        
        # Determinar formato
        persona_data = {}
        
        if len(textos) >= 5:
            persona_data = {
                "tipo_doc": textos[0],
                "numero_doc": textos[1],
                "nombre": textos[2],
                "cargo": textos[3],
                "fecha_desde": textos[4]
            }
        elif len(textos) == 4:
            persona_data = {
                "tipo_doc": "DNI",
                "numero_doc": textos[0],
                "nombre": textos[1],
                "cargo": textos[2],
                "fecha_desde": textos[3]
            }
        elif len(textos) == 3:
            persona_data = {
                "tipo_doc": "-",
                "numero_doc": "-",
                "nombre": textos[0],
                "cargo": textos[1],
                "fecha_desde": textos[2]
            }
        else:
            return None
        
        # Validar nombre
        nombre = persona_data.get("nombre", "")
        if not self._es_nombre_valido(nombre):
            return None
        
        try:
            return RepresentanteLegal(**persona_data)
        except Exception as e:
            logger.warning(f"⚠️ [Lambda-SUNAT] Error creando representante: {str(e)}")
            return None
    
    def _es_nombre_valido(self, nombre: str) -> bool:
        """Validar nombre de representante"""
        if not nombre or len(nombre) < 3:
            return False
        
        headers_invalidos = [
            "NOMBRE", "APELLIDOS", "TIPO", "DOC", "CARGO", "FECHA",
            "DOCUMENTO", "REPRESENTANTE", "LEGAL", "DESDE"
        ]
        
        if nombre.upper() in headers_invalidos:
            return False
        
        if all(char == "-" for char in nombre):
            return False
        
        return True
    
    async def _extraer_nombre_persona_natural(self, page: Page, ruc: str) -> str:
        """Extraer nombre de persona natural"""
        try:
            page_text = await page.inner_text('body')
            lines = page_text.split('\n')
            
            for line in lines:
                line = line.strip()
                if line.startswith("DNI ") and " - " in line:
                    parts = line.split(" - ", 1)
                    if len(parts) > 1:
                        nombre_completo = parts[1].strip()
                        if len(nombre_completo) > 3:
                            return nombre_completo
            return ""
        except Exception:
            return ""
    
    async def _extraer_razon_social_persona_juridica(self, page: Page, ruc: str) -> str:
        """Extraer razón social de persona jurídica"""
        try:
            page_text = await page.inner_text('body')
            lines = page_text.split('\n')
            
            for line in lines:
                line = line.strip()
                if ruc in line and " - " in line:
                    parts = line.split(" - ", 1)
                    if len(parts) > 1:
                        razon_social = parts[1].strip()
                        if len(razon_social) > 5:
                            return razon_social
            return ""
        except Exception:
            return ""
    
    async def _extraer_nombre_desde_texto(self, page_text: str) -> str:
        """Extraer nombre desde texto de página"""
        lines = page_text.split('\n')
        for line in lines:
            line = line.strip()
            if "DNI " in line and " - " in line:
                parts = line.split(" - ", 1)
                if len(parts) > 1:
                    return parts[1].strip()
        return ""
    
    async def _extraer_ruc_desde_url(self, page: Page) -> str:
        """Extraer RUC desde URL o página actual"""
        try:
            url = page.url
            # Buscar RUC en la URL o contenido
            import re
            ruc_match = re.search(r'\b(10|20)\d{9}\b', url)
            if ruc_match:
                return ruc_match.group(0)
        except:
            pass
        return ""


# Instancia singleton del servicio optimizado para Lambda
sunat_service_lambda = SUNATServiceLambda()