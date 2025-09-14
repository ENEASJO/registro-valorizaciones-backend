#!/usr/bin/env python3
"""
Script de prueba para verificar los endpoints de categorización de empresas
"""
import asyncio
import sys
import os

# Añadir el directorio raíz al path para importar módulos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.empresa_service_neon import empresa_service_neon

async def test_category_filtering():
    """Probar el filtrado por categorías"""
    print("🧪 Iniciando pruebas de filtrado por categorías")
    
    # Obtener todas las empresas
    print("\n1. Obteniendo todas las empresas:")
    todas_empresas = empresa_service_neon.listar_empresas(limit=10)
    print(f"   Total empresas: {len(todas_empresas)}")
    
    for empresa in todas_empresas:
        print(f"   - {empresa.get('razon_social')} (RUC: {empresa.get('ruc')}) - Categoría: {empresa.get('categoria_contratista', 'Sin categoría')}")
    
    # Filtrar ejecutoras
    print("\n2. Filtrando empresas EJECUTORAS:")
    ejecutoras = [emp for emp in todas_empresas if emp.get('categoria_contratista') == 'EJECUTORA']
    print(f"   Total ejecutoras: {len(ejecutoras)}")
    
    for empresa in ejecutoras:
        print(f"   ✅ {empresa.get('razon_social')} (RUC: {empresa.get('ruc')})")
    
    # Filtrar supervisoras
    print("\n3. Filtrando empresas SUPERVISORAS:")
    supervisoras = [emp for emp in todas_empresas if emp.get('categoria_contratista') == 'SUPERVISORA']
    print(f"   Total supervisoras: {len(supervisoras)}")
    
    for empresa in supervisoras:
        print(f"   ✅ {empresa.get('razon_social')} (RUC: {empresa.get('ruc')})")
    
    # Empresas sin categoría
    print("\n4. Empresas sin categoría:")
    sin_categoria = [emp for emp in todas_empresas if not emp.get('categoria_contratista')]
    print(f"   Total sin categoría: {len(sin_categoria)}")
    
    for empresa in sin_categoria:
        print(f"   ⚠️ {empresa.get('razon_social')} (RUC: {empresa.get('ruc')})")
    
    print("\n✅ Pruebas completadas")
    
    # Resumen
    print(f"\n📊 RESUMEN:")
    print(f"   Total empresas: {len(todas_empresas)}")
    print(f"   Ejecutoras: {len(ejecutoras)}")
    print(f"   Supervisoras: {len(supervisoras)}")
    print(f"   Sin categoría: {len(sin_categoria)}")
    
    # Verificar que no hay duplicación
    if len(ejecutoras) + len(supervisoras) + len(sin_categoria) == len(todas_empresas):
        print("   ✅ Las categorías están correctamente separadas")
    else:
        print("   ❌ Error: Las categorías se superponen o faltan empresas")

if __name__ == "__main__":
    asyncio.run(test_category_filtering())