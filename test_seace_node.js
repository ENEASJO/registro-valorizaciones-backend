/**
 * Script de prueba para verificar si el campo CUI funciona en SEACE con Node.js + Playwright
 *
 * Instalación:
 * npm install playwright
 * npx playwright install chromium
 *
 * Ejecución:
 * node test_seace_node.js
 */

const { chromium } = require('playwright');

async function testSEACE() {
    console.log('🚀 Iniciando prueba SEACE con Node.js + Playwright...\n');

    const browser = await chromium.launch({
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });

    try {
        const page = await browser.newPage();
        page.setDefaultTimeout(30000);

        // Navegar a SEACE
        console.log('📍 Navegando a SEACE...');
        await page.goto('https://prod2.seace.gob.pe/seacebus-uiwd-pub/buscadorPublico/buscadorPublico.xhtml', {
            waitUntil: 'networkidle',
            timeout: 60000
        });

        // Esperar a que el tab activo cargue
        await page.waitForSelector('.ui-tabs-selected.ui-state-active', { timeout: 30000, state: 'visible' });
        console.log('✅ Tab de búsqueda activo');

        // Esperar inicialización del formulario
        await page.waitForTimeout(8000);
        console.log('✅ Formulario inicializado (8 segundos)');

        // Verificar que el campo CUI exista
        const cuiInputId = 'tbBuscador\\:idFormBuscarProceso\\:CUI';
        await page.waitForFunction(
            (selector) => document.querySelector(selector) !== null,
            `#${cuiInputId}`,
            { timeout: 30000 }
        );
        console.log('✅ Campo CUI encontrado\n');

        // === PRUEBA 1: Buscar por año + CUI en campo "Código Único de Inversión" ===
        console.log('🔍 PRUEBA 1: Año 2024 + CUI 2595080 en campo "Código Único de Inversión"');

        // Seleccionar año 2024
        const yearDropdownId = 'tbBuscador\\:idFormBuscarProceso\\:anioConvocatoria';
        await page.evaluate((selector) => {
            document.querySelector(selector).click();
        }, `#${yearDropdownId}`);

        await page.waitForTimeout(500);

        await page.evaluate((selector) => {
            const panel = document.querySelector(`${selector}_panel`);
            if (panel) {
                const option = Array.from(panel.querySelectorAll('li')).find(li => li.textContent.trim() === '2024');
                if (option) {
                    option.click();
                }
            }
        }, `#${yearDropdownId}`);

        console.log('  ✓ Año 2024 seleccionado');

        // Ingresar CUI
        await page.evaluate(() => {
            const cuiInput = document.querySelector('#tbBuscador\\:idFormBuscarProceso\\:CUI');
            if (cuiInput) {
                cuiInput.value = '2595080';
                cuiInput.dispatchEvent(new Event('input', { bubbles: true }));
                cuiInput.dispatchEvent(new Event('change', { bubbles: true }));
            }
        });

        console.log('  ✓ CUI 2595080 ingresado');

        // Hacer clic en Buscar
        await page.waitForTimeout(2000);
        const buttonClicked = await page.evaluate(() => {
            const buscarButton = Array.from(document.querySelectorAll('button')).find(btn => btn.textContent.includes('Buscar'));
            if (buscarButton) {
                buscarButton.click();
                return true;
            }
            return false;
        });

        if (!buttonClicked) {
            throw new Error('No se pudo hacer clic en el botón Buscar');
        }

        console.log('  ✓ Clic en botón Buscar');

        // Esperar resultados
        await page.waitForTimeout(5000);

        // Verificar resultados
        const paginatorText = await page.evaluate(() => {
            const paginator = document.querySelector('#tbBuscador\\:idFormBuscarProceso\\:pnlGrdResultadosProcesos .ui-paginator-current');
            return paginator ? paginator.textContent : 'No encontrado';
        });

        console.log(`  📊 Paginador: ${paginatorText}`);

        if (paginatorText.includes('total 0') || paginatorText.includes('0 a 0')) {
            console.log('  ❌ RESULTADO: 0 resultados - Campo CUI NO funciona\n');
        } else {
            console.log('  ✅ RESULTADO: Se encontraron resultados - Campo CUI SÍ funciona\n');
        }

        // === PRUEBA 2: Buscar solo por año ===
        console.log('🔍 PRUEBA 2: Solo año 2024 (sin CUI)');

        // Limpiar formulario
        await page.evaluate(() => {
            const limpiarButton = Array.from(document.querySelectorAll('button')).find(btn => btn.textContent.includes('Limpiar'));
            if (limpiarButton) {
                limpiarButton.click();
            }
        });

        await page.waitForTimeout(2000);

        // Seleccionar año 2024 nuevamente
        await page.evaluate((selector) => {
            document.querySelector(selector).click();
        }, `#${yearDropdownId}`);

        await page.waitForTimeout(500);

        await page.evaluate((selector) => {
            const panel = document.querySelector(`${selector}_panel`);
            if (panel) {
                const option = Array.from(panel.querySelectorAll('li')).find(li => li.textContent.trim() === '2024');
                if (option) {
                    option.click();
                }
            }
        }, `#${yearDropdownId}`);

        console.log('  ✓ Año 2024 seleccionado');

        // Hacer clic en Buscar (sin CUI)
        await page.waitForTimeout(2000);
        await page.evaluate(() => {
            const buscarButton = Array.from(document.querySelectorAll('button')).find(btn => btn.textContent.includes('Buscar'));
            if (buscarButton) {
                buscarButton.click();
            }
        });

        console.log('  ✓ Clic en botón Buscar (sin CUI)');

        // Esperar resultados
        await page.waitForTimeout(5000);

        // Verificar resultados
        const paginatorText2 = await page.evaluate(() => {
            const paginator = document.querySelector('#tbBuscador\\:idFormBuscarProceso\\:pnlGrdResultadosProcesos .ui-paginator-current');
            return paginator ? paginator.textContent : 'No encontrado';
        });

        console.log(`  📊 Paginador: ${paginatorText2}`);

        if (paginatorText2.includes('total 0') || paginatorText2.includes('0 a 0')) {
            console.log('  ❌ RESULTADO: 0 resultados\n');
        } else {
            console.log('  ✅ RESULTADO: Se encontraron resultados');

            // Buscar CUI en los resultados
            const cuiEncontrado = await page.evaluate(() => {
                const rows = document.querySelectorAll('#tbBuscador\\:idFormBuscarProceso\\:pnlGrdResultadosProcesos table tbody tr');
                for (let row of rows) {
                    const descripcionCell = row.querySelector('td:nth-child(8)');
                    if (descripcionCell && descripcionCell.textContent.includes('CUI 2595080')) {
                        return true;
                    }
                }
                return false;
            });

            if (cuiEncontrado) {
                console.log('  ✅ CUI 2595080 encontrado en los resultados\n');
            } else {
                console.log('  ⚠️  CUI 2595080 NO encontrado en los resultados\n');
            }
        }

        console.log('✅ Prueba completada');

    } catch (error) {
        console.error('❌ Error:', error.message);
    } finally {
        await browser.close();
    }
}

testSEACE();
