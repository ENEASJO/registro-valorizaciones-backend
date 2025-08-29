#!/usr/bin/env python3
"""
Debug del objeto result de Turso
"""
import os
from dotenv import load_dotenv
from libsql_client import create_client_sync

load_dotenv()

def debug_result():
    """Investigar propiedades del objeto result"""
    
    url = os.getenv("TURSO_DATABASE_URL")
    token = os.getenv("TURSO_AUTH_TOKEN")
    
    http_url = url.replace("libsql://", "https://")
    client = create_client_sync(url=http_url, auth_token=token)
    
    # Test insert
    sql = "INSERT INTO empresas (ruc, razon_social, fuente_datos) VALUES (?, ?, ?)"
    result = client.execute(sql, ["99999999999", "TEST EMPRESA", "DEBUG"])
    
    print(f"Tipo de result: {type(result)}")
    print(f"Atributos disponibles: {dir(result)}")
    
    # Probar diferentes formas de obtener el ID
    try:
        print(f"result.last_insert_rowid: {result.last_insert_rowid}")
    except:
        print("No tiene last_insert_rowid")
    
    try:
        print(f"result.lastInsertRowid: {result.lastInsertRowid}")
    except:
        print("No tiene lastInsertRowid")
    
    try:
        print(f"result.rowcount: {result.rowcount}")
    except:
        print("No tiene rowcount")
        
    try:
        print(f"result.rows: {result.rows}")
    except:
        print("No tiene rows")
        
    client.close()

if __name__ == "__main__":
    debug_result()