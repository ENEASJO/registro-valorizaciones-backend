"""
Servicio simple para empresas usando libsql-client directo
"""
import logging
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
from libsql_client import create_client_sync

logger = logging.getLogger(__name__)

class EmpresaServiceSimple:
    """Servicio simple para operaciones CRUD de empresas en Turso"""
    
    def __init__(self):
        self.client = None
        self._init_client()
    
    def _init_client(self):
        """Inicializar cliente Turso simple"""
        try:
            # Obtener configuración desde variables de entorno
            database_url = os.getenv("TURSO_DATABASE_URL", "libsql://registro-de-valorizaciones-eneasjo.aws-us-east-2.turso.io")
            auth_token = os.getenv("TURSO_AUTH_TOKEN")
            
            if not auth_token:
                logger.warning("⚠️ TURSO_AUTH_TOKEN no encontrado en variables de entorno")
                return
            
            logger.info(f"🔗 Conectando a Turso: {database_url}")
            
            # Crear cliente síncrono
            self.client = create_client_sync(
                url=database_url,
                auth_token=auth_token
            )
            
            logger.info("✅ Cliente Turso conectado exitosamente")
            
            # Verificar conexión con query simple
            result = self.client.execute("SELECT 1 as test")
            logger.info("✅ Conexión Turso verificada")
            
        except Exception as e:
            logger.error(f"❌ Error conectando a Turso: {e}")
            self.client = None
    
    def crear_tabla_si_no_existe(self):
        """Crear tabla empresas si no existe"""
        if not self.client:
            logger.warning("⚠️ Cliente Turso no disponible para crear tabla")
            return False
        
        try:
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS empresas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo TEXT UNIQUE,
                ruc TEXT UNIQUE NOT NULL,
                razon_social TEXT NOT NULL,
                nombre_comercial TEXT,
                email TEXT,
                telefono TEXT,
                celular TEXT,
                direccion TEXT,
                representante_legal TEXT,
                dni_representante TEXT,
                estado TEXT DEFAULT 'ACTIVO',
                tipo_empresa TEXT DEFAULT 'SAC',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
            
            self.client.execute(create_table_sql)
            logger.info("✅ Tabla empresas creada/verificada exitosamente")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error creando tabla empresas: {e}")
            return False
    
    def guardar_empresa(self, datos_empresa: Dict[str, Any]) -> Optional[int]:
        """
        Guardar empresa en Turso
        """
        if not self.client:
            logger.warning("⚠️ Cliente Turso no disponible")
            return None
        
        try:
            # Asegurar que la tabla existe
            self.crear_tabla_si_no_existe()
            
            ruc = datos_empresa.get('ruc', '').strip()
            razon_social = datos_empresa.get('razon_social', '').strip()
            
            if not ruc or not razon_social:
                logger.warning("⚠️ RUC y razón social son requeridos")
                return None
            
            # Generar código único
            codigo = f"EMP{ruc[:6]}"
            
            # SQL para insertar o actualizar
            insert_sql = """
            INSERT OR REPLACE INTO empresas (
                codigo, ruc, razon_social, nombre_comercial, 
                email, telefono, celular, direccion, 
                representante_legal, dni_representante, 
                estado, tipo_empresa, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """
            
            params = [
                codigo,
                ruc,
                razon_social,
                datos_empresa.get('nombre_comercial', ''),
                datos_empresa.get('email', ''),
                datos_empresa.get('telefono', ''),
                datos_empresa.get('celular', ''),
                datos_empresa.get('direccion', ''),
                datos_empresa.get('representante_legal', ''),
                datos_empresa.get('dni_representante', ''),
                datos_empresa.get('estado', 'ACTIVO'),
                datos_empresa.get('tipo_empresa', 'SAC')
            ]
            
            # Ejecutar inserción
            result = self.client.execute(insert_sql, params)
            
            # Obtener ID insertado
            if hasattr(result, 'last_insert_rowid') and result.last_insert_rowid:
                empresa_id = result.last_insert_rowid
                logger.info(f"✅ Empresa guardada en Turso - ID: {empresa_id}, RUC: {ruc}")
                return empresa_id
            else:
                # Si no hay last_insert_rowid, buscar por RUC
                select_sql = "SELECT id FROM empresas WHERE ruc = ? LIMIT 1"
                select_result = self.client.execute(select_sql, [ruc])
                
                if select_result.rows and len(select_result.rows) > 0:
                    empresa_id = select_result.rows[0][0]
                    logger.info(f"✅ Empresa actualizada en Turso - ID: {empresa_id}, RUC: {ruc}")
                    return empresa_id
                else:
                    logger.warning(f"⚠️ No se pudo obtener ID de empresa guardada: {ruc}")
                    return 1  # Retornar 1 como ID temporal si no se puede obtener
            
        except Exception as e:
            logger.error(f"❌ Error guardando empresa en Turso: {e}")
            return None
    
    def listar_empresas(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Listar empresas desde Turso
        """
        if not self.client:
            logger.warning("⚠️ Cliente Turso no disponible")
            return []
        
        try:
            # Asegurar que la tabla existe
            self.crear_tabla_si_no_existe()
            
            # Query para obtener empresas
            select_sql = """
            SELECT 
                id, codigo, ruc, razon_social, nombre_comercial,
                email, telefono, celular, direccion,
                representante_legal, dni_representante,
                estado, tipo_empresa, created_at, updated_at
            FROM empresas 
            ORDER BY updated_at DESC 
            LIMIT ?
            """
            
            result = self.client.execute(select_sql, [limit])
            
            if not result.rows:
                logger.info("📋 No hay empresas guardadas en Turso")
                return []
            
            # Convertir rows a diccionarios
            empresas = []
            columns = [
                'id', 'codigo', 'ruc', 'razon_social', 'nombre_comercial',
                'email', 'telefono', 'celular', 'direccion',
                'representante_legal', 'dni_representante',
                'estado', 'tipo_empresa', 'created_at', 'updated_at'
            ]
            
            for row in result.rows:
                empresa = {}
                for i, column in enumerate(columns):
                    empresa[column] = row[i] if i < len(row) else None
                empresas.append(empresa)
            
            logger.info(f"📋 {len(empresas)} empresas obtenidas desde Turso")
            return empresas
            
        except Exception as e:
            logger.error(f"❌ Error listando empresas desde Turso: {e}")
            return []
    
    def obtener_empresa_por_ruc(self, ruc: str) -> Optional[Dict[str, Any]]:
        """
        Obtener empresa específica por RUC
        """
        if not self.client:
            return None
        
        try:
            select_sql = """
            SELECT 
                id, codigo, ruc, razon_social, nombre_comercial,
                email, telefono, celular, direccion,
                representante_legal, dni_representante,
                estado, tipo_empresa, created_at, updated_at
            FROM empresas 
            WHERE ruc = ? 
            LIMIT 1
            """
            
            result = self.client.execute(select_sql, [ruc])
            
            if not result.rows or len(result.rows) == 0:
                return None
            
            row = result.rows[0]
            columns = [
                'id', 'codigo', 'ruc', 'razon_social', 'nombre_comercial',
                'email', 'telefono', 'celular', 'direccion',
                'representante_legal', 'dni_representante',
                'estado', 'tipo_empresa', 'created_at', 'updated_at'
            ]
            
            empresa = {}
            for i, column in enumerate(columns):
                empresa[column] = row[i] if i < len(row) else None
            
            return empresa
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo empresa por RUC {ruc}: {e}")
            return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas básicas"""
        if not self.client:
            return {"total": 0, "activas": 0, "error": "Cliente no disponible"}
        
        try:
            # Total de empresas
            total_result = self.client.execute("SELECT COUNT(*) FROM empresas")
            total = total_result.rows[0][0] if total_result.rows else 0
            
            # Empresas activas
            activas_result = self.client.execute("SELECT COUNT(*) FROM empresas WHERE estado = 'ACTIVO'")
            activas = activas_result.rows[0][0] if activas_result.rows else 0
            
            return {
                "total": total,
                "activas": activas,
                "inactivas": total - activas
            }
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo estadísticas: {e}")
            return {"total": 0, "activas": 0, "error": str(e)}

# Instancia global
empresa_service_simple = EmpresaServiceSimple()