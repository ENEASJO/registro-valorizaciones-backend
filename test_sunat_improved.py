#!/usr/bin/env python3
"""
Script para probar el servicio SUNAT mejorado
"""

import asyncio
import json
import pytest
from app.services.sunat_service_improved import sunat_service_improved

@pytest.mark.asyncio
async def test_sunat_improved():
    """Probar el servicio SUNAT mejorado"""

    ruc = "20600074114"
    print(f"🧪 Probando servicio SUNAT mejorado para RUC: {ruc}")

    try:
        # Consultar empresa con el servicio mejorado
        empresa = await sunat_service_improved.consultar_empresa_completa(ruc)

        print(f"\n✅ Resultados:")
        print(f"   Razón Social: {empresa.razon_social}")
        print(f"   Estado: {empresa.estado}")
        print(f"   Dirección: {empresa.domicilio_fiscal}")
        print(f"   Total Representantes: {empresa.total_representantes}")

        print(f"\n👥 Representantes encontrados:")
        if empresa.representantes:
            for i, rep in enumerate(empresa.representantes, 1):
                print(f"   {i}. {rep.nombre}")
                print(f"      Cargo: {rep.cargo}")
                print(f"      Documento: {rep.tipo_doc} {rep.numero_doc}")
                if rep.fecha_desde:
                    print(f"      Fecha: {rep.fecha_desde}")
                print()
        else:
            print("   ❌ No se encontraron representantes")

        # Guardar resultados en archivo
        resultados = {
            "ruc": ruc,
            "razon_social": empresa.razon_social,
            "estado": empresa.estado,
            "direccion": empresa.domicilio_fiscal,
            "representantes": [
                {
                    "nombre": rep.nombre,
                    "cargo": rep.cargo,
                    "tipo_doc": rep.tipo_doc,
                    "numero_doc": rep.numero_doc,
                    "fecha_desde": rep.fecha_desde
                }
                for rep in empresa.representantes
            ],
            "total_representantes": empresa.total_representantes
        }

        with open(f"/tmp/sunat_resultados_{ruc}.json", "w", encoding="utf-8") as f:
            json.dump(resultados, f, indent=2, ensure_ascii=False)

        print(f"📄 Resultados guardados en /tmp/sunat_resultados_{ruc}.json")

        return empresa

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    resultado = asyncio.run(test_sunat_improved())

    if resultado:
        print(f"\n🎉 Prueba completada!")
        print(f"   Se encontraron {resultado.total_representantes} representantes")
    else:
        print(f"\n💥 La prueba falló")