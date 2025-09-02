"""
Servicio mejorado para gestionar empresas en Turso
"""
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from libsql_client import create_client_sync
from app.core.database_turso import get_turso_config
from app.models.empresa import EmpresaDB

logger = logging.getLogger(__name__)

class EmpresaServiceTurso:
    """Servicio para operaciones CRUD de empresas en Turso"""
    
    def __init__(self):
        self.client = None
        self._init_client()
    
    def _init_client(self):
        """Inicializar cliente Turso"""
        try:
            url, token = get_turso_config()
            if url and token:
                # Conectar con libsql-client usando la API correcta
                self.client = create_client_sync(url=url, auth_token=token)
                logger.info("✅ Cliente Turso inicializado")
            else:
                logger.warning("⚠️ Turso no configurado, usando modo degradado")
        except Exception as e:
            logger.error(f"❌ Error inicializando cliente Turso: {e}")
            self.client = None
    
    def save_empresa_from_consulta(self, ruc: str, datos_consulta: Dict[str, Any]) -> Optional[int]:
        """
        Guardar empresa desde los datos de consulta RUC consolidada
        """
        if not self.client:
            logger.warning("⚠️ Cliente Turso no disponible")
            return None
            
        try:
            # Preparar datos para insertar
            empresa_data = self._prepare_empresa_data(ruc, datos_consulta)
            
            # SQL para insertar/actualizar empresa (adaptado a estructura real)
            insert_sql = """
            INSERT OR REPLACE INTO empresas (
                codigo, ruc, razon_social, nombre_comercial, direccion, 
                telefono, email, representante_legal, dni_representante, 
                estado, tipo_empresa, activo, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            # Ejecutar inserción usando cursor
            cursor = self.client.cursor()
            cursor.execute(insert_sql, [
                empresa_data['codigo'],
                empresa_data['ruc'],
                empresa_data['razon_social'],
                empresa_data['razon_social'],  # nombre_comercial = razon_social por defecto
                empresa_data['direccion'],
                empresa_data['telefono'],
                empresa_data['email'],
                empresa_data['representante_legal'],
                empresa_data['dni_representante'],
                empresa_data['estado'],
                'SAC',  # tipo_empresa por defecto
                True,  # activo = True
                datetime.now().isoformat()
            ])
            
            # Commit la transacción
            self.client.commit()
            
            logger.info(f"✅ Empresa {ruc} guardada en Turso")
            return cursor.lastrowid
            
        except Exception as e:
            logger.error(f"❌ Error guardando empresa {ruc}: {e}")
            return None
    
    def _prepare_empresa_data(self, ruc: str, datos_consulta: Dict[str, Any]) -> Dict[str, str]:
        """
        Preparar datos de empresa desde respuesta de consulta
        """
        data = datos_consulta.get('data', {})
        contacto = data.get('contacto', {})
        miembros = data.get('miembros', [])
        
        # Obtener primer representante si existe
        representante_legal = ""
        dni_representante = ""
        
        if miembros:
            primer_miembro = miembros[0]
            representante_legal = primer_miembro.get('nombre', '')
            dni_representante = primer_miembro.get('numero_documento', '')
        
        # Generar código único para la empresa
        codigo = f"EMP-{ruc[-6:]}"  # Usar últimos 6 dígitos del RUC
        
        return {
            'codigo': codigo,
            'ruc': ruc,
            'razon_social': data.get('razon_social', ''),
            'direccion': contacto.get('direccion', '') or contacto.get('domicilio_fiscal', ''),
            'telefono': contacto.get('telefono', ''),
            'email': contacto.get('email', ''),
            'representante_legal': representante_legal,
            'dni_representante': dni_representante,
            'estado': 'ACTIVO'
        }
    
    def get_empresa_by_ruc(self, ruc: str) -> Optional[Dict[str, Any]]:
        """
        Obtener empresa por RUC
        """
        if not self.client:
            return None
            
        try:
            cursor = self.client.cursor()
            cursor.execute(
                "SELECT * FROM empresas WHERE ruc = ? LIMIT 1", 
                [ruc]
            )
            
            row = cursor.fetchone()
            if row:
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                return dict(zip(columns, row))
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error consultando empresa {ruc}: {e}")
            return None
    
    def list_empresas(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Listar empresas con paginación
        """
        if not self.client:
            return []
            
        try:
            cursor = self.client.cursor()
            cursor.execute(
                "SELECT * FROM empresas ORDER BY created_at DESC LIMIT ? OFFSET ?",
                [limit, offset]
            )
            
            rows = cursor.fetchall()
            if rows:
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                return [dict(zip(columns, row)) for row in rows]
            
            return []
            
        except Exception as e:
            logger.error(f"❌ Error listando empresas: {e}")
            return []
    
    def search_empresas(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Buscar empresas por RUC o razón social
        """
        if not self.client:
            return []
            
        try:
            cursor = self.client.cursor()
            search_query = f"%{query}%"
            cursor.execute("""
                SELECT * FROM empresas 
                WHERE ruc LIKE ? OR razon_social LIKE ?
                ORDER BY 
                    CASE WHEN ruc = ? THEN 1 ELSE 2 END,
                    razon_social
                LIMIT ?
            """, [search_query, search_query, query, limit])
            
            rows = cursor.fetchall()
            if rows:
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                return [dict(zip(columns, row)) for row in rows]
            
            return []
            
        except Exception as e:
            logger.error(f"❌ Error buscando empresas: {e}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Obtener estadísticas de la base de datos
        """
        if not self.client:
            return {"error": "Cliente no disponible"}
            
        try:
            cursor = self.client.cursor()
            
            # Total empresas
            cursor.execute("SELECT COUNT(*) FROM empresas")
            total_empresas = cursor.fetchone()[0]
            
            # Empresas por estado
            cursor.execute("""
                SELECT estado, COUNT(*) as count 
                FROM empresas 
                GROUP BY estado
            """)
            estados = {}
            for row in cursor.fetchall():
                estados[row[0] or 'UNKNOWN'] = row[1]
            
            # Empresas recientes (últimas 24h)
            cursor.execute("""
                SELECT COUNT(*) FROM empresas 
                WHERE datetime(created_at) >= datetime('now', '-1 day')
            """)
            empresas_recientes = cursor.fetchone()[0]
            
            return {
                'total_empresas': total_empresas,
                'empresas_recientes_24h': empresas_recientes,
                'empresas_por_estado': estados,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo estadísticas: {e}")
            return {"error": str(e)}
    
    def delete_empresa(self, ruc: str) -> bool:
        """
        Eliminar empresa por RUC
        """
        if not self.client:
            logger.warning("⚠️ Cliente Turso no disponible")
            return False
            
        try:
            cursor = self.client.cursor()
            cursor.execute("DELETE FROM empresas WHERE ruc = ?", (ruc,))
            
            # Verificar si se eliminó alguna fila
            rows_affected = cursor.rowcount
            logger.info(f"✅ Empresa {ruc} eliminada. Filas afectadas: {rows_affected}")
            
            return rows_affected > 0
            
        except Exception as e:
            logger.error(f"❌ Error eliminando empresa {ruc}: {e}")
            return False
    
    def close(self):
        """Cerrar cliente"""
        if self.client:
            self.client.close()
            logger.info("✅ Cliente Turso cerrado")