#!/usr/bin/env python3
"""
Script de inicio para Cloud Run
Maneja la variable PORT correctamente
"""
import os
import uvicorn

if __name__ == "__main__":
    # Obtener el puerto desde la variable de entorno
    port = int(os.environ.get("PORT", 8080))
    host = os.environ.get("HOST", "0.0.0.0")
    
    print(f"🚀 Iniciando servidor en {host}:{port}")
    
    uvicorn.run(
        "main:app", 
        host=host, 
        port=port, 
        workers=1,
        timeout_keep_alive=30,
        access_log=True
    )