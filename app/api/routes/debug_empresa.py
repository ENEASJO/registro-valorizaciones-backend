"""
Endpoint temporal para depurar creación de empresas
"""
from fastapi import APIRouter, HTTPException, Request
from typing import Dict, Any
import json
from datetime import datetime

router = APIRouter(prefix="/debug", tags=["debug"])

@router.post("/test-empresa-creation")
async def test_empresa_creation(request: Request):
    """Endpoint para probar la creación de empresas con logging detallado"""
    try:
        # Obtener el body de la request
        body = await request.body()
        data = json.loads(body)

        print("🔍 DEBUG: Recibida request para crear empresa")
        print(f"📊 Data: {json.dumps(data, indent=2, default=str)}")

        # Importar aquí para evitar import circular
        from app.services.empresa_service_neon import empresa_service_neon
        from app.api.routes.empresas import convertir_empresa_dict_a_response

        # Preparar datos para el servicio
        empresa_data_neon = {
            'ruc': data.get('ruc'),
            'razon_social': data.get('razon_social'),
            'nombre_comercial': data.get('nombre_comercial') or data.get('razon_social'),
            'email': data.get('email'),
            'telefono': data.get('telefono') or data.get('celular'),
            'direccion': data.get('direccion'),
            'departamento': data.get('departamento'),
            'provincia': data.get('provincia'),
            'distrito': data.get('distrito'),
            'ubigeo': data.get('ubigeo'),
            'estado_contribuyente': data.get('estado_contribuyente'),
            'tipo_contribuyente': data.get('tipo_contribuyente'),
            'fecha_inscripcion': data.get('fecha_inscripcion'),
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }

        print("📝 Datos preparados para Neon:")
        print(f"   RUC: {empresa_data_neon['ruc']}")
        print(f"   Razón Social: {empresa_data_neon['razon_social']}")
        print(f"   Email: {empresa_data_neon['email']}")
        print(f"   Teléfono: {empresa_data_neon['telefono']}")

        # Intentar guardar
        print("\n💾 Intentando guardar en la base de datos...")
        empresa_id = empresa_service_neon.guardar_empresa(empresa_data_neon)
        print(f"✅ Empresa guardada con ID: {empresa_id}")

        # Recuperar para verificar
        print("\n🔍 Recuperando empresa para verificar...")
        empresa_guardada = empresa_service_neon.obtener_empresa_por_ruc(data.get('ruc'))

        if empresa_guardada:
            print("✅ Empresa recuperada exitosamente")

            # Convertir a response
            print("\n🔄 Convirtiendo a response...")
            response = convertir_empresa_dict_a_response(empresa_guardada)
            print("✅ Conversión exitosa")

            return {
                "success": True,
                "message": "Empresa creada exitosamente en modo debug",
                "data": {
                    "empresa_id": empresa_id,
                    "response_id": response.id,
                    "ruc": response.ruc,
                    "razon_social": response.razon_social,
                    "telefono": response.telefono,
                    "email": response.email
                }
            }
        else:
            raise Exception("No se pudo recuperar la empresa guardada")

    except Exception as e:
        print(f"❌ ERROR en creación de empresa: {e}")
        import traceback
        traceback.print_exc()

        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "traceback": traceback.format_exc(),
            "received_data": data if 'data' in locals() else None
        }