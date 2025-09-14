#!/usr/bin/env python3
"""
Script para probar con el formato exacto que el backend espera
"""

import requests
import json

BACKEND_URL = "https://registro-valorizaciones-backend-503600768755.southamerica-west1.run.app/api/empresas"

# Datos que coinciden exactamente con lo que espera el backend
# Basado en el código de empresa_service_neon.py
empresa_data_neon = {
    'ruc': '20610701117',
    'razon_social': 'VIDA SANA ALEMANA SOCIEDAD ANONIMA CERRADA',
    'nombre_comercial': 'VIDA SANA ALEMANA S.A.C.',
    'email': 'estudiocontablefiori@gmail.com',
    'telefono': '',
    'direccion': 'JR. AMAZONAS NRO. 435 INT. 202',
    'representante_legal': 'FEDERICO GIANCARLO CORONADO RODRIGUEZ',
    'dni_representante': '07779930',
    'estado': 'ACTIVO',
    'tipo_empresa': 'SAC',
    'categoria_contratista': 'EJECUTORA'
}

# Pero el endpoint espera el formato de EmpresaCreateSchema
# Vamos a construir el payload correcto
payload = {
    "ruc": "20610701117",
    "razon_social": "VIDA SANA ALEMANA SOCIEDAD ANONIMA CERRADA - VIDA SANA ALEMANA S.A.C.",
    "email": "estudiocontablefiori@gmail.com",
    "celular": None,
    "direccion": "JR. AMAZONAS NRO. 435 INT. 202",
    "representantes": [
        {
            "nombre": "FEDERICO GIANCARLO CORONADO RODRIGUEZ",
            "cargo": "SOCIO",
            "numero_documento": "07779930",
            "tipo_documento": "DNI",
            "fuente": "OECE",
            "es_principal": True,
            "activo": True
        },
        {
            "nombre": "JORGE LUIS AYALA FLORES",
            "cargo": "SOCIO",
            "numero_documento": "09461684",
            "tipo_documento": "DNI",
            "fuente": "OECE",
            "es_principal": False,
            "activo": True
        }
    ],
    "representante_principal_id": 0,
    "estado": "ACTIVO",
    "tipo_empresa": "SAC",
    "categoria_contratista": "EJECUTORA",
    "especialidades_oece": [],
    "estado_sunat": "ACTIVO",
    "estado_osce": "ACTIVO",
    "fuentes_consultadas": ["OECE"],
    "capacidad_contratacion": None
}

print("Enviando petición con payload completo...")
print(json.dumps(payload, indent=2))

try:
    response = requests.post(
        BACKEND_URL,
        json=payload,
        headers={'Content-Type': 'application/json'},
        timeout=30
    )

    print(f"\nStatus Code: {response.status_code}")

    if response.status_code == 200:
        print("\n✅ ÉXITO!")
        print(json.dumps(response.json(), indent=2))
    else:
        print(f"\n❌ ERROR {response.status_code}")
        try:
            error_json = response.json()
            print(json.dumps(error_json, indent=2))
        except:
            print(response.text)

except Exception as e:
    print(f"\n❌ Error: {e}")