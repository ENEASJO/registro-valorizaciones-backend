"""
Helper utilities for Playwright configuration across services
"""
import os
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


def get_browser_launch_options(headless: bool = True, custom_args: list = None) -> Dict[str, Any]:
    """
    Get browser launch options with Chrome for Testing path detection
    
    Args:
        headless: Whether to run browser in headless mode
        custom_args: Additional browser arguments to include
        
    Returns:
        Dict with launch options for Playwright
    """
    # Configurar ruta de Chrome for Testing en Cloud Run
    chrome_path = None
    if os.path.exists('/opt/chrome-linux64/chrome'):
        chrome_path = '/opt/chrome-linux64/chrome'
        logger.info(f"🐳 Usando Chrome for Testing en Cloud Run: {chrome_path}")
        # FORZAR variable de entorno para Playwright
        os.environ['PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH'] = chrome_path
        logger.info(f"🔧 FORZADO: PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH={chrome_path}")
    else:
        logger.info("🖥️ Usando Chromium local en desarrollo")

    # Argumentos base para optimización
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
        '--disable-blink-features=AutomationControlled'
    ]
    
    # Agregar argumentos personalizados si se proporcionan
    if custom_args:
        base_args.extend(custom_args)
    
    launch_options = {
        'headless': headless,
        'args': base_args
    }
    
    # Agregar executable_path Y forzar variable de entorno
    if chrome_path:
        launch_options['executable_path'] = chrome_path
        logger.info(f"✅ Launch options configuradas con executable_path: {chrome_path}")
        
    return launch_options


def is_cloud_run_environment() -> bool:
    """
    Detect if running in Cloud Run environment
    
    Returns:
        True if running in Cloud Run, False otherwise
    """
    return os.path.exists('/opt/chrome-linux64/chrome')