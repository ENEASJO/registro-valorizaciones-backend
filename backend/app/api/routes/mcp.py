# mcp.py
# Rutas API para el servidor MCP (Model Context Protocol)

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import json
from datetime import datetime

# Try to import MCP database, but make it optional
try:
    from app.core.database_mcp import db_mcp
    MCP_DB_AVAILABLE = True
except ImportError:
    MCP_DB_AVAILABLE = False
    db_mcp = None

router = APIRouter(prefix="/mcp", tags=["mcp"])

# Modelos Pydantic para MCP
class MCPToolCall(BaseModel):
    tool: str
    arguments: Dict[str, Any]

class MCPResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    timestamp: str = datetime.now().isoformat()

class MCPManifestResponse(BaseModel):
    name: str
    version: str
    description: str
    tools: List[Dict[str, Any]]

# Endpoint para obtener el manifiesto MCP
@router.get("/manifest", response_model=MCPManifestResponse)
async def get_mcp_manifest():
    """
    Retorna el manifiesto del servidor MCP con todas las herramientas disponibles
    """
    try:
        manifest = await db_mcp.get_mcp_manifest()
        return MCPManifestResponse(**manifest)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo manifiesto MCP: {str(e)}")

# Endpoint para ejecutar herramientas MCP
@router.post("/tool", response_model=MCPResponse)
async def execute_mcp_tool(tool_call: MCPToolCall):
    """
    Ejecuta una herramienta MCP específica con los argumentos proporcionados
    """
    try:
        # Validar que la base de datos esté inicializada
        if not db_mcp.async_session_maker:
            raise HTTPException(status_code=503, detail="Base de datos MCP no inicializada")
        
        # Ejecutar herramienta
        result = await db_mcp.handle_mcp_tool_call(tool_call.tool, tool_call.arguments)
        
        if result["success"]:
            return MCPResponse(
                success=True,
                data=result["data"]
            )
        else:
            return MCPResponse(
                success=False,
                error=result["error"]
            )
    
    except Exception as e:
        return MCPResponse(
            success=False,
            error=f"Error ejecutando herramienta MCP: {str(e)}"
        )

# Endpoint para consultar empresas (herramienta MCP específica)
@router.get("/empresas", response_model=MCPResponse)
async def mcp_consultar_empresas(
    ruc: Optional[str] = None,
    nombre: Optional[str] = None,
    estado: Optional[str] = None
):
    """
    Herramienta MCP: Consulta empresas con filtros opcionales
    """
    try:
        result = await db_mcp.consultar_empresas(ruc=ruc, nombre=nombre, estado=estado)
        return MCPResponse(success=True, data=result)
    except Exception as e:
        return MCPResponse(success=False, error=str(e))

# Endpoint para consultar obras (herramienta MCP específica)
@router.get("/obras", response_model=MCPResponse)
async def mcp_consultar_obras(
    codigo: Optional[str] = None,
    estado: Optional[str] = None,
    empresa_id: Optional[str] = None
):
    """
    Herramienta MCP: Consulta obras con filtros opcionales
    """
    try:
        result = await db_mcp.consultar_obras(codigo=codigo, estado=estado, empresa_id=empresa_id)
        return MCPResponse(success=True, data=result)
    except Exception as e:
        return MCPResponse(success=False, error=str(e))

# Endpoint para consultar valorizaciones (herramienta MCP específica)
@router.get("/valorizaciones", response_model=MCPResponse)
async def mcp_consultar_valorizaciones(
    obra_id: Optional[str] = None,
    periodo: Optional[str] = None,
    tipo: Optional[str] = None
):
    """
    Herramienta MCP: Consulta valorizaciones con filtros opcionales
    """
    try:
        result = await db_mcp.consultar_valorizaciones(obra_id=obra_id, periodo=periodo, tipo=tipo)
        return MCPResponse(success=True, data=result)
    except Exception as e:
        return MCPResponse(success=False, error=str(e))

# Endpoint para ejecutar consultas SQL personalizadas (solo SELECT)
@router.post("/query", response_model=MCPResponse)
async def mcp_execute_query(query_data: Dict[str, Any]):
    """
    Herramienta MCP: Ejecuta una consulta SQL personalizada (solo SELECT por seguridad)
    """
    try:
        query = query_data.get("query")
        params = query_data.get("params", {})
        
        if not query:
            return MCPResponse(success=False, error="Se requiere el parámetro 'query'")
        
        result = await db_mcp.execute_query(query, params)
        return MCPResponse(success=True, data=result)
    except Exception as e:
        return MCPResponse(success=False, error=str(e))

# Endpoint de salud para el servidor MCP
@router.get("/health", response_model=MCPResponse)
async def mcp_health_check():
    """
    Verifica el estado de salud del servidor MCP
    """
    try:
        # Verificar conexión a base de datos
        if not db_mcp.async_session_maker:
            return MCPResponse(
                success=False,
                error="Base de datos MCP no inicializada"
            )
        
        # Ejecutar consulta simple para verificar conectividad
        async with db_mcp.get_session() as session:
            from sqlalchemy import text
            result = await session.execute(text("SELECT 1 as health_check"))
            row = result.fetchone()
        
        return MCPResponse(
            success=True,
            data={
                "status": "healthy",
                "database": "connected",
                "mcp_version": "1.0.0",
                "available_tools": len(db_mcp.mcp_config["tools"])
            }
        )
    
    except Exception as e:
        return MCPResponse(
            success=False,
            error=f"Error en verificación de salud MCP: {str(e)}"
        )

# Endpoint para obtener estadísticas del servidor MCP
@router.get("/stats", response_model=MCPResponse)
async def mcp_get_stats():
    """
    Obtiene estadísticas del servidor MCP
    """
    try:
        async with db_mcp.get_session() as session:
            from sqlalchemy import text
            
            # Contar registros en tablas principales
            stats_queries = {
                "total_empresas": "SELECT COUNT(*) FROM empresas",
                "empresas_activas": "SELECT COUNT(*) FROM empresas WHERE estado = 'activo'",
                "total_obras": "SELECT COUNT(*) FROM obras",
                "obras_activas": "SELECT COUNT(*) FROM obras WHERE estado IN ('en_ejecucion', 'planificada')",
                "total_valorizaciones": "SELECT COUNT(*) FROM valorizaciones",
                "valorizaciones_aprobadas": "SELECT COUNT(*) FROM valorizaciones WHERE estado = 'aprobada'"
            }
            
            stats = {}
            for key, query in stats_queries.items():
                try:
                    result = await session.execute(text(query))
                    stats[key] = result.scalar()
                except Exception:
                    stats[key] = 0
        
        return MCPResponse(
            success=True,
            data={
                "database_stats": stats,
                "mcp_config": {
                    "name": db_mcp.mcp_config["name"],
                    "version": db_mcp.mcp_config["version"],
                    "total_tools": len(db_mcp.mcp_config["tools"])
                }
            }
        )
    
    except Exception as e:
        return MCPResponse(
            success=False,
            error=f"Error obteniendo estadísticas MCP: {str(e)}"
        )