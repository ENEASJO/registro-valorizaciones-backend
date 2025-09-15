#!/usr/bin/env python3
"""
Test script to verify the UUID conversion fix
"""
import sys
sys.path.append('.')

from datetime import datetime
from typing import Dict, Any
from app.api.routes.empresas import convertir_empresa_dict_a_response

def test_uuid_conversion():
    """Test the conversion function with UUID data"""

    # Mock empresa data that would come from the database
    empresa_mock = {
        'id': '123',  # This should be an integer string
        'ruc': '20123456789',
        'razon_social': 'Test Company',
        'nombre_comercial': 'Test Co',
        'email': 'test@example.com',
        'telefono': '999123456',
        'direccion': 'Av. Test 123',
        'departamento': 'Lima',
        'provincia': 'Lima',
        'distrito': 'Miraflores',
        'ubigeo': '150101',
        'estado_contribuyente': 'ACTIVO',
        'tipo_contribuyente': 'EMPRESA',
        'fecha_inscripcion': '2020-01-01',
        'created_at': datetime.now(),
        'updated_at': datetime.now(),
        'representantes_legales': [
            {
                'id': '96aefc9c-e193-477a-a6d3-51b5e03a8aea',  # UUID as string
                'empresa_id': '123',
                'nombre': 'John Doe',
                'cargo': 'Gerente',
                'tipo_documento': 'DNI',
                'numero_documento': '12345678',
                'participacion': 100.0,
                'fuente': 'TEST',
                'es_principal': True,
                'activo': True,
                'fecha_desde': '2020-01-01',
                'created_at': datetime.now()
            }
        ]
    }

    print("Testing UUID conversion...")
    print(f"Empresa ID: {empresa_mock['id']} (type: {type(empresa_mock['id'])})")
    print(f"Representante ID: {empresa_mock['representantes_legales'][0]['id']} (type: {type(empresa_mock['representantes_legales'][0]['id'])})")

    try:
        result = convertir_empresa_dict_a_response(empresa_mock)
        print("\n✅ Success! Conversion completed without errors")
        print(f"Empresa ID in response: {result.id} (type: {type(result.id)})")
        print(f"First representante ID: {result.representantes_legales[0].id} (type: {type(result.representantes_legales[0].id)})")
        return True
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_uuid_conversion()