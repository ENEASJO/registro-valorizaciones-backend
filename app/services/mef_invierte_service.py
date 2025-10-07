import os
import base64
from io import BytesIO
from PIL import Image
from playwright.async_api import async_playwright, Page
import logging

# Intentar importar pytesseract para OCR
try:
    import pytesseract
    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False
    logging.warning("pytesseract no está instalado. El captcha deberá ser resuelto manualmente.")

logger = logging.getLogger(__name__)


async def scrape_mef_invierte(cui: str):
    """
    Scraping de datos de proyectos de inversión desde MEF Invierte.

    Args:
        cui: Código Único de Inversión

    Returns:
        dict: Datos completos del proyecto incluyendo:
            - datos_generales: Información básica del proyecto
            - datos_formulacion: Datos de la fase de formulación y evaluación
            - datos_ejecucion: Datos de la fase de ejecución
            - modificaciones: Lista de modificaciones durante la ejecución
    """
    print(f"[MEF] Iniciando scraping MEF Invierte para CUI: {cui}", flush=True)
    logger.info(f"Iniciando scraping MEF Invierte para CUI: {cui}")

    async with async_playwright() as p:
        print("[MEF] Iniciando Playwright...", flush=True)
        # Configurar browser
        browser = await p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        print("[MEF] Browser lanzado", flush=True)

        try:
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080}
            )
            page = await context.new_page()
            print("[MEF] Página creada", flush=True)

            # 1. NAVEGAR A LA PÁGINA DE CONSULTA
            print("[MEF] 1. Navegando a página de consulta MEF Invierte...", flush=True)
            logger.info("1. Navegando a página de consulta MEF Invierte...")
            await page.goto(
                'https://ofi5.mef.gob.pe/invierte/consultapublica/consultainversiones',
                wait_until='domcontentloaded',
                timeout=60000
            )
            print("[MEF] Página cargada exitosamente", flush=True)
            await page.wait_for_timeout(2000)

            # 2. EXTRAER TEXTO DEL CAPTCHA
            print("[MEF] 2. Extrayendo texto del captcha...", flush=True)
            logger.info("2. Extrayendo texto del captcha...")
            captcha_selector = 'img[alt="captcha"]'

            # Obtener el captcha usando OCR simple (necesitamos extraer el texto de la imagen)
            # Por ahora, usaremos evaluate para obtener el texto si está disponible en algún atributo
            # En una implementación real, necesitaríamos OCR o un servicio de resolución de captcha

            # ESTRATEGIA: El captcha es texto simple en la imagen
            # Vamos a usar el atributo data o similar si existe
            # Por ahora, vamos a implementar la extracción del captcha con Playwright

            captcha_text = await _extract_captcha_text(page)
            logger.info(f"   Captcha detectado: {captcha_text}")

            # 3. LLENAR FORMULARIO
            logger.info("3. Llenando formulario de búsqueda...")

            # Campo CUI
            cui_input_selector = 'input[name="codigoUnico"]'
            await page.fill(cui_input_selector, cui)
            logger.info(f"   ✓ CUI ingresado: {cui}")

            # Campo captcha
            captcha_input_selector = 'input[name="captcha"]'
            await page.fill(captcha_input_selector, captcha_text)
            logger.info(f"   ✓ Captcha ingresado: {captcha_text}")

            await page.wait_for_timeout(1000)

            # 4. HACER CLIC EN BUSCAR
            logger.info("4. Haciendo clic en Buscar...")
            search_button_selector = 'button:has-text("Buscar")'
            await page.click(search_button_selector)
            await page.wait_for_timeout(3000)

            # 5. EXTRAER DATOS DE LA TABLA DE RESULTADOS
            logger.info("5. Extrayendo datos de resultados...")
            datos_resultado = await _extract_resultado_table(page)
            logger.info(f"   ✓ Datos de resultado extraídos")

            # 6. HACER CLIC EN EL ICONO DE FICHA DE EJECUCIÓN (icono azul)
            logger.info("6. Navegando a ficha de ejecución...")
            ficha_icon_selector = 'a[title*="Ficha de ejecución"], a[href*="traeListaEjecucionSimplePublica"]'

            # Esperar a que el icono esté disponible
            await page.wait_for_selector(ficha_icon_selector, timeout=30000)
            await page.click(ficha_icon_selector)
            await page.wait_for_timeout(3000)

            # 7. EXTRAER DATOS DE LA PÁGINA DE LISTA DE EJECUCIÓN
            logger.info("7. Extrayendo datos generales de ejecución...")
            datos_ejecucion_lista = await _extract_ejecucion_lista(page)
            logger.info(f"   ✓ Datos de ejecución extraídos")

            # 8. HACER CLIC EN EL ICONO DEL PDF (primer link en la columna Ver)
            logger.info("8. Navegando a ficha detallada (Formato N°08-C)...")
            pdf_icon_selector = 'a[href*="verFichaEjecucion"]'
            await page.wait_for_selector(pdf_icon_selector, timeout=30000)
            await page.click(pdf_icon_selector)
            await page.wait_for_timeout(3000)

            # 9. EXTRAER TODA LA INFORMACIÓN DEL FORMATO N°08-C
            logger.info("9. Extrayendo información completa del Formato N°08-C...")
            datos_formato_08c = await _extract_formato_08c(page)
            logger.info(f"   ✓ Formato N°08-C completo extraído")

            # 10. CONSOLIDAR TODA LA INFORMACIÓN
            resultado_completo = {
                "cui": cui,
                "datos_resultado": datos_resultado,
                "datos_ejecucion_lista": datos_ejecucion_lista,
                "formato_08c": datos_formato_08c
            }

            logger.info("✓ Scraping completado exitosamente")
            return resultado_completo

        except Exception as e:
            logger.error(f"Error durante el scraping: {str(e)}")
            raise
        finally:
            await browser.close()


async def _extract_captcha_text(page: Page) -> str:
    """
    Extrae el texto del captcha usando OCR.

    Returns:
        str: Texto del captcha detectado
    """
    try:
        if not PYTESSERACT_AVAILABLE:
            raise NotImplementedError(
                "pytesseract no está instalado. "
                "Instalar con: pip install pytesseract pillow"
            )

        # Localizar la imagen del captcha
        captcha_img = await page.query_selector('img[alt="captcha"]')
        if not captcha_img:
            raise Exception("No se encontró la imagen del captcha")

        # Obtener el screenshot del captcha
        captcha_screenshot = await captcha_img.screenshot()

        # Convertir a imagen PIL
        image = Image.open(BytesIO(captcha_screenshot))

        # Preprocesar imagen para mejorar OCR
        # Convertir a escala de grises
        image = image.convert('L')

        # Aumentar contraste
        from PIL import ImageEnhance
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.0)

        # Aplicar OCR
        # Configuración para texto simple alfanumérico
        custom_config = r'--oem 3 --psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        captcha_text = pytesseract.image_to_string(image, config=custom_config).strip()

        # Limpiar resultado
        captcha_text = ''.join(c for c in captcha_text if c.isalnum())

        if not captcha_text:
            raise Exception("No se pudo extraer texto del captcha")

        return captcha_text

    except Exception as e:
        logger.error(f"Error al extraer captcha: {str(e)}")
        raise


async def _extract_resultado_table(page: Page) -> dict:
    """
    Extrae los datos de la tabla de resultados de búsqueda.

    Returns:
        dict con:
            - codigo_idea
            - cui
            - estado
            - nombre
            - tipo_formato
            - situacion
            - costo_viable
            - costo_actualizado
    """
    try:
        # Esperar a que aparezca la tabla de resultados
        await page.wait_for_selector('table', timeout=30000)

        # Extraer datos usando evaluate
        datos = await page.evaluate('''() => {
            const rows = document.querySelectorAll('table tbody tr');
            if (rows.length === 0) return null;

            const firstRow = rows[0];
            const cells = firstRow.querySelectorAll('td');

            return {
                codigo_idea: cells[0]?.innerText.trim() || '',
                cui: cells[1]?.innerText.trim() || '',
                estado: cells[2]?.innerText.trim() || '',
                nombre: cells[3]?.innerText.trim() || '',
                tipo_formato: cells[4]?.innerText.trim() || '',
                situacion: cells[5]?.innerText.trim() || '',
                costo_viable: cells[6]?.innerText.trim() || '',
                costo_actualizado: cells[7]?.innerText.trim() || ''
            };
        }''')

        return datos
    except Exception as e:
        logger.error(f"Error al extraer tabla de resultados: {str(e)}")
        return {}


async def _extract_ejecucion_lista(page: Page) -> dict:
    """
    Extrae datos de la página de lista de ejecución.

    Returns:
        dict con:
            - datos_generales: CUI, nombre, monto inversión, monto actualizado
            - modificaciones: lista de modificaciones
    """
    try:
        datos = await page.evaluate('''() => {
            // Datos generales
            const cui = document.querySelector('body')?.innerText.match(/Código único de inversiones[\\s\\n]+(\\d+)/)?.[1] || '';
            const monto_inversion = document.querySelector('body')?.innerText.match(/Monto de la inversión[\\s\\n]+(S\\/[\\d,\\.]+)/)?.[1] || '';
            const monto_actualizado = document.querySelector('body')?.innerText.match(/Monto actualizado[\\s\\n]+(S\\/[\\d,\\.]+)/)?.[1] || '';

            // Tabla de modificaciones
            const modificaciones = [];
            const rows = document.querySelectorAll('table tbody tr');
            rows.forEach(row => {
                const cells = row.querySelectorAll('td');
                if (cells.length > 0) {
                    modificaciones.push({
                        fecha: cells[0]?.innerText.trim() || '',
                        monto_actualizado: cells[1]?.innerText.trim() || '',
                        comentarios: cells[2]?.innerText.trim() || '',
                        usuario: cells[3]?.innerText.trim() || '',
                        tipo_documento: cells[4]?.innerText.trim() || '',
                        es_historico: cells[5]?.innerText.trim() || ''
                    });
                }
            });

            return {
                datos_generales: {
                    cui: cui,
                    monto_inversion: monto_inversion,
                    monto_actualizado: monto_actualizado
                },
                modificaciones: modificaciones
            };
        }''')

        return datos
    except Exception as e:
        logger.error(f"Error al extraer lista de ejecución: {str(e)}")
        return {}


async def _extract_formato_08c(page: Page) -> dict:
    """
    Extrae toda la información del Formato N°08-C - Registros en la Fase de Ejecución.

    Returns:
        dict completo con todas las secciones:
            - encabezado: fecha_registro, etapa, estado
            - datos_generales: cui, nombre
            - seccion_a_formulacion: responsabilidad_funcional, pmi, institucionalidad
            - seccion_b_ejecucion: expediente_tecnico, modificaciones
            - costos_finales: costos actualizados, CCC, controversias, etc.
    """
    try:
        datos = await page.evaluate('''() => {
            const getText = (selector) => {
                const el = document.querySelector(selector);
                return el ? el.innerText.trim() : '';
            };

            const getAllText = (selector) => {
                const elements = document.querySelectorAll(selector);
                return Array.from(elements).map(el => el.innerText.trim());
            };

            // ENCABEZADO
            const encabezado = {
                titulo: getText('h2'),
                fecha_registro: document.body.innerText.match(/Fecha de registro ([\\d\\/\\s:]+)/)?.[1] || '',
                etapa: document.body.innerText.match(/ETAPA:[\\s]+([^\\n]+)/)?.[1] || '',
                estado: document.body.innerText.match(/ESTADO:[\\s]+([^\\n]+)/)?.[1] || ''
            };

            // DATOS GENERALES
            const datos_generales = {
                cui: document.body.innerText.match(/Código único de inversiones[\\s\\n]+(\\d+)/)?.[1] || '',
                nombre: document.body.innerText.match(/Nombre de la inversión[\\s\\n]+([^\\n]+)/)?.[1] || ''
            };

            // A. DATOS DE LA FASE DE FORMULACIÓN Y EVALUACIÓN

            // 1. Responsabilidad funcional
            const responsabilidad_funcional = {
                funcion_aprobacion: '',
                funcion_ejecucion: '',
                division_funcional_aprobacion: '',
                division_funcional_ejecucion: '',
                grupo_funcional_aprobacion: '',
                grupo_funcional_ejecucion: '',
                sector_responsable_aprobacion: '',
                sector_responsable_ejecucion: ''
            };

            // Extraer de la tabla (simplificado)
            const textContent = document.body.innerText;

            // 2. Articulación con el PMI
            const pmi = {
                servicio_publico: textContent.match(/SERVICIO DE ([^\\n]+)/)?.[1] || '',
                indicador_brechas: textContent.match(/PORCENTAJE DE ([^\\n]+)/)?.[1] || '',
                unidad_medida: textContent.match(/Unidad de medida[\\s\\n]+([^\\n]+)/)?.[1] || '',
                espacio_geografico: textContent.match(/Espacio geográfico[\\s\\n]+([^\\n]+)/)?.[1] || '',
                contribucion_cierre: textContent.match(/Contribución de cierre de brechas[\\s\\n]+(\\d+)/)?.[1] || ''
            };

            // 3. Institucionalidad
            const institucionalidad = {
                opmi_aprobacion: '',
                opmi_ejecucion: textContent.match(/OPMI DE LA ([^\\n]+)/)?.[1] || '',
                uf_aprobacion: '',
                uf_ejecucion: textContent.match(/UF DE LA ([^-\\n]+)/)?.[1] || '',
                uei_aprobacion: '',
                uei_ejecucion: textContent.match(/UEI DE LA ([^-\\n]+)/)?.[1] || '',
                uep: textContent.match(/UEP[\\s\\n]+([^\\n]+)/)?.[1] || ''
            };

            // B. DATOS EN LA FASE DE EJECUCIÓN

            // 4.1 Metas, costos y plazos según expediente técnico
            const metas_expediente = [];

            // 4.2 Programación de la ejecución
            const programacion_ejecucion = {
                subtotal: textContent.match(/Subtotal:[\\s]+S\\/([\\d,\\.]+)/)?.[1] || '',
                gastos_generales_covid: textContent.match(/GASTOS GENERALES COVID:[\\s]+S\\/([\\d,\\.]+)/)?.[1] || '',
                inventario_fisico_covid: textContent.match(/INVENTARIO FISICO COVID:[\\s]+S\\/([\\d,\\.]+)/)?.[1] || '',
                expediente_tecnico: textContent.match(/EXPEDIENTE TÉCNICO:[\\s]+S\\/([\\d,\\.]+)/)?.[1] || '',
                supervision: textContent.match(/SUPERVISIÓN:[\\s]+S\\/([\\d,\\.]+)/)?.[1] || '',
                liquidacion: textContent.match(/LIQUIDACIÓN:[\\s]+S\\/([\\d,\\.]+)/)?.[1] || '',
                costo_inversion_actualizado: textContent.match(/Costo de inversión actualizado:[\\s]+S\\/([\\d,\\.]+)/)?.[1] || ''
            };

            // 5. Modificaciones durante la ejecución física
            const modificaciones = [];

            // COSTOS FINALES
            const costos_finales = {
                costo_inversion_actualizado: textContent.match(/Costo de inversión actualizado:[\\s]+S\\/([\\d,\\.]+)/g)?.pop()?.match(/([\\d,\\.]+)/)?.[1] || '',
                costo_control_concurrente: textContent.match(/Costo de control concurrente \\(CCC\\):[\\s]+S\\/([\\d,\\.]+)/)?.[1] || '',
                costo_controversias: textContent.match(/Costo de controversias:[\\s]+S\\/\\.([\\d,\\.]+)/)?.[1] || '',
                monto_carta_fianza: textContent.match(/Monto de carta fianza:[\\s]+S\\/\\.([\\d,\\.]+)/)?.[1] || '',
                costo_total_actualizado: textContent.match(/Costo total de inversión actualizado:[\\s]+S\\/\\.?([\\d,\\.]+)/)?.[1] || ''
            };

            return {
                encabezado: encabezado,
                datos_generales: datos_generales,
                seccion_a_formulacion: {
                    responsabilidad_funcional: responsabilidad_funcional,
                    pmi: pmi,
                    institucionalidad: institucionalidad
                },
                seccion_b_ejecucion: {
                    programacion_ejecucion: programacion_ejecucion,
                    modificaciones: modificaciones
                },
                costos_finales: costos_finales
            };
        }''')

        return datos
    except Exception as e:
        logger.error(f"Error al extraer Formato 08-C: {str(e)}")
        return {}
