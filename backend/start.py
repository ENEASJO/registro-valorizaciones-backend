#!/usr/bin/env python3
"""
Script de inicio para Cloud Run
Maneja la variable PORT correctamente
"""
import os
import uvicorn
import sys
import socket

def check_port_available(host, port):
    """Verificar si el puerto está disponible"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((host, port))
            return True
    except OSError as e:
        print(f"❌ Puerto {port} no disponible: {e}")
        return False

if __name__ == "__main__":
    # Obtener el puerto desde la variable de entorno
    port = int(os.environ.get("PORT", 8080))
    host = os.environ.get("HOST", "0.0.0.0")
    
    print(f"🚀 Iniciando servidor en {host}:{port}")
    print(f"📊 Variables de entorno PORT: {os.environ.get('PORT')}")
    print(f"🔍 Verificando disponibilidad del puerto...")
    
    # Verificar puerto disponible
    if not check_port_available(host, port):
        print(f"❌ No se puede usar el puerto {port}")
        sys.exit(1)
    
    # Usar aplicación simple para debug
    try:
        print(f"▶️ Iniciando uvicorn...")
        uvicorn.run(
            "main_simple:app", 
            host=host, 
            port=port, 
            workers=1,
            log_level="debug",
            access_log=True,
            reload=False
        )
    except Exception as e:
        print(f"❌ Error iniciando servidor: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)