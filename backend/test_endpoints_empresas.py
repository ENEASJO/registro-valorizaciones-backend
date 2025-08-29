#!/usr/bin/env python3
"""
Probar los nuevos endpoints de empresas guardadas
"""
import asyncio
import sys
from pathlib import Path

# Add the app directory to the Python path
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

async def test_endpoints_empresas():
    """Probar todos los endpoints de empresas guardadas"""
    
    print(f"🧪 Probando endpoints de empresas guardadas")
    
    try:
        # Importar funciones de endpoints directamente
        from main import (
            listar_empresas_guardadas,
            buscar_empresas_guardadas,
            obtener_empresa_guardada,
            estadisticas_empresas_guardadas
        )
        
        print(f"\n✅ Endpoints importados exitosamente")
        
        # 1. Probar listado de empresas
        print(f"\n📋 1. Probando listado de empresas...")
        resultado = await listar_empresas_guardadas()
        
        if resultado.get("success"):
            empresas = resultado.get("empresas", [])
            print(f"   ✅ Total empresas: {len(empresas)}")
            print(f"   📊 Paginación: {resultado.get('pagination', {})}")
            
            if empresas:
                print(f"   📋 Primera empresa:")
                primera = empresas[0]
                print(f"      RUC: {primera.get('ruc')}")
                print(f"      Razón Social: {primera.get('razon_social', 'N/A')[:50]}...")
        else:
            print(f"   ❌ Error en listado: {resultado.get('message')}")
        
        # 2. Probar búsqueda
        print(f"\n🔍 2. Probando búsqueda de empresas...")
        resultado_busqueda = await buscar_empresas_guardadas("SUPERMER")
        
        if resultado_busqueda.get("success"):
            encontradas = resultado_busqueda.get("empresas", [])
            print(f"   ✅ Empresas encontradas: {len(encontradas)}")
            print(f"   🔍 Query: {resultado_busqueda.get('query')}")
            
            if encontradas:
                print(f"   📋 Primera coincidencia:")
                print(f"      RUC: {encontradas[0].get('ruc')}")
                print(f"      Razón Social: {encontradas[0].get('razon_social', 'N/A')}")
        else:
            print(f"   ❌ Error en búsqueda: {resultado_busqueda.get('message')}")
            
        # 3. Probar obtención de empresa específica
        test_ruc = "20100070970"  # RUC que guardamos anteriormente
        print(f"\n👤 3. Probando obtención empresa específica ({test_ruc})...")
        resultado_empresa = await obtener_empresa_guardada(test_ruc)
        
        if resultado_empresa.get("success"):
            empresa = resultado_empresa.get("data")
            print(f"   ✅ Empresa encontrada:")
            print(f"      RUC: {empresa.get('ruc')}")
            print(f"      Razón Social: {empresa.get('razon_social', 'N/A')}")
            print(f"      Estado: {empresa.get('estado')}")
            print(f"      Código: {empresa.get('codigo')}")
        else:
            print(f"   ❌ Empresa no encontrada: {resultado_empresa.get('message')}")
            
        # 4. Probar estadísticas
        print(f"\n📊 4. Probando estadísticas...")
        resultado_stats = await estadisticas_empresas_guardadas()
        
        if resultado_stats.get("success"):
            stats = resultado_stats.get("stats", {})
            print(f"   ✅ Estadísticas obtenidas:")
            print(f"      Total empresas: {stats.get('total_empresas', 0)}")
            print(f"      Recientes 24h: {stats.get('empresas_recientes_24h', 0)}")
            print(f"      Por estado: {stats.get('empresas_por_estado', {})}")
        else:
            print(f"   ❌ Error en estadísticas: {resultado_stats.get('message')}")
            
        print(f"\n🎉 ¡Todas las pruebas completadas!")
        return True
        
    except Exception as e:
        print(f"❌ Error en pruebas: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_endpoints_empresas())
    if success:
        print(f"\n✅ Todos los endpoints funcionan correctamente")
        print(f"🚀 Los endpoints están listos para el frontend")
    else:
        print(f"\n❌ Algunas pruebas fallaron")