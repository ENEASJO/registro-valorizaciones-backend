#!/usr/bin/env python3
"""
Probar conexión directa con libsql
"""
import os
from dotenv import load_dotenv
import libsql

load_dotenv()

def test_libsql_connection():
    """Probar diferentes formas de conectar con libsql"""
    
    url = os.getenv("TURSO_DATABASE_URL")
    token = os.getenv("TURSO_AUTH_TOKEN")
    
    print(f"URL: {url}")
    print(f"Token: {token[:50]}...")
    
    # Método 1: URL con parámetros
    try:
        conn_string = f"{url}?authToken={token}"
        print(f"🔗 Probando conexión: {conn_string}")
        
        conn = libsql.connect(conn_string)
        cursor = conn.cursor()
        cursor.execute("SELECT 1 as test")
        result = cursor.fetchone()
        print(f"✅ Método 1 funciona: {result}")
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Método 1 falló: {e}")
    
    # Método 2: Usando variables de entorno separadas
    try:
        os.environ['TURSO_DATABASE_URL'] = url
        os.environ['TURSO_AUTH_TOKEN'] = token
        
        conn = libsql.connect(url, auth_token=token)
        cursor = conn.cursor()
        cursor.execute("SELECT 1 as test")
        result = cursor.fetchone()
        print(f"✅ Método 2 funciona: {result}")
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Método 2 falló: {e}")
        
    # Método 3: Solo URL con variables de entorno set
    try:
        conn = libsql.connect(url)
        cursor = conn.cursor()
        cursor.execute("SELECT 1 as test")
        result = cursor.fetchone()
        print(f"✅ Método 3 funciona: {result}")
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Método 3 falló: {e}")
    
    return False

if __name__ == "__main__":
    success = test_libsql_connection()
    if not success:
        print("❌ Ningún método de conexión funcionó")