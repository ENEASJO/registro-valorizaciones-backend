#!/usr/bin/env python3
"""
🧪 Test rápido del fix de Pydantic V2 - regex → pattern
Verifica que los modelos pueden ser importados sin error de regex
"""

import sys
from datetime import datetime

def test_pydantic_imports():
    """Test que los modelos Pydantic se importen sin error de regex"""
    print("🧪 PRUEBA: Importación de modelos Pydantic V2")
    print("="*60)
    
    try:
        print("1️⃣ Importando modelos de empresa...")
        from app.models.empresa import EmpresaCreateSchema, EmpresaManualCompleta
        print("   ✅ Modelos de empresa importados sin error")
        
        print("2️⃣ Importando modelos de empresas_smart...")
        from app.api.routes.empresas_smart import EmpresaManualCompleta as SmartEmpresa, EmpresaDualCreate
        print("   ✅ Modelos de empresas_smart importados sin error")
        
        print("3️⃣ Importando modelos de notificaciones...")
        from app.api.schemas.notifications import NotificationFilters, TestMessageRequest
        print("   ✅ Modelos de notificaciones importados sin error")
        
        print("4️⃣ Verificando que pattern= funciona correctamente...")
        
        # Test con RUC válido
        try:
            empresa = EmpresaCreateSchema(
                ruc="20123456781", 
                razon_social="Test Company SAC"
            )
            print("   ✅ RUC válido aceptado correctamente")
        except Exception as e:
            print(f"   ❌ Error con RUC válido: {e}")
            return False
        
        # Test con RUC inválido (debe fallar)
        try:
            empresa_invalid = EmpresaCreateSchema(
                ruc="123", 
                razon_social="Test Invalid"
            )
            print("   ❌ RUC inválido fue aceptado (esto no debería pasar)")
            return False
        except Exception:
            print("   ✅ RUC inválido rechazado correctamente")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error en la prueba: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_regex_vs_pattern():
    """Test que demuestra que el fix de regex → pattern funciona"""
    print("\n🔧 PRUEBA: Verificación regex → pattern")
    print("="*60)
    
    try:
        print("1️⃣ Verificando que no hay referencias a 'regex=' en modelos...")
        
        # Verificar que los modelos usan 'pattern=' en lugar de 'regex='
        from app.models.empresa import EmpresaCreateSchema
        from app.api.routes.empresas_smart import EmpresaManualCompleta
        
        # Intentar crear instancias para activar la validación
        valid_ruc = "20123456781"
        invalid_ruc = "abc123"
        
        try:
            # Debe funcionar con RUC válido
            EmpresaCreateSchema(ruc=valid_ruc, razon_social="Test")
            EmpresaManualCompleta(ruc=valid_ruc, razon_social="Test")
            print("   ✅ Validación con pattern= funciona para RUCs válidos")
        except Exception as e:
            print(f"   ❌ Error con RUCs válidos: {e}")
            return False
        
        try:
            # Debe fallar con RUC inválido
            EmpresaCreateSchema(ruc=invalid_ruc, razon_social="Test")
            print("   ❌ RUC inválido no fue rechazado")
            return False
        except:
            print("   ✅ Validación con pattern= rechaza correctamente RUCs inválidos")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error verificando pattern: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Ejecutar todas las pruebas"""
    print("🔧 TEST DEL FIX PYDANTIC V2 - regex → pattern")
    print(f"⏰ Ejecutado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("Importación Pydantic", test_pydantic_imports),
        ("Regex → Pattern", test_regex_vs_pattern)
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
        print("✅ El fix de regex → pattern funciona correctamente")
        print("🚀 Los tests de Pydantic V2 deberían pasar sin errores")
        return True
    else:
        print(f"\n⚠️ ALGUNAS PRUEBAS FALLARON ({passed}/{total} - {success_rate:.1f}%)")
        print("❌ Es necesario revisar el fix antes del deployment")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)