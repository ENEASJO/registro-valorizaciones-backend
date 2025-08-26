"""
Excepciones personalizadas para la aplicación
"""


class BaseAppException(Exception):
    """Excepción base de la aplicación"""
    def __init__(self, message: str, details: str = None):
        self.message = message
        self.details = details
        super().__init__(self.message)


class ValidationError(BaseAppException):
    """Error de validación de datos"""
    pass


class SUNATServiceError(BaseAppException):
    """Error del servicio SUNAT"""
    pass


class RUCNotFoundError(SUNATServiceError):
    """RUC no encontrado en SUNAT"""
    pass


class BrowserError(SUNATServiceError):
    """Error relacionado con el navegador/scraping"""
    pass


class TimeoutError(SUNATServiceError):
    """Error de timeout en operación"""
    pass


class ValidationException(BaseAppException):
    """Excepción de validación de entrada"""
    pass


class ExtractionException(BaseAppException):
    """Excepción de extracción de datos"""
    pass


class OSCEServiceError(BaseAppException):
    """Error del servicio OSCE"""
    pass


class WhatsAppError(BaseAppException):
    """Error relacionado con WhatsApp Business API"""
    pass


class NotificationError(BaseAppException):
    """Error en el sistema de notificaciones"""
    pass


class SchedulerError(BaseAppException):
    """Error en el servicio de programación de tareas"""
    pass