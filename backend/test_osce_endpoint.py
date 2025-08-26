#!/usr/bin/env python3
"""
Test script para verificar que el endpoint OSCE funciona correctamente
"""
import asyncio
import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_osce_legacy_endpoint():
    """Test del endpoint legacy de OSCE"""
    print("🧪 Probando endpoint OSCE legacy...")
    
    try:
        # Importar la función del endpoint
        from main_restored import consultar_osce_legacy
        
        # RUC de prueba (empresa conocida)
        test_ruc = "20100070970"  # Ejemplo de RUC de empresa
        
        print(f"🔍 Consultando RUC: {test_ruc}")
        
        # Ejecutar la consulta
        result = await consultar_osce_legacy(test_ruc)
        
        print(f"📋 Resultado:")
        print(f"  Error: {result.get('error', 'N/A')}")
        print(f"  RUC: {result.get('ruc', 'N/A')}")
        print(f"  Fuente: {result.get('fuente', 'N/A')}")
        print(f"  Estado: {result.get('status', 'N/A')}")
        
        if not result.get('error'):
            print(f"  Razón Social: {result.get('razon_social', 'N/A')}")
            print(f"  Estado Registro: {result.get('estado', 'N/A')}")
            print(f"  Teléfono: {result.get('telefono', 'N/A')}")
            print(f"  Email: {result.get('email', 'N/A')}")
            print(f"  Especialidades: {len(result.get('especialidades', []))}")
            print(f"  Integrantes: {result.get('integrantes', 0)}")
        
        return result
        
    except ImportError as e:
        print(f"❌ Error de importación: {e}")
        return {"error": True, "message": f"Error de importación: {e}"}
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return {"error": True, "message": f"Error inesperado: {e}"}

async def test_osce_service_directly():
    """Test directo del servicio OSCE"""
    print("🧪 Probando servicio OSCE directamente...")
    
    try:
        from app.services.osce_service import osce_service
        
        test_ruc = "20100070970"
        print(f"🔍 Consultando RUC directo: {test_ruc}")
        
        result = await osce_service.consultar_empresa(test_ruc)
        
        print(f"📋 Resultado directo:")
        print(f"  RUC: {result.ruc}")
        print(f"  Razón Social: {result.razon_social}")
        print(f"  Estado: {result.estado_registro}")
        print(f"  Teléfono: {result.telefono}")
        print(f"  Email: {result.email}")
        print(f"  Especialidades: {len(result.especialidades) if result.especialidades else 0}")
        print(f"  Integrantes: {len(result.integrantes) if result.integrantes else 0}")
        
        return result
        
    except ImportError as e:
        print(f"❌ Error de importación: {e}")
        return None
    except Exception as e:
        print(f"❌ Error en servicio: {e}")
        return None

async def main():
    """Función principal"""
    print("🚀 Iniciando tests de OSCE...")
    
    print("\n" + "="*50)
    print("TEST 1: Endpoint Legacy")
    print("="*50)
    legacy_result = await test_osce_legacy_endpoint()
    
    print("\n" + "="*50)
    print("TEST 2: Servicio Directo")
    print("="*50)
    direct_result = await test_osce_service_directly()
    
    print("\n" + "="*50)
    print("RESUMEN")
    print("="*50)
    print(f"Legacy endpoint: {'✅ OK' if not legacy_result.get('error') else '❌ ERROR'}")
    print(f"Servicio directo: {'✅ OK' if direct_result else '❌ ERROR'}")
    
    if legacy_result.get('error'):
        print(f"Error legacy: {legacy_result.get('message')}")
    
    print("\n🎯 Tests completados!")

if __name__ == "__main__":
    asyncio.run(main())