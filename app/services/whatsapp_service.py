"""
Servicio para integración con WhatsApp Business API
Maneja el envío de mensajes, webhooks y reintentos
"""

import asyncio
import json
import logging
import re
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
import aiohttp
import phonenumbers
from phonenumbers import NumberParseException, PhoneNumberFormat
import pytz
from jinja2 import Template

from app.core.config import settings
from app.utils.exceptions import WhatsAppError, ValidationError

logger = logging.getLogger(__name__)

class WhatsAppService:
    """Servicio para integración con WhatsApp Business API"""
    
    def __init__(self):
        self.api_url = settings.WHATSAPP_API_URL
        self.access_token = settings.WHATSAPP_ACCESS_TOKEN
        self.phone_number_id = settings.WHATSAPP_PHONE_NUMBER_ID
        self.rate_limit = settings.WHATSAPP_RATE_LIMIT_PER_MINUTE
        self.retry_attempts = settings.WHATSAPP_RETRY_ATTEMPTS
        self.retry_delay = settings.WHATSAPP_RETRY_DELAY_SECONDS
        
        # Rate limiting
        self._message_timestamps: List[datetime] = []
        
        # Validar configuración inicial
        if not self.access_token:
            logger.warning("WhatsApp Access Token no configurado")
        if not self.phone_number_id:
            logger.warning("WhatsApp Phone Number ID no configurado")
    
    def _clean_rate_limit_window(self) -> None:
        """Limpia ventana de rate limiting (últimos 60 segundos)"""
        cutoff = datetime.now() - timedelta(minutes=1)
        self._message_timestamps = [
            ts for ts in self._message_timestamps if ts > cutoff
        ]
    
    def _can_send_message(self) -> bool:
        """Verifica si se puede enviar un mensaje según rate limit"""
        self._clean_rate_limit_window()
        return len(self._message_timestamps) < self.rate_limit
    
    def _add_message_timestamp(self) -> None:
        """Registra timestamp de mensaje enviado para rate limiting"""
        self._message_timestamps.append(datetime.now())
    
    def validate_phone_number(self, phone: str, country_code: str = "PE") -> Tuple[bool, str, str]:
        """
        Valida y formatea número telefónico peruano
        
        Args:
            phone: Número telefónico a validar
            country_code: Código de país (default: PE)
            
        Returns:
            Tuple[bool, str, str]: (es_válido, número_formateado, mensaje_error)
        """
        try:
            # Limpiar el número de espacios y caracteres especiales
            phone_clean = re.sub(r'[^\d+]', '', phone)
            
            # Agregar código de país si no está presente
            if not phone_clean.startswith('+'):
                if phone_clean.startswith('51'):
                    phone_clean = '+' + phone_clean
                elif phone_clean.startswith('9') and len(phone_clean) == 9:
                    phone_clean = '+51' + phone_clean
                else:
                    return False, "", "Formato de número inválido para Perú"
            
            # Parsear número con phonenumbers
            parsed_number = phonenumbers.parse(phone_clean, country_code)
            
            # Validar que es un número válido
            if not phonenumbers.is_valid_number(parsed_number):
                return False, "", "Número telefónico no válido"
            
            # Validar que es un número móvil peruano
            if parsed_number.country_code != 51:
                return False, "", "Solo se permiten números peruanos (+51)"
                
            number_type = phonenumbers.number_type(parsed_number)
            if number_type not in [phonenumbers.PhoneNumberType.MOBILE, phonenumbers.PhoneNumberType.FIXED_LINE_OR_MOBILE]:
                return False, "", "Solo se permiten números móviles"
            
            # Formatear para WhatsApp (sin símbolos, solo dígitos)
            formatted = phonenumbers.format_number(parsed_number, PhoneNumberFormat.E164)
            whatsapp_format = formatted.replace('+', '')
            
            return True, whatsapp_format, ""
            
        except NumberParseException as e:
            return False, "", f"Error al parsear número: {str(e)}"
        except Exception as e:
            logger.error(f"Error validando número telefónico {phone}: {str(e)}")
            return False, "", "Error interno al validar número"
    
    def render_message_template(self, template: str, variables: Dict[str, Any]) -> str:
        """
        Renderiza plantilla de mensaje con variables
        
        Args:
            template: Plantilla Jinja2 del mensaje
            variables: Diccionario con variables para reemplazar
            
        Returns:
            str: Mensaje renderizado
        """
        try:
            jinja_template = Template(template)
            rendered_message = jinja_template.render(**variables)
            
            # Validar longitud máxima para WhatsApp (1024 caracteres)
            if len(rendered_message) > 1024:
                logger.warning(f"Mensaje excede 1024 caracteres: {len(rendered_message)}")
                rendered_message = rendered_message[:1021] + "..."
            
            return rendered_message
            
        except Exception as e:
            logger.error(f"Error renderizando plantilla: {str(e)}")
            raise ValidationError(f"Error en plantilla de mensaje: {str(e)}")
    
    def is_within_work_hours(self, timezone: str = None) -> bool:
        """
        Verifica si la hora actual está dentro del horario laboral
        
        Args:
            timezone: Zona horaria (default: configuración)
            
        Returns:
            bool: True si está en horario laboral
        """
        try:
            tz = pytz.timezone(timezone or settings.WHATSAPP_TIMEZONE)
            now = datetime.now(tz)
            
            # Obtener hora actual
            current_time = now.time()
            
            # Parsear horas de configuración
            start_time = datetime.strptime(settings.WHATSAPP_WORK_HOURS_START, "%H:%M").time()
            end_time = datetime.strptime(settings.WHATSAPP_WORK_HOURS_END, "%H:%M").time()
            
            # Verificar si es día laborable (lunes a viernes por default)
            is_weekday = now.weekday() < 5  # 0=Monday, 6=Sunday
            
            # Verificar si está en horario
            is_work_hour = start_time <= current_time <= end_time
            
            return is_weekday and is_work_hour
            
        except Exception as e:
            logger.error(f"Error verificando horario laboral: {str(e)}")
            return True  # En caso de error, permitir envío
    
    async def send_message(
        self,
        phone_number: str,
        message: str,
        message_type: str = "text"
    ) -> Dict[str, Any]:
        """
        Envía mensaje de WhatsApp
        
        Args:
            phone_number: Número de teléfono (formato E164 sin +)
            message: Contenido del mensaje
            message_type: Tipo de mensaje (text, template, etc.)
            
        Returns:
            Dict con respuesta de la API de WhatsApp
        """
        if not self.access_token or not self.phone_number_id:
            raise WhatsAppError("WhatsApp no configurado correctamente")
        
        # Verificar rate limit
        if not self._can_send_message():
            raise WhatsAppError("Rate limit excedido. Intente más tarde.")
        
        url = f"{self.api_url}/{self.phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "to": phone_number,
            "type": message_type,
            "text": {
                "body": message
            }
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url, 
                    json=payload, 
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    response_data = await response.json()
                    
                    if response.status == 200:
                        # Registrar timestamp para rate limiting
                        self._add_message_timestamp()
                        
                        logger.info(f"Mensaje enviado exitosamente a {phone_number}")
                        return {
                            "success": True,
                            "message_id": response_data.get("messages", [{}])[0].get("id"),
                            "status": "sent",
                            "response": response_data
                        }
                    else:
                        error_msg = response_data.get("error", {}).get("message", "Error desconocido")
                        logger.error(f"Error enviando mensaje: {error_msg}")
                        raise WhatsAppError(f"Error de WhatsApp API: {error_msg}")
                        
        except aiohttp.ClientError as e:
            logger.error(f"Error de conexión con WhatsApp API: {str(e)}")
            raise WhatsAppError(f"Error de conectividad: {str(e)}")
        except asyncio.TimeoutError:
            logger.error("Timeout al enviar mensaje de WhatsApp")
            raise WhatsAppError("Timeout al enviar mensaje")
        except Exception as e:
            logger.error(f"Error inesperado enviando mensaje: {str(e)}")
            raise WhatsAppError(f"Error interno: {str(e)}")
    
    async def send_message_with_retry(
        self,
        phone_number: str,
        message: str,
        max_retries: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Envía mensaje con sistema de reintentos y backoff exponencial
        
        Args:
            phone_number: Número de teléfono
            message: Contenido del mensaje
            max_retries: Máximo número de reintentos (default: configuración)
            
        Returns:
            Dict con resultado del envío
        """
        max_retries = max_retries or self.retry_attempts
        last_error = None
        
        for attempt in range(max_retries + 1):
            try:
                return await self.send_message(phone_number, message)
                
            except WhatsAppError as e:
                last_error = e
                
                if attempt < max_retries:
                    # Backoff exponencial: 30s, 60s, 120s
                    delay = self.retry_delay * (2 ** attempt)
                    logger.warning(f"Intento {attempt + 1} falló, reintentando en {delay}s: {str(e)}")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"Todos los reintentos fallaron para {phone_number}: {str(e)}")
        
        return {
            "success": False,
            "error": str(last_error),
            "attempts": max_retries + 1
        }
    
    def parse_webhook_payload(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Procesa payload de webhook de WhatsApp
        
        Args:
            payload: Datos recibidos del webhook
            
        Returns:
            Lista de eventos procesados
        """
        events = []
        
        try:
            if "entry" not in payload:
                return events
            
            for entry in payload["entry"]:
                if "changes" not in entry:
                    continue
                    
                for change in entry["changes"]:
                    if change.get("field") != "messages":
                        continue
                    
                    value = change.get("value", {})
                    
                    # Procesar estados de mensajes
                    if "statuses" in value:
                        for status in value["statuses"]:
                            events.append({
                                "type": "message_status",
                                "message_id": status.get("id"),
                                "status": status.get("status"),
                                "timestamp": status.get("timestamp"),
                                "recipient_id": status.get("recipient_id"),
                                "errors": status.get("errors", [])
                            })
                    
                    # Procesar mensajes recibidos
                    if "messages" in value:
                        for message in value["messages"]:
                            events.append({
                                "type": "message_received",
                                "message_id": message.get("id"),
                                "from": message.get("from"),
                                "timestamp": message.get("timestamp"),
                                "text": message.get("text", {}).get("body", ""),
                                "message_type": message.get("type")
                            })
            
            return events
            
        except Exception as e:
            logger.error(f"Error procesando webhook payload: {str(e)}")
            return []
    
    async def verify_webhook(self, mode: str, token: str, challenge: str) -> Optional[str]:
        """
        Verifica webhook de WhatsApp durante setup
        
        Args:
            mode: Modo de verificación
            token: Token recibido
            challenge: Challenge string
            
        Returns:
            Challenge string si es válido, None si no
        """
        if mode == "subscribe" and token == settings.WHATSAPP_VERIFY_TOKEN:
            logger.info("Webhook de WhatsApp verificado exitosamente")
            return challenge
        else:
            logger.warning(f"Verificación de webhook falló - token: {token}")
            return None
    
    def get_message_status_description(self, status: str) -> str:
        """
        Obtiene descripción amigable del estado del mensaje
        
        Args:
            status: Estado del mensaje de WhatsApp
            
        Returns:
            str: Descripción amigable
        """
        status_descriptions = {
            "sent": "Enviado",
            "delivered": "Entregado",
            "read": "Leído",
            "failed": "Fallido",
            "deleted": "Eliminado"
        }
        return status_descriptions.get(status, f"Estado desconocido: {status}")
    
    async def get_business_profile(self) -> Dict[str, Any]:
        """
        Obtiene perfil de negocio de WhatsApp
        
        Returns:
            Dict con información del perfil
        """
        if not self.access_token or not self.phone_number_id:
            raise WhatsAppError("WhatsApp no configurado")
        
        url = f"{self.api_url}/{self.phone_number_id}"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_data = await response.json()
                        raise WhatsAppError(f"Error obteniendo perfil: {error_data}")
                        
        except Exception as e:
            logger.error(f"Error obteniendo perfil de negocio: {str(e)}")
            raise WhatsAppError(f"Error obteniendo perfil: {str(e)}")
    
    def format_message_for_logging(self, phone: str, message: str) -> str:
        """
        Formatea mensaje para logging (enmascarando datos sensibles)
        
        Args:
            phone: Número de teléfono
            message: Contenido del mensaje
            
        Returns:
            str: Mensaje formateado para log
        """
        # Enmascarar número telefónico (mostrar solo últimos 4 dígitos)
        masked_phone = "****" + phone[-4:] if len(phone) > 4 else "****"
        
        # Truncar mensaje si es muy largo
        truncated_message = message[:100] + "..." if len(message) > 100 else message
        
        return f"To: {masked_phone}, Message: {truncated_message}"

# Instancia global del servicio
whatsapp_service = WhatsAppService()