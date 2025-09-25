#!/usr/bin/env python3
"""
Script para depurar la creación de empresas
"""
import sys
import os
sys.path.append('.')

from datetime import datetime

# Datos de prueba basados en el log
test_empresa_data = {
    "ruc": "20610701117",
    "razon_social": "VIDA SANA ALEMANA SOCIEDAD ANONIMA CERRADA - VIDA SANA ALEMANA S.A.C.",
    "dni": None,
    "tipo_empresa": "SAC",
    "email": "estudiocontablefiori@gmail.com",
    "telefono": None,
    "celular": None,
    "direccion": None,
    "representante_legal": None,
    "dni_representante": None,
    "departamento": None,
    "provincia": None,
    "distrito": None,
    "ubigeo": None,
    "estado_contribuyente": "ACTIVO",
    "tipo_contribuyente": "SOCIEDAD ANONIMA CERRADA",
    "fecha_inscripcion": "2013-08-01",
    "categoria_contratista": "EJECUTORA",
    "especialidades": [],
    "representantes": [],
    "representante_principal_id": 0,
    "contactos": [],
    "datos_sunat": {
        "ruc": "20610701117",
        "razon_social": "VIDA SANA ALEMANA SOCIEDAD ANONIMA CERRADA - VIDA SANA ALEMANA S.A.C.",
        "tipo_contribuyente": "SOCIEDAD ANONIMA CERRADA",
        "estado_contribuyente": "ACTIVO",
        "direccion": "AV. AREQUIPA 2445 MIRAFLORES (LIMA) LIMA 15074",
        "departamento": "LIMA",
        "provincia": "LIMA",
        "distrito": "MIRAFLORES"
    },
    "datos_osce": None,
    "fuentes_consultadas": ["SUNAT"]
}

def test_empresa_creation():
    """Probar la creación de empresa con los datos del error"""
    try:
        from app.services.empresa_service_neon import empresa_service_neon
        from app.api.routes.empresas import convertir_empresa_dict_a_response

        print("🔍 Probando creación de empresa...")
        print(f"📊 RUC: {test_empresa_data['ruc']}")
        print(f"📊 Razón Social: {test_empresa_data['razon_social']}")

        # Paso 1: Guardar empresa
        print("\n1️⃣ Intentando guardar empresa...")
        empresa_id = empresa_service_neon.guardar_empresa(test_empresa_data)
        print(f"✅ Empresa guardada con ID: {empresa_id}")

        # Paso 2: Recuperar empresa
        print("\n2️⃣ Recuperando empresa guardada...")
        empresa_recuperada = empresa_service_neon.obtener_empresa_por_ruc(test_empresa_data['ruc'])

        if empresa_recuperada:
            print("✅ Empresa recuperada exitosamente")

            # Paso 3: Convertir a response
            print("\n3️⃣ Convirtiendo a response...")
            response = convertir_empresa_dict_a_response(empresa_recuperada)
            print("✅ Conversión exitosa")

            print(f"\n📋 Resultado:")
            print(f"   ID: {response.id}")
            print(f"   RUC: {response.ruc}")
            print(f"   Teléfono: {response.telefono}")
            print(f"   Email: {response.email}")

            return True
        else:
            print("❌ No se pudo recuperar la empresa")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Configurar variable de entorno para la base de datos
    if len(sys.argv) > 1:
        os.environ['NEON_CONNECTION_STRING'] = sys.argv[1]

    test_empresa_creation()