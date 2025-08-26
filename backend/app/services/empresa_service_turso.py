"""
Servicio para gestionar empresas en Turso
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
import json
from app.core.database_turso import execute_query, get_turso_client
from app.models.consolidated import EmpresaConsolidada

class EmpresaServiceTurso:
    
    @staticmethod
    async def existe_empresa(ruc: str) -> bool:
        """Verificar si una empresa ya existe por RUC"""
        try:
            result = await execute_query(
                "SELECT COUNT(*) as count FROM empresas WHERE ruc = ?",
                [ruc]
            )
            count = result.rows[0]["count"] if result.rows else 0
            return count > 0
        except Exception as e:
            print(f"❌ Error verificando empresa: {e}")
            return False

    @staticmethod
    async def obtener_empresa_por_ruc(ruc: str) -> Optional[Dict[str, Any]]:
        """Obtener empresa por RUC con sus representantes"""
        try:
            # Obtener empresa
            empresa_result = await execute_query(
                "SELECT * FROM empresas WHERE ruc = ? AND activo = 1",
                [ruc]
            )
            
            if not empresa_result.rows:
                return None
            
            # Convertir tupla a diccionario usando los nombres de columnas
            empresa_row = empresa_result.rows[0]
            empresa_fields = [
                'id', 'codigo', 'ruc', 'razon_social', 'nombre_comercial', 
                'email', 'telefono', 'celular', 'direccion', 'distrito', 
                'provincia', 'departamento', 'ubigeo', 'representante_legal', 
                'dni_representante', 'capital_social', 'fecha_constitucion', 
                'estado', 'tipo_empresa', 'categoria_contratista', 'especialidades',
                'numero_registro_nacional', 'vigencia_registro_desde', 'vigencia_registro_hasta',
                'observaciones', 'activo', 'created_at', 'updated_at', 
                'created_by', 'updated_by', 'version'
            ]
            empresa = dict(zip(empresa_fields, empresa_row))
            
            # Obtener representantes
            repr_result = await execute_query(
                "SELECT * FROM empresa_representantes WHERE empresa_id = ? AND activo = 1",
                [empresa["id"]]
            )
            
            # Convertir representantes de tuplas a diccionarios
            representantes = []
            if repr_result.rows:
                repr_fields = [
                    'id', 'empresa_id', 'nombre', 'cargo', 'tipo_documento', 
                    'numero_documento', 'participacion', 'fecha_desde', 'fuente', 
                    'es_principal', 'estado', 'activo', 'created_at', 'updated_at', 
                    'created_by', 'updated_by'
                ]
                for row in repr_result.rows:
                    representantes.append(dict(zip(repr_fields, row)))
            
            empresa["representantes"] = representantes
            empresa["total_representantes"] = len(representantes)
            
            # Parsear JSON fields
            if empresa.get("especialidades"):
                try:
                    empresa["especialidades"] = json.loads(empresa["especialidades"])
                except:
                    empresa["especialidades"] = []
            
            return empresa
            
        except Exception as e:
            print(f"❌ Error obteniendo empresa: {e}")
            return None

    @staticmethod
    async def generar_codigo_empresa() -> str:
        """Generar código único para empresa"""
        try:
            result = await execute_query(
                "SELECT COUNT(*) as count FROM empresas"
            )
            total = result.rows[0]["count"] if result.rows else 0
            return f"EMP-{total + 1:06d}"
        except Exception as e:
            print(f"❌ Error generando código: {e}")
            return f"EMP-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    @staticmethod
    async def guardar_empresa_consolidada(
        empresa_consolidada: EmpresaConsolidada
    ) -> Optional[Dict[str, Any]]:
        """Guardar empresa desde datos consolidados de scraping"""
        try:
            # Verificar si ya existe
            if await EmpresaServiceTurso.existe_empresa(empresa_consolidada.ruc):
                raise ValueError(f"Ya existe una empresa con RUC {empresa_consolidada.ruc}")
            
            # Generar código único
            codigo = await EmpresaServiceTurso.generar_codigo_empresa()
            
            # Preparar datos de empresa
            now = datetime.now().isoformat()
            # Convertir especialidades_detalle a formato JSON serializable
            especialidades = empresa_consolidada.especialidades_detalle or []
            especialidades_data = []
            for esp in especialidades:
                if hasattr(esp, 'dict'):
                    especialidades_data.append(esp.dict())
                elif isinstance(esp, dict):
                    especialidades_data.append(esp)
                else:
                    especialidades_data.append(str(esp))
            especialidades_json = json.dumps(especialidades_data)
            
            # Insertar empresa
            empresa_sql = """
            INSERT INTO empresas (
                codigo, ruc, razon_social, nombre_comercial, email, telefono, celular,
                direccion, distrito, provincia, departamento, ubigeo,
                estado, tipo_empresa, categoria_contratista, especialidades,
                numero_registro_nacional, activo, created_at, updated_at, version
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, 1)
            """
            
            tipo_empresa = "PERSONA_NATURAL" if empresa_consolidada.ruc.startswith('10') else "SAC"
            
            await execute_query(empresa_sql, [
                codigo,
                empresa_consolidada.ruc,
                empresa_consolidada.razon_social,
                empresa_consolidada.razon_social,  # usar razon_social como nombre_comercial
                empresa_consolidada.contacto.email or "",
                empresa_consolidada.contacto.telefono or "",
                "",  # celular
                empresa_consolidada.contacto.direccion or "",
                "",  # distrito
                "",  # provincia 
                empresa_consolidada.contacto.departamento or "",
                "",  # ubigeo
                empresa_consolidada.registro.estado_sunat or "ACTIVO",
                tipo_empresa,
                empresa_consolidada.capacidad_contratacion or "",
                especialidades_json,
                "",  # numero_registro_nacional
                now,
                now
            ])
            
            # Obtener ID de la empresa recién creada
            empresa_id_result = await execute_query(
                "SELECT id FROM empresas WHERE ruc = ?",
                [empresa_consolidada.ruc]
            )
            
            if not empresa_id_result.rows:
                raise Exception("No se pudo obtener ID de empresa creada")
            
            empresa_id = empresa_id_result.rows[0]["id"]
            
            # Insertar representantes
            representantes_creados = 0
            representante_principal = None
            
            for idx, representante in enumerate(empresa_consolidada.miembros):
                es_principal = idx == 0  # El primer representante es principal
                
                repr_sql = """
                INSERT INTO empresa_representantes (
                    empresa_id, nombre, cargo, tipo_documento, numero_documento,
                    participacion, fuente, es_principal, estado, activo,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'ACTIVO', 1, ?, ?)
                """
                
                await execute_query(repr_sql, [
                    empresa_id,
                    representante.nombre,
                    representante.cargo,
                    representante.tipo_documento or "DNI",
                    representante.numero_documento,
                    representante.participacion,
                    representante.fuente,
                    1 if es_principal else 0,
                    now,
                    now
                ])
                
                representantes_creados += 1
                
                if es_principal:
                    representante_principal = representante
            
            # Actualizar representante legal en empresa
            if representante_principal:
                await execute_query(
                    "UPDATE empresas SET representante_legal = ?, dni_representante = ? WHERE id = ?",
                    [representante_principal.nombre, representante_principal.numero_documento, empresa_id]
                )
            
            print(f"✅ Empresa {empresa_consolidada.ruc} guardada con {representantes_creados} representantes")
            
            # Retornar empresa completa
            return await EmpresaServiceTurso.obtener_empresa_por_ruc(empresa_consolidada.ruc)
            
        except Exception as e:
            print(f"❌ Error guardando empresa: {e}")
            raise

    @staticmethod
    async def listar_empresas(
        limit: int = 10,
        offset: int = 0,
        buscar: Optional[str] = None
    ) -> tuple[List[Dict[str, Any]], int]:
        """Listar empresas con paginación y búsqueda"""
        try:
            # Base query
            where_clause = "WHERE activo = 1"
            params = []
            
            # Añadir búsqueda
            if buscar:
                where_clause += " AND (ruc LIKE ? OR razon_social LIKE ? OR nombre_comercial LIKE ?)"
                buscar_param = f"%{buscar}%"
                params.extend([buscar_param, buscar_param, buscar_param])
            
            # Contar total
            count_sql = f"SELECT COUNT(*) as count FROM empresas {where_clause}"
            count_result = await execute_query(count_sql, params)
            total = count_result.rows[0]["count"] if count_result.rows else 0
            
            # Obtener empresas con paginación
            empresas_sql = f"""
            SELECT * FROM empresas {where_clause} 
            ORDER BY updated_at DESC 
            LIMIT ? OFFSET ?
            """
            
            empresas_result = await execute_query(empresas_sql, params + [limit, offset])
            empresas = [dict(row) for row in empresas_result.rows] if empresas_result.rows else []
            
            # Para cada empresa, obtener representantes
            for empresa in empresas:
                repr_result = await execute_query(
                    "SELECT * FROM empresa_representantes WHERE empresa_id = ? AND activo = 1",
                    [empresa["id"]]
                )
                empresa["representantes"] = [dict(row) for row in repr_result.rows] if repr_result.rows else []
                empresa["total_representantes"] = len(empresa["representantes"])
                
                # Parsear especialidades JSON
                if empresa.get("especialidades"):
                    try:
                        empresa["especialidades"] = json.loads(empresa["especialidades"])
                    except:
                        empresa["especialidades"] = []
            
            return empresas, total
            
        except Exception as e:
            print(f"❌ Error listando empresas: {e}")
            return [], 0