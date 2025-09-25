#!/usr/bin/env python3
"""
Script para verificar directamente en Neon qué empresas existen
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import os

# Connection string del servicio
conn_str = "postgresql://neondb_owner:npg_puYoPelF96Hd@ep-fancy-river-acd46jxk-pooler.sa-east-1.aws.neon.tech/neondb?sslmode=require"

def verificar_empresas():
    """Verificar empresas directamente en Neon"""
    try:
        conn = psycopg2.connect(conn_str, cursor_factory=RealDictCursor)
        with conn.cursor() as cursor:
            # 1. Contar total de empresas
            cursor.execute("SELECT COUNT(*) as total FROM empresas;")
            result = cursor.fetchone()
            print(f"📊 Total de empresas en la tabla: {result['total']}")

            # 2. Listar todas las empresas sin límite
            cursor.execute("SELECT id, ruc, razon_social, created_at FROM empresas ORDER BY created_at DESC;")
            empresas = cursor.fetchall()

            print(f"\n📋 Lista de empresas ({len(empresas)}):")
            for emp in empresas:
                print(f"   ID: {emp['id']}")
                print(f"   RUC: {emp['ruc']}")
                print(f"   Razón Social: {emp['razon_social']}")
                print(f"   Creado: {emp['created_at']}")
                print("   ---")

            # 3. Verificar la tabla completa
            cursor.execute("SELECT * FROM empresas;")
            todas = cursor.fetchall()
            print(f"\n🔍 Todas las columnas de la primera empresa:")
            if todas:
                for key, value in todas[0].items():
                    print(f"   {key}: {value}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verificar_empresas()