"""
Servicio para empresas usando Neon PostgreSQL
"""
import logging
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid
import json

logger = logging.getLogger(__name__)

class EmpresaServiceNeon:
    """Servicio para operaciones CRUD de empresas en Neon PostgreSQL"""
    
    def __init__(self):
        # Connection string de Neon
        self.connection_string = os.getenv(
            "NEON_CONNECTION_STRING", 
            "postgresql://neondb_owner:npg_puYoPelF96Hd@ep-fancy-river-acd46jxk-pooler.sa-east-1.aws.neon.tech/neondb?channel_binding=require&sslmode=require"
        )
        
        self._verificar_conexion()
    
    def _get_connection(self):
        """Obtener conexión a la base de datos"""
        return psycopg2.connect(self.connection_string, cursor_factory=RealDictCursor)
    
    def _verificar_conexion(self):
        """Verificar que podemos conectar a Neon"""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT version();")
                    version = cursor.fetchone()
                    logger.info(f"✅ Conexión a Neon verificada: {version['version'][:50]}...")
        except Exception as e:
            logger.error(f"❌ Error conectando a Neon: {e}")
    
    def guardar_empresa(self, datos_empresa: Dict[str, Any]) -> Optional[str]:
        """
        Guardar empresa en Neon PostgreSQL
        """
        try:
            ruc = datos_empresa.get('ruc', '').strip()
            razon_social = datos_empresa.get('razon_social', '').strip()
            
            if not ruc or not razon_social:
                logger.warning("⚠️ RUC y razón social son requeridos")
                return None
            
            # Preparar datos para inserción
            empresa_data = {
                'codigo': f"EMP{ruc[:6]}",
                'ruc': ruc,
                'razon_social': razon_social,
                'nombre_comercial': datos_empresa.get('nombre_comercial', ''),
                'email': datos_empresa.get('email', ''),
                'telefono': datos_empresa.get('telefono', ''),
                'celular': datos_empresa.get('celular', ''),
                'direccion': datos_empresa.get('direccion', ''),
                'distrito': datos_empresa.get('distrito', ''),
                'provincia': datos_empresa.get('provincia', ''),
                'departamento': datos_empresa.get('departamento', ''),
                'representante_legal': datos_empresa.get('representante_legal', ''),
                'dni_representante': datos_empresa.get('dni_representante', ''),
                'estado': datos_empresa.get('estado', 'ACTIVO'),
                'tipo_empresa': datos_empresa.get('tipo_empresa', 'SAC'),
            'categoria_contratista': datos_empresa.get('categoria_contratista', None),
                'datos_sunat': json.dumps(datos_empresa.get('datos_sunat', {})) if datos_empresa.get('datos_sunat') else None,
                'datos_osce': json.dumps(datos_empresa.get('datos_osce', {})) if datos_empresa.get('datos_osce') else None,
                'fuentes_consultadas': datos_empresa.get('fuentes_consultadas', [])
            }
            
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    # Insertar o actualizar (ON CONFLICT)
                    insert_query = """
                        INSERT INTO empresas (
                            codigo, ruc, razon_social, nombre_comercial, email, telefono, celular,
                            direccion, distrito, provincia, departamento, representante_legal,
                            dni_representante, estado, tipo_empresa, categoria_contratista, 
                            datos_sunat, datos_osce, fuentes_consultadas
                        ) VALUES (
                            %(codigo)s, %(ruc)s, %(razon_social)s, %(nombre_comercial)s, %(email)s, 
                            %(telefono)s, %(celular)s, %(direccion)s, %(distrito)s, %(provincia)s,
                            %(departamento)s, %(representante_legal)s, %(dni_representante)s,
                            %(estado)s, %(tipo_empresa)s, %(categoria_contratista)s,
                            %(datos_sunat)s, %(datos_osce)s, %(fuentes_consultadas)s
                        )
                        ON CONFLICT (ruc) DO UPDATE SET
                            razon_social = EXCLUDED.razon_social,
                            nombre_comercial = EXCLUDED.nombre_comercial,
                            email = EXCLUDED.email,
                            telefono = EXCLUDED.telefono,
                            celular = EXCLUDED.celular,
                            direccion = EXCLUDED.direccion,
                            distrito = EXCLUDED.distrito,
                            provincia = EXCLUDED.provincia,
                            departamento = EXCLUDED.departamento,
                            representante_legal = EXCLUDED.representante_legal,
                            dni_representante = EXCLUDED.dni_representante,
                            estado = EXCLUDED.estado,
                            tipo_empresa = EXCLUDED.tipo_empresa,
                            categoria_contratista = EXCLUDED.categoria_contratista,
                            datos_sunat = EXCLUDED.datos_sunat,
                            datos_osce = EXCLUDED.datos_osce,
                            fuentes_consultadas = EXCLUDED.fuentes_consultadas,
                            updated_at = NOW()
                        RETURNING id;
                    """
                    
                    cursor.execute(insert_query, empresa_data)
                    result = cursor.fetchone()
                    empresa_id = str(result['id']) if result else None
                    
                    conn.commit()
                    
                    if empresa_id:
                        logger.info(f"✅ Empresa guardada en Neon - ID: {empresa_id}, RUC: {ruc}")
                        return empresa_id
                    else:
                        logger.warning(f"⚠️ No se obtuvo ID para empresa RUC: {ruc}")
                        return "neon-success"
                        
        except Exception as e:
            logger.error(f"❌ Error guardando empresa en Neon: {e}")
            return None
    
    def listar_empresas(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Listar empresas desde Neon
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    query = """
                        SELECT * FROM empresas 
                        ORDER BY created_at DESC 
                        LIMIT %s;
                    """
                    
                    cursor.execute(query, (limit,))
                    empresas = cursor.fetchall()
                    
                    # Convertir RealDictRow a dict y manejar UUIDs
                    result = []
                    for empresa in empresas:
                        empresa_dict = dict(empresa)
                        # Convertir UUID a string
                        if 'id' in empresa_dict and empresa_dict['id']:
                            empresa_dict['id'] = str(empresa_dict['id'])
                        # Parsear JSON fields
                        if empresa_dict.get('datos_sunat'):
                            try:
                                empresa_dict['datos_sunat'] = json.loads(empresa_dict['datos_sunat']) if isinstance(empresa_dict['datos_sunat'], str) else empresa_dict['datos_sunat']
                            except:
                                pass
                        if empresa_dict.get('datos_osce'):
                            try:
                                empresa_dict['datos_osce'] = json.loads(empresa_dict['datos_osce']) if isinstance(empresa_dict['datos_osce'], str) else empresa_dict['datos_osce']
                            except:
                                pass
                        result.append(empresa_dict)
                    
                    logger.info(f"📋 {len(result)} empresas obtenidas desde Neon")
                    return result
                    
        except Exception as e:
            logger.error(f"❌ Error listando empresas desde Neon: {e}")
            return []
    
    def obtener_empresa_por_ruc(self, ruc: str) -> Optional[Dict[str, Any]]:
        """
        Obtener empresa específica por RUC
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    query = "SELECT * FROM empresas WHERE ruc = %s LIMIT 1;"
                    cursor.execute(query, (ruc,))
                    empresa = cursor.fetchone()
                    
                    if empresa:
                        empresa_dict = dict(empresa)
                        # Convertir UUID a string
                        if 'id' in empresa_dict and empresa_dict['id']:
                            empresa_dict['id'] = str(empresa_dict['id'])
                        return empresa_dict
                    return None
                    
        except Exception as e:
            logger.error(f"❌ Error obteniendo empresa por RUC {ruc}: {e}")
            return None
    
    def eliminar_empresa(self, empresa_id: str) -> bool:
        """
        Eliminar empresa de Neon PostgreSQL
        Intenta por UUID primero, luego por RUC como fallback
        """
        try:
            logger.info(f"🗑️ Intentando eliminar empresa: {empresa_id}")
            
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    # Primero verificar si existe la empresa
                    cursor.execute("SELECT id, ruc, razon_social FROM empresas WHERE id = %s OR ruc = %s;", 
                                 (empresa_id, empresa_id))
                    empresa_existente = cursor.fetchone()
                    
                    if not empresa_existente:
                        logger.warning(f"⚠️ Empresa no encontrada para eliminar: {empresa_id}")
                        return False
                    
                    logger.info(f"📋 Empresa encontrada: ID={empresa_existente['id']}, RUC={empresa_existente['ruc']}, Nombre={empresa_existente['razon_social']}")
                    
                    # Eliminar por ID (más preciso)
                    query = "DELETE FROM empresas WHERE id = %s;"
                    cursor.execute(query, (empresa_existente['id'],))
                    
                    rows_deleted = cursor.rowcount
                    conn.commit()
                    
                    if rows_deleted > 0:
                        logger.info(f"✅ Empresa eliminada exitosamente - ID: {empresa_existente['id']}, RUC: {empresa_existente['ruc']}")
                        return True
                    else:
                        logger.error(f"❌ Error: No se pudo eliminar la empresa aunque fue encontrada: {empresa_id}")
                        return False
                        
        except Exception as e:
            logger.error(f"❌ Error eliminando empresa {empresa_id}: {e}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas básicas"""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    # Total de empresas
                    cursor.execute("SELECT COUNT(*) as total FROM empresas;")
                    total = cursor.fetchone()['total']
                    
                    # Empresas activas
                    cursor.execute("SELECT COUNT(*) as activas FROM empresas WHERE estado = 'ACTIVO';")
                    activas = cursor.fetchone()['activas']
                    
                    return {
                        "total": total,
                        "activas": activas,
                        "inactivas": total - activas,
                        "fuente": "neon",
                        "database": "PostgreSQL"
                    }
                    
        except Exception as e:
            logger.error(f"❌ Error obteniendo estadísticas: {e}")
            return {"total": 0, "activas": 0, "error": str(e)}

# Instancia global
empresa_service_neon = EmpresaServiceNeon()