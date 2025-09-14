"""
Configuración de logging estructurado y monitoring para la API de notificaciones WhatsApp
Sistema de logs optimizado para producción con métricas y observabilidad
"""

import os
import sys
import json
import time
import traceback
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path

import logging
import logging.config
from pythonjsonlogger import jsonlogger
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter

# =====================================================================
# CONFIGURACIÓN DE LOGGING
# =====================================================================

class NotificationLoggerConfig:
    """Configuración centralizada de logging"""
    
    def __init__(self):
        self.app_name = "notifications-api"
        self.version = "2.0.0"
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.log_format = os.getenv("LOG_FORMAT", "json")  # json | text
        self.log_dir = Path(os.getenv("LOG_DIR", "./logs"))
        
        # Crear directorio de logs si no existe
        self.log_dir.mkdir(exist_ok=True)
        
        # Configuración de archivos de log
        self.log_files = {
            "main": self.log_dir / "notifications-api.log",
            "security": self.log_dir / "security.log", 
            "performance": self.log_dir / "performance.log",
            "webhooks": self.log_dir / "webhooks.log",
            "errors": self.log_dir / "errors.log"
        }
        
        # Configuración de rotación
        self.max_bytes = int(os.getenv("LOG_MAX_BYTES", "50000000"))  # 50MB
        self.backup_count = int(os.getenv("LOG_BACKUP_COUNT", "10"))

class StructuredFormatter(jsonlogger.JsonFormatter):
    """Formatter personalizado para logs estructurados"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hostname = os.uname().nodename
        self.process_id = os.getpid()
    
    def add_fields(self, log_record: Dict, record: logging.LogRecord, message_dict: Dict):
        super().add_fields(log_record, record, message_dict)
        
        # Agregar campos estándar
        log_record["timestamp"] = datetime.utcfromtimestamp(record.created).isoformat() + "Z"
        log_record["level"] = record.levelname
        log_record["logger"] = record.name
        log_record["module"] = record.module
        log_record["function"] = record.funcName
        log_record["line"] = record.lineno
        log_record["hostname"] = self.hostname
        log_record["process_id"] = self.process_id
        log_record["thread_id"] = record.thread
        
        # Agregar información de la aplicación
        log_record["application"] = "notifications-api"
        log_record["version"] = "2.0.0"
        log_record["environment"] = os.getenv("ENVIRONMENT", "development")
        
        # Agregar trace ID si está disponible
        span = trace.get_current_span()
        if span and span.is_recording():
            log_record["trace_id"] = format(span.get_span_context().trace_id, "032x")
            log_record["span_id"] = format(span.get_span_context().span_id, "016x")

class PerformanceLogger:
    """Logger especializado para métricas de performance"""
    
    def __init__(self):
        self.logger = logging.getLogger("performance")
        self.metrics_buffer = []
        self.buffer_size = 100
    
    def log_api_call(
        self,
        method: str,
        endpoint: str,
        status_code: int,
        duration_ms: float,
        user_id: str = None,
        request_id: str = None,
        error: str = None
    ):
        """Log de llamada API con métricas"""
        
        metric_data = {
            "metric_type": "api_call",
            "method": method,
            "endpoint": endpoint,
            "status_code": status_code,
            "duration_ms": round(duration_ms, 2),
            "success": status_code < 400,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        if user_id:
            metric_data["user_id"] = user_id
        if request_id:
            metric_data["request_id"] = request_id
        if error:
            metric_data["error"] = error
        
        self.logger.info("API call completed", extra=metric_data)
        
        # Agregar al buffer para agregaciones
        self.metrics_buffer.append(metric_data)
        if len(self.metrics_buffer) >= self.buffer_size:
            self._flush_metrics_buffer()
    
    def log_notification_event(
        self,
        event_type: str,
        notification_id: int,
        valorizacion_id: int,
        estado_anterior: str,
        estado_nuevo: str,
        duration_ms: float = None,
        error: str = None
    ):
        """Log de evento de notificación"""
        
        event_data = {
            "metric_type": "notification_event",
            "event_type": event_type,
            "notification_id": notification_id,
            "valorizacion_id": valorizacion_id,
            "estado_anterior": estado_anterior,
            "estado_nuevo": estado_nuevo,
            "success": error is None,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        if duration_ms:
            event_data["duration_ms"] = round(duration_ms, 2)
        if error:
            event_data["error"] = error
        
        self.logger.info(f"Notification {event_type}", extra=event_data)
    
    def log_whatsapp_api_call(
        self,
        operation: str,
        phone_number: str,
        message_id: str = None,
        duration_ms: float = None,
        status_code: int = None,
        error: str = None
    ):
        """Log de llamada a WhatsApp API"""
        
        api_data = {
            "metric_type": "whatsapp_api_call",
            "operation": operation,
            "phone_number_hash": hash(phone_number) if phone_number else None,
            "success": error is None,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        if message_id:
            api_data["whatsapp_message_id"] = message_id
        if duration_ms:
            api_data["duration_ms"] = round(duration_ms, 2)
        if status_code:
            api_data["whatsapp_status_code"] = status_code
        if error:
            api_data["error"] = error
        
        self.logger.info(f"WhatsApp API {operation}", extra=api_data)
    
    def _flush_metrics_buffer(self):
        """Procesar buffer de métricas para agregaciones"""
        try:
            # Aquí se podrían enviar métricas agregadas a sistemas como Prometheus
            self.metrics_buffer.clear()
        except Exception as e:
            self.logger.error(f"Error flushing metrics buffer: {str(e)}")

class SecurityLogger:
    """Logger especializado para eventos de seguridad"""
    
    def __init__(self):
        self.logger = logging.getLogger("security")
    
    def log_authentication_event(
        self,
        event_type: str,  # login, logout, token_refresh, invalid_token
        user_id: str = None,
        ip_address: str = None,
        user_agent: str = None,
        success: bool = True,
        error: str = None
    ):
        """Log de evento de autenticación"""
        
        auth_data = {
            "security_event_type": "authentication",
            "event_type": event_type,
            "success": success,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        if user_id:
            auth_data["user_id"] = user_id
        if ip_address:
            auth_data["ip_address"] = ip_address
        if user_agent:
            auth_data["user_agent"] = user_agent[:200]  # Limitar longitud
        if error:
            auth_data["error"] = error
        
        level = logging.WARNING if not success else logging.INFO
        self.logger.log(level, f"Authentication {event_type}", extra=auth_data)
    
    def log_rate_limit_event(
        self,
        client_id: str,
        endpoint: str,
        limit: int,
        current_count: int,
        ip_address: str = None
    ):
        """Log de rate limiting"""
        
        rate_limit_data = {
            "security_event_type": "rate_limit",
            "client_id": client_id,
            "endpoint": endpoint,
            "limit": limit,
            "current_count": current_count,
            "exceeded": current_count > limit,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        if ip_address:
            rate_limit_data["ip_address"] = ip_address
        
        self.logger.warning("Rate limit check", extra=rate_limit_data)
    
    def log_suspicious_activity(
        self,
        activity_type: str,
        details: Dict[str, Any],
        severity: str = "medium",  # low, medium, high, critical
        ip_address: str = None,
        user_id: str = None
    ):
        """Log de actividad sospechosa"""
        
        suspicious_data = {
            "security_event_type": "suspicious_activity",
            "activity_type": activity_type,
            "severity": severity,
            "details": details,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        if ip_address:
            suspicious_data["ip_address"] = ip_address
        if user_id:
            suspicious_data["user_id"] = user_id
        
        # Determinar nivel de log por severidad
        level_mapping = {
            "low": logging.INFO,
            "medium": logging.WARNING, 
            "high": logging.ERROR,
            "critical": logging.CRITICAL
        }
        
        level = level_mapping.get(severity, logging.WARNING)
        self.logger.log(level, f"Suspicious activity: {activity_type}", extra=suspicious_data)

class WebhookLogger:
    """Logger especializado para webhooks"""
    
    def __init__(self):
        self.logger = logging.getLogger("webhooks")
    
    def log_webhook_received(
        self,
        source: str,
        payload_size: int,
        ip_address: str = None,
        user_agent: str = None,
        signature_valid: bool = None
    ):
        """Log de webhook recibido"""
        
        webhook_data = {
            "webhook_event_type": "received",
            "source": source,
            "payload_size_bytes": payload_size,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        if ip_address:
            webhook_data["ip_address"] = ip_address
        if user_agent:
            webhook_data["user_agent"] = user_agent[:200]
        if signature_valid is not None:
            webhook_data["signature_valid"] = signature_valid
        
        self.logger.info("Webhook received", extra=webhook_data)
    
    def log_webhook_processed(
        self,
        source: str,
        events_processed: int,
        updates_made: int,
        errors: int,
        processing_time_ms: float,
        request_id: str = None
    ):
        """Log de webhook procesado"""
        
        processed_data = {
            "webhook_event_type": "processed",
            "source": source,
            "events_processed": events_processed,
            "updates_made": updates_made,
            "errors": errors,
            "processing_time_ms": round(processing_time_ms, 2),
            "success": errors == 0,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        if request_id:
            processed_data["request_id"] = request_id
        
        level = logging.INFO if errors == 0 else logging.WARNING
        self.logger.log(level, "Webhook processed", extra=processed_data)

# =====================================================================
# CONFIGURACIÓN PRINCIPAL DE LOGGING
# =====================================================================

def setup_logging():
    """Configurar sistema de logging estructurado"""
    
    config = NotificationLoggerConfig()
    
    # Configuración de logging
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": StructuredFormatter,
                "format": "%(timestamp)s %(level)s %(name)s %(message)s"
            },
            "text": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": config.log_level,
                "formatter": config.log_format,
                "stream": sys.stdout
            },
            "main_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "json",
                "filename": str(config.log_files["main"]),
                "maxBytes": config.max_bytes,
                "backupCount": config.backup_count,
                "encoding": "utf-8"
            },
            "security_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "json",
                "filename": str(config.log_files["security"]),
                "maxBytes": config.max_bytes,
                "backupCount": config.backup_count,
                "encoding": "utf-8"
            },
            "performance_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "json",
                "filename": str(config.log_files["performance"]),
                "maxBytes": config.max_bytes,
                "backupCount": config.backup_count,
                "encoding": "utf-8"
            },
            "webhooks_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "json",
                "filename": str(config.log_files["webhooks"]),
                "maxBytes": config.max_bytes,
                "backupCount": config.backup_count,
                "encoding": "utf-8"
            },
            "errors_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "json",
                "filename": str(config.log_files["errors"]),
                "maxBytes": config.max_bytes,
                "backupCount": config.backup_count,
                "encoding": "utf-8"
            }
        },
        "loggers": {
            "": {  # Root logger
                "level": config.log_level,
                "handlers": ["console", "main_file", "errors_file"],
                "propagate": False
            },
            "security": {
                "level": "INFO",
                "handlers": ["security_file", "console"],
                "propagate": False
            },
            "performance": {
                "level": "INFO", 
                "handlers": ["performance_file"],
                "propagate": False
            },
            "webhooks": {
                "level": "INFO",
                "handlers": ["webhooks_file", "console"],
                "propagate": False
            },
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False
            },
            "sqlalchemy": {
                "level": "WARNING",
                "handlers": ["main_file"],
                "propagate": False
            }
        }
    }
    
    logging.config.dictConfig(logging_config)
    
    # Log de inicio del sistema
    logger = logging.getLogger(__name__)
    logger.info(
        "Logging system initialized",
        extra={
            "log_level": config.log_level,
            "log_format": config.log_format,
            "log_directory": str(config.log_dir),
            "environment": config.environment
        }
    )

# =====================================================================
# TRACING Y OBSERVABILIDAD
# =====================================================================

def setup_tracing(service_name: str = "notifications-api"):
    """Configurar distributed tracing con OpenTelemetry"""
    
    # Solo configurar en producción si Jaeger está disponible
    jaeger_endpoint = os.getenv("JAEGER_ENDPOINT")
    if not jaeger_endpoint:
        return
    
    try:
        # Configurar tracer provider
        trace.set_tracer_provider(TracerProvider())
        tracer = trace.get_tracer(__name__)
        
        # Configurar Jaeger exporter
        jaeger_exporter = JaegerExporter(
            agent_host_name=os.getenv("JAEGER_HOST", "localhost"),
            agent_port=int(os.getenv("JAEGER_PORT", "14268")),
        )
        
        # Configurar span processor
        span_processor = BatchSpanProcessor(jaeger_exporter)
        trace.get_tracer_provider().add_span_processor(span_processor)
        
        logger = logging.getLogger(__name__)
        logger.info(
            "Distributed tracing initialized",
            extra={
                "service_name": service_name,
                "jaeger_endpoint": jaeger_endpoint
            }
        )
        
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to initialize tracing: {str(e)}")

# =====================================================================
# MIDDLEWARE DE LOGGING
# =====================================================================

class LoggingMiddleware:
    """Middleware para logging automático de requests"""
    
    def __init__(self, app):
        self.app = app
        self.performance_logger = PerformanceLogger()
        self.security_logger = SecurityLogger()
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        request_id = None
        start_time = time.time()
        
        # Wrapper para capturar response
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                status_code = message["status"]
                duration_ms = (time.time() - start_time) * 1000
                
                # Log de performance
                self.performance_logger.log_api_call(
                    method=scope["method"],
                    endpoint=scope["path"],
                    status_code=status_code,
                    duration_ms=duration_ms,
                    request_id=request_id
                )
                
                # Log de seguridad para requests fallidas
                if status_code >= 400:
                    self.security_logger.log_suspicious_activity(
                        activity_type="failed_request",
                        details={
                            "method": scope["method"],
                            "path": scope["path"],
                            "status_code": status_code
                        },
                        ip_address=self._get_client_ip(scope)
                    )
            
            await send(message)
        
        await self.app(scope, receive, send_wrapper)
    
    def _get_client_ip(self, scope) -> str:
        """Extraer IP del cliente"""
        for header_name, header_value in scope.get("headers", []):
            if header_name == b"x-forwarded-for":
                return header_value.decode().split(",")[0].strip()
        
        if scope.get("client"):
            return scope["client"][0]
        
        return "unknown"

# =====================================================================
# UTILIDADES DE LOGGING
# =====================================================================

def get_logger(name: str) -> logging.Logger:
    """Obtener logger configurado"""
    return logging.getLogger(name)

def log_exception(logger: logging.Logger, message: str, extra: Dict[str, Any] = None):
    """Log de excepción con contexto completo"""
    
    exc_info = sys.exc_info()
    if exc_info[0] is None:
        logger.error(message, extra=extra)
        return
    
    exception_data = {
        "exception_type": exc_info[0].__name__,
        "exception_message": str(exc_info[1]),
        "traceback": traceback.format_exception(*exc_info)
    }
    
    if extra:
        exception_data.update(extra)
    
    logger.error(message, extra=exception_data, exc_info=True)

def create_request_context(request_id: str, user_id: str = None) -> Dict[str, Any]:
    """Crear contexto común para logs de request"""
    return {
        "request_id": request_id,
        "user_id": user_id,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

# =====================================================================
# INSTANCIAS GLOBALES DE LOGGERS ESPECIALIZADOS
# =====================================================================

# Inicializar loggers especializados
performance_logger = PerformanceLogger()
security_logger = SecurityLogger()
webhook_logger = WebhookLogger()

# =====================================================================
# INICIALIZACIÓN AUTOMÁTICA
# =====================================================================

# Auto-setup cuando se importa el módulo
setup_logging()

# Setup tracing si está configurado
if os.getenv("TRACING_ENABLED", "false").lower() == "true":
    setup_tracing()