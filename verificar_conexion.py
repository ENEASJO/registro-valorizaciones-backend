#!/usr/bin/env python3
"""
Script para verificar la conexión y mostrar información detallada
"""

import requests
import json

BACKEND_URL = "https://registro-valorizaciones-backend-503600768755.southamerica-west1.run.app"

print("=== VERIFICACIÓN DETALLADA DE CONEXIÓN ===\n")

# 1. Verificar endpoint normal
print("1. Probando endpoint /api/empresas/")
try:
    response = requests.get(f"{BACKEND_URL}/api/empresas/", timeout=10)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Total empresas: {data['data']['total']}")
    else:
        print(f"   Error: {response.text[:200]}")
except Exception as e:
    print(f"   Error: {e}")

# 2. Verificar endpoint de debug
print("\n2. Probando endpoint /api/empresas/debug/connection")
try:
    response = requests.get(f"{BACKEND_URL}/api/empresas/debug/connection", timeout=10)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print("   ✅ Conexión exitosa")
        if 'data' in data and 'connection_string' in data['data']:
            conn_str = data['data']['connection_string']
            print(f"   Connection string: {conn_str}")
            # Verificar si está truncada
            if conn_str.endswith('.aw'):
                print("   ❌ LA CONEXIÓN ESTÁ TRUNCADA")
            elif conn_str.endswith('.neon.tech'):
                print("   ✅ La conexión parece completa")
    else:
        data = response.json()
        print(f"   ❌ Error: {data.get('error', 'Unknown error')}")
except Exception as e:
    print(f"   Error: {e}")

# 3. Probar conexión directa a Neon
print("\n3. Probando conexión directa a Neon (para comparar)")
import psycopg2
from psycopg2.extras import RealDictCursor

# Probar con hostname largo
print("   a) Probando hostname largo...")
try:
    conn_str_largo = "postgresql://neondb_owner:npg_puYoPelF96Hd@ep-fancy-river-acd46jxk-pooler.sa-east-1.aws.neon.tech/neondb?sslmode=require"
    conn = psycopg2.connect(conn_str_largo, cursor_factory=RealDictCursor)
    with conn.cursor() as cursor:
        cursor.execute("SELECT 1 as test;")
        result = cursor.fetchone()
        print(f"   ✅ Hostname largo funciona: {result}")
    conn.close()
except Exception as e:
    print(f"   ❌ Hostname largo falla: {e}")

# Probar con hostname corto
print("   b) Probando hostname corto...")
try:
    conn_str_corto = "postgresql://neondb_owner:npg_puYoPelF96Hd@ep-fancy-river-acd46jxk.sa-east-1.aws.neon.tech/neondb?sslmode=require"
    conn = psycopg2.connect(conn_str_corto, cursor_factory=RealDictCursor)
    with conn.cursor() as cursor:
        cursor.execute("SELECT 1 as test;")
        result = cursor.fetchone()
        print(f"   ✅ Hostname corto funciona: {result}")
    conn.close()
except Exception as e:
    print(f"   ❌ Hostname corto falla: {e}")

print("\n=== CONCLUSIÓN ===")
print("Si ambos hostnames funcionan localmente pero no en Cloud Run,")
print("el problema podría ser:")
print("- La variable de entorno en Cloud Run está mal configurada")
print("- Hay un firewall o restricción de red")
print("- El problema está en el código que lee la variable de entorno")