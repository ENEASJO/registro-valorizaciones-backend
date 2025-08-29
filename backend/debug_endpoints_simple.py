#!/usr/bin/env python3
"""
Debug simple de endpoints
"""
import sys
from pathlib import Path

# Add the app directory to the Python path
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

from app.services.empresa_service_turso_enhanced import EmpresaServiceTurso

def debug_simple():
    """Debug simple del servicio"""
    
    print(f"🔍 Debug simple del servicio")
    
    # Test con UNA sola instancia del servicio
    service = EmpresaServiceTurso()
    
    print(f"\n1. Probando get_stats()...")
    stats = service.get_stats()
    print(f"   Stats: {stats}")
    
    print(f"\n2. Probando list_empresas(limit=2)...")
    empresas = service.list_empresas(limit=2)
    print(f"   Empresas: {len(empresas)}")
    for emp in empresas:
        print(f"      {emp.get('ruc')} - {emp.get('razon_social', 'N/A')}")
        
    print(f"\n3. Probando search_empresas('SUPERMERC')...")
    encontradas = service.search_empresas("SUPERMERC")
    print(f"   Encontradas: {len(encontradas)}")
    for emp in encontradas:
        print(f"      {emp.get('ruc')} - {emp.get('razon_social', 'N/A')}")
        
    print(f"\n4. Probando get_empresa_by_ruc('20100070970')...")
    empresa = service.get_empresa_by_ruc("20100070970")
    if empresa:
        print(f"   Encontrada: {empresa.get('ruc')} - {empresa.get('razon_social', 'N/A')}")
    else:
        print(f"   NO encontrada")
        
    service.close()
    
    # Ahora probemos con INSTANCIAS SEPARADAS (como hacen los endpoints)
    print(f"\n" + "="*60)
    print(f"🔍 AHORA CON INSTANCIAS SEPARADAS (como endpoints)")
    
    print(f"\n1. Stats con nueva instancia...")
    service1 = EmpresaServiceTurso()
    stats = service1.get_stats()
    print(f"   Stats: {stats}")
    service1.close()
    
    print(f"\n2. List con nueva instancia...")
    service2 = EmpresaServiceTurso()
    empresas = service2.list_empresas(limit=2)
    print(f"   Empresas: {len(empresas)}")
    service2.close()
    
    print(f"\n3. Get empresa con nueva instancia...")
    service3 = EmpresaServiceTurso()
    empresa = service3.get_empresa_by_ruc("20100070970")
    if empresa:
        print(f"   Encontrada: {empresa.get('ruc')}")
    else:
        print(f"   NO encontrada")
    service3.close()

if __name__ == "__main__":
    debug_simple()