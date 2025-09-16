"""
Servicio SUNAT mejorado con métodos avanzados para extraer representantes legales
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


class SUNATServiceImproved:
    """Servicio SUNAT mejorado con métodos robustos para extraer representantes"""

    def __init__(self):
        self.base_url = "https://e-consultaruc.sunat.gob.pe/cl-ti-itmrconsruc/FrameCriterioBusquedaWeb.jsp"
        self.timeout = 45000  # Aumentado a 45 segundos

    async def consultar_empresa_completa(self, ruc: str) -> EmpresaInfo:
        """Consulta información completa incluyendo representantes mejorados"""
        logger.info(f"=== INICIANDO CONSULTA SUNAT MEJORADA PARA RUC: {ruc} ===")

        if not self._validar_ruc(ruc):
            raise ValidationException(f"RUC inválido: {ruc}")

        async with async_playwright() as p:
            browser = None
            try:
                launch_options = get_browser_launch_options(headless=True)
                logger.info(f"Opciones de lanzamiento: {launch_options}")

                browser = await p.chromium.launch(**launch_options)

                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    viewport={'width': 1280, 'height': 720},
                    ignore_https_errors=True
                )

                page = await context.new_page()

                logger.info("Navegando a SUNAT...")
                await page.goto(self.base_url, timeout=self.timeout)

                # Llenar formulario
                await page.fill("#txtRuc", ruc)
                await page.wait_for_timeout(1500)

                # Verificar CAPTCHA
                captcha_required = await self._verificar_captcha(page)
                if captcha_required:
                    logger.warning("CAPTCHA detectado - usando métodos alternativos")

                # Submit
                await page.click("#btnAceptar")

                # Esperar más tiempo para que cargue todo (SUNAT puede ser lento)
                await page.wait_for_timeout(8000)

                # Esperar a que aparezca el contenido
                try:
                    await page.wait_for_selector('h4, .form-group, table', timeout=15000)
                    logger.info("✅ Página cargada correctamente")
                except:
                    logger.warning("Timeout esperando selectores principales, continuando igualmente")

                # Extraer datos básicos
                datos_basicos = await self._extraer_datos_basicos_mejorado(page, ruc)

                # Buscar y hacer clic en el botón de representantes legales
                logger.info("🔍 Buscando botón de representantes legales...")
                try:
                    # Buscar el botón por diferentes selectores
                    btn_selectors = [
                        ".btnInfRepLeg",  # Clase específica de SUNAT
                        "button:has-text('Representante')",
                        "button:has-text('Representante(s) Legal(es)')",
                        "[onclick*='representante']",
                        ".btn-representante",
                        "button:has-text('Ver Representantes')"
                    ]

                    btn_clicked = False
                    for selector in btn_selectors:
                        try:
                            btn = await page.query_selector(selector)
                            if btn:
                                logger.info(f"✅ Botón encontrado con selector: {selector}")
                                await btn.click()
                                btn_clicked = True
                                # Esperar a que cargue el modal/panel
                                await page.wait_for_timeout(3000)
                                break
                        except:
                            continue

                    if not btn_clicked:
                        logger.info("ℹ️ No se encontró botón de representantes (puede que no haya)")

                except Exception as e:
                    logger.warning(f"Error buscando botón de representantes: {e}")

                # Extraer representantes con métodos mejorados
                representantes = await self._extraer_representantes_mejorado(page, ruc)

                empresa_info = EmpresaInfo(
                    ruc=ruc,
                    razon_social=datos_basicos.get("razon_social", ""),
                    domicilio_fiscal=datos_basicos.get("direccion", ""),
                    estado=datos_basicos.get("estado", "ACTIVO"),
                    representantes=representantes,
                    total_representantes=len(representantes)
                )

                logger.info(f"✅ Consulta SUNAT mejorada completada: {len(representantes)} representantes")
                return empresa_info

            except Exception as e:
                logger.error(f"Error en consulta SUNAT mejorada: {str(e)}")
                if browser:
                    await browser.close()
                raise ExtractionException(f"Error consultando SUNAT: {str(e)}")
            finally:
                if browser:
                    await browser.close()

    async def _extraer_representantes_mejorado(self, page, ruc: str) -> List[RepresentanteLegal]:
        """Método mejorado para extraer representantes"""
        logger.info("🔍 Iniciando extracción mejorada de representantes...")

        representantes = []

        try:
            # Esperar más tiempo para que cargue el contenido dinámico
            await page.wait_for_timeout(3000)

            # Método 1: Buscar por selectores específicos de SUNAT
            representantes.extend(await self._metodo_selectores_especificos(page))

            # Método 2: Buscar en tablas con criterios mejorados
            if not representantes:
                representantes.extend(await self._metodo_tablas_mejorado(page))

            # Método 3: Análisis de HTML con patrones específicos
            if not representantes:
                representantes.extend(await self._metodo_html_patterns(page))

            # Método 4: Búsqueda avanzada por texto
            if not representantes:
                page_text = await page.inner_text('body')
                representantes.extend(self._metodo_texto_avanzado(page_text))

            # Eliminar duplicados
            representantes = self._eliminar_duplicados(representantes)

            logger.info(f"✅ Total de {len(representantes)} representantes únicos encontrados")

            if not representantes:
                logger.warning("⚠️ No se encontraron representantes - revisando estructura de página...")
                await self._debug_estructura_pagina(page)

        except Exception as e:
            logger.error(f"Error en extracción mejorada: {e}")

        return representantes

    async def _metodo_selectores_especificos(self, page) -> List[RepresentanteLegal]:
        """Método 1: Buscar con selectores específicos de SUNAT"""
        logger.info("📋 Método 1: Buscando con selectores específicos...")

        representantes = []

        # Selectores comunes en SUNAT para representantes (actualizados)
        selectores_representantes = [
            "table.form-table tbody tr",  # Tabla principal con datos
            "#tblRepresentantes tbody tr",  # Tabla específica de representantes
            ".form-table tbody tr",  # Tablas con clase form-table
            "table:has(th:has-text('Representante')) tbody tr",  # Tabla con encabezado Representante
            "table:has(th:has-text('Nombre')) tbody tr",  # Tabla con encabezado Nombre
            # Selectores para modal/panel de representantes
            ".modal table tbody tr",  # Tabla dentro de modal
            ".panel table tbody tr",  # Tabla dentro de panel
            "[style*='display: block'] table tbody tr",  # Tabla en elemento visible
            ".dataTable tbody tr",  # Tabla con clase dataTable
        ]

        for selector in selectores_representantes:
            try:
                elementos = await page.query_selector_all(selector)
                logger.info(f"Selector '{selector}' encontró {len(elementos)} elementos")

                for elemento in elementos:
                    try:
                        # Extraer datos de las celdas de la tabla
                        celdas = await elemento.query_selector_all('td')
                        if len(celdas) >= 3:  # Mínimo 3 celdas (nombre, cargo, documento)
                            row_data = []
                            for celda in celdas:
                                cell_text = await celda.inner_text()
                                row_data.append(cell_text.strip())

                            logger.info(f"📋 Fila encontrada: {row_data}")

                            # Procesar la fila como representante
                            representante = self._procesar_fila_representante(row_data)
                            if representante:
                                representantes.append(representante)
                                logger.info(f"✅ Representante extraído: {representante.nombre}")
                    except Exception as e:
                        logger.warning(f"Error procesando elemento: {e}")
                        continue

                if representantes:
                    break

            except:
                continue

        return representantes

    def _procesar_fila_representante(self, row_data: List[str]) -> Optional[RepresentanteLegal]:
        """Procesar una fila de tabla de representantes"""
        if not row_data or len(row_data) < 4:
            return None

        nombre = ""
        cargo = ""
        tipo_doc = ""
        numero_doc = ""
        fecha_desde = ""

        # Procesar según el número de columnas
        if len(row_data) >= 5:
            # Formato SUNAT: Tipo Doc, Número Doc, Nombre, Cargo, Fecha
            tipo_doc = row_data[0]
            numero_doc = row_data[1]
            nombre = row_data[2]
            cargo = row_data[3]
            fecha_desde = row_data[4]
        elif len(row_data) >= 4:
            # Formato sin fecha: Tipo Doc, Número Doc, Nombre, Cargo
            tipo_doc = row_data[0]
            numero_doc = row_data[1]
            nombre = row_data[2]
            cargo = row_data[3]
        else:
            # Formato alternativo - intentar detectar patrones
            for i, campo in enumerate(row_data):
                if campo.isdigit() and len(campo) == 8:
                    numero_doc = campo
                    tipo_doc = "DNI"
                elif campo.upper() in ["DNI", "CE", "PASAPORTE"]:
                    tipo_doc = campo
                elif any(cargo_kw in campo.upper() for cargo_kw in ["GERENTE", "DIRECTOR", "ADMINISTRADOR", "REPRESENTANTE", "PRESIDENTE"]):
                    cargo = campo
                elif len(campo) > 10 and campo.isupper():
                    nombre = campo

        # Validar datos mínimos
        if not nombre or len(nombre) < 5:
            return None

        # Limpiar nombre
        nombre = re.sub(r'\s+', ' ', nombre).strip()

        return RepresentanteLegal(
            nombre=nombre,
            cargo=cargo or "No especificado",
            tipo_doc=tipo_doc or "DNI",
            numero_doc=numero_doc,
            fecha_desde=fecha_desde or ""
        )

    async def _metodo_tablas_mejorado(self, page) -> List[RepresentanteLegal]:
        """Método 2: Buscar en tablas con criterios mejorados"""
        logger.info("📊 Método 2: Buscando en tablas...")

        representantes = []

        tables = await page.query_selector_all('table')
        logger.info(f"Analizando {len(tables)} tablas...")

        for i, table in enumerate(tables):
            try:
                # Obtener HTML completo de la tabla
                table_html = await table.inner_html()
                table_text = await table.inner_text()

                # Criterios más específicos
                if any(keyword in table_text.upper() for keyword in [
                    "REPRESENTANTE LEGAL", "GERENTE GENERAL", "DIRECTOR",
                    "APODERADO", "ADMINISTRADOR", "PRESIDENTE"
                ]):
                    logger.info(f"Tabla {i} parece contener representantes")

                    # Extraer filas
                    rows = await table.query_selector_all('tr')

                    for row in rows[1:]:  # Saltar header
                        cells = await row.query_selector_all('td')
                        if len(cells) >= 2:
                            row_data = []
                            for cell in cells:
                                cell_text = await cell.inner_text()
                                row_data.append(cell_text.strip())

                            representante = self._procesar_fila_mejorada(row_data)
                            if representante:
                                representantes.append(representante)

            except Exception as e:
                logger.warning(f"Error procesando tabla {i}: {e}")
                continue

        return representantes

    async def _metodo_html_patterns(self, page) -> List[RepresentanteLegal]:
        """Método 3: Análisis de HTML con patrones específicos"""
        logger.info("🔍 Método 3: Analizando HTML con patrones...")

        representantes = []

        # Obtener HTML completo
        html_content = await page.content()

        # Patrones para encontrar información de representantes
        patrones = [
            # Patrón 1: Tabla con representante legal
            r'<table[^>]*>.*?representante.*?</table>',
            # Patrón 2: Div con representante
            r'<div[^>]*class="[^"]*representante[^"]*"[^>]*>(.*?)</div>',
            # Patrón 3: Fila de tabla con DNI y nombre
            r'<tr[^>]*>.*?<td[^>]*>\s*(\d{8})\s*</td>.*?<td[^>]*>\s*([A-ZÁÉÍÓÚÑ\s,]+)\s*</td>',
            # Patrón 4: Gerente general específico
            r'gerente general.*?<strong[^>]*>([A-ZÁÉÍÓÚÑ\s,]+)</strong>',
        ]

        for pattern in patrones:
            try:
                matches = re.findall(pattern, html_content, re.IGNORECASE | re.DOTALL)
                logger.info(f"Patrón encontrado {len(matches)} coincidencias")

                for match in matches:
                    if isinstance(match, tuple):
                        # Es el patrón con DNI y nombre
                        dni, nombre = match
                        representante = RepresentanteLegal(
                            nombre=nombre.strip(),
                            cargo="GERENTE GENERAL",
                            tipo_doc="DNI",
                            numero_doc=dni.strip(),
                            fecha_desde=""
                        )
                        representantes.append(representante)
                    else:
                        # Extraer del texto completo
                        representante = self._extraer_representante_de_texto(match)
                        if representante:
                            representantes.append(representante)

                if representantes:
                    break

            except Exception as e:
                logger.warning(f"Error con patrón {pattern}: {e}")
                continue

        return representantes

    def _metodo_texto_avanzado(self, texto: str) -> List[RepresentanteLegal]:
        """Método 4: Búsqueda avanzada por texto"""
        logger.info("📝 Método 4: Búsqueda avanzada en texto...")

        representantes = []
        lineas = texto.split('\n')

        # Patrones mejorados para nombres completos
        patrones_nombre = [
            r'([A-ZÁÉÍÓÚÑ\s]+,?\s+[A-ZÁÉÍÓÚÑ\s]+)',  # Apellido, Nombre
            r'([A-ZÁÉÍÓÚÑ]+\s+[A-ZÁÉÍÓÚÑ]+\s+[A-ZÁÉÍÓÚÑ\s]+)'  # Nombre completo
        ]

        # Buscar bloques de información
        i = 0
        while i < len(lineas):
            linea = lineas[i].strip()

            # Buscar nombres que parezcan personas (no empresas)
            if (len(linea) > 15 and
                linea.isupper() and
                any(char.isalpha() for char in linea) and
                not any(kw in linea for kw in ['S.A.C', 'S.A.', 'S.R.L', 'SOCIEDAD ANONIMA', 'RUC:', 'AV.', 'JR.', 'CALLE'])):

                # Verificar si es un nombre de persona (no empresa)
                palabras = linea.split()
                if len(palabras) >= 2 and all(len(p) > 1 for p in palabras[:2]):
                    # Buscar información relacionada en líneas cercanas
                    nombre_candidato = linea
                    dni = ""
                    cargo = ""
                    fecha_desde = ""

                    # Buscar en contexto cercano (3 líneas antes y 5 después)
                    for j in range(max(0, i-3), min(len(lineas), i+6)):
                        if j == i:
                            continue

                        linea_busqueda = lineas[j].strip()

                        # Buscar DNI (8 dígitos)
                        dni_match = re.search(r'\b(\d{8})\b', linea_busqueda)
                        if dni_match:
                            dni = dni_match.group(1)

                        # Buscar cargo específico
                        if any(cargo_kw in linea_busqueda.upper() for cargo_kw in [
                            'GERENTE GENERAL', 'GERENTE', 'DIRECTOR', 'ADMINISTRADOR',
                            'REPRESENTANTE LEGAL', 'PRESIDENTE', 'APODERADO'
                        ]):
                            # Limpiar el cargo
                            if ':' in linea_busqueda:
                                cargo = linea_busqueda.split(':')[1].strip().upper()
                            else:
                                cargo = linea_busqueda.upper()

                        # Buscar fecha
                        fecha_match = re.search(r'\b\d{2}/\d{2}/\d{4}\b', linea_busqueda)
                        if fecha_match:
                            fecha_desde = fecha_match.group()

                        # Buscar "REPRESENTANTE:" seguido de nombre
                        if 'REPRESENTANTE:' in linea_busqueda.upper() and ':' in linea_busqueda:
                            nombre_pos = linea_busqueda.find(':')
                            posible_nombre = linea_busqueda[nombre_pos+1:].strip()
                            if len(posible_nombre) > 5:
                                nombre_candidato = posible_nombre

                    # Solo agregar si tenemos nombre y DNI (más confiable)
                    if nombre_candidato and dni:
                        representante = RepresentanteLegal(
                            nombre=nombre_candidato,
                            cargo=cargo or "REPRESENTANTE LEGAL",
                            tipo_doc="DNI",
                            numero_doc=dni,
                            fecha_desde=fecha_desde
                        )
                        representantes.append(representante)

            # Patrón 2: Buscar bloques con etiquetas claras
            elif ':' in linea:
                etiqueta = linea.split(':')[0].strip().upper()
                valor = linea.split(':')[1].strip() if ':' in linea else ""

                # Si encontramos una etiqueta de representante
                if any(etq in etiqueta for etq in ['REPRESENTANTE', 'NOMBRE/RAZON SOCIAL']):
                    nombre = valor
                    dni = ""
                    cargo = ""

                    # Buscar datos en líneas siguientes
                    for j in range(i+1, min(len(lineas), i+10)):
                        siguiente = lineas[j].strip()

                        if ':' in siguiente:
                            sig_etiqueta = siguiente.split(':')[0].strip().upper()
                            sig_valor = siguiente.split(':')[1].strip()

                            if 'DNI' in sig_etiqueta or 'NUMERO DOCUMENTO' in sig_etiqueta:
                                dni_match = re.search(r'\b(\d{8})\b', sig_valor)
                                if dni_match:
                                    dni = dni_match.group(1)

                            if 'CARGO' in sig_etiqueta:
                                cargo = sig_valor.upper()

                            if 'FECHA DESDE' in sig_etiqueta:
                                fecha_match = re.search(r'\b(\d{2}/\d{2}/\d{4})\b', sig_valor)
                                if fecha_match:
                                    fecha_desde = fecha_match.group(1)

                    if nombre and dni:
                        representante = RepresentanteLegal(
                            nombre=nombre,
                            cargo=cargo or "REPRESENTANTE LEGAL",
                            tipo_doc="DNI",
                            numero_doc=dni,
                            fecha_desde=fecha_desde or ""
                        )
                        representantes.append(representante)

            i += 1

        # Eliminar duplicados
        return self._eliminar_duplicados(representantes)

    def _procesar_fila_mejorada(self, row_data: List[str]) -> Optional[RepresentanteLegal]:
        """Procesar una fila de tabla mejorada"""
        if not row_data or len(row_data) < 2:
            return None

        nombre = ""
        cargo = ""
        dni = ""

        # Buscar en cada celda
        for data in row_data:
            data = data.strip()
            if not data:
                continue

            # Buscar DNI
            dni_match = re.search(r'\b\d{8}\b', data)
            if dni_match:
                dni = dni_match.group()
                continue

            # Buscar nombre (texto largo con letras)
            if (len(data) > 10 and
                any(char.isalpha() for char in data) and
                not any(kw in data.upper() for kw in ['RUC', 'FECHA', 'ESTADO'])):
                nombre = data
                continue

            # Buscar cargo
            if any(cargo_kw in data.upper() for cargo_kw in [
                'GERENTE', 'DIRECTOR', 'ADMINISTRADOR', 'REPRESENTANTE',
                'PRESIDENTE', 'APODERADO'
            ]):
                cargo = data

        # Crear representante si tenemos suficiente información
        if nombre and (dni or cargo):
            return RepresentanteLegal(
                nombre=nombre,
                cargo=cargo or "REPRESENTANTE LEGAL",
                tipo_doc="DNI",
                numero_doc=dni,
                fecha_desde=""
            )

        return None

    def _extraer_representante_de_texto(self, texto: str) -> Optional[RepresentanteLegal]:
        """Extraer representante de un bloque de texto"""
        try:
            # Buscar DNI
            dni_match = re.search(r'\b\d{8}\b', texto)
            dni = dni_match.group() if dni_match else ""

            # Buscar nombre (texto largo)
            lineas = texto.split('\n')
            nombre = ""
            cargo = ""

            for linea in lineas:
                linea = linea.strip()
                if len(linea) > 15 and linea.isupper() and any(char.isalpha() for char in linea):
                    if not any(kw in linea for kw in ['RUC:', 'FECHA:', 'ESTADO:', 'DIRECCIÓN:']):
                        nombre = linea

                if any(cargo_kw in linea.upper() for cargo_kw in [
                    'GERENTE', 'DIRECTOR', 'ADMINISTRADOR', 'REPRESENTANTE'
                ]):
                    cargo = linea

            if nombre and (dni or cargo):
                return RepresentanteLegal(
                    nombre=nombre,
                    cargo=cargo or "REPRESENTANTE LEGAL",
                    tipo_doc="DNI",
                    numero_doc=dni,
                    fecha_desde=""
                )

        except Exception as e:
            logger.warning(f"Error extrayendo representante de texto: {e}")

        return None

    def _contiene_info_representante(self, texto: str) -> bool:
        """Verificar si un texto contiene información de representante"""
        texto_upper = texto.upper()

        # Debe tener nombre y alguna indicación de cargo o DNI
        tiene_nombre = len(texto) > 20 and any(char.isalpha() for char in texto)
        tiene_cargo = any(kw in texto_upper for kw in [
            'GERENTE', 'DIRECTOR', 'ADMINISTRADOR', 'REPRESENTANTE',
            'PRESIDENTE', 'APODERADO'
        ])
        tiene_dni = bool(re.search(r'\b\d{8}\b', texto))

        return tiene_nombre and (tiene_cargo or tiene_dni)

    def _eliminar_duplicados(self, representantes: List[RepresentanteLegal]) -> List[RepresentanteLegal]:
        """Eliminar duplicados basado en DNI o nombre"""
        unicos = []
        vistos = set()

        for rep in representantes:
            # Crear clave única basada en DNI o nombre
            clave = rep.numero_doc or rep.nombre

            if clave not in vistos:
                vistos.add(clave)
                unicos.append(rep)

        return unicos

    async def _extraer_datos_basicos_mejorado(self, page, ruc: str) -> Dict[str, str]:
        """Extraer datos básicos mejorado"""
        logger.info("📋 Extrayendo datos básicos...")

        datos = {
            "razon_social": "No disponible",
            "estado": "ACTIVO",
            "direccion": "No disponible"
        }

        try:
            # Esperar a que cargue el contenido
            await page.wait_for_timeout(2000)

            # Buscar razón social en h4
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

            # Buscar estado
            texto_completo = await page.inner_text('body')
            if "ACTIVO" in texto_completo.upper():
                datos["estado"] = "ACTIVO"
            elif "INACTIVO" in texto_completo.upper():
                datos["estado"] = "INACTIVO"

            # Buscar dirección (patrones mejorados)
            direccion_patterns = [
                r'Domicilio Fiscal:\s*(.+)',
                r'Dirección:\s*(.+)',
                r'AV\.\s*[A-ZÁÉÍÓÚÑ\s]+',
                r'JR\.\s*[A-ZÁÉÍÓÚÑ\s]+',
                r'CALLE\s*[A-ZÁÉÍÓÚÑ\s]+',
                r'CAL\.\s*[A-ZÁÉÍÓÚÑ\s]+',
                r'PSJE\.\s*[A-ZÁÉÍÓÚÑ\s]+'
            ]

            for pattern in direccion_patterns:
                match = re.search(pattern, texto_completo, re.IGNORECASE)
                if match:
                    datos["direccion"] = match.group(1).strip() if match.group(1) else match.group(0).strip()
                    logger.info(f"✅ Dirección encontrada: {datos['direccion']}")
                    break

        except Exception as e:
            logger.warning(f"Error extrayendo datos básicos: {e}")

        return datos

    async def _verificar_captcha(self, page) -> bool:
        """Verificar si hay CAPTCHA"""
        captcha_selectors = ["#txtCodigo", "#txtCaptcha", "img[src*='captcha']"]

        for selector in captcha_selectors:
            try:
                if await page.is_visible(selector, timeout=1000):
                    return True
            except:
                continue
        return False

    async def _debug_estructura_pagina(self, page):
        """Depurar estructura de página para análisis"""
        try:
            # Guardar screenshot para depuración
            await page.screenshot(path="/tmp/sunat_debug.png", full_page=True)

            # Guardar HTML
            html_content = await page.content()
            with open("/tmp/sunat_debug.html", "w", encoding="utf-8") as f:
                f.write(html_content)

            logger.info("📸 Debug guardado en /tmp/sunat_debug.png y /tmp/sunat_debug.html")
        except:
            pass

    def _validar_ruc(self, ruc: str) -> bool:
        """Validar RUC"""
        if not ruc or len(ruc) != 11 or not ruc.isdigit():
            return False
        return ruc[:2] in ['10', '20']


# Instancia singleton
sunat_service_improved = SUNATServiceImproved()