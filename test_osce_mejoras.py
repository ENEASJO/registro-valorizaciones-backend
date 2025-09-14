#!/usr/bin/env python3
"""
Test script para verificar las mejoras específicas de OSCE:
- Contacto mejorado (teléfono, email)
- Representantes con DNI y cargos
- Consolidación sin duplicados
"""
import asyncio
import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_mejoras_osce():
    """Test de las mejoras específicas de OSCE"""
    print("🧪 Probando mejoras específicas de OSCE...")
    print("="*60)
    
    try:
        from app.services.osce_service import osce_service
        
        # RUC de prueba
        test_ruc = "20100070970"  # Supermercados Peruanos
        
        print(f"🔍 Consultando RUC: {test_ruc}")
        print(f"📋 Buscando específicamente:")
        print(f"   - Contacto: Teléfono y email")
        print(f"   - Representantes: Con DNI y cargos")
        print(f"   - Sin duplicados")
        print()
        
        # Ejecutar consulta
        empresa = await osce_service.consultar_empresa(test_ruc)
        
        print("="*60)
        print("📊 RESULTADOS DE MEJORAS")
        print("="*60)
        
        # 1. INFORMACIÓN DE CONTACTO
        print("📞 CONTACTO:")
        print(f"   Teléfono: {empresa.telefono or 'NO ENCONTRADO'}")
        print(f"   Email: {empresa.email or 'NO ENCONTRADO'}")
        
        if empresa.contacto:
            print(f"   Dirección: {empresa.contacto.direccion or 'NO ENCONTRADA'}")
            print(f"   Ciudad: {empresa.contacto.ciudad or 'NO ENCONTRADA'}")
        
        # 2. REPRESENTANTES CON DNI
        print(f"\n👥 REPRESENTANTES ({len(empresa.integrantes)} encontrados):")
        
        if empresa.integrantes:
            for i, integrante in enumerate(empresa.integrantes, 1):
                dni_info = f"DNI: {integrante.numero_documento}" if integrante.numero_documento else "SIN DNI"
                cargo_info = integrante.cargo or "SIN CARGO"
                
                print(f"   {i}. {integrante.nombre}")
                print(f"      └─ {dni_info} | Cargo: {cargo_info}")
        else:
            print("   ❌ No se encontraron representantes")
        
        # 3. VALIDACIONES DE CALIDAD
        print(f"\n✅ VALIDACIONES:")
        
        # Contacto
        tiene_telefono = bool(empresa.telefono and len(empresa.telefono) >= 7)
        tiene_email = bool(empresa.email and '@' in empresa.email)
        
        print(f"   Teléfono válido: {'✅ SÍ' if tiene_telefono else '❌ NO'}")
        print(f"   Email válido: {'✅ SÍ' if tiene_email else '❌ NO'}")
        
        # Representantes con DNI
        representantes_con_dni = [r for r in empresa.integrantes if r.numero_documento and len(r.numero_documento) == 8]
        representantes_con_cargo = [r for r in empresa.integrantes if r.cargo and r.cargo != 'SOCIO']
        
        print(f"   Representantes con DNI: {len(representantes_con_dni)}/{len(empresa.integrantes)}")
        print(f"   Representantes con cargo específico: {len(representantes_con_cargo)}/{len(empresa.integrantes)}")
        
        # Duplicados (por DNI)
        dnis = [r.numero_documento for r in empresa.integrantes if r.numero_documento]
        dnis_unicos = set(dnis)
        sin_duplicados = len(dnis) == len(dnis_unicos)
        
        print(f"   Sin duplicados por DNI: {'✅ SÍ' if sin_duplicados else '❌ NO'}")
        
        # 4. RESUMEN DE MEJORAS
        print(f"\n📈 RESUMEN DE MEJORAS:")
        mejoras_exitosas = 0
        
        if tiene_telefono:
            print("   ✅ Extracción de teléfono mejorada")
            mejoras_exitosas += 1
        else:
            print("   ❌ Extracción de teléfono necesita ajustes")
        
        if tiene_email:
            print("   ✅ Extracción de email mejorada") 
            mejoras_exitosas += 1
        else:
            print("   ❌ Extracción de email necesita ajustes")
        
        if len(representantes_con_dni) > 0:
            print("   ✅ Representantes con DNI extraídos")
            mejoras_exitosas += 1
        else:
            print("   ❌ Extracción de DNI necesita ajustes")
        
        if len(representantes_con_cargo) > 0:
            print("   ✅ Cargos específicos extraídos")
            mejoras_exitosas += 1
        else:
            print("   ❌ Extracción de cargos necesita ajustes")
        
        if sin_duplicados:
            print("   ✅ Consolidación sin duplicados")
            mejoras_exitosas += 1
        else:
            print("   ❌ Consolidación necesita ajustes")
        
        print(f"\n🎯 MEJORAS EXITOSAS: {mejoras_exitosas}/5")
        
        # Porcentaje de éxito
        porcentaje = (mejoras_exitosas / 5) * 100
        if porcentaje >= 80:
            print(f"🌟 EXCELENTE: {porcentaje:.0f}% de mejoras funcionando")
        elif porcentaje >= 60:
            print(f"✅ BUENO: {porcentaje:.0f}% de mejoras funcionando")
        elif porcentaje >= 40:
            print(f"⚠️ REGULAR: {porcentaje:.0f}% de mejoras funcionando")
        else:
            print(f"❌ NECESITA TRABAJO: {porcentaje:.0f}% de mejoras funcionando")
        
        return empresa
        
    except Exception as e:
        print(f"❌ Error en test de mejoras: {e}")
        import traceback
        traceback.print_exc()
        return None

async def main():
    """Función principal"""
    print("🚀 Iniciando test de mejoras OSCE...")
    
    resultado = await test_mejoras_osce()
    
    print("\n" + "="*60)
    print("🏁 Test de mejoras completado")
    print("="*60)
    
    if resultado:
        print("✅ Consulta exitosa - Revisar resultados arriba")
    else:
        print("❌ Consulta falló - Revisar logs de error")

if __name__ == "__main__":
    asyncio.run(main())