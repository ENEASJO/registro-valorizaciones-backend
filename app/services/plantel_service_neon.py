"""
Servicio de plantel profesional para Neon PostgreSQL usando psycopg2
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Any, Optional
from uuid import uuid4

def get_connection_string():
    """
    Obtiene la connection string de Neon y elimina parámetros incompatibles con psycopg2
    """
    conn_str = os.getenv("NEON_CONNECTION_STRING")

    if not conn_str:
        return "postgresql://neondb_owner:npg_puYoPelF96Hd@ep-fancy-river-acd46jxk-pooler.sa-east-1.aws.neon.tech/neondb?sslmode=require"

    if "channel_binding=require" in conn_str:
        conn_str = conn_str.replace("channel_binding=require&", "")
        conn_str = conn_str.replace("&channel_binding=require", "")
        conn_str = conn_str.replace("channel_binding=require", "")

    return conn_str

NEON_CONNECTION_STRING = get_connection_string()

def obtener_plantel_por_obra(obra_id: str) -> List[Dict[str, Any]]:
    """
    Obtiene todos los profesionales del plantel de una obra específica.

    Args:
        obra_id: UUID de la obra

    Returns:
        Lista de profesionales del plantel
    """
    conn = psycopg2.connect(NEON_CONNECTION_STRING)

    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        query = """
            SELECT id, obra_id, nombres, apellidos, cargo_categoria, cargo_tecnico, fecha_registro
            FROM plantel_profesional
            WHERE obra_id = %s AND activo = TRUE
            ORDER BY cargo_categoria ASC, apellidos ASC
        """

        cursor.execute(query, (obra_id,))
        rows = cursor.fetchall()

        plantel = [dict(row) for row in rows]

        cursor.close()
        return plantel

    finally:
        conn.close()


def agregar_profesional(
    obra_id: str,
    nombres: str,
    apellidos: str,
    cargo_categoria: str,
    cargo_tecnico: str
) -> Dict[str, Any]:
    """
    Agrega un nuevo profesional al plantel de una obra.

    Args:
        obra_id: UUID de la obra
        nombres: Nombres del profesional
        apellidos: Apellidos del profesional
        cargo_categoria: Categoría del cargo
        cargo_tecnico: Cargo técnico específico

    Returns:
        Datos del profesional creado
    """
    conn = psycopg2.connect(NEON_CONNECTION_STRING)

    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        query = """
            INSERT INTO plantel_profesional
            (id, obra_id, nombres, apellidos, cargo_categoria, cargo_tecnico)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id, obra_id, nombres, apellidos, cargo_categoria, cargo_tecnico, fecha_registro
        """

        profesional_id = str(uuid4())
        cursor.execute(query, (profesional_id, obra_id, nombres, apellidos, cargo_categoria, cargo_tecnico))

        row = cursor.fetchone()
        conn.commit()

        profesional = dict(row) if row else None

        cursor.close()
        return profesional

    finally:
        conn.close()


def actualizar_profesional(
    profesional_id: str,
    nombres: Optional[str] = None,
    apellidos: Optional[str] = None,
    cargo_categoria: Optional[str] = None,
    cargo_tecnico: Optional[str] = None
) -> Dict[str, Any]:
    """
    Actualiza los datos de un profesional del plantel.

    Args:
        profesional_id: UUID del profesional
        nombres: Nuevos nombres (opcional)
        apellidos: Nuevos apellidos (opcional)
        cargo_categoria: Nueva categoría (opcional)
        cargo_tecnico: Nuevo cargo (opcional)

    Returns:
        Datos actualizados del profesional
    """
    conn = psycopg2.connect(NEON_CONNECTION_STRING)

    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Construir query dinámicamente solo con campos proporcionados
        updates = []
        params = []

        if nombres is not None:
            updates.append("nombres = %s")
            params.append(nombres)

        if apellidos is not None:
            updates.append("apellidos = %s")
            params.append(apellidos)

        if cargo_categoria is not None:
            updates.append("cargo_categoria = %s")
            params.append(cargo_categoria)

        if cargo_tecnico is not None:
            updates.append("cargo_tecnico = %s")
            params.append(cargo_tecnico)

        if not updates:
            # No hay nada que actualizar
            cursor.close()
            return None

        params.append(profesional_id)

        query = f"""
            UPDATE plantel_profesional
            SET {', '.join(updates)}
            WHERE id = %s AND activo = TRUE
            RETURNING id, obra_id, nombres, apellidos, cargo_categoria, cargo_tecnico, fecha_registro
        """

        cursor.execute(query, params)
        row = cursor.fetchone()
        conn.commit()

        profesional = dict(row) if row else None

        cursor.close()
        return profesional

    finally:
        conn.close()


def eliminar_profesional(profesional_id: str) -> bool:
    """
    Elimina (desactiva) un profesional del plantel.

    Args:
        profesional_id: UUID del profesional

    Returns:
        True si se eliminó correctamente, False en caso contrario
    """
    conn = psycopg2.connect(NEON_CONNECTION_STRING)

    try:
        cursor = conn.cursor()

        query = """
            UPDATE plantel_profesional
            SET activo = FALSE
            WHERE id = %s
        """

        cursor.execute(query, (profesional_id,))
        conn.commit()

        affected = cursor.rowcount > 0

        cursor.close()
        return affected

    finally:
        conn.close()


# Catálogo de cargos técnicos
CARGOS_TECNICOS = {
    "Supervisión y Gestión de Obra": [
        "SUPERVISOR DE OBRA",
        "INGENIERO SUPERVISOR DE OBRA",
        "JEFE DE SUPERVISIÓN",
        "RESIDENTE DE OBRA",
        "INGENIERO RESIDENTE DE OBRA"
    ],
    "Estructuras y Construcción": [
        "ESPECIALISTA EN ESTRUCTURAS",
        "ESTRUCTURISTA",
        "ESPECIALISTA EN ESTRUCTURA Y OBRAS DE ARTE",
        "ESPECIALISTA EN MUROS DE CONTENCIÓN / OBRAS DE ARTE"
    ],
    "Hidráulica, Riego y Agua": [
        "ESPECIALISTA EN HIDRÁULICA",
        "ESPECIALISTA EN HIDROLOGÍA E HIDRÁULICA",
        "ESPECIALISTA EN OBRAS HIDRÁULICAS",
        "ESPECIALISTA EN SISTEMA DE RIEGO TECNIFICADO"
    ],
    "Suelos, Pavimentos y Geotecnia": [
        "ESPECIALISTA EN SUELOS Y PAVIMENTOS",
        "ESPECIALISTA EN GEOTECNIA",
        "ESPECIALISTA EN GEOTECNIA Y GEOLOGÍA",
        "ESPECIALISTA EN MECÁNICA DE SUELOS",
        "ESPECIALISTA EN SUELOS Y GEOTECNIA"
    ],
    "Instalaciones": [
        "ESPECIALISTA EN INSTALACIONES SANITARIAS",
        "ESPECIALISTA EN INSTALACIONES ELÉCTRICAS",
        "ESPECIALISTA EN ELECTROMECÁNICA"
    ],
    "Calidad, Metrados y Costos": [
        "ESPECIALISTA EN CONTROL DE CALIDAD",
        "ESPECIALISTA EN AUTOCAD, METRADOS, PRESUPUESTOS Y VALORIZACIONES",
        "ESPECIALISTA EN COSTOS, METRADOS Y VALORIZACIONES"
    ],
    "Arquitectura y Diseño": [
        "ARQUITECTO",
        "ESPECIALISTA EN ARQUITECTURA"
    ],
    "Topografía y Vialidad": [
        "ESPECIALISTA EN TOPOGRAFÍA Y EXPLANACIONES",
        "ESPECIALISTA EN TRÁFICO"
    ],
    "Arqueología": [
        "ARQUEÓLOGO"
    ],
    "Seguridad, Salud y Medio Ambiente (SSOMA)": [
        "ESPECIALISTA EN SEGURIDAD, SALUD Y MEDIO AMBIENTE (SSOMA)",
        "ESPECIALISTA EN SEGURIDAD Y SALUD OCUPACIONAL",
        "ESPECIALISTA EN MITIGACIÓN DE IMPACTO AMBIENTAL",
        "ESPECIALISTA EN MEDIO AMBIENTE"
    ],
    "Cargos Genéricos o No Especificados": [
        "ESPECIALISTA"
    ]
}


def obtener_catalogo_cargos() -> Dict[str, List[str]]:
    """
    Obtiene el catálogo completo de categorías y cargos técnicos.

    Returns:
        Diccionario con categorías como claves y listas de cargos como valores
    """
    return CARGOS_TECNICOS
