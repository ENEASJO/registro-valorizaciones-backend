#!/usr/bin/env python3
"""
Debug directo de la respuesta HTTP de Turso
"""
import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

def debug_http_response():
    """Investigar respuesta HTTP directa"""
    
    url = os.getenv("TURSO_DATABASE_URL")
    token = os.getenv("TURSO_AUTH_TOKEN")
    
    http_url = url.replace("libsql://", "https://")
    api_url = f"{http_url}/v1/execute"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Test simple SELECT
    payload = {
        "stmt": "SELECT COUNT(*) FROM empresas"
    }
    
    print(f"🔗 Enviando a: {api_url}")
    print(f"📋 Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=30)
        
        print(f"Status: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        print(f"Response text: {response.text}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"JSON parsed: {json.dumps(data, indent=2)}")
            except:
                print("No se pudo parsear JSON")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_http_response()