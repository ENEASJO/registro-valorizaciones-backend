"""
Manejador de respuestas HTTP
"""
from typing import Any, Dict, Optional
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse

from app.models.ruc import ErrorResponse
from app.utils.exceptions import (
    BaseAppException,
    ValidationError,
    SUNATServiceError,
    RUCNotFoundError,
    BrowserError,
    TimeoutError
)


class ResponseHandler:
    """Manejador centralizado de respuestas"""
    
    @staticmethod
    def success(data: Any, message: str = "Operación exitosa") -> Dict[str, Any]:
        """
        Crear respuesta exitosa
        
        Args:
            data: Datos de la respuesta
            message: Mensaje de éxito
            
        Returns:
            Dict: Respuesta estructurada
        """
        return {
            "success": True,
            "message": message,
            "data": data
        }
    
    @staticmethod
    def error(
        message: str,
        details: Optional[str] = None,
        status_code: int = status.HTTP_400_BAD_REQUEST
    ) -> JSONResponse:
        """
        Crear respuesta de error
        
        Args:
            message: Mensaje de error
            details: Detalles adicionales del error
            status_code: Código de estado HTTP
            
        Returns:
            JSONResponse: Respuesta de error
        """
        error_response = ErrorResponse(
            error=True,
            message=message,
            details=details
        )
        
        return JSONResponse(
            status_code=status_code,
            content=error_response.dict()
        )
    
    @staticmethod
    def handle_exception(exc: Exception) -> JSONResponse:
        """
        Manejar excepciones y convertirlas en respuestas HTTP
        
        Args:
            exc: Excepción a manejar
            
        Returns:
            JSONResponse: Respuesta de error apropiada
        """
        if isinstance(exc, ValidationError):
            return ResponseHandler.error(
                message="Error de validación",
                details=str(exc),
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
            )
        
        elif isinstance(exc, RUCNotFoundError):
            return ResponseHandler.error(
                message="RUC no encontrado",
                details=str(exc),
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        elif isinstance(exc, TimeoutError):
            return ResponseHandler.error(
                message="Timeout en la consulta",
                details="La consulta tardó demasiado tiempo en completarse",
                status_code=status.HTTP_408_REQUEST_TIMEOUT
            )
        
        elif isinstance(exc, BrowserError):
            return ResponseHandler.error(
                message="Error en el navegador",
                details=str(exc),
                status_code=status.HTTP_502_BAD_GATEWAY
            )
        
        elif isinstance(exc, SUNATServiceError):
            return ResponseHandler.error(
                message="Error del servicio SUNAT",
                details=str(exc),
                status_code=status.HTTP_502_BAD_GATEWAY
            )
        
        elif isinstance(exc, BaseAppException):
            return ResponseHandler.error(
                message=exc.message,
                details=exc.details,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        else:
            # Error genérico
            return ResponseHandler.error(
                message="Error interno del servidor",
                details="Ha ocurrido un error inesperado",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# Instancia singleton
response_handler = ResponseHandler()

# Aliases para compatibilidad
success_response = response_handler.success
error_response = response_handler.error