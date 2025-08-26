"""
Configuración de la base de datos Turso
"""
import os
from typing import AsyncGenerator, Optional
from dotenv import load_dotenv
from libsql_client import create_client_sync, create_client
from sqlalchemy import create_engine, MetaData, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy.pool import StaticPool

# Load environment variables
load_dotenv()

# Turso configuration - load at runtime to avoid import errors
def get_turso_config():
    """Get Turso configuration from environment"""
    TURSO_DATABASE_URL = os.getenv("TURSO_DATABASE_URL")
    TURSO_AUTH_TOKEN = os.getenv("TURSO_AUTH_TOKEN")
    
    if not TURSO_DATABASE_URL or not TURSO_AUTH_TOKEN:
        print(f"⚠️ Turso config missing: URL={bool(TURSO_DATABASE_URL)}, TOKEN={bool(TURSO_AUTH_TOKEN)}")
        return None, None
    
    return TURSO_DATABASE_URL, TURSO_AUTH_TOKEN

# Turso async client
turso_client = None

# Base para modelos
Base = declarative_base()

# SQLAlchemy engine (para schema creation solamente)
engine = create_engine(
    "sqlite:///:memory:",  # Temporary engine for schema generation
    echo=False
)

async def init_turso():
    """Inicializar cliente Turso"""
    global turso_client
    try:
        # Get config at runtime
        TURSO_DATABASE_URL, TURSO_AUTH_TOKEN = get_turso_config()
        
        if not TURSO_DATABASE_URL or not TURSO_AUTH_TOKEN:
            print("❌ Turso configuration not available")
            return False
        
        # Use HTTP instead of WebSocket to avoid 505 error
        # Convert wss:// to https:// for HTTP API
        http_url = TURSO_DATABASE_URL.replace("libsql://", "https://")
        if not http_url.endswith(".turso.io"):
            http_url = http_url + ".turso.io"
        
        turso_client = create_client_sync(
            url=http_url,
            auth_token=TURSO_AUTH_TOKEN
        )
        print("✅ Turso client inicializado")
        return True
    except Exception as e:
        print(f"❌ Error inicializando Turso: {e}")
        return False

async def close_turso():
    """Cerrar cliente Turso"""
    global turso_client
    try:
        if turso_client:
            await turso_client.close()
        print("✅ Turso client cerrado")
    except Exception as e:
        print(f"⚠️ Error cerrando Turso: {e}")

def get_turso_client():
    """Obtener cliente Turso"""
    return turso_client

async def execute_query(query: str, parameters: list = None):
    """Ejecutar query en Turso"""
    if not turso_client:
        raise RuntimeError("Turso client not initialized")
    
    try:
        if parameters:
            result = turso_client.execute(query, parameters)
        else:
            result = turso_client.execute(query)
        return result
    except Exception as e:
        print(f"❌ Error ejecutando query: {e}")
        raise

async def create_tables():
    """Crear tablas en Turso"""
    try:
        # No necesitamos importar los modelos SQLAlchemy para Turso
        # Usamos SQL directo para crear las tablas
        
        # SQL para crear tablas (compatible con SQLite/Turso)
        create_empresas_sql = """
        CREATE TABLE IF NOT EXISTS empresas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo VARCHAR(20) UNIQUE NOT NULL,
            ruc VARCHAR(11) UNIQUE NOT NULL,
            razon_social VARCHAR(255) NOT NULL,
            nombre_comercial VARCHAR(255),
            email VARCHAR(100),
            telefono VARCHAR(20),
            celular VARCHAR(20),
            direccion TEXT,
            distrito VARCHAR(100),
            provincia VARCHAR(100),
            departamento VARCHAR(100),
            ubigeo VARCHAR(6),
            representante_legal VARCHAR(255),
            dni_representante VARCHAR(8),
            capital_social DECIMAL(15,2),
            fecha_constitucion DATE,
            estado VARCHAR(20) NOT NULL DEFAULT 'ACTIVO',
            tipo_empresa VARCHAR(50) NOT NULL,
            categoria_contratista VARCHAR(10),
            especialidades JSON,
            numero_registro_nacional VARCHAR(50),
            vigencia_registro_desde DATE,
            vigencia_registro_hasta DATE,
            observaciones TEXT,
            activo BOOLEAN NOT NULL DEFAULT 1,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER,
            updated_by INTEGER,
            version INTEGER NOT NULL DEFAULT 1
        );
        """
        
        create_representantes_sql = """
        CREATE TABLE IF NOT EXISTS empresa_representantes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa_id INTEGER NOT NULL,
            nombre VARCHAR(255) NOT NULL,
            cargo VARCHAR(100),
            tipo_documento VARCHAR(10) DEFAULT 'DNI',
            numero_documento VARCHAR(20) NOT NULL,
            participacion VARCHAR(50),
            fecha_desde DATE,
            fuente VARCHAR(20),
            es_principal BOOLEAN NOT NULL DEFAULT 0,
            estado VARCHAR(20) NOT NULL DEFAULT 'ACTIVO',
            activo BOOLEAN NOT NULL DEFAULT 1,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER,
            updated_by INTEGER,
            FOREIGN KEY (empresa_id) REFERENCES empresas (id)
        );
        """
        
        # Tabla de obras
        create_obras_sql = """
        CREATE TABLE IF NOT EXISTS obras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo VARCHAR(50) UNIQUE NOT NULL,
            nombre VARCHAR(500) NOT NULL,
            descripcion TEXT,
            empresa_id INTEGER NOT NULL,
            cliente VARCHAR(255),
            ubicacion TEXT,
            distrito VARCHAR(100),
            provincia VARCHAR(100),
            departamento VARCHAR(100),
            ubigeo VARCHAR(6),
            modalidad_ejecucion VARCHAR(50),
            sistema_contratacion VARCHAR(50),
            tipo_obra VARCHAR(100),
            monto_contractual DECIMAL(15,2),
            monto_adicionales DECIMAL(15,2) DEFAULT 0,
            monto_total DECIMAL(15,2),
            fecha_inicio DATE,
            fecha_fin_contractual DATE,
            fecha_fin_real DATE,
            plazo_contractual INTEGER,
            plazo_total INTEGER,
            estado_obra VARCHAR(50) NOT NULL DEFAULT 'PLANIFICADA',
            porcentaje_avance DECIMAL(5,2) DEFAULT 0,
            observaciones TEXT,
            activo BOOLEAN NOT NULL DEFAULT 1,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER,
            updated_by INTEGER,
            version INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY (empresa_id) REFERENCES empresas (id)
        );
        """
        
        # Tabla de valorizaciones
        create_valorizaciones_sql = """
        CREATE TABLE IF NOT EXISTS valorizaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo VARCHAR(50) UNIQUE NOT NULL,
            obra_id INTEGER NOT NULL,
            numero_valorizacion INTEGER NOT NULL,
            periodo VARCHAR(20) NOT NULL,
            fecha_inicio DATE NOT NULL,
            fecha_fin DATE NOT NULL,
            fecha_presentacion DATE,
            fecha_aprobacion DATE,
            tipo_valorizacion VARCHAR(50) NOT NULL DEFAULT 'MENSUAL',
            monto_ejecutado DECIMAL(15,2) NOT NULL DEFAULT 0,
            monto_materiales DECIMAL(15,2) DEFAULT 0,
            monto_mano_obra DECIMAL(15,2) DEFAULT 0,
            monto_equipos DECIMAL(15,2) DEFAULT 0,
            monto_subcontratos DECIMAL(15,2) DEFAULT 0,
            monto_gastos_generales DECIMAL(15,2) DEFAULT 0,
            monto_utilidad DECIMAL(15,2) DEFAULT 0,
            igv DECIMAL(15,2) DEFAULT 0,
            monto_total DECIMAL(15,2) NOT NULL DEFAULT 0,
            porcentaje_avance_periodo DECIMAL(5,2) DEFAULT 0,
            porcentaje_avance_acumulado DECIMAL(5,2) DEFAULT 0,
            estado_valorizacion VARCHAR(50) NOT NULL DEFAULT 'BORRADOR',
            observaciones TEXT,
            archivos_adjuntos JSON,
            metrado_ejecutado JSON,
            partidas_ejecutadas JSON,
            activo BOOLEAN NOT NULL DEFAULT 1,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER,
            updated_by INTEGER,
            version INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY (obra_id) REFERENCES obras (id),
            UNIQUE(obra_id, numero_valorizacion)
        );
        """
        
        # Crear índices
        create_indexes_sql = [
            # Índices para empresas
            "CREATE INDEX IF NOT EXISTS idx_empresas_ruc ON empresas(ruc);",
            "CREATE INDEX IF NOT EXISTS idx_empresas_codigo ON empresas(codigo);",
            "CREATE INDEX IF NOT EXISTS idx_empresas_razon_social ON empresas(razon_social);",
            
            # Índices para representantes
            "CREATE INDEX IF NOT EXISTS idx_representantes_empresa ON empresa_representantes(empresa_id);",
            "CREATE INDEX IF NOT EXISTS idx_representantes_documento ON empresa_representantes(numero_documento);",
            
            # Índices para obras
            "CREATE INDEX IF NOT EXISTS idx_obras_codigo ON obras(codigo);",
            "CREATE INDEX IF NOT EXISTS idx_obras_empresa ON obras(empresa_id);",
            "CREATE INDEX IF NOT EXISTS idx_obras_estado ON obras(estado_obra);",
            "CREATE INDEX IF NOT EXISTS idx_obras_fecha_inicio ON obras(fecha_inicio);",
            "CREATE INDEX IF NOT EXISTS idx_obras_cliente ON obras(cliente);",
            
            # Índices para valorizaciones  
            "CREATE INDEX IF NOT EXISTS idx_valorizaciones_obra ON valorizaciones(obra_id);",
            "CREATE INDEX IF NOT EXISTS idx_valorizaciones_periodo ON valorizaciones(periodo);",
            "CREATE INDEX IF NOT EXISTS idx_valorizaciones_estado ON valorizaciones(estado_valorizacion);",
            "CREATE INDEX IF NOT EXISTS idx_valorizaciones_fecha ON valorizaciones(fecha_inicio, fecha_fin);",
            "CREATE INDEX IF NOT EXISTS idx_valorizaciones_numero ON valorizaciones(obra_id, numero_valorizacion);"
        ]
        
        # Ejecutar creación de tablas
        await execute_query(create_empresas_sql)
        print("✅ Tabla 'empresas' creada")
        
        await execute_query(create_representantes_sql)
        print("✅ Tabla 'empresa_representantes' creada")
        
        await execute_query(create_obras_sql)
        print("✅ Tabla 'obras' creada")
        
        await execute_query(create_valorizaciones_sql)
        print("✅ Tabla 'valorizaciones' creada")
        
        # Crear índices
        for index_sql in create_indexes_sql:
            await execute_query(index_sql)
        
        print("✅ Índices creados")
        print("🎉 Schema completo de base de datos creado exitosamente en Turso")
        
    except Exception as e:
        print(f"❌ Error creando tablas: {e}")
        raise

async def init_database():
    """Inicializar base de datos completa"""
    try:
        # Inicializar cliente
        success = await init_turso()
        if not success:
            return False
        
        # Crear tablas
        await create_tables()
        
        print("🚀 Base de datos Turso inicializada completamente")
        return True
        
    except Exception as e:
        print(f"❌ Error inicializando base de datos: {e}")
        return False

async def close_database():
    """Cerrar base de datos"""
    await close_turso()

# Alias para compatibilidad
get_db_session = get_turso_client