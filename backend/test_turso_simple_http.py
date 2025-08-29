#!/usr/bin/env python3
"""
Probar Turso con requests HTTP puro usando su API REST
"""
import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

def test_turso_rest():
    """Probar con API REST de Turso"""
    
    url = os.getenv("TURSO_DATABASE_URL") 
    token = os.getenv("TURSO_AUTH_TOKEN")
    
    # Convertir a HTTP API endpoint
    http_url = url.replace("libsql://", "https://")
    
    # Probar diferentes endpoints
    endpoints = [
        f"{http_url}/v1/execute",
        f"{http_url}/v2/pipeline", 
        f"{http_url}/health"
    ]
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    for endpoint in endpoints:
        print(f"\n🔗 Probando: {endpoint}")
        try:
            response = requests.get(endpoint, headers=headers, timeout=5)
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text[:150]}")
            
            if response.status_code < 400:
                print("✅ Endpoint responde")
            else:
                print("❌ Endpoint no responde")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Probar con libsql usando HTTP transport
    print(f"\n🔧 Probando libsql con HTTP...")
    try:
        from libsql_client import create_client_sync
        
        # Forzar HTTP en lugar de WebSocket
        http_client_url = url.replace("libsql://", "https://")
        client = create_client_sync(
            url=http_client_url,
            auth_token=token
        )
        
        result = client.execute("SELECT 1 as test")
        print(f"✅ libsql HTTP funciona: {result.rows}")
        client.close()
        return True
        
    except Exception as e:
        print(f"❌ libsql HTTP falló: {e}")
        return False

if __name__ == "__main__":
    test_turso_rest()