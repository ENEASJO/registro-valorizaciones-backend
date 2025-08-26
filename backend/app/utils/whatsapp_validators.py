"""
Utilidades de validación específicas para el sistema de notificaciones WhatsApp
"""

import re
import json
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, time, date
import phonenumbers
from phonenumbers import NumberParseException, PhoneNumberFormat
import pytz

from app.models.whatsapp_notifications import EventoTrigger, EstadoNotificacion, TipoContacto

logger = logging.getLogger(__name__)

class WhatsAppValidators:
    """Clase con utilidades de validación para WhatsApp"""
    
    @staticmethod
    def validate_phone_number(phone: str, country_code: str = "PE") -> Tuple[bool, str, str]:
        """
        Valida y formatea número telefónico peruano para WhatsApp
        
        Args:
            phone: Número telefónico a validar
            country_code: Código de país (default: PE para Perú)
            
        Returns:
            Tuple[bool, str, str]: (es_válido, número_formateado, mensaje_error)
        """
        try:
            if not phone or not isinstance(phone, str):
                return False, "", "Número telefónico es requerido"
            
            # Limpiar número de espacios, guiones y caracteres especiales
            phone_clean = re.sub(r'[^\d+]', '', phone.strip())
            
            if not phone_clean:
                return False, "", "Número telefónico no puede estar vacío"
            
            # Agregar código de país para Perú si no está presente
            if not phone_clean.startswith('+'):
                if phone_clean.startswith('51'):
                    # Ya tiene código de país sin el +
                    phone_clean = '+' + phone_clean
                elif phone_clean.startswith('9') and len(phone_clean) == 9:
                    # Número móvil peruano sin código de país
                    phone_clean = '+51' + phone_clean
                elif len(phone_clean) == 8:
                    # Número fijo peruano sin código de país
                    phone_clean = '+51' + phone_clean
                else:
                    return False, "", "Formato de número inválido para Perú"
            
            # Parsear número con phonenumbers
            try:
                parsed_number = phonenumbers.parse(phone_clean, country_code)
            except NumberParseException as e:
                error_messages = {
                    NumberParseException.INVALID_COUNTRY_CODE: "Código de país inválido",
                    NumberParseException.NOT_A_NUMBER: "No es un número válido",
                    NumberParseException.TOO_SHORT_NSN: "Número muy corto",
                    NumberParseException.TOO_LONG: "Número muy largo",
                    NumberParseException.TOO_SHORT_AFTER_IDD: "Número muy corto después del código internacional"
                }
                return False, "", error_messages.get(e.error_type, f"Error al parsear número: {str(e)}")
            
            # Validar que es un número válido
            if not phonenumbers.is_valid_number(parsed_number):
                return False, "", "Número telefónico no es válido según estándares internacionales"
            
            # Validar que es un número peruano
            if parsed_number.country_code != 51:
                return False, "", "Solo se permiten números peruanos (+51)"
            
            # Validar que es un número móvil o fijo
            number_type = phonenumbers.number_type(parsed_number)
            if number_type not in [
                phonenumbers.PhoneNumberType.MOBILE, 
                phonenumbers.PhoneNumberType.FIXED_LINE_OR_MOBILE,
                phonenumbers.PhoneNumberType.FIXED_LINE
            ]:
                return False, "", "Solo se permiten números móviles o fijos"
            
            # Formatear para WhatsApp (E164 sin símbolo +)
            formatted = phonenumbers.format_number(parsed_number, PhoneNumberFormat.E164)
            whatsapp_format = formatted.replace('+', '')
            
            return True, whatsapp_format, ""
            
        except Exception as e:
            logger.error(f"Error inesperado validando número {phone}: {str(e)}")
            return False, "", f"Error interno al validar número: {str(e)}"
    
    @staticmethod
    def validate_message_content(message: str, max_length: int = 1024) -> Tuple[bool, str]:
        """
        Valida el contenido de un mensaje de WhatsApp
        
        Args:
            message: Contenido del mensaje
            max_length: Longitud máxima permitida
            
        Returns:
            Tuple[bool, str]: (es_válido, mensaje_error)
        """
        if not message or not isinstance(message, str):
            return False, "El mensaje es requerido y debe ser texto"
        
        message_clean = message.strip()
        
        if not message_clean:
            return False, "El mensaje no puede estar vacío"
        
        if len(message_clean) > max_length:
            return False, f"El mensaje excede la longitud máxima de {max_length} caracteres"
        
        # Validar caracteres problemáticos para WhatsApp
        problematic_chars = ['\x00', '\x01', '\x02', '\x03', '\x04', '\x05', '\x06', '\x07', '\x08']
        for char in problematic_chars:
            if char in message_clean:
                return False, f"El mensaje contiene caracteres no válidos"
        
        return True, ""
    
    @staticmethod
    def validate_template_variables(template: str, available_variables: List[str]) -> Tuple[bool, List[str], str]:
        """
        Valida las variables utilizadas en una plantilla
        
        Args:
            template: Plantilla de mensaje con variables Jinja2
            available_variables: Lista de variables disponibles
            
        Returns:
            Tuple[bool, List[str], str]: (es_válido, variables_encontradas, mensaje_error)
        """
        try:
            # Buscar variables en formato {variable}
            pattern = r'\{([^}]+)\}'
            variables_found = re.findall(pattern, template)
            
            if not variables_found:
                return True, [], ""
            
            # Verificar que todas las variables existen
            invalid_variables = []
            for var in variables_found:
                var_clean = var.strip()
                if var_clean not in available_variables:
                    invalid_variables.append(var_clean)
            
            if invalid_variables:
                return False, variables_found, f"Variables no disponibles: {', '.join(invalid_variables)}"
            
            return True, variables_found, ""
            
        except Exception as e:
            return False, [], f"Error validando plantilla: {str(e)}"
    
    @staticmethod
    def validate_time_range(start_time: str, end_time: str) -> Tuple[bool, str]:
        """
        Valida un rango de horas
        
        Args:
            start_time: Hora de inicio en formato HH:MM
            end_time: Hora de fin en formato HH:MM
            
        Returns:
            Tuple[bool, str]: (es_válido, mensaje_error)
        """
        try:
            # Validar formato
            time_pattern = r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$'
            
            if not re.match(time_pattern, start_time):
                return False, f"Hora de inicio inválida: {start_time}. Use formato HH:MM"
            
            if not re.match(time_pattern, end_time):
                return False, f"Hora de fin inválida: {end_time}. Use formato HH:MM"
            
            # Parsear horas
            start = datetime.strptime(start_time, "%H:%M").time()
            end = datetime.strptime(end_time, "%H:%M").time()
            
            # Validar que la hora de inicio sea menor que la de fin
            if start >= end:
                return False, "La hora de inicio debe ser anterior a la hora de fin"
            
            return True, ""
            
        except ValueError as e:
            return False, f"Error en formato de hora: {str(e)}"
        except Exception as e:
            return False, f"Error validando rango de horas: {str(e)}"
    
    @staticmethod
    def validate_timezone(timezone_str: str) -> Tuple[bool, str]:
        """
        Valida una zona horaria
        
        Args:
            timezone_str: Zona horaria (ej: 'America/Lima')
            
        Returns:
            Tuple[bool, str]: (es_válido, mensaje_error)
        """
        try:
            pytz.timezone(timezone_str)
            return True, ""
        except pytz.exceptions.UnknownTimeZoneError:
            return False, f"Zona horaria desconocida: {timezone_str}"
        except Exception as e:
            return False, f"Error validando zona horaria: {str(e)}"
    
    @staticmethod
    def validate_workdays(workdays: List[str]) -> Tuple[bool, str]:
        """
        Valida una lista de días laborables
        
        Args:
            workdays: Lista de días en español
            
        Returns:
            Tuple[bool, str]: (es_válido, mensaje_error)
        """
        valid_days = ["LUNES", "MARTES", "MIERCOLES", "JUEVES", "VIERNES", "SABADO", "DOMINGO"]
        
        if not workdays or not isinstance(workdays, list):
            return False, "Días laborables deben ser una lista"
        
        if len(workdays) == 0:
            return False, "Debe especificar al menos un día laborable"
        
        for day in workdays:
            if not isinstance(day, str) or day.upper() not in valid_days:
                return False, f"Día inválido: {day}. Use: {', '.join(valid_days)}"
        
        return True, ""
    
    @staticmethod
    def validate_json_field(json_str: str, field_name: str) -> Tuple[bool, Any, str]:
        """
        Valida un campo JSON
        
        Args:
            json_str: String JSON a validar
            field_name: Nombre del campo (para mensajes de error)
            
        Returns:
            Tuple[bool, Any, str]: (es_válido, datos_parseados, mensaje_error)
        """
        try:
            if not json_str:
                return True, None, ""
            
            parsed_data = json.loads(json_str)
            return True, parsed_data, ""
            
        except json.JSONDecodeError as e:
            return False, None, f"JSON inválido en {field_name}: {str(e)}"
        except Exception as e:
            return False, None, f"Error validando JSON en {field_name}: {str(e)}"
    
    @staticmethod
    def validate_priority(priority: int) -> Tuple[bool, str]:
        """
        Valida la prioridad de una notificación
        
        Args:
            priority: Valor de prioridad (1-10)
            
        Returns:
            Tuple[bool, str]: (es_válido, mensaje_error)
        """
        if not isinstance(priority, int):
            return False, "La prioridad debe ser un número entero"
        
        if priority < 1 or priority > 10:
            return False, "La prioridad debe estar entre 1 (alta) y 10 (baja)"
        
        return True, ""
    
    @staticmethod
    def validate_retry_config(max_retries: int, delay_seconds: int) -> Tuple[bool, str]:
        """
        Valida configuración de reintentos
        
        Args:
            max_retries: Número máximo de reintentos
            delay_seconds: Segundos de delay entre reintentos
            
        Returns:
            Tuple[bool, str]: (es_válido, mensaje_error)
        """
        if not isinstance(max_retries, int) or max_retries < 0:
            return False, "Máximo de reintentos debe ser un entero mayor o igual a 0"
        
        if max_retries > 10:
            return False, "Máximo de reintentos no puede ser mayor a 10"
        
        if not isinstance(delay_seconds, int) or delay_seconds < 5:
            return False, "Delay debe ser un entero mayor o igual a 5 segundos"
        
        if delay_seconds > 3600:
            return False, "Delay no puede ser mayor a 3600 segundos (1 hora)"
        
        return True, ""
    
    @staticmethod
    def sanitize_template_content(content: str) -> str:
        """
        Sanitiza el contenido de una plantilla para WhatsApp
        
        Args:
            content: Contenido a sanitizar
            
        Returns:
            str: Contenido sanitizado
        """
        if not content:
            return ""
        
        # Remover caracteres de control problemáticos
        sanitized = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', content)
        
        # Normalizar saltos de línea
        sanitized = re.sub(r'\r\n', '\n', sanitized)
        sanitized = re.sub(r'\r', '\n', sanitized)
        
        # Limitar líneas consecutivas
        sanitized = re.sub(r'\n{3,}', '\n\n', sanitized)
        
        # Remover espacios al inicio y final
        sanitized = sanitized.strip()
        
        return sanitized
    
    @staticmethod
    def validate_contact_data(contact_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Valida datos completos de un contacto
        
        Args:
            contact_data: Diccionario con datos del contacto
            
        Returns:
            Tuple[bool, List[str]]: (es_válido, lista_de_errores)
        """
        errors = []
        
        # Validar nombre
        if not contact_data.get("nombre"):
            errors.append("El nombre es requerido")
        elif len(contact_data["nombre"]) > 255:
            errors.append("El nombre no puede exceder 255 caracteres")
        
        # Validar teléfono
        phone = contact_data.get("telefono", "")
        is_valid, _, phone_error = WhatsAppValidators.validate_phone_number(phone)
        if not is_valid:
            errors.append(f"Teléfono: {phone_error}")
        
        # Validar email si se proporciona
        email = contact_data.get("email")
        if email:
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, email):
                errors.append("Email no tiene formato válido")
        
        # Validar tipo de contacto
        tipo_contacto = contact_data.get("tipo_contacto")
        if tipo_contacto and tipo_contacto not in [tc.value for tc in TipoContacto]:
            errors.append(f"Tipo de contacto inválido: {tipo_contacto}")
        
        # Validar eventos suscritos si se proporcionan
        eventos_suscritos = contact_data.get("eventos_suscritos", [])
        if eventos_suscritos:
            for evento in eventos_suscritos:
                if hasattr(evento, 'value'):
                    evento = evento.value
                if evento not in [et.value for et in EventoTrigger]:
                    errors.append(f"Evento suscrito inválido: {evento}")
        
        return len(errors) == 0, errors

# Clase helper para validaciones complejas
class WhatsAppBusinessValidator:
    """Validador específico para reglas de WhatsApp Business API"""
    
    @staticmethod
    def validate_business_phone_format(phone: str) -> Tuple[bool, str]:
        """
        Valida formato específico requerido por WhatsApp Business
        
        Args:
            phone: Número en formato WhatsApp Business
            
        Returns:
            Tuple[bool, str]: (es_válido, mensaje_error)
        """
        # WhatsApp Business requiere formato específico sin + y con código de país
        if not phone or not isinstance(phone, str):
            return False, "Número requerido"
        
        # Debe ser solo dígitos
        if not phone.isdigit():
            return False, "Número debe contener solo dígitos"
        
        # Debe empezar con código de país (51 para Perú)
        if not phone.startswith('51'):
            return False, "Número debe incluir código de país 51 para Perú"
        
        # Longitud válida para números peruanos (51 + 9 dígitos = 11 total)
        if len(phone) != 11:
            return False, "Longitud inválida para número peruano (debe ser 11 dígitos incluyendo código de país)"
        
        return True, ""
    
    @staticmethod
    def validate_message_limits(message: str) -> Tuple[bool, str]:
        """
        Valida límites específicos de WhatsApp Business
        """
        if len(message) > 1024:
            return False, "Mensaje excede límite de 1024 caracteres de WhatsApp"
        
        # Validar número de líneas
        lines = message.split('\n')
        if len(lines) > 20:
            return False, "Mensaje no puede tener más de 20 líneas"
        
        return True, ""

# Funciones helper de conveniencia
def validate_phone_for_whatsapp(phone: str) -> Tuple[bool, str, str]:
    """Función de conveniencia para validar teléfonos"""
    return WhatsAppValidators.validate_phone_number(phone)

def validate_message_for_whatsapp(message: str) -> Tuple[bool, str]:
    """Función de conveniencia para validar mensajes"""
    return WhatsAppValidators.validate_message_content(message)

def sanitize_whatsapp_content(content: str) -> str:
    """Función de conveniencia para sanitizar contenido"""
    return WhatsAppValidators.sanitize_template_content(content)