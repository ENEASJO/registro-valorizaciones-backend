#!/usr/bin/env python3
"""
Script para probar conexión HTTP a Turso
"""
import os
import requests
import json
from dotenv import load_dotenv

# Load environment
load_dotenv()

def test_turso_http():
    """Probar conexión HTTP directa a Turso"""
    
    url = os.getenv("TURSO_DATABASE_URL")
    token = os.getenv("TURSO_AUTH_TOKEN")
    
    if not url or not token:
        print("❌ Variables de entorno faltantes")
        return False
    
    # Convertir WebSocket URL a HTTP
    http_url = url.replace("libsql://", "https://").replace(":443", "")
    api_url = f"{http_url}/v1/execute"
    
    print(f"🔗 Probando conexión HTTP: {api_url}")
    
    # Preparar headers
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Test simple SELECT - formato correcto para Turso
    test_payload = {
        "stmt": "SELECT 1 as test"
    }
    
    try:
        print("📊 Ejecutando query de prueba...")
        response = requests.post(api_url, headers=headers, json=test_payload, timeout=10)
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:200]}...")
        
        if response.status_code == 200:
            print("✅ Conexión HTTP exitosa")
            return True
        else:
            print(f"❌ Error HTTP: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_turso_http()
    if success:
        print("✅ HTTP funciona, intentando crear tablas...")
    else:
        print("❌ HTTP también falló")