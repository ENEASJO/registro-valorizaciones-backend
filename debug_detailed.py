#!/usr/bin/env python3
"""
Script detallado para depurar el endpoint POST /api/empresas
"""

import requests
import json
import sys
import time

# URL del backend
BACKEND_URL = "https://registro-valorizaciones-backend-503600768755.southamerica-west1.run.app/api/empresas"

# Primero probemos si el backend está vivo
print("1. Verificando si el backend está respondiendo...")
try:
    response = requests.get(f"{BACKEND_URL}?limit=1", timeout=10)
    print(f"   Status GET: {response.status_code}")
    if response.status_code == 200:
        print("   ✅ Backend está respondiendo")
    else:
        print(f"   ❌ Backend respondió con {response.status_code}")
except Exception as e:
    print(f"   ❌ Error al conectar: {e}")
    sys.exit(1)

print("\n2. Probando con datos mínimos...")
# Datos mínimos para crear una empresa
minimal_data = {
    "ruc": "20610701117",
    "razon_social": "VIDA SANA ALEMANA SOCIEDAD ANONIMA CERRADA",
    "tipo_empresa": "SAC",
    "representantes": [
        {
            "nombre": "FEDERICO GIANCARLO CORONADO RODRIGUEZ",
            "cargo": "SOCIO",
            "numero_documento": "07779930",
            "tipo_documento": "DNI"
        }
    ],
    "representante_principal_id": 0,
    "categoria_contratista": "EJECUTORA"
}

print(f"   URL: {BACKEND_URL}")
print(f"   Datos: {json.dumps(minimal_data, indent=2)}")

try:
    response = requests.post(
        BACKEND_URL,
        json=minimal_data,
        headers={'Content-Type': 'application/json'},
        timeout=30
    )

    print(f"\n   Status Code: {response.status_code}")
    print(f"   Headers: {dict(response.headers)}")

    if response.status_code == 200:
        print("\n   ✅ ÉXITO!")
        print(f"   Response: {json.dumps(response.json(), indent=2)}")
    else:
        print(f"\n   ❌ ERROR {response.status_code}")
        try:
            error_response = response.json()
            print(f"   Error Response: {json.dumps(error_response, indent=2)}")
        except:
            print(f"   Raw Response: {response.text}")

        # Verificar si hay más información en los headers
        if 'x-cloud-trace-context' in response.headers:
            print(f"   Trace ID: {response.headers['x-cloud-trace-context']}")
            print("   Puedes buscar este Trace ID en Google Cloud Logging")

except requests.exceptions.RequestException as e:
    print(f"\n   ❌ Error de conexión: {e}")

print("\n3. Revisión del formato de fecha y campos...")
# Vamos a revisar si hay problemas con los campos de fecha
test_data_no_dates = {
    "ruc": "20610701117",
    "razon_social": "VIDA SANA ALEMANA SOCIEDAD ANONIMA CERRADA",
    "tipo_empresa": "SAC",
    "email": "",
    "telefono": "",
    "direccion": "",
    "representante_legal": "",
    "dni_representante": "",
    "estado": "ACTIVO",
    "categoria_contratista": "EJECUTORA",
    "representantes": [
        {
            "nombre": "FEDERICO GIANCARLO CORONADO RODRIGUEZ",
            "cargo": "SOCIO",
            "numero_documento": "07779930",
            "tipo_documento": "DNI",
            "participacion": "",
            "fuente": "MANUAL",
            "es_principal": True,
            "activo": True
        }
    ],
    "representante_principal_id": 0,
    "especialidades_oece": [],
    "estado_sunat": "",
    "estado_osce": "",
    "fuentes_consultadas": []
}

print("   Probando con formato más completo sin fechas...")
try:
    response = requests.post(
        BACKEND_URL,
        json=test_data_no_dates,
        headers={'Content-Type': 'application/json'},
        timeout=30
    )

    print(f"   Status Code: {response.status_code}")
    if response.status_code != 200:
        try:
            error_response = response.json()
            print(f"   Error: {json.dumps(error_response, indent=2)}")
        except:
            print(f"   Raw: {response.text[:200]}")

except Exception as e:
    print(f"   Error: {e}")

print("\n" + "="*50)