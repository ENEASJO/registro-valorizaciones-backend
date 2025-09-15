"""
Pruebas para asegurar que el manejo de UUIDs sea correcto
"""
import pytest
from datetime import datetime
from app.api.routes.empresas import convertir_empresa_dict_a_response
from app.models.empresa import EmpresaResponse, RepresentanteResponse

def test_empresa_response_with_uuid_id():
    """Test que EmpresaResponse maneje correctamente UUIDs como strings"""
    # Datos de prueba con UUIDs
    empresa_data = {
        'id': '96aefc9c-e193-477a-a6d3-51b5e03a8aea',  # UUID como string
        'ruc': '20512345678',
        'razon_social': 'Test Company',
        'nombre_comercial': 'Test Co',
        'email': 'test@example.com',
        'telefono': '999123456',
        'direccion': 'Av. Test 123',
        'estado': 'ACTIVO',
        'tipo_empresa': 'SAC',
        'categoria_contratista': 'EJECUTORA',
        'especialidades': ['EDIFICACIONES'],
        'representantes': [
            {
                'id': '0d3cb2d2-d054-4ddc-846a-606d13c6ab3e',  # UUID como string
                'nombre': 'Test Representative',
                'cargo': 'Gerente',
                'numero_documento': '12345678',
                'tipo_documento': 'DNI',
                'es_principal': True,
                'activo': True,
                'fecha_desde': '2023-01-01',
                'created_at': datetime.now()
            }
        ],
        'created_at': datetime.now(),
        'updated_at': datetime.now()
    }

    # Esta función no debería lanzar error
    result = convertir_empresa_dict_a_response(empresa_data)

    # Verificaciones
    assert isinstance(result, EmpresaResponse)
    assert result.id == '96aefc9c-e193-477a-a6d3-51b5e03a8aea'
    assert isinstance(result.id, str)
    assert len(result.representantes) == 1
    assert isinstance(result.representantes[0].id, str)

def test_representante_response_uuid():
    """Test que RepresentanteResponse maneje UUIDs correctamente"""
    rep_data = {
        'id': '550e8400-e29b-41d4-a716-446655440000',
        'nombre': 'John Doe',
        'cargo': 'Manager',
        'numero_documento': '12345678',
        'tipo_documento': 'DNI',
        'es_principal': True,
        'activo': True,
        'estado': 'ACTIVO',  # Campo requerido
        'created_at': datetime.now()
    }

    response = RepresentanteResponse(**rep_data)
    assert isinstance(response.id, str)
    assert response.id == '550e8400-e29b-41d4-a716-446655440000'

def test_empresa_response_integer_id():
    """Test que EmpresaResponse también maneje IDs enteros para compatibilidad"""
    empresa_data = {
        'id': '123',  # ID como string que podría ser entero
        'ruc': '20512345678',
        'razon_social': 'Test Company',
        'representantes': [],
        'created_at': datetime.now(),
        'updated_at': datetime.now()
    }

    result = convertir_empresa_dict_a_response(empresa_data)
    assert result.id == '123'
    assert isinstance(result.id, str)