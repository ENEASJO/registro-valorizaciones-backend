#!/usr/bin/env python3
"""
Script para probar la misma consulta SQL que usa el servicio (integración manual).
Marcado como prueba de integración para excluirlo del CI por defecto.
"""

import pytest
pytestmark = pytest.mark.integration

import psycopg2
from psycopg2.extras import RealDictCursor
import os

# Connection string exactamente como la usa el servicio
import os
conn_str = os.environ.get('NEON_CONNECTION_STRING')
if not conn_str:
    raise RuntimeError('NEON_CONNECTION_STRING is not set. Configure it before running this integration script.')

def test_sql_query():
    """Probar la consulta exacta que usa listar_empresas"""
    try:
        conn = psycopg2.connect(conn_str, cursor_factory=RealDictCursor)
        with conn.cursor() as cursor:
            # La misma consulta que usa el servicio
            query = """
                SELECT * FROM empresas
                ORDER BY created_at DESC
                LIMIT %s;
            """

            limit = 100
            print(f"🔍 Ejecutando query con limit={limit}")
            cursor.execute(query, (limit,))
            empresas = cursor.fetchall()

            print(f"📋 Empresas obtenidas: {len(empresas)}")

            if empresas:
                print("\n📊 Primera empresa encontrada:")
                emp = empresas[0]
                for key, value in emp.items():
                    print(f"   {key}: {value}")
            else:
                print("⚠️ No se encontraron empresas")

            # Verificar si hay algún error en la conexión
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            print(f"\n🔗 Versión de PostgreSQL: {version['version'][:50]}...")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_sql_query()
