"""
Servicio dedicado para consultas SUNAT con extracción de representantes legales
"""
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Any
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

from app.models.ruc import EmpresaInfo, RepresentanteLegal
from app.utils.exceptions import ValidationException, ExtractionException
from app.utils.playwright_helper import get_browser_launch_options

logger = logging.getLogger(__name__)


class SUNATService:
    """Servicio para consultar datos completos de empresas en SUNAT incluyendo representantes legales"""
    
    def __init__(self):
        self.base_url = "https://e-consultaruc.sunat.gob.pe/cl-ti-itmrconsruc/FrameCriterioBusquedaWeb.jsp"
        self.timeout = 30000
        
    async def consultar_empresa_completa(self, ruc: str) -> EmpresaInfo:
        """
        Consulta información completa de una empresa en SUNAT incluyendo representantes
        
        Args:
            ruc: RUC de 11 dígitos
            
        Returns:
            EmpresaInfo: Información completa de la empresa con representantes
            
        Raises:
            ValidationException: Si el RUC no es válido
            ExtractionException: Si hay errores en la extracción
        """
        logger.info(f"=== INICIANDO CONSULTA SUNAT COMPLETA PARA RUC: {ruc} ===")
        
        # Validar RUC
        if not self._validar_ruc(ruc):
            raise ValidationException(f"RUC inválido: {ruc}")
        
        async with async_playwright() as p:
            try:
                launch_options = get_browser_launch_options(headless=True)
                browser = await p.chromium.launch(**launch_options)
                
                page = await browser.new_page(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/114.0.0.0 Safari/537.36"
                )
                
                logger.info("Navegando a SUNAT...")
                await page.goto(self.base_url, timeout=self.timeout)
                
                # Llenar formulario de búsqueda
                await page.fill("#txtRuc", ruc)
                await page.wait_for_timeout(1000)
                
                # Verificar si hay captcha
                captcha_required = await self._verificar_captcha(page)
                if captcha_required:
                    logger.warning("SUNAT requiere CAPTCHA - extracción limitada")
                
                # Submit
                await page.click("#btnAceptar")
                await page.wait_for_timeout(5000)
                
                # Extraer datos básicos
                datos_basicos = await self._extraer_datos_basicos(page, ruc)
                
                # Extraer representantes legales
                representantes = await self._extraer_representantes(page, ruc)
                
                empresa_info = EmpresaInfo(
                    ruc=ruc,
                    razon_social=datos_basicos.get("razon_social", ""),
                    domicilio_fiscal=datos_basicos.get("direccion", ""),
                    estado=datos_basicos.get("estado", "ACTIVO"),
                    representantes=representantes,
                    total_representantes=len(representantes)
                )
                
                logger.info(f"✅ Consulta SUNAT completada: {len(representantes)} representantes encontrados")
                await browser.close()
                return empresa_info
                
            except Exception as e:
                logger.error(f"Error en consulta SUNAT: {str(e)}")
                if 'browser' in locals():
                    await browser.close()
                raise ExtractionException(f"Error consultando SUNAT: {str(e)}")
    
    async def _verificar_captcha(self, page) -> bool:
        """Verificar si se requiere CAPTCHA"""
        captcha_selectors = ["#txtCodigo", "#txtCaptcha", "input[name*='captcha']", "input[name*='codigo']"]
        
        for selector in captcha_selectors:
            try:
                if await page.is_visible(selector, timeout=1000):
                    return True
            except:
                continue
        return False
    
    async def _extraer_datos_basicos(self, page, ruc: str) -> Dict[str, str]:
        """Extraer datos básicos de la empresa"""
        logger.info("Extrayendo datos básicos...")
        
        datos = {
            "razon_social": "No disponible",
            "estado": "ACTIVO", 
            "direccion": "No disponible"
        }
        
        try:
            # Método 1: Buscar H4 con patrón RUC - NOMBRE
            h4_elements = await page.query_selector_all('h4')
            for h4 in h4_elements:
                try:
                    text = await h4.inner_text()
                    text = text.strip()
                    
                    if " - " in text and text.startswith(ruc):
                        parts = text.split(" - ", 1)
                        if len(parts) >= 2 and len(parts[1].strip()) > 5:
                            datos["razon_social"] = parts[1].strip()
                            logger.info(f"✅ Razón social encontrada: {datos['razon_social']}")
                            break
                except:
                    continue
            
            # Extraer estado y dirección
            paragraphs = await page.query_selector_all('p')
            for p in paragraphs:
                try:
                    p_text = await p.inner_text()
                    p_text = p_text.strip()
                    
                    # Buscar estado
                    if datos["estado"] == "ACTIVO" and p_text in ["ACTIVO", "INACTIVO", "SUSPENDIDO"]:
                        datos["estado"] = p_text
                        logger.info(f"✅ Estado encontrado: {datos['estado']}")
                    
                    # Buscar dirección
                    if datos["direccion"] == "No disponible" and p_text and len(p_text) > 20:
                        if any(word in p_text.upper() for word in ["AV.", "JR.", "CALLE", "CAL.", "LIMA", "NRO.", "MZA", "LOTE", "INT."]):
                            datos["direccion"] = p_text
                            logger.info(f"✅ Dirección encontrada: {datos['direccion'][:50]}...")
                except:
                    continue
        
        except Exception as e:
            logger.warning(f"Error extrayendo datos básicos: {e}")
        
        return datos
    
    async def _extraer_representantes(self, page, ruc: str) -> List[RepresentanteLegal]:
        """Extraer representantes legales de la página de SUNAT"""
        logger.info("Extrayendo representantes legales...")
        
        representantes = []
        
        try:
            # SUNAT muestra representantes en tablas o listas estructuradas
            # Buscar sección de "Representantes Legales" o "Datos del Representante Legal"
            
            # Método 1: Buscar tablas que contengan datos de representantes
            tables = await page.query_selector_all('table')
            logger.info(f"Encontradas {len(tables)} tablas para analizar")
            
            for i, table in enumerate(tables):
                try:
                    table_text = await table.inner_text()
                    
                    # Verificar si la tabla contiene información de representantes
                    if any(keyword in table_text.upper() for keyword in [
                        "REPRESENTANTE", "GERENTE", "ADMINISTRADOR", "APODERADO", 
                        "PRESIDENTE", "DIRECTOR", "DNI", "DOCUMENTO"
                    ]):
                        logger.info(f"Tabla {i} parece contener representantes")
                        representantes_tabla = await self._extraer_de_tabla(table)
                        representantes.extend(representantes_tabla)
                        
                except Exception as e:
                    logger.warning(f"Error procesando tabla {i}: {e}")
                    continue
            
            # Método 2: Buscar elementos div que contengan información estructurada
            if not representantes:
                divs = await page.query_selector_all('div')
                for div in divs:
                    try:
                        div_text = await div.inner_text()
                        if self._parece_info_representante(div_text):
                            representante = await self._extraer_de_div(div)
                            if representante:
                                representantes.append(representante)
                    except:
                        continue
            
            # Método 3: Análisis de texto completo si no se encontraron representantes
            if not representantes:
                logger.info("Analizando texto completo para encontrar representantes...")
                page_text = await page.evaluate('() => document.body.innerText')
                representantes = self._extraer_de_texto_completo(page_text)
            
            logger.info(f"✅ Encontrados {len(representantes)} representantes legales")
            
        except Exception as e:
            logger.error(f"Error extrayendo representantes: {e}")
        
        return representantes
    
    async def _extraer_de_tabla(self, table) -> List[RepresentanteLegal]:
        """Extraer representantes de una tabla HTML"""
        representantes = []
        
        try:
            # Obtener filas de la tabla
            rows = await table.query_selector_all('tr')
            
            # Buscar encabezados para entender la estructura
            headers = []
            if rows:
                first_row = rows[0]
                header_cells = await first_row.query_selector_all('th, td')
                for cell in header_cells:
                    header_text = await cell.inner_text()
                    headers.append(header_text.strip().upper())
            
            # Procesar filas de datos
            for row in rows[1:]:  # Saltar header
                try:
                    cells = await row.query_selector_all('td')
                    if len(cells) >= 2:  # Necesitamos al menos 2 celdas
                        row_data = []
                        for cell in cells:
                            cell_text = await cell.inner_text()
                            row_data.append(cell_text.strip())
                        
                        representante = self._procesar_fila_representante(row_data, headers)
                        if representante:
                            representantes.append(representante)
                            
                except Exception as e:
                    logger.warning(f"Error procesando fila de tabla: {e}")
                    continue
                    
        except Exception as e:
            logger.warning(f"Error procesando tabla: {e}")
        
        return representantes
    
    def _procesar_fila_representante(self, row_data: List[str], headers: List[str]) -> Optional[RepresentanteLegal]:
        """Procesar una fila de datos de representante"""
        
        if not row_data or len(row_data) < 2:
            return None
        
        # Mapear campos comunes
        nombre = ""
        cargo = ""
        tipo_doc = "DNI"
        numero_doc = ""
        fecha_desde = ""
        
        # Buscar nombre (usualmente la primera columna no vacía)
        for data in row_data:
            if data and len(data) > 3 and not data.isdigit():
                # Verificar si parece un nombre
                if any(char.isalpha() for char in data) and not any(keyword in data.upper() for keyword in ["RUC", "FECHA", "ESTADO"]):
                    nombre = data
                    break
        
        # Buscar número de documento (8 dígitos para DNI)
        for data in row_data:
            if data and data.isdigit() and len(data) == 8:
                numero_doc = data
                break
        
        # Buscar cargo
        for data in row_data:
            if data and any(keyword in data.upper() for keyword in [
                "GERENTE", "ADMINISTRADOR", "PRESIDENTE", "DIRECTOR", "APODERADO", "REPRESENTANTE"
            ]):
                cargo = data
                break
        
        # Buscar fecha
        for data in row_data:
            if data and self._parece_fecha(data):
                fecha_desde = data
                break
        
        # Crear representante si tenemos datos mínimos
        if nombre and (numero_doc or cargo):
            return RepresentanteLegal(
                nombre=nombre,
                cargo=cargo or "Representante Legal",
                tipo_doc=tipo_doc,
                numero_doc=numero_doc,
                fecha_desde=fecha_desde
            )
        
        return None
    
    async def _extraer_de_div(self, div) -> Optional[RepresentanteLegal]:
        """Extraer representante de un elemento div"""
        try:
            div_text = await div.inner_text()
            lines = div_text.strip().split('\n')
            
            # Buscar patrones comunes
            nombre = ""
            cargo = ""
            numero_doc = ""
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Buscar nombre
                if not nombre and len(line) > 10 and any(char.isalpha() for char in line):
                    if not any(keyword in line.upper() for keyword in ["RUC", "FECHA", "ESTADO", "DOCUMENTO"]):
                        nombre = line
                
                # Buscar cargo
                if any(keyword in line.upper() for keyword in [
                    "GERENTE", "ADMINISTRADOR", "PRESIDENTE", "DIRECTOR", "APODERADO"
                ]):
                    cargo = line
                
                # Buscar DNI
                dni_match = re.search(r'\b\d{8}\b', line)
                if dni_match:
                    numero_doc = dni_match.group()
            
            if nombre:
                return RepresentanteLegal(
                    nombre=nombre,
                    cargo=cargo or "Representante Legal",
                    tipo_doc="DNI",
                    numero_doc=numero_doc,
                    fecha_desde=""
                )
                
        except Exception as e:
            logger.warning(f"Error extrayendo de div: {e}")
        
        return None
    
    def _extraer_de_texto_completo(self, texto: str) -> List[RepresentanteLegal]:
        """Extraer representantes del texto completo usando patrones"""
        representantes = []
        
        try:
            lines = texto.split('\n')
            
            # Buscar patrones que indiquen información de representantes
            for i, line in enumerate(lines):
                line = line.strip()
                
                # Buscar líneas que contengan cargos típicos
                if any(keyword in line.upper() for keyword in [
                    "GERENTE GENERAL", "ADMINISTRADOR", "PRESIDENTE", "DIRECTOR", "APODERADO"
                ]):
                    # Buscar nombre en líneas cercanas
                    nombre_candidato = ""
                    numero_doc = ""
                    
                    # Buscar en líneas anteriores y siguientes
                    for j in range(max(0, i-2), min(len(lines), i+3)):
                        candidate_line = lines[j].strip()
                        
                        # Buscar nombre (línea con letras, no muy corta)
                        if (not nombre_candidato and len(candidate_line) > 10 and 
                            any(char.isalpha() for char in candidate_line) and
                            not any(kw in candidate_line.upper() for kw in ["RUC", "FECHA", "ESTADO"])):
                            nombre_candidato = candidate_line
                        
                        # Buscar DNI
                        dni_match = re.search(r'\b\d{8}\b', candidate_line)
                        if dni_match:
                            numero_doc = dni_match.group()
                    
                    if nombre_candidato:
                        representante = RepresentanteLegal(
                            nombre=nombre_candidato,
                            cargo=line,
                            tipo_doc="DNI",
                            numero_doc=numero_doc,
                            fecha_desde=""
                        )
                        representantes.append(representante)
        
        except Exception as e:
            logger.warning(f"Error extrayendo de texto completo: {e}")
        
        return representantes
    
    def _parece_info_representante(self, texto: str) -> bool:
        """Verificar si un texto parece contener información de representante"""
        texto_upper = texto.upper()
        
        # Debe contener al menos un cargo y un nombre
        tiene_cargo = any(keyword in texto_upper for keyword in [
            "GERENTE", "ADMINISTRADOR", "PRESIDENTE", "DIRECTOR", "APODERADO", "REPRESENTANTE"
        ])
        
        tiene_nombre = len(texto) > 20 and any(char.isalpha() for char in texto)
        
        return tiene_cargo and tiene_nombre
    
    def _parece_fecha(self, texto: str) -> bool:
        """Verificar si un texto parece una fecha"""
        # Patrones comunes de fecha
        date_patterns = [
            r'\d{2}/\d{2}/\d{4}',
            r'\d{2}-\d{2}-\d{4}',
            r'\d{1,2} de \w+ de \d{4}'
        ]
        
        return any(re.search(pattern, texto) for pattern in date_patterns)
    
    def _validar_ruc(self, ruc: str) -> bool:
        """Validar formato del RUC"""
        if not ruc or len(ruc) != 11 or not ruc.isdigit():
            return False
        
        primeros_dos_digitos = ruc[:2]
        if primeros_dos_digitos not in ['10', '20']:
            return False
        
        return True


# Instancia singleton del servicio SUNAT
sunat_service = SUNATService()