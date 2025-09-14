# main.py - Versión limpia que funciona en Cloud Run
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
import os
from typing import Dict, Any

app = FastAPI(
    title="API de Valorizaciones", 
    description="Backend para sistema de valorizaciones",
    version="3.0.0"
)

# CORS simple
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Endpoints básicos necesarios para el frontend
@app.get("/")
async def root():
    return {
        "message": "API de Valorizaciones funcionando",
        "status": "OK",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/api/empresas")
async def listar_empresas():
    """Endpoint temporal para empresas"""
    return {
        "success": True,
        "data": [],
        "total": 0,
        "message": "Endpoint empresas temporal",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/empresas")
async def crear_empresa(data: dict):
    """Endpoint temporal para crear empresas"""
    return {
        "success": True,
        "data": {"id": 1, **data},
        "message": "Empresa creada (temporal)",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/obras")
async def listar_obras():
    """Endpoint temporal para obras"""
    return {
        "success": True,
        "data": [],
        "message": "Endpoint obras temporal",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/obras")
async def crear_obra(data: dict):
    """Endpoint temporal para crear obras"""
    return {
        "success": True,
        "data": {"id": 1, **data},
        "message": "Obra creada (temporal)",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/valorizaciones")
async def listar_valorizaciones():
    """Endpoint temporal para valorizaciones"""
    return {
        "success": True,
        "data": [],
        "message": "Endpoint valorizaciones temporal",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/valorizaciones")
async def crear_valorizacion(data: dict):
    """Endpoint temporal para crear valorizaciones"""
    return {
        "success": True,
        "data": {"id": 1, **data},
        "message": "Valorización creada (temporal)",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/empresas-guardadas")
async def empresas_guardadas():
    """Endpoint temporal para empresas guardadas"""
    return {
        "success": True,
        "data": [],
        "total": 0,
        "message": "Empresas guardadas temporal",
        "timestamp": datetime.now().isoformat()
    }