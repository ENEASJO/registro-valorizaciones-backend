"""
Utilidades para generar códigos automáticos de obra
"""
import asyncio
from datetime import datetime
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class CodigoGenerator:
    """Generador de códigos automáticos para obras"""
    
    @staticmethod
    def generar_codigo_obra(
        empresa_id: int,
        prefijo: str = "OBR",
        año: Optional[int] = None
    ) -> str:
        """
        Genera un código único para obra usando el patrón:
        {PREFIJO}-{EMPRESA_ID}-{AÑO}-{SECUENCIA}
        
        Ejemplo: OBR-001-2025-0001
        
        Args:
            empresa_id: ID de la empresa
            prefijo: Prefijo del código (por defecto "OBR")
            año: Año para el código (por defecto año actual)
            
        Returns:
            Código generado como string
        """
        if año is None:
            año = datetime.now().year
            
        # Formatear empresa_id con 3 dígitos
        empresa_str = str(empresa_id).zfill(3)
        
        # Por ahora generar secuencia basada en timestamp para evitar duplicados
        # En producción debería usar una secuencia de base de datos
        timestamp = datetime.now()
        secuencia = f"{timestamp.month:02d}{timestamp.day:02d}{timestamp.hour:02d}{timestamp.minute:02d}"
        
        codigo = f"{prefijo}-{empresa_str}-{año}-{secuencia}"
        
        logger.info(f"📝 Código generado: {codigo}")
        return codigo
    
    @staticmethod
    def generar_codigo_valorizacion(
        obra_codigo: str,
        numero_valorizacion: int,
        prefijo: str = "VAL"
    ) -> str:
        """
        Genera código para valorización usando el patrón:
        {PREFIJO}-{OBRA_CODIGO}-{NUMERO}
        
        Ejemplo: VAL-OBR-001-2025-0001-001
        
        Args:
            obra_codigo: Código de la obra
            numero_valorizacion: Número de la valorización
            prefijo: Prefijo del código (por defecto "VAL")
            
        Returns:
            Código de valorización generado
        """
        numero_str = str(numero_valorizacion).zfill(3)
        codigo = f"{prefijo}-{obra_codigo}-{numero_str}"
        
        logger.info(f"📝 Código de valorización generado: {codigo}")
        return codigo
    
    @staticmethod
    def validar_codigo_obra(codigo: str) -> bool:
        """
        Valida si un código de obra tiene el formato correcto
        
        Args:
            codigo: Código a validar
            
        Returns:
            True si el formato es válido
        """
        if not codigo:
            return False
            
        partes = codigo.split('-')
        
        # Debe tener 4 partes: PREFIJO-EMPRESA-AÑO-SECUENCIA
        if len(partes) != 4:
            return False
            
        prefijo, empresa, año, secuencia = partes
        
        # Validar cada parte
        try:
            # Prefijo debe ser texto
            if not prefijo.isalpha():
                return False
                
            # Empresa debe ser numérico
            int(empresa)
            
            # Año debe ser numérico y razonable
            año_int = int(año)
            if año_int < 2020 or año_int > 2100:
                return False
                
            # Secuencia debe ser numérica
            int(secuencia)
            
            return True
            
        except ValueError:
            return False
    
    @staticmethod
    def extraer_info_codigo(codigo: str) -> dict:
        """
        Extrae información de un código de obra
        
        Args:
            codigo: Código a analizar
            
        Returns:
            Diccionario con información extraída
        """
        if not CodigoGenerator.validar_codigo_obra(codigo):
            return {}
            
        partes = codigo.split('-')
        prefijo, empresa, año, secuencia = partes
        
        return {
            "prefijo": prefijo,
            "empresa_id": int(empresa),
            "año": int(año),
            "secuencia": secuencia,
            "codigo_completo": codigo
        }

# Función de conveniencia para usar directamente
async def generar_codigo_obra_async(empresa_id: int, prefijo: str = "OBR") -> str:
    """
    Versión async del generador de códigos (para futuras mejoras con DB)
    """
    return CodigoGenerator.generar_codigo_obra(empresa_id, prefijo)