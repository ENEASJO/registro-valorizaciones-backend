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
NEON_CONNECTION_STRING = os.getenv("NEON_CONNECTION_STRING")
DATABASE_URL = os.getenv("DATABASE_URL")

if NEON_CONNECTION_STRING:
    # Convertir PostgreSQL connection string a async
    if NEON_CONNECTION_STRING.startswith("postgresql://"):
        DATABASE_URL = NEON_CONNECTION_STRING.replace("postgresql://", "postgresql+asyncpg://")
    else:
        DATABASE_URL = NEON_CONNECTION_STRING
elif not DATABASE_URL:
    DATABASE_URL = "sqlite+aiosqlite:///./valoraciones.db"

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
database = Database(DATABASE_URL)

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
            
        print("✅ Base de datos inicializada correctamente")
        
    except Exception as e:
        print(f"❌ Error inicializando base de datos: {e}")
        raise

async def close_database():
    """
    Cerrar conexiones de base de datos
    """
    try:
        await engine.dispose()
        if database.is_connected:
            await database.disconnect()
        print("✅ Conexiones de base de datos cerradas")
    except Exception as e:
        print(f"⚠️ Error cerrando base de datos: {e}")

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