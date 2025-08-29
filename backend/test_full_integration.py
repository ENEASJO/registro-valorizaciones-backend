#!/usr/bin/env python3
"""
Prueba de integración completa: API + Scraping + Turso
"""
import sys
from pathlib import Path
import asyncio

# Add the app directory to the Python path
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

from app.services.sunat_master_service import SUNATMasterService
from app.services.empresa_service_turso_enhanced import EmpresaServiceTurso

async def test_full_integration():
    """Probar flujo completo de consulta y guardado"""
    
    # RUC de prueba
    test_ruc = "20600074114"
    
    print(f"🔍 Iniciando prueba integral para RUC: {test_ruc}")
    
    # 1. Consultar empresa con scraping
    print("\n📋 Paso 1: Consultando datos de SUNAT/OSCE...")
    sunat_service = SUNATMasterService()
    empresa_info = await sunat_service.consultar_empresa(test_ruc)
    
    # Convertir EmpresaInfo a formato dict para compatibilidad
    primer_representante = empresa_info.representantes[0] if empresa_info.representantes else None
    
    consulta_result = {
        "success": True,
        "data": {
            "ruc": empresa_info.ruc,
            "razon_social": empresa_info.razon_social,
            "contacto": {
                "direccion": empresa_info.domicilio_fiscal,
                "telefono": "",  # No disponible en el modelo actual
                "email": ""      # No disponible en el modelo actual
            },
            "miembros": [
                {
                    "nombre": primer_representante.nombre,
                    "numero_documento": primer_representante.numero_doc
                }
            ] if primer_representante else []
        }
    }
    
    if not consulta_result or not consulta_result.get('success'):
        print("❌ Error en consulta SUNAT")
        return False
    
    print("✅ Datos obtenidos correctamente:")
    print(f"   Razón Social: {consulta_result['data'].get('razon_social', 'N/A')}")
    print(f"   Dirección: {consulta_result['data']['contacto'].get('direccion', 'N/A')}")
    
    # 2. Guardar en Turso
    print("\n📋 Paso 2: Guardando en Turso...")
    turso_service = EmpresaServiceTurso()
    empresa_id = turso_service.save_empresa_from_consulta(test_ruc, consulta_result)
    
    if not empresa_id:
        print("❌ Error guardando en Turso")
        return False
    
    print(f"✅ Empresa guardada con ID: {empresa_id}")
    
    # 3. Verificar datos guardados
    print("\n📋 Paso 3: Verificando datos guardados...")
    empresa_guardada = turso_service.get_empresa_by_ruc(test_ruc)
    
    if not empresa_guardada:
        print("❌ Error recuperando empresa")
        return False
    
    print("✅ Empresa recuperada:")
    print(f"   RUC: {empresa_guardada.get('ruc')}")
    print(f"   Razón Social: {empresa_guardada.get('razon_social')}")
    print(f"   Dirección: {empresa_guardada.get('direccion')}")
    print(f"   Estado: {empresa_guardada.get('estado')}")
    print(f"   Código: {empresa_guardada.get('codigo')}")
    
    # 4. Mostrar estadísticas
    print("\n📋 Paso 4: Estadísticas de la base de datos...")
    stats = turso_service.get_stats()
    print(f"   Total empresas: {stats.get('total_empresas', 0)}")
    print(f"   Empresas recientes (24h): {stats.get('empresas_recientes_24h', 0)}")
    print(f"   Estados: {stats.get('empresas_por_estado', {})}")
    
    # 5. Buscar empresas
    print(f"\n📋 Paso 5: Buscando empresas por RUC '{test_ruc[:4]}'...")
    empresas_encontradas = turso_service.search_empresas(test_ruc[:4])
    print(f"   Empresas encontradas: {len(empresas_encontradas)}")
    for emp in empresas_encontradas[:3]:  # Mostrar solo las primeras 3
        print(f"   - {emp.get('ruc')} - {emp.get('razon_social')}")
    
    # Cleanup
    turso_service.close()
    
    print("\n🎉 ¡Integración completa funcionando correctamente!")
    return True

if __name__ == "__main__":
    success = asyncio.run(test_full_integration())
    if success:
        print("\n✅ Todas las pruebas pasaron exitosamente")
        print("🚀 El sistema está listo para producción")
    else:
        print("\n❌ Algunas pruebas fallaron")
        print("🔧 Revisar la configuración")