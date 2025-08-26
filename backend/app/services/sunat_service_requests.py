"""
Servicio SUNAT alternativo usando requests + BeautifulSoup
Compatible con cualquier imagen Lambda sin dependencias de GLIBC
"""
import requests
import logging
import time
import re
from typing import List, Optional, Dict, Any
from bs4 import BeautifulSoup
from urllib.parse import urljoin, parse_qs, urlparse

from app.models.ruc import EmpresaInfo, RepresentanteLegal
from app.utils.validators import validate_ruc

logger = logging.getLogger(__name__)


class SUNATServiceRequests:
    """Servicio SUNAT usando requests + BeautifulSoup - Compatible con cualquier Lambda"""
    
    def __init__(self):
        self.base_url = "https://e-consultaruc.sunat.gob.pe/cl-ti-itmrconsruc/FrameCriterioBusquedaWeb.jsp"
        self.session = requests.Session()
        
        # Headers para simular navegador real
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        # Configuración de timeouts
        self.timeout = 30
        self.retry_attempts = 3
        
        logger.info("🔧 SUNAT Service (requests) inicializado")
        
    def consultar_empresa(self, ruc: str) -> EmpresaInfo:
        """
        Consultar información completa de una empresa por RUC
        Versión síncrona con requests
        """
        # Validar RUC
        if not validate_ruc(ruc):
            raise ValueError(f"RUC inválido: {ruc}")
        
        logger.info(f"🔍 [Requests-SUNAT] Consultando RUC: {ruc}")
        
        # Configuración específica por tipo de RUC
        es_persona_natural = ruc.startswith('10')
        
        for attempt in range(self.retry_attempts):
            try:
                # Obtener información básica
                razon_social = self._obtener_razon_social(ruc, es_persona_natural)
                
                # Obtener domicilio fiscal desde la misma respuesta
                domicilio_fiscal = self._obtener_domicilio_fiscal()
                
                # Obtener representantes legales
                representantes = self._obtener_representantes_legales(ruc, es_persona_natural)
                
                resultado = EmpresaInfo(
                    ruc=ruc,
                    razon_social=razon_social,
                    domicilio_fiscal=domicilio_fiscal,
                    representantes=representantes
                )
                
                logger.info(f"📊 [Requests-SUNAT] Consulta exitosa para RUC {ruc}: {len(representantes)} representantes")
                return resultado
                
            except Exception as e:
                logger.warning(f"⚠️ [Requests-SUNAT] Intento {attempt + 1} falló para RUC {ruc}: {str(e)}")
                if attempt == self.retry_attempts - 1:
                    raise
                time.sleep(1)  # Breve pausa entre reintentos
    
    def _obtener_razon_social(self, ruc: str, es_persona_natural: bool) -> str:
        """Obtener razón social mediante requests"""
        try:
            # Hacer petición inicial
            response = self.session.get(self.base_url, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Buscar formulario y campos necesarios
            form = soup.find('form')
            if not form:
                raise ValueError("No se encontró formulario en la página")
            
            # Preparar datos del formulario
            form_data = {}
            
            # Obtener todos los inputs hidden
            for input_field in soup.find_all('input', type='hidden'):
                name = input_field.get('name')
                value = input_field.get('value', '')
                if name:
                    form_data[name] = value
            
            # Agregar RUC
            form_data['txtRuc'] = ruc
            form_data['btnAceptar'] = 'Aceptar'
            
            # Construir URL del formulario
            form_action = form.get('action', '')
            if form_action:
                submit_url = urljoin(self.base_url, form_action)
            else:
                submit_url = self.base_url
            
            # Enviar formulario
            response = self.session.post(submit_url, data=form_data, timeout=self.timeout)
            response.raise_for_status()
            
            # Guardar respuesta para uso posterior
            self.last_response = response
            
            # Parsear respuesta
            soup = BeautifulSoup(response.content, 'html.parser')
            page_text = soup.get_text()
            
            # Extraer según tipo de persona
            if es_persona_natural:
                return self._extraer_nombre_persona_natural(page_text, ruc)
            else:
                return self._extraer_razon_social_persona_juridica(page_text, ruc)
                
        except Exception as e:
            logger.error(f"❌ [Requests-SUNAT] Error obteniendo razón social: {str(e)}")
            return ""
    
    def _obtener_domicilio_fiscal(self) -> str:
        """Obtener domicilio fiscal de la última respuesta"""
        try:
            if not hasattr(self, 'last_response'):
                return ""
            
            soup = BeautifulSoup(self.last_response.content, 'html.parser')
            page_text = soup.get_text()
            lines = page_text.split('\n')
            
            patterns = ["Domicilio Fiscal:", "DOMICILIO FISCAL:", "Domicilio:", "DOMICILIO:"]
            
            for i, line in enumerate(lines):
                line = line.strip()
                if any(pattern in line for pattern in patterns):
                    logger.info(f"✅ Encontrada línea con domicilio fiscal: {line}")
                    
                    # Si el domicilio está en la misma línea
                    if ":" in line:
                        parts = line.split(":", 1)
                        if len(parts) > 1 and parts[1].strip():
                            domicilio = parts[1].strip()
                            if len(domicilio) > 2 and domicilio != "-":
                                return domicilio
                    
                    # Buscar en líneas siguientes
                    for offset in [1, 2]:
                        if i + offset < len(lines):
                            siguiente_linea = lines[i + offset].strip()
                            if siguiente_linea == "-":
                                return "No registrado"
                            elif siguiente_linea and len(siguiente_linea) > 10:
                                if not any(nav in siguiente_linea.lower() for nav in ['volver', 'imprimir', 'email', 'consulta', 'resultado']):
                                    return siguiente_linea
            
            return ""
            
        except Exception as e:
            logger.error(f"❌ [Requests-SUNAT] Error obteniendo domicilio fiscal: {str(e)}")
            return ""
    
    def _obtener_representantes_legales(self, ruc: str, es_persona_natural: bool) -> List[RepresentanteLegal]:
        """Obtener representantes legales"""
        representantes = []
        
        try:
            # Para personas naturales, crear representante basado en el RUC
            if es_persona_natural:
                if hasattr(self, 'last_response'):
                    soup = BeautifulSoup(self.last_response.content, 'html.parser')
                    nombre = self._extraer_nombre_desde_texto(soup.get_text())
                    
                    if nombre:
                        dni = ruc[2:10] if len(ruc) >= 11 else ""
                        
                        representante = RepresentanteLegal(
                            tipo_doc="DNI",
                            numero_doc=dni,
                            nombre=nombre,
                            cargo="TITULAR",
                            fecha_desde="-"
                        )
                        representantes.append(representante)
                
                return representantes
            
            # Para personas jurídicas, buscar link de representantes
            logger.info("🔍 [Requests-SUNAT] Buscando representantes legales...")
            
            representantes_url = self._buscar_url_representantes()
            
            if not representantes_url:
                logger.warning("⚠️ [Requests-SUNAT] No se encontró URL de representantes")
                return representantes
            
            # Hacer petición para obtener representantes
            response = self.session.get(representantes_url, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            representantes = self._extraer_datos_tablas(soup)
            
            logger.info(f"📊 [Requests-SUNAT] Total representantes extraídos: {len(representantes)}")
            return representantes
            
        except Exception as e:
            logger.error(f"⚠️ [Requests-SUNAT] Error extrayendo representantes: {str(e)}")
            return representantes
    
    def _buscar_url_representantes(self) -> Optional[str]:
        """Buscar URL de representantes legales"""
        if not hasattr(self, 'last_response'):
            return None
        
        try:
            soup = BeautifulSoup(self.last_response.content, 'html.parser')
            
            # Buscar enlaces que contengan "representante"
            links = soup.find_all('a', href=True)
            
            for link in links:
                href = link.get('href', '')
                texto = link.get_text().lower()
                
                if 'representante' in texto or 'legal' in texto:
                    # Construir URL completa
                    full_url = urljoin(self.last_response.url, href)
                    logger.info(f"✅ [Requests-SUNAT] Encontrada URL representantes: {full_url}")
                    return full_url
            
            # Buscar inputs type="button" con value que contenga "representante"
            buttons = soup.find_all('input', type='button')
            
            for button in buttons:
                value = button.get('value', '').lower()
                onclick = button.get('onclick', '')
                
                if 'representante' in value and onclick:
                    # Extraer URL del onclick si es posible
                    url_match = re.search(r"'([^']+)'", onclick)
                    if url_match:
                        url = url_match.group(1)
                        full_url = urljoin(self.last_response.url, url)
                        logger.info(f"✅ [Requests-SUNAT] Encontrada URL representantes desde botón: {full_url}")
                        return full_url
            
            return None
            
        except Exception as e:
            logger.error(f"❌ [Requests-SUNAT] Error buscando URL representantes: {str(e)}")
            return None
    
    def _extraer_datos_tablas(self, soup: BeautifulSoup) -> List[RepresentanteLegal]:
        """Extraer datos de tablas de representantes"""
        representantes = []
        
        try:
            tables = soup.find_all('table')
            
            for table in tables:
                rows = table.find_all("tr")
                
                if len(rows) == 0:
                    continue
                
                # Verificar estructura de tabla
                primera_fila_celdas = rows[0].find_all(["td", "th"])
                if len(primera_fila_celdas) < 3:
                    continue
                
                # Procesar filas
                for row in rows:
                    celdas = row.find_all("td")
                    if not celdas or len(celdas) < 3:
                        continue
                    
                    textos = [celda.get_text().strip() for celda in celdas]
                    representante = self._procesar_fila_representante(textos)
                    if representante:
                        representantes.append(representante)
            
            return representantes
            
        except Exception as e:
            logger.error(f"❌ [Requests-SUNAT] Error extrayendo datos de tablas: {str(e)}")
            return representantes
    
    def _procesar_fila_representante(self, textos: List[str]) -> Optional[RepresentanteLegal]:
        """Procesar fila de representante con validaciones"""
        # Filtrar filas vacías
        if not any(texto and texto != "-" and len(texto) > 2 for texto in textos):
            return None
        
        # Determinar formato
        persona_data = {}
        
        if len(textos) >= 5:
            persona_data = {
                "tipo_doc": textos[0],
                "numero_doc": textos[1],
                "nombre": textos[2],
                "cargo": textos[3],
                "fecha_desde": textos[4]
            }
        elif len(textos) == 4:
            persona_data = {
                "tipo_doc": "DNI",
                "numero_doc": textos[0],
                "nombre": textos[1],
                "cargo": textos[2],
                "fecha_desde": textos[3]
            }
        elif len(textos) == 3:
            persona_data = {
                "tipo_doc": "-",
                "numero_doc": "-",
                "nombre": textos[0],
                "cargo": textos[1],
                "fecha_desde": textos[2]
            }
        else:
            return None
        
        # Validar nombre
        nombre = persona_data.get("nombre", "")
        if not self._es_nombre_valido(nombre):
            return None
        
        try:
            return RepresentanteLegal(**persona_data)
        except Exception as e:
            logger.warning(f"⚠️ [Requests-SUNAT] Error creando representante: {str(e)}")
            return None
    
    def _es_nombre_valido(self, nombre: str) -> bool:
        """Validar nombre de representante"""
        if not nombre or len(nombre) < 3:
            return False
        
        headers_invalidos = [
            "NOMBRE", "APELLIDOS", "TIPO", "DOC", "CARGO", "FECHA",
            "DOCUMENTO", "REPRESENTANTE", "LEGAL", "DESDE"
        ]
        
        if nombre.upper() in headers_invalidos:
            return False
        
        if all(char == "-" for char in nombre):
            return False
        
        return True
    
    def _extraer_nombre_persona_natural(self, page_text: str, ruc: str) -> str:
        """Extraer nombre de persona natural"""
        try:
            lines = page_text.split('\n')
            
            for line in lines:
                line = line.strip()
                if line.startswith("DNI ") and " - " in line:
                    parts = line.split(" - ", 1)
                    if len(parts) > 1:
                        nombre_completo = parts[1].strip()
                        if len(nombre_completo) > 3:
                            return nombre_completo
            return ""
        except Exception:
            return ""
    
    def _extraer_razon_social_persona_juridica(self, page_text: str, ruc: str) -> str:
        """Extraer razón social de persona jurídica"""
        try:
            lines = page_text.split('\n')
            
            for line in lines:
                line = line.strip()
                if ruc in line and " - " in line:
                    parts = line.split(" - ", 1)
                    if len(parts) > 1:
                        razon_social = parts[1].strip()
                        if len(razon_social) > 5:
                            return razon_social
            return ""
        except Exception:
            return ""
    
    def _extraer_nombre_desde_texto(self, page_text: str) -> str:
        """Extraer nombre desde texto de página"""
        lines = page_text.split('\n')
        for line in lines:
            line = line.strip()
            if "DNI " in line and " - " in line:
                parts = line.split(" - ", 1)
                if len(parts) > 1:
                    return parts[1].strip()
        return ""


# Instancia singleton del servicio requests
sunat_service_requests = SUNATServiceRequests()