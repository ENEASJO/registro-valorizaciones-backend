"""
Servicio para manejo de empresas y representantes
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload
from datetime import datetime
import re

from app.models.empresa import (
    EmpresaDB, 
    RepresentanteDB,
    EmpresaCreateSchema,
    EmpresaResponse,
    RepresentanteResponse,
    RepresentanteSchema
)

class EmpresaService:
    """Servicio para gestionar empresas y representantes"""
    
    @staticmethod
    async def crear_empresa_con_representantes(
        session: AsyncSession,
        empresa_data: EmpresaCreateSchema,
        created_by: Optional[int] = None
    ) -> EmpresaResponse:
        """
        Crear una empresa con todos sus representantes
        """
        try:
            # 1. Validar que no exista el RUC
            existing_empresa = await session.execute(
                select(EmpresaDB).where(EmpresaDB.ruc == empresa_data.ruc)
            )
            if existing_empresa.scalar_one_or_none():
                raise ValueError(f"Ya existe una empresa con RUC {empresa_data.ruc}")
            
            # 2. Generar código único
            codigo = await EmpresaService._generate_empresa_codigo(session)
            
            # 3. Determinar tipo de empresa basado en RUC
            tipo_empresa = EmpresaService._determine_tipo_empresa(empresa_data.ruc)
            
            # 4. Crear la empresa
            nueva_empresa = EmpresaDB(
                codigo=codigo,
                ruc=empresa_data.ruc,
                razon_social=empresa_data.razon_social,
                email=empresa_data.email,
                celular=empresa_data.celular,
                telefono=empresa_data.celular,  # Usar celular como teléfono principal
                direccion=empresa_data.direccion,
                estado=empresa_data.estado,
                tipo_empresa=tipo_empresa,
                especialidades=empresa_data.especialidades_oece,
                created_by=created_by,
                updated_by=created_by
            )
            
            # 5. Determinar representante principal
            representante_principal = None
            if empresa_data.representantes:
                if (empresa_data.representante_principal_id >= 0 and 
                    empresa_data.representante_principal_id < len(empresa_data.representantes)):
                    representante_principal = empresa_data.representantes[empresa_data.representante_principal_id]
                else:
                    # Si no hay índice válido, usar el primero
                    representante_principal = empresa_data.representantes[0]
                
                # Asignar datos del representante principal a la empresa
                nueva_empresa.representante_legal = representante_principal.nombre
                nueva_empresa.dni_representante = representante_principal.numero_documento
            
            # 6. Agregar empresa a la sesión
            session.add(nueva_empresa)
            await session.flush()  # Para obtener el ID
            
            # 7. Crear todos los representantes
            representantes_creados = []
            for i, repr_data in enumerate(empresa_data.representantes):
                es_principal = (i == empresa_data.representante_principal_id)
                
                nuevo_representante = RepresentanteDB(
                    empresa_id=nueva_empresa.id,
                    nombre=repr_data.nombre,
                    cargo=repr_data.cargo,
                    tipo_documento=repr_data.tipo_documento or "DNI",
                    numero_documento=repr_data.numero_documento,
                    participacion=repr_data.participacion,
                    fecha_desde=EmpresaService._parse_date_string(repr_data.fecha_desde),
                    fuente=repr_data.fuente,
                    es_principal=es_principal,
                    created_by=created_by,
                    updated_by=created_by
                )
                
                session.add(nuevo_representante)
                representantes_creados.append(nuevo_representante)
            
            # 8. Confirmar cambios
            await session.commit()
            
            # 9. Recargar con relaciones
            await session.refresh(nueva_empresa, ['representantes'])
            
            # 10. Crear respuesta
            return EmpresaResponse.from_db_model(nueva_empresa)
            
        except Exception as e:
            await session.rollback()
            raise Exception(f"Error creando empresa: {str(e)}")
    
    @staticmethod
    async def obtener_empresa_por_id(
        session: AsyncSession,
        empresa_id: int
    ) -> Optional[EmpresaResponse]:
        """Obtener empresa por ID con sus representantes"""
        try:
            result = await session.execute(
                select(EmpresaDB)
                .options(selectinload(EmpresaDB.representantes))
                .where(and_(EmpresaDB.id == empresa_id, EmpresaDB.activo == True))
            )
            empresa = result.scalar_one_or_none()
            
            if not empresa:
                return None
                
            return EmpresaResponse.from_db_model(empresa)
            
        except Exception as e:
            raise Exception(f"Error obteniendo empresa: {str(e)}")
    
    @staticmethod
    async def obtener_empresa_por_ruc(
        session: AsyncSession,
        ruc: str
    ) -> Optional[EmpresaResponse]:
        """Obtener empresa por RUC con sus representantes"""
        try:
            result = await session.execute(
                select(EmpresaDB)
                .options(selectinload(EmpresaDB.representantes))
                .where(and_(EmpresaDB.ruc == ruc, EmpresaDB.activo == True))
            )
            empresa = result.scalar_one_or_none()
            
            if not empresa:
                return None
                
            return EmpresaResponse.from_db_model(empresa)
            
        except Exception as e:
            raise Exception(f"Error obteniendo empresa por RUC: {str(e)}")
    
    @staticmethod
    async def listar_empresas(
        session: AsyncSession,
        page: int = 1,
        per_page: int = 20,
        search: Optional[str] = None,
        estado: Optional[str] = None
    ) -> Dict[str, Any]:
        """Listar empresas con filtros y paginación"""
        try:
            # Construir query base
            query = select(EmpresaDB).options(selectinload(EmpresaDB.representantes))
            conditions = [EmpresaDB.activo == True]
            
            # Aplicar filtros
            if search:
                search_term = f"%{search}%"
                conditions.append(
                    or_(
                        EmpresaDB.razon_social.ilike(search_term),
                        EmpresaDB.nombre_comercial.ilike(search_term),
                        EmpresaDB.ruc.ilike(search_term),
                        EmpresaDB.representante_legal.ilike(search_term)
                    )
                )
            
            if estado:
                conditions.append(EmpresaDB.estado == estado)
            
            # Aplicar condiciones
            if conditions:
                query = query.where(and_(*conditions))
            
            # Contar total
            count_query = select(EmpresaDB.id).where(and_(*conditions))
            total_result = await session.execute(count_query)
            total = len(total_result.all())
            
            # Aplicar paginación
            offset = (page - 1) * per_page
            query = query.offset(offset).limit(per_page)
            query = query.order_by(EmpresaDB.created_at.desc())
            
            # Ejecutar query
            result = await session.execute(query)
            empresas_db = result.scalars().all()
            
            # Convertir a respuesta
            empresas = [EmpresaResponse.from_db_model(empresa) for empresa in empresas_db]
            
            return {
                "empresas": empresas,
                "total": total,
                "page": page,
                "per_page": per_page,
                "total_pages": (total + per_page - 1) // per_page
            }
            
        except Exception as e:
            raise Exception(f"Error listando empresas: {str(e)}")
    
    @staticmethod
    async def actualizar_empresa(
        session: AsyncSession,
        empresa_id: int,
        empresa_data: Dict[str, Any],
        updated_by: Optional[int] = None
    ) -> Optional[EmpresaResponse]:
        """Actualizar empresa existente"""
        try:
            # Obtener empresa
            result = await session.execute(
                select(EmpresaDB)
                .options(selectinload(EmpresaDB.representantes))
                .where(and_(EmpresaDB.id == empresa_id, EmpresaDB.activo == True))
            )
            empresa = result.scalar_one_or_none()
            
            if not empresa:
                return None
            
            # Actualizar campos permitidos
            campos_permitidos = [
                'razon_social', 'nombre_comercial', 'email', 'telefono', 'celular',
                'direccion', 'distrito', 'provincia', 'departamento',
                'representante_legal', 'dni_representante', 'estado', 
                'categoria_contratista', 'especialidades', 'observaciones'
            ]
            
            for campo in campos_permitidos:
                if campo in empresa_data:
                    setattr(empresa, campo, empresa_data[campo])
            
            empresa.updated_by = updated_by
            empresa.version += 1
            
            await session.commit()
            await session.refresh(empresa, ['representantes'])
            
            return EmpresaResponse.from_db_model(empresa)
            
        except Exception as e:
            await session.rollback()
            raise Exception(f"Error actualizando empresa: {str(e)}")
    
    @staticmethod
    async def eliminar_empresa(
        session: AsyncSession,
        empresa_id: int,
        deleted_by: Optional[int] = None
    ) -> bool:
        """Eliminación lógica de empresa"""
        try:
            result = await session.execute(
                select(EmpresaDB).where(
                    and_(EmpresaDB.id == empresa_id, EmpresaDB.activo == True)
                )
            )
            empresa = result.scalar_one_or_none()
            
            if not empresa:
                return False
            
            # Eliminación lógica
            empresa.activo = False
            empresa.estado = "ELIMINADO"
            empresa.updated_by = deleted_by
            empresa.version += 1
            
            # También marcar representantes como inactivos
            representantes_result = await session.execute(
                select(RepresentanteDB).where(RepresentanteDB.empresa_id == empresa_id)
            )
            for representante in representantes_result.scalars().all():
                representante.activo = False
                representante.estado = "ELIMINADO"
                representante.updated_by = deleted_by
            
            await session.commit()
            return True
            
        except Exception as e:
            await session.rollback()
            raise Exception(f"Error eliminando empresa: {str(e)}")
    
    # =================================================================
    # MÉTODOS AUXILIARES
    # =================================================================
    
    @staticmethod
    async def _generate_empresa_codigo(session: AsyncSession) -> str:
        """Generar código único para empresa"""
        # Obtener el último número
        result = await session.execute(
            select(EmpresaDB.codigo)
            .where(EmpresaDB.codigo.like('EMP%'))
            .order_by(EmpresaDB.codigo.desc())
            .limit(1)
        )
        ultimo_codigo = result.scalar_one_or_none()
        
        if ultimo_codigo:
            # Extraer número y incrementar
            numero = int(re.findall(r'\d+', ultimo_codigo)[0]) + 1
        else:
            numero = 1
        
        return f"EMP{numero:03d}"
    
    @staticmethod
    def _determine_tipo_empresa(ruc: str) -> str:
        """Determinar tipo de empresa basado en RUC"""
        if ruc.startswith('10'):
            return 'PERSONA_NATURAL'
        elif ruc.startswith('20'):
            # Por defecto SAC para empresas, se puede especificar más tarde
            return 'SAC'
        else:
            return 'OTROS'
    
    @staticmethod
    def _parse_date_string(date_str: Optional[str]):
        """Parsear string de fecha a date object"""
        if not date_str or date_str in ['-', '']:
            return None
        
        try:
            # Intentar diferentes formatos
            formats = ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y']
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt).date()
                except ValueError:
                    continue
            return None
        except:
            return None
    
    @staticmethod
    def validar_ruc(ruc: str) -> bool:
        """Validar formato de RUC"""
        if not ruc or len(ruc) != 11:
            return False
        
        if not ruc.isdigit():
            return False
        
        # Debe comenzar con 10 o 20
        if not (ruc.startswith('10') or ruc.startswith('20')):
            return False
        
        return True