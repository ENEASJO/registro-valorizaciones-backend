#!/usr/bin/env python3
"""
Script para investigar sistemáticamente el problema
"""

import requests
import json

BACKEND_URL = "https://registro-valorizaciones-backend-503600768755.southamerica-west1.run.app"

print("=== INVESTIGACIÓN SISTEMÁTICA DEL PROBLEMA ===\n")

# 1. Verificar si el endpoint principal funciona
print("1. Probando endpoint /api/empresas/")
try:
    response = requests.get(f"{BACKEND_URL}/api/empresas/", timeout=10)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Total empresas: {data['data']['total']}")
        print(f"   Mensaje: {data['message']}")
    else:
        print(f"   Error: {response.text}")
except Exception as e:
    print(f"   Error: {e}")

# 2. Verificar logs de la aplicación (si hay algún endpoint que los muestre)
print("\n2. No hay forma directa de ver logs, pero podemos inferir...")

# 3. Probar a crear una empresa nueva para ver si funciona
print("\n3. Probando crear una empresa de prueba...")
test_empresa = {
    "ruc": "20555555555",
    "razon_social": "EMPRESA DE PRUEBA INVESTIGACIÓN",
    "tipo_empresa": "SAC",
    "representantes": [
        {
            "nombre": "REPRESENTANTE DE PRUEBA",
            "cargo": "GERENTE",
            "numero_documento": "12345678",
            "tipo_documento": "DNI"
        }
    ],
    "representante_principal_id": 0,
    "categoria_contratista": "EJECUTORA"
}

try:
    response = requests.post(
        f"{BACKEND_URL}/api/empresas/",
        json=test_empresa,
        timeout=30
    )
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        print("   ✅ Empresa creada exitosamente")
        data = response.json()
        print(f"   ID: {data.get('data', {}).get('id', 'No ID')}")
    elif response.status_code == 500:
        print("   ❌ Error 500 - Esto podría indicar problema con la base de datos")
        try:
            error = response.json()
            print(f"   Detalle: {error.get('detail', 'Sin detalle')}")
        except:
            pass
    else:
        print(f"   Respuesta: {response.text[:200]}")
except Exception as e:
    print(f"   Error: {e}")

# 4. Verificar si el problema es de permisos o conexión
print("\n4. El problema podría ser:")
print("   a) La conexión a Neon no funciona desde el entorno desplegado")
print("   b) Las empresas existen pero no se pueden leer por algún filtro")
print("   c) Hay un error en el código que solo se manifiesta en producción")
print("   d) Las variables de entorno son diferentes en producción")

# 5. Verificar la estructura real del proyecto
print("\n5. Estructura del proyecto:")
print("   - main.py (usa empresas_simple)")
print("   - app/api/routes/empresas_simple.py")
print("   - app/api/routes/empresas.py")
print("   - backend/ (directorio duplicado?)")

print("\n=== ANÁLISIS ===")
print("Como no podemos ver los logs directamente, necesitamos:")
print("1. Probar diferentes endpoints para ver cuál funciona")
print("2. Intentar crear una empresa para ver si el problema es solo de lectura")
print("3. Verificar si hay patrones en los errores")