"""
Servicio para consultas SEACE (Sistema Electrónico de Contrataciones del Estado)
"""
import logging
import re
from typing import Optional
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError, Page

from app.models.seace import ObraSEACE
from app.utils.exceptions import ValidationException, ExtractionException
from app.utils.playwright_helper import get_browser_launch_options

logger = logging.getLogger(__name__)


class SEACEService:
    """Servicio para consultar datos de obras en SEACE"""

    def __init__(self):
        self.base_url = "https://prod2.seace.gob.pe/seacebus-uiwd-pub/buscadorPublico/buscadorPublico.xhtml"
        self.timeout = 120000  # 120 seconds (2 minutes) para permitir scraping completo

    async def consultar_obra(self, cui: str, anio: int) -> ObraSEACE:
        """
        Consulta información completa de una obra en SEACE

        Args:
            cui: Código Único de Inversión
            anio: Año de la convocatoria

        Returns:
            ObraSEACE: Información completa de la obra

        Raises:
            ValidationException: Si los parámetros no son válidos
            ExtractionException: Si hay errores en la extracción
        """
        logger.info(f"=== INICIANDO CONSULTA SEACE PARA CUI: {cui}, AÑO: {anio} ===")

        # Validar CUI
        if not self._validar_cui(cui):
            logger.error(f"CUI inválido: {cui}")
            raise ValidationException(f"CUI inválido: {cui}")

        # Validar año
        if not (2000 <= anio <= 2100):
            logger.error(f"Año inválido: {anio}")
            raise ValidationException(f"Año inválido: {anio}. Debe estar entre 2000 y 2100")

        logger.info(f"CUI {cui} y año {anio} validados correctamente")

        async with async_playwright() as p:
            launch_options = get_browser_launch_options(headless=True)
            browser = await p.chromium.launch(**launch_options)

            try:
                context = await browser.new_context(
                    viewport={'width': 1280, 'height': 720},
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )

                page = await context.new_page()

                # Navegar a SEACE
                logger.info("Navegando a página principal de SEACE")
                await page.goto(self.base_url, timeout=60000, wait_until='domcontentloaded')
                logger.info("Página SEACE cargada")

                # Hacer clic en la pestaña "Buscador de Procedimientos de Selección"
                logger.info("Haciendo clic en pestaña de búsqueda de procedimientos")
                await page.click('a:has-text("Buscador de Procedimientos de Selección")', timeout=20000)
                logger.info("Pestaña clickeada")

                # Esperar a que aparezca el formulario de búsqueda
                logger.info("Esperando formulario de búsqueda")
                await page.wait_for_selector('#tbBuscador\\:idFormBuscarProceso\\:CUI', timeout=60000, state='visible')
                logger.info("Formulario disponible")

                # Realizar búsqueda
                await self._ejecutar_busqueda(page, cui, anio)

                # Navegar al historial de contratación
                await self._navegar_a_historial(page)

                # Navegar a la ficha de selección
                await self._navegar_a_ficha_seleccion(page)

                # Extraer datos completos de la ficha de selección
                logger.info(f"🚀 Iniciando extracción de datos completos para CUI: {cui}")
                obra_data = await self._extraer_datos_completos(page, cui, anio)

                # Navegar a "Ver integrantes y encargado" para extraer el número de contrato
                await self._navegar_a_integrantes(page)
                numero_contrato = await self._extraer_numero_contrato(page)

                # Actualizar obra_data con el número de contrato si se extrajo
                if numero_contrato:
                    obra_data.numero_contrato = numero_contrato

                logger.info(f"✅ Extracción de datos completos completada para CUI: {cui}")

                logger.info(f"Consulta SEACE completada exitosamente para CUI: {cui}")
                return obra_data

            except PlaywrightTimeoutError as e:
                logger.error(f"Timeout en consulta SEACE para CUI {cui}: {str(e)}")
                raise ExtractionException(f"Timeout al consultar SEACE: {str(e)}")

            except Exception as e:
                logger.error(f"Error en consulta SEACE para CUI {cui}: {str(e)}")
                raise ExtractionException(f"Error al consultar SEACE: {str(e)}")

            finally:
                await browser.close()

    def _validar_cui(self, cui: str) -> bool:
        """Valida el formato del CUI"""
        if not cui or len(cui) < 7 or len(cui) > 10:
            return False
        if not cui.isdigit():
            return False
        return True

    async def _ejecutar_busqueda(self, page: Page, cui: str, anio: int):
        """Ejecuta la búsqueda inicial en SEACE"""
        logger.info(f"Ejecutando búsqueda para CUI: {cui}, Año: {anio}")

        try:
            # Llenar el campo CUI (ya está visible del paso anterior)
            cui_input = await page.query_selector('#tbBuscador\\:idFormBuscarProceso\\:CUI')
            await cui_input.fill(cui)
            logger.info(f"CUI {cui} ingresado")

            # Cambiar el año seleccionando del dropdown
            year_selector = '#tbBuscador\\:idFormBuscarProceso\\:anioConvocatoria'
            await page.select_option(year_selector, str(anio))
            logger.info(f"Año {anio} seleccionado en dropdown")

            # Esperar a que el cambio se procese
            await page.wait_for_timeout(1000)

            # Hacer clic en el botón Buscar
            buscar_button = await page.query_selector('#tbBuscador\\:idFormBuscarProceso\\:btnBuscarSelToken')
            await buscar_button.click()
            logger.info("Botón Buscar clickeado")

            # Esperar a que termine la actividad de red después del clic
            logger.info("Esperando que termine la actividad de red")
            try:
                await page.wait_for_load_state('networkidle', timeout=45000)
                logger.info("Actividad de red completada")
            except Exception as e:
                logger.warning(f"Timeout esperando networkidle: {str(e)}, continuando...")

            # Esperar a que aparezcan los resultados - esperar por texto "Mostrando de"
            logger.info("Esperando que aparezcan los resultados de búsqueda")
            await page.wait_for_selector('text=Mostrando de', timeout=45000, state='visible')
            logger.info("Tabla de resultados encontrada")

            # Confirmar que la columna "Acciones" está visible
            await page.wait_for_selector('span.ui-outputlabel:text-is("Acciones")', timeout=10000, state='visible')
            logger.info("Resultados de búsqueda cargados completamente")

        except Exception as e:
            logger.error(f"Error ejecutando búsqueda: {str(e)}")
            raise ExtractionException(f"Error ejecutando búsqueda: {str(e)}")

    async def _navegar_a_historial(self, page: Page):
        """Navega al historial de contratación (primer ícono en Acciones)"""
        logger.info("Navegando a historial de contratación")

        try:
            # Buscar la tabla de resultados
            tabla_resultados = await page.wait_for_selector(
                '#tbBuscador\\:idFormBuscarProceso\\:pnlGrdResultadosProcesos table tbody tr:last-child',
                timeout=30000,
                state='visible'
            )

            # Buscar el primer ícono (historial) en la columna de Acciones
            historial_icon = await tabla_resultados.query_selector('td:last-child a.ui-commandlink:first-child')

            if not historial_icon:
                raise ExtractionException("No se encontró el ícono de historial")

            await historial_icon.click()
            logger.info("Clic en ícono de historial")

            # Esperar a que cargue el historial - buscar por texto "Visualizar historial"
            await page.wait_for_selector('text=Visualizar historial de contratación', timeout=30000, state='visible')
            logger.info("Historial cargado")

        except Exception as e:
            logger.error(f"Error navegando a historial: {str(e)}")
            raise ExtractionException(f"Error navegando a historial: {str(e)}")

    async def _navegar_a_ficha_seleccion(self, page: Page):
        """Navega a la ficha de selección (segundo ícono en la tabla de historial)"""
        logger.info("Navegando a ficha de selección")

        try:
            # Buscar todas las tablas y encontrar la que tiene la columna "Acciones"
            # En la página de historial, buscar el segundo ícono (ficha) en la primera fila
            ficha_icon = await page.wait_for_selector(
                'table tbody tr:first-child td:last-child a.ui-commandlink:nth-child(2)',
                timeout=30000,
                state='visible'
            )
            await ficha_icon.click()
            logger.info("Clic en ícono de ficha")

            # Esperar a que cargue la ficha - buscar el tab "Ficha de Seleccion"
            await page.wait_for_selector('text=Ficha de Seleccion', timeout=30000, state='visible')
            logger.info("Ficha cargada")

        except Exception as e:
            logger.error(f"Error navegando a ficha: {str(e)}")
            raise ExtractionException(f"Error navegando a ficha: {str(e)}")

    async def _navegar_a_integrantes(self, page: Page):
        """Navega a 'Ver integrantes y encargado' para extraer el número de contrato"""
        logger.info("Navegando a 'Ver integrantes y encargado'")

        try:
            # Buscar y hacer clic en el enlace
            integrantes_link = await page.wait_for_selector(
                'a:has-text("Ver integrantes y encargado")',
                timeout=30000,
                state='visible'
            )
            await integrantes_link.click()
            logger.info("Clic en 'Ver integrantes'")

            # Esperar a que cargue la página
            await page.wait_for_selector('span.ui-outputlabel:text-is("Tipo de documento")', timeout=30000, state='visible')
            logger.info("Página integrantes cargada")

        except Exception as e:
            logger.error(f"Error navegando a integrantes: {str(e)}")
            raise ExtractionException(f"Error navegando a integrantes: {str(e)}")

    async def _extraer_numero_contrato(self, page: Page) -> Optional[str]:
        """Extrae el número de contrato desde la página de integrantes"""
        logger.info("Extrayendo número de contrato")

        try:
            # Buscar el campo "Tipo de documento" que contiene el número de contrato
            numero_contrato = await self._extraer_texto_por_label(page, "Tipo de documento")

            if numero_contrato:
                logger.info(f"Número de contrato extraído: {numero_contrato}")
                return numero_contrato
            else:
                logger.warning("No se encontró el número de contrato")
                return None

        except Exception as e:
            logger.warning(f"Error extrayendo número de contrato: {str(e)}")
            return None

    async def _extraer_datos_completos(self, page: Page, cui: str, anio: int) -> ObraSEACE:
        """Extrae todos los datos de la ficha de selección"""
        logger.info("Extrayendo datos de la ficha de selección")

        try:
            # Extraer Nomenclatura
            nomenclatura = await self._extraer_texto_por_label(page, "Nomenclatura")

            # Extraer Número de Convocatoria
            numero_convocatoria = await self._extraer_texto_por_label(page, "N° Convocatoria")

            # Extraer Tipo Compra o Selección
            tipo_compra = await self._extraer_texto_por_label(page, "Tipo Compra o Selección")

            # Extraer Normativa Aplicable
            normativa_aplicable = await self._extraer_texto_por_label(page, "Normativa Aplicable")

            # Extraer Entidad Convocante
            entidad_convocante = await self._extraer_texto_por_label(page, "Entidad Convocante")

            # Extraer Objeto de Contratación
            objeto_contratacion = await self._extraer_texto_por_label(page, "Objeto de Contratación")

            # Extraer Descripción del Objeto
            descripcion = await self._extraer_texto_por_label(page, "Descripción del Objeto")

            # Extraer VR / VE / Cuantía de la contratación
            monto_str = await self._extraer_texto_por_label(page, "VR / VE / Cuantía de la contratación")
            monto_contractual = self._limpiar_monto(monto_str)

            # Extraer Fecha y Hora Publicación
            fecha_publicacion = await self._extraer_texto_por_label(page, "Fecha y Hora Publicación")

            # Crear objeto ObraSEACE
            obra_data = ObraSEACE(
                nomenclatura=nomenclatura or "",
                numero_contrato=None,  # Se extraerá después desde "Ver integrantes y encargado"
                normativa_aplicable=normativa_aplicable or "",
                objeto_contratacion=objeto_contratacion or "",
                descripcion=descripcion or "",
                monto_contractual=monto_contractual,
                cui=cui,
                anio=anio,
                numero_convocatoria=numero_convocatoria,
                entidad_convocante=entidad_convocante,
                fecha_publicacion=fecha_publicacion,
                tipo_compra=tipo_compra
            )

            logger.info(f"Datos extraídos exitosamente: {obra_data.dict()}")
            return obra_data

        except Exception as e:
            logger.error(f"Error extrayendo datos completos: {str(e)}")
            raise ExtractionException(f"Error extrayendo datos completos: {str(e)}")

    async def _extraer_texto_por_label(self, page: Page, label: str) -> Optional[str]:
        """Extrae el texto asociado a un label específico"""
        try:
            # Buscar el elemento que contiene el label
            selector = f'span.ui-outputlabel:text-is("{label}") ~ span.halfSizeText'

            # Intentar encontrar el elemento
            element = await page.query_selector(selector)

            if element:
                texto = await element.inner_text()
                texto = texto.strip()
                logger.info(f"Extraído {label}: {texto}")
                return texto
            else:
                logger.warning(f"No se encontró el elemento para {label}")
                return None

        except Exception as e:
            logger.warning(f"Error extrayendo {label}: {str(e)}")
            return None

    def _limpiar_monto(self, monto_str: Optional[str]) -> float:
        """Limpia el string del monto y lo convierte a float"""
        if not monto_str:
            return 0.0

        try:
            # Extraer solo los números y punto decimal
            # Ejemplo: "640,251.96 Soles" -> "640251.96"
            monto_limpio = re.sub(r'[^\d.]', '', monto_str.replace(',', ''))
            return float(monto_limpio)
        except Exception as e:
            logger.warning(f"Error limpiando monto '{monto_str}': {str(e)}")
            return 0.0


# Instancia del servicio
seace_service = SEACEService()
