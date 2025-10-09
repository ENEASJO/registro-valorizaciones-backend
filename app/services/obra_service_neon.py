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

    # Ya no necesitamos _get_connection(), usamos database directamente
    
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
            conn = await ObraServiceNeon._get_connection()
            try:
                # Convertir empresa_id a UUID si es string
                if isinstance(obra_data.empresa_id, str):
                    empresa_uuid = uuid.UUID(obra_data.empresa_id)
                else:
                    empresa_uuid = obra_data.empresa_id
                    
                # Verificar que la empresa existe
                empresa_exists = await conn.fetchval(
                    "SELECT EXISTS(SELECT 1 FROM empresas WHERE id = $1 AND estado = 'ACTIVO')",
                    empresa_uuid
                )
                
                if not empresa_exists:
                    raise ValidationException(f"La empresa con ID {empresa_uuid} no existe o está inactiva")
                    
                # Generar código usando la función de base de datos
                codigo = await conn.fetchval(
                    "SELECT generar_codigo_obra_uuid($1)",
                    empresa_uuid
                )
                
                # Calcular monto total
                monto_contractual = obra_data.monto_contractual or Decimal('0')
                monto_adicionales = obra_data.monto_adicionales or Decimal('0')
                monto_total = monto_contractual + monto_adicionales
                
                # Insertar obra
                obra_id = await conn.fetchval("""
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
                        $1, $2, $3, $4, $5,
                        $6, $7, $8, $9, $10,
                        $11, $12, $13,
                        $14, $15,
                        $16, $17, $18,
                        $19, $20,
                        $21, $22, $23,
                        true, 1
                    ) RETURNING id
                """, 
                    codigo, obra_data.nombre, obra_data.descripcion, empresa_uuid, obra_data.cliente,
                    obra_data.ubicacion, obra_data.distrito, obra_data.provincia, obra_data.departamento, obra_data.ubigeo,
                    obra_data.modalidad_ejecucion, obra_data.sistema_contratacion, obra_data.tipo_obra,
                    monto_contractual, monto_adicionales,
                    obra_data.fecha_inicio, obra_data.fecha_fin_contractual, obra_data.fecha_fin_real,
                    obra_data.plazo_contractual, obra_data.plazo_total,
                    obra_data.estado_obra, obra_data.porcentaje_avance, obra_data.observaciones
                )
                
                # Obtener la obra creada
                obra = await conn.fetchrow("""
                    SELECT o.*, e.razon_social as empresa_nombre
                    FROM obras o
                    JOIN empresas e ON o.empresa_id = e.id
                    WHERE o.id = $1
                """, obra_id)
                
                obra_dict = dict(obra)
                
                logger.info(f"✅ Obra creada exitosamente: {codigo} (ID: {obra_id})")
                
                return obra_dict
                
            finally:
                await conn.close()
                
        except ValidationException:
            raise
        except Exception as e:
            logger.error(f"❌ Error creando obra: {str(e)}")
            raise Exception(f"Error al crear la obra: {str(e)}")
    
    @staticmethod
    async def obtener_obra_por_id(obra_id: int) -> Optional[Dict[str, Any]]:
        """Obtener obra por ID"""
        try:
            conn = await ObraServiceNeon._get_connection()
            try:
                obra = await conn.fetchrow("""
                    SELECT o.*, e.razon_social as empresa_nombre
                    FROM obras o
                    JOIN empresas e ON o.empresa_id = e.id
                    WHERE o.id = $1 AND o.activo = true
                """, obra_id)
                
                if obra:
                    return dict(obra)
                return None
                
            finally:
                await conn.close()
                
        except Exception as e:
            logger.error(f"❌ Error obteniendo obra {obra_id}: {str(e)}")
            return None
    
    @staticmethod
    async def obtener_obra_por_codigo(codigo: str) -> Optional[Dict[str, Any]]:
        """Obtener obra por código"""
        try:
            conn = await ObraServiceNeon._get_connection()
            try:
                obra = await conn.fetchrow("""
                    SELECT o.*, e.razon_social as empresa_nombre
                    FROM obras o
                    JOIN empresas e ON o.empresa_id = e.id
                    WHERE o.codigo = $1 AND o.activo = true
                """, codigo.upper())
                
                if obra:
                    return dict(obra)
                return None
                
            finally:
                await conn.close()
                
        except Exception as e:
            logger.error(f"❌ Error obteniendo obra {codigo}: {str(e)}")
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
            conn = await ObraServiceNeon._get_connection()
            try:
                # Verificar que la obra existe
                exists = await conn.fetchval(
                    "SELECT EXISTS(SELECT 1 FROM obras WHERE id = $1 AND activo = true)",
                    obra_id
                )
                
                if not exists:
                    return None
                
                # Construir query de actualización dinámicamente
                update_fields = []
                params = []
                param_count = 0
                
                update_data = obra_update.dict(exclude_unset=True)
                
                for field, value in update_data.items():
                    if value is not None:
                        param_count += 1
                        update_fields.append(f"{field} = ${param_count}")
                        params.append(value)
                
                if not update_fields:
                    # No hay campos para actualizar
                    return await ObraServiceNeon.obtener_obra_por_id(obra_id)
                
                # Agregar campos de auditoría
                param_count += 1
                update_fields.append(f"updated_at = ${param_count}")
                params.append(datetime.now())
                
                param_count += 1
                update_fields.append(f"version = version + 1")
                
                # Agregar ID para WHERE
                param_count += 1
                params.append(obra_id)
                
                query = f"""
                    UPDATE obras 
                    SET {', '.join(update_fields)}
                    WHERE id = ${param_count}
                    RETURNING id
                """
                
                updated_id = await conn.fetchval(query, *params)
                
                if updated_id:
                    return await ObraServiceNeon.obtener_obra_por_id(updated_id)
                
                return None
                
            finally:
                await conn.close()
                
        except Exception as e:
            logger.error(f"❌ Error actualizando obra {obra_id}: {str(e)}")
            return None
    
    @staticmethod
    async def eliminar_obra(obra_id: int) -> bool:
        """Eliminar obra (soft delete)"""
        try:
            conn = await ObraServiceNeon._get_connection()
            try:
                result = await conn.execute("""
                    UPDATE obras 
                    SET activo = false, updated_at = NOW(), version = version + 1
                    WHERE id = $1 AND activo = true
                """, obra_id)
                
                return result == "UPDATE 1"
                
            finally:
                await conn.close()
                
        except Exception as e:
            logger.error(f"❌ Error eliminando obra {obra_id}: {str(e)}")
            return False
    
    @staticmethod
    async def verificar_codigo_unico(codigo: str) -> bool:
        """Verificar si un código de obra es único"""
        try:
            conn = await ObraServiceNeon._get_connection()
            try:
                exists = await conn.fetchval(
                    "SELECT EXISTS(SELECT 1 FROM obras WHERE codigo = $1)",
                    codigo.upper()
                )
                return not exists
                
            finally:
                await conn.close()
                
        except Exception as e:
            logger.error(f"❌ Error verificando código único {codigo}: {str(e)}")
            return False
