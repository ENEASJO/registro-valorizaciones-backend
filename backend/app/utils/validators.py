"""
Utilidades de validación
"""
import re
from typing import Optional


def validate_ruc(ruc: Optional[str]) -> bool:
    """
    Validar formato de RUC peruano
    
    Args:
        ruc: RUC a validar
        
    Returns:
        bool: True si el RUC es válido
    """
    if not ruc:
        return False
    
    # Remover espacios en blanco
    ruc = ruc.strip()
    
    # Verificar que tenga exactamente 11 dígitos
    if not re.match(r'^\d{11}$', ruc):
        return False
    
    # Verificar que comience con dígitos válidos (10 para persona natural, 20 para persona jurídica)
    primeros_dos_digitos = ruc[:2]
    if primeros_dos_digitos not in ['10', '20']:
        return False
    
    return True


def clean_ruc(ruc: Optional[str]) -> Optional[str]:
    """
    Limpiar y normalizar RUC
    
    Args:
        ruc: RUC a limpiar
        
    Returns:
        str: RUC limpio o None si no es válido
    """
    if not ruc:
        return None
    
    # Remover espacios y caracteres no numéricos
    ruc_clean = re.sub(r'[^\d]', '', ruc.strip())
    
    # Validar longitud
    if len(ruc_clean) != 11:
        return None
    
    return ruc_clean


def validate_documento_identidad(numero_doc: Optional[str], tipo_doc: str = "DNI") -> bool:
    """
    Validar número de documento de identidad
    
    Args:
        numero_doc: Número de documento
        tipo_doc: Tipo de documento (DNI, CE, etc.)
        
    Returns:
        bool: True si el documento es válido
    """
    if not numero_doc:
        return False
    
    numero_doc = numero_doc.strip()
    
    if tipo_doc.upper() == "DNI":
        # DNI debe tener 8 dígitos
        return re.match(r'^\d{8}$', numero_doc) is not None
    elif tipo_doc.upper() == "CE":
        # Carnet de extranjería puede tener varios formatos
        return re.match(r'^[\dA-Z]{4,12}$', numero_doc.upper()) is not None
    
    # Para otros tipos, validación básica
    return len(numero_doc) >= 4 and len(numero_doc) <= 15


def normalize_text(text: Optional[str]) -> str:
    """
    Normalizar texto (mayúsculas, espacios, etc.)
    
    Args:
        text: Texto a normalizar
        
    Returns:
        str: Texto normalizado
    """
    if not text:
        return ""
    
    # Convertir a mayúsculas y limpiar espacios extra
    text = text.strip().upper()
    text = re.sub(r'\s+', ' ', text)  # Múltiples espacios -> un espacio
    
    return text


def is_valid_name(name: Optional[str]) -> bool:
    """
    Validar que sea un nombre válido (no header de tabla, etc.)
    
    Args:
        name: Nombre a validar
        
    Returns:
        bool: True si el nombre es válido
    """
    if not name or len(name.strip()) < 3:
        return False
    
    name = name.strip().upper()
    
    # Headers inválidos comunes
    headers_invalidos = [
        "NOMBRE", "APELLIDOS", "TIPO", "DOC", "CARGO", "FECHA",
        "DOCUMENTO", "REPRESENTANTE", "LEGAL", "DESDE", "HASTA",
        "NUMERO", "VIGENCIA", "ESTADO", "CONDICION"
    ]
    
    if name in headers_invalidos:
        return False
    
    # No debe ser solo guiones o caracteres especiales
    if re.match(r'^[-\s_]+$', name):
        return False
    
    return True