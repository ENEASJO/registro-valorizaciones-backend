#!/usr/bin/env python3
"""
Test the fixed SUNAT endpoint
"""

import asyncio
import json
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the main FastAPI app
from main import consultar_ruc_sunat, RUCInput

async def test_fixed_endpoint():
    """Test the fixed SUNAT endpoint with known RUCs"""
    
    test_cases = [
        ("20100113610", "BACKUS - Should work"),
        ("20100070970", "SUPERMERCADOS PERUANOS - Should work"),
        ("20100017491", "INTEGRATEL PERU - Should work")
    ]
    
    print("🧪 TESTING FIXED SUNAT ENDPOINT")
    print("="*60)
    
    for ruc, description in test_cases:
        print(f"\n📍 Testing: {ruc} ({description})")
        print(f"⏳ Consultando...")
        
        try:
            # Create RUCInput object
            ruc_input = RUCInput(ruc=ruc)
            
            # Call the endpoint function
            result = await consultar_ruc_sunat(ruc_input)
            
            # Parse the result
            success = result.get("success", False)
            data = result.get("data", {})
            
            razon_social = data.get("razon_social", "N/A")
            estado = data.get("estado", "N/A") 
            direccion = data.get("direccion", "N/A")
            extraccion_exitosa = data.get("extraccion_exitosa", False)
            metodo = data.get("metodo_extraccion", "N/A")
            
            print(f"✅ Resultado:")
            print(f"   Success: {success}")
            print(f"   Razón Social: {razon_social}")
            print(f"   Estado: {estado}")
            print(f"   Dirección: {direccion[:50]}{'...' if len(direccion) > 50 else ''}")
            print(f"   Extracción Exitosa: {'✅' if extraccion_exitosa else '❌'}")
            print(f"   Método: {metodo}")
            
            if extraccion_exitosa and razon_social != "No disponible":
                print(f"   🎯 SUCCESS! Empresa encontrada correctamente")
            else:
                print(f"   ⚠️ FAILED! Still returning 'No disponible'")
                print(f"   🔍 Debug info:")
                print(f"      - Success flag: {success}")
                print(f"      - Data keys: {list(data.keys())}")
                
        except Exception as e:
            print(f"   ❌ ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
        
        print("-" * 40)
    
    print(f"\n🏁 Test completed!")

if __name__ == "__main__":
    asyncio.run(test_fixed_endpoint())