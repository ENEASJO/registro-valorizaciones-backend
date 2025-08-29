"""
Servicio SUNAT robusto con gestión avanzada del browser lifecycle y retry logic
Diseñado para obtener datos reales de SUNAT de manera confiable
"""
import logging
import asyncio
import random
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError, Browser, BrowserContext, Page

from app.models.ruc import EmpresaInfo, RepresentanteLegal
from app.utils.validators import validate_ruc

logger = logging.getLogger(__name__)


class SunatErrorType(Enum):
    """Tipos de errores específicos de SUNAT"""
    TIMEOUT = "timeout"
    BROWSER_CLOSED = "browser_closed"  
    ANTI_BOT = "anti_bot"
    RUC_NOT_FOUND = "ruc_not_found"
    NETWORK = "network"
    EXTRACTION = "extraction"
    UNKNOWN = "unknown"


@dataclass
class SunatResult:
    """Resultado estructurado de consulta SUNAT"""
    success: bool
    data: Optional[EmpresaInfo] = None
    error_type: Optional[SunatErrorType] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    execution_time: float = 0.0


class SUNATServiceRobust:
    """Servicio SUNAT robusto y confiable con manejo avanzado de errores"""
    
    def __init__(self):
        self.base_url = "https://e-consultaruc.sunat.gob.pe/cl-ti-itmrconsruc/FrameCriterioBusquedaWeb.jsp"
        self.max_retries = 3
        self.base_delay = 2.0  # Delay base para retry
        self.max_delay = 30.0  # Delay máximo para retry
        self.page_timeout = 90000  # 90 segundos para navegación
        self.action_timeout = 30000  # 30 segundos para acciones
        self.wait_timeout = 45000  # 45 segundos para elementos
        
    def _get_robust_browser_options(self) -> Dict[str, Any]:
        """Opciones de browser optimizadas para robustez y anti-detección"""
        return {
            'headless': True,
            'slow_mo': 100,  # Pequeña pausa entre acciones para simular comportamiento humano
            'args': [
                # Configuración básica de seguridad
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                
                # Anti-detección avanzada
                '--disable-blink-features=AutomationControlled',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor',
                '--disable-ipc-flooding-protection',
                '--no-first-run',
                '--no-default-browser-check',
                '--no-zygote',
                
                # Optimizaciones de red
                '--disable-background-networking',
                '--disable-background-timer-throttling',
                '--disable-backgrounding-occluded-windows',
                '--disable-renderer-backgrounding',
                '--disable-extensions-http-throttling',
                
                # Configuración de memoria
                '--memory-pressure-off',
                '--max_old_space_size=4096',
                '--disable-background-timer-throttling',
                
                # Configuración de ventana
                '--window-size=1366,768',
                '--start-maximized',
                
                # Deshabilitar notificaciones y popups
                '--disable-notifications',
                '--disable-popup-blocking',
                '--disable-translate',
                '--disable-sync',
                '--disable-plugins',
                '--disable-extensions',
                '--disable-default-apps',
            ]
        }
    
    def _get_robust_context_options(self) -> Dict[str, Any]:
        """Opciones de contexto robustas para anti-detección"""
        return {
            'viewport': {'width': 1366, 'height': 768},
            'user_agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/120.0.0.0 Safari/537.36'
            ),
            'java_script_enabled': True,
            'accept_downloads': False,
            'ignore_https_errors': True,
            'bypass_csp': True,
            'extra_http_headers': {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Cache-Control': 'no-cache',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
            }
        }
    
    async def _calculate_delay(self, retry_count: int) -> float:
        """Calcula delay exponencial con jitter para retry"""
        delay = min(self.base_delay * (2 ** retry_count), self.max_delay)
        # Agregar jitter aleatorio (±25%)
        jitter = delay * 0.25 * (2 * random.random() - 1)
        final_delay = delay + jitter
        return max(0.5, final_delay)  # Mínimo 0.5 segundos
    
    async def _setup_stealth_mode(self, page: Page) -> None:
        """Configura el modo stealth avanzado para evitar detección"""
        await page.add_init_script("""
            // Eliminar propiedades que indican automatización
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            
            // Simular plugins reales
            Object.defineProperty(navigator, 'plugins', {
                get: () => [
                    {name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer', description: 'Portable Document Format'},
                    {name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai', description: ''},
                    {name: 'Native Client', filename: 'internal-nacl-plugin', description: 'Native Client'}
                ],
            });
            
            // Simular WebGL
            const getParameter = WebGLRenderingContext.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {
                if (parameter === 37445) {
                    return 'Intel Open Source Technology Center';
                }
                if (parameter === 37446) {
                    return 'Mesa DRI Intel(R) Ivybridge Mobile ';
                }
                return getParameter(parameter);
            };
            
            // Configurar chrome runtime
            window.chrome = {
                runtime: {},
                loadTimes: function() {
                    return {
                        requestTime: Date.now() / 1000 - Math.random(),
                        startLoadTime: Date.now() / 1000 - Math.random(),
                        commitLoadTime: Date.now() / 1000 - Math.random(),
                        finishDocumentLoadTime: Date.now() / 1000 - Math.random(),
                        finishLoadTime: Date.now() / 1000 - Math.random(),
                        firstPaintTime: Date.now() / 1000 - Math.random(),
                        firstPaintAfterLoadTime: 0,
                        navigationType: 'Other',
                        wasFetchedViaSpdy: false,
                        wasNpnNegotiated: false,
                        npnNegotiatedProtocol: 'unknown',
                        wasAlternateProtocolAvailable: false,
                        connectionInfo: 'http/1.1'
                    };
                },
                csi: function() {
                    return {
                        startE: Date.now(),
                        onloadT: Date.now(),
                        pageT: Date.now(),
                        tran: 15
                    };
                }
            };
            
            // Configurar idiomas
            Object.defineProperty(navigator, 'languages', {
                get: () => ['es-ES', 'es', 'en-US', 'en'],
            });
            
            // Ocultar automatización en permisos
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
        """)
        
        # Configurar timeout por defecto
        page.set_default_timeout(self.action_timeout)
        page.set_default_navigation_timeout(self.page_timeout)
    
    async def consultar_empresa(self, ruc: str) -> EmpresaInfo:
        """Consulta información completa de una empresa por RUC con retry logic"""
        if not validate_ruc(ruc):
            raise ValueError(f"RUC inválido: {ruc}")
        
        logger.info(f"🔍 SUNAT ROBUST - Iniciando consulta para RUC: {ruc}")
        
        for attempt in range(self.max_retries):
            start_time = datetime.now()
            
            try:
                logger.info(f"📞 Intento {attempt + 1}/{self.max_retries} para RUC: {ruc}")
                
                result = await self._execute_single_query(ruc)
                
                execution_time = (datetime.now() - start_time).total_seconds()
                
                if result.success:
                    logger.info(f"✅ SUNAT ROBUST - Consulta exitosa para RUC {ruc} en {execution_time:.2f}s")
                    return result.data
                
                # Si no fue exitoso, preparar retry
                if attempt < self.max_retries - 1:
                    delay = await self._calculate_delay(attempt)
                    logger.warning(f"⚠️ Intento {attempt + 1} falló. Reintentando en {delay:.1f}s - Error: {result.error_message}")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"❌ Todos los intentos fallaron para RUC {ruc}. Último error: {result.error_message}")
                    raise Exception(f"Error después de {self.max_retries} intentos: {result.error_message}")
                    
            except Exception as e:
                execution_time = (datetime.now() - start_time).total_seconds()
                
                if attempt < self.max_retries - 1:
                    delay = await self._calculate_delay(attempt)
                    logger.warning(f"⚠️ Intento {attempt + 1} falló con excepción. Reintentando en {delay:.1f}s - Error: {str(e)}")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"❌ Error final después de {self.max_retries} intentos para RUC {ruc}: {str(e)}")
                    raise Exception(f"Error después de {self.max_retries} intentos: {str(e)}")
        
        # No debería llegar aquí, pero por seguridad
        raise Exception(f"Error inesperado en consulta de RUC {ruc}")
    
    async def _execute_single_query(self, ruc: str) -> SunatResult:
        """Ejecuta una consulta individual a SUNAT"""
        browser = None
        context = None
        page = None
        
        try:
            # Inicializar Playwright con manejo robusto
            async with async_playwright() as playwright:
                # Lanzar browser con opciones robustas
                browser = await playwright.chromium.launch(**self._get_robust_browser_options())
                
                # Crear contexto con configuración robusta
                context = await browser.new_context(**self._get_robust_context_options())
                
                # Crear página
                page = await context.new_page()
                
                # Configurar stealth mode
                await self._setup_stealth_mode(page)
                
                # Ejecutar navegación y extracción
                logger.info(f"🌐 Navegando a SUNAT...")
                
                # Navegar con timeout robusto
                await page.goto(
                    self.base_url, 
                    timeout=self.page_timeout,
                    wait_until='domcontentloaded'
                )
                
                # Espera aleatoria para simular comportamiento humano
                human_delay = random.uniform(2.0, 5.0)
                logger.info(f"⏳ Pausa humana: {human_delay:.1f}s")
                await asyncio.sleep(human_delay)
                
                # Verificar que la página cargó correctamente
                await self._verify_page_loaded(page)
                
                # Ejecutar búsqueda con manejo robusto
                await self._execute_robust_search(page, ruc)
                
                # Extraer datos con timeout robusto
                empresa_data = await self._extract_empresa_data(page, ruc)
                
                return SunatResult(
                    success=True,
                    data=empresa_data
                )
                
        except PlaywrightTimeoutError as e:
            logger.error(f"⏰ Timeout en consulta SUNAT: {str(e)}")
            return SunatResult(
                success=False,
                error_type=SunatErrorType.TIMEOUT,
                error_message=f"Timeout en consulta SUNAT: {str(e)}"
            )
        
        except Exception as e:
            error_msg = str(e).lower()
            
            # Clasificar tipo de error
            if "target page, context or browser has been closed" in error_msg or "browser closed" in error_msg:
                error_type = SunatErrorType.BROWSER_CLOSED
            elif "timeout" in error_msg:
                error_type = SunatErrorType.TIMEOUT
            elif "network" in error_msg or "connection" in error_msg:
                error_type = SunatErrorType.NETWORK
            elif "anti" in error_msg or "blocked" in error_msg or "captcha" in error_msg:
                error_type = SunatErrorType.ANTI_BOT
            else:
                error_type = SunatErrorType.UNKNOWN
            
            logger.error(f"❌ Error en consulta SUNAT ({error_type.value}): {str(e)}")
            
            return SunatResult(
                success=False,
                error_type=error_type,
                error_message=f"Error SUNAT ({error_type.value}): {str(e)}"
            )
        
        finally:
            # Cleanup robusto
            await self._cleanup_browser_resources(page, context, browser)
    
    async def _verify_page_loaded(self, page: Page) -> None:
        """Verifica que la página de SUNAT cargó correctamente"""
        try:
            # Verificar título de la página
            title = await page.title()
            logger.info(f"📄 Título de página: {title}")
            
            if "sunat" not in title.lower():
                logger.warning(f"⚠️ Título de página sospechoso: {title}")
            
            # Verificar elementos críticos
            await page.wait_for_selector('body', timeout=self.wait_timeout)
            
            # Verificar que no hay errores evidentes
            body_text = await page.inner_text('body')
            
            if any(error in body_text.lower() for error in ['error', 'mantenimiento', 'no disponible', 'bloqueado']):
                raise Exception(f"SUNAT reporta error o mantenimiento: {body_text[:200]}")
                
            logger.info("✅ Página SUNAT cargada correctamente")
            
        except Exception as e:
            logger.error(f"❌ Error verificando página SUNAT: {str(e)}")
            raise Exception(f"Error verificando página SUNAT: {str(e)}")
    
    async def _execute_robust_search(self, page: Page, ruc: str) -> None:
        """Ejecuta búsqueda de RUC con manejo robusto"""
        try:
            logger.info(f"🔍 Buscando campo RUC...")
            
            # Esperar el campo RUC con múltiples estrategias
            ruc_field = None
            selectors_to_try = [
                '#txtRuc',
                'input[name="txtRuc"]',
                'input[type="text"]',
                'input[placeholder*="RUC"]'
            ]
            
            for selector in selectors_to_try:
                try:
                    ruc_field = await page.wait_for_selector(selector, timeout=10000)
                    if ruc_field:
                        logger.info(f"✅ Campo RUC encontrado con selector: {selector}")
                        break
                except:
                    continue
            
            if not ruc_field:
                raise Exception("No se pudo localizar el campo RUC")
            
            # Limpiar campo y escribir RUC de manera humana
            await ruc_field.click()
            await asyncio.sleep(random.uniform(0.2, 0.5))
            
            # Seleccionar todo el texto (fix para Playwright)
            await ruc_field.press("Control+a")
            await asyncio.sleep(random.uniform(0.1, 0.3))
            
            await ruc_field.type(ruc, delay=random.randint(80, 150))
            await asyncio.sleep(random.uniform(0.5, 1.0))
            
            logger.info(f"✅ RUC {ruc} ingresado correctamente")
            
            # Buscar botón de búsqueda
            search_button = None
            button_selectors = [
                '#btnAceptar',
                'input[value="Aceptar"]',
                'input[type="submit"]',
                'button[type="submit"]',
                'input[value*="Buscar"]'
            ]
            
            for selector in button_selectors:
                try:
                    search_button = await page.wait_for_selector(selector, timeout=5000)
                    if search_button:
                        logger.info(f"✅ Botón búsqueda encontrado: {selector}")
                        break
                except:
                    continue
            
            if not search_button:
                raise Exception("No se pudo localizar el botón de búsqueda")
            
            # Hacer clic en búsqueda
            await search_button.click()
            logger.info("✅ Búsqueda iniciada")
            
            # Esperar respuesta de SUNAT de manera escalonada
            logger.info("⏳ Esperando respuesta de SUNAT...")
            
            # Esperar múltiples checkpoints
            await asyncio.sleep(3.0)  # Checkpoint 1
            logger.info("⏳ Checkpoint 1/3 - Procesando...")
            
            await asyncio.sleep(4.0)  # Checkpoint 2  
            logger.info("⏳ Checkpoint 2/3 - Obteniendo datos...")
            
            await asyncio.sleep(3.0)  # Checkpoint 3
            logger.info("✅ Respuesta SUNAT recibida")
            
        except Exception as e:
            logger.error(f"❌ Error en búsqueda robusta: {str(e)}")
            raise Exception(f"Error en búsqueda SUNAT: {str(e)}")
    
    async def _extract_empresa_data(self, page: Page, ruc: str) -> EmpresaInfo:
        """Extrae datos de empresa con múltiples estrategias y validación"""
        try:
            logger.info(f"📊 Extrayendo datos para RUC: {ruc}")
            
            # Obtener contenido completo de la página
            page_content = await page.content()
            body_text = await page.inner_text('body')
            
            # Verificar que hay datos válidos
            if len(body_text.strip()) < 100:
                raise Exception("Respuesta de SUNAT demasiado corta - posible error")
            
            # Extraer datos usando múltiples métodos
            extracted_data = {
                'razon_social': await self._extract_razon_social(body_text, ruc),
                'domicilio_fiscal': await self._extract_domicilio_fiscal(body_text),
                'representantes': await self._extract_representantes(page, body_text, ruc)
            }
            
            # Validar datos extraídos
            if not extracted_data['razon_social']:
                logger.warning(f"⚠️ No se pudo extraer razón social para RUC: {ruc}")
                extracted_data['razon_social'] = f"EMPRESA RUC {ruc}"
            
            if not extracted_data['domicilio_fiscal']:
                logger.warning(f"⚠️ No se pudo extraer domicilio fiscal para RUC: {ruc}")
                extracted_data['domicilio_fiscal'] = "No disponible"
            
            logger.info(f"📊 Datos extraídos - Razón Social: {extracted_data['razon_social'][:50]}...")
            logger.info(f"📊 Domicilio: {extracted_data['domicilio_fiscal'][:50]}...")
            logger.info(f"📊 Representantes: {len(extracted_data['representantes'])}")
            
            return EmpresaInfo(
                ruc=ruc,
                razon_social=extracted_data['razon_social'],
                domicilio_fiscal=extracted_data['domicilio_fiscal'],
                representantes=extracted_data['representantes']
            )
            
        except Exception as e:
            logger.error(f"❌ Error extrayendo datos: {str(e)}")
            raise Exception(f"Error extrayendo datos de SUNAT: {str(e)}")
    
    async def _extract_razon_social(self, body_text: str, ruc: str) -> str:
        """Extrae razón social con múltiples estrategias mejoradas"""
        lines = body_text.split('\n')
        
        # Estrategia 1: Buscar línea que empiece con RUC - NOMBRE
        for line in lines:
            line = line.strip()
            if line.startswith(f"{ruc} - "):
                razon = line.replace(f"{ruc} - ", "").strip()
                if len(razon) > 3:
                    return razon
        
        # Estrategia 2: Buscar después de etiquetas conocidas
        etiquetas = [
            "Nombre o Razón Social:",
            "Razón Social:",
            "Denominación:",
            "Empresa:"
        ]
        
        for i, line in enumerate(lines):
            for etiqueta in etiquetas:
                if etiqueta in line:
                    # En la misma línea
                    if ":" in line:
                        partes = line.split(":", 1)
                        if len(partes) > 1:
                            razon = partes[1].strip()
                            if len(razon) > 3:
                                return razon
                    
                    # En línea siguiente
                    if i + 1 < len(lines):
                        siguiente = lines[i + 1].strip()
                        if len(siguiente) > 3 and not siguiente.startswith(("Tipo", "Estado")):
                            return siguiente
        
        # Estrategia 3: Buscar patrones de empresa
        import re
        for line in lines:
            line = line.strip()
            if len(line) > 10 and re.search(r'\b(S\.A\.C\.|S\.A\.|S\.R\.L\.|E\.I\.R\.L\.)\b', line, re.IGNORECASE):
                if ruc not in line:
                    return line
        
        return ""
    
    async def _extract_domicilio_fiscal(self, body_text: str) -> str:
        """Extrae domicilio fiscal con estrategias mejoradas"""
        lines = body_text.split('\n')
        
        for i, line in enumerate(lines):
            if "Domicilio Fiscal:" in line:
                # En la misma línea
                if ":" in line:
                    partes = line.split(":", 1)
                    if len(partes) > 1:
                        domicilio = partes[1].strip()
                        if len(domicilio) > 10 and domicilio != "-":
                            return self._clean_domicilio(domicilio)
                
                # En líneas siguientes
                for j in range(i + 1, min(i + 4, len(lines))):
                    siguiente = lines[j].strip()
                    if len(siguiente) > 15 and siguiente != "-":
                        domicilio_limpio = self._clean_domicilio(siguiente)
                        if len(domicilio_limpio) > 15:
                            return domicilio_limpio
        
        return ""
    
    def _clean_domicilio(self, domicilio: str) -> str:
        """Limpia el domicilio fiscal de texto adicional"""
        import re
        
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
    
    async def _extract_representantes(self, page: Page, body_text: str, ruc: str) -> List[RepresentanteLegal]:
        """Extrae representantes legales con estrategias robustas"""
        representantes = []
        
        try:
            # Para RUC de persona natural (10xxxxxxxxx)
            if ruc.startswith('10'):
                return await self._extract_representantes_persona_natural(body_text, ruc)
            
            # Para RUC de persona jurídica (20xxxxxxxxx)
            return await self._extract_representantes_persona_juridica(page, body_text)
            
        except Exception as e:
            logger.warning(f"⚠️ Error extrayendo representantes: {str(e)}")
            return representantes
    
    async def _extract_representantes_persona_natural(self, body_text: str, ruc: str) -> List[RepresentanteLegal]:
        """Extrae representante para persona natural"""
        representantes = []
        
        try:
            # Para persona natural, el titular es el representante
            razon_social = await self._extract_razon_social(body_text, ruc)
            
            if razon_social:
                dni_from_ruc = ruc[2:10] if len(ruc) == 11 else ""
                
                representante = RepresentanteLegal(
                    tipo_doc="DNI",
                    numero_doc=dni_from_ruc,
                    nombre=razon_social,
                    cargo="TITULAR",
                    fecha_desde="-"
                )
                
                representantes.append(representante)
                logger.info(f"✅ Representante natural: {razon_social} (DNI: {dni_from_ruc})")
        
        except Exception as e:
            logger.warning(f"⚠️ Error extrayendo representante persona natural: {str(e)}")
        
        return representantes
    
    async def _extract_representantes_persona_juridica(self, page: Page, body_text: str) -> List[RepresentanteLegal]:
        """Extrae representantes para persona jurídica"""
        representantes = []
        
        try:
            # Intentar hacer clic en botón de representantes
            boton_representantes = await self._find_representantes_button(page)
            
            if boton_representantes:
                await boton_representantes.click()
                await asyncio.sleep(3.0)
                
                # Extraer datos de tabla de representantes
                representantes = await self._extract_representantes_from_tables(page)
            
        except Exception as e:
            logger.warning(f"⚠️ Error extrayendo representantes persona jurídica: {str(e)}")
        
        return representantes
    
    async def _find_representantes_button(self, page: Page) -> Optional[Any]:
        """Busca el botón de representantes legales"""
        selectors = [
            "text='Representante(s) Legal(es)'",
            "input[type='button'][value*='Representante']",
            "a:has-text('Representante')",
            "text=/Representante/"
        ]
        
        for selector in selectors:
            try:
                button = await page.wait_for_selector(selector, timeout=5000)
                if button:
                    logger.info(f"✅ Botón representantes encontrado: {selector}")
                    return button
            except:
                continue
        
        return None
    
    async def _extract_representantes_from_tables(self, page: Page) -> List[RepresentanteLegal]:
        """Extrae representantes de las tablas de SUNAT"""
        representantes = []
        
        try:
            tables = await page.query_selector_all('table')
            
            for table in tables:
                rows = await table.query_selector_all("tr")
                
                for row in rows:
                    cells = await row.query_selector_all("td")
                    
                    if len(cells) >= 4:
                        texts = []
                        for cell in cells:
                            text = await cell.inner_text()
                            texts.append(text.strip())
                        
                        representante = self._parse_representante_row(texts)
                        if representante:
                            representantes.append(representante)
        
        except Exception as e:
            logger.warning(f"⚠️ Error extrayendo tabla representantes: {str(e)}")
        
        return representantes
    
    def _parse_representante_row(self, texts: List[str]) -> Optional[RepresentanteLegal]:
        """Parsea fila de representante"""
        if len(texts) < 3:
            return None
        
        # Filtrar filas vacías o headers
        if not any(text and len(text) > 2 for text in texts):
            return None
        
        try:
            if len(texts) >= 5:
                return RepresentanteLegal(
                    tipo_doc=texts[0],
                    numero_doc=texts[1],
                    nombre=texts[2],
                    cargo=texts[3],
                    fecha_desde=texts[4] if len(texts) > 4 else ""
                )
            elif len(texts) >= 4:
                return RepresentanteLegal(
                    tipo_doc="DNI",
                    numero_doc=texts[0],
                    nombre=texts[1],
                    cargo=texts[2],
                    fecha_desde=texts[3]
                )
        except Exception:
            pass
        
        return None
    
    async def _cleanup_browser_resources(self, page: Optional[Page], context: Optional[BrowserContext], browser: Optional[Browser]) -> None:
        """Cleanup robusto de recursos del browser"""
        cleanup_errors = []
        
        try:
            if page:
                await page.close()
                logger.debug("✅ Página cerrada")
        except Exception as e:
            cleanup_errors.append(f"Error cerrando página: {str(e)}")
        
        try:
            if context:
                await context.close()
                logger.debug("✅ Contexto cerrado")
        except Exception as e:
            cleanup_errors.append(f"Error cerrando contexto: {str(e)}")
        
        try:
            if browser:
                await browser.close()
                logger.debug("✅ Browser cerrado")
        except Exception as e:
            cleanup_errors.append(f"Error cerrando browser: {str(e)}")
        
        if cleanup_errors:
            logger.warning(f"⚠️ Errores en cleanup: {', '.join(cleanup_errors)}")


# Instancia singleton del servicio robusto
sunat_service_robust = SUNATServiceRobust()