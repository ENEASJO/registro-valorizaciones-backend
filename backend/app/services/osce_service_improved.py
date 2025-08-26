"""
Servicio OSCE mejorado - Mejores extracciones de contacto, email y representantes
"""
import logging
import re
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

class OSCEServiceImproved:
    """Mejoras específicas para extracción de datos OSCE"""
    
    def __init__(self):
        # Patrones mejorados para identificar representantes con DNI y cargo
        self.patrones_representante = {
            # DNI seguido de nombre y cargo
            'dni_nombre_cargo': r'(\d{8})\s+([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ\s]{15,60})\s+([A-ZÁÉÍÓÚÑ\s]{5,30})',
            
            # Nombre seguido de DNI y cargo
            'nombre_dni_cargo': r'([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ\s]{15,60})\s+(\d{8})\s+([A-ZÁÉÍÓÚÑ\s]{5,30})',
            
            # Patrón con separadores
            'separado': r'([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ\s]{15,60})\s*[-–—|]\s*(\d{8})\s*[-–—|]\s*([A-ZÁÉÍÓÚÑ\s]{5,30})',
            
            # En líneas consecutivas
            'multilinea': r'([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ\s]{15,60})\n\s*(\d{8})\n\s*([A-ZÁÉÍÓÚÑ\s]{5,30})'
        }
        
        # Cargos válidos específicos para consolidación
        self.cargos_validos = {
            'GERENTE GENERAL', 'PRESIDENTE', 'PRESIDENTA', 'DIRECTOR', 'DIRECTORA',
            'VICEPRESIDENTE', 'VICEPRESIDENTA', 'REPRESENTANTE LEGAL',
            'SECRETARIO', 'SECRETARIA', 'TESORERO', 'TESORERA',
            'ADMINISTRADOR', 'ADMINISTRADORA', 'SOCIO', 'SOCIA',
            'APODERADO', 'APODERADA', 'VOCAL', 'CONSEJERO', 'CONSEJERA'
        }
        
        # Patrones de contacto mejorados
        self.patrones_contacto = {
            'telefono': [
                r'teléfono[:\s]*(\d{2,3}[-\s]?\d{6,7})',
                r'telf[:\s]*(\d{2,3}[-\s]?\d{6,7})',
                r'tel[:\s]*(\d{2,3}[-\s]?\d{6,7})',
                r'fono[:\s]*(\d{2,3}[-\s]?\d{6,7})',
                r'contacto[:\s]*(\d{2,3}[-\s]?\d{6,7})'
            ],
            'email': [
                r'email[:\s]*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
                r'correo[:\s]*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
                r'e-mail[:\s]*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
                r'mail[:\s]*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
            ]
        }

    async def extraer_contacto_mejorado(self, page, texto_pagina: str) -> Dict[str, str]:
        """Extrae información de contacto con patrones mejorados"""
        logger.info("🔍 Extrayendo contacto con método mejorado")
        
        contacto = {
            "telefono": "",
            "email": "",
            "direccion": "",
            "ciudad": "",
            "departamento": ""
        }
        
        try:
            # 1. Buscar teléfono con múltiples patrones
            telefono = await self._extraer_telefono_mejorado(texto_pagina)
            if telefono:
                contacto["telefono"] = telefono
                logger.info(f"📞 Teléfono encontrado: {telefono}")
            
            # 2. Buscar email con múltiples patrones
            email = await self._extraer_email_mejorado(texto_pagina)
            if email:
                contacto["email"] = email
                logger.info(f"📧 Email encontrado: {email}")
            
            # 3. Buscar dirección
            direccion = await self._extraer_direccion_mejorada(texto_pagina)
            if direccion:
                contacto["direccion"] = direccion
                logger.info(f"🏠 Dirección encontrada: {direccion}")
            
            # 4. Buscar en elementos específicos de la página
            await self._extraer_contacto_desde_elementos(page, contacto)
            
        except Exception as e:
            logger.error(f"Error extrayendo contacto mejorado: {e}")
        
        return contacto
    
    async def _extraer_telefono_mejorado(self, texto: str) -> str:
        """Extrae teléfono con patrones mejorados"""
        for patron in self.patrones_contacto['telefono']:
            matches = re.finditer(patron, texto, re.IGNORECASE)
            for match in matches:
                telefono = match.group(1).strip()
                # Limpiar formato
                telefono_limpio = re.sub(r'[^\d]', '', telefono)
                if self._validar_telefono_peru(telefono_limpio):
                    # Formatear bonito: 618-8000 o 987654321
                    if len(telefono_limpio) == 7:
                        return f"{telefono_limpio[:3]}-{telefono_limpio[3:]}"
                    elif len(telefono_limpio) == 9:
                        return telefono_limpio
                    else:
                        return telefono_limpio
        return ""
    
    async def _extraer_email_mejorado(self, texto: str) -> str:
        """Extrae email con patrones mejorados"""
        for patron in self.patrones_contacto['email']:
            matches = re.finditer(patron, texto, re.IGNORECASE)
            for match in matches:
                email = match.group(1).strip().lower()
                if self._validar_email_formato(email):
                    return email
        return ""
    
    async def _extraer_direccion_mejorada(self, texto: str) -> str:
        """Extrae dirección con patrones específicos"""
        patrones_direccion = [
            r'dirección[:\s]*([^,\n]{20,100})',
            r'ubicación[:\s]*([^,\n]{20,100})',
            r'domicilio[:\s]*([^,\n]{20,100})',
            r'sede[:\s]*([^,\n]{20,100})'
        ]
        
        for patron in patrones_direccion:
            matches = re.finditer(patron, texto, re.IGNORECASE)
            for match in matches:
                direccion = match.group(1).strip()
                if len(direccion) > 15:
                    return direccion[:100]  # Limitar longitud
        return ""
    
    async def _extraer_contacto_desde_elementos(self, page, contacto: Dict[str, str]):
        """Busca información de contacto en elementos específicos de la página"""
        try:
            # Buscar en inputs y spans que puedan contener información de contacto
            elementos = await page.query_selector_all('input, span, div')
            
            for elemento in elementos:
                try:
                    valor = await elemento.get_attribute('value') or await elemento.inner_text()
                    if valor:
                        valor = valor.strip()
                        
                        # Verificar si es teléfono
                        if not contacto["telefono"] and self._es_telefono_valido(valor):
                            contacto["telefono"] = valor
                        
                        # Verificar si es email
                        if not contacto["email"] and '@' in valor and self._validar_email_formato(valor):
                            contacto["email"] = valor.lower()
                
                except Exception:
                    continue
                    
        except Exception as e:
            logger.debug(f"Error buscando en elementos: {e}")

    async def extraer_representantes_consolidados(self, page, texto_pagina: str, razon_social: str = "") -> List[Dict[str, str]]:
        """Extrae representantes con DNI y cargos, eliminando duplicados"""
        logger.info("🔍 Extrayendo representantes con método consolidado")
        
        representantes_raw = []
        representantes_consolidados = []
        
        try:
            # 1. Extraer con patrones específicos
            representantes_raw.extend(await self._extraer_con_patrones_dni(texto_pagina))
            
            # 2. Extraer desde tablas
            representantes_raw.extend(await self._extraer_desde_tablas_representantes(page))
            
            # 3. Extraer desde secciones específicas
            representantes_raw.extend(await self._extraer_desde_secciones_representantes(page))
            
            # 4. Consolidar y eliminar duplicados
            representantes_consolidados = self._consolidar_representantes(representantes_raw, razon_social)
            
            logger.info(f"✅ Representantes consolidados: {len(representantes_consolidados)}")
            
        except Exception as e:
            logger.error(f"Error extrayendo representantes consolidados: {e}")
        
        return representantes_consolidados
    
    async def _extraer_con_patrones_dni(self, texto: str) -> List[Dict[str, str]]:
        """Extrae representantes usando patrones específicos de DNI"""
        representantes = []
        
        for nombre_patron, patron in self.patrones_representante.items():
            matches = re.finditer(patron, texto, re.MULTILINE | re.IGNORECASE)
            
            for match in matches:
                try:
                    grupos = match.groups()
                    
                    if nombre_patron == 'dni_nombre_cargo':
                        dni, nombre, cargo = grupos
                    elif nombre_patron == 'nombre_dni_cargo':
                        nombre, dni, cargo = grupos
                    elif nombre_patron in ['separado', 'multilinea']:
                        nombre, dni, cargo = grupos
                    else:
                        continue
                    
                    # Limpiar y validar datos extraídos
                    nombre_limpio = self._limpiar_nombre_persona(nombre)
                    if self._validar_dni(dni) and self._validar_nombre_persona(nombre_limpio):
                        cargo_limpio = self._normalizar_cargo(cargo)
                        
                        representante = {
                            "nombre": nombre_limpio.strip().upper(),
                            "dni": dni.strip(),
                            "cargo": cargo_limpio,
                            "tipo_documento": "DNI"
                        }
                        
                        representantes.append(representante)
                        logger.debug(f"Representante extraído ({nombre_patron}): {nombre_limpio} - DNI: {dni} - Cargo: {cargo_limpio}")
                
                except Exception as e:
                    logger.debug(f"Error procesando match de {nombre_patron}: {e}")
                    continue
        
        return representantes
    
    async def _extraer_desde_tablas_representantes(self, page) -> List[Dict[str, str]]:
        """Extrae representantes desde tablas en la página"""
        representantes = []
        
        try:
            tablas = await page.query_selector_all('table')
            
            for tabla in tablas:
                # Verificar si la tabla contiene información de representantes
                tabla_texto = await tabla.inner_text()
                if any(keyword in tabla_texto.lower() for keyword in ['representante', 'socio', 'director', 'gerente', 'dni']):
                    
                    filas = await tabla.query_selector_all('tr')
                    headers = []
                    
                    # Extraer headers
                    if filas:
                        primera_fila = filas[0]
                        celdas_header = await primera_fila.query_selector_all('th, td')
                        headers = [await celda.inner_text() for celda in celdas_header]
                    
                    # Identificar columnas
                    col_nombre = self._encontrar_columna(headers, ['nombre', 'apellidos', 'integrante'])
                    col_dni = self._encontrar_columna(headers, ['dni', 'documento', 'número'])
                    col_cargo = self._encontrar_columna(headers, ['cargo', 'puesto', 'función'])
                    
                    # Extraer datos
                    for fila in filas[1:]:
                        celdas = await fila.query_selector_all('td')
                        if len(celdas) >= max(col_nombre or 0, col_dni or 0, col_cargo or 0):
                            
                            nombre = await celdas[col_nombre].inner_text() if col_nombre is not None and col_nombre < len(celdas) else ""
                            dni = await celdas[col_dni].inner_text() if col_dni is not None and col_dni < len(celdas) else ""
                            cargo = await celdas[col_cargo].inner_text() if col_cargo is not None and col_cargo < len(celdas) else "SOCIO"
                            
                            nombre_limpio = self._limpiar_nombre_persona(nombre)
                            if self._validar_dni(dni) and self._validar_nombre_persona(nombre_limpio):
                                representante = {
                                    "nombre": nombre_limpio.strip().upper(),
                                    "dni": dni.strip(),
                                    "cargo": self._normalizar_cargo(cargo),
                                    "tipo_documento": "DNI"
                                }
                                representantes.append(representante)
                                logger.debug(f"Representante extraído de tabla: {nombre_limpio} - DNI: {dni}")
        
        except Exception as e:
            logger.debug(f"Error extrayendo desde tablas: {e}")
        
        return representantes
    
    async def _extraer_desde_secciones_representantes(self, page) -> List[Dict[str, str]]:
        """Extrae representantes navegando a secciones específicas"""
        representantes = []
        
        secciones = ['representantes', 'socios', 'directores', 'accionistas', 'gerencia']
        
        try:
            for seccion in secciones:
                elementos = await page.query_selector_all(f'a, button, span')
                
                for elemento in elementos:
                    texto = await elemento.inner_text()
                    if seccion.lower() in texto.lower():
                        try:
                            await elemento.click()
                            await page.wait_for_timeout(2000)
                            
                            # Extraer representantes de la nueva página
                            contenido = await page.inner_text('body')
                            representantes_seccion = await self._extraer_con_patrones_dni(contenido)
                            representantes.extend(representantes_seccion)
                            
                            # Volver atrás
                            await page.go_back()
                            await page.wait_for_timeout(1000)
                            
                        except Exception:
                            continue
                        break
        
        except Exception as e:
            logger.debug(f"Error navegando secciones: {e}")
        
        return representantes
    
    def _consolidar_representantes(self, representantes_raw: List[Dict[str, str]], razon_social: str) -> List[Dict[str, str]]:
        """Consolida representantes eliminando duplicados y filtrando nombres de empresa"""
        logger.info(f"📋 Consolidando {len(representantes_raw)} representantes raw")
        
        # Usar DNI como clave única para eliminar duplicados
        representantes_por_dni: Dict[str, Dict[str, str]] = {}
        
        for rep in representantes_raw:
            dni = rep.get('dni', '').strip()
            nombre = rep.get('nombre', '').strip()
            
            if not dni or not nombre:
                continue
            
            # Filtrar nombres que sean claramente de empresa (no personas)
            if self._es_nombre_empresa(nombre, razon_social):
                logger.debug(f"❌ Filtrando nombre de empresa: {nombre}")
                continue
            
            if dni in representantes_por_dni:
                # Si ya existe, mantener el cargo más específico
                cargo_actual = representantes_por_dni[dni].get('cargo', '')
                cargo_nuevo = rep.get('cargo', '')
                
                if self._es_cargo_mas_especifico(cargo_nuevo, cargo_actual):
                    representantes_por_dni[dni]['cargo'] = cargo_nuevo
            else:
                representantes_por_dni[dni] = rep.copy()
        
        # Convertir a lista y ordenar
        consolidados = list(representantes_por_dni.values())
        consolidados.sort(key=lambda x: (x.get('cargo', ''), x.get('nombre', '')))
        
        logger.info(f"✅ Representantes consolidados finales: {len(consolidados)}")
        
        return consolidados[:10]  # Limitar a 10 representantes principales
    
    def _validar_dni(self, dni: str) -> bool:
        """Valida formato de DNI peruano"""
        if not dni:
            return False
        dni_clean = re.sub(r'[^\d]', '', dni)
        return len(dni_clean) == 8 and dni_clean.isdigit()
    
    def _validar_nombre_persona(self, nombre: str) -> bool:
        """Valida que el nombre sea de una persona real"""
        if not nombre or len(nombre) < 10:
            return False
        
        nombre_upper = nombre.upper().strip()
        
        # Filtrar headers de tabla y texto basura
        headers_invalidos = [
            'NOMBRE', 'APELLIDOS', 'DNI', 'CARGO', 'DOCUMENTO', 'INTEGRANTE',
            'TIPO DE', 'REPRESENTANTES', 'OTROS ACCIONISTAS', 'VER TODOS',
            'ÓRGANOS DE ADMINISTRACIÓN', 'ADMINISTRACIÓN'
        ]
        
        # Verificar si el nombre contiene headers inválidos
        for header in headers_invalidos:
            if header in nombre_upper:
                return False
        
        # Debe tener al menos 2 palabras de nombre real
        palabras = [p for p in nombre.strip().split() if len(p) > 2]
        if len(palabras) < 2:
            return False
            
        # No debe contener solo mayúsculas sin espacios (probable header)
        if nombre.isupper() and ' ' not in nombre.strip():
            return False
        
        return True
    
    def _limpiar_nombre_persona(self, nombre: str) -> str:
        """Limpia el nombre de persona removiendo headers y texto basura"""
        if not nombre:
            return ""
        
        # Remover texto basura común
        texto_basura = [
            'TIPO DE DOCUMENTO', 'DOCUMENTO', 'REPRESENTANTES', 
            'OTROS ACCIONISTAS', 'VER TODOS', 'ÓRGANOS DE ADMINISTRACIÓN',
            'ADMINISTRACIÓN', '\n', '\t'
        ]
        
        nombre_limpio = nombre
        for basura in texto_basura:
            nombre_limpio = nombre_limpio.replace(basura, ' ')
        
        # Limpiar espacios múltiples
        nombre_limpio = ' '.join(nombre_limpio.split())
        
        # Solo mantener letras, espacios y acentos
        import re
        nombre_limpio = re.sub(r'[^A-ZÁÉÍÓÚÑ\s]', '', nombre_limpio.upper())
        
        return nombre_limpio.strip()
    
    def _normalizar_cargo(self, cargo: str) -> str:
        """Normaliza y valida cargo"""
        if not cargo:
            return "SOCIO"
        
        cargo_upper = cargo.strip().upper()
        
        # Buscar cargo específico
        for cargo_valido in self.cargos_validos:
            if cargo_valido in cargo_upper:
                return cargo_valido
        
        return cargo_upper[:30]  # Limitar longitud
    
    def _es_nombre_empresa(self, nombre: str, razon_social: str) -> bool:
        """Verifica si el nombre corresponde a una empresa en lugar de persona"""
        nombre_upper = nombre.upper()
        
        # Palabras clave de empresa
        palabras_empresa = ['S.A.', 'SAC', 'S.R.L.', 'EIRL', 'CORPORACION', 'EMPRESA', 'COMPAÑIA']
        if any(palabra in nombre_upper for palabra in palabras_empresa):
            return True
        
        # Verificar similitud con razón social
        if razon_social and len(razon_social) > 10:
            if razon_social.upper() in nombre_upper or nombre_upper in razon_social.upper():
                return True
        
        return False
    
    def _es_cargo_mas_especifico(self, cargo_nuevo: str, cargo_actual: str) -> bool:
        """Determina si un cargo es más específico que otro"""
        jerarquia_cargos = [
            'PRESIDENTE', 'PRESIDENTA', 'GERENTE GENERAL',
            'VICEPRESIDENTE', 'VICEPRESIDENTA', 'DIRECTOR', 'DIRECTORA',
            'REPRESENTANTE LEGAL', 'ADMINISTRADOR', 'ADMINISTRADORA',
            'SECRETARIO', 'SECRETARIA', 'TESORERO', 'TESORERA',
            'SOCIO', 'SOCIA'
        ]
        
        try:
            indice_nuevo = jerarquia_cargos.index(cargo_nuevo.upper())
            indice_actual = jerarquia_cargos.index(cargo_actual.upper())
            return indice_nuevo < indice_actual
        except ValueError:
            return len(cargo_nuevo) > len(cargo_actual)
    
    def _encontrar_columna(self, headers: List[str], palabras_clave: List[str]) -> Optional[int]:
        """Encuentra el índice de columna que contiene alguna palabra clave"""
        for i, header in enumerate(headers):
            header_lower = header.lower()
            for palabra in palabras_clave:
                if palabra in header_lower:
                    return i
        return None
    
    def _validar_telefono_peru(self, telefono: str) -> bool:
        """Valida formato de teléfono peruano"""
        telefono_clean = re.sub(r'[^\d]', '', telefono)
        
        # Móvil (9 dígitos empezando por 9)
        if len(telefono_clean) == 9 and telefono_clean.startswith('9'):
            return True
        
        # Fijo Lima (7-8 dígitos)
        if len(telefono_clean) in [7, 8]:
            return True
        
        return False
    
    def _validar_email_formato(self, email: str) -> bool:
        """Valida formato básico de email"""
        patron = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(patron, email) is not None
    
    def _es_telefono_valido(self, texto: str) -> bool:
        """Verifica si un texto es un teléfono válido"""
        # Limpiar y verificar si contiene solo números y algunos separadores
        limpio = re.sub(r'[^\d\-\s]', '', texto)
        solo_numeros = re.sub(r'[^\d]', '', limpio)
        
        return len(solo_numeros) >= 7 and len(solo_numeros) <= 10


# Instancia global del servicio mejorado
osce_improved = OSCEServiceImproved()