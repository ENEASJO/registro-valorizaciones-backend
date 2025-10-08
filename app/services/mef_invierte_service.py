"""
Servicio para scraping de datos desde MEF Invierte
Sistema de Banco de Inversiones del Ministerio de Economía y Finanzas

URL: https://ofi5.mef.gob.pe/invierte/consultapublica/consultainversiones
"""

from typing import Optional, Dict, Any
import asyncio
import logging

logger = logging.getLogger(__name__)


async def consultar_cui_mef(cui: str, timeout: int = 300000) -> Dict[str, Any]:
    """
    Consulta información COMPLETA de una inversión pública desde la Ficha de Ejecución en MEF Invierte

    Args:
        cui: Código Único de Inversiones (ejemplo: "2595080")
        timeout: Timeout en milisegundos para operaciones de Playwright

    Returns:
        Dict con TODA la información de la inversión desde la Ficha de Ejecución
    """
    from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

    try:
        async with async_playwright() as p:
            # Iniciar navegador con configuración simple (igual a Node que funciona)
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox'
                ]
            )

            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )

            page = await context.new_page()

            # PASO 1: Navegar a la página de búsqueda
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

            # PASO 2: Esperar resultados y hacer clic en "Ver ficha de ejecución"
            try:
                # Esperar a que aparezca la tabla con resultados
                await page.wait_for_selector('table tbody tr td a', timeout=30000)

                # Buscar el link de "Ver ficha de ejecución" (icono PDF en columna Ver)
                logger.info("Buscando link de ficha de ejecución")

                # Hacer clic en el primer icono de ficha de ejecución
                await page.click('table tbody tr td a[title*="ejecución"], table tbody tr td a[href*="ejecucion"]')

                # Esperar a que se abra la nueva página
                await page.wait_for_load_state('domcontentloaded', timeout=30000)

                logger.info(f"Navegado a ficha de ejecución, URL actual: {page.url}")

            except PlaywrightTimeout:
                logger.warning(f"No se encontraron resultados para CUI: {cui}")
                await browser.close()
                return {
                    "success": False,
                    "error": "No se encontró información para el CUI proporcionado",
                    "cui": cui
                }

            # PASO 3: Navegar a la ficha de ejecución completa
            ficha_url = f'https://ofi5.mef.gob.pe/invierte/ejecucion/verFichaEjecucion/{cui}'
            logger.info(f"Navegando a ficha de ejecución completa: {ficha_url}")
            await page.goto(ficha_url, wait_until='domcontentloaded', timeout=timeout)

            # Esperar a que cargue el formato
            await page.wait_for_selector('h2:has-text("Formato")', timeout=20000)

            # PASO 4: Extraer TODA la información de la ficha de ejecución
            resultado = await page.evaluate(r"""
                () => {
                    const bodyText = document.body.textContent;

                    // Helper para parsear números
                    const parseNumber = (text) => {
                        if (!text) return null;
                        const match = text.match(/([\d,]+\.[\d]{2})/);
                        return match ? parseFloat(match[1].replace(/,/g, '')) : null;
                    };

                    // DATOS BÁSICOS
                    const cuiMatch = bodyText.match(/Código único de inversiones[\s\S]*?(\d{7})/);
                    const cui = cuiMatch ? cuiMatch[1] : null;

                    const nombreMatch = bodyText.match(/Nombre de la inversión\s+([\s\S]*?)(?=A\. Datos)/);
                    const nombre = nombreMatch ? nombreMatch[1].trim() : null;

                    const estadoMatch = bodyText.match(/ESTADO:\s+([A-Z\s]+?)(?=Exportar|Historial)/);
                    const estado = estadoMatch ? estadoMatch[1].trim() : null;

                    const etapaMatch = bodyText.match(/ETAPA:\s+([^\n]+?)(?=ESTADO:)/);
                    const etapa = etapaMatch ? etapaMatch[1].trim() : null;

                    const fechaRegistroMatch = bodyText.match(/Fecha de registro\s+([\d/]+\s+[\d:]+)/);
                    const fecha_registro = fechaRegistroMatch ? fechaRegistroMatch[1] : null;

                    // A. DATOS DE FORMULACIÓN Y EVALUACIÓN

                    // 1. Responsabilidad funcional
                    const funcionMatch = bodyText.match(/Función[\s\S]*?Fase de Ejecución[\s\S]*?([A-Z\s]+)(?=[\s]*División funcional)/);
                    const funcion = funcionMatch ? funcionMatch[1].trim() : null;

                    const divisionMatch = bodyText.match(/División funcional[\s\S]*?Fase de Ejecución[\s\S]*?([A-Z\s]+)(?=[\s]*Grupo funcional)/);
                    const division_funcional = divisionMatch ? divisionMatch[1].trim() : null;

                    const grupoMatch = bodyText.match(/Grupo funcional[\s\S]*?Fase de Ejecución[\s\S]*?([A-Z\s]+?)(?=[\s]*Sector responsable)/);
                    const grupo_funcional = grupoMatch ? grupoMatch[1].trim() : null;

                    const sectorMatch = bodyText.match(/Sector responsable[\s\S]*?Fase de Ejecución[\s\S]*?([A-Z,\s]+?)(?=[\s]*2\. Articulación)/);
                    const sector_responsable = sectorMatch ? sectorMatch[1].trim() : null;

                    // 2. Articulación con PMI
                    const servicioMatch = bodyText.match(/SERVICIO DE ([A-Z\sÓÚÁÉÍ]+?)(?=PORCENTAJE)/);
                    const servicio_publico = servicioMatch ? servicioMatch[1].trim() : null;

                    const brechaMatch = bodyText.match(/PORCENTAJE DE LA POBLACIÓN ([A-Z\sÓÚÁÉÍ]+?)(?=PERSONAS)/);
                    const indicador_brecha = brechaMatch ? brechaMatch[1].trim() : null;

                    const espacioMatch = bodyText.match(/Espacio geográfico[\s\S]*?PERSONAS[\s\S]*?([A-Z]+)/);
                    const espacio_geografico = espacioMatch ? espacioMatch[1].trim() : null;

                    const contribucionMatch = bodyText.match(/Contribución de cierre de brechas[\s\S]*?(\d+)/);
                    const contribucion_brecha = contribucionMatch ? parseInt(contribucionMatch[1]) : null;

                    // 3. Institucionalidad
                    const opmiMatch = bodyText.match(/OPMI[\s\S]*?Fase de Ejecución[\s\S]*?\(([A-Z0-9]+)\s+-\s+([A-Z\sÓÚÁÉÍ]+?)\)/);
                    const opmi_codigo = opmiMatch ? opmiMatch[1] : null;
                    const opmi_responsable = opmiMatch ? opmiMatch[2].trim() : null;

                    const ufMatch = bodyText.match(/UF[\s\S]*?Fase de Ejecución[\s\S]*?\(([A-Z0-9]+)\s+-\s+([A-Z\sÓÚÁÉÍ]+?)\)/);
                    const uf_codigo = ufMatch ? ufMatch[1] : null;
                    const uf_responsable = ufMatch ? ufMatch[2].trim() : null;

                    const ueiMatch = bodyText.match(/UEI[\s\S]*?Fase de Ejecución[\s\S]*?\(([A-Z0-9]+)\s+-\s+([A-Z\sÓÚÁÉÍ]+?)\)/);
                    const uei_codigo = ueiMatch ? ueiMatch[1] : null;
                    const uei_responsable = ueiMatch ? ueiMatch[2].trim() : null;

                    const uepMatch = bodyText.match(/UEP[\s\S]*?(\d+)\s+-\s+([A-Z\sÓÚÁÉÍ]+)/);
                    const uep_codigo = uepMatch ? uepMatch[1] : null;
                    const uep_nombre = uepMatch ? uepMatch[2].trim() : null;

                    // B. DATOS EN FASE DE EJECUCIÓN

                    // 4.1 Metas según expediente técnico
                    const metas = [];

                    // Meta 1: MURO DE CONTENCION
                    const muro = bodyText.match(/OPTIMIZACIÓN[\s\S]*?CONSTRUCCION[\s\S]*?INFRAESTRUCTURA[\s\S]*?MURO DE CONTENCION[\s\S]*?M[\s\S]*?(\d+)/);
                    if (muro) {
                        metas.push({
                            tipo: "OPTIMIZACIÓN",
                            naturaleza: "CONSTRUCCION",
                            factor_productivo: "INFRAESTRUCTURA",
                            activo: "MURO DE CONTENCION",
                            unidad: "M",
                            cantidad: parseInt(muro[1])
                        });
                    }

                    // Meta 2: PTAR
                    const ptar = bodyText.match(/REHABILITACIÓN[\s\S]*?REPARACION[\s\S]*?INFRAESTRUCTURA[\s\S]*?PTAR[\s\S]*?M[\s\S]*?(\d+)/);
                    if (ptar) {
                        metas.push({
                            tipo: "REHABILITACIÓN",
                            naturaleza: "REPARACION",
                            factor_productivo: "INFRAESTRUCTURA",
                            activo: "PTAR",
                            unidad: "M",
                            cantidad: parseInt(ptar[1])
                        });
                    }

                    // 4.2 Programación de ejecución - EXTRAER FECHAS POR COMPONENTE
                    const modalidadMatch = bodyText.match(/ADMINISTRACIÓN INDIRECTA - POR CONTRATA/);
                    const modalidad_ejecucion = modalidadMatch ? "ADMINISTRACIÓN INDIRECTA - POR CONTRATA" : null;

                    // Fechas del MURO DE CONTENCION (primera meta física)
                    const muroFechas = bodyText.match(/MURO DE CONTENCION[\s\S]*?ADMINISTRACIÓN INDIRECTA[\s\S]*?(\d{1,2}\/\d{1,2}\/\d{4})[\s\S]*?(\d{1,2}\/\d{1,2}\/\d{4})[\s\S]*?(\d{1,2}\/\d{1,2}\/\d{4})/);
                    const fechas_muro = muroFechas ? {
                        inicio: muroFechas[1],
                        termino: muroFechas[2],
                        entrega: muroFechas[3]
                    } : null;

                    // Fechas de PTAR (segunda meta física)
                    const ptarFechas = bodyText.match(/REHABILITACIÓN[\s\S]*?REPARACION[\s\S]*?INFRAESTRUCTURA[\s\S]*?PTAR[\s\S]*?ADMINISTRACIÓN INDIRECTA[\s\S]*?(\d{1,2}\/\d{1,2}\/\d{4})[\s\S]*?(\d{1,2}\/\d{1,2}\/\d{4})[\s\S]*?(\d{1,2}\/\d{1,2}\/\d{4})/);
                    const fechas_ptar = ptarFechas ? {
                        inicio: ptarFechas[1],
                        termino: ptarFechas[2],
                        entrega: ptarFechas[3]
                    } : null;

                    // Fechas de EXPEDIENTE TÉCNICO
                    const expFechas = bodyText.match(/EXPEDIENTE TÉCNICO:[\s\S]*?ADMINISTRACIÓN INDIRECTA[\s\S]*?(\d{1,2}\/\d{1,2}\/\d{4})[\s\S]*?(\d{1,2}\/\d{1,2}\/\d{4})/);
                    const fechas_expediente = expFechas ? {
                        inicio: expFechas[1],
                        termino: expFechas[2]
                    } : null;

                    // Fechas de SUPERVISIÓN (original, antes de modificaciones)
                    const supFechas = bodyText.match(/SUPERVISIÓN:[\s\S]*?ADMINISTRACIÓN INDIRECTA[\s\S]*?(\d{1,2}\/\d{1,2}\/\d{4})[\s\S]*?(\d{1,2}\/\d{1,2}\/\d{4})/);
                    const fechas_supervision = supFechas ? {
                        inicio: supFechas[1],
                        termino: supFechas[2]
                    } : null;

                    // Fechas de LIQUIDACIÓN (original)
                    const liqFechas = bodyText.match(/LIQUIDACIÓN:[\s\S]*?ADMINISTRACIÓN INDIRECTA[\s\S]*?(\d{1,2}\/\d{1,2}\/\d{4})[\s\S]*?(\d{1,2}\/\d{1,2}\/\d{4})/);
                    const fechas_liquidacion = liqFechas ? {
                        inicio: liqFechas[1],
                        termino: liqFechas[2]
                    } : null;

                    // Costos según expediente técnico
                    const expedienteMatches = bodyText.match(/EXPEDIENTE TÉCNICO:[\s\S]*?S\/[\s]*?([\d,]+\.[\d]{2})/g);
                    const costo_expediente_tecnico = expedienteMatches && expedienteMatches.length > 0 ?
                        parseNumber(expedienteMatches[0]) : null;

                    const supervisionMatches = bodyText.match(/SUPERVISIÓN:[\s\S]*?S\/[\s]*?([\d,]+\.[\d]{2})/g);
                    const costo_supervision_original = supervisionMatches && supervisionMatches.length > 0 ?
                        parseNumber(supervisionMatches[0]) : null;

                    const liquidacionMatches = bodyText.match(/LIQUIDACIÓN:[\s\S]*?S\/[\s]*?([\d,]+\.[\d]{2})/g);
                    const costo_liquidacion = liquidacionMatches && liquidacionMatches.length > 0 ?
                        parseNumber(liquidacionMatches[0]) : null;

                    // Costos de inversión según expediente
                    const costoInvExpMatches = bodyText.match(/Costo de inversión actualizado:[\s\S]*?S\/[\s]*?([\d,]+\.[\d]{2})/g);
                    const costo_inversion_expediente = costoInvExpMatches && costoInvExpMatches.length > 0 ?
                        parseNumber(costoInvExpMatches[0]) : null;

                    // Subtotal según expediente
                    const subtotalMatch = bodyText.match(/Subtotal:[\s\S]*?S\/[\s]*?([\d,]+\.[\d]{2})/);
                    const subtotal_metas = parseNumber(subtotalMatch ? subtotalMatch[0] : null);

                    // 5. Modificaciones durante ejecución física
                    const documentos_modificacion = [];

                    // RGDUR
                    const rgdurMatches = bodyText.matchAll(/RGDUR Nº([^\s]+)[\s\S]*?\((\d{1,2}\/\d{1,2}\/\d{4})\)/g);
                    for (const match of rgdurMatches) {
                        documentos_modificacion.push({
                            tipo: "RGDUR",
                            numero: match[1],
                            fecha: match[2],
                            descripcion: "RGDUR"
                        });
                    }

                    // ADENDA
                    const adendaMatch = bodyText.match(/ADENDA (\d+ AL CONTRATO \d+-\d+)/);
                    if (adendaMatch) {
                        documentos_modificacion.push({
                            tipo: "ADENDA",
                            numero: adendaMatch[1],
                            descripcion: "ADENDA AL CONTRATO"
                        });
                    }

                    // INF (Informes técnicos)
                    const infMatches = bodyText.matchAll(/INF N° ([^\s]+)[\s\S]*?\((\d{1,2}\/\d{1,2}\/\d{4})\)/g);
                    for (const match of infMatches) {
                        documentos_modificacion.push({
                            tipo: "INFORME",
                            numero: match[1],
                            fecha: match[2],
                            descripcion: "CONSISTENCIA PMI"
                        });
                    }

                    // 5. Modificaciones durante ejecución - FECHAS MODIFICADAS POR COMPONENTE

                    // Fechas modificadas del MURO (sección 5)
                    const muroModFechas = bodyText.match(/5\. Modificaciones[\s\S]*?OPTIMIZACIÓN[\s\S]*?CONSTRUCCION[\s\S]*?INFRAESTRUCTURA[\s\S]*?MURO DE CONTENCION[\s\S]*?ADMINISTRACIÓN INDIRECTA[\s\S]*?(\d{1,2}\/\d{1,2}\/\d{4})[\s\S]*?(\d{1,2}\/\d{1,2}\/\d{4})[\s\S]*?(\d{1,2}\/\d{1,2}\/\d{4})/);
                    const fechas_muro_modificado = muroModFechas ? {
                        inicio: muroModFechas[1],
                        termino_vigente: muroModFechas[2],
                        entrega: muroModFechas[3]
                    } : null;

                    // Fechas modificadas de PTAR (sección 5)
                    const ptarModFechas = bodyText.match(/5\. Modificaciones[\s\S]*?REHABILITACIÓN[\s\S]*?REPARACION[\s\S]*?INFRAESTRUCTURA[\s\S]*?PTAR[\s\S]*?ADMINISTRACIÓN INDIRECTA[\s\S]*?(\d{1,2}\/\d{1,2}\/\d{4})[\s\S]*?(\d{1,2}\/\d{1,2}\/\d{4})[\s\S]*?(\d{1,2}\/\d{1,2}\/\d{4})/);
                    const fechas_ptar_modificado = ptarModFechas ? {
                        inicio: ptarModFechas[1],
                        termino_vigente: ptarModFechas[2],
                        entrega: ptarModFechas[3]
                    } : null;

                    // Fechas modificadas de SUPERVISIÓN (sección 5)
                    const supModFechas = bodyText.match(/5\. Modificaciones[\s\S]*?SUPERVISIÓN:[\s\S]*?ADMINISTRACIÓN INDIRECTA[\s\S]*?(\d{1,2}\/\d{1,2}\/\d{4})[\s\S]*?(\d{1,2}\/\d{1,2}\/\d{4})/);
                    const fechas_supervision_modificado = supModFechas ? {
                        inicio: supModFechas[1],
                        termino_vigente: supModFechas[2]
                    } : null;

                    // Fechas modificadas de LIQUIDACIÓN (sección 5)
                    const liqModFechas = bodyText.match(/5\. Modificaciones[\s\S]*?LIQUIDACIÓN:[\s\S]*?ADMINISTRACIÓN INDIRECTA[\s\S]*?(\d{1,2}\/\d{1,2}\/\d{4})[\s\S]*?(\d{1,2}\/\d{1,2}\/\d{4})/);
                    const fechas_liquidacion_modificado = liqModFechas ? {
                        inicio: liqModFechas[1],
                        termino_vigente: liqModFechas[2]
                    } : null;

                    // Costos modificados (última aparición - sección 5)
                    const supervisionModMatches = bodyText.match(/SUPERVISIÓN:[\s\S]*?S\/[\s]*?([\d,]+\.[\d]{2})/g);
                    const costo_supervision_modificado = supervisionModMatches && supervisionModMatches.length > 1 ?
                        parseNumber(supervisionModMatches[supervisionModMatches.length - 1]) : null;

                    const liquidacionModMatch = bodyText.match(/Fecha de término vigente[\s\S]*?LIQUIDACIÓN:[\s\S]*?S\/[\s]*?([\d,]+\.[\d]{2})/);
                    const costo_liquidacion_modificado = liquidacionModMatch ? parseNumber(liquidacionModMatch[0]) : null;

                    // Costo de inversión modificado
                    const costoInvModMatches = bodyText.match(/Costo de inversión actualizado:[\s\S]*?S\/[\s]*?([\d,]+\.[\d]{2})/g);
                    const costo_inversion_modificado = costoInvModMatches && costoInvModMatches.length > 1 ?
                        parseNumber(costoInvModMatches[costoInvModMatches.length - 1]) : null;

                    // Subtotal modificado
                    const subtotalModMatch = bodyText.match(/5\. Modificaciones[\s\S]*?Subtotal:[\s\S]*?S\/[\s]*?([\d,]+\.[\d]{2})/);
                    const subtotal_modificado = parseNumber(subtotalModMatch ? subtotalModMatch[0] : null);

                    // Costo total actualizado FINAL
                    const costoTotalMatches = bodyText.match(/Costo total de inversión actualizado:[\s\S]*?S\/[\s.]*?([\d,]+\.[\d]{2})/g);
                    const costo_total_actualizado = costoTotalMatches && costoTotalMatches.length > 0 ?
                        parseNumber(costoTotalMatches[costoTotalMatches.length - 1]) : null;

                    // Costos adicionales
                    const ccMatch = bodyText.match(/Costo de control concurrente[\s\S]*?S\/[\s]*?([\d,]+\.[\d]{2})/);
                    const costo_control_concurrente = parseNumber(ccMatch ? ccMatch[0] : null);

                    const controversiasMatch = bodyText.match(/Costo de controversias[\s\S]*?S\/[\s.]*?([\d,]+\.[\d]{2})/);
                    const costo_controversias = parseNumber(controversiasMatch ? controversiasMatch[0] : null);

                    const cartaFianzaMatch = bodyText.match(/Monto de carta fianza[\s\S]*?S\/[\s.]*?([\d,]+\.[\d]{2})/);
                    const monto_carta_fianza = parseNumber(cartaFianzaMatch ? cartaFianzaMatch[0] : null);

                    return {
                        // Datos básicos
                        cui: cui,
                        nombre: nombre,
                        estado: estado,
                        etapa: etapa,
                        fecha_registro: fecha_registro,

                        // A. Formulación y Evaluación
                        responsabilidad_funcional: {
                            funcion: funcion,
                            division_funcional: division_funcional,
                            grupo_funcional: grupo_funcional,
                            sector_responsable: sector_responsable
                        },

                        articulacion_pmi: {
                            servicio_publico: servicio_publico,
                            indicador_brecha: indicador_brecha,
                            espacio_geografico: espacio_geografico,
                            contribucion_brecha: contribucion_brecha
                        },

                        institucionalidad: {
                            opmi: { codigo: opmi_codigo, responsable: opmi_responsable },
                            uf: { codigo: uf_codigo, responsable: uf_responsable },
                            uei: { codigo: uei_codigo, responsable: uei_responsable },
                            uep: { codigo: uep_codigo, nombre: uep_nombre }
                        },

                        // B. Datos en Fase de Ejecución
                        expediente_tecnico: {
                            metas: metas,
                            modalidad_ejecucion: modalidad_ejecucion,

                            // Fechas detalladas por componente (original del expediente)
                            fechas_muro: fechas_muro,
                            fechas_ptar: fechas_ptar,
                            fechas_expediente: fechas_expediente,
                            fechas_supervision: fechas_supervision,
                            fechas_liquidacion: fechas_liquidacion,

                            subtotal_metas: subtotal_metas,
                            costo_expediente_tecnico: costo_expediente_tecnico,
                            costo_supervision: costo_supervision_original,
                            costo_liquidacion: costo_liquidacion,
                            costo_inversion_actualizado: costo_inversion_expediente
                        },

                        modificaciones_ejecucion: {
                            documentos: documentos_modificacion,

                            // Fechas modificadas por componente
                            fechas_muro_modificado: fechas_muro_modificado,
                            fechas_ptar_modificado: fechas_ptar_modificado,
                            fechas_supervision_modificado: fechas_supervision_modificado,
                            fechas_liquidacion_modificado: fechas_liquidacion_modificado,

                            subtotal_modificado: subtotal_modificado,
                            costo_supervision_modificado: costo_supervision_modificado,
                            costo_liquidacion_modificado: costo_liquidacion_modificado,
                            costo_inversion_modificado: costo_inversion_modificado
                        },

                        // Costos finales
                        costos_finales: {
                            costo_total_actualizado: costo_total_actualizado,
                            costo_control_concurrente: costo_control_concurrente,
                            costo_controversias: costo_controversias,
                            monto_carta_fianza: monto_carta_fianza
                        },

                        fuente: 'MEF Invierte - Ficha Ejecución Completa'
                    };
                }
            """)

            await browser.close()

            if resultado and resultado.get('cui'):
                logger.info(f"Datos extraídos de ficha de ejecución: {resultado['nombre'][:100] if resultado.get('nombre') else 'N/A'}")
                return {
                    "success": True,
                    "data": resultado,
                    "fuente": "MEF Invierte - Ficha Ejecución Completa"
                }
            else:
                logger.warning(f"No se pudo extraer información de la ficha para CUI: {cui}")
                return {
                    "success": False,
                    "error": "No se pudo extraer información de la ficha de ejecución",
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
    timeout: int = 300000
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
            # Configuración simple (igual a Node que funciona)
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox'
                ]
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
