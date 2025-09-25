#!/usr/bin/env python3
"""
Script para probar la conexión a Neon PostgreSQL (integración manual).
Marcado como prueba de integración para excluirlo del CI por defecto.
"""

import pytest
pytestmark = pytest.mark.integration


def main():
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor
        
import os
connection_string = os.environ.get('NEON_CONNECTION_STRING')
if not connection_string:
    raise RuntimeError('NEON_CONNECTION_STRING is not set. Configure it before running this integration script.')
        
        print("🔗 Intentando conectar a Neon...")
        conn = psycopg2.connect(connection_string, cursor_factory=RealDictCursor)
        cursor = conn.cursor()
        
        # Obtener versión
        cursor.execute('SELECT version();')
        version = cursor.fetchone()
        print('✅ Conexión exitosa a Neon!')
        print('Versión PostgreSQL:', version['version'][:100])
        
        # Base de datos actual
        cursor.execute('SELECT current_database();')
        db_name = cursor.fetchone()
        print('Base de datos actual:', db_name['current_database'])
        
        # Listar tablas existentes
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        tables = cursor.fetchall()
        print('\nTablas en la base de datos:')
        for table in tables:
            print(f'  - {table["table_name"]}')
        
        # Si hay tablas, mostrar información de una de ellas
        if tables:
            tabla_ejemplo = tables[0]["table_name"]
            cursor.execute(f"""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = %s
                ORDER BY ordinal_position;
            """, (tabla_ejemplo,))
            columns = cursor.fetchall()
            print(f'\nColumnas de la tabla "{tabla_ejemplo}":')
            for col in columns:
                print(f'  - {col["column_name"]}: {col["data_type"]} (Nullable: {col["is_nullable"]})')
        
        cursor.close()
        conn.close()
        print("\n✅ Prueba de conexión completada exitosamente")
        
    except Exception as e:
        print('❌ Error conectando a Neon:', str(e))
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
