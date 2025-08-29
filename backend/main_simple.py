#!/usr/bin/env python3
"""
Versión simplificada para debug de Cloud Run
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

# Aplicación mínima
app = FastAPI(title="API Debug", version="1.0.0")

# CORS básico
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "API funcionando correctamente", "status": "OK"}

@app.get("/health")
async def health():
    return {"status": "healthy", "port": os.environ.get("PORT", "not set")}

@app.get("/debug")
async def debug():
    return {
        "port": os.environ.get("PORT"),
        "host": os.environ.get("HOST", "0.0.0.0"),
        "env_vars": dict(os.environ)
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    print(f"🚀 Iniciando servidor debug en puerto {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)