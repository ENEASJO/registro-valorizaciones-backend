"""
Servicio para consultar información de empresas en SUNAT
"""
import asyncio
from typing import List, Optional, Dict, Any
from playwright.async_api import async_playwright, Browser, Page, TimeoutError
import logging

from app.models.ruc import EmpresaInfo, RepresentanteLegal
from app.core.config import settings
from app.utils.validators import validate_ruc

logger = logging.getLogger(__name__)


class SUNATService:
    """Servicio para consultar información de empresas en SUNAT"""
    
    def __init__(self):
        self.base_url = "https://e-consultaruc.sunat.gob.pe/cl-ti-itmrconsruc/FrameCriterioBusquedaWeb.jsp"
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/114.0.0.0 Safari/537.36"
        self.timeout = 30000  # 30 segundos
        
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
        
        logger.info(f"🔍 Consultando RUC: {ruc}")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=settings.HEADLESS_BROWSER,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--no-first-run',
                    '--no-zygote',
                    '--single-process',
                    '--disable-gpu',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor',
                    '--disable-extensions',
                    '--disable-plugins',
                    '--disable-background-timer-throttling',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-renderer-backgrounding'
                ]
            )
            
            context = None
            page = None
            try:
                logger.info(f"🌐 Creando contexto de navegador...")
                context = await browser.new_context(user_agent=self.user_agent)
                logger.info(f"✅ Contexto creado exitosamente")
                
                logger.info(f"📄 Creando nueva página...")
                page = await context.new_page()
                if not page:
                    raise Exception("No se pudo crear la página del navegador")
                logger.info(f"✅ Página creada exitosamente")
                
                logger.info(f"⏱️ Configurando timeout ({self.timeout}ms)...")
                page.set_default_timeout(self.timeout)  # Cambiar a versión síncrona
                logger.info(f"✅ Timeout configurado")
                
                # Navegar a la página principal y hacer búsqueda
                logger.info(f"🌐 Navegando a SUNAT...")
                await page.goto(self.base_url)
                await page.fill('#txtRuc', ruc)
                await page.click('#btnAceptar')
                await page.wait_for_timeout(3000)
                logger.info(f"✅ Búsqueda completada")
                
                # Obtener información básica
                razon_social = await self._obtener_razon_social(page, ruc)
                
                # Obtener domicilio fiscal
                domicilio_fiscal = await self._obtener_domicilio_fiscal(page, ruc)
                
                # Obtener representantes legales
                representantes = await self._obtener_representantes_legales(page)
                
                resultado = EmpresaInfo(
                    ruc=ruc,
                    razon_social=razon_social,
                    domicilio_fiscal=domicilio_fiscal,
                    representantes=representantes
                )
                
                logger.info(f"📊 Consulta exitosa para RUC {ruc}: {len(representantes)} representantes encontrados")
                return resultado
                
            except Exception as e:
                logger.error(f"❌ Error consultando RUC {ruc}: {str(e)}")
                # Tomar screenshot para debug si hay error
                if settings.DEBUG:
                    try:
                        await page.screenshot(path=f"error_sunat_{ruc}.png")
                    except:
                        pass
                raise
                
            finally:
                if context:
                    try:
                        await context.close()
                    except:
                        pass
                await browser.close()
    
    async def _obtener_razon_social(self, page: Page, ruc: str) -> str:
        """
        Obtener la razón social de la empresa desde la página ya cargada
        
        Args:
            page: Página de Playwright ya navegada
            ruc: RUC a consultar
            
        Returns:
            str: Razón social de la empresa
        """
        try:
            logger.info(f"🔍 Buscando razón social en la página actual...")
            
            # Debug: mostrar parte del contenido de la página
            texto_pagina = await page.inner_text('body')
            print(f"🔍 DEBUG SUNAT: Primeros 800 chars: {texto_pagina[:800]}")
            
            # Intentar múltiples selectores para razón social
            selectores_razon_social = [
                "td.bgn:has-text('Nombre o Razón Social:') + td",
                "td:has-text('Nombre o Razón Social:') + td", 
                "td.bgn:has-text('Razón Social:') + td",
                "td:has-text('Razón Social:') + td",
                "span:has-text('Nombre o Razón Social:') ~ span",
                "div:has-text('Nombre o Razón Social:') ~ div"
            ]
            
            for selector in selectores_razon_social:
                try:
                    razon_social_elem = await page.query_selector(selector)
                    if razon_social_elem:
                        razon_social = (await razon_social_elem.inner_text()).strip()
                        if razon_social and len(razon_social) > 5:  # Filtrar respuestas muy cortas
                            logger.info(f"📝 Razón Social encontrada con selector {selector}: {razon_social}")
                            return razon_social
                except Exception:
                    continue
            
            # Método alternativo: buscar en todo el texto de la página
            logger.info("🔍 Método alternativo: buscando en texto completo...")
            texto_completo = await page.inner_text('body')
            lineas = texto_completo.split('\n')
            
            # Método específico para SUNAT: buscar línea con RUC - RAZÓN SOCIAL
            for linea in lineas:
                if ruc in linea and ' - ' in linea:
                    partes = linea.split(' - ', 1)
                    if len(partes) > 1:
                        razon_social = partes[1].strip()
                        if razon_social and len(razon_social) > 5:
                            logger.info(f"📝 Razón Social encontrada en formato RUC - NOMBRE: {razon_social}")
                            return razon_social
            
            # Método general: buscar por etiquetas
            for i, linea in enumerate(lineas):
                if 'Nombre o Razón Social:' in linea or 'Razón Social:' in linea:
                    # La razón social puede estar en la misma línea o en la siguiente
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
            
            logger.warning(f"⚠️ No se encontró razón social para RUC {ruc}")
            return ""
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo razón social: {str(e)}")
            return ""
    
    async def _obtener_domicilio_fiscal(self, page: Page, ruc: str) -> str:
        """
        Obtener el domicilio fiscal de la empresa
        
        Args:
            page: Página de Playwright
            ruc: RUC a consultar
            
        Returns:
            str: Domicilio fiscal de la empresa
        """
        try:
            logger.info(f"🏠 Buscando domicilio fiscal para RUC: {ruc}")
            
            # Método 1: Buscar en todo el texto de la página
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
                                logger.info(f"🏠 Domicilio fiscal extraído (misma línea): {domicilio}")
                                return domicilio
                    
                    # Verificar líneas siguientes para el domicilio
                    if i + 1 < len(lines):
                        siguiente_linea = lines[i + 1].strip()
                        
                        if siguiente_linea == "-":
                            logger.info(f"🏠 Domicilio fiscal no registrado (guión encontrado)")
                            return "No registrado"
                        elif siguiente_linea and len(siguiente_linea) > 10:
                            # Verificar que no sea parte del menú o navegación
                            if not any(nav in siguiente_linea.lower() for nav in ['volver', 'imprimir', 'email', 'consulta', 'resultado']):
                                logger.info(f"🏠 Domicilio fiscal extraído (línea siguiente): {siguiente_linea}")
                                return siguiente_linea
                        elif i + 2 < len(lines):
                            # Buscar en la línea que está después de una posible línea vacía
                            linea_dos_despues = lines[i + 2].strip()
                            
                            if linea_dos_despues == "-":
                                logger.info(f"🏠 Domicilio fiscal no registrado (guión encontrado)")
                                return "No registrado"
                            elif linea_dos_despues and len(linea_dos_despues) > 10:
                                # Verificar que no sea parte del menú o navegación
                                if not any(nav in linea_dos_despues.lower() for nav in ['volver', 'imprimir', 'email', 'consulta', 'resultado']):
                                    logger.info(f"🏠 Domicilio fiscal extraído (dos líneas después): {linea_dos_despues}")
                                    return linea_dos_despues
            
            # Método 2: Buscar con selectores CSS específicos
            logger.info("⚠️ Método de texto falló, buscando con selectores CSS...")
            
            # Selector para tabla con "Domicilio Fiscal"
            domicilio_elem = await page.query_selector("td.bgn:has-text('Domicilio Fiscal:') + td")
            if domicilio_elem:
                domicilio = (await domicilio_elem.inner_text()).strip()
                if domicilio and len(domicilio) > 10:
                    logger.info(f"🏠 Domicilio fiscal extraído con CSS específico: {domicilio}")
                    return domicilio
            
            logger.warning(f"⚠️ No se pudo extraer domicilio fiscal para RUC: {ruc}")
            return ""
            
        except Exception as e:
            logger.error(f"❌ Error al extraer domicilio fiscal: {str(e)}")
            return ""
    
    async def _obtener_representantes_legales(self, page: Page) -> List[RepresentanteLegal]:
        """
        Obtener la lista de representantes legales
        
        Args:
            page: Página de Playwright
            
        Returns:
            List[RepresentanteLegal]: Lista de representantes legales
        """
        representantes = []
        
        try:
            logger.info("⏳ Buscando botón 'Representante(s) Legal(es)'...")
            
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
    
    async def _clickear_boton_representantes(self, page: Page) -> bool:
        """
        Intentar hacer clic en el botón de representantes legales
        
        Args:
            page: Página de Playwright
            
        Returns:
            bool: True si se hizo clic exitosamente
        """
        # Método 1: Buscar por texto exacto
        try:
            await page.click("text='Representante(s) Legal(es)'", timeout=5000)
            logger.info("✅ Botón clickeado por texto")
            return True
        except:
            pass
        
        # Método 2: Buscar por input value
        try:
            boton = await page.query_selector("input[type='button'][value*='Representante']")
            if boton:
                await boton.click()
                logger.info("✅ Botón clickeado por input value")
                return True
        except:
            pass
        
        # Método 3: Buscar enlaces
        try:
            link = await page.query_selector("a:has-text('Representante')")
            if link:
                await link.click()
                logger.info("✅ Enlace de representantes clickeado")
                return True
        except:
            pass
        
        return False
    
    async def _extraer_datos_tablas(self, page: Page) -> List[RepresentanteLegal]:
        """
        Extraer datos de representantes de todas las tablas
        
        Args:
            page: Página de Playwright
            
        Returns:
            List[RepresentanteLegal]: Lista de representantes extraídos
        """
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
        """
        Procesar una fila de datos y crear un RepresentanteLegal
        
        Args:
            textos: Lista de textos de las celdas
            
        Returns:
            Optional[RepresentanteLegal]: Representante creado o None si no es válido
        """
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
        """
        Validar que el nombre sea válido y no un header de tabla
        
        Args:
            nombre: Nombre a validar
            
        Returns:
            bool: True si el nombre es válido
        """
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


# Instancia singleton del servicio
sunat_service = SUNATService()