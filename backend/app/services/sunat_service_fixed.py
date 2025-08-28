"""
Servicio para consultar información de empresas en SUNAT
Basado en la estructura exitosa de OSCE
"""
import logging
from typing import List, Optional, Dict, Any
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

from app.models.ruc import EmpresaInfo, RepresentanteLegal
from app.core.config import settings
from app.utils.validators import validate_ruc
from app.utils.playwright_helper import get_browser_launch_options

logger = logging.getLogger(__name__)


class SUNATServiceFixed:
    """Servicio para consultar información de empresas en SUNAT - versión mejorada basada en OSCE"""
    
    def __init__(self):
        self.base_url = "https://e-consultaruc.sunat.gob.pe/cl-ti-itmrconsruc/FrameCriterioBusquedaWeb.jsp"
        self.timeout = 60000  # 60 segundos como OSCE
        self.search_timeout = 10000  # 10 segundos como OSCE
        
    async def consultar_empresa(self, ruc: str) -> EmpresaInfo:
        """
        Consultar información completa de una empresa por RUC
        
        Args:
            ruc: RUC de la empresa a consultar
            
        Returns:
            EmpresaInfo: Información completa de la empresa
            
        Raises:
            ValueError: Si el RUC no es válido
            Exception: Si hay errores en la consulta
        """
        # Validar RUC
        if not validate_ruc(ruc):
            raise ValueError(f"RUC inválido: {ruc}")
        
        logger.info(f"🔍 SUNAT FIXED - Consultando RUC: {ruc}")
        
        async with async_playwright() as p:
            launch_options = get_browser_launch_options(headless=settings.HEADLESS_BROWSER)
            browser = await p.chromium.launch(**launch_options)
            
            try:
                # Configurar context exactamente como OSCE
                context = await browser.new_context(
                    viewport={'width': 1280, 'height': 720},
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
                
                page = await context.new_page()
                
                # Navegar con configuración igual a OSCE
                logger.info("🌐 Navegando a SUNAT...")
                await page.goto(self.base_url, timeout=self.timeout, wait_until='domcontentloaded')
                await page.wait_for_timeout(3000)
                
                # Ejecutar búsqueda
                await self._ejecutar_busqueda(page, ruc)
                
                # Extraer datos
                razon_social = await self._obtener_razon_social(page, ruc)
                domicilio_fiscal = await self._obtener_domicilio_fiscal(page, ruc)
                representantes = await self._obtener_representantes_legales(page)
                
                resultado = EmpresaInfo(
                    ruc=ruc,
                    razon_social=razon_social,
                    domicilio_fiscal=domicilio_fiscal,
                    representantes=representantes
                )
                
                logger.info(f"✅ SUNAT FIXED - Consulta exitosa para RUC {ruc}")
                return resultado
                
            except PlaywrightTimeoutError as e:
                logger.error(f"⏰ Timeout en SUNAT para RUC {ruc}: {str(e)}")
                raise Exception(f"Timeout al consultar SUNAT: {str(e)}")
                
            except Exception as e:
                logger.error(f"❌ Error en SUNAT para RUC {ruc}: {str(e)}")
                raise Exception(f"Error al consultar SUNAT: {str(e)}")
                
            finally:
                # Cleanup igual a OSCE - solo cerrar browser
                await browser.close()
    
    async def _ejecutar_busqueda(self, page, ruc: str):
        """Ejecuta la búsqueda inicial en SUNAT"""
        logger.info(f"🔍 Ejecutando búsqueda para RUC: {ruc}")
        
        # Llenar campo RUC
        await page.fill('#txtRuc', ruc)
        await page.click('#btnAceptar')
        await page.wait_for_timeout(5000)  # Mayor espera para que cargue
        
        logger.info("✅ Búsqueda completada")
    
    async def _obtener_razon_social(self, page, ruc: str) -> str:
        """Obtener la razón social de la empresa"""
        try:
            logger.info(f"📝 Buscando razón social para RUC: {ruc}")
            
            # Esperar a que la página cargue completamente
            await page.wait_for_load_state('domcontentloaded')
            await page.wait_for_timeout(2000)
            
            # Debug: mostrar contenido de la página
            texto_pagina = await page.inner_text('body')
            print(f"🔍 DEBUG SUNAT FIXED: Primeros 500 chars: {texto_pagina[:500]}")
            
            # Métodos de extracción múltiples
            selectores_razon_social = [
                "td.bgn:has-text('Nombre o Razón Social:') + td",
                "td:has-text('Nombre o Razón Social:') + td", 
                "td.bgn:has-text('Razón Social:') + td",
                "td:has-text('Razón Social:') + td"
            ]
            
            # Intentar con selectores CSS
            for selector in selectores_razon_social:
                try:
                    razon_social_elem = await page.wait_for_selector(selector, timeout=self.search_timeout)
                    if razon_social_elem:
                        razon_social = (await razon_social_elem.inner_text()).strip()
                        if razon_social and len(razon_social) > 5:
                            logger.info(f"📝 Razón Social encontrada: {razon_social}")
                            return razon_social
                except PlaywrightTimeoutError:
                    continue
                except Exception:
                    continue
            
            # Método alternativo: buscar en texto completo
            logger.info("🔍 Buscando en texto completo...")
            texto_completo = await page.inner_text('body')
            lineas = texto_completo.split('\n')
            
            # Buscar línea con RUC - RAZÓN SOCIAL
            for linea in lineas:
                if ruc in linea and ' - ' in linea:
                    partes = linea.split(' - ', 1)
                    if len(partes) > 1:
                        razon_social = partes[1].strip()
                        if razon_social and len(razon_social) > 5:
                            logger.info(f"📝 Razón Social encontrada en formato RUC-NOMBRE: {razon_social}")
                            return razon_social
            
            # Buscar por etiquetas
            for i, linea in enumerate(lineas):
                if 'Nombre o Razón Social:' in linea or 'Razón Social:' in linea:
                    if ':' in linea:
                        razon_social = linea.split(':', 1)[1].strip()
                        if razon_social and len(razon_social) > 5:
                            logger.info(f"📝 Razón Social encontrada en línea: {razon_social}")
                            return razon_social
                    
                    # Verificar línea siguiente
                    if i + 1 < len(lineas):
                        siguiente_linea = lineas[i + 1].strip()
                        if siguiente_linea and len(siguiente_linea) > 5 and not siguiente_linea.startswith(('Nombre', 'RUC', 'Tipo')):
                            logger.info(f"📝 Razón Social encontrada en línea siguiente: {siguiente_linea}")
                            return siguiente_linea
            
            raise Exception(f"No se pudo encontrar razón social para RUC {ruc}")
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo razón social: {str(e)}")
            raise Exception(f"Error al obtener razón social: {str(e)}")
    
    async def _obtener_domicilio_fiscal(self, page, ruc: str) -> str:
        """Obtener el domicilio fiscal de la empresa"""
        try:
            logger.info(f"🏠 Buscando domicilio fiscal para RUC: {ruc}")
            
            # Esperar a que la página cargue
            await page.wait_for_load_state('domcontentloaded')
            await page.wait_for_timeout(1000)
            
            # Buscar en texto de la página
            page_text = await page.inner_text('body')
            lines = page_text.split('\n')
            
            for i, line in enumerate(lines):
                line = line.strip()
                if "Domicilio Fiscal:" in line or "DOMICILIO FISCAL:" in line.upper():
                    logger.info(f"✅ Encontrada línea con domicilio fiscal: {line}")
                    
                    # Si el domicilio está en la misma línea
                    if ":" in line:
                        parts = line.split(":", 1)
                        if len(parts) > 1 and parts[1].strip():
                            domicilio = parts[1].strip()
                            if len(domicilio) > 2 and domicilio != "-":
                                logger.info(f"🏠 Domicilio fiscal extraído: {domicilio}")
                                return domicilio
                    
                    # Verificar líneas siguientes
                    if i + 1 < len(lines):
                        siguiente_linea = lines[i + 1].strip()
                        
                        if siguiente_linea == "-":
                            return "No registrado"
                        elif siguiente_linea and len(siguiente_linea) > 10:
                            if not any(nav in siguiente_linea.lower() for nav in ['volver', 'imprimir', 'email', 'consulta', 'resultado']):
                                logger.info(f"🏠 Domicilio fiscal extraído: {siguiente_linea}")
                                return siguiente_linea
            
            # Método CSS como fallback
            try:
                domicilio_elem = await page.wait_for_selector("td.bgn:has-text('Domicilio Fiscal:') + td", timeout=self.search_timeout)
                if domicilio_elem:
                    domicilio = (await domicilio_elem.inner_text()).strip()
                    if domicilio and len(domicilio) > 10:
                        logger.info(f"🏠 Domicilio fiscal extraído con CSS: {domicilio}")
                        return domicilio
            except PlaywrightTimeoutError:
                pass
            
            return "No disponible"
            
        except Exception as e:
            logger.error(f"❌ Error al extraer domicilio fiscal: {str(e)}")
            return "No disponible"
    
    async def _obtener_representantes_legales(self, page) -> List[RepresentanteLegal]:
        """Obtener la lista de representantes legales"""
        representantes = []
        
        try:
            logger.info("⏳ Buscando representantes legales...")
            
            # Intentar hacer clic en el botón de representantes
            boton_encontrado = await self._clickear_boton_representantes(page)
            
            if not boton_encontrado:
                logger.warning("⚠️ No se encontró el botón de Representantes Legales")
                return representantes
            
            # Esperar a que se cargue la información
            await page.wait_for_timeout(3000)
            logger.info("📋 Extrayendo tabla de Representantes Legales...")
            
            # Extraer datos de las tablas
            representantes = await self._extraer_datos_tablas(page)
            
            logger.info(f"📊 Total de representantes extraídos: {len(representantes)}")
            return representantes
            
        except Exception as e:
            logger.error(f"⚠️ Error al extraer representantes: {str(e)}")
            return representantes
    
    async def _clickear_boton_representantes(self, page) -> bool:
        """Intentar hacer clic en el botón de representantes legales"""
        # Método 1: Buscar por texto exacto
        try:
            await page.click("text='Representante(s) Legal(es)'", timeout=self.search_timeout)
            logger.info("✅ Botón clickeado por texto")
            return True
        except PlaywrightTimeoutError:
            pass
        except Exception:
            pass
        
        # Método 2: Buscar por input value
        try:
            boton = await page.wait_for_selector("input[type='button'][value*='Representante']", timeout=self.search_timeout)
            if boton:
                await boton.click()
                logger.info("✅ Botón clickeado por input value")
                return True
        except PlaywrightTimeoutError:
            pass
        except Exception:
            pass
        
        # Método 3: Buscar enlaces
        try:
            link = await page.wait_for_selector("a:has-text('Representante')", timeout=self.search_timeout)
            if link:
                await link.click()
                logger.info("✅ Enlace de representantes clickeado")
                return True
        except PlaywrightTimeoutError:
            pass
        except Exception:
            pass
        
        return False
    
    async def _extraer_datos_tablas(self, page) -> List[RepresentanteLegal]:
        """Extraer datos de representantes de todas las tablas"""
        representantes = []
        
        try:
            # Buscar todas las tablas
            tables = await page.query_selector_all('table')
            
            for table_idx, table in enumerate(tables):
                rows = await table.query_selector_all("tr")
                
                if len(rows) == 0:
                    continue
                
                # Verificar si tiene estructura de tabla de personas
                primera_fila_celdas = await rows[0].query_selector_all("td, th")
                
                if len(primera_fila_celdas) < 3:
                    continue
                
                logger.info(f"   📊 Procesando tabla {table_idx + 1} con {len(rows)} filas...")
                
                # Procesar cada fila
                for row_idx, row in enumerate(rows):
                    celdas = await row.query_selector_all("td")
                    
                    if not celdas or len(celdas) < 3:
                        continue
                    
                    # Extraer texto de cada celda
                    textos = []
                    for celda in celdas:
                        texto = (await celda.inner_text()).strip()
                        textos.append(texto)
                    
                    # Validar y procesar fila
                    representante = self._procesar_fila_representante(textos)
                    
                    if representante:
                        representantes.append(representante)
                        logger.info(f"   ✅ Persona {len(representantes)}: {representante.nombre} - {representante.cargo}")
            
            return representantes
            
        except Exception as e:
            logger.error(f"❌ Error extrayendo datos de tablas: {str(e)}")
            return representantes
    
    def _procesar_fila_representante(self, textos: List[str]) -> Optional[RepresentanteLegal]:
        """Procesar una fila de datos y crear un RepresentanteLegal"""
        # Filtrar filas vacías o de encabezado
        if not any(texto and texto != "-" and len(texto) > 2 for texto in textos):
            return None
        
        # Determinar el formato basado en número de columnas
        persona_data = {}
        
        if len(textos) >= 5:
            # Formato: TIPO DOC | NUM DOC | NOMBRE | CARGO | FECHA
            persona_data = {
                "tipo_doc": textos[0],
                "numero_doc": textos[1],
                "nombre": textos[2],
                "cargo": textos[3],
                "fecha_desde": textos[4] if len(textos) > 4 else ""
            }
        elif len(textos) == 4:
            # Formato: NUM DOC | NOMBRE | CARGO | FECHA
            persona_data = {
                "tipo_doc": "DNI",
                "numero_doc": textos[0],
                "nombre": textos[1],
                "cargo": textos[2],
                "fecha_desde": textos[3]
            }
        elif len(textos) == 3:
            # Formato: NOMBRE | CARGO | FECHA
            persona_data = {
                "tipo_doc": "-",
                "numero_doc": "-",
                "nombre": textos[0],
                "cargo": textos[1],
                "fecha_desde": textos[2]
            }
        else:
            return None
        
        # Validar que el nombre no sea un header
        nombre = persona_data.get("nombre", "")
        if not self._es_nombre_valido(nombre):
            return None
        
        try:
            return RepresentanteLegal(**persona_data)
        except Exception as e:
            logger.warning(f"⚠️ Error creando representante: {str(e)} - Datos: {persona_data}")
            return None
    
    def _es_nombre_valido(self, nombre: str) -> bool:
        """Validar que el nombre sea válido y no un header de tabla"""
        if not nombre or len(nombre) < 3:
            return False
        
        # Headers inválidos
        headers_invalidos = [
            "NOMBRE", "APELLIDOS", "TIPO", "DOC", "CARGO", "FECHA",
            "DOCUMENTO", "REPRESENTANTE", "LEGAL", "DESDE"
        ]
        
        if nombre.upper() in headers_invalidos:
            return False
        
        # No debe ser solo guiones
        if all(char == "-" for char in nombre):
            return False
        
        return True


# Instancia singleton del servicio fixed
sunat_service_fixed = SUNATServiceFixed()