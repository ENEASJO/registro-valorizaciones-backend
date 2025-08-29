#!/usr/bin/env python3
"""
Verificar estructura actual de la tabla empresas
"""
import os
from dotenv import load_dotenv
import libsql

load_dotenv()

def check_table_structure():
    """Verificar estructura de tabla empresas"""
    
    url = os.getenv("TURSO_DATABASE_URL")
    token = os.getenv("TURSO_AUTH_TOKEN")
    
    conn = libsql.connect(url, auth_token=token)
    cursor = conn.cursor()
    
    # Ver todas las tablas
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"📊 Tablas disponibles: {[t[0] for t in tables]}")
    
    # Ver estructura de tabla empresas
    cursor.execute("PRAGMA table_info(empresas)")
    columns = cursor.fetchall()
    print(f"📋 Columnas en tabla empresas:")
    for col in columns:
        print(f"   - {col[1]} ({col[2]}) {'NOT NULL' if col[3] else ''}")
    
    # Ver datos de ejemplo
    cursor.execute("SELECT * FROM empresas LIMIT 3")
    rows = cursor.fetchall()
    print(f"📋 Registros de ejemplo: {len(rows)} filas")
    for row in rows:
        print(f"   {row}")
    
    conn.close()

if __name__ == "__main__":
    check_table_structure()