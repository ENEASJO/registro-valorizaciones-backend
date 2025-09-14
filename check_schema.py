#!/usr/bin/env python3
"""
Script para verificar el schema de la base de datos
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import os

# Connection string - reemplazar con la real
conn_str = "postgresql://neondb_owner:npg_puYoPelF96Hd@ep-fancy-river-acd46jxk-pooler.sa-east-1.aws.neon.tech/neondb?sslmode=require"

def check_empresas_schema():
    """Verificar el schema de la tabla empresas"""
    try:
        conn = psycopg2.connect(conn_str, cursor_factory=RealDictCursor)
        with conn.cursor() as cursor:
            # Obtener información de las columnas
            cursor.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_name = 'empresas'
                ORDER BY ordinal_position;
            """)

            columns = cursor.fetchall()

            print("Schema de la tabla 'empresas':")
            print("-" * 50)
            for col in columns:
                print(f"{col['column_name']:<25} {col['data_type']:<15} {col['is_nullable']:<10} {col['column_default'] or ''}")

    except Exception as e:
        print(f"Error: {e}")

def test_simple_insert():
    """Probar un insert simple"""
    try:
        conn = psycopg2.connect(conn_str, cursor_factory=RealDictCursor)
        with conn.cursor() as cursor:
            # Intentar insertar con los campos mínimos
            test_data = {
                'codigo': 'TEST001',
                'ruc': '99999999999',  # RUC de prueba
                'razon_social': 'EMPRESA DE PRUEBA'
            }

            query = """
                INSERT INTO empresas (codigo, ruc, razon_social)
                VALUES (%(codigo)s, %(ruc)s, %(razon_social)s)
                RETURNING id;
            """

            cursor.execute(query, test_data)
            result = cursor.fetchone()
            empresa_id = result['id']

            conn.commit()
            print(f"\n✅ Insert test exitoso! ID: {empresa_id}")

            # Limpiar
            cursor.execute("DELETE FROM empresas WHERE ruc = '99999999999'")
            conn.commit()
            print("🧹 Registro de prueba eliminado")

    except Exception as e:
        print(f"\n❌ Error en insert test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_empresas_schema()
    test_simple_insert()