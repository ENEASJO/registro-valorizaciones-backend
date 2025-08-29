#!/usr/bin/env python3
"""
Debug para entender las tablas de Turso
"""
import os
from dotenv import load_dotenv
import libsql

load_dotenv()

def debug_tablas():
    """Investigar las tablas y sus datos"""
    
    url = os.getenv("TURSO_DATABASE_URL")
    token = os.getenv("TURSO_AUTH_TOKEN")
    
    conn = libsql.connect(url, auth_token=token)
    cursor = conn.cursor()
    
    print("🔍 INVESTIGANDO BASE DE DATOS TURSO")
    
    # Ver todas las tablas
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"\n📊 Tablas disponibles: {[t[0] for t in tables]}")
    
    # Investigar tabla empresas
    print(f"\n🔍 TABLA EMPRESAS:")
    cursor.execute("SELECT COUNT(*) FROM empresas")
    total = cursor.fetchone()[0]
    print(f"   Total registros: {total}")
    
    # Ver los RUCs que tenemos
    cursor.execute("SELECT ruc, razon_social, created_at FROM empresas ORDER BY created_at DESC LIMIT 10")
    rucs = cursor.fetchall()
    print(f"\n📋 Últimos RUCs registrados:")
    for ruc_data in rucs:
        ruc, razon, created = ruc_data
        print(f"   {ruc} - {razon[:40]}... - {created}")
        
    # Buscar específicamente el RUC de nuestras pruebas
    test_rucs = ["20600074114", "20100070970"]
    for test_ruc in test_rucs:
        cursor.execute("SELECT * FROM empresas WHERE ruc = ?", [test_ruc])
        result = cursor.fetchone()
        if result:
            print(f"\n✅ {test_ruc} ENCONTRADO:")
            cursor.execute("PRAGMA table_info(empresas)")
            columns = [col[1] for col in cursor.fetchall()]
            empresa_dict = dict(zip(columns, result))
            print(f"   ID: {empresa_dict.get('id')}")
            print(f"   Código: {empresa_dict.get('codigo')}")
            print(f"   Razón Social: {empresa_dict.get('razon_social')}")
            print(f"   Estado: {empresa_dict.get('estado')}")
            print(f"   Created: {empresa_dict.get('created_at')}")
        else:
            print(f"\n❌ {test_ruc} NO encontrado")
    
    conn.close()

if __name__ == "__main__":
    debug_tablas()