#!/usr/bin/env python3
"""
Script de verificación de importaciones para deployment
Verifica que todas las importaciones críticas funcionen antes del despliegue
"""

import sys
import traceback

def test_import(module_name, description):
    """Probar importación de un módulo"""
    try:
        __import__(module_name)
        print(f"✅ {description}")
        return True
    except ImportError as e:
        print(f"❌ {description}: {e}")
        return False
    except Exception as e:
        print(f"⚠️ {description}: Error inesperado - {e}")
        return False

def verify_critical_imports():
    """Verificar importaciones críticas"""
    print("🔍 Verificando importaciones críticas para deployment...\n")
    
    results = []
    
    # Core modules
    results.append(test_import("app.core.database", "Configuración de base de datos"))
    results.append(test_import("app.core.config", "Configuración de la aplicación"))
    
    # Critical services
    results.append(test_import("app.services.empresa_service_neon", "Servicio de empresas Neon"))
    
    # Main routes
    results.append(test_import("app.api.routes.empresas", "Router principal de empresas"))
    results.append(test_import("app.api.routes.empresas_smart", "Router inteligente de empresas"))
    results.append(test_import("app.api.routes.debug_logs", "Router de debug"))
    
    # Optional routes
    test_import("app.api.routes.ubicaciones", "Router de ubicaciones (opcional)")
    test_import("app.api.routes.debug_empresa", "Router debug empresas (opcional)")
    
    print(f"\n📊 Resultado: {sum(results)} de {len(results)} importaciones críticas exitosas")
    
    return all(results)

def test_specific_functions():
    """Probar funciones específicas que han causado problemas"""
    print("\n🧪 Verificando funciones específicas...\n")
    
    success_count = 0
    total_count = 0
    
    # Test get_database_url
    total_count += 1
    try:
        from app.core.database import get_database_url
        url = get_database_url()
        if url and isinstance(url, str):
            print(f"✅ get_database_url funciona correctamente")
            success_count += 1
        else:
            print(f"⚠️ get_database_url retorna valor inválido: {url}")
    except Exception as e:
        print(f"❌ get_database_url falló: {e}")
    
    # Test empresa_service_neon instance
    total_count += 1
    try:
        from app.services.empresa_service_neon import empresa_service_neon
        if hasattr(empresa_service_neon, 'listar_empresas'):
            print(f"✅ empresa_service_neon instance funciona correctamente")
            success_count += 1
        else:
            print(f"⚠️ empresa_service_neon no tiene método listar_empresas")
    except Exception as e:
        print(f"❌ empresa_service_neon instance falló: {e}")
    
    # Test router creation
    total_count += 1
    try:
        from app.api.routes.empresas_smart import router
        if hasattr(router, 'routes') and len(router.routes) > 0:
            print(f"✅ Router empresas_smart creado correctamente con {len(router.routes)} rutas")
            success_count += 1
        else:
            print(f"⚠️ Router empresas_smart sin rutas")
    except Exception as e:
        print(f"❌ Router empresas_smart falló: {e}")
    
    print(f"\n📊 Funciones específicas: {success_count} de {total_count} exitosas")
    
    return success_count == total_count

def test_main_app():
    """Probar que main.py puede importarse correctamente"""
    print("\n🚀 Verificando main.py...\n")
    
    try:
        # Intentar importar main.py
        import main
        if hasattr(main, 'app'):
            print("✅ main.py importado correctamente")
            print("✅ FastAPI app instance encontrada")
            
            # Verificar routers incluidos
            router_count = len(main.app.routes) if hasattr(main.app, 'routes') else 0
            print(f"📊 Total de rutas registradas: {router_count}")
            
            return True
        else:
            print("⚠️ main.py importado pero no se encontró 'app' instance")
            return False
    except Exception as e:
        print(f"❌ Error importando main.py: {e}")
        print("\n📋 Stack trace completo:")
        traceback.print_exc()
        return False

def main():
    """Función principal"""
    print("="*60)
    print("🛠️  VERIFICACIÓN DE IMPORTACIONES PARA DEPLOYMENT")
    print("="*60)
    
    # Verificar importaciones críticas
    critical_ok = verify_critical_imports()
    
    # Verificar funciones específicas
    functions_ok = test_specific_functions()
    
    # Verificar main.py
    main_ok = test_main_app()
    
    # Resultado final
    print("\n" + "="*60)
    print("📋 RESUMEN FINAL")
    print("="*60)
    
    if critical_ok and functions_ok and main_ok:
        print("🎉 TODAS LAS VERIFICACIONES PASARON")
        print("✅ El deployment debería funcionar correctamente")
        sys.exit(0)
    else:
        print("❌ ALGUNAS VERIFICACIONES FALLARON")
        print("⚠️  Revisar los errores antes del deployment")
        print(f"   - Importaciones críticas: {'✅' if critical_ok else '❌'}")
        print(f"   - Funciones específicas: {'✅' if functions_ok else '❌'}")
        print(f"   - Main.py: {'✅' if main_ok else '❌'}")
        sys.exit(1)

if __name__ == "__main__":
    main()