#!/usr/bin/env python3
"""
Simple test script for SUNAT debugging
Tests with a known working RUC to identify the issue
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from debug_sunat_scraper import SUNATDebugger

async def test_known_ruc():
    """Test with a known RUC that should work"""
    # RUC de BACKUS (empresa conocida que debería existir)
    test_ruc = "20100070970"
    
    print(f"🔍 TESTING SUNAT DEBUG CON RUC: {test_ruc}")
    print(f"📝 Esta es la empresa: UNION DE CERVECERIAS PERUANAS BACKUS Y JOHNSTON S.A.A.")
    print(f"🎯 Este RUC debería funcionar para identificar el problema")
    
    debugger = SUNATDebugger()
    
    try:
        result = await debugger.debug_ruc_extraction(test_ruc)
        
        print(f"\n" + "="*60)
        print(f"RESULTADO DEL DEBUG")
        print(f"="*60)
        
        print(f"RUC testeado: {result['ruc']}")
        print(f"Timestamp: {result['timestamp']}")
        print(f"CAPTCHA detectado: {'SÍ' if result['captcha_detected'] else 'NO'}")
        print(f"Archivos guardados en: {result['debug_dir']}")
        
        print(f"\n📊 MEJOR RESULTADO:")
        print(f"   Estrategia exitosa: {result['best_result']['strategy']}")
        print(f"   Razón Social extraída: {result['best_result']['razon_social']}")
        print(f"   Método usado: {result['best_result'].get('method', 'N/A')}")
        print(f"   Éxito: {'✅ SÍ' if result['best_result']['success'] else '❌ NO'}")
        
        print(f"\n🔍 TODAS LAS ESTRATEGIAS:")
        for i, strategy in enumerate(result['all_results']['strategies']):
            status = "✅" if strategy['success'] else "❌"
            print(f"   {i+1}. {strategy['name']}: {status} - {strategy.get('razon_social', 'N/A')}")
        
        successful_count = len([s for s in result['all_results']['strategies'] if s['success']])
        print(f"\n📈 Resumen: {successful_count}/{len(result['all_results']['strategies'])} estrategias exitosas")
        
        if result['captcha_detected']:
            print(f"\n⚠️  IMPORTANTE: CAPTCHA fue detectado")
            print(f"   Esto podría explicar por qué falla el scraping en producción")
            print(f"   SUNAT puede estar requiriendo verificación humana")
        
        if not result['best_result']['success']:
            print(f"\n❌ PROBLEMA IDENTIFICADO:")
            print(f"   Ninguna estrategia pudo extraer la razón social correctamente")
            print(f"   Revisar los archivos HTML y screenshots para identificar:")
            print(f"   1. Si SUNAT cambió la estructura de la página")
            print(f"   2. Si hay elementos dinámicos que no esperamos")
            print(f"   3. Si hay CAPTCHA o bloqueos")
        
        print(f"\n📁 ARCHIVOS PARA REVISAR:")
        print(f"   • Screenshots: 01_pagina_inicial_*.png, 02_despues_submit_*.png") 
        print(f"   • HTML completo: 03_html_completo_*.html")
        print(f"   • Texto extraído: 04_texto_pagina_*.txt")
        print(f"   • Debug info: 05_debug_info_*.json")
        print(f"   • Resultados extracción: 06_extraccion_resultados_*.json")
        
        return result
        
    except Exception as e:
        print(f"\n❌ ERROR EN DEBUG: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    result = asyncio.run(test_known_ruc())