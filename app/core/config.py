"""
Configuración de la aplicación por ambiente
"""
import os
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuración de la aplicación"""
    
    # Información de la aplicación
    APP_NAME: str = Field(default="Consultor RUC SUNAT", env="APP_NAME")
    APP_VERSION: str = Field(default="1.0.0", env="APP_VERSION")
    APP_DESCRIPTION: str = Field(
        default="API para consultar información de empresas en SUNAT",
        env="APP_DESCRIPTION"
    )
    
    # Configuración del servidor
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8000, env="PORT")
    DEBUG: bool = Field(default=False, env="DEBUG")
    RELOAD: bool = Field(default=False, env="RELOAD")
    
    # Configuración de CORS
    ALLOWED_ORIGINS: List[str] = Field(
        default=["*"], 
        env="ALLOWED_ORIGINS",
        description="Lista de orígenes permitidos para CORS"
    )
    ALLOW_CREDENTIALS: bool = Field(default=True, env="ALLOW_CREDENTIALS")
    ALLOWED_METHODS: List[str] = Field(default=["*"], env="ALLOWED_METHODS")
    ALLOWED_HEADERS: List[str] = Field(default=["*"], env="ALLOWED_HEADERS")
    
    # Configuración de scraping
    HEADLESS_BROWSER: bool = Field(
        default=True, 
        env="HEADLESS_BROWSER",
        description="Ejecutar navegador en modo headless"
    )
    BROWSER_TIMEOUT: int = Field(
        default=30000,
        env="BROWSER_TIMEOUT",
        description="Timeout del navegador en milisegundos"
    )
    
    # Configuración de logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        env="LOG_FORMAT"
    )
    
    # Configuración de seguridad
    SECRET_KEY: str = Field(
        default="change-this-secret-key-in-production",
        env="SECRET_KEY",
        description="Clave secreta para la aplicación"
    )
    
    # Rate limiting
    RATE_LIMIT_REQUESTS: int = Field(
        default=100,
        env="RATE_LIMIT_REQUESTS",
        description="Número máximo de requests por minuto"
    )
    
    # Configuración de base de datos (para futuro uso)
    DATABASE_URL: str = Field(
        default="sqlite:///./app.db",
        env="DATABASE_URL",
        description="URL de la base de datos"
    )
    
    # Configuración de WhatsApp Business API
    WHATSAPP_API_URL: str = Field(
        default="https://graph.facebook.com/v18.0",
        env="WHATSAPP_API_URL",
        description="URL base de la API de WhatsApp Business"
    )
    WHATSAPP_ACCESS_TOKEN: str = Field(
        default="",
        env="WHATSAPP_ACCESS_TOKEN",
        description="Token de acceso para WhatsApp Business API"
    )
    WHATSAPP_PHONE_NUMBER_ID: str = Field(
        default="",
        env="WHATSAPP_PHONE_NUMBER_ID", 
        description="ID del número de teléfono de WhatsApp Business"
    )
    WHATSAPP_VERIFY_TOKEN: str = Field(
        default="whatsapp_verify_token_2025",
        env="WHATSAPP_VERIFY_TOKEN",
        description="Token de verificación para webhooks de WhatsApp"
    )
    WHATSAPP_WEBHOOK_ENDPOINT: str = Field(
        default="/api/webhooks/whatsapp",
        env="WHATSAPP_WEBHOOK_ENDPOINT",
        description="Endpoint para recibir webhooks de WhatsApp"
    )
    
    # Configuración de rate limiting para WhatsApp
    WHATSAPP_RATE_LIMIT_PER_MINUTE: int = Field(
        default=100,
        env="WHATSAPP_RATE_LIMIT_PER_MINUTE",
        description="Límite de mensajes por minuto para WhatsApp"
    )
    WHATSAPP_RETRY_ATTEMPTS: int = Field(
        default=3,
        env="WHATSAPP_RETRY_ATTEMPTS",
        description="Número máximo de reintentos para envío de mensajes"
    )
    WHATSAPP_RETRY_DELAY_SECONDS: int = Field(
        default=30,
        env="WHATSAPP_RETRY_DELAY_SECONDS", 
        description="Delay inicial para reintentos (backoff exponencial)"
    )
    
    # Configuración de horarios de trabajo
    WHATSAPP_WORK_HOURS_START: str = Field(
        default="08:00",
        env="WHATSAPP_WORK_HOURS_START",
        description="Hora de inicio para envío de mensajes (HH:MM)"
    )
    WHATSAPP_WORK_HOURS_END: str = Field(
        default="18:00", 
        env="WHATSAPP_WORK_HOURS_END",
        description="Hora de fin para envío de mensajes (HH:MM)"
    )
    WHATSAPP_TIMEZONE: str = Field(
        default="America/Lima",
        env="WHATSAPP_TIMEZONE",
        description="Zona horaria para horarios de trabajo"
    )
    
    # Configuración de Redis para tareas en background
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        env="REDIS_URL",
        description="URL de conexión a Redis"
    )
    
    # Configuración de tareas en background
    BACKGROUND_TASKS_ENABLED: bool = Field(
        default=True,
        env="BACKGROUND_TASKS_ENABLED",
        description="Habilitar procesamiento de tareas en background"
    )
    BACKGROUND_TASKS_INTERVAL_SECONDS: int = Field(
        default=30,
        env="BACKGROUND_TASKS_INTERVAL_SECONDS",
        description="Intervalo para procesar tareas pendientes"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields from .env file

    def get_cors_settings(self) -> dict:
        """Obtener configuración de CORS"""
        return {
            "allow_origins": self.ALLOWED_ORIGINS,
            "allow_credentials": self.ALLOW_CREDENTIALS,
            "allow_methods": self.ALLOWED_METHODS,
            "allow_headers": self.ALLOWED_HEADERS,
        }

    def is_production(self) -> bool:
        """Verificar si está en modo producción"""
        return not self.DEBUG and not self.RELOAD

    def get_app_info(self) -> dict:
        """Obtener información de la aplicación"""
        return {
            "title": self.APP_NAME,
            "version": self.APP_VERSION,
            "description": self.APP_DESCRIPTION,
        }


# Instancia global de configuración
settings = Settings()


def get_settings() -> Settings:
    """Factory para obtener la configuración"""
    return settings