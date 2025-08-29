#!/usr/bin/env python3
"""
Script para crear tablas en Turso usando conexión HTTP
"""
import os
from dotenv import load_dotenv
from libsql_client import create_client_sync

load_dotenv()

def create_tables():
    """Crear tablas necesarias en Turso"""
    
    url = os.getenv("TURSO_DATABASE_URL")
    token = os.getenv("TURSO_AUTH_TOKEN")
    
    if not url or not token:
        print("❌ Variables de entorno faltantes")
        return False
    
    try:
        # Convertir a HTTPS para evitar WebSocket
        http_url = url.replace("libsql://", "https://")
        print(f"🔗 Conectando a: {http_url}")
        
        client = create_client_sync(url=http_url, auth_token=token)
        
        # SQL para crear tabla empresas simplificada
        create_empresas_sql = """
        CREATE TABLE IF NOT EXISTS empresas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ruc VARCHAR(11) UNIQUE NOT NULL,
            razon_social VARCHAR(255) NOT NULL,
            direccion TEXT,
            telefono VARCHAR(20),
            email VARCHAR(100),
            representante_legal VARCHAR(255),
            dni_representante VARCHAR(8),
            estado VARCHAR(20) DEFAULT 'ACTIVO',
            fuente_datos VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        print("📋 Creando tabla empresas...")
        client.execute(create_empresas_sql)
        print("✅ Tabla empresas creada")
        
        # Crear índices
        indices_sql = [
            "CREATE INDEX IF NOT EXISTS idx_empresas_ruc ON empresas(ruc)",
            "CREATE INDEX IF NOT EXISTS idx_empresas_razon_social ON empresas(razon_social)",
            "CREATE INDEX IF NOT EXISTS idx_empresas_estado ON empresas(estado)"
        ]
        
        print("📋 Creando índices...")
        for sql in indices_sql:
            client.execute(sql)
        print("✅ Índices creados")
        
        # Verificar tablas
        result = client.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in result.rows]
        print(f"📊 Tablas disponibles: {tables}")
        
        # Test insert
        test_sql = """
        INSERT OR IGNORE INTO empresas (ruc, razon_social, fuente_datos) 
        VALUES ('12345678901', 'EMPRESA DE PRUEBA S.A.C.', 'TEST')
        """
        client.execute(test_sql)
        
        # Verificar datos
        result = client.execute("SELECT COUNT(*) FROM empresas")
        count = result.rows[0][0]
        print(f"📊 Total empresas: {count}")
        
        # Test select
        result = client.execute("SELECT ruc, razon_social FROM empresas LIMIT 1")
        if result.rows:
            ruc, razon = result.rows[0]
            print(f"📋 Empresa de prueba: {ruc} - {razon}")
        
        client.close()
        print("🎉 Turso inicializado correctamente")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = create_tables()
    if success:
        print("✅ ¡Listo para usar Turso!")
    else:
        print("❌ Falló la inicialización")