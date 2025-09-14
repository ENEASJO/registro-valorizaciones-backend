#!/usr/bin/env python3
"""
Script para probar si los representantes se guardan correctamente
"""

import requests
import json

BACKEND_URL = "https://registro-valorizaciones-backend-503600768755.southamerica-west1.run.app"

def test_guardar_empresa_con_representantes():
    """Probar guardar una empresa con representantes"""

    empresa_test = {
        "ruc": "20512345678",
        "razon_social": "EMPRESA DE PRUEBA CON REPRESENTANTES",
        "tipo_empresa": "SAC",
        "email": "test@empresa.com",
        "celular": "987654321",
        "direccion": "Av. Test 123",
        "representantes": [
            {
                "nombre": "REPRESENTANTE PRINCIPAL",
                "cargo": "GERENTE GENERAL",
                "numero_documento": "12345678",
                "tipo_documento": "DNI",
                "es_principal": True,
                "fuente": "MANUAL",
                "activo": True
            },
            {
                "nombre": "REPRESENTANTE SECUNDARIO",
                "cargo": "ADMINISTRADOR",
                "numero_documento": "87654321",
                "tipo_documento": "DNI",
                "es_principal": False,
                "fuente": "MANUAL",
                "activo": True
            }
        ],
        "representante_principal_id": 0,
        "categoria_contratista": "EJECUTORA",
        "estado": "ACTIVO"
    }

    print("=== PROBANDO GUARDAR EMPRESA CON REPRESENTANTES ===")
    print(f"RUC: {empresa_test['ruc']}")
    print(f"Representantes: {len(empresa_test['representantes'])}")

    try:
        # Primero verificar si ya existe
        response = requests.get(f"{BACKEND_URL}/api/empresas/", timeout=10)
        if response.status_code == 200:
            data = response.json()
            empresas_existentes = [e for e in data['data']['empresas'] if e['ruc'] == empresa_test['ruc']]
            if empresas_existentes:
                print("⚠️ La empresa ya existe, eliminándola primero...")
                # Intentar eliminar
                delete_resp = requests.delete(f"{BACKEND_URL}/api/empresas/{empresas_existentes[0]['id']}", timeout=10)
                print(f"   Delete response: {delete_resp.status_code}")

        # Crear la empresa
        print("\n📝 Creando empresa con representantes...")
        response = requests.post(
            f"{BACKEND_URL}/api/empresas/",
            json=empresa_test,
            timeout=30
        )

        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print("✅ Empresa creada exitosamente")

            # Verificar si se guardaron los representantes
            if 'data' in data and 'representantes' in data['data']:
                reps = data['data']['representantes']
                print(f"✅ Representantes guardados: {len(reps)}")
                for rep in reps:
                    print(f"   - {rep['nombre']} ({rep['cargo']})")
            else:
                print("❌ La respuesta no incluye representantes")
                print("   Esto podría indicar que no se guardaron")

            # Verificar directamente en la lista
            print("\n🔍 Verificando en lista completa...")
            response2 = requests.get(f"{BACKEND_URL}/api/empresas/", timeout=10)
            if response2.status_code == 200:
                data2 = response2.json()
                empresa_guardada = next((e for e in data2['data']['empresas'] if e['ruc'] == empresa_test['ruc']), None)
                if empresa_guardada:
                    if 'representantes' in empresa_guardada and empresa_guardada['representantes']:
                        print(f"✅ Confirmado: {len(empresa_guardada['representantes'])} representantes en la lista")
                    else:
                        print("❌ La empresa está en la lista pero sin representantes")
                else:
                    print("❌ La empresa no aparece en la lista")

        else:
            print("❌ Error al crear empresa")
            try:
                error = response.json()
                print(f"   Detalle: {error.get('detail', 'Sin detalle')}")
            except:
                print(f"   Respuesta: {response.text[:200]}")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_guardar_empresa_con_representantes()