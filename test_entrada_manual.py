#!/usr/bin/env python3
"""
Script de prueba para el sistema de entrada manual inteligente
"""

import asyncio
import json
import requests
from datetime import datetime
from typing import Dict, Any

# Configuración
BASE_URL = "http://localhost:8000/api/empresas/smart"
TEST_RUCs = [
    "20100070970",  # RUC que debería existir en SUNAT
    "20123456789",  # RUC que probablemente no existe
    "20987654321",  # RUC para prueba manual
]

class TestEntradaManual:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
        self.resultados = []
    
    def log(self, mensaje: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {mensaje}")
        self.resultados.append(f"[{timestamp}] {mensaje}")
    
    def test_validar_ruc(self, ruc: str) -> Dict[str, Any]:
        """Prueba el endpoint de validación de RUC"""
        self.log(f"🔍 Probando validación de RUC: {ruc}")
        
        try:
            response = self.session.post(
                f"{self.base_url}/validar-ruc",
                json={"ruc": ruc}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("valido"):
                    if data.get("existe"):
                        self.log(f"✅ RUC {ruc} ya existe en BD")
                    elif data.get("datos_automaticos"):
                        self.log(f"🤖 RUC {ruc} - Datos automáticos encontrados: {data['datos_automaticos']['razon_social']}")
                    else:
                        self.log(f"📝 RUC {ruc} - Requiere entrada manual")
                else:
                    self.log(f"❌ RUC {ruc} - Inválido")
                return data
            else:
                self.log(f"❌ Error HTTP {response.status_code} para RUC {ruc}")
                return {"error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            self.log(f"❌ Error validando RUC {ruc}: {e}")
            return {"error": str(e)}
    
    def test_crear_automatica(self, datos_automaticos: Dict[str, Any]) -> Dict[str, Any]:
        """Prueba la creación automática con datos scraped"""
        self.log("🤖 Probando creación automática...")
        
        try:
            response = self.session.post(
                f"{self.base_url}/crear-automatica",
                json=datos_automaticos
            )
            
            if response.status_code == 201:
                data = response.json()
                self.log(f"✅ Empresa creada automáticamente: {data.get('message', 'OK')}")
                return data
            else:
                self.log(f"❌ Error HTTP {response.status_code} en creación automática")
                return {"error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            self.log(f"❌ Error creando empresa automática: {e}")
            return {"error": str(e)}
    
    def test_obtener_plantilla(self, ruc: str) -> Dict[str, Any]:
        """Prueba obtener plantilla para entrada manual"""
        self.log(f"📋 Obteniendo plantilla manual para RUC: {ruc}")
        
        try:
            response = self.session.get(f"{self.base_url}/plantilla-manual/{ruc}")
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ Plantilla obtenida - Datos parciales: {data.get('datos_parciales_encontrados', False)}")
                return data
            else:
                self.log(f"❌ Error HTTP {response.status_code} obteniendo plantilla")
                return {"error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            self.log(f"❌ Error obteniendo plantilla: {e}")
            return {"error": str(e)}
    
    def test_crear_manual(self, empresa_manual: Dict[str, Any]) -> Dict[str, Any]:
        """Prueba la creación manual completa"""
        self.log("📝 Probando creación manual...")
        
        try:
            response = self.session.post(
                f"{self.base_url}/crear-manual",
                json=empresa_manual
            )
            
            if response.status_code == 201:
                data = response.json()
                self.log(f"✅ Empresa creada manualmente: {data.get('message', 'OK')}")
                return data
            else:
                self.log(f"❌ Error HTTP {response.status_code} en creación manual")
                return {"error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            self.log(f"❌ Error creando empresa manual: {e}")
            return {"error": str(e)}
    
    def test_obtener_validadores(self):
        """Prueba obtener validadores de referencia"""
        self.log("📚 Obteniendo validadores de referencia...")
        
        try:
            response = self.session.get(f"{self.base_url}/validadores/referencia")
            
            if response.status_code == 200:
                data = response.json()
                referencia = data.get("referencia", {})
                self.log(f"✅ Validadores obtenidos - Tipos empresa: {len(referencia.get('tipos_empresa', []))}")
                return data
            else:
                self.log(f"❌ Error HTTP {response.status_code} obteniendo validadores")
                return {"error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            self.log(f"❌ Error obteniendo validadores: {e}")
            return {"error": str(e)}
    
    def test_estadisticas(self):
        """Prueba obtener estadísticas de entrada manual"""
        self.log("📊 Obteniendo estadísticas de entrada manual...")
        
        try:
            response = self.session.get(f"{self.base_url}/estadisticas/entrada-manual")
            
            if response.status_code == 200:
                data = response.json()
                stats = data.get("estadisticas", {})
                self.log(f"✅ Estadísticas - Total: {stats.get('total_empresas', 0)}, Manual: {stats.get('entrada_manual', 0)}")
                return data
            else:
                self.log(f"❌ Error HTTP {response.status_code} obteniendo estadísticas")
                return {"error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            self.log(f"❌ Error obteniendo estadísticas: {e}")
            return {"error": str(e)}
    
    def test_crear_dual(self, empresa_dual: Dict[str, Any]) -> Dict[str, Any]:
        """Prueba el endpoint de creación dual inteligente"""
        self.log("🤖 Probando creación dual inteligente...")
        
        try:
            response = self.session.post(
                f"{self.base_url}/crear-dual",
                json=empresa_dual
            )
            
            if response.status_code == 201:
                data = response.json()
                self.log(f"✅ Creación dual exitosa - Modo: {data.get('modo_creacion', 'N/A')}, Calidad: {data.get('calidad_datos', 'N/A')}")
                return data
            else:
                self.log(f"❌ Error HTTP {response.status_code} en creación dual")
                return {"error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            self.log(f"❌ Error en creación dual: {e}")
            return {"error": str(e)}
    
    def test_crear_con_fallback(self, ruc: str) -> Dict[str, Any]:
        """Prueba el endpoint con sistema de fallback inteligente"""
        self.log(f"🔄 Probando sistema de fallback para RUC: {ruc}")
        
        try:
            response = self.session.post(
                f"{self.base_url}/crear-con-fallback",
                json={"ruc": ruc}
            )
            
            if response.status_code == 201:
                data = response.json()
                modo = data.get('modo', 'N/A')
                fallback_activado = data.get('fallback_activado', False)
                self.log(f"✅ Fallback completado - Modo: {modo}, Fallback activado: {fallback_activado}")
                return data
            else:
                self.log(f"❌ Error HTTP {response.status_code} con fallback")
                return {"error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            self.log(f"❌ Error con fallback: {e}")
            return {"error": str(e)}
    
    def test_validar_datos_manuales(self, datos_empresa: Dict[str, Any]) -> Dict[str, Any]:
        """Prueba el validador avanzado de datos manuales"""
        self.log("🔍 Probando validador avanzado de datos manuales...")
        
        try:
            response = self.session.post(
                f"{self.base_url}/validar-datos-manuales",
                json=datos_empresa
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ Validación completada - Calidad: {data.get('puntuacion_calidad', 0)}%, Confianza: {data.get('nivel_confianza', 'N/A')}")
                return data
            else:
                self.log(f"❌ Error HTTP {response.status_code} en validación")
                return {"error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            self.log(f"❌ Error en validación: {e}")
            return {"error": str(e)}
    
    def test_estadisticas_fallback(self):
        """Prueba obtener estadísticas del sistema de fallback"""
        self.log("📊 Obteniendo estadísticas de fallback...")
        
        try:
            response = self.session.get(f"{self.base_url}/fallback/estadisticas")
            
            if response.status_code == 200:
                data = response.json()
                stats = data.get("estadisticas_fallback", {})
                self.log(f"✅ Estadísticas fallback - Activados: {stats.get('fallbacks_activados', 0)}, Tasa éxito: {stats.get('tasa_exitosa_fallback', 0)}%")
                return data
            else:
                self.log(f"❌ Error HTTP {response.status_code} obteniendo estadísticas fallback")
                return {"error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            self.log(f"❌ Error obteniendo estadísticas fallback: {e}")
            return {"error": str(e)}
    
    def crear_empresa_manual_ejemplo(self, ruc: str) -> Dict[str, Any]:
        """Crear un ejemplo de empresa manual para prueba"""
        return {
            "ruc": ruc,
            "razon_social": f"EMPRESA DE PRUEBA MANUAL {ruc[-4:]} S.A.C.",
            "nombre_comercial": f"PRUEBA MANUAL {ruc[-4:]}",
            "tipo_empresa": "SAC",
            "estado": "ACTIVO",
            "departamento": "LIMA",
            "provincia": "LIMA", 
            "distrito": "MIRAFLORES",
            "contacto": {
                "email": f"contacto{ruc[-4:]}@pruebamanual.com",
                "telefono": "01-1234567",
                "celular": "999123456",
                "direccion": f"Av. Prueba {ruc[-4:]} # 123, Miraflores",
                "pagina_web": f"https://pruebamanual{ruc[-4:]}.com"
            },
            "representantes": [
                {
                    "nombre": f"Juan Carlos Prueba {ruc[-4:]}",
                    "cargo": "GERENTE GENERAL",
                    "tipo_documento": "DNI",
                    "numero_documento": f"1234567{ruc[-1]}",
                    "es_principal": True,
                    "participacion": "100%",
                    "fecha_desde": "2020-01-01",
                    "estado": "ACTIVO"
                },
                {
                    "nombre": f"María Elena Validacion {ruc[-4:]}",
                    "cargo": "GERENTE COMERCIAL",
                    "tipo_documento": "DNI", 
                    "numero_documento": f"9876543{ruc[-1]}",
                    "es_principal": False,
                    "estado": "ACTIVO"
                }
            ],
            "categoria_contratista": "EJECUTORA",
            "especialidades": ["EDIFICACIONES", "CARRETERAS"],
            "sector_economico": "CONSTRUCCIÓN",
            "tamaño_empresa": "PEQUEÑA",
            "capital_social": 50000.0,
            "fecha_constitucion": "2020-01-15",
            "observaciones": "Empresa creada para prueba del sistema de entrada manual",
            "fuente_datos": "MANUAL",
            "requiere_verificacion": True,
            "calidad_datos": "ACEPTABLE"
        }
    
    def crear_empresa_dual_ejemplo(self, ruc: str) -> Dict[str, Any]:
        """Crear ejemplo de empresa para creación dual"""
        return {
            "ruc": ruc,
            "intentar_scraping": True,
            "forzar_manual": False,
            "combinar_fuentes": True,
            "datos_manuales": {
                "ruc": ruc,
                "razon_social": f"EMPRESA DUAL {ruc[-4:]} S.A.C.",
                "tipo_empresa": "SAC",
                "estado": "ACTIVO",
                "contacto": {
                    "email": f"contacto{ruc[-4:]}@empresadual.com",
                    "telefono": "01-7654321",
                    "direccion": f"Av. Dual {ruc[-4:]} # 456, Lima"
                },
                "representantes": [
                    {
                        "nombre": f"Ana María Dual {ruc[-4:]}",
                        "cargo": "GERENTE GENERAL",
                        "tipo_documento": "DNI",
                        "numero_documento": f"8765432{ruc[-1]}",
                        "es_principal": True,
                        "estado": "ACTIVO"
                    }
                ],
                "especialidades": ["EDIFICACIONES"],
                "fuente_datos": "MANUAL",
                "requiere_verificacion": False
            },
            "validacion_estricta": False,
            "permitir_datos_parciales": True,
            "creado_por": "test_automatico",
            "motivo_creacion": "Prueba del sistema dual"
        }
    
    def ejecutar_prueba_completa(self):
        """Ejecutar la prueba completa del sistema"""
        self.log("🚀 Iniciando prueba completa del sistema de entrada manual inteligente")
        
        # 1. Probar validadores de referencia
        self.test_obtener_validadores()
        
        # 2. Probar validación de RUCs
        for ruc in TEST_RUCs:
            resultado_validacion = self.test_validar_ruc(ruc)
            
            if "error" in resultado_validacion:
                continue
                
            # Si tiene datos automáticos, probar creación automática
            if resultado_validacion.get("datos_automaticos"):
                datos_auto = resultado_validacion["datos_automaticos"]
                datos_auto["ruc"] = ruc  # Asegurar que tiene RUC
                self.test_crear_automatica(datos_auto)
            
            # Si requiere entrada manual, probar flujo manual
            elif resultado_validacion.get("requiere_entrada_manual"):
                # Obtener plantilla
                plantilla = self.test_obtener_plantilla(ruc)
                
                if "error" not in plantilla:
                    # Crear empresa manual de ejemplo
                    empresa_manual = self.crear_empresa_manual_ejemplo(ruc)
                    
                    # Probar validador avanzado antes de crear
                    self.test_validar_datos_manuales(empresa_manual)
                    
                    # Probar creación manual
                    self.test_crear_manual(empresa_manual)
                    
                    # Probar creación dual con datos manuales
                    empresa_dual = self.crear_empresa_dual_ejemplo(ruc)
                    self.test_crear_dual(empresa_dual)
        
        # 3. Probar sistema de fallback con RUCs adicionales
        rucs_fallback = ["20999999999", "20888888888"]  # RUCs que seguramente no existen
        for ruc in rucs_fallback:
            self.test_crear_con_fallback(ruc)
        
        # 4. Probar estadísticas finales
        self.test_estadisticas()
        self.test_estadisticas_fallback()
        
        self.log("✅ Prueba completa finalizada")
    
    def generar_reporte(self) -> str:
        """Generar reporte de las pruebas"""
        reporte = f"""
=== REPORTE DE PRUEBAS - SISTEMA ENTRADA MANUAL INTELIGENTE ===
Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
URL Base: {self.base_url}

RESULTADOS:
{chr(10).join(self.resultados)}

=== FIN DEL REPORTE ===
"""
        return reporte
    
    def guardar_reporte(self, filename: str = None):
        """Guardar reporte en archivo"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"reporte_entrada_manual_{timestamp}.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(self.generar_reporte())
        
        self.log(f"📄 Reporte guardado en: {filename}")


def main():
    """Función principal"""
    print("=" * 60)
    print("🧪 PRUEBA DEL SISTEMA DE ENTRADA MANUAL INTELIGENTE")
    print("=" * 60)
    
    # Crear tester
    tester = TestEntradaManual()
    
    try:
        # Ejecutar prueba completa
        tester.ejecutar_prueba_completa()
        
        # Mostrar reporte
        print("\n" + "=" * 60)
        print("📄 REPORTE FINAL")
        print("=" * 60)
        print(tester.generar_reporte())
        
        # Guardar reporte
        tester.guardar_reporte()
        
    except KeyboardInterrupt:
        tester.log("⚠️ Prueba interrumpida por el usuario")
    except Exception as e:
        tester.log(f"❌ Error crítico: {e}")
    finally:
        print("\n🏁 Prueba finalizada")


if __name__ == "__main__":
    main()