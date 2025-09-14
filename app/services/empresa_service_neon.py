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
        env_connection_string = os.getenv("NEON_CONNECTION_STRING")
        
        # Validar que la conexión no tenga formato inválido
        if env_connection_string and not env_connection_string.startswith("postgresql://"):
            logger.warning(f"⚠️ NEON_CONNECTION_STRING tiene formato inválido: {env_connection_string[:50]}...")
            logger.warning("🔄 Usando cadena de conexión por defecto")
            env_connection_string = None
        
        self.connection_string = env_connection_string or "postgresql://neondb_owner:npg_puYoPelF96Hd@ep-fancy-river-acd46jxk-pooler.sa-east-1.aws.neon.tech/neondb?sslmode=require"
        
        logger.info(f"🔗 Usando conexión: {self.connection_string[:50]}...")
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
                        return None
                        
        except Exception as e:
            logger.error(f"❌ Error guardando empresa en Neon: {e}")
            import traceback
            logger.error(f"❌ Traceback completo: {traceback.format_exc()}")

            # Log adicional para depuración
            logger.error(f"❌ Datos que se intentaron guardar:")
            for key, value in empresa_data.items():
                logger.error(f"   - {key}: {value}")

            return None
    
    def listar_empresas(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Listar empresas desde Neon con sus representantes
        """
        try:
            logger.info(f"🔍 Iniciando listar_empresas con limit={limit}")
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    # Primero contemos cuántas empresas hay
                    cursor.execute("SELECT COUNT(*) as total FROM empresas;")
                    count_result = cursor.fetchone()
                    total_empresas = count_result['total']
                    logger.info(f"📊 Total de empresas en la base de datos: {total_empresas}")

                    query = """
                        SELECT * FROM empresas
                        ORDER BY created_at DESC
                        LIMIT %s;
                    """

                    logger.info(f"🔍 Ejecutando query con limit: {limit}")
                    cursor.execute(query, (limit,))
                    empresas = cursor.fetchall()
                    logger.info(f"📋 Empresas obtenidas de la consulta: {len(empresas)}")

                    # Convertir RealDictRow a dict y manejar UUIDs
                    result = []
                    for i, empresa in enumerate(empresas):
                        logger.info(f"🔄 Procesando empresa {i+1}: {empresa.get('ruc', 'Sin RUC')}")
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

                        # Obtener representantes para esta empresa
                        representantes = self._obtener_representantes_por_empresa(empresa_dict['id'])
                        empresa_dict['representantes'] = representantes

                        result.append(empresa_dict)

                    logger.info(f"✅ {len(result)} empresas procesadas y retornadas")
                    return result

        except Exception as e:
            logger.error(f"❌ Error listando empresas desde Neon: {e}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            return []
    
    def obtener_empresa_por_ruc(self, ruc: str) -> Optional[Dict[str, Any]]:
        """
        Obtener empresa específica por RUC con sus representantes
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
                        
                        # Obtener representantes para esta empresa
                        representantes = self._obtener_representantes_por_empresa(empresa_dict['id'])
                        empresa_dict['representantes'] = representantes
                        
                        return empresa_dict
                    return None
                    
        except Exception as e:
            logger.error(f"❌ Error obteniendo empresa por RUC {ruc}: {e}")
            return None
    
    def eliminar_empresa(self, identificador_empresa: str) -> bool:
        """
        NUEVA IMPLEMENTACIÓN - Eliminar empresa de Neon PostgreSQL
        Detecta UUID vs RUC automáticamente y busca correctamente
        """
        try:
            logger.info(f"🗑️ NUEVA IMPLEMENTACIÓN - Eliminando empresa: {identificador_empresa}")
            
            # Test UUID detection
            es_formato_uuid = self._es_uuid(identificador_empresa)
            logger.info(f"🔍 Formato UUID detectado: {es_formato_uuid}")
            
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                    empresa_encontrada = None
                    
                    # Buscar empresa según el formato detectado
                    if es_formato_uuid:
                        logger.info(f"🔍 Buscando empresa por UUID: {identificador_empresa}")
                        cursor.execute("SELECT id, ruc, razon_social FROM empresas WHERE id = %s;", (identificador_empresa,))
                        empresa_encontrada = cursor.fetchone()
                    else:
                        logger.info(f"🔍 Buscando empresa por RUC: {identificador_empresa}")
                        cursor.execute("SELECT id, ruc, razon_social FROM empresas WHERE ruc = %s;", (identificador_empresa,))
                        empresa_encontrada = cursor.fetchone()
                    
                    if not empresa_encontrada:
                        logger.warning(f"⚠️ EMPRESA NO ENCONTRADA para eliminar: {identificador_empresa}")
                        return False
                    
                    logger.info(f"📋 EMPRESA ENCONTRADA: ID={empresa_encontrada['id']}, RUC={empresa_encontrada['ruc']}, Nombre={empresa_encontrada['razon_social']}")
                    
                    # Eliminar usando el ID UUID de la empresa encontrada
                    delete_query = "DELETE FROM empresas WHERE id = %s;"
                    cursor.execute(delete_query, (empresa_encontrada['id'],))
                    
                    filas_eliminadas = cursor.rowcount
                    conn.commit()
                    
                    if filas_eliminadas > 0:
                        logger.info(f"✅ ELIMINACIÓN EXITOSA - ID: {empresa_encontrada['id']}, RUC: {empresa_encontrada['ruc']}")
                        return True
                    else:
                        logger.error(f"❌ ERROR: No se eliminaron filas aunque la empresa fue encontrada: {identificador_empresa}")
                        return False
                        
        except Exception as exception:
            logger.error(f"❌ ERROR eliminando empresa {identificador_empresa}: {exception}")
            import traceback
            logger.error(f"❌ Traceback completo: {traceback.format_exc()}")
            return False
    
    def _es_uuid(self, texto: str) -> bool:
        """
        Verificar si un texto tiene formato de UUID
        """
        try:
            uuid.UUID(texto)
            return True
        except ValueError:
            return False
    
    def _obtener_representantes_por_empresa(self, empresa_id: str) -> List[Dict[str, Any]]:
        """
        Obtener representantes legales de una empresa específica
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    query = """
                        SELECT
                            id,
                            nombre,
                            cargo,
                            tipo_documento,
                            numero_documento,
                            participacion,
                            fuente,
                            es_principal,
                            activo,
                            creado_en as created_at
                        FROM representantes_legales
                        WHERE empresa_id = %s AND activo = true
                        ORDER BY creado_en DESC;
                    """
                    
                    cursor.execute(query, (empresa_id,))
                    representantes = cursor.fetchall()
                    
                    # Convertir a lista de diccionarios
                    result = []
                    for rep in representantes:
                        rep_dict = dict(rep)
                        # Convertir UUID a string si es necesario
                        if 'id' in rep_dict and rep_dict['id']:
                            rep_dict['id'] = str(rep_dict['id'])
                        result.append(rep_dict)
                    
                    logger.info(f"📋 {len(result)} representantes obtenidos para empresa {empresa_id}")
                    return result
                    
        except Exception as e:
            logger.error(f"❌ Error obteniendo representantes para empresa {empresa_id}: {e}")
            return []
    
    def obtener_representantes_por_empresa(self, empresa_id: str) -> List[Dict[str, Any]]:
        """
        Método público para obtener representantes legales de una empresa
        """
        return self._obtener_representantes_por_empresa(empresa_id)
    
    def guardar_representante(self, empresa_id: str, representante_data: Dict[str, Any]) -> Optional[str]:
        """
        Guardar un representante legal para una empresa
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    # Generar ID único para el representante
                    representante_id = str(uuid.uuid4())

                    query = """
                        INSERT INTO representantes_legales (
                            id, empresa_id, nombre, cargo,
                            tipo_documento, numero_documento,
                            participacion, fuente, es_principal, activo, creado_en
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                    """

                    cursor.execute(query, (
                        representante_id,
                        empresa_id,
                        representante_data.get('nombre', ''),
                        representante_data.get('cargo', ''),
                        representante_data.get('tipo_documento', 'DNI'),
                        representante_data.get('numero_documento', ''),
                        representante_data.get('participacion', None),
                        representante_data.get('fuente', 'MANUAL'),
                        representante_data.get('es_principal', False),
                        representante_data.get('activo', True),
                        datetime.now()
                    ))

                    conn.commit()
                    logger.info(f"✅ Representante guardado para empresa {empresa_id}: {representante_data.get('nombre')}")
                    return representante_id

        except Exception as e:
            logger.error(f"❌ Error guardando representante para empresa {empresa_id}: {e}")
            return None
    
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