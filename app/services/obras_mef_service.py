"""
Servicio para gestión de obras con integración MEF Invierte en Neon PostgreSQL
"""
from typing import Optional, Dict, Any, List
from datetime import datetime, date
import json
import os
import asyncpg
import logging

logger = logging.getLogger(__name__)

def get_database_url():
    """Obtener URL de conexión a la base de datos"""
    return os.getenv("NEON_CONNECTION_STRING") or os.getenv("DATABASE_URL")

class ObrasMEFService:
    """Servicio para operaciones CRUD de obras con datos MEF"""

    @staticmethod
    async def _get_connection():
        """Obtener conexión a la base de datos"""
        database_url = get_database_url()
        return await asyncpg.connect(database_url)

    async def crear_obra(
        self,
        cui: str,
        datos_mef: Dict[str, Any],
        contrato_numero: str,
        contrato_fecha: date,
        contrato_plazo_dias: Optional[int] = None,
        contrato_monto: Optional[float] = None,
        ubicacion_tipo: str = None,
        ubicacion_nombre: str = None,
        estado_obra: str = "registrada",
        codigo_interno: Optional[str] = None,
        contratista_ruc: Optional[str] = None,
        contratista_nombre: Optional[str] = None,
        supervisor_ruc: Optional[str] = None,
        supervisor_nombre: Optional[str] = None,
        ubicacion_direccion: Optional[str] = None,
        ubicacion_latitud: Optional[float] = None,
        ubicacion_longitud: Optional[float] = None,
        observaciones: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Crea una nueva obra en la base de datos"""
        conn = await self._get_connection()
        try:
            # Convertir datos_mef a JSON string para JSONB
            datos_mef_json = json.dumps(datos_mef, ensure_ascii=False, default=str)

            obra = await conn.fetchrow("""
                INSERT INTO obras (
                    cui, codigo_interno, datos_mef, fecha_actualizacion_mef,
                    contrato_numero, contrato_fecha, contrato_plazo_dias, contrato_monto,
                    contratista_ruc, contratista_nombre,
                    supervisor_ruc, supervisor_nombre,
                    ubicacion_tipo, ubicacion_nombre, ubicacion_direccion,
                    ubicacion_latitud, ubicacion_longitud,
                    estado_obra, observaciones
                ) VALUES (
                    $1, $2, $3::jsonb, $4,
                    $5, $6, $7, $8,
                    $9, $10,
                    $11, $12,
                    $13, $14, $15,
                    $16, $17,
                    $18, $19
                )
                RETURNING
                    id, cui, codigo_interno,
                    datos_mef, fecha_actualizacion_mef,
                    contrato_numero, contrato_fecha, contrato_plazo_dias, contrato_monto,
                    contratista_ruc, contratista_nombre,
                    supervisor_ruc, supervisor_nombre,
                    ubicacion_tipo, ubicacion_nombre, ubicacion_direccion,
                    ubicacion_latitud, ubicacion_longitud,
                    estado_obra, observaciones,
                    created_at, updated_at
            """,
                cui, codigo_interno, datos_mef_json, datetime.now(),
                contrato_numero, contrato_fecha, contrato_plazo_dias, contrato_monto,
                contratista_ruc, contratista_nombre,
                supervisor_ruc, supervisor_nombre,
                ubicacion_tipo, ubicacion_nombre, ubicacion_direccion,
                ubicacion_latitud, ubicacion_longitud,
                estado_obra, observaciones
            )

            return dict(obra) if obra else None

        finally:
            await conn.close()

    async def obtener_obra_por_id(self, obra_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene una obra por su ID"""
        conn = await self._get_connection()
        try:
            obra = await conn.fetchrow("""
                SELECT
                    id, cui, codigo_interno,
                    datos_mef, fecha_actualizacion_mef,
                    contrato_numero, contrato_fecha, contrato_plazo_dias, contrato_monto,
                    contratista_ruc, contratista_nombre,
                    supervisor_ruc, supervisor_nombre,
                    ubicacion_tipo, ubicacion_nombre, ubicacion_direccion,
                    ubicacion_latitud, ubicacion_longitud,
                    estado_obra, observaciones,
                    created_at, updated_at
                FROM obras
                WHERE id = $1
            """, obra_id)

            if obra:
                result = dict(obra)
                # Parsear datos_mef si es string
                if isinstance(result.get('datos_mef'), str):
                    result['datos_mef'] = json.loads(result['datos_mef'])
                return result
            return None

        finally:
            await conn.close()

    async def obtener_obra_por_cui(self, cui: str) -> Optional[Dict[str, Any]]:
        """Obtiene una obra por su CUI"""
        conn = await self._get_connection()
        try:
            obra = await conn.fetchrow("""
                SELECT
                    id, cui, codigo_interno,
                    datos_mef, fecha_actualizacion_mef,
                    contrato_numero, contrato_fecha, contrato_plazo_dias, contrato_monto,
                    contratista_ruc, contratista_nombre,
                    supervisor_ruc, supervisor_nombre,
                    ubicacion_tipo, ubicacion_nombre, ubicacion_direccion,
                    ubicacion_latitud, ubicacion_longitud,
                    estado_obra, observaciones,
                    created_at, updated_at
                FROM obras
                WHERE cui = $1
            """, cui)

            if obra:
                result = dict(obra)
                if isinstance(result.get('datos_mef'), str):
                    result['datos_mef'] = json.loads(result['datos_mef'])
                return result
            return None

        finally:
            await conn.close()

    async def listar_obras(
        self,
        estado_obra: Optional[str] = None,
        ubicacion_tipo: Optional[str] = None,
        busqueda: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Lista obras con filtros opcionales"""
        conn = await self._get_connection()
        try:
            conditions = []
            params = []
            param_count = 0

            if estado_obra:
                param_count += 1
                conditions.append(f"estado_obra = ${param_count}")
                params.append(estado_obra)

            if ubicacion_tipo:
                param_count += 1
                conditions.append(f"ubicacion_tipo = ${param_count}")
                params.append(ubicacion_tipo)

            if busqueda:
                param_count += 1
                conditions.append(f"""
                    (cui ILIKE ${param_count}
                    OR contrato_numero ILIKE ${param_count}
                    OR datos_mef->>'nombre' ILIKE ${param_count})
                """)
                params.append(f"%{busqueda}%")

            where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

            param_count += 1
            limit_param = f"${param_count}"
            params.append(limit)

            param_count += 1
            offset_param = f"${param_count}"
            params.append(offset)

            query = f"""
                SELECT
                    id, cui, codigo_interno,
                    datos_mef, fecha_actualizacion_mef,
                    contrato_numero, contrato_fecha, contrato_plazo_dias, contrato_monto,
                    contratista_ruc, contratista_nombre,
                    supervisor_ruc, supervisor_nombre,
                    ubicacion_tipo, ubicacion_nombre, ubicacion_direccion,
                    ubicacion_latitud, ubicacion_longitud,
                    estado_obra, observaciones,
                    created_at, updated_at
                FROM obras
                {where_clause}
                ORDER BY created_at DESC
                LIMIT {limit_param} OFFSET {offset_param}
            """

            results = await conn.fetch(query, *params)

            obras = []
            for result in results:
                obra = dict(result)
                if isinstance(obra.get('datos_mef'), str):
                    obra['datos_mef'] = json.loads(obra['datos_mef'])
                obras.append(obra)

            return obras

        finally:
            await conn.close()

    async def actualizar_obra(
        self,
        obra_id: str,
        **campos
    ) -> Optional[Dict[str, Any]]:
        """Actualiza campos específicos de una obra"""
        conn = await self._get_connection()
        try:
            # Convertir datos_mef a JSON si existe
            if 'datos_mef' in campos and isinstance(campos['datos_mef'], dict):
                campos['datos_mef'] = json.dumps(campos['datos_mef'], ensure_ascii=False, default=str)

            # Construir SET clause dinámicamente
            set_clauses = []
            params = []
            param_count = 0

            for campo, valor in campos.items():
                param_count += 1
                if campo == 'datos_mef':
                    set_clauses.append(f"{campo} = ${param_count}::jsonb")
                else:
                    set_clauses.append(f"{campo} = ${param_count}")
                params.append(valor)

            if not set_clauses:
                return await self.obtener_obra_por_id(obra_id)

            # Agregar updated_at
            set_clauses.append("updated_at = CURRENT_TIMESTAMP")

            # Agregar obra_id
            param_count += 1
            params.append(obra_id)

            query = f"""
                UPDATE obras
                SET {', '.join(set_clauses)}
                WHERE id = ${param_count}
                RETURNING
                    id, cui, codigo_interno,
                    datos_mef, fecha_actualizacion_mef,
                    contrato_numero, contrato_fecha, contrato_plazo_dias, contrato_monto,
                    contratista_ruc, contratista_nombre,
                    supervisor_ruc, supervisor_nombre,
                    ubicacion_tipo, ubicacion_nombre, ubicacion_direccion,
                    ubicacion_latitud, ubicacion_longitud,
                    estado_obra, observaciones,
                    created_at, updated_at
            """

            result = await conn.fetchrow(query, *params)

            if result:
                obra = dict(result)
                if isinstance(obra.get('datos_mef'), str):
                    obra['datos_mef'] = json.loads(obra['datos_mef'])
                return obra
            return None

        finally:
            await conn.close()

    async def eliminar_obra(self, obra_id: str) -> bool:
        """Elimina una obra por su ID"""
        conn = await self._get_connection()
        try:
            result = await conn.execute("DELETE FROM obras WHERE id = $1", obra_id)
            return result == "DELETE 1"

        finally:
            await conn.close()

    async def obtener_estadisticas(self) -> Dict[str, Any]:
        """Obtiene estadísticas generales de obras"""
        conn = await self._get_connection()
        try:
            stats = await conn.fetchrow("""
                SELECT
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE estado_obra = 'registrada') as registradas,
                    COUNT(*) FILTER (WHERE estado_obra = 'en_ejecucion') as en_ejecucion,
                    COUNT(*) FILTER (WHERE estado_obra = 'paralizada') as paralizadas,
                    COUNT(*) FILTER (WHERE estado_obra = 'terminada') as terminadas,
                    COUNT(*) FILTER (WHERE estado_obra = 'liquidada') as liquidadas,
                    COUNT(*) FILTER (WHERE estado_obra = 'cancelada') as canceladas,
                    COALESCE(SUM(contrato_monto), 0) as inversion_total
                FROM obras
            """)

            result = dict(stats) if stats else {}

            return {
                "total": result.get("total", 0),
                "por_estado": {
                    "registrada": result.get("registradas", 0),
                    "en_ejecucion": result.get("en_ejecucion", 0),
                    "paralizada": result.get("paralizadas", 0),
                    "terminada": result.get("terminadas", 0),
                    "liquidada": result.get("liquidadas", 0),
                    "cancelada": result.get("canceladas", 0),
                },
                "inversion_total": float(result.get("inversion_total", 0))
            }

        finally:
            await conn.close()

    async def actualizar_datos_mef(self, obra_id: str, datos_mef: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Actualiza solo los datos MEF de una obra"""
        return await self.actualizar_obra(
            obra_id,
            datos_mef=datos_mef,
            fecha_actualizacion_mef=datetime.now()
        )


# Instancia singleton del servicio
obras_mef_service = ObrasMEFService()
