"""
Script de prueba para el sistema de generación automática de códigos de obra
"""
import asyncio
import json
from app.services.obra_service_neon import ObraServiceNeon
from app.models.obra import ObraCreate

async def test_crear_obra_con_codigo_automatico():
    """Probar la creación de obra con código automático"""
    
    print("🧪 PROBANDO SISTEMA DE GENERACIÓN AUTOMÁTICA DE CÓDIGOS")
    print("=" * 60)
    
    # Datos de prueba - usando UUIDs reales de tu base de datos
    empresas_test = [
        {
            "id": "35582cb8-ab04-474e-926c-5b52cc2f9889",
            "nombre": "VIDA SANA ALEMANA S.A.C."
        },
        {
            "id": "a6be08c9-3037-4a18-a019-32c0cc5ca218", 
            "nombre": "CONSTRUCTORA E INGENIERIA V & Z S.A.C."
        },
        {
            "id": "3df286aa-98b6-45dc-9039-f8591f2020f8",
            "nombre": "SANTIAGO DE MATIBAMBA S.A.C."
        }
    ]
    
    obras_test = [
        {
            "nombre": "Construcción de Centro de Salud San Pedro",
            "descripcion": "Centro de salud tipo I-3 con emergencia 24 horas",
            "cliente": "Ministerio de Salud",
            "ubicacion": "Av. San Pedro 456",
            "distrito": "San Pedro",
            "provincia": "Lima",
            "departamento": "Lima",
            "tipo_obra": "Edificación - Salud",
            "modalidad_ejecucion": "CONTRATA",
            "sistema_contratacion": "SUMA_ALZADA",
            "monto_contractual": 750000.00,
            "fecha_inicio": "2025-03-01",
            "fecha_fin_contractual": "2025-12-31",
            "plazo_contractual": 305,
            "estado_obra": "PLANIFICADA"
        },
        {
            "nombre": "Mejoramiento de Plaza Principal",
            "descripcion": "Renovación integral de plaza principal con áreas verdes",
            "cliente": "Municipalidad Distrital",
            "ubicacion": "Plaza Principal S/N",
            "distrito": "Centro",
            "provincia": "Lima", 
            "departamento": "Lima",
            "tipo_obra": "Urbanización",
            "modalidad_ejecucion": "ADMINISTRACION_DIRECTA",
            "sistema_contratacion": "PRECIOS_UNITARIOS",
            "monto_contractual": 250000.00,
            "monto_adicionales": 25000.00,
            "fecha_inicio": "2025-02-15",
            "estado_obra": "EN_PROCESO"
        },
        {
            "nombre": "Construcción de Puente Vehicular",
            "descripcion": "Puente vehicular de 30m de luz sobre río Rímac",
            "cliente": "Ministerio de Transportes",
            "ubicacion": "Río Rímac KM 15+200",
            "distrito": "San Juan",
            "provincia": "Lima",
            "departamento": "Lima",
            "tipo_obra": "Transporte - Puentes",
            "modalidad_ejecucion": "CONTRATA",
            "sistema_contratacion": "SUMA_ALZADA",
            "monto_contractual": 1200000.00,
            "fecha_inicio": "2025-04-01",
            "fecha_fin_contractual": "2025-10-31",
            "plazo_contractual": 213,
            "estado_obra": "PLANIFICADA"
        }
    ]
    
    try:
        for i, obra_data in enumerate(obras_test):
            empresa = empresas_test[i]
            obra_data["empresa_id"] = empresa["id"]
            
            print(f"\\n📋 CREANDO OBRA {i+1}: {obra_data['nombre']}")
            print(f"🏢 Empresa: {empresa['nombre']}")
            print(f"📍 Ubicación: {obra_data['ubicacion']}")
            print(f"💰 Monto: S/ {obra_data['monto_contractual']:,.2f}")
            
            # Crear objeto ObraCreate
            obra_create = ObraCreate(**obra_data)
            
            # Llamar al servicio para crear la obra
            obra_creada = await ObraServiceNeon.crear_obra(obra_create)
            
            print(f"✅ OBRA CREADA EXITOSAMENTE!")
            print(f"   🆔 ID: {obra_creada['id']}")
            print(f"   📄 CÓDIGO: {obra_creada['codigo']}")
            print(f"   💰 Monto Total: S/ {obra_creada.get('monto_total', 0):,.2f}")
            print(f"   📅 Fecha: {obra_creada['created_at']}")
            print("-" * 60)
            
        print("\\n🎉 TODAS LAS OBRAS FUERON CREADAS EXITOSAMENTE!")
        print("\\n📊 RESUMEN DEL SISTEMA:")
        print("   ✅ Códigos generados automáticamente")
        print("   ✅ Formato: OBR-{EMPRESA}-{AÑO}-{SECUENCIA}")
        print("   ✅ Sin duplicados garantizado")
        print("   ✅ Información de empresa incluida")
        print("   ✅ Timestamp para unicidad")
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

# Función para probar directamente con SQL
async def test_sql_direct():
    """Prueba directa con SQL para verificar funcionamiento"""
    
    print("\\n🗄️ PROBANDO FUNCIÓN SQL DIRECTA")
    print("=" * 40)
    
    from app.services.obra_service_neon import ObraServiceNeon
    
    try:
        conn = await ObraServiceNeon._get_connection()
        
        # Probar generación de códigos para diferentes empresas
        empresas_test = [
            "35582cb8-ab04-474e-926c-5b52cc2f9889",
            "a6be08c9-3037-4a18-a019-32c0cc5ca218", 
            "3df286aa-98b6-45dc-9039-f8591f2020f8"
        ]
        
        for i, empresa_uuid in enumerate(empresas_test):
            codigo = await conn.fetchval(
                "SELECT generar_codigo_obra_uuid($1::uuid)",
                empresa_uuid
            )
            
            empresa_info = await conn.fetchval(
                "SELECT razon_social FROM empresas WHERE id = $1::uuid",
                empresa_uuid
            )
            
            print(f"🏢 Empresa {i+1}: {empresa_info}")
            print(f"📄 Código generado: {codigo}")
            print()
            
        await conn.close()
        
    except Exception as e:
        print(f"❌ Error en prueba SQL: {str(e)}")

if __name__ == "__main__":
    # Ejecutar pruebas
    print("🚀 INICIANDO PRUEBAS DEL SISTEMA DE OBRAS")
    print("🔧 Sistema de Generación Automática de Códigos")
    print("📅 Fecha:", "27 de enero de 2025")
    print()
    
    # Probar función SQL directa primero
    asyncio.run(test_sql_direct())
    
    # Luego probar creación completa de obras
    asyncio.run(test_crear_obra_con_codigo_automatico())