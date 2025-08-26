"""
Configuración de logging para la aplicación
"""
import logging
import logging.config
from typing import Dict, Any

from app.core.config import settings


def setup_logging() -> None:
    """Configurar el sistema de logging"""
    
    logging_config: Dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": settings.LOG_FORMAT,
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "detailed": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s:%(lineno)d - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": settings.LOG_LEVEL,
                "formatter": "default",
                "stream": "ext://sys.stdout",
            },
            "file": {
                "class": "logging.FileHandler",
                "level": "DEBUG",
                "formatter": "detailed",
                "filename": "app.log",
                "mode": "a",
            },
        },
        "loggers": {
            "app": {
                "level": settings.LOG_LEVEL,
                "handlers": ["console", "file"] if settings.DEBUG else ["console"],
                "propagate": False,
            },
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False,
            },
            "fastapi": {
                "level": "INFO", 
                "handlers": ["console"],
                "propagate": False,
            },
        },
        "root": {
            "level": settings.LOG_LEVEL,
            "handlers": ["console"],
        },
    }
    
    logging.config.dictConfig(logging_config)


def get_logger(name: str = __name__) -> logging.Logger:
    """Obtener logger configurado"""
    return logging.getLogger(name)