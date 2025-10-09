"""
Servicio para gestión de obras usando Neon PostgreSQL
"""
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal

from app.models.obra import ObraCreate, ObraUpdate, ObraResponse
from app.utils.codigo_generator import CodigoGenerator
from app.core.database import database  # Usar la instancia de databases
from app.utils.exceptions import ValidationException
import uuid

logger = logging.getLogger(__name__)

class ObraServiceNeon:
    """Servicio para gestión de obras usando Neon PostgreSQL"""

    @staticmethod
    async def crear_obra(obra_data: ObraCreate) -> Dict[str, Any]:
        """
        Crear una nueva obra con código generado automáticamente

        Args:
            obra_data: Datos de la obra a crear

        Returns:
            Diccionario con datos de la obra creada

        Raises:
            ValidationException: Si hay errores de validación
        """
        try:
            # Convertir empresa_id a UUID si es string
            if isinstance(obra_data.empresa_id, str):
                empresa_uuid = uuid.UUID(obra_data.empresa_id)
            else:
                empresa_uuid = obra_data.empresa_id

            # Verificar que la empresa existe
            empresa_exists_query = """
                SELECT EXISTS(SELECT 1 FROM empresas WHERE id = :empresa_id AND estado = 'ACTIVO')
            """
            empresa_exists = await database.fetch_val(
                query=empresa_exists_query,
                values={"empresa_id": empresa_uuid}
            )

            if not empresa_exists:
                raise ValidationException(f"La empresa con ID {empresa_uuid} no existe o está inactiva")

            # Generar código usando la función de base de datos
            codigo_query = "SELECT generar_codigo_obra_uuid(:empresa_id)"
            codigo = await database.fetch_val(
                query=codigo_query,
                values={"empresa_id": empresa_uuid}
            )

            # Calcular monto total
            monto_contractual = obra_data.monto_contractual or Decimal('0')
            monto_adicionales = obra_data.monto_adicionales or Decimal('0')
            monto_total = monto_contractual + monto_adicionales

            # Insertar obra
            insert_query = """
                INSERT INTO obras (
                    codigo, nombre, descripcion, empresa_id, cliente,
                    ubicacion, distrito, provincia, departamento, ubigeo,
                    modalidad_ejecucion, sistema_contratacion, tipo_obra,
                    monto_contractual, monto_adicionales,
                    fecha_inicio, fecha_fin_contractual, fecha_fin_real,
                    plazo_contractual, plazo_total,
                    estado_obra, porcentaje_avance, observaciones,
                    activo, version
                ) VALUES (
                    :codigo, :nombre, :descripcion, :empresa_id, :cliente,
                    :ubicacion, :distrito, :provincia, :departamento, :ubigeo,
                    :modalidad_ejecucion, :sistema_contratacion, :tipo_obra,
                    :monto_contractual, :monto_adicionales,
                    :fecha_inicio, :fecha_fin_contractual, :fecha_fin_real,
                    :plazo_contractual, :plazo_total,
                    :estado_obra, :porcentaje_avance, :observaciones,
                    true, 1
                ) RETURNING id
            """

            obra_id = await database.fetch_val(
                query=insert_query,
                values={
                    "codigo": codigo,
                    "nombre": obra_data.nombre,
                    "descripcion": obra_data.descripcion,
                    "empresa_id": empresa_uuid,
                    "cliente": obra_data.cliente,
                    "ubicacion": obra_data.ubicacion,
                    "distrito": obra_data.distrito,
                    "provincia": obra_data.provincia,
                    "departamento": obra_data.departamento,
                    "ubigeo": obra_data.ubigeo,
                    "modalidad_ejecucion": obra_data.modalidad_ejecucion,
                    "sistema_contratacion": obra_data.sistema_contratacion,
                    "tipo_obra": obra_data.tipo_obra,
                    "monto_contractual": monto_contractual,
                    "monto_adicionales": monto_adicionales,
                    "fecha_inicio": obra_data.fecha_inicio,
                    "fecha_fin_contractual": obra_data.fecha_fin_contractual,
                    "fecha_fin_real": obra_data.fecha_fin_real,
                    "plazo_contractual": obra_data.plazo_contractual,
                    "plazo_total": obra_data.plazo_total,
                    "estado_obra": obra_data.estado_obra,
                    "porcentaje_avance": obra_data.porcentaje_avance,
                    "observaciones": obra_data.observaciones
                }
            )

            # Obtener la obra creada
            select_query = """
                SELECT o.*, e.razon_social as empresa_nombre
                FROM obras o
                JOIN empresas e ON o.empresa_id = e.id
                WHERE o.id = :obra_id
            """
            obra = await database.fetch_one(
                query=select_query,
                values={"obra_id": obra_id}
            )

            obra_dict = dict(obra)

            logger.info(f"✅ Obra creada exitosamente: {codigo} (ID: {obra_id})")

            return obra_dict

        except ValidationException:
            raise
        except Exception as e:
            logger.error(f"❌ Error creando obra: {str(e)}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            raise Exception(f"Error al crear la obra: {str(e)}")

    @staticmethod
    async def obtener_obra_por_id(obra_id: int) -> Optional[Dict[str, Any]]:
        """Obtener obra por ID"""
        try:
            query = """
                SELECT o.*, e.razon_social as empresa_nombre
                FROM obras o
                JOIN empresas e ON o.empresa_id = e.id
                WHERE o.id = :obra_id AND o.activo = true
            """
            obra = await database.fetch_one(
                query=query,
                values={"obra_id": obra_id}
            )

            if obra:
                return dict(obra)
            return None

        except Exception as e:
            logger.error(f"❌ Error obteniendo obra {obra_id}: {str(e)}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            return None

    @staticmethod
    async def obtener_obra_por_codigo(codigo: str) -> Optional[Dict[str, Any]]:
        """Obtener obra por código"""
        try:
            query = """
                SELECT o.*, e.razon_social as empresa_nombre
                FROM obras o
                JOIN empresas e ON o.empresa_id = e.id
                WHERE o.codigo = :codigo AND o.activo = true
            """
            obra = await database.fetch_one(
                query=query,
                values={"codigo": codigo.upper()}
            )

            if obra:
                return dict(obra)
            return None

        except Exception as e:
            logger.error(f"❌ Error obteniendo obra {codigo}: {str(e)}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            return None

    @staticmethod
    async def listar_obras(
        empresa_id: Optional[int] = None,
        estado: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Listar obras con filtros"""
        try:
            # Construir query dinámicamente con placeholders :param_name
            where_conditions = ["o.activo = true"]
            values = {}

            if empresa_id:
                where_conditions.append("o.empresa_id = :empresa_id")
                values["empresa_id"] = empresa_id

            if estado:
                where_conditions.append("o.estado_obra = :estado")
                values["estado"] = estado.upper()

            values["limit"] = limit
            values["offset"] = offset

            where_clause = " AND ".join(where_conditions)

            query = f"""
                SELECT o.*, e.razon_social as empresa_nombre
                FROM obras o
                JOIN empresas e ON o.empresa_id = e.id
                WHERE {where_clause}
                ORDER BY o.created_at DESC
                LIMIT :limit OFFSET :offset
            """

            logger.info(f"🔍 Ejecutando query: {query[:100]}...")
            logger.info(f"🔍 Parámetros: {values}")

            obras = await database.fetch_all(query=query, values=values)

            logger.info(f"✅ Se encontraron {len(obras)} obras")

            return [dict(obra) for obra in obras]

        except Exception as e:
            logger.error(f"❌ Error listando obras: {str(e)}")
            logger.error(f"❌ Tipo: {type(e).__name__}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            return []

    @staticmethod
    async def actualizar_obra(obra_id: int, obra_update: ObraUpdate) -> Optional[Dict[str, Any]]:
        """Actualizar obra existente"""
        try:
            # Verificar que la obra existe
            exists_query = """
                SELECT EXISTS(SELECT 1 FROM obras WHERE id = :obra_id AND activo = true)
            """
            exists = await database.fetch_val(
                query=exists_query,
                values={"obra_id": obra_id}
            )

            if not exists:
                return None

            # Construir query de actualización dinámicamente
            update_fields = []
            values = {"obra_id": obra_id}

            update_data = obra_update.dict(exclude_unset=True)

            for field, value in update_data.items():
                if value is not None:
                    update_fields.append(f"{field} = :{field}")
                    values[field] = value

            if not update_fields:
                # No hay campos para actualizar
                return await ObraServiceNeon.obtener_obra_por_id(obra_id)

            # Agregar campos de auditoría
            update_fields.append("updated_at = :updated_at")
            values["updated_at"] = datetime.now()

            update_fields.append("version = version + 1")

            query = f"""
                UPDATE obras
                SET {', '.join(update_fields)}
                WHERE id = :obra_id
                RETURNING id
            """

            updated_id = await database.fetch_val(query=query, values=values)

            if updated_id:
                return await ObraServiceNeon.obtener_obra_por_id(updated_id)

            return None

        except Exception as e:
            logger.error(f"❌ Error actualizando obra {obra_id}: {str(e)}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            return None

    @staticmethod
    async def eliminar_obra(obra_id: int) -> bool:
        """Eliminar obra (soft delete)"""
        try:
            query = """
                UPDATE obras
                SET activo = false, updated_at = :updated_at, version = version + 1
                WHERE id = :obra_id AND activo = true
            """
            result = await database.execute(
                query=query,
                values={"obra_id": obra_id, "updated_at": datetime.now()}
            )

            # execute() returns the row count for UPDATE statements
            return result == 1

        except Exception as e:
            logger.error(f"❌ Error eliminando obra {obra_id}: {str(e)}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            return False

    @staticmethod
    async def verificar_codigo_unico(codigo: str) -> bool:
        """Verificar si un código de obra es único"""
        try:
            query = """
                SELECT EXISTS(SELECT 1 FROM obras WHERE codigo = :codigo)
            """
            exists = await database.fetch_val(
                query=query,
                values={"codigo": codigo.upper()}
            )
            return not exists

        except Exception as e:
            logger.error(f"❌ Error verificando código único {codigo}: {str(e)}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            return False
