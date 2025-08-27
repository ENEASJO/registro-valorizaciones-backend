"""
Helper utilities for Playwright configuration across services
"""
import os
import logging
from typing import Dict, Any

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
    logger.info("🚀 Usando Playwright browsers oficiales")

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
        '--disable-blink-features=AutomationControlled'
    ]
    
    # Agregar argumentos personalizados si se proporcionan
    if custom_args:
        base_args.extend(custom_args)
    
    launch_options = {
        'headless': headless,
        'args': base_args
    }
    
    logger.info(f"✅ Launch options configuradas para Cloud Run")
        
    return launch_options


def is_cloud_run_environment() -> bool:
    """
    Detect if running in Cloud Run environment
    
    Returns:
        True if running in Cloud Run, False otherwise
    """
    return os.path.exists('/opt/chrome-linux64/chrome')