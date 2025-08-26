"""
Servicio de consolidación que combina datos de SUNAT y OECE
Implementa deduplicación inteligente y lógica de prioridades
"""
import asyncio
import logging
import difflib
import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from app.models.consolidated import (
    EmpresaConsolidada, 
    MiembroConsolidado, 
    ContactoConsolidado, 
    RegistroConsolidado,
    ErrorConsolidado
)
from app.models.ruc import EmpresaInfo, RepresentanteLegal
from app.models.osce import EmpresaOSCE, IntegranteOSCE
# Import the working SUNAT function from main.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from app.services.osce_service import OSCEService
from app.utils.exceptions import ValidationException, ExtractionException

logger = logging.getLogger(__name__)


class ConsolidationService:
    """Servicio para consolidar datos de SUNAT y OECE"""
    
    def __init__(self):
        self.oece_service = OSCEService()
        
        # Configuración para matching de nombres
        self.similarity_threshold = 0.7  # Umbral de similitud para considerar nombres iguales
        self.dni_match_priority = True   # Priorizar matching por DNI sobre nombre
        
    async def consultar_consolidado(self, ruc: str) -> EmpresaConsolidada:
        """
        Consultar información consolidada de SUNAT y OECE
        
        Args:
            ruc: RUC de 11 dígitos
            
        Returns:
            EmpresaConsolidada: Información consolidada de ambas fuentes
            
        Raises:
            ValidationException: Si el RUC no es válido
            ExtractionException: Si ambas fuentes fallan
        """
        logger.info(f"🔄 Iniciando consolidación para RUC: {ruc}")
        
        # Validar RUC
        if not self._validar_ruc(ruc):
            raise ValidationException(f"RUC inválido: {ruc}")
        
        # Inicializar resultados
        datos_sunat = None
        datos_oece = None
        errores_sunat = None
        errores_osce = None
        
        # Ejecutar consultas en paralelo para mejor rendimiento
        try:
            resultados = await asyncio.gather(
                self._consultar_sunat_safe(ruc),
                self._consultar_oece_safe(ruc),
                return_exceptions=True
            )
            
            # Procesar resultados de SUNAT
            resultado_sunat = resultados[0]
            if isinstance(resultado_sunat, Exception):
                errores_sunat = str(resultado_sunat)
                logger.warning(f"⚠️ Error en SUNAT: {errores_sunat}")
            else:
                datos_sunat = resultado_sunat
                logger.info("✅ Datos SUNAT obtenidos exitosamente")
            
            # Procesar resultados de OSCE
            resultado_osce = resultados[1]
            if isinstance(resultado_osce, Exception):
                errores_osce = str(resultado_osce)
                logger.warning(f"⚠️ Error en OSCE: {errores_osce}")
            else:
                datos_oece = resultado_osce
                logger.info("✅ Datos OSCE obtenidos exitosamente")
                
        except Exception as e:
            logger.error(f"❌ Error en consultas paralelas: {str(e)}")
            raise ExtractionException(f"Error general en consolidación: {str(e)}")
        
        # Verificar que al menos una fuente haya respondido
        if datos_sunat is None and datos_oece is None:
            raise ExtractionException(
                f"Ambas fuentes fallaron - SUNAT: {errores_sunat} | OSCE: {errores_osce}"
            )
        
        # Consolidar datos
        empresa_consolidada = await self._consolidar_datos(
            ruc, datos_sunat, datos_oece, errores_sunat, errores_osce
        )
        
        logger.info(f"✅ Consolidación completada para RUC {ruc}")
        return empresa_consolidada
    
    async def _consultar_sunat_safe(self, ruc: str) -> Optional[EmpresaInfo]:
        """Consultar SUNAT con manejo seguro de errores usando la función funcional de main.py"""
        try:
            # Import the working SUNAT function from main.py
            from main import buscar_ruc_impl
            
            # Call the working function directly
            data = await buscar_ruc_impl(ruc)
            
            if "error" in data and data["error"]:
                raise Exception(data.get("message", "Error en consulta SUNAT"))
            
            # Crear lista de representantes
            representantes = []
            for rep_data in data.get("representantes", []):
                representante = RepresentanteLegal(
                    tipo_doc=rep_data.get("tipo_doc", ""),
                    numero_doc=rep_data.get("numero_doc", ""),
                    nombre=rep_data.get("nombre", ""),
                    cargo=rep_data.get("cargo", ""),
                    fecha_desde=rep_data.get("fecha_desde", "")
                )
                representantes.append(representante)
            
            # Crear objeto EmpresaInfo
            empresa_info = EmpresaInfo(
                ruc=data.get("ruc", ruc),
                razon_social=data.get("razon_social", ""),
                domicilio_fiscal=data.get("domicilio_fiscal", ""),
                representantes=representantes
            )
            
            logger.info(f"✅ SUNAT: Datos obtenidos exitosamente para RUC {ruc}")
            return empresa_info
            
        except Exception as e:
            logger.warning(f"Error en consulta SUNAT: {str(e)}")
            raise e
    
    async def _consultar_oece_safe(self, ruc: str) -> Optional[EmpresaOSCE]:
        """Consultar OECE con manejo seguro de errores"""
        try:
            return await self.oece_service.consultar_empresa(ruc)
        except Exception as e:
            logger.warning(f"Error en consulta OECE: {str(e)}")
            raise e
    
    async def _consolidar_datos(
        self, 
        ruc: str, 
        datos_sunat: Optional[EmpresaInfo], 
        datos_oece: Optional[EmpresaOSCE],
        error_sunat: Optional[str],
        error_oece: Optional[str]
    ) -> EmpresaConsolidada:
        """Consolidar datos de ambas fuentes aplicando lógica de prioridades"""
        
        logger.info("🔧 Iniciando proceso de consolidación de datos")
        
        # Determinar razón social (prioridad: SUNAT)
        razon_social = ""
        if datos_sunat and datos_sunat.razon_social:
            razon_social = datos_sunat.razon_social
        elif datos_oece and datos_oece.razon_social:
            razon_social = datos_oece.razon_social
        
        # Consolidar información de contacto
        contacto = await self._consolidar_contacto(datos_sunat, datos_oece)
        
        # Consolidar miembros (deduplicación inteligente)
        miembros = await self._consolidar_miembros(datos_sunat, datos_oece)
        
        # Consolidar información de registro
        registro = await self._consolidar_registro(datos_sunat, datos_oece)
        
        # Determinar fuentes consultadas y con errores
        fuentes_consultadas = []
        fuentes_con_errores = []
        
        if datos_sunat:
            fuentes_consultadas.append("SUNAT")
        elif error_sunat:
            fuentes_con_errores.append("SUNAT")
            
        if datos_oece:
            fuentes_consultadas.append("OECE")
        elif error_oece:
            fuentes_con_errores.append("OECE")
        
        # Especialidades (solo OECE)
        especialidades = []
        especialidades_detalle = []
        capacidad_contratacion = ""
        vigencia = ""
        
        if datos_oece:
            especialidades = datos_oece.especialidades or []
            especialidades_detalle = datos_oece.especialidades_detalle or []
            capacidad_contratacion = datos_oece.capacidad_contratacion or ""
            vigencia = datos_oece.vigencia or ""
        
        # Observaciones sobre la consolidación
        observaciones = []
        if error_sunat:
            observaciones.append(f"SUNAT: {error_sunat}")
        if error_oece:
            observaciones.append(f"OECE: {error_oece}")
        
        consolidacion_exitosa = len(fuentes_consultadas) > 0
        
        empresa_consolidada = EmpresaConsolidada(
            ruc=ruc,
            razon_social=razon_social,
            contacto=contacto,
            miembros=miembros,
            especialidades=especialidades,
            especialidades_detalle=especialidades_detalle,
            registro=registro,
            fuentes_consultadas=fuentes_consultadas,
            fuentes_con_errores=fuentes_con_errores,
            capacidad_contratacion=capacidad_contratacion,
            vigencia=vigencia,
            consolidacion_exitosa=consolidacion_exitosa,
            observaciones=observaciones
        )
        
        logger.info(f"📊 Consolidación: {len(miembros)} miembros únicos, {len(especialidades)} especialidades")
        return empresa_consolidada
    
    async def _consolidar_contacto(
        self, 
        datos_sunat: Optional[EmpresaInfo], 
        datos_oece: Optional[EmpresaOSCE]
    ) -> ContactoConsolidado:
        """Consolidar información de contacto con prioridad OECE > SUNAT"""
        
        contacto = ContactoConsolidado()
        
        # Domicilio fiscal (solo SUNAT tiene esta información típicamente)
        if datos_sunat and datos_sunat.domicilio_fiscal:
            contacto.domicilio_fiscal = datos_sunat.domicilio_fiscal
        
        # Información de OECE tiene prioridad para contacto
        if datos_oece:
            if datos_oece.telefono:
                contacto.telefono = datos_oece.telefono
            if datos_oece.email:
                contacto.email = datos_oece.email
            
            # Información del objeto contacto si existe
            if hasattr(datos_oece, 'contacto') and datos_oece.contacto:
                contacto_oece = datos_oece.contacto
                if contacto_oece.direccion:
                    contacto.direccion = contacto_oece.direccion
                if contacto_oece.ciudad:
                    contacto.ciudad = contacto_oece.ciudad
                if contacto_oece.departamento:
                    contacto.departamento = contacto_oece.departamento
                # Sobrescribir teléfono y email si están en el objeto contacto
                if contacto_oece.telefono:
                    contacto.telefono = contacto_oece.telefono
                if contacto_oece.email:
                    contacto.email = contacto_oece.email
        
        # Si OECE no tiene contacto, usar SUNAT como fallback
        if not contacto.telefono and datos_sunat and hasattr(datos_sunat, 'telefono'):
            contacto.telefono = getattr(datos_sunat, 'telefono', '')
        if not contacto.email and datos_sunat and hasattr(datos_sunat, 'email'):
            contacto.email = getattr(datos_sunat, 'email', '')
        if not contacto.direccion and contacto.domicilio_fiscal:
            contacto.direccion = contacto.domicilio_fiscal
        
        return contacto
    
    async def _consolidar_miembros(
        self, 
        datos_sunat: Optional[EmpresaInfo], 
        datos_oece: Optional[EmpresaOSCE]
    ) -> List[MiembroConsolidado]:
        """Consolidar miembros con deduplicación inteligente"""
        
        logger.info("👥 Iniciando consolidación de miembros")
        
        miembros_consolidados = []
        
        # Obtener listas de miembros
        representantes_sunat = datos_sunat.representantes if datos_sunat else []
        integrantes_oece = datos_oece.integrantes if datos_oece else []
        
        logger.info(f"   📋 SUNAT: {len(representantes_sunat)} representantes")
        logger.info(f"   📋 OECE: {len(integrantes_oece)} integrantes")
        
        # Crear diccionario de miembros OSCE por DNI para matching rápido
        oece_por_dni = {}
        oece_por_nombre = {}
        
        for integrante in integrantes_oece:
            if integrante.numero_documento:
                oece_por_dni[integrante.numero_documento] = integrante
            if integrante.nombre:
                oece_por_nombre[integrante.nombre.upper().strip()] = integrante
        
        # Procesar representantes de SUNAT
        oece_procesados = set()
        
        for representante in representantes_sunat:
            miembro_oece_coincidente = None
            metodo_matching = ""
            
            # 1. Intentar matching por DNI (más confiable)
            if representante.numero_doc and representante.numero_doc in oece_por_dni:
                miembro_oece_coincidente = oece_por_dni[representante.numero_doc]
                metodo_matching = "DNI"
                oece_procesados.add(id(miembro_oece_coincidente))
            
            # 2. Si no hay match por DNI, intentar por similitud de nombres
            elif not miembro_oece_coincidente:
                mejor_match, similitud = self._encontrar_mejor_match_nombre(
                    representante.nombre, list(oece_por_nombre.keys())
                )
                
                if mejor_match and similitud >= self.similarity_threshold:
                    miembro_oece_coincidente = oece_por_nombre[mejor_match]
                    metodo_matching = f"NOMBRE ({similitud:.2f})"
                    oece_procesados.add(id(miembro_oece_coincidente))
            
            # Crear miembro consolidado
            if miembro_oece_coincidente:
                # Combinar información de ambas fuentes
                miembro = self._crear_miembro_combinado(
                    representante, miembro_oece_coincidente, metodo_matching
                )
                logger.info(f"   ✅ Miembro combinado ({metodo_matching}): {miembro.nombre}")
            else:
                # Solo información de SUNAT
                miembro = self._crear_miembro_desde_sunat(representante)
                logger.info(f"   📍 Solo SUNAT: {miembro.nombre}")
            
            miembros_consolidados.append(miembro)
        
        # Agregar integrantes de OSCE que no fueron procesados
        for integrante in integrantes_oece:
            if id(integrante) not in oece_procesados:
                miembro = self._crear_miembro_desde_oece(integrante)
                miembros_consolidados.append(miembro)
                logger.info(f"   🎯 Solo OECE: {miembro.nombre}")
        
        logger.info(f"   ✅ Total consolidado: {len(miembros_consolidados)} miembros únicos")
        return miembros_consolidados
    
    def _encontrar_mejor_match_nombre(self, nombre_objetivo: str, lista_nombres: List[str]) -> Tuple[Optional[str], float]:
        """Encontrar el mejor match de nombre usando similitud de secuencias"""
        
        if not nombre_objetivo or not lista_nombres:
            return None, 0.0
        
        nombre_objetivo_clean = self._limpiar_nombre_para_matching(nombre_objetivo)
        mejor_match = None
        mejor_similitud = 0.0
        
        for nombre_candidato in lista_nombres:
            nombre_candidato_clean = self._limpiar_nombre_para_matching(nombre_candidato)
            
            # Calcular similitud usando difflib
            similitud = difflib.SequenceMatcher(
                None, nombre_objetivo_clean, nombre_candidato_clean
            ).ratio()
            
            if similitud > mejor_similitud:
                mejor_similitud = similitud
                mejor_match = nombre_candidato
        
        return mejor_match, mejor_similitud
    
    def _limpiar_nombre_para_matching(self, nombre: str) -> str:
        """Limpiar nombre para mejorar matching"""
        if not nombre:
            return ""
        
        # Convertir a mayúsculas y remover espacios extra
        nombre_limpio = nombre.upper().strip()
        
        # Remover caracteres especiales
        nombre_limpio = re.sub(r'[^\w\s]', '', nombre_limpio)
        
        # Normalizar espacios múltiples
        nombre_limpio = re.sub(r'\s+', ' ', nombre_limpio)
        
        return nombre_limpio
    
    def _crear_miembro_combinado(
        self, 
        representante: RepresentanteLegal, 
        integrante: IntegranteOSCE,
        metodo_matching: str
    ) -> MiembroConsolidado:
        """Crear miembro consolidado combinando datos de SUNAT y OECE"""
        
        # Combinar cargos (OECE tiene prioridad si existe)
        cargo = integrante.cargo if integrante.cargo else representante.cargo
        if integrante.cargo and representante.cargo and integrante.cargo != representante.cargo:
            cargo = f"{integrante.cargo} / {representante.cargo}"
        
        return MiembroConsolidado(
            nombre=representante.nombre,  # SUNAT es más confiable para nombres
            cargo=cargo,
            tipo_documento=representante.tipo_doc or integrante.tipo_documento or "",
            numero_documento=representante.numero_doc or integrante.numero_documento or "",
            participacion=integrante.participacion or "",
            fecha_desde=representante.fecha_desde or "",
            fuente="AMBOS",
            fuentes_detalle={
                "sunat": {
                    "cargo": representante.cargo,
                    "fecha_desde": representante.fecha_desde,
                    "tipo_doc": representante.tipo_doc,
                    "numero_doc": representante.numero_doc
                },
                "oece": {
                    "cargo": integrante.cargo,
                    "participacion": integrante.participacion,
                    "tipo_documento": integrante.tipo_documento,
                    "numero_documento": integrante.numero_documento
                },
                "matching": metodo_matching
            }
        )
    
    def _crear_miembro_desde_sunat(self, representante: RepresentanteLegal) -> MiembroConsolidado:
        """Crear miembro consolidado solo con datos de SUNAT"""
        return MiembroConsolidado(
            nombre=representante.nombre,
            cargo=representante.cargo,
            tipo_documento=representante.tipo_doc,
            numero_documento=representante.numero_doc,
            fecha_desde=representante.fecha_desde,
            fuente="SUNAT",
            fuentes_detalle={
                "sunat": {
                    "cargo": representante.cargo,
                    "fecha_desde": representante.fecha_desde,
                    "tipo_doc": representante.tipo_doc,
                    "numero_doc": representante.numero_doc
                }
            }
        )
    
    def _crear_miembro_desde_oece(self, integrante: IntegranteOSCE) -> MiembroConsolidado:
        """Crear miembro consolidado solo con datos de OECE"""
        return MiembroConsolidado(
            nombre=integrante.nombre,
            cargo=integrante.cargo,
            tipo_documento=integrante.tipo_documento,
            numero_documento=integrante.numero_documento,
            participacion=integrante.participacion,
            fuente="OECE",
            fuentes_detalle={
                "oece": {
                    "cargo": integrante.cargo,
                    "participacion": integrante.participacion,
                    "tipo_documento": integrante.tipo_documento,
                    "numero_documento": integrante.numero_documento
                }
            }
        )
    
    async def _consolidar_registro(
        self, 
        datos_sunat: Optional[EmpresaInfo], 
        datos_oece: Optional[EmpresaOSCE]
    ) -> RegistroConsolidado:
        """Consolidar información de registro de ambos sistemas"""
        
        registro = RegistroConsolidado()
        
        if datos_sunat:
            registro.sunat = {
                "ruc": datos_sunat.ruc,
                "razon_social": datos_sunat.razon_social,
                "total_representantes": datos_sunat.total_representantes
            }
            # SUNAT típicamente no tiene estado explícito, asumir ACTIVO si hay datos
            registro.estado_sunat = "ACTIVO"
        
        if datos_oece:
            registro.osce = {
                "ruc": datos_oece.ruc,
                "razon_social": datos_oece.razon_social,
                "estado_registro": datos_oece.estado_registro,
                "total_especialidades": datos_oece.total_especialidades,
                "total_integrantes": datos_oece.total_integrantes,
                "vigencia": datos_oece.vigencia,
                "capacidad_contratacion": datos_oece.capacidad_contratacion
            }
            registro.estado_osce = datos_oece.estado_registro
        
        return registro
    
    def _validar_ruc(self, ruc: str) -> bool:
        """Validar formato del RUC"""
        if not ruc or len(ruc) != 11 or not ruc.isdigit():
            return False
        
        primeros_dos_digitos = ruc[:2]
        if primeros_dos_digitos not in ['10', '20']:
            return False
        
        return True


# Instancia singleton del servicio de consolidación
consolidation_service = ConsolidationService()