#!/usr/bin/env python3
"""
Script de inicio para Cloud Run
Maneja la variable PORT correctamente
"""
import os
import uvicorn
import sys

if __name__ == "__main__":
    # Obtener el puerto desde la variable de entorno
    port = int(os.environ.get("PORT", 8080))
    host = os.environ.get("HOST", "0.0.0.0")
    
    print(f"🚀 Iniciando servidor en {host}:{port}")
    print(f"📊 Variables de entorno PORT: {os.environ.get('PORT')}")
    
    # Usar aplicación simple para debug
    try:
        uvicorn.run(
            "main_simple:app", 
            host=host, 
            port=port, 
            workers=1,
            timeout_keep_alive=30,
            access_log=True,
            log_level="info"
        )
    except Exception as e:
        print(f"❌ Error iniciando servidor: {e}")
        sys.exit(1)