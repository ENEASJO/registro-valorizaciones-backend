"""
Modelos de base de datos para empresas y representantes
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, TIMESTAMP, Numeric, Date, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime, date
from app.core.database import Base

class EmpresaDB(Base):
    """Modelo de base de datos para empresas"""
    __tablename__ = "empresas"
    
    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(20), unique=True, nullable=False, index=True)
    ruc = Column(String(11), unique=True, nullable=False, index=True)
    razon_social = Column(String(255), nullable=False, index=True)
    nombre_comercial = Column(String(255), nullable=True)
    
    # Datos de contacto
    email = Column(String(100), nullable=True)
    telefono = Column(String(20), nullable=True)
    celular = Column(String(20), nullable=True)
    direccion = Column(Text, nullable=True)
    distrito = Column(String(100), nullable=True)
    provincia = Column(String(100), nullable=True)
    departamento = Column(String(100), nullable=True)
    ubigeo = Column(String(6), nullable=True)
    
    # Datos legales y financieros
    representante_legal = Column(String(255), nullable=True)
    dni_representante = Column(String(8), nullable=True)
    capital_social = Column(Numeric(15, 2), nullable=True)
    fecha_constitucion = Column(Date, nullable=True)
    
    # Estados y clasificación
    estado = Column(String(20), nullable=False, default="ACTIVO")
    tipo_empresa = Column(String(50), nullable=False)
    categoria_contratista = Column(String(10), nullable=True)
    
    # Especialidades (JSON)
    especialidades = Column(JSON, nullable=True)
    
    # Documentos y certificaciones
    numero_registro_nacional = Column(String(50), nullable=True)
    vigencia_registro_desde = Column(Date, nullable=True)
    vigencia_registro_hasta = Column(Date, nullable=True)
    
    # Metadatos
    observaciones = Column(Text, nullable=True)
    activo = Column(Boolean, nullable=False, default=True)
    
    # Auditoría
    created_at = Column(TIMESTAMP, nullable=False, default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, nullable=False, default=func.current_timestamp(), onupdate=func.current_timestamp())
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)
    version = Column(Integer, nullable=False, default=1)
    
    # Relaciones
    representantes = relationship("RepresentanteDB", back_populates="empresa", cascade="all, delete-orphan")

class RepresentanteDB(Base):
    """Modelo de base de datos para representantes de empresas"""
    __tablename__ = "empresa_representantes"
    
    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False)
    
    # Datos del representante
    nombre = Column(String(255), nullable=False)
    cargo = Column(String(100), nullable=True)
    tipo_documento = Column(String(10), nullable=True, default="DNI")
    numero_documento = Column(String(20), nullable=False)
    
    # Datos adicionales
    participacion = Column(String(50), nullable=True)
    fecha_desde = Column(Date, nullable=True)
    fuente = Column(String(20), nullable=True)  # 'SUNAT', 'OECE', 'AMBOS'
    
    # Principal
    es_principal = Column(Boolean, nullable=False, default=False)
    
    # Estados
    estado = Column(String(20), nullable=False, default="ACTIVO")
    activo = Column(Boolean, nullable=False, default=True)
    
    # Auditoría
    created_at = Column(TIMESTAMP, nullable=False, default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, nullable=False, default=func.current_timestamp(), onupdate=func.current_timestamp())
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)
    
    # Relaciones
    empresa = relationship("EmpresaDB", back_populates="representantes")

# =================================================================
# MODELOS PYDANTIC PARA API
# =================================================================

class RepresentanteSchema(BaseModel):
    """Schema para representante"""
    nombre: str = Field(..., description="Nombre completo del representante")
    cargo: str = Field(..., description="Cargo del representante")
    numero_documento: str = Field(..., description="Número de documento")
    tipo_documento: Optional[str] = Field("DNI", description="Tipo de documento")
    fuente: Optional[str] = Field(None, description="Fuente de los datos")
    participacion: Optional[str] = Field(None, description="Porcentaje de participación")
    fecha_desde: Optional[str] = Field(None, description="Fecha desde cuando ejerce el cargo")

class EmpresaCreateSchema(BaseModel):
    """Schema para crear una empresa con representantes"""
    # Datos básicos
    ruc: str = Field(..., description="RUC de 11 dígitos")
    razon_social: str = Field(..., description="Razón social de la empresa")
    
    # Contacto
    email: Optional[str] = Field(None, description="Email corporativo")
    celular: Optional[str] = Field(None, description="Teléfono/celular")
    direccion: Optional[str] = Field(None, description="Dirección completa")
    
    # Representantes
    representantes: List[RepresentanteSchema] = Field([], description="Lista de representantes")
    representante_principal_id: int = Field(0, description="Índice del representante principal")
    
    # Estados
    estado: str = Field("ACTIVO", description="Estado de la empresa")
    
    # Datos consolidados (solo lectura)
    especialidades_oece: Optional[List[str]] = Field([], description="Especialidades OECE")
    estado_sunat: Optional[str] = Field(None, description="Estado en SUNAT")
    estado_osce: Optional[str] = Field(None, description="Estado en OSCE")
    fuentes_consultadas: Optional[List[str]] = Field([], description="Fuentes consultadas")
    capacidad_contratacion: Optional[str] = Field(None, description="Capacidad de contratación")

class RepresentanteResponse(BaseModel):
    """Schema de respuesta para representante"""
    id: int
    nombre: str
    cargo: str
    numero_documento: str
    tipo_documento: Optional[str] = None
    fuente: Optional[str] = None
    participacion: Optional[str] = None
    fecha_desde: Optional[date] = None
    es_principal: bool
    estado: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class EmpresaResponse(BaseModel):
    """Schema de respuesta para empresa"""
    id: int
    codigo: str
    ruc: str
    razon_social: str
    nombre_comercial: Optional[str] = None
    email: Optional[str] = None
    telefono: Optional[str] = None
    celular: Optional[str] = None
    direccion: Optional[str] = None
    representante_legal: Optional[str] = None
    dni_representante: Optional[str] = None
    estado: str
    tipo_empresa: str
    categoria_contratista: Optional[str] = None
    especialidades: Optional[List[str]] = None
    representantes: List[RepresentanteResponse] = []
    total_representantes: int = 0
    activo: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        
    @classmethod
    def from_db_model(cls, empresa_db: EmpresaDB):
        """Crear respuesta desde modelo de BD"""
        return cls(
            id=empresa_db.id,
            codigo=empresa_db.codigo,
            ruc=empresa_db.ruc,
            razon_social=empresa_db.razon_social,
            nombre_comercial=empresa_db.nombre_comercial,
            email=empresa_db.email,
            telefono=empresa_db.telefono,
            celular=empresa_db.celular,
            direccion=empresa_db.direccion,
            representante_legal=empresa_db.representante_legal,
            dni_representante=empresa_db.dni_representante,
            estado=empresa_db.estado,
            tipo_empresa=empresa_db.tipo_empresa,
            categoria_contratista=empresa_db.categoria_contratista,
            especialidades=empresa_db.especialidades or [],
            representantes=[
                RepresentanteResponse.from_attributes(repr) for repr in empresa_db.representantes
            ],
            total_representantes=len(empresa_db.representantes),
            activo=empresa_db.activo,
            created_at=empresa_db.created_at,
            updated_at=empresa_db.updated_at
        )

class EmpresaListResponse(BaseModel):
    """Schema de respuesta para lista de empresas"""
    empresas: List[EmpresaResponse]
    total: int
    page: int = 1
    per_page: int = 10