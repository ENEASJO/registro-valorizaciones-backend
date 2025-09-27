"""
Modelos de base de datos para empresas y representantes
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, TIMESTAMP, Numeric, Date, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from typing import Optional, List
from pydantic import BaseModel, Field, validator
from datetime import datetime, date
from app.core.database import Base
import re

class EmpresaDB(Base):
    """Modelo de base de datos para empresas"""
    __tablename__ = "empresas"
    __table_args__ = {'extend_existing': True}
    
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
    
    # Metadatos y entrada manual
    observaciones = Column(Text, nullable=True)
    activo = Column(Boolean, nullable=False, default=True)
    
    # Campos para entrada manual
    fuente_datos = Column(String(20), nullable=False, default="SCRAPING")  # MANUAL, SCRAPING, MIXTO
    fuentes_consultadas = Column(JSON, nullable=True)  # ["SUNAT", "OSCE", "MANUAL"]
    requiere_verificacion = Column(Boolean, nullable=False, default=False)
    calidad_datos = Column(String(20), nullable=False, default="BUENA")  # BUENA, ACEPTABLE, PARCIAL
    
    # Campos adicionales para entrada manual
    pagina_web = Column(String(255), nullable=True)
    redes_sociales = Column(JSON, nullable=True)  # {"facebook": "url", "linkedin": "url"}
    sector_economico = Column(String(100), nullable=True)
    tamaño_empresa = Column(String(20), nullable=True)  # MICRO, PEQUEÑA, MEDIANA, GRANDE
    
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
    __table_args__ = {'extend_existing': True}
    
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
    ruc: str = Field(..., description="RUC de 11 dígitos", regex=r'^\d{11}$')
    razon_social: str = Field(..., description="Razón social de la empresa", min_length=2, max_length=255)
    nombre_comercial: Optional[str] = Field(None, description="Nombre comercial de la empresa", max_length=255)

    # Contacto completo
    email: Optional[str] = Field(None, description="Email corporativo")
    telefono: Optional[str] = Field(None, description="Teléfono fijo")
    celular: Optional[str] = Field(None, description="Teléfono celular")
    direccion: Optional[str] = Field(None, description="Dirección completa")
    pagina_web: Optional[str] = Field(None, description="Página web corporativa")
    redes_sociales: Optional[dict] = Field(None, description="Redes sociales {facebook, linkedin, etc}")

    # Ubicación
    departamento: Optional[str] = Field(None, description="Departamento", max_length=100)
    provincia: Optional[str] = Field(None, description="Provincia", max_length=100)
    distrito: Optional[str] = Field(None, description="Distrito", max_length=100)
    ubigeo: Optional[str] = Field(None, description="Código de ubigeo", max_length=6)

    # Clasificación empresarial
    tipo_empresa: str = Field("SAC", description="Tipo de empresa")
    sector_economico: Optional[str] = Field(None, description="Sector económico", max_length=100)
    tamaño_empresa: Optional[str] = Field(None, description="Tamaño: MICRO, PEQUEÑA, MEDIANA, GRANDE")

    # Datos financieros y legales
    capital_social: Optional[float] = Field(None, description="Capital social")
    fecha_constitucion: Optional[str] = Field(None, description="Fecha de constitución")
    numero_registro_nacional: Optional[str] = Field(None, description="Número de registro nacional")

    # Representantes
    representantes: List[RepresentanteSchema] = Field([], description="Lista de representantes")
    representante_principal_id: int = Field(0, description="Índice del representante principal")

    # Estados
    estado: str = Field("ACTIVO", description="Estado de la empresa")

    # Categorización
    categoria_contratista: Optional[str] = Field(None, description="Categoría del contratista: EJECUTORA o SUPERVISORA")

    # Metadatos de entrada
    fuente_datos: str = Field("SCRAPING", description="MANUAL, SCRAPING o MIXTO")
    fuentes_consultadas: Optional[List[str]] = Field([], description="Fuentes consultadas: SUNAT, OSCE, MANUAL")
    requiere_verificacion: bool = Field(False, description="Requiere verificación posterior")
    calidad_datos: str = Field("BUENA", description="BUENA, ACEPTABLE o PARCIAL")
    observaciones: Optional[str] = Field(None, description="Observaciones adicionales")

    # Datos consolidados específicos (solo lectura)
    especialidades_oece: Optional[List[str]] = Field([], description="Especialidades OECE")
    estado_sunat: Optional[str] = Field(None, description="Estado en SUNAT")
    estado_osce: Optional[str] = Field(None, description="Estado en OSCE")
    capacidad_contratacion: Optional[str] = Field(None, description="Capacidad de contratación")

class RepresentanteResponse(BaseModel):
    """Schema de respuesta para representante"""
    id: str
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
    id: str
    codigo: str
    ruc: str
    razon_social: str
    nombre_comercial: Optional[str] = None
    
    # Contacto completo
    email: Optional[str] = None
    telefono: Optional[str] = None
    celular: Optional[str] = None
    direccion: Optional[str] = None
    pagina_web: Optional[str] = None
    redes_sociales: Optional[dict] = None
    
    # Ubicación
    departamento: Optional[str] = None
    provincia: Optional[str] = None
    distrito: Optional[str] = None
    ubigeo: Optional[str] = None
    
    # Clasificación
    sector_economico: Optional[str] = None
    tamaño_empresa: Optional[str] = None
    
    # Datos legales
    representante_legal: Optional[str] = None
    dni_representante: Optional[str] = None
    capital_social: Optional[float] = None
    fecha_constitucion: Optional[date] = None
    numero_registro_nacional: Optional[str] = None
    
    # Estados y clasificación
    estado: str
    tipo_empresa: str
    categoria_contratista: Optional[str] = None
    especialidades: Optional[List[str]] = None
    
    # Metadatos de entrada
    fuente_datos: str = "SCRAPING"
    fuentes_consultadas: Optional[List[str]] = None
    requiere_verificacion: bool = False
    calidad_datos: str = "BUENA"
    observaciones: Optional[str] = None
    
    # Representantes
    representantes: List[RepresentanteResponse] = []
    total_representantes: int = 0
    
    # Metadatos del sistema
    activo: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        
    @classmethod
    def from_db_model(cls, empresa_db: EmpresaDB):
        """Crear respuesta desde modelo de BD"""
        return cls(
            id=str(empresa_db.id),
            codigo=empresa_db.codigo,
            ruc=empresa_db.ruc,
            razon_social=empresa_db.razon_social,
            nombre_comercial=empresa_db.nombre_comercial,
            
            # Contacto completo
            email=empresa_db.email,
            telefono=empresa_db.telefono,
            celular=empresa_db.celular,
            direccion=empresa_db.direccion,
            pagina_web=getattr(empresa_db, 'pagina_web', None),
            redes_sociales=getattr(empresa_db, 'redes_sociales', None),
            
            # Ubicación
            departamento=empresa_db.departamento,
            provincia=empresa_db.provincia,
            distrito=empresa_db.distrito,
            ubigeo=empresa_db.ubigeo,
            
            # Clasificación
            sector_economico=getattr(empresa_db, 'sector_economico', None),
            tamaño_empresa=getattr(empresa_db, 'tamaño_empresa', None),
            
            # Datos legales
            representante_legal=empresa_db.representante_legal,
            dni_representante=empresa_db.dni_representante,
            capital_social=empresa_db.capital_social,
            fecha_constitucion=empresa_db.fecha_constitucion,
            numero_registro_nacional=empresa_db.numero_registro_nacional,
            
            # Estados y clasificación
            estado=empresa_db.estado,
            tipo_empresa=empresa_db.tipo_empresa,
            categoria_contratista=empresa_db.categoria_contratista,
            especialidades=empresa_db.especialidades or [],
            
            # Metadatos de entrada
            fuente_datos=getattr(empresa_db, 'fuente_datos', 'SCRAPING'),
            fuentes_consultadas=getattr(empresa_db, 'fuentes_consultadas', None),
            requiere_verificacion=getattr(empresa_db, 'requiere_verificacion', False),
            calidad_datos=getattr(empresa_db, 'calidad_datos', 'BUENA'),
            observaciones=empresa_db.observaciones,
            
            # Representantes
            representantes=[
                RepresentanteResponse.from_attributes(repr) for repr in empresa_db.representantes
            ],
            total_representantes=len(empresa_db.representantes),
            
            # Metadatos del sistema
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

# =================================================================
# MODELOS ESPECIALIZADOS PARA ENTRADA MANUAL
# =================================================================

class RepresentanteManualSchema(BaseModel):
    """Schema específico para representante con entrada manual"""
    nombre: str = Field(..., min_length=2, max_length=255, title="Nombre completo")
    cargo: str = Field(..., min_length=2, max_length=100, title="Cargo en la empresa")
    tipo_documento: str = Field("DNI", title="Tipo de documento")
    numero_documento: str = Field(..., min_length=8, max_length=20, title="Número de documento")
    es_principal: bool = Field(False, title="Es el representante principal?")
    participacion: Optional[str] = Field(None, title="Porcentaje de participación")
    fecha_desde: Optional[str] = Field(None, title="Fecha desde cuando ejerce el cargo")
    estado: str = Field("ACTIVO", title="Estado del representante")
    
    @validator('numero_documento')
    def validar_numero_documento(cls, v, values):
        tipo_doc = values.get('tipo_documento', 'DNI')
        if tipo_doc == 'DNI':
            if not v.isdigit() or len(v) != 8:
                raise ValueError('DNI debe tener exactamente 8 dígitos numéricos')
        elif tipo_doc == 'CE':
            if len(v) < 9 or len(v) > 12:
                raise ValueError('Carné de Extranjería debe tener entre 9 y 12 caracteres')
        elif tipo_doc == 'PASAPORTE':
            if len(v) < 6 or len(v) > 15:
                raise ValueError('Pasaporte debe tener entre 6 y 15 caracteres')
        return v
    
    @validator('nombre')
    def validar_nombre(cls, v):
        # Solo letras, espacios y algunos caracteres especiales
        if not re.match(r"^[A-ZÁÉÍÓÚÑ][a-záéíóúñA-ZÁÉÍÓÚÑ\s\.,'\-]+$", v):
            raise ValueError('Nombre debe contener solo letras, espacios y caracteres válidos')
        return v.strip().title()
    
    @validator('cargo')
    def validar_cargo(cls, v):
        return v.strip().upper()
    
    @validator('fecha_desde')
    def validar_fecha_desde(cls, v):
        if v and v.strip():
            try:
                datetime.strptime(v, '%Y-%m-%d')
            except ValueError:
                try:
                    datetime.strptime(v, '%d/%m/%Y')
                    # Convertir al formato estándar
                    fecha = datetime.strptime(v, '%d/%m/%Y')
                    return fecha.strftime('%Y-%m-%d')
                except ValueError:
                    raise ValueError('Fecha debe estar en formato YYYY-MM-DD o DD/MM/YYYY')
        return v

class ContactoManualSchema(BaseModel):
    """Schema para contacto con entrada manual"""
    email: Optional[str] = Field(None, title="Email corporativo")
    telefono: Optional[str] = Field(None, title="Teléfono fijo")
    celular: Optional[str] = Field(None, title="Celular")
    direccion: Optional[str] = Field(None, title="Dirección completa")
    pagina_web: Optional[str] = Field(None, title="Página web corporativa")
    
    @validator('email')
    def validar_email(cls, v):
        if v and v.strip():
            email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_regex, v.strip()):
                raise ValueError('Email debe tener formato válido')
            return v.strip().lower()
        return v
    
    @validator('telefono', 'celular')
    def validar_telefono(cls, v):
        if v and v.strip():
            # Permitir números con espacios, guiones y paréntesis
            telefono_limpio = re.sub(r'[\s\-\(\)]+', '', v.strip())
            if not telefono_limpio.isdigit() or len(telefono_limpio) < 7 or len(telefono_limpio) > 15:
                raise ValueError('Teléfono debe tener entre 7 y 15 dígitos')
            return telefono_limpio
        return v
    
    @validator('pagina_web')
    def validar_pagina_web(cls, v):
        if v and v.strip():
            url = v.strip().lower()
            if not url.startswith('http'):
                url = 'https://' + url
            # Validación básica de URL
            if not re.match(r'^https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', url):
                raise ValueError('Página web debe tener formato válido')
            return url
        return v

class EmpresaManualCompleta(BaseModel):
    """Modelo completo para empresa con entrada manual y validaciones robustas"""
    
    # Datos básicos (obligatorios)
    ruc: str = Field(..., regex=r'^\d{11}$', title="RUC de 11 dígitos")
    razon_social: str = Field(..., min_length=3, max_length=255, title="Razón social")
    
    # Datos adicionales básicos
    nombre_comercial: Optional[str] = Field(None, max_length=255, title="Nombre comercial")
    tipo_empresa: str = Field("SAC", title="Tipo de empresa")
    estado: str = Field("ACTIVO", title="Estado de la empresa")
    
    # Ubicación
    departamento: Optional[str] = Field(None, max_length=100, title="Departamento")
    provincia: Optional[str] = Field(None, max_length=100, title="Provincia") 
    distrito: Optional[str] = Field(None, max_length=100, title="Distrito")
    ubigeo: Optional[str] = Field(None, max_length=6, title="Código UBIGEO")
    
    # Contacto
    contacto: Optional[ContactoManualSchema] = Field(None, title="Información de contacto")
    
    # Representantes
    representantes: List[RepresentanteManualSchema] = Field([], title="Lista de representantes")
    
    # Clasificación empresarial
    categoria_contratista: Optional[str] = Field(None, title="EJECUTORA o SUPERVISORA")
    especialidades: List[str] = Field([], title="Especialidades de la empresa")
    sector_economico: Optional[str] = Field(None, title="Sector económico", max_length=100)
    tamaño_empresa: Optional[str] = Field(None, title="MICRO, PEQUEÑA, MEDIANA, GRANDE")
    
    # Datos financieros y legales opcionales
    capital_social: Optional[float] = Field(None, title="Capital social", ge=0)
    fecha_constitucion: Optional[str] = Field(None, title="Fecha de constitución")
    numero_registro_nacional: Optional[str] = Field(None, title="Número de registro nacional")
    
    # Redes sociales
    redes_sociales: Optional[dict] = Field(None, title="Redes sociales")
    
    # Datos adicionales
    observaciones: Optional[str] = Field(None, title="Observaciones adicionales")
    
    # Metadatos
    fuente_datos: str = Field("MANUAL", title="Fuente de los datos")
    requiere_verificacion: bool = Field(True, title="Requiere verificación posterior")
    calidad_datos: str = Field("ACEPTABLE", title="Calidad de los datos")
    
    @validator('ruc')
    def validar_ruc_formato(cls, v):
        if not v.isdigit() or len(v) != 11:
            raise ValueError('RUC debe tener exactamente 11 dígitos')
        if not (v.startswith('10') or v.startswith('20')):
            raise ValueError('RUC debe comenzar con 10 o 20')
        return v
    
    @validator('razon_social')
    def validar_razon_social(cls, v):
        if len(v.strip()) < 3:
            raise ValueError('Razón social debe tener al menos 3 caracteres')
        # Limpiar espacios múltiples
        return ' '.join(v.strip().split())
    
    @validator('tipo_empresa')
    def validar_tipo_empresa(cls, v):
        tipos_validos = ['SAC', 'SA', 'SRL', 'EIRL', 'OTROS']
        if v.upper() not in tipos_validos:
            raise ValueError(f'Tipo de empresa debe ser uno de: {", ".join(tipos_validos)}')
        return v.upper()
    
    @validator('estado')
    def validar_estado(cls, v):
        estados_validos = ['ACTIVO', 'INACTIVO', 'SUSPENDIDO']
        if v.upper() not in estados_validos:
            raise ValueError(f'Estado debe ser uno de: {", ".join(estados_validos)}')
        return v.upper()
    
    @validator('categoria_contratista')
    def validar_categoria_contratista(cls, v):
        if v and v.strip():
            categorias_validas = ['EJECUTORA', 'SUPERVISORA']
            if v.upper() not in categorias_validas:
                raise ValueError(f'Categoría debe ser una de: {", ".join(categorias_validas)}')
            return v.upper()
        return v
    
    @validator('tamaño_empresa')
    def validar_tamano_empresa(cls, v):
        if v and v.strip():
            tamanos_validos = ['MICRO', 'PEQUEÑA', 'MEDIANA', 'GRANDE']
            if v.upper() not in tamanos_validos:
                raise ValueError(f'Tamaño debe ser uno de: {", ".join(tamanos_validos)}')
            return v.upper()
        return v
    
    @validator('representantes')
    def validar_representantes(cls, v):
        if not v:
            raise ValueError('Debe proporcionar al menos un representante legal')
        
        # Verificar que haya al menos un representante principal
        principales = [r for r in v if r.es_principal]
        if not principales:
            # Asignar el primer representante como principal automáticamente
            v[0].es_principal = True
            principales = [v[0]]
        
        if len(principales) > 1:
            raise ValueError('Solo puede haber un representante principal')
        
        # Verificar documentos únicos
        documentos = [r.numero_documento for r in v]
        if len(documentos) != len(set(documentos)):
            raise ValueError('No puede haber representantes con el mismo número de documento')
        
        return v
    
    @validator('fecha_constitucion')
    def validar_fecha_constitucion(cls, v):
        if v and v.strip():
            try:
                fecha = datetime.strptime(v, '%Y-%m-%d')
            except ValueError:
                try:
                    fecha = datetime.strptime(v, '%d/%m/%Y')
                    return fecha.strftime('%Y-%m-%d')
                except ValueError:
                    raise ValueError('Fecha debe estar en formato YYYY-MM-DD o DD/MM/YYYY')
            
            # Verificar que no sea una fecha futura
            if fecha > datetime.now():
                raise ValueError('Fecha de constitución no puede ser en el futuro')
            
            # Verificar que no sea muy antigua (ej: antes de 1900)
            if fecha.year < 1900:
                raise ValueError('Fecha de constitución no puede ser anterior a 1900')
        
        return v
    
    @validator('especialidades')
    def validar_especialidades(cls, v):
        if v:
            # Limpiar y normalizar especialidades
            especialidades_limpias = []
            for esp in v:
                if esp and esp.strip():
                    especialidades_limpias.append(esp.strip().upper())
            return list(set(especialidades_limpias))  # Eliminar duplicados
        return v
