import os
import psycopg2
from psycopg2.extras import execute_values

CENTROS_POBLADOS = [
  'PICHIU SAN PEDRO',
  'PICHIU QUINHUARAGRA',
  'SANTA CRUZ DE MOSNA',
  'QUINHUARAGRA',
  'CHALLHUAYACO',
  'LA MERCED DE GAUCHO',
  'RANCAS',
  'SAN ANDRES DE RUNTU',
  'SAN LUIS DE PUJUN',
  'SAN PEDRO DE CARASH',
  'CARHUAYOC',
  'SAN MIGUEL DE OPAYACO',
  'HUARIPAMPA',
  'HUARIPAMPA ALTO',
  'AYASH HUARIPAMPA',
]

CASERIOS_INDEPENDIENTES = [
  'MULLIPAMPA',
  'MULLIPATAC',
  'HUARCON - TINYAYOC (QUISHU)',
  'QUISHU',
  'CASERIO DE VISTA ALEGRE',
  'CASERIO DE CHUYO',
  'CASHAPATAC',
  'OPAYACO',
  'AYASH HUAMANIN',
  'HUANCHA',
  'BADO',
]

DDL = """
CREATE TABLE IF NOT EXISTS ubicaciones (
  id SERIAL PRIMARY KEY,
  nombre VARCHAR(200) NOT NULL,
  tipo VARCHAR(50) NOT NULL,
  departamento VARCHAR(100) NOT NULL DEFAULT 'Áncash',
  provincia VARCHAR(100) NOT NULL DEFAULT 'Huari',
  distrito VARCHAR(100) NOT NULL DEFAULT 'San Marcos',
  activo BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE UNIQUE INDEX IF NOT EXISTS ux_ubicaciones_nombre ON ubicaciones(nombre);
"""

UPSERT_SQL = """
INSERT INTO ubicaciones (nombre, tipo, departamento, provincia, distrito)
VALUES %s
ON CONFLICT (nombre) DO UPDATE SET
  tipo = EXCLUDED.tipo,
  departamento = EXCLUDED.departamento,
  provincia = EXCLUDED.provincia,
  distrito = EXCLUDED.distrito,
  updated_at = NOW();
"""

def main():
    conn_str = os.getenv("NEON_CONNECTION_STRING")
    if not conn_str:
        raise RuntimeError("NEON_CONNECTION_STRING no está definido")

    conn = psycopg2.connect(conn_str)
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute(DDL)
            values = []
            for n in CENTROS_POBLADOS:
                values.append((n, 'CENTRO_POBLADO', 'Áncash', 'Huari', 'San Marcos'))
            for n in CASERIOS_INDEPENDIENTES:
                values.append((n, 'CASERIO', 'Áncash', 'Huari', 'San Marcos'))
            execute_values(cur, UPSERT_SQL, values)
            print(f"✅ Seed completado. Registros: {len(values)}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()