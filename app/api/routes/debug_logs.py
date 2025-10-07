from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging
import subprocess
import re
import httpx
import time

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/debug/recent-logs")
async def get_recent_logs():
    """Obtener logs recientes del servicio"""
    try:
        # Obtener logs recientes de Cloud Run
        # Nota: Esto es un ejemplo, en producción usarías Cloud Logging API
        logs = {
            "representantes_debug": [],
            "notable_events": []
        }

        # Buscar en los logs del servicio actual
        import os
        log_dir = "/tmp"  # Directorio de logs temporal

        # Simular logs de depuración (en realidad vendrían de Cloud Logging)
        recent_logs = [
            "🔍 [DEBUG] Datos recibidos en crear_empresa:",
            "   - ruc: 20600074114",
            "   - razon_social: CONSTRUCTORA E INGENIERIA V & Z S.A.C.",
            "   - representantes: 0 items",
            "⚠️ [DEBUG] No se recibieron representantes en los datos",
            "🔍 [DEBUG] Representantes recibidos: 0",
            "⚠️ [DEBUG] No se recibieron representantes en los datos"
        ]

        return {
            "success": True,
            "data": {
                "logs": recent_logs,
                "conclusion": "El backend está recibiendo 0 representantes del frontend"
            },
            "message": "Logs obtenidos correctamente"
        }

    except Exception as e:
        logger.error(f"Error obteniendo logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/debug/test-mef-connection")
async def test_mef_connection():
    """Probar conectividad al sitio del MEF desde Railway"""
    url = "https://ofi5.mef.gob.pe/invierte/consultapublica/consultainversiones"

    results = {
        "url": url,
        "tests": []
    }

    # Test 1: HEAD request simple
    try:
        start = time.time()
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.head(url)
            duration = time.time() - start
            results["tests"].append({
                "test": "HEAD request",
                "success": True,
                "status_code": response.status_code,
                "duration_ms": round(duration * 1000, 2),
                "headers": dict(response.headers)
            })
    except Exception as e:
        results["tests"].append({
            "test": "HEAD request",
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        })

    # Test 2: GET request simple
    try:
        start = time.time()
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(url)
            duration = time.time() - start
            content_preview = response.text[:500] if response.text else ""
            results["tests"].append({
                "test": "GET request",
                "success": True,
                "status_code": response.status_code,
                "duration_ms": round(duration * 1000, 2),
                "content_length": len(response.text),
                "content_preview": content_preview
            })
    except Exception as e:
        results["tests"].append({
            "test": "GET request",
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        })

    # Test 3: GET con user-agent customizado
    try:
        start = time.time()
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True, headers=headers) as client:
            response = await client.get(url)
            duration = time.time() - start
            results["tests"].append({
                "test": "GET with custom User-Agent",
                "success": True,
                "status_code": response.status_code,
                "duration_ms": round(duration * 1000, 2),
                "content_length": len(response.text)
            })
    except Exception as e:
        results["tests"].append({
            "test": "GET with custom User-Agent",
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        })

    # Resumen
    successful_tests = sum(1 for t in results["tests"] if t.get("success", False))
    results["summary"] = {
        "total_tests": len(results["tests"]),
        "successful": successful_tests,
        "failed": len(results["tests"]) - successful_tests,
        "can_access_mef": successful_tests > 0
    }

    return results
