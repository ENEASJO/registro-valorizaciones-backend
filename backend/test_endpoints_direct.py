#!/usr/bin/env python3
"""
Prueba directa de la funcionalidad de endpoints
"""
import requests
import json

BASE_URL = "https://registro-valorizaciones-503600768755.southamerica-west1.run.app"

def test_endpoint(endpoint, description):
    """Probar un endpoint específico"""
    try:
        url = f"{BASE_URL}{endpoint}"
        print(f"\n🧪 Probando: {description}")
        print(f"   URL: {url}")
        
        response = requests.get(url, timeout=10)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and 'empresas' in data['data']:
                empresas = data['data']['empresas']
                print(f"   ✅ Empresas encontradas: {len(empresas)}")
                for empresa in empresas:
                    categoria = empresa.get('categoria_contratista', 'Sin categoría')
                    print(f"      - {empresa['razon_social']} ({categoria})")
            else:
                print(f"   📄 Respuesta: {json.dumps(data, indent=2)}")
        else:
            print(f"   ❌ Error: {response.status_code} - {response.text[:200]}")
            
    except Exception as e:
        print(f"   ❌ Excepción: {str(e)}")

def main():
    print("🚀 Probando endpoints de categorización de empresas")
    
    # Probar endpoints
    test_endpoint("/api/empresas", "Endpoint general de empresas")
    test_endpoint("/api/empresas/ejecutoras", "Endpoint empresas ejecutoras")
    test_endpoint("/api/empresas/supervisoras", "Endpoint empresas supervisoras")
    
    print("\n📊 Pruebas completadas")

if __name__ == "__main__":
    main()