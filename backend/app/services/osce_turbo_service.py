"""
Servicio OSCE TURBO - Extracción ultra-rápida con HTTP directo y selectores optimizados
"""
import aiohttp
import asyncio
import re
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
from bs4 import BeautifulSoup
from urllib.parse import urlencode

logger = logging.getLogger(__name__)

class OSCETurboService:
    """Servicio OSCE optimizado para velocidad máxima"""
    
    def __init__(self):
        self.session = None
        self.base_url = "https://www.osce.gob.pe"
        
        # Headers para simular browser real pero más ligero
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'es-PE,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        # Selectores CSS ultra-optimizados (más específicos = más rápidos)
        self.selectores_rapidos = {
            'razon_social': [
                'h2.empresa-nombre',
                '.datos-empresa h2',
                '[data-field="razon-social"]',
                'td:contains("RAZÓN SOCIAL") + td',
                '.field-razon-social'
            ],
            'ruc': [
                '[data-field="ruc"]',
                'td:contains("RUC") + td',
                '.field-ruc',
                'span.ruc-number'
            ],
            'telefono': [
                '[data-field="telefono"]',
                'a[href^="tel:"]',
                '.contacto-telefono',
                'td:contains("TELÉFONO") + td',
                '.field-telefono'
            ],
            'email': [
                '[data-field="email"]',
                'a[href^="mailto:"]',
                '.contacto-email',
                'td:contains("EMAIL") + td',
                '.field-email'
            ]
        }
        
        # Patrones regex pre-compilados para máximo rendimiento
        self.regex_patterns = {
            'telefono': re.compile(r'(\d{2,3}[-\s]?\d{6,7})', re.IGNORECASE),
            'email': re.compile(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', re.IGNORECASE),
            'ruc': re.compile(r'(\d{11})', re.IGNORECASE),
            'representante': re.compile(r'([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ\s]{15,60})\s*[-–—|]\s*(\d{8})', re.IGNORECASE)
        }
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Obtener sesión HTTP reutilizable"""
        if not self.session or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=15, connect=5)  # Timeouts agresivos
            connector = aiohttp.TCPConnector(
                limit=10,           # Máximo 10 conexiones
                limit_per_host=5,   # Máximo 5 por host
                keepalive_timeout=60,
                enable_cleanup_closed=True
            )
            
            self.session = aiohttp.ClientSession(
                headers=self.headers,
                timeout=timeout,
                connector=connector
            )
        
        return self.session
    
    async def consultar_turbo(self, ruc: str) -> Dict[str, Any]:
        """
        Consulta TURBO - Extracción en paralelo con múltiples métodos ultra-rápidos
        """
        logger.info(f"🚀 TURBO: Iniciando consulta para RUC {ruc}")
        start_time = datetime.now()
        
        try:
            # Ejecutar métodos en paralelo para máxima velocidad
            resultados = await asyncio.gather(
                self._metodo_api_directa(ruc),
                self._metodo_scraping_ligero(ruc),
                self._metodo_busqueda_rapida(ruc),
                return_exceptions=True
            )
            
            # Consolidar mejor resultado
            resultado_final = self._consolidar_resultados_turbo(resultados, ruc)
            
            tiempo_total = (datetime.now() - start_time).total_seconds()
            logger.info(f"⚡ TURBO completado en {tiempo_total:.2f}s")
            
            resultado_final['tiempo_procesamiento'] = tiempo_total
            return resultado_final
            
        except Exception as e:
            logger.error(f"❌ Error TURBO: {e}")
            return {
                'success': False,
                'error': str(e),
                'fuente': 'OSCE_TURBO_ERROR',
                'tiempo_procesamiento': (datetime.now() - start_time).total_seconds()
            }
    
    async def _metodo_api_directa(self, ruc: str) -> Dict[str, Any]:
        """Método 1: Intentar API directa (más rápido si existe)"""
        try:
            session = await self._get_session()
            
            # URLs de APIs posibles de OSCE
            api_urls = [
                f"{self.base_url}/api/proveedores/{ruc}",
                f"{self.base_url}/ws/proveedor/{ruc}",
                f"{self.base_url}/json/empresa/{ruc}"
            ]
            
            for url in api_urls:
                try:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                        if response.status == 200:
                            data = await response.json()
                            if data and 'ruc' in str(data).lower():
                                logger.info("⚡ API directa exitosa")
                                return {
                                    'success': True,
                                    'data': self._procesar_datos_api(data, ruc),
                                    'metodo': 'api_directa',
                                    'fuente': 'OSCE_API'
                                }
                except:
                    continue
            
            return {'success': False, 'error': 'APIs no disponibles'}
            
        except Exception as e:
            return {'success': False, 'error': f'API directa falló: {e}'}
    
    async def _metodo_scraping_ligero(self, ruc: str) -> Dict[str, Any]:
        """Método 2: Scraping ligero con BeautifulSoup (sin browser)"""
        try:
            session = await self._get_session()
            
            # URL de búsqueda directa OSCE
            search_url = f"{self.base_url}/proveedores/buscar"
            params = {'ruc': ruc, 'tipo': 'ruc'}
            
            async with session.get(f"{search_url}?{urlencode(params)}", timeout=aiohttp.ClientTimeout(total=8)) as response:
                if response.status != 200:
                    return {'success': False, 'error': f'HTTP {response.status}'}
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Extracción ultra-rápida con selectores optimizados
                datos = await self._extraer_datos_rapido(soup, ruc)
                
                if datos['razon_social'] or datos['telefono'] or datos['email']:
                    logger.info("⚡ Scraping ligero exitoso")
                    return {
                        'success': True,
                        'data': datos,
                        'metodo': 'scraping_ligero',
                        'fuente': 'OSCE_SCRAPING_LIGERO'
                    }
                else:
                    return {'success': False, 'error': 'Sin datos extraídos'}
            
        except Exception as e:
            return {'success': False, 'error': f'Scraping ligero falló: {e}'}
    
    async def _metodo_busqueda_rapida(self, ruc: str) -> Dict[str, Any]:
        """Método 3: Búsqueda rápida en directorios públicos"""
        try:
            session = await self._get_session()
            
            # URLs alternativas de búsqueda
            search_urls = [
                f"{self.base_url}/directorio/empresa/{ruc}",
                f"{self.base_url}/registro/proveedor/{ruc}",
                f"{self.base_url}/consulta/empresa/{ruc}"
            ]
            
            for url in search_urls:
                try:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=6)) as response:
                        if response.status == 200:
                            html = await response.text()
                            
                            # Extracción rápida con regex
                            datos = self._extraer_con_regex(html, ruc)
                            
                            if datos['razon_social']:
                                logger.info("⚡ Búsqueda rápida exitosa")
                                return {
                                    'success': True,
                                    'data': datos,
                                    'metodo': 'busqueda_rapida',
                                    'fuente': 'OSCE_BUSQUEDA_RAPIDA'
                                }
                except:
                    continue
            
            return {'success': False, 'error': 'Búsquedas rápidas sin resultados'}
            
        except Exception as e:
            return {'success': False, 'error': f'Búsqueda rápida falló: {e}'}
    
    async def _extraer_datos_rapido(self, soup: BeautifulSoup, ruc: str) -> Dict[str, Any]:
        """Extracción ultra-rápida con selectores CSS optimizados"""
        datos = {
            'ruc': ruc,
            'razon_social': '',
            'telefono': '',
            'email': '',
            'direccion': '',
            'representantes': []
        }
        
        # Extracción paralela de campos
        tareas = [
            self._extraer_campo_rapido(soup, 'razon_social'),
            self._extraer_campo_rapido(soup, 'telefono'),
            self._extraer_campo_rapido(soup, 'email')
        ]
        
        resultados = await asyncio.gather(*tareas, return_exceptions=True)
        
        # Asignar resultados
        for i, campo in enumerate(['razon_social', 'telefono', 'email']):
            if not isinstance(resultados[i], Exception) and resultados[i]:
                datos[campo] = resultados[i]
        
        return datos
    
    async def _extraer_campo_rapido(self, soup: BeautifulSoup, campo: str) -> str:
        """Extraer un campo específico con selectores optimizados"""
        selectores = self.selectores_rapidos.get(campo, [])
        
        for selector in selectores:
            try:
                elemento = soup.select_one(selector)
                if elemento:
                    texto = elemento.get_text(strip=True)
                    if texto and len(texto) > 2:  # Validación básica
                        return texto
            except:
                continue
        
        return ''
    
    def _extraer_con_regex(self, html: str, ruc: str) -> Dict[str, Any]:
        """Extracción ultra-rápida con patrones regex pre-compilados"""
        datos = {
            'ruc': ruc,
            'razon_social': '',
            'telefono': '',
            'email': '',
            'direccion': '',
            'representantes': []
        }
        
        # Búsqueda con regex pre-compilados (ultra-rápido)
        for campo, pattern in self.regex_patterns.items():
            if campo in datos:
                matches = pattern.findall(html)
                if matches:
                    datos[campo] = matches[0] if isinstance(matches[0], str) else matches[0][0]
        
        # Búsqueda específica de razón social con contexto
        razon_patterns = [
            re.compile(rf'{ruc}[^\w]*([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ\s\.]{10,100})', re.IGNORECASE),
            re.compile(r'razón\s*social[:\s]*([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ\s\.]{10,100})', re.IGNORECASE),
            re.compile(r'empresa[:\s]*([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ\s\.]{10,100})', re.IGNORECASE)
        ]
        
        for pattern in razon_patterns:
            match = pattern.search(html)
            if match:
                datos['razon_social'] = match.group(1).strip()
                break
        
        return datos
    
    def _procesar_datos_api(self, data: Dict, ruc: str) -> Dict[str, Any]:
        """Procesar datos de respuesta API"""
        resultado = {
            'ruc': ruc,
            'razon_social': '',
            'telefono': '',
            'email': '',
            'direccion': '',
            'representantes': []
        }
        
        # Mapeo flexible de campos API
        mapeo_campos = {
            'razon_social': ['razonSocial', 'nombre', 'denominacion', 'empresa'],
            'telefono': ['telefono', 'phone', 'tel', 'contacto'],
            'email': ['email', 'correo', 'mail'],
            'direccion': ['direccion', 'domicilio', 'address']
        }
        
        for campo, posibles_keys in mapeo_campos.items():
            for key in posibles_keys:
                if key in data and data[key]:
                    resultado[campo] = str(data[key]).strip()
                    break
        
        return resultado
    
    def _consolidar_resultados_turbo(self, resultados: List[Dict], ruc: str) -> Dict[str, Any]:
        """Consolidar resultados de métodos paralelos TURBO"""
        
        # Filtrar resultados exitosos
        exitosos = [r for r in resultados if isinstance(r, dict) and r.get('success', False)]
        
        if not exitosos:
            return {
                'success': False,
                'error': 'Ningún método TURBO obtuvo resultados',
                'fuente': 'OSCE_TURBO_FALLIDO',
                'metodos_intentados': len(resultados)
            }
        
        # Seleccionar resultado con más datos
        def contar_datos(resultado: Dict) -> int:
            data = resultado.get('data', {})
            count = 0
            if data.get('razon_social'): count += 3  # Peso mayor para razón social
            if data.get('telefono'): count += 2
            if data.get('email'): count += 2
            if data.get('direccion'): count += 1
            return count
        
        mejor_resultado = max(exitosos, key=contar_datos)
        
        # Enriquecer con datos de otros resultados
        data_final = mejor_resultado['data'].copy()
        
        for resultado in exitosos:
            if resultado == mejor_resultado:
                continue
            
            other_data = resultado.get('data', {})
            for campo in ['telefono', 'email', 'direccion']:
                if not data_final.get(campo) and other_data.get(campo):
                    data_final[campo] = other_data[campo]
        
        return {
            'success': True,
            'data': data_final,
            'fuente': f"OSCE_TURBO_{mejor_resultado.get('metodo', 'UNKNOWN').upper()}",
            'metodos_exitosos': len(exitosos),
            'metodos_totales': len(resultados)
        }
    
    async def close(self):
        """Cerrar sesión HTTP"""
        if self.session and not self.session.closed:
            await self.session.close()

# Instancia global
osce_turbo = OSCETurboService()