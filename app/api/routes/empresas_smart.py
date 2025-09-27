"""
API endpoints inteligentes para empresas con fallback manual cuando falla el scraping
"""
from typing import List, Optional, Dict, Any, Union
from fastapi import APIRouter, HTTPException, Query, status, BackgroundTasks
from datetime import datetime
import re
import logging
from pydantic import BaseModel, Field, validator

logger = logging.getLogger(__name__)

# Modelos para entrada manual
class RepresentanteManual(BaseModel):
    """Modelo para representante ingresado manualmente"""
    nombre: str = Field(..., min_length=2, max_length=255, title="Nombre completo")
    cargo: str = Field(..., min_length=2, max_length=100, title="Cargo en la empresa")
    tipo_documento: str = Field("DNI", title="Tipo de documento")
    numero_documento: str = Field(..., min_length=8, max_length=20, title="Número de documento")
    es_principal: bool = Field(False, title="¿Es el representante principal?")
    participacion: Optional[str] = Field(None, title="Porcentaje de participación")
    fecha_desde: Optional[str] = Field(None, title="Fecha desde cuando ejerce el cargo")
    
    @validator('numero_documento')
    def validar_documento(cls, v, values):
        if values.get('tipo_documento') == 'DNI':
            if not v.isdigit() or len(v) != 8:
                raise ValueError('DNI debe tener exactamente 8 dígitos')
        elif values.get('tipo_documento') == 'CE':
            if len(v) < 9 or len(v) > 12:
                raise ValueError('CE debe tener entre 9 y 12 caracteres')
        return v

class ContactoManual(BaseModel):
    """Modelo para contacto ingresado manualmente"""
    email: Optional[str] = Field(None, title="Email corporativo")
    telefono: Optional[str] = Field(None, title="Teléfono")
    celular: Optional[str] = Field(None, title="Celular")
    direccion: Optional[str] = Field(None, title="Dirección completa")
    
    @validator('email')
    def validar_email(cls, v):
        if v and '@' not in v:
            raise ValueError('Email debe tener formato válido')
        return v

class EmpresaManualCompleta(BaseModel):
    """Modelo completo para empresa ingresada manualmente"""
    
    # Datos básicos (obligatorios)
    ruc: str = Field(..., pattern=r'^\d{11}$', title="RUC de 11 dígitos")
    razon_social: str = Field(..., min_length=2, max_length=255, title="Razón social")
    
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
    contacto: Optional[ContactoManual] = Field(None, title="Información de contacto")
    
    # Representantes
    representantes: List[RepresentanteManual] = Field([], title="Lista de representantes")
    
    # Clasificación
    categoria_contratista: Optional[str] = Field(None, title="EJECUTORA o SUPERVISORA")
    especialidades: List[str] = Field([], title="Especialidades de la empresa")
    
    # Datos adicionales opcionales
    capital_social: Optional[float] = Field(None, title="Capital social")
    fecha_constitucion: Optional[str] = Field(None, title="Fecha de constitución")
    numero_registro_nacional: Optional[str] = Field(None, title="Número de registro nacional")
    observaciones: Optional[str] = Field(None, title="Observaciones adicionales")
    
    # Metadatos
    fuente_datos: str = Field("MANUAL", title="Fuente de los datos")
    requiere_verificacion: bool = Field(True, title="Requiere verificación posterior")

class ValidacionRucResponse(BaseModel):
    """Respuesta de validación de RUC"""
    ruc: str
    valido: bool
    existe: bool = False
    datos_automaticos: Optional[Dict[str, Any]] = None
    errores_scraping: List[str] = []
    requiere_entrada_manual: bool = True
    mensaje: str
    timestamp: datetime

router = APIRouter(prefix="/empresas/smart", tags=["empresas-inteligentes"])

# Servicio Neon se importará bajo demanda (lazy loading)
def get_empresa_service():
    """Obtener instancia del servicio de Neon de forma lazy"""
    from app.services.empresa_service_neon import empresa_service_neon
    return empresa_service_neon

def validar_ruc_formato(ruc: str) -> bool:
    """Validar formato de RUC"""
    if not ruc or len(ruc) != 11:
        return False
    if not ruc.isdigit():
        return False
    if not (ruc.startswith('10') or ruc.startswith('20')):
        return False
    return True

async def intentar_scraping_automatico(ruc: str) -> Dict[str, Any]:
    """Intentar obtener datos automáticamente via scraping"""
    datos_scraped = {"sunat": None, "osce": None, "errores": []}
    
    try:
        # Intentar SUNAT primero
        logger.info(f"🔍 Intentando scraping SUNAT para RUC: {ruc}")
        from app.services.sunat_service import sunat_service
        
        try:
            datos_sunat = await sunat_service.consultar_empresa_completa(ruc)
            if datos_sunat and datos_sunat.razon_social:
                datos_scraped["sunat"] = {
                    "razon_social": datos_sunat.razon_social,
                    "direccion": datos_sunat.domicilio_fiscal,
                    "estado": datos_sunat.estado,
                    "representantes": [
                        {
                            "nombre": rep.nombre,
                            "cargo": rep.cargo,
                            "tipo_documento": rep.tipo_doc,
                            "numero_documento": rep.numero_doc,
                            "fecha_desde": rep.fecha_desde
                        }
                        for rep in datos_sunat.representantes
                    ] if datos_sunat.representantes else []
                }
                logger.info(f"✅ SUNAT exitoso: {datos_sunat.razon_social}")
        except Exception as e:
            error_msg = f"Error SUNAT: {str(e)}"
            datos_scraped["errores"].append(error_msg)
            logger.warning(error_msg)
        
        # Intentar OSCE
        logger.info(f"🔍 Intentando scraping OSCE para RUC: {ruc}")
        from app.services.osce_service import OSCEService
        
        try:
            osce_service = OSCEService()
            datos_osce = await osce_service.consultar_empresa(ruc)
            if datos_osce and datos_osce.razon_social:
                datos_scraped["osce"] = {
                    "razon_social": datos_osce.razon_social,
                    "estado_registro": datos_osce.estado_registro,
                    "telefono": datos_osce.telefono,
                    "email": datos_osce.email,
                    "especialidades": datos_osce.especialidades,
                    "representantes": [
                        {
                            "nombre": rep.nombre,
                            "cargo": rep.cargo,
                            "tipo_documento": rep.tipo_documento,
                            "numero_documento": rep.numero_documento
                        }
                        for rep in datos_osce.integrantes
                    ] if datos_osce.integrantes else []
                }
                logger.info(f"✅ OSCE exitoso: {datos_osce.razon_social}")
        except Exception as e:
            error_msg = f"Error OSCE: {str(e)}"
            datos_scraped["errores"].append(error_msg)
            logger.warning(error_msg)
        
    except Exception as e:
        error_msg = f"Error general scraping: {str(e)}"
        datos_scraped["errores"].append(error_msg)
        logger.error(error_msg)
    
    return datos_scraped

def consolidar_datos_scraping(datos_scraped: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Consolidar datos obtenidos de múltiples fuentes"""
    if not datos_scraped.get("sunat") and not datos_scraped.get("osce"):
        return None
    
    datos_consolidados = {
        "ruc": "",
        "razon_social": "",
        "direccion": "",
        "telefono": "",
        "email": "",
        "estado": "ACTIVO",
        "representantes": [],
        "especialidades": [],
        "fuente_datos": [],
        "calidad_datos": "PARCIAL"
    }
    
    # Priorizar SUNAT para datos básicos
    if datos_scraped.get("sunat"):
        sunat_data = datos_scraped["sunat"]
        datos_consolidados["razon_social"] = sunat_data.get("razon_social", "")
        datos_consolidados["direccion"] = sunat_data.get("direccion", "")
        datos_consolidados["estado"] = sunat_data.get("estado", "ACTIVO")
        datos_consolidados["representantes"].extend(sunat_data.get("representantes", []))
        datos_consolidados["fuente_datos"].append("SUNAT")
    
    # Complementar con OSCE
    if datos_scraped.get("osce"):
        osce_data = datos_scraped["osce"]
        
        # Si no tenemos razón social de SUNAT, usar OSCE
        if not datos_consolidados["razon_social"]:
            datos_consolidados["razon_social"] = osce_data.get("razon_social", "")
        
        datos_consolidados["telefono"] = osce_data.get("telefono", "")
        datos_consolidados["email"] = osce_data.get("email", "")
        datos_consolidados["especialidades"] = osce_data.get("especialidades", [])
        
        # Agregar representantes de OSCE (evitar duplicados)
        representantes_existentes = {r.get("numero_documento") for r in datos_consolidados["representantes"]}
        for rep_osce in osce_data.get("representantes", []):
            if rep_osce.get("numero_documento") not in representantes_existentes:
                datos_consolidados["representantes"].append(rep_osce)
        
        datos_consolidados["fuente_datos"].append("OSCE")
    
    # Determinar calidad de datos
    if len(datos_consolidados["fuente_datos"]) >= 2 and datos_consolidados["razon_social"]:
        datos_consolidados["calidad_datos"] = "BUENA"
    elif datos_consolidados["razon_social"]:
        datos_consolidados["calidad_datos"] = "ACEPTABLE"
    
    return datos_consolidados

@router.post("/validar-ruc", response_model=ValidacionRucResponse)
async def validar_ruc_inteligente(
    ruc_data: Dict[str, str],
    background_tasks: BackgroundTasks
):
    """
    Validar RUC e intentar obtener datos automáticamente
    
    Este endpoint:
    1. Valida el formato del RUC
    2. Verifica si ya existe en la base de datos
    3. Intenta scraping automático (SUNAT + OSCE)
    4. Devuelve datos encontrados o indica que se requiere entrada manual
    """
    try:
        ruc = ruc_data.get("ruc", "").strip()
        
        # Validar formato
        if not validar_ruc_formato(ruc):
            return ValidacionRucResponse(
                ruc=ruc,
                valido=False,
                requiere_entrada_manual=True,
                mensaje="RUC inválido. Debe tener 11 dígitos y comenzar con 10 o 20",
                timestamp=datetime.now()
            )
        
        # Verificar si ya existe
        empresa_service = get_empresa_service()
        empresa_existente = empresa_service.obtener_empresa_por_ruc(ruc)
        
        if empresa_existente:
            return ValidacionRucResponse(
                ruc=ruc,
                valido=True,
                existe=True,
                requiere_entrada_manual=False,
                mensaje=f"Empresa ya existe: {empresa_existente.get('razon_social', 'Sin nombre')}",
                timestamp=datetime.now()
            )
        
        # Intentar scraping automático
        logger.info(f"🤖 Iniciando scraping automático para RUC: {ruc}")
        datos_scraped = await intentar_scraping_automatico(ruc)
        
        # Consolidar datos
        datos_consolidados = consolidar_datos_scraping(datos_scraped)
        
        if datos_consolidados and datos_consolidados.get("razon_social"):
            return ValidacionRucResponse(
                ruc=ruc,
                valido=True,
                existe=False,
                datos_automaticos=datos_consolidados,
                errores_scraping=datos_scraped.get("errores", []),
                requiere_entrada_manual=False,
                mensaje=f"Datos encontrados automáticamente: {datos_consolidados['razon_social']}",
                timestamp=datetime.now()
            )
        else:
            return ValidacionRucResponse(
                ruc=ruc,
                valido=True,
                existe=False,
                datos_automaticos=None,
                errores_scraping=datos_scraped.get("errores", []),
                requiere_entrada_manual=True,
                mensaje="No se pudieron obtener datos automáticamente. Por favor, complete los datos manualmente.",
                timestamp=datetime.now()
            )
    
    except Exception as e:
        logger.error(f"❌ Error validando RUC {ruc}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )

@router.post("/crear-automatica", status_code=status.HTTP_201_CREATED)
async def crear_empresa_automatica(
    empresa_automatica: Dict[str, Any]
):
    """
    Crear empresa usando datos obtenidos automáticamente
    
    Este endpoint recibe datos que ya fueron obtenidos via scraping
    y los guarda en la base de datos con validaciones adicionales.
    """
    try:
        ruc = empresa_automatica.get("ruc")
        if not ruc or not validar_ruc_formato(ruc):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="RUC inválido"
            )
        
        # Verificar que no exista
        empresa_service = get_empresa_service()
        if empresa_service.obtener_empresa_por_ruc(ruc):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La empresa ya existe"
            )
        
        # Preparar datos para guardar
        datos_guardar = {
            "ruc": ruc,
            "razon_social": empresa_automatica.get("razon_social", ""),
            "direccion": empresa_automatica.get("direccion", ""),
            "telefono": empresa_automatica.get("telefono", ""),
            "email": empresa_automatica.get("email", ""),
            "estado": empresa_automatica.get("estado", "ACTIVO"),
            "tipo_empresa": "SAC",
            "fuentes_consultadas": empresa_automatica.get("fuente_datos", []),
            "representantes": empresa_automatica.get("representantes", [])
        }
        
        # Asignar especialidades si existen
        if empresa_automatica.get("especialidades"):
            datos_guardar["categoria_contratista"] = "EJECUTORA"
        
        # Guardar empresa
        empresa_id = empresa_service.guardar_empresa(datos_guardar)
        
        if not empresa_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error creando empresa"
            )
        
        # Obtener empresa creada
        empresa_creada = empresa_service.obtener_empresa_por_ruc(ruc)
        
        return {
            "success": True,
            "message": f"Empresa creada automáticamente: {empresa_automatica.get('razon_social', '')}",
            "data": empresa_creada,
            "modo": "AUTOMATICO",
            "fuentes": empresa_automatica.get("fuente_datos", []),
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error creando empresa automática: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )

@router.post("/crear-manual", status_code=status.HTTP_201_CREATED)
async def crear_empresa_manual(
    empresa_manual: EmpresaManualCompleta
):
    """
    Crear empresa con datos ingresados completamente a mano
    
    Este endpoint permite la creación completa manual cuando:
    1. El scraping automático falló
    2. El usuario prefiere ingresar todos los datos manualmente
    3. Se requiere información adicional no disponible en fuentes públicas
    """
    try:
        # Validaciones adicionales para entrada manual
        if len(empresa_manual.razon_social.strip()) < 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La razón social debe tener al menos 5 caracteres"
            )
        
        # Verificar que no exista
        empresa_service = get_empresa_service()
        if empresa_service.obtener_empresa_por_ruc(empresa_manual.ruc):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La empresa ya existe"
            )
        
        # Validar que tenga al menos un representante
        if not empresa_manual.representantes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Debe proporcionar al menos un representante legal"
            )
        
        # Validar que tenga un representante principal
        principales = [r for r in empresa_manual.representantes if r.es_principal]
        if not principales:
            # Asignar el primer representante como principal
            empresa_manual.representantes[0].es_principal = True
            principales = [empresa_manual.representantes[0]]
        
        if len(principales) > 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Solo puede haber un representante principal"
            )
        
        # Preparar datos para guardar
        representante_principal = principales[0]
        
        datos_guardar = {
            "ruc": empresa_manual.ruc,
            "razon_social": empresa_manual.razon_social.strip(),
            "nombre_comercial": empresa_manual.nombre_comercial or empresa_manual.razon_social.strip(),
            "tipo_empresa": empresa_manual.tipo_empresa,
            "estado": empresa_manual.estado,
            "departamento": empresa_manual.departamento or "",
            "provincia": empresa_manual.provincia or "",
            "distrito": empresa_manual.distrito or "",
            "ubigeo": empresa_manual.ubigeo or "",
            "categoria_contratista": empresa_manual.categoria_contratista,
            "representante_legal": representante_principal.nombre,
            "dni_representante": representante_principal.numero_documento,
            "fuentes_consultadas": ["MANUAL"],
            "representantes": [
                {
                    "nombre": rep.nombre,
                    "cargo": rep.cargo,
                    "tipo_documento": rep.tipo_documento,
                    "numero_documento": rep.numero_documento,
                    "es_principal": rep.es_principal,
                    "participacion": rep.participacion,
                    "fecha_desde": rep.fecha_desde,
                    "fuente": "MANUAL"
                }
                for rep in empresa_manual.representantes
            ]
        }
        
        # Agregar datos de contacto si existen
        if empresa_manual.contacto:
            datos_guardar.update({
                "email": empresa_manual.contacto.email or "",
                "telefono": empresa_manual.contacto.celular or empresa_manual.contacto.telefono or "",
                "direccion": empresa_manual.contacto.direccion or ""
            })
        
        # Agregar datos adicionales opcionales
        if empresa_manual.observaciones:
            datos_guardar["observaciones"] = empresa_manual.observaciones
        
        # Guardar empresa
        empresa_id = empresa_service.guardar_empresa(datos_guardar)
        
        if not empresa_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error creando empresa"
            )
        
        # Obtener empresa creada
        empresa_creada = empresa_service.obtener_empresa_por_ruc(empresa_manual.ruc)
        
        return {
            "success": True,
            "message": f"Empresa creada manualmente: {empresa_manual.razon_social}",
            "data": empresa_creada,
            "modo": "MANUAL",
            "representantes_registrados": len(empresa_manual.representantes),
            "requiere_verificacion": empresa_manual.requiere_verificacion,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error creando empresa manual: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )

@router.get("/plantilla-manual/{ruc}")
async def obtener_plantilla_manual(ruc: str):
    """
    Obtener plantilla de empresa para entrada manual
    
    Genera una plantilla con campos pre-llenados si hay datos parciales
    disponibles, o una plantilla completamente vacía para entrada manual.
    """
    try:
        if not validar_ruc_formato(ruc):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="RUC inválido"
            )
        
        # Intentar obtener datos parciales
        logger.info(f"🔍 Generando plantilla manual para RUC: {ruc}")
        datos_scraped = await intentar_scraping_automatico(ruc)
        datos_consolidados = consolidar_datos_scraping(datos_scraped)
        
        # Generar plantilla base
        plantilla = {
            "ruc": ruc,
            "razon_social": "",
            "nombre_comercial": "",
            "tipo_empresa": "SAC",
            "estado": "ACTIVO",
            "departamento": "",
            "provincia": "",
            "distrito": "",
            "contacto": {
                "email": "",
                "telefono": "",
                "celular": "",
                "direccion": ""
            },
            "representantes": [
                {
                    "nombre": "",
                    "cargo": "GERENTE GENERAL",
                    "tipo_documento": "DNI",
                    "numero_documento": "",
                    "es_principal": True,
                    "participacion": "",
                    "fecha_desde": ""
                }
            ],
            "categoria_contratista": None,
            "especialidades": [],
            "observaciones": "",
            "fuente_datos": "MANUAL",
            "requiere_verificacion": True
        }
        
        # Rellenar con datos obtenidos automáticamente si están disponibles
        if datos_consolidados:
            plantilla.update({
                "razon_social": datos_consolidados.get("razon_social", ""),
                "contacto": {
                    "email": datos_consolidados.get("email", ""),
                    "telefono": datos_consolidados.get("telefono", ""),
                    "celular": datos_consolidados.get("telefono", ""),
                    "direccion": datos_consolidados.get("direccion", "")
                },
                "especialidades": datos_consolidados.get("especialidades", [])
            })
            
            # Actualizar representantes si hay datos
            if datos_consolidados.get("representantes"):
                rep_automatico = datos_consolidados["representantes"][0]
                plantilla["representantes"][0].update({
                    "nombre": rep_automatico.get("nombre", ""),
                    "cargo": rep_automatico.get("cargo", "GERENTE GENERAL"),
                    "numero_documento": rep_automatico.get("numero_documento", "")
                })
        
        return {
            "success": True,
            "plantilla": plantilla,
            "datos_parciales_encontrados": datos_consolidados is not None,
            "errores_scraping": datos_scraped.get("errores", []),
            "mensaje": (
                "Plantilla generada con datos parciales encontrados" 
                if datos_consolidados 
                else "Plantilla vacía para entrada completamente manual"
            ),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error generando plantilla manual: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )

@router.get("/validadores/referencia")
async def obtener_validadores_referencia():
    """
    Obtener información de referencia para validadores
    
    Devuelve listas de valores válidos para ayudar en la entrada manual:
    - Tipos de empresa
    - Estados válidos
    - Tipos de documento
    - Cargos comunes
    - Especialidades comunes
    """
    return {
        "success": True,
        "referencia": {
            "tipos_empresa": [
                {"value": "SAC", "label": "Sociedad Anónima Cerrada"},
                {"value": "SA", "label": "Sociedad Anónima"},
                {"value": "SRL", "label": "Sociedad de Responsabilidad Limitada"},
                {"value": "EIRL", "label": "Empresa Individual de Responsabilidad Limitada"},
                {"value": "OTROS", "label": "Otros"}
            ],
            "estados_empresa": [
                {"value": "ACTIVO", "label": "Activa"},
                {"value": "INACTIVO", "label": "Inactiva"},
                {"value": "SUSPENDIDO", "label": "Suspendida"}
            ],
            "tipos_documento": [
                {"value": "DNI", "label": "Documento Nacional de Identidad"},
                {"value": "CE", "label": "Carné de Extranjería"},
                {"value": "PASAPORTE", "label": "Pasaporte"}
            ],
            "cargos_comunes": [
                "GERENTE GENERAL",
                "GERENTE",
                "ADMINISTRADOR",
                "PRESIDENTE",
                "DIRECTOR GENERAL",
                "APODERADO",
                "REPRESENTANTE LEGAL",
                "SOCIO GERENTE"
            ],
            "categorias_contratista": [
                {"value": "EJECUTORA", "label": "Empresa Ejecutora"},
                {"value": "SUPERVISORA", "label": "Empresa Supervisora"},
                {"value": null, "label": "No definida"}
            ],
            "especialidades_comunes": [
                "EDIFICACIONES",
                "CARRETERAS",
                "PUENTES",
                "AGUA Y SANEAMIENTO",
                "ELECTRIFICACION",
                "TELECOMUNICACIONES",
                "INFRAESTRUCTURA PORTUARIA",
                "SUPERVISION DE OBRAS"
            ]
        }
    }

@router.get("/estadisticas/entrada-manual")
async def obtener_estadisticas_entrada_manual():
    """
    Obtener estadísticas sobre empresas creadas manualmente vs automáticamente
    """
    try:
        empresa_service = get_empresa_service()
        empresas = empresa_service.listar_empresas(limit=1000)
        
        estadisticas = {
            "total_empresas": len(empresas),
            "entrada_manual": 0,
            "entrada_automatica": 0,
            "entrada_mixta": 0,
            "fuentes": {
                "MANUAL": 0,
                "SUNAT": 0,
                "OSCE": 0,
                "MIXTA": 0
            }
        }
        
        for empresa in empresas:
            fuentes = empresa.get("fuentes_consultadas", [])
            
            if "MANUAL" in fuentes and len(fuentes) == 1:
                estadisticas["entrada_manual"] += 1
                estadisticas["fuentes"]["MANUAL"] += 1
            elif len(fuentes) > 1:
                estadisticas["entrada_mixta"] += 1
                estadisticas["fuentes"]["MIXTA"] += 1
            else:
                estadisticas["entrada_automatica"] += 1
                if "SUNAT" in fuentes:
                    estadisticas["fuentes"]["SUNAT"] += 1
                if "OSCE" in fuentes:
                    estadisticas["fuentes"]["OSCE"] += 1
        
        return {
            "success": True,
            "estadisticas": estadisticas,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo estadísticas: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )

# =================================================================
# ENDPOINT DE CREACIÓN DUAL (AUTOMÁTICO/MANUAL) CON IA
# =================================================================

class EmpresaDualCreate(BaseModel):
    """Modelo para creación dual inteligente de empresas"""
    
    # Datos básicos (siempre requeridos)
    ruc: str = Field(..., pattern=r'^\d{11}$', title="RUC de 11 dígitos")
    
    # Configuración del comportamiento
    intentar_scraping: bool = Field(True, title="¿Intentar scraping automático primero?")
    forzar_manual: bool = Field(False, title="¿Forzar entrada manual sin scraping?")
    combinar_fuentes: bool = Field(True, title="¿Combinar datos de múltiples fuentes?")
    
    # Datos manuales (opcionales, usados si scraping falla o se combinan)
    datos_manuales: Optional[EmpresaManualCompleta] = Field(None, title="Datos ingresados manualmente")
    
    # Configuraciones avanzadas
    priorizar_fuente: Optional[str] = Field(None, title="SUNAT, OSCE o MANUAL para priorizar")
    validacion_estricta: bool = Field(False, title="¿Activar validación estricta?")
    permitir_datos_parciales: bool = Field(True, title="¿Permitir crear con datos parciales?")
    
    # Metadata
    creado_por: Optional[str] = Field(None, title="Usuario que crea la empresa")
    motivo_creacion: Optional[str] = Field(None, title="Motivo de la creación")
    notas_adicionales: Optional[str] = Field(None, title="Notas adicionales")

class CreacionDualResponse(BaseModel):
    """Respuesta detallada de creación dual"""
    success: bool
    empresa_id: Optional[str] = None
    empresa_data: Optional[Dict[str, Any]] = None
    modo_creacion: str  # AUTOMATICO, MANUAL, MIXTO, FALLBACK
    fuentes_utilizadas: List[str]
    calidad_datos: str  # EXCELENTE, BUENA, ACEPTABLE, PARCIAL
    
    # Detalle del proceso
    scraping_intentado: bool
    scraping_exitoso: bool
    datos_sunat_encontrados: bool = False
    datos_osce_encontrados: bool = False
    datos_manuales_utilizados: bool = False
    
    # Validaciones
    validaciones_pasadas: List[str]
    validaciones_fallidas: List[str]
    advertencias: List[str]
    
    # Metadata
    timestamp: datetime
    tiempo_procesamiento_ms: Optional[float] = None
    requiere_verificacion_posterior: bool = False

def evaluar_calidad_datos_ia(fuentes: List[str], datos: Dict[str, Any]) -> str:
    """IA simple para evaluar calidad de datos basada en completitud y fuentes"""
    
    puntuacion = 0
    campos_criticos = ['razon_social', 'ruc', 'estado']
    campos_importantes = ['direccion', 'telefono', 'email', 'representantes']
    campos_adicionales = ['especialidades', 'categoria_contratista', 'tipo_empresa']
    
    # Puntos por fuentes
    if 'SUNAT' in fuentes:
        puntuacion += 40  # SUNAT es muy confiable
    if 'OSCE' in fuentes:
        puntuacion += 30  # OSCE es confiable para contratistas
    if 'MANUAL' in fuentes:
        puntuacion += 10  # Manual depende de la calidad del input
    
    # Puntos por completitud de campos críticos
    for campo in campos_criticos:
        if datos.get(campo):
            puntuacion += 10
    
    # Puntos por campos importantes
    for campo in campos_importantes:
        if datos.get(campo):
            if campo == 'representantes' and isinstance(datos[campo], list) and len(datos[campo]) > 0:
                puntuacion += 5
            elif campo != 'representantes' and datos.get(campo):
                puntuacion += 5
    
    # Puntos por campos adicionales
    for campo in campos_adicionales:
        if datos.get(campo):
            puntuacion += 2
    
    # Clasificar según puntuación
    if puntuacion >= 85:
        return "EXCELENTE"
    elif puntuacion >= 70:
        return "BUENA"
    elif puntuacion >= 50:
        return "ACEPTABLE"
    else:
        return "PARCIAL"

def detectar_modo_creacion_optimo(datos_scraped: Dict[str, Any], datos_manuales: Optional[EmpresaManualCompleta]) -> str:
    """IA para detectar el modo de creación óptimo"""
    
    tiene_sunat = bool(datos_scraped.get("sunat"))
    tiene_osce = bool(datos_scraped.get("osce"))
    tiene_manuales = bool(datos_manuales)
    
    if tiene_sunat and tiene_osce and tiene_manuales:
        return "MIXTO_COMPLETO"
    elif tiene_sunat and tiene_osce:
        return "AUTOMATICO_DUAL"
    elif (tiene_sunat or tiene_osce) and tiene_manuales:
        return "MIXTO_PARCIAL"
    elif tiene_sunat or tiene_osce:
        return "AUTOMATICO_SIMPLE"
    elif tiene_manuales:
        return "MANUAL_PURO"
    else:
        return "FALLBACK_ERROR"

@router.post("/crear-dual", status_code=status.HTTP_201_CREATED, response_model=CreacionDualResponse)
async def crear_empresa_dual(
    empresa_dual: EmpresaDualCreate,
    background_tasks: BackgroundTasks
):
    """
    🤖 Endpoint de creación dual inteligente que combina lo mejor de ambos mundos
    
    Este endpoint avanzado:
    1. Intenta scraping automático si se solicita
    2. Usa datos manuales como fallback o complemento
    3. Combina fuentes inteligentemente
    4. Evalúa calidad de datos con IA simple
    5. Aplica validaciones contextuales
    6. Proporciona feedback detallado
    """
    inicio_proceso = datetime.now()
    
    try:
        ruc = empresa_dual.ruc
        logger.info(f"🤖 Iniciando creación dual inteligente para RUC: {ruc}")
        
        # Validaciones iniciales
        if not validar_ruc_formato(ruc):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="RUC inválido. Debe tener 11 dígitos y comenzar con 10 o 20"
            )
        
        # Verificar si ya existe
        empresa_service = get_empresa_service()
        if empresa_service.obtener_empresa_por_ruc(ruc):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La empresa ya existe en el sistema"
            )
        
        # Variables de control
        datos_scraped = {"sunat": None, "osce": None, "errores": []}
        scraping_intentado = False
        scraping_exitoso = False
        validaciones_pasadas = []
        validaciones_fallidas = []
        advertencias = []
        
        # FASE 1: Scraping automático (si se solicita)
        if empresa_dual.intentar_scraping and not empresa_dual.forzar_manual:
            logger.info(f"🔍 Fase 1: Intentando scraping automático para RUC: {ruc}")
            scraping_intentado = True
            
            try:
                datos_scraped = await intentar_scraping_automatico(ruc)
                
                tiene_sunat = bool(datos_scraped.get("sunat"))
                tiene_osce = bool(datos_scraped.get("osce"))
                
                if tiene_sunat or tiene_osce:
                    scraping_exitoso = True
                    logger.info(f"✅ Scraping exitoso - SUNAT: {tiene_sunat}, OSCE: {tiene_osce}")
                    validaciones_pasadas.append("Scraping automático exitoso")
                else:
                    logger.warning(f"⚠️ Scraping sin resultados para RUC: {ruc}")
                    validaciones_fallidas.append("Scraping no encontró datos")
                    advertencias.append("Se procederá con datos manuales")
                    
            except Exception as e:
                logger.error(f"❌ Error en scraping: {e}")
                datos_scraped["errores"].append(f"Error scraping: {str(e)}")
                validaciones_fallidas.append(f"Error en scraping: {str(e)}")
        else:
            logger.info(f"⏭️ Scraping omitido para RUC: {ruc} (configuración del usuario)")
            validaciones_pasadas.append("Scraping omitido por configuración")
        
        # FASE 2: Determinar modo de creación óptimo
        modo_creacion = detectar_modo_creacion_optimo(datos_scraped, empresa_dual.datos_manuales)
        logger.info(f"🧠 Modo de creación detectado: {modo_creacion}")
        
        # FASE 3: Consolidación inteligente de datos
        if modo_creacion == "FALLBACK_ERROR":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se encontraron datos automáticos ni se proporcionaron datos manuales"
            )
        
        # Consolidar datos según el modo detectado
        datos_finales = {}
        fuentes_utilizadas = []
        
        if "AUTOMATICO" in modo_creacion or "MIXTO" in modo_creacion:
            # Usar datos consolidados del scraping
            datos_automaticos = consolidar_datos_scraping(datos_scraped)
            if datos_automaticos:
                datos_finales.update(datos_automaticos)
                fuentes_utilizadas.extend(datos_automaticos.get("fuente_datos", []))
                validaciones_pasadas.append("Datos automáticos consolidados")
        
        if "MANUAL" in modo_creacion or "MIXTO" in modo_creacion:
            # Incorporar datos manuales
            if empresa_dual.datos_manuales:
                datos_manuales = empresa_dual.datos_manuales.dict(exclude_unset=True)
                
                # Si es modo mixto, combinar inteligentemente
                if "MIXTO" in modo_creacion:
                    # Priorizar según configuración
                    if empresa_dual.priorizar_fuente == "MANUAL":
                        # Datos manuales sobrescriben automáticos
                        datos_finales.update(datos_manuales)
                    else:
                        # Datos automáticos tienen prioridad, manuales rellenan vacíos
                        for key, value in datos_manuales.items():
                            if key not in datos_finales or not datos_finales.get(key):
                                datos_finales[key] = value
                else:
                    # Modo manual puro
                    datos_finales = datos_manuales
                
                fuentes_utilizadas.append("MANUAL")
                validaciones_pasadas.append("Datos manuales incorporados")
        
        # FASE 4: Validaciones contextuales avanzadas
        if empresa_dual.validacion_estricta:
            # Validaciones estrictas adicionales
            campos_requeridos_estrictos = ['razon_social', 'ruc', 'estado', 'tipo_empresa']
            for campo in campos_requeridos_estrictos:
                if not datos_finales.get(campo):
                    validaciones_fallidas.append(f"Campo requerido faltante en modo estricto: {campo}")
            
            # Validar representantes en modo estricto
            representantes = datos_finales.get('representantes', [])
            if not representantes or len(representantes) == 0:
                validaciones_fallidas.append("Al menos un representante es requerido en modo estricto")
            
            if validaciones_fallidas:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Validación estricta falló: {'; '.join(validaciones_fallidas)}"
                )
        
        # FASE 5: Verificar si se permiten datos parciales
        if not empresa_dual.permitir_datos_parciales:
            campos_importantes = ['razon_social', 'direccion', 'representantes']
            campos_faltantes = []
            for campo in campos_importantes:
                if not datos_finales.get(campo):
                    campos_faltantes.append(campo)
            
            if campos_faltantes:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Datos parciales no permitidos. Faltan: {', '.join(campos_faltantes)}"
                )
        
        # FASE 6: Enriquecer datos finales con metadata
        datos_finales.update({
            "ruc": ruc,
            "fuente_datos": "MIXTO" if len(set(fuentes_utilizadas)) > 1 else fuentes_utilizadas[0] if fuentes_utilizadas else "MANUAL",
            "fuentes_consultadas": list(set(fuentes_utilizadas)),
            "modo_creacion": modo_creacion,
            "requiere_verificacion": not scraping_exitoso or "MANUAL" in fuentes_utilizadas,
            "creado_por": empresa_dual.creado_por,
            "motivo_creacion": empresa_dual.motivo_creacion,
            "notas_adicionales": empresa_dual.notas_adicionales,
            "timestamp_creacion": datetime.now().isoformat()
        })
        
        # FASE 7: Evaluar calidad de datos con IA
        calidad_datos = evaluar_calidad_datos_ia(fuentes_utilizadas, datos_finales)
        datos_finales["calidad_datos"] = calidad_datos
        
        logger.info(f"📊 Calidad de datos evaluada: {calidad_datos}")
        validaciones_pasadas.append(f"Calidad de datos: {calidad_datos}")
        
        # FASE 8: Guardar empresa
        empresa_id = empresa_service.guardar_empresa(datos_finales)
        
        if not empresa_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error guardando empresa en la base de datos"
            )
        
        # FASE 9: Obtener empresa creada para respuesta
        empresa_creada = empresa_service.obtener_empresa_por_ruc(ruc)
        
        # Calcular tiempo de procesamiento
        fin_proceso = datetime.now()
        tiempo_procesamiento_ms = (fin_proceso - inicio_proceso).total_seconds() * 1000
        
        # FASE 10: Preparar respuesta detallada
        respuesta = CreacionDualResponse(
            success=True,
            empresa_id=str(empresa_id),
            empresa_data=empresa_creada,
            modo_creacion=modo_creacion,
            fuentes_utilizadas=list(set(fuentes_utilizadas)),
            calidad_datos=calidad_datos,
            
            # Detalle del proceso
            scraping_intentado=scraping_intentado,
            scraping_exitoso=scraping_exitoso,
            datos_sunat_encontrados=bool(datos_scraped.get("sunat")),
            datos_osce_encontrados=bool(datos_scraped.get("osce")),
            datos_manuales_utilizados="MANUAL" in fuentes_utilizadas,
            
            # Validaciones
            validaciones_pasadas=validaciones_pasadas,
            validaciones_fallidas=validaciones_fallidas,
            advertencias=advertencias,
            
            # Metadata
            timestamp=fin_proceso,
            tiempo_procesamiento_ms=tiempo_procesamiento_ms,
            requiere_verificacion_posterior=datos_finales.get("requiere_verificacion", False)
        )
        
        logger.info(f"🎉 Empresa creada exitosamente - ID: {empresa_id}, Modo: {modo_creacion}, Calidad: {calidad_datos}")
        
        return respuesta
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error crítico en creación dual: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )

# =================================================================
# SISTEMA DE FALLBACK INTELIGENTE AUTOMÁTICO
# =================================================================

class FallbackConfig(BaseModel):
    """Configuración del sistema de fallback inteligente"""
    activar_fallback: bool = Field(True, title="¿Activar fallback automático?")
    timeout_scraping_segundos: int = Field(30, title="Timeout para scraping en segundos")
    reintentos_scraping: int = Field(2, title="Número de reintentos para scraping")
    modo_fallback: str = Field("AUTOMATICO", title="AUTOMATICO, PLANTILLA o MANUAL_COMPLETO")
    notificar_fallbacks: bool = Field(True, title="¿Notificar cuando ocurra fallback?")
    guardar_intentos_fallidos: bool = Field(True, title="¿Guardar log de intentos fallidos?")

class FallbackResponse(BaseModel):
    """Respuesta del sistema de fallback"""
    fallback_activado: bool
    motivo_fallback: str
    accion_tomada: str
    datos_parciales_encontrados: bool = False
    plantilla_generada: Optional[Dict[str, Any]] = None
    recomendacion: str
    tiempo_total_intento_ms: float
    timestamp: datetime

class ScrapingAttempt:
    """Clase para manejar intentos de scraping con reintentos y timeouts"""
    
    def __init__(self, config: FallbackConfig):
        self.config = config
        self.intentos = []
        self.inicio = datetime.now()
    
    async def intentar_con_timeout_y_reintentos(self, ruc: str) -> Dict[str, Any]:
        """Intentar scraping con timeout y reintentos configurables"""
        import asyncio
        
        for intento in range(1, self.config.reintentos_scraping + 1):
            logger.info(f"🔄 Intento {intento}/{self.config.reintentos_scraping} de scraping para RUC: {ruc}")
            inicio_intento = datetime.now()
            
            try:
                # Aplicar timeout al scraping
                datos_scraped = await asyncio.wait_for(
                    intentar_scraping_automatico(ruc),
                    timeout=self.config.timeout_scraping_segundos
                )
                
                fin_intento = datetime.now()
                tiempo_intento = (fin_intento - inicio_intento).total_seconds() * 1000
                
                # Registrar intento exitoso
                self.intentos.append({
                    "numero_intento": intento,
                    "exitoso": True,
                    "tiempo_ms": tiempo_intento,
                    "datos_encontrados": bool(datos_scraped.get("sunat") or datos_scraped.get("osce")),
                    "errores": datos_scraped.get("errores", [])
                })
                
                # Si encontramos datos, devolver inmediatamente
                if datos_scraped.get("sunat") or datos_scraped.get("osce"):
                    logger.info(f"✅ Scraping exitoso en intento {intento}")
                    return datos_scraped
                
                # Si no hay datos pero no hubo errores, continuar con siguiente intento
                if not datos_scraped.get("errores"):
                    logger.warning(f"⚠️ Intento {intento}: Sin datos encontrados pero sin errores")
                    if intento < self.config.reintentos_scraping:
                        await asyncio.sleep(1)  # Espera breve antes del siguiente intento
                        continue
                
                # Si hay errores, registrar y continuar
                logger.warning(f"⚠️ Intento {intento} con errores: {datos_scraped.get('errores', [])}")
                
            except asyncio.TimeoutError:
                fin_intento = datetime.now()
                tiempo_intento = (fin_intento - inicio_intento).total_seconds() * 1000
                
                self.intentos.append({
                    "numero_intento": intento,
                    "exitoso": False,
                    "tiempo_ms": tiempo_intento,
                    "error": "Timeout",
                    "timeout_segundos": self.config.timeout_scraping_segundos
                })
                
                logger.warning(f"⏰ Timeout en intento {intento} después de {self.config.timeout_scraping_segundos}s")
                
                if intento < self.config.reintentos_scraping:
                    await asyncio.sleep(2)  # Espera más larga después de timeout
                    continue
            
            except Exception as e:
                fin_intento = datetime.now()
                tiempo_intento = (fin_intento - inicio_intento).total_seconds() * 1000
                
                self.intentos.append({
                    "numero_intento": intento,
                    "exitoso": False,
                    "tiempo_ms": tiempo_intento,
                    "error": str(e)
                })
                
                logger.error(f"❌ Error en intento {intento}: {e}")
                
                if intento < self.config.reintentos_scraping:
                    await asyncio.sleep(1)
                    continue
        
        # Todos los intentos fallaron
        logger.error(f"❌ Todos los intentos de scraping fallaron para RUC: {ruc}")
        return {
            "sunat": None,
            "osce": None,
            "errores": [f"Scraping falló después de {self.config.reintentos_scraping} intentos"],
            "intentos_detallados": self.intentos
        }

class FallbackIntelligentSystem:
    """Sistema inteligente de fallback que detecta y maneja fallos automáticamente"""
    
    def __init__(self, config: FallbackConfig = None):
        self.config = config or FallbackConfig()
        self.estadisticas_fallback = {
            "total_solicitudes": 0,
            "fallbacks_activados": 0,
            "fallbacks_exitosos": 0,
            "tipos_fallback": {}
        }
    
    def detectar_necesidad_fallback(self, datos_scraped: Dict[str, Any]) -> tuple[bool, str]:
        """Detectar si se necesita activar fallback y determinar el motivo"""
        
        # Caso 1: Sin datos encontrados
        if not datos_scraped.get("sunat") and not datos_scraped.get("osce"):
            if datos_scraped.get("errores"):
                return True, "ERRORES_SCRAPING"
            else:
                return True, "SIN_DATOS_ENCONTRADOS"
        
        # Caso 2: Datos muy parciales o de baja calidad
        datos_consolidados = consolidar_datos_scraping(datos_scraped)
        if datos_consolidados:
            campos_criticos = ['razon_social', 'ruc']
            campos_faltantes = [campo for campo in campos_criticos if not datos_consolidados.get(campo)]
            
            if campos_faltantes:
                return True, "DATOS_CRITICOS_FALTANTES"
            
            # Verificar calidad mínima
            campos_importantes = ['direccion', 'representantes', 'estado']
            campos_importantes_presentes = sum(1 for campo in campos_importantes if datos_consolidados.get(campo))
            
            if campos_importantes_presentes < 1:  # Menos del 33% de campos importantes
                return True, "CALIDAD_DATOS_INSUFICIENTE"
        
        # Caso 3: Errores críticos en scraping
        if datos_scraped.get("errores"):
            errores_criticos = ["timeout", "connection", "blocked", "captcha"]
            for error in datos_scraped.get("errores", []):
                for error_critico in errores_criticos:
                    if error_critico.lower() in error.lower():
                        return True, "ERROR_CRITICO_SCRAPING"
        
        return False, "NO_REQUERIDO"
    
    def determinar_accion_fallback(self, motivo: str, datos_parciales: bool = False) -> str:
        """Determinar la acción de fallback más apropiada según el motivo"""
        
        if self.config.modo_fallback == "MANUAL_COMPLETO":
            return "ENTRADA_MANUAL_COMPLETA"
        
        if motivo in ["SIN_DATOS_ENCONTRADOS", "ERROR_CRITICO_SCRAPING"]:
            if datos_parciales:
                return "PLANTILLA_PRELLENADA"
            else:
                return "PLANTILLA_VACIA"
        
        elif motivo in ["DATOS_CRITICOS_FALTANTES", "CALIDAD_DATOS_INSUFICIENTE"]:
            return "COMPLEMENTAR_DATOS_MANUALES"
        
        else:
            return "ENTRADA_MANUAL_COMPLETA"
    
    async def manejar_fallback(
        self, 
        ruc: str, 
        datos_scraped: Dict[str, Any], 
        motivo: str
    ) -> FallbackResponse:
        """Manejar el fallback inteligentemente según el caso"""
        inicio = datetime.now()
        
        self.estadisticas_fallback["total_solicitudes"] += 1
        self.estadisticas_fallback["fallbacks_activados"] += 1
        
        # Actualizar estadísticas por tipo
        if motivo not in self.estadisticas_fallback["tipos_fallback"]:
            self.estadisticas_fallback["tipos_fallback"][motivo] = 0
        self.estadisticas_fallback["tipos_fallback"][motivo] += 1
        
        logger.info(f"🔄 Activando fallback inteligente - RUC: {ruc}, Motivo: {motivo}")
        
        # Verificar si hay datos parciales utilizables
        datos_consolidados = consolidar_datos_scraping(datos_scraped)
        datos_parciales_encontrados = bool(datos_consolidados and datos_consolidados.get("razon_social"))
        
        # Determinar acción
        accion = self.determinar_accion_fallback(motivo, datos_parciales_encontrados)
        
        plantilla_generada = None
        recomendacion = ""
        
        # Ejecutar acción de fallback
        if accion == "PLANTILLA_PRELLENADA":
            plantilla_generada = await self._generar_plantilla_prellenada(ruc, datos_consolidados)
            recomendacion = "Se generó una plantilla con los datos encontrados. Complete los campos faltantes."
        
        elif accion == "PLANTILLA_VACIA":
            plantilla_generada = await self._generar_plantilla_vacia(ruc)
            recomendacion = "No se encontraron datos. Complete todos los campos manualmente."
        
        elif accion == "COMPLEMENTAR_DATOS_MANUALES":
            plantilla_generada = await self._generar_plantilla_complementaria(ruc, datos_consolidados)
            recomendacion = "Se encontraron datos parciales. Complete los campos críticos faltantes."
        
        else:  # ENTRADA_MANUAL_COMPLETA
            plantilla_generada = await self._generar_plantilla_vacia(ruc)
            recomendacion = "Se requiere entrada manual completa debido a problemas con el scraping."
        
        fin = datetime.now()
        tiempo_total = (fin - inicio).total_seconds() * 1000
        
        # Marcar como exitoso si se generó plantilla
        if plantilla_generada:
            self.estadisticas_fallback["fallbacks_exitosos"] += 1
        
        return FallbackResponse(
            fallback_activado=True,
            motivo_fallback=motivo,
            accion_tomada=accion,
            datos_parciales_encontrados=datos_parciales_encontrados,
            plantilla_generada=plantilla_generada,
            recomendacion=recomendacion,
            tiempo_total_intento_ms=tiempo_total,
            timestamp=fin
        )
    
    async def _generar_plantilla_prellenada(self, ruc: str, datos_consolidados: Dict[str, Any]) -> Dict[str, Any]:
        """Generar plantilla con datos encontrados pre-llenados"""
        plantilla_base = await self._generar_plantilla_vacia(ruc)
        
        # Rellenar con datos consolidados
        if datos_consolidados:
            plantilla_base.update({
                "razon_social": datos_consolidados.get("razon_social", ""),
                "estado": datos_consolidados.get("estado", "ACTIVO"),
                "contacto": {
                    "direccion": datos_consolidados.get("direccion", ""),
                    "telefono": datos_consolidados.get("telefono", ""),
                    "email": datos_consolidados.get("email", "")
                },
                "especialidades": datos_consolidados.get("especialidades", [])
            })
            
            # Rellenar representantes si existen
            if datos_consolidados.get("representantes"):
                plantilla_base["representantes"] = [
                    {
                        "nombre": rep.get("nombre", ""),
                        "cargo": rep.get("cargo", "GERENTE GENERAL"),
                        "tipo_documento": rep.get("tipo_documento", "DNI"),
                        "numero_documento": rep.get("numero_documento", ""),
                        "es_principal": i == 0,  # Primer representante como principal
                        "estado": "ACTIVO"
                    }
                    for i, rep in enumerate(datos_consolidados["representantes"])
                ]
        
        plantilla_base["_metadata"] = {
            "tipo_plantilla": "PRELLENADA",
            "fuentes_datos_parciales": datos_consolidados.get("fuente_datos", []) if datos_consolidados else [],
            "completitud_estimada": self._calcular_completitud(plantilla_base)
        }
        
        return plantilla_base
    
    async def _generar_plantilla_vacia(self, ruc: str) -> Dict[str, Any]:
        """Generar plantilla completamente vacía"""
        return {
            "ruc": ruc,
            "razon_social": "",
            "nombre_comercial": "",
            "tipo_empresa": "SAC",
            "estado": "ACTIVO",
            "departamento": "",
            "provincia": "",
            "distrito": "",
            "contacto": {
                "email": "",
                "telefono": "",
                "celular": "",
                "direccion": ""
            },
            "representantes": [
                {
                    "nombre": "",
                    "cargo": "GERENTE GENERAL",
                    "tipo_documento": "DNI",
                    "numero_documento": "",
                    "es_principal": True,
                    "estado": "ACTIVO"
                }
            ],
            "categoria_contratista": None,
            "especialidades": [],
            "observaciones": "",
            "fuente_datos": "MANUAL",
            "requiere_verificacion": True,
            "_metadata": {
                "tipo_plantilla": "VACIA",
                "completitud_estimada": 0.1
            }
        }
    
    async def _generar_plantilla_complementaria(self, ruc: str, datos_consolidados: Dict[str, Any]) -> Dict[str, Any]:
        """Generar plantilla que necesita complementar datos críticos faltantes"""
        plantilla = await self._generar_plantilla_prellenada(ruc, datos_consolidados)
        
        # Identificar campos críticos faltantes
        campos_criticos = ['razon_social', 'direccion', 'representantes']
        campos_faltantes = []
        
        for campo in campos_criticos:
            if campo == 'representantes':
                if not plantilla.get('representantes') or len(plantilla['representantes']) == 0:
                    campos_faltantes.append(campo)
            else:
                if not plantilla.get(campo) and not (plantilla.get('contacto', {}).get(campo)):
                    campos_faltantes.append(campo)
        
        plantilla["_metadata"] = {
            "tipo_plantilla": "COMPLEMENTARIA",
            "campos_criticos_faltantes": campos_faltantes,
            "completitud_estimada": self._calcular_completitud(plantilla)
        }
        
        return plantilla
    
    def _calcular_completitud(self, plantilla: Dict[str, Any]) -> float:
        """Calcular porcentaje de completitud de la plantilla"""
        campos_totales = [
            'razon_social', 'tipo_empresa', 'estado', 'contacto.email', 
            'contacto.telefono', 'contacto.direccion', 'representantes'
        ]
        
        campos_completos = 0
        
        for campo in campos_totales:
            if '.' in campo:
                # Campo anidado
                partes = campo.split('.')
                valor = plantilla.get(partes[0], {})
                if isinstance(valor, dict) and valor.get(partes[1]):
                    campos_completos += 1
            else:
                if campo == 'representantes':
                    if plantilla.get(campo) and len(plantilla[campo]) > 0:
                        rep = plantilla[campo][0]
                        if rep.get('nombre') and rep.get('numero_documento'):
                            campos_completos += 1
                else:
                    if plantilla.get(campo):
                        campos_completos += 1
        
        return campos_completos / len(campos_totales)
    
    def obtener_estadisticas(self) -> Dict[str, Any]:
        """Obtener estadísticas del sistema de fallback"""
        return {
            **self.estadisticas_fallback,
            "tasa_exitosa_fallback": (
                self.estadisticas_fallback["fallbacks_exitosos"] / 
                max(self.estadisticas_fallback["fallbacks_activados"], 1)
            ) * 100
        }

# Instancia global del sistema de fallback
fallback_system = FallbackIntelligentSystem()

@router.post("/crear-con-fallback", status_code=status.HTTP_201_CREATED)
async def crear_empresa_con_fallback_inteligente(
    ruc_data: Dict[str, str],
    config_fallback: Optional[FallbackConfig] = None,
    background_tasks: BackgroundTasks = None
):
    """
    🔄 Endpoint con sistema de fallback inteligente automático
    
    Este endpoint:
    1. Intenta scraping con timeout y reintentos configurables
    2. Detecta automáticamente la necesidad de fallback
    3. Activa el modo de fallback más apropiado
    4. Genera plantillas inteligentes según el caso
    5. Proporciona recomendaciones específicas
    """
    try:
        ruc = ruc_data.get("ruc", "").strip()
        
        if not validar_ruc_formato(ruc):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="RUC inválido. Debe tener 11 dígitos y comenzar con 10 o 20"
            )
        
        # Configurar sistema de fallback
        if config_fallback:
            system = FallbackIntelligentSystem(config_fallback)
        else:
            system = fallback_system
        
        # Verificar si ya existe
        empresa_service = get_empresa_service()
        empresa_existente = empresa_service.obtener_empresa_por_ruc(ruc)
        
        if empresa_existente:
            return {
                "success": True,
                "empresa_existente": True,
                "data": empresa_existente,
                "message": f"Empresa ya existe: {empresa_existente.get('razon_social', 'Sin nombre')}",
                "timestamp": datetime.now().isoformat()
            }
        
        logger.info(f"🔄 Iniciando proceso con fallback inteligente para RUC: {ruc}")
        
        # FASE 1: Intentar scraping con reintentos y timeout
        scraping_attempt = ScrapingAttempt(system.config)
        datos_scraped = await scraping_attempt.intentar_con_timeout_y_reintentos(ruc)
        
        # FASE 2: Detectar si se necesita fallback
        necesita_fallback, motivo = system.detectar_necesidad_fallback(datos_scraped)
        
        if not necesita_fallback:
            # CASO EXITOSO: Crear empresa automáticamente
            logger.info(f"✅ Scraping exitoso, creando empresa automáticamente")
            
            datos_consolidados = consolidar_datos_scraping(datos_scraped)
            datos_guardar = {
                **datos_consolidados,
                "ruc": ruc,
                "fuentes_consultadas": datos_consolidados.get("fuente_datos", []),
                "requiere_verificacion": False,
                "calidad_datos": "BUENA"
            }
            
            empresa_id = empresa_service.guardar_empresa(datos_guardar)
            empresa_creada = empresa_service.obtener_empresa_por_ruc(ruc)
            
            return {
                "success": True,
                "modo": "AUTOMATICO",
                "empresa_id": str(empresa_id),
                "data": empresa_creada,
                "fallback_activado": False,
                "fuentes_utilizadas": datos_consolidados.get("fuente_datos", []),
                "calidad_datos": "BUENA",
                "message": f"Empresa creada automáticamente: {datos_consolidados.get('razon_social', '')}",
                "timestamp": datetime.now().isoformat()
            }
        
        else:
            # CASO FALLBACK: Activar sistema inteligente
            logger.warning(f"⚠️ Activando fallback - Motivo: {motivo}")
            
            fallback_response = await system.manejar_fallback(ruc, datos_scraped, motivo)
            
            return {
                "success": True,
                "modo": "FALLBACK",
                "fallback_activado": True,
                "motivo_fallback": motivo,
                "accion_tomada": fallback_response.accion_tomada,
                "datos_parciales_encontrados": fallback_response.datos_parciales_encontrados,
                "plantilla_generada": fallback_response.plantilla_generada,
                "recomendacion": fallback_response.recomendacion,
                "errores_scraping": datos_scraped.get("errores", []),
                "intentos_scraping": datos_scraped.get("intentos_detallados", []),
                "tiempo_total_ms": fallback_response.tiempo_total_intento_ms,
                "message": f"Fallback activado: {fallback_response.recomendacion}",
                "timestamp": fallback_response.timestamp.isoformat()
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error crítico en proceso con fallback: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )

@router.get("/fallback/estadisticas")
async def obtener_estadisticas_fallback():
    """Obtener estadísticas del sistema de fallback inteligente"""
    try:
        estadisticas = fallback_system.obtener_estadisticas()
        
        return {
            "success": True,
            "estadisticas_fallback": estadisticas,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo estadísticas de fallback: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )

# =================================================================
# VALIDADORES ESPECÍFICOS AVANZADOS PARA DATOS MANUALES
# =================================================================

class ValidacionResult(BaseModel):
    """Resultado de una validación específica"""
    campo: str
    valido: bool
    mensaje: Optional[str] = None
    severidad: str = "INFO"  # INFO, WARNING, ERROR, CRITICAL
    sugerencia: Optional[str] = None
    valor_corregido: Optional[Any] = None

class ValidacionCompleteResult(BaseModel):
    """Resultado completo de validaciones"""
    validacion_exitosa: bool
    puntuacion_calidad: float  # 0.0 a 100.0
    nivel_confianza: str  # ALTA, MEDIA, BAJA
    validaciones_individuales: List[ValidacionResult]
    errores_criticos: List[str]
    advertencias: List[str]
    sugerencias_mejora: List[str]
    campos_corregidos: Dict[str, Any]
    timestamp: datetime

class ValidadorAvanzadoDatosManuales:
    """Sistema avanzado de validación para datos ingresados manualmente"""
    
    def __init__(self):
        # Patrones y reglas de validación
        self.patrones_email = [
            r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',  # Estándar
            r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,4}$'  # Con TLD de 2-4 caracteres
        ]
        
        self.patrones_telefono_peru = [
            r'^\d{7}$',        # Teléfono fijo Lima (7 dígitos)
            r'^01\d{7}$',      # Teléfono fijo Lima con código
            r'^\d{6}$',        # Teléfono fijo provincia (6 dígitos)
            r'^0\d{2}\d{6}$',  # Teléfono fijo provincia con código
            r'^9\d{8}$',       # Celular (9 dígitos iniciando en 9)
            r'^\+51\d{9}$',    # Celular con código país
        ]
        
        self.nombres_empresas_comunes = [
            'SAC', 'S.A.C.', 'S.A.C', 'SA', 'S.A.', 'S.A',
            'SRL', 'S.R.L.', 'S.R.L', 'EIRL', 'E.I.R.L.', 'E.I.R.L'
        ]
        
        self.ubigeos_validos = self._cargar_ubigeos_validos()
        self.sectores_economicos = self._cargar_sectores_economicos()
        self.cargos_directivos_comunes = self._cargar_cargos_directivos()
    
    def _cargar_ubigeos_validos(self) -> List[str]:
        """Cargar códigos UBIGEO válidos (simulado - en producción sería desde BD)"""
        # En producción esto se cargaría desde la BD o un archivo
        return [
            "150101",  # Lima - Lima - Lima
            "150102",  # Lima - Lima - Ancón
            "150103",  # Lima - Lima - Ate
            "150104",  # Lima - Lima - Barranco
            "150105",  # Lima - Lima - Breña
            # ... más ubigeos
        ]
    
    def _cargar_sectores_economicos(self) -> List[str]:
        """Cargar sectores económicos válidos"""
        return [
            "CONSTRUCCIÓN", "MANUFACTURA", "SERVICIOS", "COMERCIO",
            "AGRICULTURA", "MINERÍA", "PESCA", "TURISMO", "TECNOLOGÍA",
            "EDUCACIÓN", "SALUD", "TRANSPORTE", "COMUNICACIONES",
            "ENERGÍA", "INMOBILIARIO", "FINANCIERO"
        ]
    
    def _cargar_cargos_directivos(self) -> Dict[str, List[str]]:
        """Cargar cargos directivos válidos por categoría"""
        return {
            "ejecutivos": [
                "GERENTE GENERAL", "GERENTE", "DIRECTOR GENERAL", "DIRECTOR EJECUTIVO",
                "PRESIDENTE", "VICEPRESIDENTE", "ADMINISTRADOR GENERAL"
            ],
            "gerenciales": [
                "GERENTE COMERCIAL", "GERENTE ADMINISTRATIVO", "GERENTE FINANCIERO",
                "GERENTE DE OPERACIONES", "GERENTE DE MARKETING", "GERENTE TÉCNICO"
            ],
            "legales": [
                "REPRESENTANTE LEGAL", "APODERADO", "APODERADO GENERAL",
                "MANDATARIO", "ADMINISTRADOR"
            ]
        }
    
    def validar_ruc_avanzado(self, ruc: str) -> ValidacionResult:
        """Validación avanzada de RUC con verificación de dígito verificador"""
        if not ruc or len(ruc) != 11:
            return ValidacionResult(
                campo="ruc",
                valido=False,
                mensaje="RUC debe tener exactamente 11 dígitos",
                severidad="CRITICAL",
                sugerencia="Verificar que el RUC esté completo y sin espacios"
            )
        
        if not ruc.isdigit():
            # Intentar limpiar caracteres no numéricos
            ruc_limpio = ''.join(filter(str.isdigit, ruc))
            return ValidacionResult(
                campo="ruc",
                valido=False,
                mensaje="RUC debe contener solo dígitos",
                severidad="ERROR",
                sugerencia="Remover espacios, guiones y otros caracteres",
                valor_corregido=ruc_limpio if len(ruc_limpio) == 11 else None
            )
        
        # Validar que comience con 10 o 20
        if not (ruc.startswith('10') or ruc.startswith('20')):
            return ValidacionResult(
                campo="ruc",
                valido=False,
                mensaje="RUC debe comenzar con 10 (persona natural) o 20 (empresa)",
                severidad="CRITICAL"
            )
        
        # Validación del dígito verificador (algoritmo oficial SUNAT)
        if not self._validar_digito_verificador_ruc(ruc):
            return ValidacionResult(
                campo="ruc",
                valido=False,
                mensaje="RUC tiene dígito verificador inválido",
                severidad="ERROR",
                sugerencia="Verificar que el RUC esté escrito correctamente"
            )
        
        return ValidacionResult(
            campo="ruc",
            valido=True,
            mensaje="RUC válido",
            severidad="INFO"
        )
    
    def _validar_digito_verificador_ruc(self, ruc: str) -> bool:
        """Validar dígito verificador del RUC según algoritmo SUNAT"""
        if len(ruc) != 11:
            return False
        
        # Factores de multiplicación
        factores = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]
        
        # Calcular suma ponderada de los primeros 10 dígitos
        suma = sum(int(ruc[i]) * factores[i] for i in range(10))
        
        # Calcular residuo
        residuo = suma % 11
        
        # Determinar dígito verificador esperado
        if residuo < 2:
            digito_esperado = residuo
        else:
            digito_esperado = 11 - residuo
        
        # Comparar con el dígito actual
        return int(ruc[10]) == digito_esperado
    
    def validar_nombre_empresa(self, razon_social: str) -> ValidacionResult:
        """Validación avanzada del nombre de empresa"""
        if not razon_social or len(razon_social.strip()) < 3:
            return ValidacionResult(
                campo="razon_social",
                valido=False,
                mensaje="Razón social debe tener al menos 3 caracteres",
                severidad="CRITICAL"
            )
        
        nombre_limpio = razon_social.strip()
        
        # Detectar si tiene formato de empresa
        tiene_tipo_empresa = any(tipo in nombre_limpio.upper() for tipo in self.nombres_empresas_comunes)
        
        # Validar caracteres permitidos
        patron_valido = r"^[A-Za-zÁáÉéÍíÓóÚúÜüÑñ0-9\s\-\.,'&]+$"
        if not re.match(patron_valido, nombre_limpio):
            return ValidacionResult(
                campo="razon_social",
                valido=False,
                mensaje="Razón social contiene caracteres no válidos",
                severidad="ERROR",
                sugerencia="Solo se permiten letras, números, espacios y signos básicos"
            )
        
        # Normalizar espacios múltiples
        nombre_normalizado = ' '.join(nombre_limpio.split())
        
        sugerencias = []
        if not tiene_tipo_empresa:
            sugerencias.append("Considerar agregar el tipo de empresa (SAC, SRL, etc.)")
        
        if nombre_limpio != nombre_normalizado:
            sugerencias.append("Se normalizaron espacios múltiples")
        
        return ValidacionResult(
            campo="razon_social",
            valido=True,
            mensaje="Razón social válida",
            severidad="INFO" if not sugerencias else "WARNING",
            sugerencia="; ".join(sugerencias) if sugerencias else None,
            valor_corregido=nombre_normalizado if nombre_limpio != nombre_normalizado else None
        )
    
    def validar_email_empresarial(self, email: str) -> ValidacionResult:
        """Validación avanzada de email empresarial"""
        if not email or not email.strip():
            return ValidacionResult(
                campo="email",
                valido=True,
                mensaje="Email opcional no proporcionado",
                severidad="INFO"
            )
        
        email_limpio = email.strip().lower()
        
        # Validar formato básico
        email_valido = any(re.match(patron, email_limpio) for patron in self.patrones_email)
        
        if not email_valido:
            return ValidacionResult(
                campo="email",
                valido=False,
                mensaje="Email tiene formato inválido",
                severidad="ERROR",
                sugerencia="Verificar que tenga formato nombre@dominio.com"
            )
        
        # Detectar dominios comunes de email personal
        dominios_personales = ['gmail.com', 'hotmail.com', 'yahoo.com', 'outlook.com', 'live.com']
        dominio = email_limpio.split('@')[1] if '@' in email_limpio else ''
        
        advertencias = []
        if dominio in dominios_personales:
            advertencias.append("Se detectó email personal, considerar usar email corporativo")
        
        # Detectar patrones profesionales
        if any(palabra in email_limpio for palabra in ['info', 'contacto', 'ventas', 'admin']):
            advertencias.append("Email parece ser corporativo")
        
        return ValidacionResult(
            campo="email",
            valido=True,
            mensaje="Email válido",
            severidad="WARNING" if advertencias else "INFO",
            sugerencia="; ".join(advertencias) if advertencias else None,
            valor_corregido=email_limpio if email != email_limpio else None
        )
    
    def validar_telefono_peruano(self, telefono: str, tipo: str = "general") -> ValidacionResult:
        """Validación específica para teléfonos peruanos"""
        if not telefono or not telefono.strip():
            return ValidacionResult(
                campo=f"telefono_{tipo}",
                valido=True,
                mensaje="Teléfono opcional no proporcionado",
                severidad="INFO"
            )
        
        # Limpiar formato
        telefono_limpio = re.sub(r'[\s\-\(\)\+]+', '', telefono.strip())
        
        # Remover código de país si está presente
        if telefono_limpio.startswith('51') and len(telefono_limpio) == 11:
            telefono_limpio = telefono_limpio[2:]
        elif telefono_limpio.startswith('+51'):
            telefono_limpio = telefono_limpio[3:]
        
        # Validar contra patrones peruanos
        telefono_valido = any(re.match(patron, telefono_limpio) for patron in self.patrones_telefono_peru)
        
        if not telefono_valido:
            return ValidacionResult(
                campo=f"telefono_{tipo}",
                valido=False,
                mensaje="Formato de teléfono no válido para Perú",
                severidad="ERROR",
                sugerencia="Teléfonos fijos: 7 dígitos (Lima) o 6 dígitos (provincia). Celulares: 9 dígitos iniciando en 9"
            )
        
        # Determinar tipo de teléfono
        tipo_detectado = ""
        if telefono_limpio.startswith('9') and len(telefono_limpio) == 9:
            tipo_detectado = "Celular"
        elif len(telefono_limpio) == 7:
            tipo_detectado = "Fijo Lima"
        elif len(telefono_limpio) == 6:
            tipo_detectado = "Fijo Provincia"
        
        return ValidacionResult(
            campo=f"telefono_{tipo}",
            valido=True,
            mensaje=f"Teléfono válido ({tipo_detectado})",
            severidad="INFO",
            valor_corregido=telefono_limpio if telefono != telefono_limpio else None
        )
    
    def validar_representante_avanzado(self, representante: Dict[str, Any]) -> List[ValidacionResult]:
        """Validación avanzada de representante legal"""
        resultados = []
        
        # Validar nombre
        nombre = representante.get('nombre', '')
        if not nombre or len(nombre.strip()) < 2:
            resultados.append(ValidacionResult(
                campo="representante.nombre",
                valido=False,
                mensaje="Nombre del representante es requerido",
                severidad="CRITICAL"
            ))
        else:
            # Validar que no tenga números (raro en nombres)
            if re.search(r'\d', nombre):
                resultados.append(ValidacionResult(
                    campo="representante.nombre",
                    valido=False,
                    mensaje="Nombre del representante contiene números",
                    severidad="WARNING",
                    sugerencia="Verificar que el nombre esté correcto"
                ))
            
            # Normalizar nombre
            nombre_normalizado = ' '.join(word.capitalize() for word in nombre.strip().split())
            if nombre != nombre_normalizado:
                resultados.append(ValidacionResult(
                    campo="representante.nombre",
                    valido=True,
                    mensaje="Nombre normalizado",
                    severidad="INFO",
                    valor_corregido=nombre_normalizado
                ))
        
        # Validar cargo
        cargo = representante.get('cargo', '')
        if cargo:
            cargo_upper = cargo.upper().strip()
            cargo_encontrado = None
            
            # Buscar cargo en categorías
            for categoria, cargos in self.cargos_directivos_comunes.items():
                if cargo_upper in cargos:
                    cargo_encontrado = categoria
                    break
            
            if cargo_encontrado:
                resultados.append(ValidacionResult(
                    campo="representante.cargo",
                    valido=True,
                    mensaje=f"Cargo válido (categoría: {cargo_encontrado})",
                    severidad="INFO"
                ))
            else:
                resultados.append(ValidacionResult(
                    campo="representante.cargo",
                    valido=True,
                    mensaje="Cargo no estándar",
                    severidad="WARNING",
                    sugerencia="Verificar que el cargo sea correcto"
                ))
        
        # Validar documento
        tipo_doc = representante.get('tipo_documento', 'DNI')
        numero_doc = representante.get('numero_documento', '')
        
        if tipo_doc == 'DNI':
            if not numero_doc.isdigit() or len(numero_doc) != 8:
                resultados.append(ValidacionResult(
                    campo="representante.numero_documento",
                    valido=False,
                    mensaje="DNI debe tener exactamente 8 dígitos",
                    severidad="CRITICAL"
                ))
            else:
                resultados.append(ValidacionResult(
                    campo="representante.numero_documento",
                    valido=True,
                    mensaje="DNI válido",
                    severidad="INFO"
                ))
        
        return resultados
    
    def validar_direccion_avanzada(self, direccion: str, ubigeo: str = None) -> ValidacionResult:
        """Validación avanzada de dirección"""
        if not direccion or len(direccion.strip()) < 5:
            return ValidacionResult(
                campo="direccion",
                valido=False,
                mensaje="Dirección debe tener al menos 5 caracteres",
                severidad="ERROR",
                sugerencia="Proporcionar dirección completa con referencia"
            )
        
        direccion_limpia = direccion.strip()
        
        # Detectar componentes de dirección
        componentes = {
            'tiene_numero': bool(re.search(r'\d', direccion_limpia)),
            'tiene_calle': any(palabra in direccion_limpia.lower() for palabra in 
                              ['av', 'avenida', 'jr', 'jiron', 'jirón', 'calle', 'ca', 'psj', 'pasaje']),
            'tiene_distrito': any(palabra in direccion_limpia.lower() for palabra in 
                                 ['lima', 'miraflores', 'san isidro', 'barranco', 'surco', 'chorrillos']),
        }
        
        calidad = sum(componentes.values())
        
        if calidad >= 2:
            severidad = "INFO"
            mensaje = "Dirección completa"
        elif calidad == 1:
            severidad = "WARNING"
            mensaje = "Dirección básica, considerar agregar más detalles"
        else:
            severidad = "ERROR"
            mensaje = "Dirección muy básica"
        
        # Validar UBIGEO si está presente
        sugerencia = None
        if ubigeo and ubigeo not in self.ubigeos_validos:
            sugerencia = "UBIGEO no reconocido, verificar código"
        
        return ValidacionResult(
            campo="direccion",
            valido=calidad > 0,
            mensaje=mensaje,
            severidad=severidad,
            sugerencia=sugerencia
        )
    
    def validar_empresa_completa(self, datos_empresa: Dict[str, Any]) -> ValidacionCompleteResult:
        """Validación completa de todos los datos de la empresa"""
        inicio = datetime.now()
        
        validaciones = []
        errores_criticos = []
        advertencias = []
        sugerencias_mejora = []
        campos_corregidos = {}
        
        # Validar RUC
        validacion_ruc = self.validar_ruc_avanzado(datos_empresa.get('ruc', ''))
        validaciones.append(validacion_ruc)
        if not validacion_ruc.valido and validacion_ruc.severidad == "CRITICAL":
            errores_criticos.append(validacion_ruc.mensaje)
        elif validacion_ruc.valor_corregido:
            campos_corregidos['ruc'] = validacion_ruc.valor_corregido
        
        # Validar razón social
        validacion_nombre = self.validar_nombre_empresa(datos_empresa.get('razon_social', ''))
        validaciones.append(validacion_nombre)
        if validacion_nombre.valor_corregido:
            campos_corregidos['razon_social'] = validacion_nombre.valor_corregido
        if validacion_nombre.sugerencia:
            sugerencias_mejora.append(validacion_nombre.sugerencia)
        
        # Validar contacto
        if datos_empresa.get('contacto'):
            contacto = datos_empresa['contacto']
            
            # Email
            if contacto.get('email'):
                validacion_email = self.validar_email_empresarial(contacto['email'])
                validaciones.append(validacion_email)
                if validacion_email.valor_corregido:
                    if 'contacto' not in campos_corregidos:
                        campos_corregidos['contacto'] = {}
                    campos_corregidos['contacto']['email'] = validacion_email.valor_corregido
                if validacion_email.sugerencia:
                    advertencias.append(f"Email: {validacion_email.sugerencia}")
            
            # Teléfonos
            for tipo_tel in ['telefono', 'celular']:
                if contacto.get(tipo_tel):
                    validacion_tel = self.validar_telefono_peruano(contacto[tipo_tel], tipo_tel)
                    validaciones.append(validacion_tel)
                    if validacion_tel.valor_corregido:
                        if 'contacto' not in campos_corregidos:
                            campos_corregidos['contacto'] = {}
                        campos_corregidos['contacto'][tipo_tel] = validacion_tel.valor_corregido
            
            # Dirección
            if contacto.get('direccion'):
                validacion_dir = self.validar_direccion_avanzada(
                    contacto['direccion'], 
                    datos_empresa.get('ubigeo')
                )
                validaciones.append(validacion_dir)
                if not validacion_dir.valido:
                    advertencias.append(f"Dirección: {validacion_dir.mensaje}")
        
        # Validar representantes
        if datos_empresa.get('representantes'):
            for i, rep in enumerate(datos_empresa['representantes']):
                validaciones_rep = self.validar_representante_avanzado(rep)
                validaciones.extend(validaciones_rep)
                
                for val_rep in validaciones_rep:
                    if not val_rep.valido and val_rep.severidad == "CRITICAL":
                        errores_criticos.append(f"Representante {i+1}: {val_rep.mensaje}")
                    elif val_rep.valor_corregido:
                        if 'representantes' not in campos_corregidos:
                            campos_corregidos['representantes'] = {}
                        if i not in campos_corregidos['representantes']:
                            campos_corregidos['representantes'][i] = {}
                        campo_rep = val_rep.campo.split('.')[-1]
                        campos_corregidos['representantes'][i][campo_rep] = val_rep.valor_corregido
        
        # Calcular puntuación de calidad
        total_validaciones = len(validaciones)
        validaciones_exitosas = sum(1 for v in validaciones if v.valido)
        puntuacion_base = (validaciones_exitosas / max(total_validaciones, 1)) * 100
        
        # Ajustar puntuación por errores críticos
        penalizacion_criticos = len(errores_criticos) * 15
        puntuacion_final = max(0, puntuacion_base - penalizacion_criticos)
        
        # Determinar nivel de confianza
        if puntuacion_final >= 85:
            nivel_confianza = "ALTA"
        elif puntuacion_final >= 70:
            nivel_confianza = "MEDIA"
        else:
            nivel_confianza = "BAJA"
        
        # Agregar sugerencias generales
        if not datos_empresa.get('especialidades'):
            sugerencias_mejora.append("Considerar agregar especialidades de la empresa")
        
        if not datos_empresa.get('categoria_contratista'):
            sugerencias_mejora.append("Especificar si es empresa EJECUTORA o SUPERVISORA")
        
        return ValidacionCompleteResult(
            validacion_exitosa=len(errores_criticos) == 0,
            puntuacion_calidad=round(puntuacion_final, 2),
            nivel_confianza=nivel_confianza,
            validaciones_individuales=validaciones,
            errores_criticos=errores_criticos,
            advertencias=advertencias,
            sugerencias_mejora=sugerencias_mejora,
            campos_corregidos=campos_corregidos,
            timestamp=datetime.now()
        )

# Instancia global del validador
validador_avanzado = ValidadorAvanzadoDatosManuales()

@router.post("/validar-datos-manuales")
async def validar_datos_manuales_avanzado(
    datos_empresa: Dict[str, Any]
) -> ValidacionCompleteResult:
    """
    🔍 Validación avanzada de datos ingresados manualmente
    
    Este endpoint:
    1. Ejecuta validaciones específicas para cada campo
    2. Detecta y corrige errores comunes
    3. Proporciona sugerencias de mejora
    4. Calcula puntuación de calidad de datos
    5. Determina nivel de confianza
    """
    try:
        logger.info(f"🔍 Iniciando validación avanzada de datos manuales")
        
        resultado = validador_avanzado.validar_empresa_completa(datos_empresa)
        
        logger.info(f"✅ Validación completada - Calidad: {resultado.puntuacion_calidad}%, Confianza: {resultado.nivel_confianza}")
        
        return resultado
        
    except Exception as e:
        logger.error(f"❌ Error en validación avanzada: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )
