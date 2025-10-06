"""
Servicio para consultar información de obras en SEACE
"""
from playwright.async_api import async_playwright, Page, TimeoutError as PlaywrightTimeoutError
from typing import Optional
import logging

from app.models.seace import ObraSEACE
from app.utils.exceptions import ExtractionException

logger = logging.getLogger(__name__)


class SEACEService:
    """Servicio para extraer información de obras desde SEACE"""
    
    BASE_URL = "https://prod2.seace.gob.pe/seacebus-uiwd-pub/buscadorPublico/buscadorPublico.xhtml"
    
    async def consultar_obra(self, cui: str, anio: int) -> ObraSEACE:
        """
        Consulta información completa de una obra en SEACE por CUI y año
        
        Args:
            cui: Código Único de Inversión
            anio: Año de la convocatoria
            
        Returns:
            ObraSEACE con toda la información extraída
            
        Raises:
            ExtractionException: Si hay error en la extracción
        """
        logger.info(f"Iniciando consulta SEACE para CUI: {cui}, Año: {anio}")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            
            try:
                page = await browser.new_page()
                page.set_default_timeout(30000)  # 30 segundos timeout por defecto
                
                # Navegar a SEACE
                await self._navegar_a_seace(page)
                
                # Ejecutar búsqueda
                await self._ejecutar_busqueda(page, cui, anio)
                
                # Navegar al historial
                await self._navegar_a_historial(page)
                
                # Navegar a la ficha de selección
                await self._navegar_a_ficha_seleccion(page)
                
                # Extraer información de la ficha
                obra_info = await self._extraer_informacion_ficha(page, cui, anio)
                
                logger.info(f"Consulta SEACE exitosa para CUI {cui}")
                return obra_info
                
            except PlaywrightTimeoutError as e:
                logger.error(f"Timeout en consulta SEACE para CUI {cui}: {str(e)}")
                raise ExtractionException(f"Timeout consultando SEACE: {str(e)}")
            except Exception as e:
                logger.error(f"Error consultando SEACE para CUI {cui}: {str(e)}")
                raise ExtractionException(f"Error al consultar SEACE: {str(e)}")
            finally:
                await browser.close()
    
    async def _navegar_a_seace(self, page: Page):
        """Navega a la página principal de SEACE"""
        logger.info(f"Navegando a SEACE: {self.BASE_URL}")
        await page.goto(self.BASE_URL, wait_until='networkidle', timeout=60000)

        # Esperar a que el tab activo cargue completamente
        await page.wait_for_selector('.ui-tabs-selected.ui-state-active', timeout=30000, state='visible')
        logger.info("Tab de búsqueda activo")

        # Esperar tiempo adicional para que JavaScript inicialice el formulario
        # En headless puede tomar más tiempo que en modo gráfico
        await page.wait_for_timeout(8000)
        logger.info("Esperando inicialización del formulario (8 segundos)")

        # Verificar que el campo CUI exista (sin validar visibilidad estricta)
        # Los dos puntos en IDs JSF deben escaparse en querySelector
        cui_input_id = 'tbBuscador\\\\:idFormBuscarProceso\\\\:CUI'
        await page.wait_for_function(
            f'document.querySelector("#{cui_input_id}") !== null',
            timeout=30000
        )
        logger.info("Campo CUI encontrado - Página SEACE cargada correctamente")
    
    async def _ejecutar_busqueda(self, page: Page, cui: str, anio: int):
        """Ejecuta la búsqueda por CUI y año en SEACE"""
        logger.info(f"Ejecutando búsqueda: CUI={cui}, Año={anio}")

        try:
            # Seleccionar el año - PrimeFaces dropdown (click to open, then select)
            year_dropdown_id = 'tbBuscador\\:idFormBuscarProceso\\:anioConvocatoria'

            # Verificar que el dropdown exista (sin validar visibilidad estricta)
            # Los dos puntos en IDs JSF deben escaparse en querySelector
            year_dropdown_id_escaped = 'tbBuscador\\\\:idFormBuscarProceso\\\\:anioConvocatoria'
            await page.wait_for_function(
                f'document.querySelector("#{year_dropdown_id_escaped}") !== null',
                timeout=30000
            )
            logger.info("Dropdown de año encontrado")

            # Hacer clic en el dropdown usando JavaScript (bypass Playwright visibility check)
            await page.evaluate(f'''
                document.querySelector("#{year_dropdown_id_escaped}").click();
            ''')
            logger.info("Dropdown de año abierto (JavaScript click)")

            # Esperar a que aparezca el panel del dropdown y hacer clic en la opción usando JavaScript
            await page.wait_for_timeout(500)  # Esperar animación
            await page.evaluate(f'''
                const panel = document.querySelector("#{year_dropdown_id_escaped}_panel");
                if (panel) {{
                    const option = Array.from(panel.querySelectorAll("li")).find(li => li.textContent.trim() === "{anio}");
                    if (option) {{
                        option.click();
                    }}
                }}
            ''')
            logger.info(f"Año seleccionado: {anio} (JavaScript click)")

            # Ingresar el CUI usando JavaScript (bypass visibility check)
            cui_input_id_escaped = 'tbBuscador\\\\:idFormBuscarProceso\\\\:CUI'
            await page.evaluate(f'''
                const cuiInput = document.querySelector("#{cui_input_id_escaped}");
                if (cuiInput) {{
                    cuiInput.value = "{cui}";
                    cuiInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    cuiInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
                }}
            ''')
            logger.info(f"CUI ingresado: {cui} (JavaScript)")
            
            # Hacer clic en el botón "Buscar" usando JavaScript (bypass visibility check)
            await page.wait_for_timeout(1000)  # Esperar estabilización del formulario
            await page.evaluate('''
                const buscarButton = Array.from(document.querySelectorAll('button')).find(btn => btn.textContent.includes('Buscar'));
                if (buscarButton) {
                    buscarButton.click();
                }
            ''')
            logger.info("Clic en botón Buscar (JavaScript)")

            # Esperar a que aparezca el paginador (sin validar visibilidad estricta)
            logger.info("Esperando que aparezca el paginador de resultados")
            await page.wait_for_function(
                '''
                document.querySelector("#tbBuscador\\\\:idFormBuscarProceso\\\\:pnlGrdResultadosProcesos .ui-paginator-current") !== null
                ''',
                timeout=45000
            )
            logger.info("Paginador encontrado")

            # Esperar tiempo adicional para que SEACE termine de procesar la búsqueda
            # SEACE puede mostrar "0 a 0" inicialmente y luego actualizar a los resultados reales
            await page.wait_for_timeout(5000)
            logger.info("Esperando finalización de procesamiento SEACE (5 segundos)")

            # Verificar que haya resultados (no "0 a 0 del total 0")
            # Para query_selector CSS, usar escape simple (2 barras en Python string)
            paginator_selector_css = '#tbBuscador\\:idFormBuscarProceso\\:pnlGrdResultadosProcesos .ui-paginator-current'
            paginator = await page.query_selector(paginator_selector_css)
            if paginator:
                paginator_text = await paginator.inner_text()
                logger.info(f"Paginador: {paginator_text}")
                if 'total 0' in paginator_text.lower() or '0 a 0' in paginator_text.lower():
                    logger.error(f"No se encontraron resultados para CUI {cui}, año {anio}")
                    raise ExtractionException(f"No se encontraron resultados en SEACE para CUI {cui} en el año {anio}. Verifica que el CUI y el año sean correctos.")

            # Confirmar que la columna "Acciones" existe (sin validar visibilidad)
            await page.wait_for_function(
                'document.evaluate("//text()[contains(., \'Acciones\')]", document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue !== null',
                timeout=10000
            )
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
            # Esperar a que se cargue la tabla de historial
            await page.wait_for_selector('table tbody tr', timeout=30000, state='visible')

            # Buscar todos los enlaces en la columna de Acciones (última celda)
            # El segundo enlace (índice 1) es el ícono de ficha
            ficha_icons = await page.query_selector_all('table tbody tr td:last-child a.ui-commandlink')

            if len(ficha_icons) < 2:
                raise ExtractionException("No se encontró el ícono de ficha en el historial")

            # El segundo ícono (índice 1) es la ficha de selección
            await ficha_icons[1].click()
            logger.info("Clic en ícono de ficha")

            # Esperar a que cargue la ficha - buscar el tab "Ficha de Seleccion"
            await page.wait_for_selector('text=Ficha de Seleccion', timeout=30000, state='visible')
            logger.info("Ficha cargada")
            
        except Exception as e:
            logger.error(f"Error navegando a ficha: {str(e)}")
            raise ExtractionException(f"Error navegando a ficha: {str(e)}")
    
    async def _extraer_informacion_ficha(self, page: Page, cui: str, anio: int) -> ObraSEACE:
        """Extrae toda la información de la ficha de selección"""
        logger.info("Extrayendo información de la ficha")
        
        try:
            # Esperar a que la página cargue completamente
            await page.wait_for_timeout(2000)
            
            # Esperar a que aparezca un elemento clave de la ficha
            await page.wait_for_selector('text=Tipo de documento', timeout=30000, state='visible')
            logger.info("Ficha de documentos cargada")
            
            # Extraer información usando el método de búsqueda por label
            nomenclatura = await self._extraer_texto_por_label(page, "Nomenclatura")
            normativa_aplicable = await self._extraer_texto_por_label(page, "Normativa Aplicable")
            objeto_contratacion = await self._extraer_texto_por_label(page, "Objeto de Contratación")
            descripcion = await self._extraer_texto_por_label(page, "Descripción del Objeto")
            entidad_convocante = await self._extraer_texto_por_label(page, "Entidad Convocante")
            fecha_publicacion = await self._extraer_texto_por_label(page, "Fecha y Hora Publicación")
            tipo_compra = await self._extraer_texto_por_label(page, "Tipo Compra o Selección")
            numero_convocatoria = await self._extraer_texto_por_label(page, "N° Convocatoria")
            
            # Extraer monto contractual (formato especial)
            monto_text = await self._extraer_texto_por_label(page, "VR / VE / Cuantía de la contratación")
            monto_contractual = None
            if monto_text:
                # Limpiar el texto y convertir a float
                monto_limpio = monto_text.replace(',', '').replace(' ', '').strip()
                try:
                    monto_contractual = float(monto_limpio)
                except ValueError:
                    logger.warning(f"No se pudo convertir el monto: {monto_text}")
            
            # Validar que se hayan extraído datos mínimos
            if not nomenclatura:
                raise ExtractionException("No se pudo extraer la nomenclatura de la obra")
            
            # Crear objeto ObraSEACE
            obra = ObraSEACE(
                nomenclatura=nomenclatura or "",
                normativa_aplicable=normativa_aplicable or "",
                objeto_contratacion=objeto_contratacion or "",
                descripcion=descripcion or "",
                monto_contractual=monto_contractual,
                cui=cui,
                anio=anio,
                numero_convocatoria=numero_convocatoria,
                entidad_convocante=entidad_convocante,
                fecha_publicacion=fecha_publicacion,
                tipo_compra=tipo_compra,
                fuente="SEACE"
            )
            
            logger.info(f"Información extraída exitosamente: {nomenclatura}")
            return obra
            
        except Exception as e:
            logger.error(f"Error extrayendo información de la ficha: {str(e)}")
            raise ExtractionException(f"Error extrayendo información: {str(e)}")
    
    async def _extraer_texto_por_label(self, page: Page, label: str) -> Optional[str]:
        """Extrae el texto asociado a un label específico usando estructura de tabla"""
        try:
            # Buscar todas las filas de tabla
            rows = await page.query_selector_all('tr')
            
            for row in rows:
                # Buscar las celdas de la fila
                cells = await row.query_selector_all('td')
                if len(cells) >= 2:
                    # Primera celda contiene el label
                    label_text = await cells[0].inner_text()
                    label_text = label_text.strip()
                    
                    # Comparar con el label buscado (con o sin ":")
                    if label_text == label or label_text == f"{label}:":
                        # Segunda celda contiene el valor
                        value_text = await cells[1].inner_text()
                        value_text = value_text.strip()
                        logger.info(f"Extraído {label}: {value_text}")
                        return value_text
            
            logger.warning(f"No se encontró el elemento para {label}")
            return None
        
        except Exception as e:
            logger.warning(f"Error extrayendo {label}: {str(e)}")
            return None


# Singleton instance
seace_service = SEACEService()
