"""
Servicio OSCE optimizado para AWS Lambda Container
Versión especializada para web scraping OSCE en entorno serverless
"""
import logging
import re
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

from app.models.osce import EmpresaOSCE, IntegranteOSCE, EspecialidadOSCE, ContactoOSCE
from app.utils.exceptions import BaseAppException, ValidationException, ExtractionException

# Importar configuración Lambda si está disponible
try:
    from lambda_config import (
        LambdaPlaywrightConfig, 
        OSCEScrapingConfig,
        LambdaOptimizations
    )
    LAMBDA_CONFIG_AVAILABLE = True
except ImportError:
    LAMBDA_CONFIG_AVAILABLE = False

logger = logging.getLogger(__name__)


class OSCEServiceLambda:
    """Servicio OSCE optimizado para AWS Lambda Container"""
    
    def __init__(self):
        self.base_url = OSCEScrapingConfig.BASE_URL if LAMBDA_CONFIG_AVAILABLE else "https://apps.osce.gob.pe/perfilprov-ui/"
        
        # Configuración según ambiente
        if os.getenv('AWS_LAMBDA_FUNCTION_NAME'):
            self.is_lambda = True
            self.timeout = int(os.getenv('OSCE_TIMEOUT', '25000'))
            self.search_timeout = 8000
            self.browser_config = LambdaPlaywrightConfig.get_browser_config() if LAMBDA_CONFIG_AVAILABLE else self._get_basic_config()
        else:
            self.is_lambda = False
            self.timeout = 30000
            self.search_timeout = 5000
            self.browser_config = self._get_basic_config()
            
        logger.info(f"🔧 OSCE Service inicializado - Lambda: {self.is_lambda}")
        
    def _get_basic_config(self):
        """Configuración básica sin Lambda optimizations"""
        return {
            "headless": True,
            "args": ['--no-sandbox', '--disable-dev-shm-usage', '--disable-blink-features=AutomationControlled']
        }
        
    async def consultar_empresa(self, ruc: str) -> EmpresaOSCE:
        """
        Consulta información completa de una empresa en OSCE
        Versión optimizada para Lambda
        """
        logger.info(f"=== INICIANDO CONSULTA OSCE LAMBDA PARA RUC: {ruc} ===")
        
        # Validar RUC
        if not self._validar_ruc(ruc):
            logger.error(f"RUC inválido: {ruc}")
            raise ValidationException(f"RUC inválido: {ruc}")
        
        logger.info(f"RUC {ruc} validado correctamente")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(**self.browser_config)
            
            try:
                # Crear contexto optimizado
                if LAMBDA_CONFIG_AVAILABLE:
                    context = await browser.new_context(**LambdaPlaywrightConfig.get_context_config())
                else:
                    context = await browser.new_context(
                        viewport={'width': 1280, 'height': 720},
                        user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                    )
                
                page = await context.new_page()
                
                # Configurar timeouts
                if LAMBDA_CONFIG_AVAILABLE:
                    page_config = LambdaPlaywrightConfig.get_page_config()
                    page.set_default_navigation_timeout(page_config["default_navigation_timeout"])
                    page.set_default_timeout(page_config["default_timeout"])
                else:
                    page.set_default_timeout(self.timeout)
                
                # Navegar a OSCE con reintentos
                await self._navegar_con_reintentos(page)
                
                # Realizar búsqueda inicial
                await self._ejecutar_busqueda_inicial_optimizada(page, ruc)
                
                # Buscar el enlace al perfil detallado
                perfil_url = await self._buscar_enlace_perfil_optimizado(page, ruc)
                
                if perfil_url:
                    logger.info(f"Navegando al perfil detallado: {perfil_url}")
                    await page.goto(perfil_url, timeout=self.timeout, wait_until='domcontentloaded')
                    await page.wait_for_timeout(3000)
                
                # Extraer datos completos
                empresa_data = await self._extraer_datos_completos_optimizado(page, ruc)
                
                logger.info(f"Consulta OSCE Lambda completada exitosamente para RUC: {ruc}")
                return empresa_data
                
            except PlaywrightTimeoutError as e:
                logger.error(f"Timeout en consulta OSCE Lambda para RUC {ruc}: {str(e)}")
                raise ExtractionException(f"Timeout al consultar OSCE: {str(e)}")
                
            except Exception as e:
                logger.error(f"Error en consulta OSCE Lambda para RUC {ruc}: {str(e)}")
                
                # Screenshot para debug en desarrollo
                if os.getenv('DEBUG', 'false').lower() == 'true':
                    try:
                        await page.screenshot(path=f'/tmp/error_osce_{ruc}.png')
                        logger.info(f"📸 Screenshot OSCE guardado: /tmp/error_osce_{ruc}.png")
                    except:
                        pass
                        
                raise ExtractionException(f"Error al consultar OSCE: {str(e)}")
                
            finally:
                try:
                    await context.close()
                except:
                    pass
                await browser.close()
    
    async def _navegar_con_reintentos(self, page, max_intentos=3):
        """Navegar a OSCE con reintentos"""
        for intento in range(max_intentos):
            try:
                logger.info(f"Navegando a página principal de OSCE (intento {intento + 1})")
                await page.goto(self.base_url, timeout=self.timeout, wait_until='domcontentloaded')
                await page.wait_for_timeout(3000)
                return
            except Exception as e:
                if intento == max_intentos - 1:
                    raise
                logger.warning(f"Error navegando (intento {intento + 1}): {e}")
                await page.wait_for_timeout(2000)
    
    async def _ejecutar_busqueda_inicial_optimizada(self, page, ruc: str):
        """Ejecutar búsqueda inicial con estrategias múltiples"""
        logger.info(f"🔍 Ejecutando búsqueda optimizada para RUC: {ruc}")
        
        # Estrategias de búsqueda
        search_strategies = [
            # Estrategia 1: Buscar input por placeholder
            {
                "input_selector": "input[placeholder*='RUC']",
                "button_selector": "button:has-text('Buscar')",
                "name": "placeholder RUC"
            },
            # Estrategia 2: Buscar input por tipo
            {
                "input_selector": "input[type='text']",
                "button_selector": "button[type='submit']",
                "name": "input tipo texto"
            },
            # Estrategia 3: Buscar cualquier input visible
            {
                "input_selector": "input:visible",
                "button_selector": "button:visible",
                "name": "input visible"
            }
        ]
        
        for strategy in search_strategies:
            try:
                # Buscar input
                input_element = await page.query_selector(strategy["input_selector"])
                if not input_element:
                    continue
                
                # Limpiar y llenar
                await input_element.clear()
                await input_element.fill(ruc)
                await page.wait_for_timeout(1000)
                
                # Buscar botón y hacer click
                button_element = await page.query_selector(strategy["button_selector"])
                if button_element:
                    await button_element.click()
                else:
                    # Alternativa: presionar Enter
                    await input_element.press('Enter')
                
                # Esperar resultados
                await page.wait_for_timeout(self.search_timeout)
                
                logger.info(f"✅ Búsqueda exitosa con estrategia: {strategy['name']}")
                return
                
            except Exception as e:
                logger.warning(f"⚠️ Estrategia {strategy['name']} falló: {e}")
                continue
        
        # Si todas las estrategias fallan, lanzar excepción
        raise ExtractionException("No se pudo ejecutar búsqueda en OSCE")
    
    async def _buscar_enlace_perfil_optimizado(self, page, ruc: str) -> Optional[str]:
        """Buscar enlace al perfil con múltiples estrategias"""
        logger.info(f"🔍 Buscando enlace al perfil para RUC: {ruc}")
        
        # Estrategias para encontrar el enlace
        link_strategies = [
            f"a[href*='{ruc}']",
            f"a[href*='/perfil/']",
            f"a:has-text('{ruc}')",
            "a:has-text('Ver perfil')",
            "a:has-text('Detalle')",
            ".resultado a",
            ".empresa-link a",
            "tr a"  # Enlaces en tabla de resultados
        ]
        
        for strategy in link_strategies:
            try:
                links = await page.query_selector_all(strategy)
                for link in links:
                    href = await link.get_attribute('href')
                    if href and ('perfil' in href.lower() or ruc in href):
                        full_url = href if href.startswith('http') else f"{self.base_url.rstrip('/')}{href}"
                        logger.info(f"✅ Enlace encontrado con estrategia {strategy}: {full_url}")
                        return full_url
                        
            except Exception as e:
                logger.warning(f"⚠️ Error con estrategia {strategy}: {e}")
                continue
        
        logger.warning("⚠️ No se encontró enlace al perfil detallado")
        return None
    
    async def _extraer_datos_completos_optimizado(self, page, ruc: str) -> EmpresaOSCE:
        """Extraer datos completos con optimizaciones Lambda"""
        logger.info(f"📊 Extrayendo datos completos para RUC: {ruc}")
        
        try:
            # Obtener texto completo de la página
            page_content = await page.inner_text('body')
            
            # Extraer información básica
            razon_social = await self._extraer_razon_social_optimizada(page, page_content, ruc)
            estado_registro = await self._extraer_estado_registro_optimizado(page_content)
            
            # Extraer contacto
            telefono = await self._extraer_telefono_optimizado(page_content)
            email = await self._extraer_email_optimizado(page_content)
            
            # Extraer especialidades
            especialidades = await self._extraer_especialidades_optimizado(page)
            
            # Extraer integrantes
            integrantes = await self._extraer_integrantes_optimizado(page)
            
            # Extraer información adicional
            vigencia = await self._extraer_vigencia_optimizado(page_content)
            capacidad_contratacion = await self._extraer_capacidad_contratacion_optimizada(page_content)
            
            # Crear objeto EmpresaOSCE
            empresa_data = EmpresaOSCE(
                ruc=ruc,
                fuente="OSCE",
                razon_social=razon_social,
                estado_registro=estado_registro,
                telefono=telefono,
                email=email,
                especialidades=especialidades,
                integrantes=integrantes,
                total_especialidades=len(especialidades),
                total_integrantes=len(integrantes),
                vigencia=vigencia,
                capacidad_contratacion=capacidad_contratacion
            )
            
            logger.info(f"✅ Datos extraídos: {len(especialidades)} especialidades, {len(integrantes)} integrantes")
            return empresa_data
            
        except Exception as e:
            logger.error(f"❌ Error extrayendo datos completos: {str(e)}")
            
            # Crear objeto mínimo en caso de error
            return EmpresaOSCE(
                ruc=ruc,
                fuente="OSCE",
                razon_social="Error al extraer",
                estado_registro="DESCONOCIDO",
                telefono="",
                email="",
                especialidades=[],
                integrantes=[],
                total_especialidades=0,
                total_integrantes=0,
                vigencia="",
                capacidad_contratacion=""
            )
    
    async def _extraer_razon_social_optimizada(self, page, page_content: str, ruc: str) -> str:
        """Extraer razón social con múltiples estrategias"""
        # Estrategia 1: Buscar en encabezados
        selectors = [
            "h1", "h2", ".company-name", ".empresa-nombre", 
            ".razon-social", "[data-field='razon_social']"
        ]
        
        for selector in selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    text = await element.inner_text()
                    text = text.strip()
                    if len(text) > 5 and ruc not in text:
                        return text
            except:
                continue
        
        # Estrategia 2: Buscar en texto usando patrones
        lines = page_content.split('\n')
        for line in lines:
            line = line.strip()
            if len(line) > 10 and any(keyword in line.lower() for keyword in ['razón social', 'empresa', 'denominación']):
                if ':' in line:
                    parts = line.split(':', 1)
                    if len(parts) > 1:
                        razon = parts[1].strip()
                        if len(razon) > 5:
                            return razon
        
        return "No disponible"
    
    async def _extraer_estado_registro_optimizado(self, page_content: str) -> str:
        """Extraer estado de registro"""
        estados = ['HABILITADO', 'ACTIVO', 'VIGENTE', 'SUSPENDIDO', 'INHABILITADO']
        
        for estado in estados:
            if estado in page_content.upper():
                return estado
        
        return "DESCONOCIDO"
    
    async def _extraer_telefono_optimizado(self, page_content: str) -> str:
        """Extraer teléfono usando regex"""
        import re
        
        # Patrones de teléfono peruano
        phone_patterns = [
            r'(?:Teléfono|Tel|Phone):\s*([+\d\s\-()]{7,15})',
            r'(\+51\s*\d{2,3}\s*\d{3}\s*\d{3,4})',
            r'(\d{2,3}-\d{3}-\d{3,4})',
            r'(\d{7,9})'
        ]
        
        for pattern in phone_patterns:
            match = re.search(pattern, page_content, re.IGNORECASE)
            if match:
                telefono = match.group(1).strip()
                if len(telefono) >= 7:
                    return telefono
        
        return ""
    
    async def _extraer_email_optimizado(self, page_content: str) -> str:
        """Extraer email usando regex"""
        import re
        
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        match = re.search(email_pattern, page_content)
        
        if match:
            return match.group(0)
        
        return ""
    
    async def _extraer_especialidades_optimizado(self, page) -> List[EspecialidadOSCE]:
        """Extraer especialidades con selectors optimizados"""
        especialidades = []
        
        # Selectores para buscar especialidades
        selectors = [
            ".especialidad", ".specialty", ".especialidades .item",
            "table tr", ".list-item", ".categoria"
        ]
        
        for selector in selectors:
            try:
                elements = await page.query_selector_all(selector)
                for element in elements:
                    text = await element.inner_text()
                    text = text.strip()
                    
                    if len(text) > 3 and self._es_especialidad_valida(text):
                        especialidad = EspecialidadOSCE(
                            codigo="",
                            nombre=text,
                            categoria="GENERAL"
                        )
                        especialidades.append(especialidad)
                        
                        if len(especialidades) >= 20:  # Limitar para Lambda
                            break
                            
            except Exception as e:
                logger.warning(f"Error extrayendo especialidades con selector {selector}: {e}")
                continue
        
        return especialidades
    
    async def _extraer_integrantes_optimizado(self, page) -> List[IntegranteOSCE]:
        """Extraer integrantes con selectors optimizados"""
        integrantes = []
        
        # Buscar tablas de integrantes
        try:
            tables = await page.query_selector_all('table')
            
            for table in tables:
                rows = await table.query_selector_all('tr')
                
                for row in rows:
                    cells = await row.query_selector_all('td')
                    if len(cells) >= 3:
                        try:
                            textos = []
                            for cell in cells:
                                texto = await cell.inner_text()
                                textos.append(texto.strip())
                            
                            if self._es_fila_integrante_valida(textos):
                                integrante = self._crear_integrante_desde_fila(textos)
                                if integrante:
                                    integrantes.append(integrante)
                                    
                        except Exception as e:
                            continue
                            
                if len(integrantes) >= 15:  # Limitar para Lambda
                    break
                    
        except Exception as e:
            logger.warning(f"Error extrayendo integrantes: {e}")
        
        return integrantes
    
    def _es_especialidad_valida(self, texto: str) -> bool:
        """Validar si el texto es una especialidad válida"""
        if not texto or len(texto) < 3:
            return False
            
        # Filtrar headers y texto no válido
        headers_invalidos = [
            'ESPECIALIDAD', 'NOMBRE', 'CÓDIGO', 'CATEGORIA',
            'HEADER', 'TITLE', 'ENCABEZADO'
        ]
        
        return texto.upper() not in headers_invalidos
    
    def _es_fila_integrante_valida(self, textos: List[str]) -> bool:
        """Validar si la fila contiene datos de integrante"""
        if len(textos) < 2:
            return False
            
        # Debe tener al menos un nombre válido
        for texto in textos:
            if len(texto) > 5 and any(char.isalpha() for char in texto):
                return True
                
        return False
    
    def _crear_integrante_desde_fila(self, textos: List[str]) -> Optional[IntegranteOSCE]:
        """Crear integrante desde fila de tabla"""
        try:
            # Formato típico: [Nombre, Cargo, Participación, Documento]
            nombre = textos[0] if len(textos) > 0 else ""
            cargo = textos[1] if len(textos) > 1 else ""
            participacion = textos[2] if len(textos) > 2 else ""
            documento = textos[3] if len(textos) > 3 else ""
            
            if len(nombre) > 3:
                return IntegranteOSCE(
                    nombre=nombre,
                    cargo=cargo,
                    participacion=participacion,
                    tipo_documento="DNI" if documento.isdigit() else "OTRO",
                    numero_documento=documento
                )
                
        except Exception as e:
            logger.warning(f"Error creando integrante: {e}")
            
        return None
    
    async def _extraer_vigencia_optimizado(self, page_content: str) -> str:
        """Extraer información de vigencia"""
        import re
        
        vigencia_patterns = [
            r'Vigencia:?\s*([^\n]+)',
            r'Válido hasta:?\s*([^\n]+)',
            r'Vence:?\s*([^\n]+)'
        ]
        
        for pattern in vigencia_patterns:
            match = re.search(pattern, page_content, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return ""
    
    async def _extraer_capacidad_contratacion_optimizada(self, page_content: str) -> str:
        """Extraer capacidad de contratación"""
        import re
        
        capacidad_patterns = [
            r'Capacidad[^:]*:?\s*([^\n]+)',
            r'Contratación[^:]*:?\s*([^\n]+)',
            r'Monto[^:]*:?\s*([^\n]+)'
        ]
        
        for pattern in capacidad_patterns:
            match = re.search(pattern, page_content, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return ""
    
    def _validar_ruc(self, ruc: str) -> bool:
        """Validar formato de RUC"""
        if not ruc or len(ruc) != 11:
            return False
            
        if not ruc.isdigit():
            return False
            
        if not ruc.startswith(('10', '20')):
            return False
            
        return True


# Instancia singleton del servicio optimizado para Lambda
osce_service_lambda = OSCEServiceLambda()