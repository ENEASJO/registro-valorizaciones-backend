"""
Servicio para manejar obras en Turso
"""
import json
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from app.core.database_turso import execute_query
from app.models.obra import ObraCreate, ObraUpdate, ObraResponse
import random
import string

class ObraServiceTurso:
    """Servicio para operaciones CRUD de obras en Turso"""
    
    @staticmethod
    async def generar_codigo_obra() -> str:
        """Generar código único para obra"""
        while True:
            codigo = "OBR" + "".join(random.choices(string.digits, k=6))
            
            # Verificar que no exista
            result = await execute_query(
                "SELECT id FROM obras WHERE codigo = ?", 
                [codigo]
            )
            if not result.rows:
                return codigo
    
    @staticmethod
    async def crear_obra(obra_data: ObraCreate) -> Dict[str, Any]:
        """Crear nueva obra"""
        try:
            # Generar código único
            codigo = await ObraServiceTurso.generar_codigo_obra()
            
            # Preparar datos
            now = datetime.now().isoformat()
            
            # Calcular monto total
            monto_contractual = float(obra_data.monto_contractual or 0)
            monto_adicionales = float(obra_data.monto_adicionales or 0)
            monto_total = monto_contractual + monto_adicionales
            
            # Insertar obra
            obra_sql = """
            INSERT INTO obras (
                codigo, nombre, descripcion, empresa_id, cliente,
                ubicacion, distrito, provincia, departamento, ubigeo,
                modalidad_ejecucion, sistema_contratacion, tipo_obra,
                monto_contractual, monto_adicionales, monto_total,
                fecha_inicio, fecha_fin_contractual, fecha_fin_real,
                plazo_contractual, plazo_total, estado_obra, porcentaje_avance,
                observaciones, activo, created_at, updated_at, version
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, 1)
            """
            
            await execute_query(obra_sql, [
                codigo,
                obra_data.nombre,
                obra_data.descripcion,
                obra_data.empresa_id,
                obra_data.cliente,
                obra_data.ubicacion,
                obra_data.distrito,
                obra_data.provincia,
                obra_data.departamento,
                obra_data.ubigeo,
                obra_data.modalidad_ejecucion,
                obra_data.sistema_contratacion,
                obra_data.tipo_obra,
                monto_contractual,
                monto_adicionales,
                monto_total,
                obra_data.fecha_inicio.isoformat() if obra_data.fecha_inicio else None,
                obra_data.fecha_fin_contractual.isoformat() if obra_data.fecha_fin_contractual else None,
                obra_data.fecha_fin_real.isoformat() if obra_data.fecha_fin_real else None,
                obra_data.plazo_contractual,
                obra_data.plazo_total,
                obra_data.estado_obra,
                float(obra_data.porcentaje_avance or 0),
                obra_data.observaciones,
                now,
                now
            ])
            
            # Obtener obra creada
            result = await execute_query(
                "SELECT * FROM obras WHERE codigo = ?",
                [codigo]
            )
            
            if result.rows:
                obra_data = result.rows[0]
                print(f"✅ Obra {codigo} creada exitosamente")
                return await ObraServiceTurso._format_obra_response(obra_data)
            else:
                raise Exception("No se pudo recuperar la obra creada")
                
        except Exception as e:
            print(f"❌ Error creando obra: {e}")
            raise
    
    @staticmethod
    async def obtener_obra_por_id(obra_id: int) -> Optional[Dict[str, Any]]:
        """Obtener obra por ID"""
        try:
            result = await execute_query(
                """
                SELECT o.*, e.razon_social as empresa_razon_social 
                FROM obras o
                LEFT JOIN empresas e ON o.empresa_id = e.id
                WHERE o.id = ? AND o.activo = 1
                """,
                [obra_id]
            )
            
            if result.rows:
                return await ObraServiceTurso._format_obra_response(result.rows[0])
            return None
            
        except Exception as e:
            print(f"❌ Error obteniendo obra: {e}")
            raise
    
    @staticmethod
    async def obtener_obra_por_codigo(codigo: str) -> Optional[Dict[str, Any]]:
        """Obtener obra por código"""
        try:
            result = await execute_query(
                """
                SELECT o.*, e.razon_social as empresa_razon_social 
                FROM obras o
                LEFT JOIN empresas e ON o.empresa_id = e.id
                WHERE o.codigo = ? AND o.activo = 1
                """,
                [codigo]
            )
            
            if result.rows:
                return await ObraServiceTurso._format_obra_response(result.rows[0])
            return None
            
        except Exception as e:
            print(f"❌ Error obteniendo obra: {e}")
            raise
    
    @staticmethod
    async def listar_obras(
        empresa_id: Optional[int] = None,
        estado: Optional[str] = None, 
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Listar obras con filtros"""
        try:
            conditions = ["o.activo = 1"]
            params = []
            
            if empresa_id:
                conditions.append("o.empresa_id = ?")
                params.append(empresa_id)
            
            if estado:
                conditions.append("o.estado_obra = ?")
                params.append(estado)
            
            where_clause = " AND ".join(conditions)
            
            result = await execute_query(
                f"""
                SELECT o.*, e.razon_social as empresa_razon_social
                FROM obras o
                LEFT JOIN empresas e ON o.empresa_id = e.id
                WHERE {where_clause}
                ORDER BY o.created_at DESC
                LIMIT ? OFFSET ?
                """,
                params + [limit, offset]
            )
            
            obras = []
            for row in result.rows:
                obra_formatted = await ObraServiceTurso._format_obra_response(row)
                obras.append(obra_formatted)
            
            return obras
            
        except Exception as e:
            print(f"❌ Error listando obras: {e}")
            raise
    
    @staticmethod
    async def actualizar_obra(obra_id: int, obra_update: ObraUpdate) -> Optional[Dict[str, Any]]:
        """Actualizar obra"""
        try:
            # Construir query dinámicamente
            update_fields = []
            params = []
            
            for field, value in obra_update.dict(exclude_unset=True).items():
                if value is not None:
                    update_fields.append(f"{field} = ?")
                    if isinstance(value, date):
                        params.append(value.isoformat())
                    else:
                        params.append(value)
            
            if not update_fields:
                raise ValueError("No hay campos para actualizar")
            
            # Actualizar updated_at y version
            update_fields.extend(["updated_at = ?", "version = version + 1"])
            params.extend([datetime.now().isoformat(), obra_id])
            
            update_sql = f"""
            UPDATE obras 
            SET {', '.join(update_fields)}
            WHERE id = ? AND activo = 1
            """
            
            await execute_query(update_sql, params)
            
            # Retornar obra actualizada
            return await ObraServiceTurso.obtener_obra_por_id(obra_id)
            
        except Exception as e:
            print(f"❌ Error actualizando obra: {e}")
            raise
    
    @staticmethod
    async def eliminar_obra(obra_id: int) -> bool:
        """Eliminar obra (soft delete)"""
        try:
            await execute_query(
                """
                UPDATE obras 
                SET activo = 0, updated_at = ? 
                WHERE id = ? AND activo = 1
                """,
                [datetime.now().isoformat(), obra_id]
            )
            
            print(f"✅ Obra {obra_id} eliminada (soft delete)")
            return True
            
        except Exception as e:
            print(f"❌ Error eliminando obra: {e}")
            raise
    
    @staticmethod
    async def _format_obra_response(row_data: tuple) -> Dict[str, Any]:
        """Formatear respuesta de obra"""
        # Mapear columnas (ajustar según estructura real de la tabla)
        fields = [
            'id', 'codigo', 'nombre', 'descripcion', 'empresa_id', 'cliente',
            'ubicacion', 'distrito', 'provincia', 'departamento', 'ubigeo',
            'modalidad_ejecucion', 'sistema_contratacion', 'tipo_obra',
            'monto_contractual', 'monto_adicionales', 'monto_total',
            'fecha_inicio', 'fecha_fin_contractual', 'fecha_fin_real',
            'plazo_contractual', 'plazo_total', 'estado_obra', 'porcentaje_avance',
            'observaciones', 'activo', 'created_at', 'updated_at',
            'created_by', 'updated_by', 'version'
        ]
        
        # Si hay columna adicional de empresa
        if len(row_data) > len(fields):
            fields.append('empresa_razon_social')
        
        obra_dict = dict(zip(fields, row_data))
        
        # Calcular campos adicionales
        if obra_dict.get('fecha_inicio'):
            try:
                fecha_inicio = datetime.fromisoformat(obra_dict['fecha_inicio']).date()
                hoy = date.today()
                obra_dict['dias_transcurridos'] = (hoy - fecha_inicio).days
                
                if obra_dict.get('fecha_fin_contractual'):
                    fecha_fin = datetime.fromisoformat(obra_dict['fecha_fin_contractual']).date()
                    obra_dict['dias_restantes'] = (fecha_fin - hoy).days
                    
                    if obra_dict.get('plazo_contractual'):
                        dias_programados = obra_dict['dias_transcurridos']
                        plazo_total = obra_dict['plazo_contractual']
                        if plazo_total > 0:
                            obra_dict['avance_programado'] = min(100, (dias_programados / plazo_total) * 100)
            except:
                pass
        
        return obra_dict