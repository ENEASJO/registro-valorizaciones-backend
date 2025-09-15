"""
Middleware para validar respuestas de API y evitar errores de tipo
"""
import json
from typing import Dict, Any, List
from datetime import datetime
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import uuid

class ResponseValidationMiddleware(BaseHTTPMiddleware):
    """
    Middleware que valida las respuestas de la API para asegurar
    que los tipos de datos sean correctos antes de enviarlos
    """

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Solo validar respuestas JSON
        if response.headers.get("content-type", "").startswith("application/json"):
            try:
                # Clonar la respuesta para poder leer el cuerpo
                body = b""
                async for chunk in response.body_iterator:
                    body += chunk

                # Parsear el JSON
                data = json.loads(body.decode())

                # Validar y corregir si es necesario
                validated_data = self.validate_and_fix_response(data)

                # Crear nueva respuesta con los datos validados
                new_body = json.dumps(validated_data).encode()
                response = Response(
                    content=new_body,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type="application/json"
                )

            except Exception as e:
                # Si hay error en la validación, loggear pero no romper
                print(f"⚠️ Error en validación de respuesta: {e}")
                # Devolver respuesta original para no romper la API

        return response

    def validate_and_fix_response(self, data: Any) -> Any:
        """Valida y corrige los tipos de datos en la respuesta"""

        if isinstance(data, dict):
            # Si es una respuesta de empresa
            if data.get('success') and data.get('data'):
                empresas_data = data.get('data', {})
                if 'empresas' in empresas_data:
                    # Validar cada empresa
                    empresas_data['empresas'] = [
                        self.fix_empresa_types(empresa)
                        for empresa in empresas_data['empresas']
                    ]

            # Si es un solo objeto empresa
            elif 'id' in data and 'ruc' in data:
                data = self.fix_empresa_types(data)

            # Recursivamente validar otros objetos
            for key, value in data.items():
                data[key] = self.validate_and_fix_response(value)

        elif isinstance(data, list):
            # Validar cada elemento de la lista
            data = [self.validate_and_fix_response(item) for item in data]

        return data

    def fix_empresa_types(self, empresa: Dict[str, Any]) -> Dict[str, Any]:
        """Corrige los tipos de datos de una empresa"""

        # Asegurar que ID sea string
        if 'id' in empresa:
            empresa['id'] = str(empresa['id'])

        # Validar representantes
        if 'representantes' in empresa and isinstance(empresa['representantes'], list):
            empresa['representantes'] = [
                self.fix_representante_types(rep)
                for rep in empresa['representantes']
            ]

        # Asegurar que los timestamps sean strings ISO
        for timestamp_field in ['created_at', 'updated_at']:
            if timestamp_field in empresa:
                value = empresa[timestamp_field]
                if isinstance(value, datetime):
                    empresa[timestamp_field] = value.isoformat()
                elif isinstance(value, str):
                    # Validar que sea un formato ISO válido
                    try:
                        datetime.fromisoformat(value.replace('Z', '+00:00'))
                    except:
                        empresa[timestamp_field] = datetime.now().isoformat()

        return empresa

    def fix_representante_types(self, representante: Dict[str, Any]) -> Dict[str, Any]:
        """Corrige los tipos de datos de un representante"""

        # Asegurar que ID sea string
        if 'id' in representante:
            representante['id'] = str(representante['id'])

        # Validar timestamps
        for timestamp_field in ['created_at', 'fecha_desde']:
            if timestamp_field in representante:
                value = representante[timestamp_field]
                if isinstance(value, datetime):
                    representante[timestamp_field] = value.isoformat()
                elif isinstance(value, str):
                    try:
                        datetime.fromisoformat(value.replace('Z', '+00:00'))
                    except:
                        representante[timestamp_field] = datetime.now().isoformat()

        return representante

def is_valid_uuid(uuid_string: str) -> bool:
    """Verifica si un string es un UUID válido"""
    try:
        uuid.UUID(uuid_string)
        return True
    except ValueError:
        return False

def safe_str_conversion(value: Any, default: str = "0") -> str:
    """Convierte cualquier valor a string de forma segura"""
    try:
        return str(value)
    except:
        return default