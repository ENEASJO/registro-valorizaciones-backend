"""
Servicio para empresas usando Supabase
"""
import logging
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
import requests
import json

logger = logging.getLogger(__name__)

class EmpresaServiceSupabase:
    """Servicio para operaciones CRUD de empresas en Supabase"""
    
    def __init__(self):
        self.supabase_url = "https://ujujrbedclmsdkjcupec.supabase.co"
        self.anon_key = os.getenv("SUPABASE_ANON_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVqdWpyYmVkY2xtc2RramN1cGVjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY4MzE1MTYsImV4cCI6MjA3MjQwNzUxNn0.X4LtoBuIgStdZundCd-DSwas1UN07xQUl6lA7aFP3t8")
        
        self.headers = {
            'apikey': self.anon_key,
            'Authorization': f'Bearer {self.anon_key}',
            'Content-Type': 'application/json'
        }
        
        self._verificar_conexion()
    
    def _verificar_conexion(self):
        """Verificar que podemos conectar a Supabase"""
        try:
            response = requests.get(f"{self.supabase_url}/rest/v1/", headers=self.headers, timeout=10)
            if response.status_code == 200:
                logger.info("✅ Conexión a Supabase verificada")
            else:
                logger.warning(f"⚠️ Conexión Supabase: {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Error conectando a Supabase: {e}")
    
    def crear_tabla_empresas(self) -> bool:
        """Crear tabla empresas usando SQL directo"""
        create_sql = """
        CREATE TABLE IF NOT EXISTS public.empresas (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            codigo TEXT UNIQUE NOT NULL,
            ruc TEXT UNIQUE NOT NULL,
            razon_social TEXT NOT NULL,
            nombre_comercial TEXT,
            email TEXT,
            telefono TEXT,
            celular TEXT,
            direccion TEXT,
            distrito TEXT,
            provincia TEXT,
            departamento TEXT,
            representante_legal TEXT,
            dni_representante TEXT,
            estado TEXT DEFAULT 'ACTIVO',
            tipo_empresa TEXT DEFAULT 'SAC',
            datos_sunat JSONB,
            datos_osce JSONB,
            fuentes_consultadas TEXT[],
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );
        
        CREATE INDEX IF NOT EXISTS idx_empresas_ruc ON public.empresas(ruc);
        CREATE INDEX IF NOT EXISTS idx_empresas_codigo ON public.empresas(codigo);
        """
        
        try:
            # Intentar crear tabla via RPC
            data = {'query': create_sql}
            response = requests.post(
                f"{self.supabase_url}/rest/v1/rpc/exec", 
                headers=self.headers,
                json=data,
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                logger.info("✅ Tabla empresas creada/verificada")
                return True
            else:
                logger.warning(f"⚠️ Crear tabla: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error creando tabla: {e}")
            return False
    
    def guardar_empresa(self, datos_empresa: Dict[str, Any]) -> Optional[str]:
        """
        Guardar empresa en Supabase
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
                'datos_sunat': datos_empresa.get('datos_sunat') or {},
                'datos_osce': datos_empresa.get('datos_osce') or {},
                'fuentes_consultadas': datos_empresa.get('fuentes_consultadas', [])
            }
            
            # Intentar inserción (upsert)
            headers_upsert = self.headers.copy()
            headers_upsert['Prefer'] = 'resolution=merge-duplicates,return=representation'
            
            response = requests.post(
                f"{self.supabase_url}/rest/v1/empresas",
                headers=headers_upsert,
                json=empresa_data,
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    empresa_id = result[0].get('id')
                    logger.info(f"✅ Empresa guardada en Supabase - ID: {empresa_id}, RUC: {ruc}")
                    return empresa_id
                else:
                    logger.info(f"✅ Empresa guardada en Supabase (sin ID) - RUC: {ruc}")
                    return "supabase-success"
            else:
                logger.error(f"❌ Error guardando empresa: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error guardando empresa en Supabase: {e}")
            return None
    
    def listar_empresas(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Listar empresas desde Supabase
        """
        try:
            params = {
                'select': '*',
                'order': 'created_at.desc',
                'limit': limit
            }
            
            response = requests.get(
                f"{self.supabase_url}/rest/v1/empresas",
                headers=self.headers,
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                empresas = response.json()
                logger.info(f"📋 {len(empresas)} empresas obtenidas desde Supabase")
                return empresas
            else:
                logger.error(f"❌ Error listando empresas: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"❌ Error listando empresas desde Supabase: {e}")
            return []
    
    def obtener_empresa_por_ruc(self, ruc: str) -> Optional[Dict[str, Any]]:
        """
        Obtener empresa específica por RUC
        """
        try:
            params = {
                'select': '*',
                'ruc': f'eq.{ruc}',
                'limit': 1
            }
            
            response = requests.get(
                f"{self.supabase_url}/rest/v1/empresas",
                headers=self.headers,
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                empresas = response.json()
                if empresas and len(empresas) > 0:
                    return empresas[0]
                return None
            else:
                logger.error(f"❌ Error obteniendo empresa por RUC {ruc}: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error obteniendo empresa por RUC {ruc}: {e}")
            return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas básicas"""
        try:
            # Total de empresas
            response = requests.get(
                f"{self.supabase_url}/rest/v1/empresas",
                headers=self.headers,
                params={'select': 'count', 'head': 'true'},
                timeout=30
            )
            
            total = 0
            if response.status_code == 200:
                total = int(response.headers.get('Content-Range', '0').split('/')[-1])
            
            # Empresas activas
            response_activas = requests.get(
                f"{self.supabase_url}/rest/v1/empresas",
                headers=self.headers,
                params={'select': 'count', 'head': 'true', 'estado': 'eq.ACTIVO'},
                timeout=30
            )
            
            activas = 0
            if response_activas.status_code == 200:
                activas = int(response_activas.headers.get('Content-Range', '0').split('/')[-1])
            
            return {
                "total": total,
                "activas": activas,
                "inactivas": total - activas,
                "fuente": "supabase"
            }
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo estadísticas: {e}")
            return {"total": 0, "activas": 0, "error": str(e)}

# Instancia global
empresa_service_supabase = EmpresaServiceSupabase()