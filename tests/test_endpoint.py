#!/usr/bin/env python3
"""
Script para probar el endpoint POST /api/empresas
y ver qué está causando el error 500
"""

import requests
import json
import sys

# URL del backend
BACKEND_URL = "https://registro-valorizaciones-backend-503600768755.southamerica-west1.run.app/api/empresas"

# Datos de prueba que envía el frontend
test_data = {
    "ruc": "20610701117",
    "razon_social": "VIDA SANA ALEMANA SOCIEDAD ANONIMA CERRADA - VIDA SANA ALEMANA S.A.C.",
    "dni": None,
    "tipo_empresa": "SAC",
    "email": "estudiocontablefiori@gmail.com",
    "telefono": None,
    "direccion": "JR. AMAZONAS NRO. 435 INT. 202",
    "representante_legal": None,
    "dni_representante": None,
    "estado": "ACTIVO",
    "categoria_contratista": "EJECUTORA",
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
    "especialidades_oece": [],
    "estado_sunat": "ACTIVO",
    "estado_osce": "ACTIVO",
    "fuentes_consultadas": ["OECE"],
    "capacidad_contratacion": None
}

print("🔍 Probando endpoint POST /api/empresas")
print(f"URL: {BACKEND_URL}")
print(f"Datos: {json.dumps(test_data, indent=2)}")
print("\n" + "="*50 + "\n")

try:
    # Hacer la petición
    response = requests.post(
        BACKEND_URL,
        json=test_data,
        headers={'Content-Type': 'application/json'},
        timeout=30
    )

    print(f"Status Code: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")

    if response.status_code == 200:
        print("\n✅ ÉXITO!")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    else:
        print(f"\n❌ ERROR {response.status_code}")
        try:
            print(f"Response: {response.text}")
        except:
            print("No se pudo obtener el cuerpo de la respuesta")

except requests.exceptions.RequestException as e:
    print(f"❌ Error de conexión: {e}")
    sys.exit(1)

print("\n" + "="*50)