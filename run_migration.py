#!/usr/bin/env python3
"""Ejecutar migración de tabla mef_cache"""
import asyncio
import os
from dotenv import load_dotenv
from databases import Database

load_dotenv()

async def main():
    database_url = os.getenv("NEON_DATABASE_URL")
    if not database_url:
        print("❌ NEON_DATABASE_URL no encontrada")
        return

    database = Database(database_url)

    try:
        await database.connect()
        print("✅ Conectado a base de datos")

        # Crear tabla mef_cache
        await database.execute("""
            CREATE TABLE IF NOT EXISTS mef_cache (
                cui VARCHAR(20) PRIMARY KEY,
                datos_mef JSONB NOT NULL,
                fecha_scraping TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                ultima_actualizacion TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """)
        print("✅ Tabla mef_cache creada")

        # Crear índice
        await database.execute("""
            CREATE INDEX IF NOT EXISTS idx_mef_cache_fecha
            ON mef_cache(fecha_scraping DESC)
        """)
        print("✅ Índice creado")

        print("\n✅ Migración completada exitosamente")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await database.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
