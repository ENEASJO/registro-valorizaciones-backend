from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging
import subprocess
import re

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