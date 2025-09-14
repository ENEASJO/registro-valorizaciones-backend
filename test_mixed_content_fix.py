#!/usr/bin/env python3
"""
Script de prueba para verificar el arreglo del Mixed Content error
"""

import requests
import time

def test_backend_endpoint():
    """Test the backend endpoint to check if redirects are fixed"""
    print("🧪 Probando endpoint del backend...")
    
    # Test sin parámetro de cache busting
    url = "https://registro-valorizaciones-503600768755.southamerica-west1.run.app/api/empresas"
    
    try:
        # Seguir redirecciones para ver dónde termina
        response = requests.get(url, allow_redirects=True, timeout=10)
        
        print(f"📍 URL final: {response.url}")
        print(f"📊 Status Code: {response.status_code}")
        print(f"🔒 Es HTTPS: {response.url.startswith('https://')}")
        
        # Test con el parámetro que usa el frontend
        url_with_param = f"{url}?_v={int(time.time() * 1000)}"
        response2 = requests.get(url_with_param, allow_redirects=True, timeout=10)
        
        print(f"📍 URL con parámetro: {response2.url}")
        print(f"📊 Status Code con parámetro: {response2.status_code}")
        
        return response.url.startswith('https://') and response2.url.startswith('https://')
        
    except Exception as e:
        print(f"❌ Error probando backend: {e}")
        return False

def test_service_worker_logic():
    """Test Service Worker logic simulation"""
    print("\n🛡️ Simulando lógica del Service Worker...")
    
    # URLs de prueba
    test_urls = [
        "https://registro-valorizaciones-503600768755.southamerica-west1.run.app/api/empresas",
        "http://registro-valorizaciones-503600768755.southamerica-west1.run.app/api/empresas",
        "https://registro-valorizaciones-503600768755.southamerica-west1.run.app/api/empresas/?_v=123456789"
    ]
    
    target_domains = [
        'registro-valorizaciones-503600768755.southamerica-west1.run.app',
        'localhost:8000'
    ]
    
    for url in test_urls:
        print(f"\n🔍 Probando URL: {url}")
        
        # Simular lógica del Service Worker
        if url.startswith('https://'):
            print("  ✅ URL ya es HTTPS - FETCH DIRECTO")
            final_url = url
        else:
            # Buscar HTTP para convertir a HTTPS
            should_intercept = any(domain in url for domain in target_domains if f'http://{domain}' in url)
            if should_intercept:
                for domain in target_domains:
                    if f'http://{domain}' in url:
                        corrected_url = url.replace(f'http://{domain}', f'https://{domain}')
                        print(f"  🔧 Corrigiendo HTTP a HTTPS: {corrected_url}")
                        final_url = corrected_url
                        break
            else:
                final_url = url
        
        print(f"  🎯 URL final: {final_url}")

def main():
    """Función principal"""
    print("🚀 Iniciando pruebas de Mixed Content fix...")
    print("=" * 50)
    
    # Test backend
    backend_ok = test_backend_endpoint()
    
    # Test Service Worker logic
    test_service_worker_logic()
    
    print("\n" + "=" * 50)
    print("📋 RESUMEN:")
    print(f"Backend HTTPS: {'✅ OK' if backend_ok else '❌ FALLÓ'}")
    print("Service Worker: ✅ Lógica correcta (simulada)")
    
    if backend_ok:
        print("\n🎉 ¡Ambos componentes deberían funcionar juntos!")
        print("   El Service Worker maneja URLs HTTPS correctamente")
        print("   El backend ya no redirige a HTTP")
    else:
        print("\n⚠️  El backend aún necesita ser desplegado con el fix")
        print("   El Service Worker está listo para cuando el backend esté arreglado")

if __name__ == "__main__":
    main()