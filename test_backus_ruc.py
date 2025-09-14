#!/usr/bin/env python3
"""
Test with correct Backus RUC
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from debug_sunat_scraper import SUNATDebugger

async def test_backus_ruc():
    """Test with the correct Backus RUC"""
    # Let's try the correct Backus RUC - 20100113610
    test_ruc = "20100113610"
    
    print(f"🔍 TESTING SUNAT CON RUC BACKUS CORRECTO: {test_ruc}")
    
    debugger = SUNATDebugger()
    
    try:
        result = await debugger.debug_ruc_extraction(test_ruc)
        
        print(f"\n" + "="*60)
        print(f"RESULTADO - BACKUS RUC CORRECTO")
        print(f"="*60)
        
        print(f"RUC testeado: {result['ruc']}")
        print(f"CAPTCHA detectado: {'SÍ' if result['captcha_detected'] else 'NO'}")
        
        print(f"\n📊 MEJOR RESULTADO:")
        print(f"   Razón Social extraída: {result['best_result']['razon_social']}")
        print(f"   Éxito: {'✅ SÍ' if result['best_result']['success'] else '❌ NO'}")
        
        if result['best_result']['success']:
            print(f"\n✅ CONFIRMACIÓN: El scraping funciona correctamente!")
            print(f"   La empresa extraída es: {result['best_result']['razon_social']}")
            print(f"   Estrategia exitosa: {result['best_result']['strategy']}")
        
        return result
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        return None

async def test_multiple_rucs():
    """Test with multiple known RUCs"""
    test_rucs = [
        ("20100113610", "UNION DE CERVECERIAS PERUANAS BACKUS Y JOHNSTON S.A.A."),
        ("20100070970", "SUPERMERCADOS PERUANOS SOCIEDAD ANONIMA"),
        ("20100017491", "TELEFONICA DEL PERU S.A.A."),
    ]
    
    debugger = SUNATDebugger()
    
    print(f"🔍 TESTING MÚLTIPLES RUCs CONOCIDOS")
    print(f"="*60)
    
    for ruc, expected_name in test_rucs:
        print(f"\n📍 Probando RUC: {ruc}")
        print(f"   Empresa esperada: {expected_name}")
        
        try:
            result = await debugger.debug_ruc_extraction(ruc)
            
            actual_name = result['best_result']['razon_social']
            success = result['best_result']['success']
            
            print(f"   Resultado: {'✅' if success else '❌'} {actual_name}")
            
            if success and expected_name.upper() in actual_name.upper():
                print(f"   ✅ MATCH: Empresa correcta encontrada!")
            elif success:
                print(f"   ⚠️ DIFERENTE: Empresa encontrada pero nombre no coincide exactamente")
            else:
                print(f"   ❌ FALLO: No se pudo extraer información")
                
        except Exception as e:
            print(f"   ❌ ERROR: {str(e)}")

if __name__ == "__main__":
    # First test just the correct Backus RUC
    print("=== TEST 1: RUC BACKUS CORRECTO ===")
    asyncio.run(test_backus_ruc())
    
    print("\n\n=== TEST 2: MÚLTIPLES RUCs ===")
    asyncio.run(test_multiple_rucs())