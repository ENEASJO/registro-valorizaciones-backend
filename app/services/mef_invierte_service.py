"""
Servicio para scraping de datos desde MEF Invierte
Sistema de Banco de Inversiones del Ministerio de Economía y Finanzas

URL: https://ofi5.mef.gob.pe/invierte/consultapublica/consultainversiones
"""

from typing import Optional, Dict, Any
import asyncio
import logging

logger = logging.getLogger(__name__)


async def consultar_cui_mef(cui: str, timeout: int = 120000) -> Dict[str, Any]:
    """
    Consulta información de una inversión pública por su CUI en MEF Invierte

    Args:
        cui: Código Único de Inversiones (ejemplo: "2595080")
        timeout: Timeout en milisegundos para operaciones de Playwright

    Returns:
        Dict con la información de la inversión:
        {
            "codigo_idea": str,
            "cui": str,
            "codigo_snip": str,
            "estado": str,
            "nombre": str,
            "tipo_formato": str,
            "situacion": str,
            "costo_viable": float,
            "costo_actualizado": float,
            "tiene_ficha_ejecucion": bool,
            "tiene_ficha_seguimiento": bool
        }
    """
    from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

    try:
        async with async_playwright() as p:
            # Iniciar navegador
            browser = await p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )

            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )

            page = await context.new_page()

            # Navegar a la página
            logger.info(f"Navegando a MEF Invierte para CUI: {cui}")
            await page.goto(
                'https://ofi5.mef.gob.pe/invierte/consultapublica/consultainversiones',
                wait_until='domcontentloaded',
                timeout=timeout
            )

            # Esperar a que cargue el formulario
            await page.wait_for_selector('#divCaptcha', timeout=20000)

            # Extraer el texto del CAPTCHA (es texto HTML simple, no imagen)
            captcha_text = await page.evaluate('''() => {
                const captchaDiv = document.querySelector('#divCaptcha');
                if (captchaDiv) {
                    const cells = captchaDiv.querySelectorAll('td');
                    return Array.from(cells).map(cell => cell.textContent).join('');
                }
                return null;
            }''')

            if not captcha_text:
                raise ValueError("No se pudo extraer el texto del CAPTCHA")

            logger.info(f"CAPTCHA extraído: {captcha_text}")

            # Llenar el formulario
            await page.fill('input[type="text"]:nth-of-type(1)', cui)  # Campo CUI
            await page.fill('#txtCaptchaText', captcha_text)  # Campo CAPTCHA

            # Hacer clic en Buscar
            await page.click('button:has-text("Buscar")')

            # Esperar resultados (puede aparecer tabla o mensaje de "no hay resultados")
            try:
                # Esperar a que aparezca la fila con los resultados
                await page.wait_for_selector('table tbody tr td a', timeout=30000)

                # Extraer datos de la tabla de resultados
                resultado = await page.evaluate('''() => {
                    const firstRow = document.querySelector('table tbody tr');
                    if (!firstRow) return null;

                    const cells = firstRow.querySelectorAll('td');
                    if (cells.length < 8) return null;

                    // Función auxiliar para limpiar números
                    const parseNumber = (text) => {
                        if (!text || text === '--') return null;
                        return parseFloat(text.replace(/,/g, ''));
                    };

                    return {
                        codigo_idea: cells[0].textContent.trim(),
                        cui: cells[1].textContent.trim(),
                        codigo_snip: cells[2].textContent.trim(),
                        estado: cells[3].textContent.trim(),
                        nombre: cells[4].textContent.trim(),
                        tipo_formato: cells[5].textContent.trim(),
                        situacion: cells[6].textContent.trim(),
                        costo_viable: parseNumber(cells[7].textContent.trim()),
                        costo_actualizado: parseNumber(cells[8].textContent.trim()),
                        tiene_ficha_ejecucion: !!cells[9].querySelector('a'),
                        tiene_ficha_seguimiento: !!cells[10].querySelector('a')
                    };
                }''')

                await browser.close()

                if resultado:
                    logger.info(f"Inversión encontrada: {resultado['nombre'][:100]}")
                    return {
                        "success": True,
                        "data": resultado,
                        "fuente": "MEF Invierte"
                    }
                else:
                    logger.warning(f"No se encontró resultado para CUI: {cui}")
                    return {
                        "success": False,
                        "error": "No se encontró información para el CUI proporcionado",
                        "cui": cui
                    }

            except PlaywrightTimeout:
                # No hay resultados o timeout esperando resultados
                logger.warning(f"No se encontraron resultados para CUI: {cui}")
                await browser.close()
                return {
                    "success": False,
                    "error": "No se encontró información para el CUI proporcionado",
                    "cui": cui
                }

    except Exception as e:
        logger.error(f"Error consultando MEF Invierte para CUI {cui}: {str(e)}")
        return {
            "success": False,
            "error": f"Error al consultar MEF Invierte: {str(e)}",
            "cui": cui
        }


async def consultar_cui_mef_con_nombre(
    cui: Optional[str] = None,
    nombre: Optional[str] = None,
    timeout: int = 120000
) -> Dict[str, Any]:
    """
    Consulta inversión por CUI o nombre en MEF Invierte

    Args:
        cui: Código Único de Inversiones (opcional)
        nombre: Nombre o descripción de la inversión (opcional)
        timeout: Timeout en milisegundos

    Returns:
        Dict con resultados de la búsqueda
    """
    from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

    if not cui and not nombre:
        return {
            "success": False,
            "error": "Debe proporcionar al menos un CUI o nombre para buscar"
        }

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )

            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )

            page = await context.new_page()

            logger.info(f"Navegando a MEF Invierte - CUI: {cui}, Nombre: {nombre}")
            await page.goto(
                'https://ofi5.mef.gob.pe/invierte/consultapublica/consultainversiones',
                wait_until='domcontentloaded',
                timeout=timeout
            )

            await page.wait_for_selector('#divCaptcha', timeout=20000)

            # Extraer CAPTCHA
            captcha_text = await page.evaluate('''() => {
                const captchaDiv = document.querySelector('#divCaptcha');
                if (captchaDiv) {
                    const cells = captchaDiv.querySelectorAll('td');
                    return Array.from(cells).map(cell => cell.textContent).join('');
                }
                return null;
            }''')

            if not captcha_text:
                raise ValueError("No se pudo extraer el texto del CAPTCHA")

            logger.info(f"CAPTCHA extraído: {captcha_text}")

            # Llenar formulario según parámetros
            if cui:
                await page.fill('input[type="text"]:nth-of-type(1)', cui)

            if nombre:
                await page.fill('input[placeholder*="nombre"]', nombre)

            await page.fill('#txtCaptchaText', captcha_text)

            # Buscar
            await page.click('button:has-text("Buscar")')

            try:
                await page.wait_for_selector('table tbody tr td', timeout=30000)

                # Extraer todos los resultados
                resultados = await page.evaluate('''() => {
                    const rows = document.querySelectorAll('table tbody tr');
                    const parseNumber = (text) => {
                        if (!text || text === '--') return null;
                        return parseFloat(text.replace(/,/g, ''));
                    };

                    return Array.from(rows).map(row => {
                        const cells = row.querySelectorAll('td');
                        if (cells.length < 8) return null;

                        return {
                            codigo_idea: cells[0].textContent.trim(),
                            cui: cells[1].textContent.trim(),
                            codigo_snip: cells[2].textContent.trim(),
                            estado: cells[3].textContent.trim(),
                            nombre: cells[4].textContent.trim(),
                            tipo_formato: cells[5].textContent.trim(),
                            situacion: cells[6].textContent.trim(),
                            costo_viable: parseNumber(cells[7].textContent.trim()),
                            costo_actualizado: parseNumber(cells[8].textContent.trim()),
                            tiene_ficha_ejecucion: !!cells[9].querySelector('a'),
                            tiene_ficha_seguimiento: !!cells[10].querySelector('a')
                        };
                    }).filter(r => r !== null);
                }''')

                await browser.close()

                logger.info(f"Se encontraron {len(resultados)} resultados")
                return {
                    "success": True,
                    "data": resultados,
                    "count": len(resultados),
                    "fuente": "MEF Invierte"
                }

            except PlaywrightTimeout:
                logger.warning("No se encontraron resultados")
                await browser.close()
                return {
                    "success": False,
                    "error": "No se encontraron resultados para los criterios de búsqueda",
                    "data": []
                }

    except Exception as e:
        logger.error(f"Error en consulta MEF Invierte: {str(e)}")
        return {
            "success": False,
            "error": f"Error al consultar MEF Invierte: {str(e)}"
        }
