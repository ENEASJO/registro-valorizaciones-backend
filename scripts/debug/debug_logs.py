#!/usr/bin/env python3
"""
Script para verificar logs del backend
"""

import requests
import json

BACKEND_URL = "https://registro-valorizaciones-backend-503600768755.southamerica-west1.run.app"

def debug_ultima_empresa():
    """Verificar la última empresa creada"""

    print("=== DEBUG ÚLTIMA EMPRESA CREADA ===")

    # Obtener empresas
    response = requests.get(f"{BACKEND_URL}/api/empresas/", timeout=10)

    if response.status_code == 200:
        data = response.json()
        if data['data']['empresas']:
            ultima_empresa = data['data']['empresas'][0]
            print(f"RUC: {ultima_empresa['ruc']}")
            print(f"Nombre: {ultima_empresa['razon_social']}")
            print(f"ID: {ultima_empresa['id']}")
            print(f"Fecha: {ultima_empresa.get('created_at', 'No disponible')}")

            # Verificar estructura
            print(f"\n¿Tiene representantes? {'representantes' in ultima_empresa}")
            if 'representantes' in ultima_empresa:
                print(f"Cantidad: {len(ultima_empresa['representantes'])}")

            # Verificar campos específicos
            print(f"\nCampos en la empresa:")
            for key in ['ruc', 'razon_social', 'representantes', 'representante_principal_id']:
                if key in ultima_empresa:
                    valor = ultima_empresa[key]
                    if key == 'representantes':
                        print(f"  {key}: {len(valor)} items")
                    else:
                        print(f"  {key}: {valor}")

            # Mostrar representantes si existen
            if ultima_empresa.get('representantes'):
                print(f"\nRepresentantes detallados:")
                for i, rep in enumerate(ultima_empresa['representantes']):
                    print(f"  {i+1}. {rep.get('nombre', 'Sin nombre')} - {rep.get('cargo', 'Sin cargo')}")
                    print(f"     DNI: {rep.get('numero_documento', 'No disponible')}")
                    print(f"     Principal: {rep.get('es_principal', False)}")

    else:
        print(f"Error: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    debug_ultima_empresa()