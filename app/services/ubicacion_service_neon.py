"""
Servicio de ubicaciones para Neon PostgreSQL usando psycopg2
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Any, Optional

# Obtener URL de conexión a Neon
NEON_CONNECTION_STRING = os.getenv("NEON_CONNECTION_STRING")

def obtener_ubicaciones(tipo: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Obtiene todas las ubicaciones activas, opcionalmente filtradas por tipo.

    Args:
        tipo: Tipo de ubicación para filtrar (URBANA, CENTRO_POBLADO, CASERIO)

    Returns:
        Lista de ubicaciones
    """
    conn = psycopg2.connect(NEON_CONNECTION_STRING)

    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Construir query con filtro opcional
        if tipo:
            query = """
                SELECT id, nombre, tipo, departamento, provincia, distrito
                FROM ubicaciones
                WHERE activo = TRUE AND tipo = %s
                ORDER BY tipo ASC, nombre ASC
            """
            cursor.execute(query, (tipo,))
        else:
            query = """
                SELECT id, nombre, tipo, departamento, provincia, distrito
                FROM ubicaciones
                WHERE activo = TRUE
                ORDER BY tipo ASC, nombre ASC
            """
            cursor.execute(query)

        rows = cursor.fetchall()

        # Convertir a lista de diccionarios
        ubicaciones = [dict(row) for row in rows]

        cursor.close()
        return ubicaciones

    finally:
        conn.close()


def obtener_ubicaciones_agrupadas() -> Dict[str, List[Dict[str, Any]]]:
    """
    Obtiene ubicaciones activas agrupadas por tipo.

    Returns:
        Diccionario con ubicaciones agrupadas:
        {
            "urbana": [...],
            "centro_poblado": [...],
            "caserio": [...]
        }
    """
    conn = psycopg2.connect(NEON_CONNECTION_STRING)

    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        query = """
            SELECT id, nombre, tipo, departamento, provincia, distrito
            FROM ubicaciones
            WHERE activo = TRUE
            ORDER BY nombre ASC
        """

        cursor.execute(query)
        rows = cursor.fetchall()

        # Agrupar por tipo
        urbana = []
        centro_poblado = []
        caserio = []

        for row in rows:
            tipo_upper = (row['tipo'] or '').upper()
            ubicacion_data = {
                "id": str(row['id']),
                "nombre": row['nombre'],
                "tipo": row['tipo'].lower() if row['tipo'] else '',
                "departamento": row['departamento'],
                "provincia": row['provincia'],
                "distrito": row['distrito']
            }

            if tipo_upper == 'URBANA' or tipo_upper == 'ZONA_URBANA':
                urbana.append(ubicacion_data)
            elif tipo_upper == 'CENTRO_POBLADO':
                centro_poblado.append(ubicacion_data)
            elif tipo_upper == 'CASERIO':
                caserio.append(ubicacion_data)

        cursor.close()

        return {
            "urbana": urbana,
            "centro_poblado": centro_poblado,
            "caserio": caserio
        }

    finally:
        conn.close()
