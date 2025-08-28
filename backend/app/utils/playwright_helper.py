"""
Cloud Run optimized Playwright helper with improved Chrome detection
"""
import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def get_browser_launch_options(headless: bool = True, custom_args: list = None) -> Dict[str, Any]:
    """
    Get browser launch options optimized for Cloud Run
    
    Args:
        headless: Whether to run browser in headless mode
        custom_args: Additional browser arguments to include
        
    Returns:
        Dict with launch options for Playwright
    """
    logger.info("🚀 Configurando Playwright browsers para Cloud Run")

    # Argumentos base para optimización en Cloud Run
    base_args = [
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
        '--disable-renderer-backgrounding',
        '--disable-blink-features=AutomationControlled',
        '--disable-ipc-flooding-protection',
        '--disable-component-extensions-with-background-pages',
        '--disable-default-apps'
    ]
    
    # Agregar argumentos personalizados si se proporcionan
    if custom_args:
        base_args.extend(custom_args)
    
    launch_options = {
        'headless': headless,
        'args': base_args
    }
    
    # Buscar Chrome executable en múltiples ubicaciones posibles
    chrome_path = find_chrome_executable()
    if chrome_path:
        launch_options['executable_path'] = chrome_path
        logger.info(f"✅ Chrome encontrado en: {chrome_path}")
    else:
        logger.warning("⚠️ No se encontró Chrome executable específico, usando configuración por defecto de Playwright")
    
    logger.info(f"✅ Launch options configuradas para Cloud Run")
        
    return launch_options


def find_chrome_executable() -> str:
    """
    Find Chrome executable in different possible locations
    
    Returns:
        Path to Chrome executable or empty string if not found
    """
    import glob
    
    # Posibles ubicaciones de Chrome en orden de preferencia
    possible_chrome_paths = [
        # Ubicaciones específicas para Cloud Run con el nuevo Dockerfile
        '/app/.cache/ms-playwright/chromium-*/chrome-linux/chrome',
        '/app/.cache/ms-playwright/chromium-*/chrome-linux64/chrome',
        
        # Ubicaciones estándar de Playwright
        '/root/.cache/ms-playwright/chromium-*/chrome-linux/chrome',
        '/root/.cache/ms-playwright/chromium-*/chrome-linux64/chrome',
        '/home/app/.cache/ms-playwright/chromium-*/chrome-linux/chrome',
        '/home/app/.cache/ms-playwright/chromium-*/chrome-linux64/chrome',
        
        # Ubicaciones del sistema
        '/usr/bin/chromium-browser',
        '/usr/bin/chromium',
        '/usr/bin/google-chrome-stable',
        '/usr/bin/google-chrome',
        '/opt/google/chrome/chrome',
        '/opt/chrome/chrome',
        '/opt/chromium.org/chromium/chromium'
    ]
    
    logger.info("🔍 Buscando Chrome executable...")
    
    # Buscar usando patrones glob primero (para versiones específicas de Playwright)
    for path_pattern in possible_chrome_paths:
        if '*' in path_pattern:
            matches = glob.glob(path_pattern)
            if matches:
                # Ordenar para obtener la versión más reciente
                matches.sort(reverse=True)
                chrome_path = matches[0]
                if os.path.exists(chrome_path) and os.access(chrome_path, os.X_OK):
                    logger.info(f"✅ Chrome encontrado (glob): {chrome_path}")
                    return chrome_path
        else:
            # Buscar paths exactos
            if os.path.exists(path_pattern) and os.access(path_pattern, os.X_OK):
                logger.info(f"✅ Chrome encontrado (path directo): {path_pattern}")
                return path_pattern
    
    # Intentar encontrar usando comando 'which'
    try:
        import subprocess
        chrome_commands = ['chromium-browser', 'chromium', 'google-chrome-stable', 'google-chrome']
        for cmd in chrome_commands:
            try:
                result = subprocess.run(['which', cmd], capture_output=True, text=True, timeout=5)
                if result.returncode == 0 and result.stdout.strip():
                    chrome_path = result.stdout.strip()
                    logger.info(f"✅ Chrome encontrado (which): {chrome_path}")
                    return chrome_path
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
                continue
    except Exception as e:
        logger.debug(f"No se pudo ejecutar 'which': {e}")
    
    logger.warning("⚠️ No se encontró Chrome executable en ubicaciones conocidas")
    return ""


def is_cloud_run_environment() -> bool:
    """
    Detect if running in Cloud Run environment
    
    Returns:
        True if running in Cloud Run, False otherwise
    """
    # Detectar Cloud Run por variables de entorno
    cloud_run_indicators = [
        'K_SERVICE',  # Variable específica de Cloud Run
        'K_CONFIGURATION',
        'K_REVISION',
        'PORT'  # Puerto común en Cloud Run
    ]
    
    for indicator in cloud_run_indicators:
        if os.environ.get(indicator):
            return True
            
    # También revisar si existe algún path típico de Cloud Run
    return os.path.exists('/opt/chrome-linux64/chrome') or os.path.exists('/app/.cache/ms-playwright')