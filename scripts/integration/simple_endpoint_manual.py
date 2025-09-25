#!/usr/bin/env python3
"""
Script para probar el endpoint con una versión simplificada (integración manual).
Marcado como prueba de integración para excluirlo del CI por defecto.
"""

import pytest
pytestmark = pytest.mark.integration

import requests
import json

BACKEND_URL = "https://registro-valorizaciones-backend-503600768755.southamerica-west1.run.app"

def main():
    print("1. Probando endpoint principal...")
    try:
        response = requests.get(f"{BACKEND_URL}/api/empresas/?limit=100", timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Respuesta: {json.dumps(data, indent=2)}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error de conexión: {e}")

    print("\n2. Probando conexión básica...")
    try:
        response = requests.get(f"{BACKEND_URL}/", timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:200]}")
    except Exception as e:
        print(f"Error: {e}")

    print("\n3. Verificando headers del endpoint...")
    try:
        response = requests.get(f"{BACKEND_URL}/api/empresas/?limit=100", timeout=10)
        print(f"Headers:")
        for key, value in response.headers.items():
            print(f"  {key}: {value}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
