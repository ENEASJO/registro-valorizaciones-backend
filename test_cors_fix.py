#!/usr/bin/env python3
"""
Script para probar el fix de CORS después del reordering de middleware
"""

import requests
import json

def test_cors_endpoint():
    """Test CORS headers on the backend endpoint"""
    print("🧪 Probando CORS en endpoint del backend...")
    
    url = "https://registro-valorizaciones-503600768755.southamerica-west1.run.app/api/empresas"
    
    # Simular una petición desde el frontend (Vercel)
    headers = {
        'Origin': 'https://registro-valorizaciones.vercel.app',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        # Hacer petición OPTIONS (preflight)
        print("🔄 Probando petición OPTIONS (preflight)...")
        options_response = requests.options(url, headers=headers, timeout=10)
        
        print(f"📊 OPTIONS Status: {options_response.status_code}")
        
        # Verificar headers CORS
        cors_headers = {
            'Access-Control-Allow-Origin': options_response.headers.get('Access-Control-Allow-Origin'),
            'Access-Control-Allow-Methods': options_response.headers.get('Access-Control-Allow-Methods'),
            'Access-Control-Allow-Headers': options_response.headers.get('Access-Control-Allow-Headers'),
            'Access-Control-Allow-Credentials': options_response.headers.get('Access-Control-Allow-Credentials')
        }
        
        print("📋 CORS Headers (OPTIONS):")
        for key, value in cors_headers.items():
            print(f"   {key}: {value}")
        
        # Hacer petición GET real
        print("\n🔄 Probando petición GET...")
        get_response = requests.get(url, headers=headers, timeout=10)
        
        print(f"📊 GET Status: {get_response.status_code}")
        
        # Verificar headers CORS en respuesta GET
        get_cors_headers = {
            'Access-Control-Allow-Origin': get_response.headers.get('Access-Control-Allow-Origin'),
            'Access-Control-Allow-Credentials': get_response.headers.get('Access-Control-Allow-Credentials')
        }
        
        print("📋 CORS Headers (GET):")
        for key, value in get_cors_headers.items():
            print(f"   {key}: {value}")
        
        # Verificar si la respuesta es válida
        if get_response.status_code == 200:
            try:
                data = get_response.json()
                print(f"✅ Respuesta JSON válida: {len(data.get('data', []))} empresas encontradas")
            except:
                print("⚠️ Respuesta no es JSON válido")
        
        # Evaluar resultado
        cors_ok = (
            options_response.status_code in [200, 204] and
            get_response.status_code == 200 and
            cors_headers['Access-Control-Allow-Origin'] in ['*', 'https://registro-valorizaciones.vercel.app']
        )
        
        return cors_ok
        
    except Exception as e:
        print(f"❌ Error probando CORS: {e}")
        return False

def test_proxy_headers():
    """Test if proxy headers are working correctly"""
    print("\n🔍 Probando proxy headers...")
    
    url = "https://registro-valorizaciones-503600768755.southamerica-west1.run.app/debug/headers"
    
    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print("📋 Headers del servidor:")
            for key, value in data.items():
                print(f"   {key}: {value}")
            
            # Verificar si el proxy header está presente
            proxy_handled = data.get('x-proxy-handled') == 'true'
            scheme = data.get('scheme', 'http')
            
            print(f"\n🔒 Proxy handled: {proxy_handled}")
            print(f"🔒 Scheme: {scheme}")
            
            return scheme == 'https'
        else:
            print(f"⚠️ Debug endpoint status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error probando debug endpoint: {e}")
        return False

def main():
    """Función principal"""
    print("🚀 Iniciando pruebas de CORS fix...")
    print("=" * 50)
    
    # Test CORS
    cors_ok = test_cors_endpoint()
    
    # Test proxy headers
    proxy_ok = test_proxy_headers()
    
    print("\n" + "=" * 50)
    print("📋 RESUMEN:")
    print(f"CORS: {'✅ OK' if cors_ok else '❌ FALLÓ'}")
    print(f"Proxy Headers: {'✅ OK' if proxy_ok else '❌ FALLÓ'}")
    
    if cors_ok and proxy_ok:
        print("\n🎉 ¡Todo está funcionando correctamente!")
        print("   El frontend debería poder cargar las empresas")
    else:
        print("\n⚠️  Aún hay problemas que necesitan ser resueltos")
        if not cors_ok:
            print("   - El problema de CORS persiste")
        if not proxy_ok:
            print("   - Los proxy headers no están funcionando")

if __name__ == "__main__":
    main()