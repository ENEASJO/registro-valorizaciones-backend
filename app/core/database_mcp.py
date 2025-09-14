# database_mcp.py
# Configuración MCP (Model Context Protocol) para base de datos en Google Cloud Run

import os
import json
import asyncio
from typing import Optional, Dict, Any, List
try:
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
except ImportError:
    # Fallback para versiones anteriores de SQLAlchemy
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    async_sessionmaker = sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import text
from google.cloud.sql.connector import Connector
import asyncpg
from contextlib import asynccontextmanager

# Base para modelos SQLAlchemy
Base = declarative_base()

class DatabaseMCP:
    """
    Clase para manejar conexiones de base de datos usando MCP (Model Context Protocol)
    optimizada para Google Cloud Run con Cloud SQL
    """
    
    def __init__(self):
        self.connector: Optional[Connector] = None
        self.engine = None
        self.async_session_maker = None
        self.connection_pool = None
        
        # Configuración desde variables de entorno
        self.project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        self.region = os.getenv('GOOGLE_CLOUD_REGION', 'us-central1')
        self.instance_name = os.getenv('CLOUD_SQL_INSTANCE_NAME')
        self.database_name = os.getenv('CLOUD_SQL_DATABASE_NAME', 'valorizaciones')
        self.db_user = os.getenv('CLOUD_SQL_USER', 'postgres')
        self.db_password = os.getenv('CLOUD_SQL_PASSWORD')
        
        # Configuración alternativa para desarrollo local con Neon
        self.database_url = os.getenv('DATABASE_URL')
        
        # MCP Configuration
        self.mcp_config = {
            "name": "valoraciones-database-mcp",
            "version": "1.0.0",
            "description": "MCP Server para base de datos del sistema de valorizaciones",
            "tools": [
                {
                    "name": "consultar_empresas",
                    "description": "Consulta empresas desde la base de datos",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "ruc": {"type": "string", "description": "RUC de la empresa"},
                            "nombre": {"type": "string", "description": "Nombre de la empresa"},
                            "estado": {"type": "string", "description": "Estado de la empresa"}
                        }
                    }
                },
                {
                    "name": "consultar_obras",
                    "description": "Consulta obras desde la base de datos",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "codigo": {"type": "string", "description": "Código de la obra"},
                            "estado": {"type": "string", "description": "Estado de la obra"},
                            "empresa_id": {"type": "string", "description": "ID de la empresa"}
                        }
                    }
                },
                {
                    "name": "consultar_valorizaciones",
                    "description": "Consulta valorizaciones desde la base de datos",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "obra_id": {"type": "string", "description": "ID de la obra"},
                            "periodo": {"type": "string", "description": "Período de la valorización"},
                            "tipo": {"type": "string", "description": "Tipo de valorización"}
                        }
                    }
                },
                {
                    "name": "ejecutar_consulta_sql",
                    "description": "Ejecuta una consulta SQL personalizada (solo SELECT)",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Consulta SQL"},
                            "params": {"type": "object", "description": "Parámetros de la consulta"}
                        },
                        "required": ["query"]
                    }
                }
            ]
        }

    async def init_connection(self) -> bool:
        """
        Inicializa la conexión a la base de datos según el entorno
        """
        try:
            if self._is_cloud_run_environment():
                return await self._init_cloud_sql_connection()
            elif self.database_url:
                return await self._init_direct_connection()
            else:
                print("❌ No se encontró configuración de base de datos válida")
                return False
        except Exception as e:
            print(f"❌ Error inicializando conexión de base de datos: {e}")
            return False

    def _is_cloud_run_environment(self) -> bool:
        """Detecta si está ejecutándose en Google Cloud Run"""
        return (
            os.getenv('K_SERVICE') is not None and  # Variable específica de Cloud Run
            self.project_id and 
            self.instance_name
        )

    async def _init_cloud_sql_connection(self) -> bool:
        """
        Inicializa conexión usando Cloud SQL Connector para Cloud Run
        """
        try:
            print("🔗 Inicializando conexión Cloud SQL para Cloud Run...")
            
            # Crear connector
            self.connector = Connector()
            
            # Función para obtener conexión
            async def getconn() -> asyncpg.Connection:
                connection_string = f"{self.project_id}:{self.region}:{self.instance_name}"
                conn = await self.connector.connect_async(
                    connection_string,
                    "asyncpg",
                    user=self.db_user,
                    password=self.db_password,
                    db=self.database_name,
                )
                return conn

            # Crear engine SQLAlchemy
            self.engine = create_async_engine(
                "postgresql+asyncpg://",
                async_creator=getconn,
                echo=False,
                pool_size=5,
                max_overflow=2,
                pool_pre_ping=True,
                pool_recycle=300
            )
            
            # Crear session maker
            self.async_session_maker = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # Probar conexión
            async with self.async_session_maker() as session:
                result = await session.execute(text("SELECT 1"))
                await session.commit()
            
            print("✅ Conexión Cloud SQL establecida correctamente")
            return True
            
        except Exception as e:
            print(f"❌ Error en conexión Cloud SQL: {e}")
            return False

    #     """
    #     # Método deshabilitado - ahora usamos Neon exclusivamente
    #     return False

    async def _init_direct_connection(self) -> bool:
        """
        Inicializa conexión directa usando DATABASE_URL
        """
        try:
            print("🔗 Inicializando conexión directa...")
            
            self.engine = create_async_engine(
                self.database_url,
                echo=False,
                pool_size=5,
                max_overflow=2,
                pool_pre_ping=True
            )
            
            self.async_session_maker = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # Probar conexión
            async with self.async_session_maker() as session:
                result = await session.execute(text("SELECT 1"))
                await session.commit()
            
            print("✅ Conexión directa establecida correctamente")
            return True
            
        except Exception as e:
            print(f"❌ Error en conexión directa: {e}")
            return False

    @asynccontextmanager
    async def get_session(self):
        """
        Context manager para obtener una sesión de base de datos
        """
        if not self.async_session_maker:
            raise RuntimeError("Base de datos no inicializada. Llame a init_connection() primero.")
        
        async with self.async_session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    async def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Ejecuta una consulta SQL y retorna resultados
        """
        # Validar que la consulta sea solo SELECT para seguridad
        query_upper = query.strip().upper()
        if not query_upper.startswith('SELECT'):
            raise ValueError("Solo se permiten consultas SELECT por seguridad")
        
        async with self.get_session() as session:
            result = await session.execute(text(query), params or {})
            
            # Convertir resultados a lista de diccionarios
            columns = result.keys()
            rows = result.fetchall()
            
            return [dict(zip(columns, row)) for row in rows]

    async def consultar_empresas(self, ruc: Optional[str] = None, nombre: Optional[str] = None, estado: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Tool MCP: Consulta empresas con filtros opcionales
        """
        query = "SELECT * FROM empresas WHERE 1=1"
        params = {}
        
        if ruc:
            query += " AND ruc = :ruc"
            params['ruc'] = ruc
        
        if nombre:
            query += " AND razon_social ILIKE :nombre"
            params['nombre'] = f"%{nombre}%"
        
        if estado:
            query += " AND estado = :estado"
            params['estado'] = estado
        
        query += " ORDER BY razon_social LIMIT 100"
        
        return await self.execute_query(query, params)

    async def consultar_obras(self, codigo: Optional[str] = None, estado: Optional[str] = None, empresa_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Tool MCP: Consulta obras con filtros opcionales
        """
        query = """
        SELECT o.*, 
               ee.razon_social as empresa_ejecutora_nombre,
               es.razon_social as empresa_supervisora_nombre
        FROM obras o
        LEFT JOIN empresas ee ON o.empresa_ejecutora_id = ee.id
        LEFT JOIN empresas es ON o.empresa_supervisora_id = es.id
        WHERE 1=1
        """
        params = {}
        
        if codigo:
            query += " AND o.codigo = :codigo"
            params['codigo'] = codigo
        
        if estado:
            query += " AND o.estado = :estado"
            params['estado'] = estado
        
        if empresa_id:
            query += " AND (o.empresa_ejecutora_id = :empresa_id OR o.empresa_supervisora_id = :empresa_id)"
            params['empresa_id'] = empresa_id
        
        query += " ORDER BY o.fecha_inicio DESC LIMIT 100"
        
        return await self.execute_query(query, params)

    async def consultar_valorizaciones(self, obra_id: Optional[str] = None, periodo: Optional[str] = None, tipo: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Tool MCP: Consulta valorizaciones con filtros opcionales
        """
        query = """
        SELECT v.*, o.nombre as obra_nombre, o.codigo as obra_codigo
        FROM valorizaciones v
        LEFT JOIN obras o ON v.obra_id = o.id
        WHERE 1=1
        """
        params = {}
        
        if obra_id:
            query += " AND v.obra_id = :obra_id"
            params['obra_id'] = obra_id
        
        if periodo:
            query += " AND v.periodo = :periodo"
            params['periodo'] = periodo
        
        if tipo:
            query += " AND v.tipo = :tipo"
            params['tipo'] = tipo
        
        query += " ORDER BY v.periodo DESC, v.numero DESC LIMIT 100"
        
        return await self.execute_query(query, params)

    async def get_mcp_manifest(self) -> Dict[str, Any]:
        """
        Retorna el manifiesto MCP para este servidor
        """
        return self.mcp_config

    async def handle_mcp_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Maneja llamadas a herramientas MCP
        """
        try:
            if tool_name == "consultar_empresas":
                result = await self.consultar_empresas(**arguments)
                return {"success": True, "data": result}
            
            elif tool_name == "consultar_obras":
                result = await self.consultar_obras(**arguments)
                return {"success": True, "data": result}
            
            elif tool_name == "consultar_valorizaciones":
                result = await self.consultar_valorizaciones(**arguments)
                return {"success": True, "data": result}
            
            elif tool_name == "ejecutar_consulta_sql":
                result = await self.execute_query(arguments["query"], arguments.get("params"))
                return {"success": True, "data": result}
            
            else:
                return {"success": False, "error": f"Herramienta desconocida: {tool_name}"}
        
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def close(self):
        """
        Cierra las conexiones de base de datos
        """
        if self.engine:
            await self.engine.dispose()
        
        if self.connector:
            await self.connector.close_async()

# Instancia global
db_mcp = DatabaseMCP()

# Funciones de conveniencia
async def init_database_mcp() -> bool:
    """Inicializa el MCP de base de datos"""
    return await db_mcp.init_connection()

async def get_database_session():
    """Obtiene una sesión de base de datos"""
    return db_mcp.get_session()

async def close_database_mcp():
    """Cierra las conexiones MCP"""
    await db_mcp.close()