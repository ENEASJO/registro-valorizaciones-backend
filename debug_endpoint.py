#!/usr/bin/env python3
"""
Script para verificar qué datos está recibiendo el backend
"""
import sys
import os
sys.path.append('/home/usuario/PROYECTOS/registro-valorizaciones-app/registro-valorizaciones-backend')
import json
from datetime import datetime

from app.services.empresa_service_neon import empresa_service_neon

def simular_guardar_empresa():
    """Simular el proceso de guardar empresa con datos de prueba"""
    try:
        print("🔍 Simulando guardado de empresa...")

        # Datos similares a lo que debería enviar el frontend
        empresa_data = {
            "ruc": "20600074114",
            "razon_social": "CONSTRUCTORA E INGENIERIA V & Z S.A.C.",
            "tipo_empresa": "SAC",
            "direccion": "AV. SALAVERRY 2225",
            "representantes": [
                {
                    "nombre": "EDGAR WILFREDO GARAY DIAZ",
                    "cargo": "GERENTE GENERAL",
                    "numero_documento": "07600999",
                    "tipo_documento": "DNI",
                    "fuente": "SUNAT",
                    "es_principal": True,
                    "activo": True
                }
            ],
            "datos_sunat": {
                "representantes_legales": [
                    {
                        "nombre": "EDGAR WILFREDO GARAY DIAZ",
                        "cargo": "GERENTE GENERAL",
                        "tipo_doc": "DNI",
                        "num_doc": "07600999"
                    }
                ]
            },
            "datos_osce": {
                "representantes_legales": [
                    {
                        "nombre": "EDGAR WILFREDO GARAY DIAZ",
                        "cargo": "GERENTE GENERAL",
                        "tipo_documento": "DNI",
                        "numero_documento": "07600999"
                    }
                ]
            }
        }

        print(f"📤 Datos a guardar:")
        print(f"   - RUC: {empresa_data['ruc']}")
        print(f"   - ¿Tiene datos_sunat?: {'Sí' if empresa_data.get('datos_sunat') else 'No'}")
        print(f"   - ¿Tiene datos_osce?: {'Sí' if empresa_data.get('datos_osce') else 'No'}")
        if empresa_data.get('datos_sunat'):
            print(f"   - Representantes en datos_sunat: {len(empresa_data['datos_sunat']['representantes_legales'])}")

        # Intentar guardar
        result = empresa_service_neon.guardar_empresa(empresa_data)

        print(f"\n📋 Resultado: {result}")

        # Verificar qué se guardó
        with empresa_service_neon._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT ruc, razon_social, datos_sunat, datos_osce
                    FROM empresas
                    WHERE ruc = %s
                    ORDER BY created_at DESC
                    LIMIT 1
                """, ("20600074114",))
                empresa = cursor.fetchone()

                if empresa:
                    print(f"\n📊 Verificación en BD:")
                    print(f"   - datos_sunat guardado: {'Sí' if empresa['datos_sunat'] else 'No'}")
                    print(f"   - datos_osce guardado: {'Sí' if empresa['datos_osce'] else 'No'}")

                    # Verificar representantes
                    cursor.execute("""
                        SELECT COUNT(*) as total
                        FROM representantes_legales rl
                        JOIN empresas e ON rl.empresa_id = e.id
                        WHERE e.ruc = %s
                    """, ("20600074114",))
                    rep_count = cursor.fetchone()['total']
                    print(f"   - Representantes en BD: {rep_count}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    simular_guardar_empresa()