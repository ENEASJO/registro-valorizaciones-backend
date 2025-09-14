#!/usr/bin/env python3
"""
Prueba de filtrado por categoría usando parámetro query
"""
import requests
import json

BASE_URL = "https://registro-valorizaciones-503600768755.southamerica-west1.run.app"

def test_category_filter(categoria, descripcion):
    """Probar filtrado por categoría específica"""
    try:
        url = f"{BASE_URL}/api/empresas?categoria={categoria}"
        print(f"\n🧪 Probando: {descripcion}")
        print(f"   URL: {url}")
        
        response = requests.get(url, timeout=10)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and isinstance(data['data'], list):
                # Formato anterior (array directo)
                empresas = data['data']
                print(f"   ✅ Empresas encontradas: {len(empresas)}")
                for empresa in empresas:
                    categoria_emp = empresa.get('categoria_contratista', 'Sin categoría')
                    print(f"      - {empresa['razon_social']} ({categoria_emp})")
                    
                    # Verificar que todas las empresas tienen la categoría correcta
                    if categoria and categoria_emp.upper() != categoria.upper():
                        print(f"      ❌ ERROR: Se esperaba {categoria} pero se encontró {categoria_emp}")
                        
            elif 'data' in data and 'empresas' in data['data']:
                # Formato nuevo (objeto con estructura)
                empresas = data['data']['empresas']
                print(f"   ✅ Empresas encontradas: {len(empresas)}")
                for empresa in empresas:
                    categoria_emp = empresa.get('categoria_contratista', 'Sin categoría')
                    print(f"      - {empresa['razon_social']} ({categoria_emp})")
                    
                    # Verificar que todas las empresas tienen la categoría correcta
                    if categoria and categoria_emp.upper() != categoria.upper():
                        print(f"      ❌ ERROR: Se esperaba {categoria} pero se encontró {categoria_emp}")
            else:
                print(f"   📄 Respuesta inesperada: {json.dumps(data, indent=2)}")
        else:
            print(f"   ❌ Error: {response.status_code} - {response.text[:200]}")
            
    except Exception as e:
        print(f"   ❌ Excepción: {str(e)}")

def main():
    print("🚀 Probando filtrado de empresas por categoría usando query parameter")
    
    # Probar diferentes filtros
    test_category_filter("", "Todas las empresas (sin filtro)")
    test_category_filter("EJECUTORA", "Solo empresas ejecutoras")
    test_category_filter("SUPERVISORA", "Solo empresas supervisoras")
    test_category_filter("INVALID", "Categoría inválida (debería mostrar todas)")
    
    print(f"\n💡 Para usar en frontend:")
    print(f"   - Ejecutoras: {BASE_URL}/api/empresas?categoria=EJECUTORA")
    print(f"   - Supervisoras: {BASE_URL}/api/empresas?categoria=SUPERVISORA")
    print(f"   - Todas: {BASE_URL}/api/empresas")
    
    print("\n📊 Pruebas completadas")

if __name__ == "__main__":
    main()