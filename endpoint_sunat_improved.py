#!/usr/bin/env python3
"""
Endpoint temporal para probar el servicio SUNAT mejorado
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from datetime import datetime

router = APIRouter()

@router.get("/consultar-ruc-improved/{ruc}")
async def consultar_ruc_improved(ruc: str):
    """Endpoint temporal para probar el servicio SUNAT mejorado"""

    print(f"🔍 [IMPROVED] Consultando RUC: {ruc}")

    # Validación básica
    if not ruc or len(ruc) != 11 or not ruc.isdigit():
        return {
            "success": False,
            "error": True,
            "message": "RUC inválido. Debe tener 11 dígitos",
            "timestamp": datetime.now().isoformat()
        }

    try:
        # Importar el servicio mejorado
        from app.services.sunat_service_improved import sunat_service_improved

        # Consultar usando el servicio mejorado
        empresa_info = await sunat_service_improved.consultar_empresa_completa(ruc)

        # Convertir a formato de respuesta
        return {
            "success": True,
            "data": {
                "ruc": empresa_info.ruc,
                "razon_social": empresa_info.razon_social,
                "estado": empresa_info.estado,
                "direccion": empresa_info.domicilio_fiscal,
                "representantes": [
                    {
                        "nombre": rep.nombre,
                        "cargo": rep.cargo,
                        "tipo_doc": rep.tipo_doc,
                        "numero_doc": rep.numero_doc,
                        "fecha_desde": rep.fecha_desde
                    }
                    for rep in empresa_info.representantes
                ],
                "total_representantes": empresa_info.total_representantes,
                "fuente": "SUNAT_IMPROVED",
                "extraccion_exitosa": True
            },
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        print(f"❌ Error en consulta SUNAT mejorada: {e}")
        return {
            "success": False,
            "error": True,
            "message": f"Error consultando SUNAT: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

# También agregar al router principal si existe
try:
    from app.api.routes.empresas import router as empresas_router
    empresas_router.include_router(router, prefix="")
    print("✅ Endpoint SUNAT mejorado agregado al router de empresas")
except:
    print("⚠️ No se pudo agregar endpoint al router existente")