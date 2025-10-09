"""
Configuración de la base de datos
"""
import os
from typing import AsyncGenerator
try:
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
except ImportError:
    # Fallback para versiones anteriores de SQLAlchemy
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    async_sessionmaker = sessionmaker
from sqlalchemy.orm import declarative_base
from databases import Database
from app.core.config import settings

# Database URL con soporte async - Prioritiza Neon
# Revisar múltiples variables de entorno en orden de prioridad
NEON_CONNECTION_STRING = os.getenv("NEON_CONNECTION_STRING")
NEON_DATABASE_URL = os.getenv("NEON_DATABASE_URL")
DATABASE_URL = os.getenv("DATABASE_URL")

print(f"[STARTUP] NEON_CONNECTION_STRING: {NEON_CONNECTION_STRING[:100] if NEON_CONNECTION_STRING else 'None'}...")
print(f"[STARTUP] NEON_DATABASE_URL: {NEON_DATABASE_URL[:100] if NEON_DATABASE_URL else 'None'}...")
print(f"[STARTUP] DATABASE_URL inicial: {DATABASE_URL[:100] if DATABASE_URL else 'None'}...")

# Prioritizar NEON_DATABASE_URL sobre NEON_CONNECTION_STRING
# Mantener dos variables: una para SQLAlchemy (+asyncpg) y otra para databases library (pura)
DATABASE_URL_RAW = None  # Para databases library (formato puro)
DATABASE_URL_SQLALCHEMY = None  # Para SQLAlchemy (con +asyncpg)

if NEON_DATABASE_URL:
    print("[STARTUP] Usando NEON_DATABASE_URL")
    DATABASE_URL_RAW = NEON_DATABASE_URL
    if NEON_DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL_SQLALCHEMY = NEON_DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
    else:
        DATABASE_URL_SQLALCHEMY = NEON_DATABASE_URL
elif NEON_CONNECTION_STRING:
    print("[STARTUP] Usando NEON_CONNECTION_STRING")
    # Limpiar posibles prefijos de comando psql y comillas
    connection_str = NEON_CONNECTION_STRING.strip()
    print(f"[STARTUP] connection_str después de strip: {connection_str[:100]}...")

    if connection_str.startswith("psql "):
        print("[STARTUP] Removiendo prefijo 'psql '")
        connection_str = connection_str[5:].strip()  # Remover "psql "

    connection_str = connection_str.strip("'\"")  # Remover comillas
    print(f"[STARTUP] connection_str después de limpiar comillas: {connection_str[:100]}...")

    # Convertir PostgreSQL connection string a async
    DATABASE_URL_RAW = connection_str
    if connection_str.startswith("postgresql://"):
        DATABASE_URL_SQLALCHEMY = connection_str.replace("postgresql://", "postgresql+asyncpg://")
        print(f"[STARTUP] DATABASE_URL_SQLALCHEMY convertida a asyncpg: {DATABASE_URL_SQLALCHEMY[:100]}...")
    else:
        DATABASE_URL_SQLALCHEMY = connection_str
        print(f"[STARTUP] DATABASE_URL_SQLALCHEMY sin conversión: {DATABASE_URL_SQLALCHEMY[:100]}...")
elif DATABASE_URL:
    DATABASE_URL_RAW = DATABASE_URL
    DATABASE_URL_SQLALCHEMY = DATABASE_URL
else:
    DATABASE_URL_RAW = "sqlite+aiosqlite:///./valoraciones.db"
    DATABASE_URL_SQLALCHEMY = "sqlite+aiosqlite:///./valoraciones.db"
    print("[STARTUP] Usando SQLite como fallback")

# DATABASE_URL apunta a la versión SQLAlchemy por compatibilidad
DATABASE_URL = DATABASE_URL_SQLALCHEMY

print(f"[STARTUP] DATABASE_URL_RAW (databases lib): {DATABASE_URL_RAW[:100] if DATABASE_URL_RAW else 'None'}...")
print(f"[STARTUP] DATABASE_URL_SQLALCHEMY: {DATABASE_URL_SQLALCHEMY[:100] if DATABASE_URL_SQLALCHEMY else 'None'}...")

# Motor async de SQLAlchemy
engine = create_async_engine(
    DATABASE_URL,
    echo=settings.DEBUG,  # Log SQL queries en debug mode
    pool_pre_ping=True,   # Verificar conexiones antes de usar
    pool_recycle=300,     # Reciclar conexiones cada 5 minutos
)

# Session maker async
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Database instance para operaciones raw SQL si es necesario
# IMPORTANTE: usar DATABASE_URL_RAW (sin +asyncpg) para databases library
database = Database(DATABASE_URL_RAW)

# Base para modelos
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency para obtener sesión de base de datos
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

# Alias para compatibilidad
get_db = get_db_session

async def init_database():
    """
    Inicializar la base de datos y crear tablas si no existen
    """
    try:
        # Importar todos los modelos para asegurar que las tablas se creen
        from app.models.empresa import EmpresaDB, RepresentanteDB
        from app.models.ubicacion import UbicacionDB  # Asegurar creación de tabla ubicaciones
        
        # Crear todas las tablas
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            
        print("[OK] Base de datos inicializada correctamente")
        
    except Exception as e:
        print(f"[ERROR] Error inicializando base de datos: {e}")
        raise

async def close_database():
    """
    Cerrar conexiones de base de datos
    """
    try:
        await engine.dispose()
        if database.is_connected:
            await database.disconnect()
        print("[OK] Conexiones de base de datos cerradas")
    except Exception as e:
        print(f"[WARNING] Error cerrando base de datos: {e}")

# Context manager para transacciones
class DatabaseTransaction:
    def __init__(self):
        self.session: AsyncSession = None
    
    async def __aenter__(self) -> AsyncSession:
        self.session = async_session_maker()
        return self.session
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            await self.session.rollback()
        else:
            await self.session.commit()
        await self.session.close()

# Función de utilidad para ejecutar en transacción
async def execute_in_transaction(func, *args, **kwargs):
    """
    Ejecutar función en una transacción
    """
    async with DatabaseTransaction() as session:
        return await func(session, *args, **kwargs)

# Función para obtener la URL de la base de datos (requerida por algunos servicios)
def get_database_url() -> str:
    """
    Obtener la URL de la base de datos configurada

    Returns:
        str: URL de conexión a la base de datos (formato asyncpg puro)
    """
    # Convertir de vuelta a formato asyncpg puro si tiene +asyncpg
    url = DATABASE_URL
    print(f"[DEBUG] DATABASE_URL original: {url[:80] if url else 'None'}...")
    if url and '+asyncpg://' in url:
        url = url.replace('postgresql+asyncpg://', 'postgresql://')
        print(f"[DEBUG] URL después de conversión: {url[:80]}...")
    return url
