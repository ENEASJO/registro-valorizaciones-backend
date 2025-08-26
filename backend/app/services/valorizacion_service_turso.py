"""
Servicio para manejar valorizaciones en Turso
"""
import json
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from app.core.database_turso import execute_query
from app.models.valorizacion import ValorizacionCreate, ValorizacionUpdate
import random
import string

class ValorizacionServiceTurso:
    """Servicio para operaciones CRUD de valorizaciones en Turso"""
    
    @staticmethod
    async def generar_codigo_valorizacion(obra_id: int, numero: int) -> str:
        """Generar código único para valorización"""
        # Obtener código de obra
        result = await execute_query(
            "SELECT codigo FROM obras WHERE id = ?",
            [obra_id]
        )
        
        if result.rows:
            obra_codigo = result.rows[0][0]
            return f"{obra_codigo}-VAL-{numero:03d}"
        else:
            # Fallback si no se encuentra la obra
            return f"VAL{obra_id}-{numero:03d}"
    
    @staticmethod
    async def crear_valorizacion(valorizacion_data: ValorizacionCreate) -> Dict[str, Any]:
        """Crear nueva valorización"""
        try:
            # Verificar que no exista valorización con mismo número para la obra
            existing = await execute_query(
                "SELECT id FROM valorizaciones WHERE obra_id = ? AND numero_valorizacion = ?",
                [valorizacion_data.obra_id, valorizacion_data.numero_valorizacion]
            )
            
            if existing.rows:
                raise ValueError(f"Ya existe valorización #{valorizacion_data.numero_valorizacion} para esta obra")
            
            # Generar código único
            codigo = await ValorizacionServiceTurso.generar_codigo_valorizacion(
                valorizacion_data.obra_id, 
                valorizacion_data.numero_valorizacion
            )
            
            # Preparar datos
            now = datetime.now().isoformat()
            
            # Calcular monto total si no se proporciona
            monto_ejecutado = float(valorizacion_data.monto_ejecutado or 0)
            gastos = float(valorizacion_data.monto_gastos_generales or 0)
            utilidad = float(valorizacion_data.monto_utilidad or 0)
            igv = float(valorizacion_data.igv or 0)
            monto_total = monto_ejecutado + gastos + utilidad + igv
            
            # Insertar valorización
            val_sql = """
            INSERT INTO valorizaciones (
                codigo, obra_id, numero_valorizacion, periodo,
                fecha_inicio, fecha_fin, fecha_presentacion, fecha_aprobacion,
                tipo_valorizacion, monto_ejecutado, monto_materiales, monto_mano_obra,
                monto_equipos, monto_subcontratos, monto_gastos_generales, monto_utilidad,
                igv, monto_total, porcentaje_avance_periodo, porcentaje_avance_acumulado,
                estado_valorizacion, observaciones, archivos_adjuntos, metrado_ejecutado,
                partidas_ejecutadas, activo, created_at, updated_at, version
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, 1)
            """
            
            await execute_query(val_sql, [
                codigo,
                valorizacion_data.obra_id,
                valorizacion_data.numero_valorizacion,
                valorizacion_data.periodo,
                valorizacion_data.fecha_inicio.isoformat(),
                valorizacion_data.fecha_fin.isoformat(),
                valorizacion_data.fecha_presentacion.isoformat() if valorizacion_data.fecha_presentacion else None,
                valorizacion_data.fecha_aprobacion.isoformat() if valorizacion_data.fecha_aprobacion else None,
                valorizacion_data.tipo_valorizacion,
                monto_ejecutado,
                float(valorizacion_data.monto_materiales or 0),
                float(valorizacion_data.monto_mano_obra or 0),
                float(valorizacion_data.monto_equipos or 0),
                float(valorizacion_data.monto_subcontratos or 0),
                gastos,
                utilidad,
                igv,
                monto_total,
                float(valorizacion_data.porcentaje_avance_periodo or 0),
                float(valorizacion_data.porcentaje_avance_acumulado or 0),
                valorizacion_data.estado_valorizacion,
                valorizacion_data.observaciones,
                json.dumps(valorizacion_data.archivos_adjuntos or []),
                json.dumps(valorizacion_data.metrado_ejecutado or []),
                json.dumps(valorizacion_data.partidas_ejecutadas or []),
                now,
                now
            ])
            
            # Obtener valorización creada
            result = await execute_query(
                "SELECT * FROM valorizaciones WHERE codigo = ?",
                [codigo]
            )
            
            if result.rows:
                val_data = result.rows[0]
                print(f"✅ Valorización {codigo} creada exitosamente")
                return await ValorizacionServiceTurso._format_valorizacion_response(val_data)
            else:
                raise Exception("No se pudo recuperar la valorización creada")
                
        except Exception as e:
            print(f"❌ Error creando valorización: {e}")
            raise
    
    @staticmethod
    async def obtener_valorizacion_por_id(valorizacion_id: int) -> Optional[Dict[str, Any]]:
        """Obtener valorización por ID"""
        try:
            result = await execute_query(
                """
                SELECT v.*, o.nombre as obra_nombre, o.codigo as obra_codigo, 
                       e.razon_social as empresa_razon_social
                FROM valorizaciones v
                LEFT JOIN obras o ON v.obra_id = o.id
                LEFT JOIN empresas e ON o.empresa_id = e.id
                WHERE v.id = ? AND v.activo = 1
                """,
                [valorizacion_id]
            )
            
            if result.rows:
                return await ValorizacionServiceTurso._format_valorizacion_response(result.rows[0])
            return None
            
        except Exception as e:
            print(f"❌ Error obteniendo valorización: {e}")
            raise
    
    @staticmethod
    async def obtener_valorizacion_por_codigo(codigo: str) -> Optional[Dict[str, Any]]:
        """Obtener valorización por código"""
        try:
            result = await execute_query(
                """
                SELECT v.*, o.nombre as obra_nombre, o.codigo as obra_codigo,
                       e.razon_social as empresa_razon_social
                FROM valorizaciones v
                LEFT JOIN obras o ON v.obra_id = o.id
                LEFT JOIN empresas e ON o.empresa_id = e.id
                WHERE v.codigo = ? AND v.activo = 1
                """,
                [codigo]
            )
            
            if result.rows:
                return await ValorizacionServiceTurso._format_valorizacion_response(result.rows[0])
            return None
            
        except Exception as e:
            print(f"❌ Error obteniendo valorización: {e}")
            raise
    
    @staticmethod
    async def listar_valorizaciones(
        obra_id: Optional[int] = None,
        periodo: Optional[str] = None,
        estado: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Listar valorizaciones con filtros"""
        try:
            conditions = ["v.activo = 1"]
            params = []
            
            if obra_id:
                conditions.append("v.obra_id = ?")
                params.append(obra_id)
            
            if periodo:
                conditions.append("v.periodo = ?")
                params.append(periodo)
            
            if estado:
                conditions.append("v.estado_valorizacion = ?")
                params.append(estado)
            
            where_clause = " AND ".join(conditions)
            
            result = await execute_query(
                f"""
                SELECT v.*, o.nombre as obra_nombre, o.codigo as obra_codigo,
                       e.razon_social as empresa_razon_social
                FROM valorizaciones v
                LEFT JOIN obras o ON v.obra_id = o.id
                LEFT JOIN empresas e ON o.empresa_id = e.id
                WHERE {where_clause}
                ORDER BY v.obra_id, v.numero_valorizacion DESC
                LIMIT ? OFFSET ?
                """,
                params + [limit, offset]
            )
            
            valorizaciones = []
            for row in result.rows:
                val_formatted = await ValorizacionServiceTurso._format_valorizacion_response(row)
                valorizaciones.append(val_formatted)
            
            return valorizaciones
            
        except Exception as e:
            print(f"❌ Error listando valorizaciones: {e}")
            raise
    
    @staticmethod
    async def actualizar_valorizacion(val_id: int, val_update: ValorizacionUpdate) -> Optional[Dict[str, Any]]:
        """Actualizar valorización"""
        try:
            # Construir query dinámicamente
            update_fields = []
            params = []
            
            for field, value in val_update.dict(exclude_unset=True).items():
                if value is not None:
                    if field in ['archivos_adjuntos', 'metrado_ejecutado', 'partidas_ejecutadas']:
                        update_fields.append(f"{field} = ?")
                        params.append(json.dumps(value))
                    elif isinstance(value, date):
                        update_fields.append(f"{field} = ?")
                        params.append(value.isoformat())
                    else:
                        update_fields.append(f"{field} = ?")
                        params.append(value)
            
            if not update_fields:
                raise ValueError("No hay campos para actualizar")
            
            # Actualizar updated_at y version
            update_fields.extend(["updated_at = ?", "version = version + 1"])
            params.extend([datetime.now().isoformat(), val_id])
            
            update_sql = f"""
            UPDATE valorizaciones 
            SET {', '.join(update_fields)}
            WHERE id = ? AND activo = 1
            """
            
            await execute_query(update_sql, params)
            
            # Retornar valorización actualizada
            return await ValorizacionServiceTurso.obtener_valorizacion_por_id(val_id)
            
        except Exception as e:
            print(f"❌ Error actualizando valorización: {e}")
            raise
    
    @staticmethod
    async def eliminar_valorizacion(val_id: int) -> bool:
        """Eliminar valorización (soft delete)"""
        try:
            await execute_query(
                """
                UPDATE valorizaciones 
                SET activo = 0, updated_at = ? 
                WHERE id = ? AND activo = 1
                """,
                [datetime.now().isoformat(), val_id]
            )
            
            print(f"✅ Valorización {val_id} eliminada (soft delete)")
            return True
            
        except Exception as e:
            print(f"❌ Error eliminando valorización: {e}")
            raise
    
    @staticmethod
    async def obtener_resumen_por_obra(obra_id: int) -> Dict[str, Any]:
        """Obtener resumen de valorizaciones por obra"""
        try:
            result = await execute_query(
                """
                SELECT 
                    COUNT(*) as total_valorizaciones,
                    SUM(monto_total) as monto_total_ejecutado,
                    MAX(porcentaje_avance_acumulado) as porcentaje_avance_total,
                    MAX(fecha_fin) as ultima_valorizacion
                FROM valorizaciones
                WHERE obra_id = ? AND activo = 1
                """,
                [obra_id]
            )
            
            if result.rows:
                row = result.rows[0]
                return {
                    'obra_id': obra_id,
                    'total_valorizaciones': row[0] or 0,
                    'monto_total_ejecutado': float(row[1] or 0),
                    'porcentaje_avance_total': float(row[2] or 0),
                    'ultima_valorizacion': row[3]
                }
            
            return {
                'obra_id': obra_id,
                'total_valorizaciones': 0,
                'monto_total_ejecutado': 0,
                'porcentaje_avance_total': 0,
                'ultima_valorizacion': None
            }
            
        except Exception as e:
            print(f"❌ Error obteniendo resumen: {e}")
            raise
    
    @staticmethod
    async def _format_valorizacion_response(row_data: tuple) -> Dict[str, Any]:
        """Formatear respuesta de valorización"""
        # Mapear columnas básicas
        fields = [
            'id', 'codigo', 'obra_id', 'numero_valorizacion', 'periodo',
            'fecha_inicio', 'fecha_fin', 'fecha_presentacion', 'fecha_aprobacion',
            'tipo_valorizacion', 'monto_ejecutado', 'monto_materiales', 'monto_mano_obra',
            'monto_equipos', 'monto_subcontratos', 'monto_gastos_generales', 'monto_utilidad',
            'igv', 'monto_total', 'porcentaje_avance_periodo', 'porcentaje_avance_acumulado',
            'estado_valorizacion', 'observaciones', 'archivos_adjuntos', 'metrado_ejecutado',
            'partidas_ejecutadas', 'activo', 'created_at', 'updated_at',
            'created_by', 'updated_by', 'version'
        ]
        
        # Si hay columnas adicionales de JOIN
        if len(row_data) > len(fields):
            fields.extend(['obra_nombre', 'obra_codigo', 'empresa_razon_social'])
        
        val_dict = dict(zip(fields, row_data))
        
        # Deserializar campos JSON
        for field in ['archivos_adjuntos', 'metrado_ejecutado', 'partidas_ejecutadas']:
            if field in val_dict and val_dict[field]:
                try:
                    val_dict[field] = json.loads(val_dict[field])
                except:
                    val_dict[field] = []
        
        return val_dict