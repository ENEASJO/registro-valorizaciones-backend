"""
Verificador de salud para detectar problemas de tipos en la API
"""
import json
from datetime import datetime
from typing import Dict, Any
from app.services.empresa_service_neon import empresa_service_neon
from app.api.routes.empresas import convertir_empresa_dict_a_response

async def check_uuid_handling() -> Dict[str, Any]:
    """
    Verifica que el sistema maneje UUIDs correctamente
    """
    results = {
        "timestamp": datetime.now().isoformat(),
        "checks": {},
        "status": "healthy"
    }

    try:
        # 1. Obtener una empresa de la base de datos
        empresas = empresa_service_neon.listar_empresas(limit=1)
        results["checks"]["database_connection"] = {
            "status": "ok",
            "empresas_found": len(empresas)
        }

        if empresas:
            # 2. Probar conversión con UUIDs
            try:
                empresa_response = convertir_empresa_dict_a_response(empresas[0])
                results["checks"]["uuid_conversion"] = {
                    "status": "ok",
                    "empresa_id": empresa_response.id,
                    "empresa_id_type": type(empresa_response.id).__name__,
                    "representantes_count": len(empresa_response.representantes)
                }

                # 3. Verificar tipos de IDs de representantes
                rep_ids_valid = all(
                    isinstance(rep.id, str)
                    for rep in empresa_response.representantes
                )
                results["checks"]["representante_ids"] = {
                    "status": "ok" if rep_ids_valid else "error",
                    "all_string_ids": rep_ids_valid
                }

            except Exception as e:
                results["checks"]["uuid_conversion"] = {
                    "status": "error",
                    "error": str(e)
                }
                results["status"] = "unhealthy"

        else:
            results["checks"]["uuid_conversion"] = {
                "status": "skipped",
                "reason": "no_empresas_found"
            }

    except Exception as e:
        results["checks"]["database_connection"] = {
            "status": "error",
            "error": str(e)
        }
        results["status"] = "unhealthy"

    return results

def validate_response_structure(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valida que la estructura de la respuesta sea correcta
    """
    validation_results = {
        "timestamp": datetime.now().isoformat(),
        "validations": {},
        "status": "valid"
    }

    # Validar respuesta de empresas
    if data.get("success") and data.get("data"):
        empresas_data = data.get("data", {})
        if "empresas" in empresas_data:
            for i, empresa in enumerate(empresas_data["empresas"]):
                # Validar ID de empresa
                if not isinstance(empresa.get("id"), str):
                    validation_results["validations"][f"empresa_{i}_id"] = {
                        "status": "error",
                        "expected": "string",
                        "got": type(empresa.get("id")).__name__
                    }
                    validation_results["status"] = "invalid"

                # Validar representantes
                if "representantes" in empresa:
                    for j, rep in enumerate(empresa["representantes"]):
                        if not isinstance(rep.get("id"), str):
                            validation_results["validations"][f"empresa_{i}_rep_{j}_id"] = {
                                "status": "error",
                                "expected": "string",
                                "got": type(rep.get("id")).__name__
                            }
                            validation_results["status"] = "invalid"

    return validation_results

# Lista de errores conocidos para detección temprana
KNOWN_ERRORS = {
    "invalid literal for int()": {
        "severity": "critical",
        "component": "uuid_conversion",
        "solution": "Check EmpresaResponse and RepresentanteResponse id types"
    },
    "cannot be converted to int": {
        "severity": "critical",
        "component": "uuid_conversion",
        "solution": "Ensure all UUIDs are handled as strings"
    },
    "404 Not Found": {
        "severity": "high",
        "component": "routing",
        "solution": "Check API paths and router configuration"
    },
    "500 Internal Server Error": {
        "severity": "high",
        "component": "general",
        "solution": "Check application logs"
    }
}

def detect_known_error(error_message: str) -> Dict[str, Any]:
    """
    Detecta si un error es conocido y retorna información de diagnóstico
    """
    for error_pattern, info in KNOWN_ERRORS.items():
        if error_pattern in error_message:
            return {
                "detected": True,
                "pattern": error_pattern,
                "severity": info["severity"],
                "component": info["component"],
                "solution": info["solution"],
                "timestamp": datetime.now().isoformat()
            }
    return {"detected": False}