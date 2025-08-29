#!/usr/bin/env python3
"""
Test directo del servicio Turso enhanced
"""
import sys
from pathlib import Path

# Add the app directory to the Python path
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

from app.services.empresa_service_turso_enhanced import EmpresaServiceTurso

def test_servicio_directo():
    """Probar métodos del servicio directamente"""
    
    print(f"🧪 Probando servicio EmpresaServiceTurso directamente")
    
    service = EmpresaServiceTurso()
    
    # Test 1: get_empresa_by_ruc
    test_ruc = "20100070970"
    print(f"\n🔍 1. Probando get_empresa_by_ruc({test_ruc})...")
    
    try:
        empresa = service.get_empresa_by_ruc(test_ruc)
        if empresa:
            print(f"   ✅ Empresa encontrada:")
            print(f"      RUC: {empresa.get('ruc')}")
            print(f"      Razón Social: {empresa.get('razon_social')}")
            print(f"      Código: {empresa.get('codigo')}")
        else:
            print(f"   ❌ Empresa NO encontrada")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 2: list_empresas
    print(f"\n📋 2. Probando list_empresas...")
    
    try:
        empresas = service.list_empresas(limit=5)
        print(f"   ✅ Empresas obtenidas: {len(empresas)}")
        for i, emp in enumerate(empresas[:3]):
            print(f"      {i+1}. {emp.get('ruc')} - {emp.get('razon_social', 'N/A')[:40]}...")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 3: search_empresas
    print(f"\n🔍 3. Probando search_empresas('SUPERMERC')...")
    
    try:
        empresas = service.search_empresas("SUPERMERC", limit=5)
        print(f"   ✅ Empresas encontradas: {len(empresas)}")
        for emp in empresas:
            print(f"      {emp.get('ruc')} - {emp.get('razon_social', 'N/A')[:40]}...")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 4: get_stats
    print(f"\n📊 4. Probando get_stats...")
    
    try:
        stats = service.get_stats()
        if stats.get('error'):
            print(f"   ❌ Error en stats: {stats.get('error')}")
        else:
            print(f"   ✅ Estadísticas:")
            print(f"      Total empresas: {stats.get('total_empresas')}")
            print(f"      Recientes 24h: {stats.get('empresas_recientes_24h')}")
            print(f"      Por estado: {stats.get('empresas_por_estado')}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    service.close()

if __name__ == "__main__":
    test_servicio_directo()