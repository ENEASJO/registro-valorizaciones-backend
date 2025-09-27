#!/usr/bin/env python3
"""
🧪 Test rápido del fix de SQLAlchemy - extend_existing
Verifica que las tablas puedan importarse múltiples veces sin error
"""

import os
import sys
from datetime import datetime

def test_multiple_imports():
    """Test que las tablas puedan importarse múltiples veces"""
    print("🧪 PRUEBA: Importación múltiple de modelos SQLAlchemy")
    print("="*60)
    
    try:
        print("1️⃣ Primera importación de modelos...")
        from app.models.empresa import EmpresaDB, RepresentanteDB
        from app.models.ubicacion import UbicacionDB
        print("   ✅ Primera importación exitosa")
        
        print("2️⃣ Segunda importación de modelos (simulando routers múltiples)...")
        # Simular lo que pasa cuando múltiples routers importan los mismos modelos
        from app.models.empresa import EmpresaDB as EmpresaDB2, RepresentanteDB as RepresentanteDB2
        from app.models.ubicacion import UbicacionDB as UbicacionDB2
        print("   ✅ Segunda importación exitosa")
        
        print("3️⃣ Verificando que las clases son las mismas...")
        assert EmpresaDB is EmpresaDB2, "EmpresaDB debe ser la misma clase"
        assert RepresentanteDB is RepresentanteDB2, "RepresentanteDB debe ser la misma clase"
        assert UbicacionDB is UbicacionDB2, "UbicacionDB debe ser la misma clase"
        print("   ✅ Las clases son consistentes")
        
        print("4️⃣ Verificando configuración extend_existing...")
        assert hasattr(EmpresaDB, '__table_args__'), "EmpresaDB debe tener __table_args__"
        assert hasattr(RepresentanteDB, '__table_args__'), "RepresentanteDB debe tener __table_args__"
        
        # Verificar que extend_existing esté configurado
        empresas_args = EmpresaDB.__table_args__
        representantes_args = RepresentanteDB.__table_args__
        
        if isinstance(empresas_args, dict):
            assert empresas_args.get('extend_existing') == True, "empresas debe tener extend_existing=True"
        else:
            assert False, "empresas __table_args__ debe ser dict con extend_existing"
            
        if isinstance(representantes_args, dict):
            assert representantes_args.get('extend_existing') == True, "representantes debe tener extend_existing=True"
        else:
            assert False, "representantes __table_args__ debe ser dict con extend_existing"
            
        print("   ✅ extend_existing configurado correctamente")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error en la prueba: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_database_connection():
    """Test básico de configuración de base de datos"""
    print("\n🔗 PRUEBA: Configuración de base de datos")
    print("="*60)
    
    try:
        print("1️⃣ Importando configuración de base de datos...")
        from app.core.database import Base, DATABASE_URL, get_database_url
        print("   ✅ Configuración importada exitosamente")
        
        print("2️⃣ Verificando URL de base de datos...")
        db_url = get_database_url()
        print(f"   ℹ️  Database URL: {db_url[:50]}...")
        
        if not db_url:
            print("   ⚠️  No hay URL de base de datos configurada")
            return False
            
        print("   ✅ URL de base de datos configurada")
        
        print("3️⃣ Verificando metadata...")
        print(f"   ℹ️  Tables in metadata: {len(Base.metadata.tables)}")
        
        for table_name in Base.metadata.tables.keys():
            print(f"      - {table_name}")
            
        print("   ✅ Metadata verificada")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error en configuración de BD: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_fastapi_imports():
    """Test de importaciones como lo haría FastAPI"""
    print("\n🚀 PRUEBA: Importaciones estilo FastAPI")
    print("="*60)
    
    try:
        print("1️⃣ Simulando importación de routers (como main.py)...")
        
        # Simular lo que pasa en main.py
        print("   - Importando router empresas...")
        from app.api.routes import empresas  # Esto debe importar los modelos
        print("   ✅ Router empresas importado")
        
        print("   - Simulando router empresas_smart...")
        # Solo verificar que podemos importar sin crear el router
        from app.api.routes.empresas_smart import EmpresaManualCompleta
        print("   ✅ Router smart simulado")
        
        print("2️⃣ Verificando que no hay conflictos de tabla...")
        from app.models.empresa import EmpresaDB
        print(f"   ℹ️  Tabla empresas ID: {id(EmpresaDB.__table__)}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error en importaciones FastAPI: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Ejecutar todas las pruebas"""
    print("🔧 TEST DEL FIX SQLALCHEMY - extend_existing=True")
    print(f"⏰ Ejecutado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("Importación múltiple", test_multiple_imports),
        ("Configuración BD", test_database_connection), 
        ("Importaciones FastAPI", test_fastapi_imports)
    ]
    
    results = {}
    for name, test_func in tests:
        try:
            result = test_func()
            results[name] = result
        except Exception as e:
            print(f"\n❌ Error ejecutando {name}: {e}")
            results[name] = False
    
    # Resumen
    print("\n" + "="*60)
    print("📊 RESUMEN DE PRUEBAS")
    print("="*60)
    
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    
    for name, result in results.items():
        status = "✅ PASÓ" if result else "❌ FALLÓ"
        print(f"   {status}: {name}")
    
    success_rate = (passed / total) * 100
    
    if passed == total:
        print(f"\n🎉 TODAS LAS PRUEBAS PASARON ({passed}/{total})")
        print("✅ El fix de extend_existing=True funciona correctamente")
        print("🚀 El deployment debería funcionar sin errores de SQLAlchemy")
        return True
    else:
        print(f"\n⚠️ ALGUNAS PRUEBAS FALLARON ({passed}/{total} - {success_rate:.1f}%)")
        print("❌ Es necesario revisar el fix antes del deployment")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)