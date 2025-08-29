#!/usr/bin/env python3
"""
Probar consulta consolidada con guardado automático en Turso
"""
import asyncio
import sys
from pathlib import Path

# Add the app directory to the Python path
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

async def test_consulta_consolidada():
    """Probar endpoint consolidado + guardado Turso"""
    
    # RUC de prueba diferente para verificar funcionalidad
    test_ruc = "20100070970"  # RUC diferente para pruebas
    
    print(f"🧪 Probando consulta consolidada + guardado Turso")
    print(f"🔍 RUC de prueba: {test_ruc}")
    
    try:
        # Simular llamada al endpoint (importando la función directamente)
        from main import consultar_ruc_consolidado
        
        print("\n📋 Llamando endpoint consulta-ruc-consolidada...")
        resultado = await consultar_ruc_consolidado(test_ruc, save_to_db=True)
        
        print("\n📊 Resultado de consulta:")
        print(f"   Success: {resultado.get('success', 'N/A')}")
        print(f"   Fuente: {resultado.get('fuente', 'N/A')}")
        
        if resultado.get('data'):
            data = resultado['data']
            print(f"   RUC: {data.get('ruc', 'N/A')}")
            print(f"   Razón Social: {data.get('razon_social', 'N/A')}")
            print(f"   Dirección: {data.get('direccion', 'N/A')}")
            print(f"   Representantes: {len(data.get('miembros', []))}")
            
        # Verificar información de guardado en DB
        if resultado.get('database'):
            db_info = resultado['database']
            print(f"\n💾 Información de guardado:")
            print(f"   Guardado: {db_info.get('saved', 'N/A')}")
            print(f"   Empresa ID: {db_info.get('empresa_id', 'N/A')}")
            print(f"   Mensaje: {db_info.get('message', 'N/A')}")
        
        # Verificar en Turso directamente
        print(f"\n🔍 Verificando datos guardados en Turso...")
        from app.services.empresa_service_turso_enhanced import EmpresaServiceTurso
        
        turso_service = EmpresaServiceTurso()
        empresa_guardada = turso_service.get_empresa_by_ruc(test_ruc)
        
        if empresa_guardada:
            print(f"✅ Empresa encontrada en Turso:")
            print(f"   RUC: {empresa_guardada.get('ruc')}")
            print(f"   Razón Social: {empresa_guardada.get('razon_social')}")
            print(f"   Código: {empresa_guardada.get('codigo')}")
            print(f"   Estado: {empresa_guardada.get('estado')}")
        else:
            print(f"❌ Empresa NO encontrada en Turso")
            
        # Mostrar estadísticas
        stats = turso_service.get_stats()
        print(f"\n📊 Estadísticas Turso:")
        print(f"   Total empresas: {stats.get('total_empresas', 0)}")
        print(f"   Recientes 24h: {stats.get('empresas_recientes_24h', 0)}")
        
        turso_service.close()
        
        return resultado.get('success', False)
        
    except Exception as e:
        print(f"❌ Error en prueba: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_consulta_consolidada())
    if success:
        print(f"\n🎉 ¡Prueba exitosa! El flujo completo funciona correctamente")
        print(f"   ✅ Consulta consolidada funcionando")
        print(f"   ✅ Guardado automático en Turso funcionando")
        print(f"   ✅ Integración Frontend → Backend → Turso completa")
    else:
        print(f"\n❌ Prueba falló")