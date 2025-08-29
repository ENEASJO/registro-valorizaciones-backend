#!/usr/bin/env python3
"""
Script para inicializar la base de datos Turso con las tablas necesarias
"""
import asyncio
import os
import sys
from pathlib import Path

# Add the app directory to the Python path
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

from app.core.database_turso import get_turso_config
from libsql_client import create_client

async def create_tables():
    """Crear todas las tablas necesarias en Turso"""
    
    # Get Turso configuration
    url, token = get_turso_config()
    if not url or not token:
        print("❌ Configuración de Turso incompleta")
        print("Ejecuta: turso db tokens create registro-de-valorizaciones")
        print("Luego actualiza TURSO_AUTH_TOKEN en .env")
        return False
    
    try:
        # Create client
        client = create_client(url=url, auth_token=token)
        
        print("🔗 Conectando a Turso...")
        
        # SQL para crear tabla empresas
        create_empresas_sql = """
        CREATE TABLE IF NOT EXISTS empresas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo VARCHAR(20) UNIQUE NOT NULL,
            ruc VARCHAR(11) UNIQUE NOT NULL,
            razon_social VARCHAR(255) NOT NULL,
            nombre_comercial VARCHAR(255),
            
            -- Datos de contacto
            email VARCHAR(100),
            telefono VARCHAR(20),
            celular VARCHAR(20),
            direccion TEXT,
            distrito VARCHAR(100),
            provincia VARCHAR(100),
            departamento VARCHAR(100),
            ubigeo VARCHAR(6),
            
            -- Datos legales y financieros
            representante_legal VARCHAR(255),
            dni_representante VARCHAR(8),
            capital_social DECIMAL(15,2),
            fecha_constitucion DATE,
            
            -- Estados y clasificación
            estado VARCHAR(20) NOT NULL DEFAULT 'ACTIVO',
            tipo_empresa VARCHAR(50) NOT NULL,
            categoria_contratista VARCHAR(10),
            
            -- Especialidades (JSON como TEXT)
            especialidades TEXT,
            
            -- Documentos y certificaciones
            numero_registro_nacional VARCHAR(50),
            vigencia_registro_desde DATE,
            vigencia_registro_hasta DATE,
            
            -- Datos adicionales SUNAT/OSCE
            condicion_domicilio VARCHAR(50),
            estado_contribuyente VARCHAR(50),
            ubigeo_sunat VARCHAR(6),
            tipo_via VARCHAR(50),
            nombre_via VARCHAR(200),
            codigo_zona VARCHAR(10),
            tipo_zona VARCHAR(50),
            numero_via VARCHAR(20),
            interior VARCHAR(20),
            lote VARCHAR(20),
            departamento_direccion VARCHAR(20),
            manzana VARCHAR(20),
            kilometro VARCHAR(20),
            
            -- Metadatos
            fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            fuente_datos VARCHAR(50),
            datos_completos BOOLEAN DEFAULT FALSE,
            
            -- Indices
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        # SQL para crear tabla representantes
        create_representantes_sql = """
        CREATE TABLE IF NOT EXISTS representantes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa_id INTEGER NOT NULL,
            tipo_documento VARCHAR(10) NOT NULL DEFAULT 'DNI',
            numero_documento VARCHAR(20) NOT NULL,
            nombres VARCHAR(255) NOT NULL,
            apellido_paterno VARCHAR(100),
            apellido_materno VARCHAR(100),
            nombre_completo VARCHAR(255),
            cargo VARCHAR(100),
            desde DATE,
            vigente BOOLEAN DEFAULT TRUE,
            
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (empresa_id) REFERENCES empresas(id)
        );
        """
        
        # SQL para crear índices
        create_indexes_sql = """
        CREATE INDEX IF NOT EXISTS idx_empresas_ruc ON empresas(ruc);
        CREATE INDEX IF NOT EXISTS idx_empresas_codigo ON empresas(codigo);
        CREATE INDEX IF NOT EXISTS idx_empresas_razon_social ON empresas(razon_social);
        CREATE INDEX IF NOT EXISTS idx_empresas_estado ON empresas(estado);
        CREATE INDEX IF NOT EXISTS idx_representantes_empresa ON representantes(empresa_id);
        CREATE INDEX IF NOT EXISTS idx_representantes_documento ON representantes(numero_documento);
        """
        
        print("📋 Creando tabla empresas...")
        await client.execute(create_empresas_sql)
        print("✅ Tabla empresas creada")
        
        print("📋 Creando tabla representantes...")
        await client.execute(create_representantes_sql)
        print("✅ Tabla representantes creada")
        
        print("📋 Creando índices...")
        for index_sql in create_indexes_sql.strip().split(';'):
            if index_sql.strip():
                await client.execute(index_sql.strip())
        print("✅ Índices creados")
        
        # Verificar tablas creadas
        result = await client.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in result.rows]
        print(f"📊 Tablas creadas: {tables}")
        
        await client.close()
        print("🎉 Base de datos Turso inicializada correctamente")
        return True
        
    except Exception as e:
        print(f"❌ Error inicializando Turso: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(create_tables())
    if success:
        print("✅ Proceso completado exitosamente")
    else:
        print("❌ Proceso falló")
        sys.exit(1)