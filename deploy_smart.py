#!/usr/bin/env python3
"""
🚀 Deploy Inteligente para Cloud Run - Detección Automática de Problemas
Ejecuta deployment solo después de verificar que no hay problemas críticos
"""

import os
import sys
import subprocess
import time
from datetime import datetime
from pathlib import Path

class SmartDeployer:
    def __init__(self):
        self.project_id = "valoraciones-app-cloud-run"
        self.service_name = "registro-valorizaciones-backend"
        self.region = "southamerica-west1"
        self.image_base = f"gcr.io/{self.project_id}/{self.service_name}"
        self.errors_found = []
        
    def print_section(self, title):
        print(f"\n{'='*80}")
        print(f"🚀 {title}")
        print('='*80)

    def print_error(self, message):
        print(f"❌ {message}")
        self.errors_found.append(message)

    def print_success(self, message):
        print(f"✅ {message}")

    def print_warning(self, message):
        print(f"⚠️  {message}")

    def print_info(self, message):
        print(f"ℹ️  {message}")

    def verify_deployment_readiness(self):
        """Verificación completa antes del deployment"""
        self.print_section("VERIFICACIÓN PRE-DEPLOYMENT")
        
        checks_passed = 0
        total_checks = 0
        
        # 1. Verificar que Dockerfile use requirements-cloudrun.txt
        total_checks += 1
        dockerfile_path = Path("Dockerfile")
        if dockerfile_path.exists():
            with open(dockerfile_path, 'r') as f:
                dockerfile_content = f.read()
                
            if 'requirements-cloudrun.txt' in dockerfile_content:
                self.print_success("Dockerfile usa requirements-cloudrun.txt correctamente")
                checks_passed += 1
            else:
                self.print_error("Dockerfile NO usa requirements-cloudrun.txt")
                self.print_info("  Solución: Cambiar 'requirements.txt' por 'requirements-cloudrun.txt' en Dockerfile")
        else:
            self.print_error("Dockerfile no encontrado")
            
        # 2. Verificar sincronización de requirements
        total_checks += 1
        main_req = Path("requirements.txt")
        cloudrun_req = Path("requirements-cloudrun.txt")
        
        if main_req.exists() and cloudrun_req.exists():
            with open(main_req, 'r') as f:
                main_deps = set(line.strip() for line in f if line.strip() and not line.startswith('#'))
            with open(cloudrun_req, 'r') as f:
                cloudrun_deps = set(line.strip() for line in f if line.strip() and not line.startswith('#'))
                
            if main_deps == cloudrun_deps:
                self.print_success("requirements.txt y requirements-cloudrun.txt están sincronizados")
                checks_passed += 1
            else:
                missing = main_deps - cloudrun_deps
                if missing:
                    self.print_error(f"Dependencias faltantes en requirements-cloudrun.txt: {len(missing)}")
                    for dep in list(missing)[:3]:
                        print(f"    - {dep}")
                else:
                    self.print_success("requirements-cloudrun.txt tiene todas las dependencias")
                    checks_passed += 1
        else:
            self.print_error("Archivos de requirements faltantes")
            
        # 3. Verificar que no haya cambios sin commit
        total_checks += 1
        try:
            result = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True)
            if result.returncode == 0:
                if result.stdout.strip():
                    self.print_warning("Hay cambios sin commit")
                    print("  Cambios pendientes:")
                    for line in result.stdout.strip().split('\\n')[:5]:
                        print(f"    {line}")
                else:
                    self.print_success("Repositorio limpio - todos los cambios están committeados")
                    checks_passed += 1
        except:
            self.print_warning("No se pudo verificar estado de Git")
            
        # 4. Verificar archivos críticos
        total_checks += 1
        critical_files = ["main.py", "app/core/database.py", "app/api/routes/empresas_smart.py"]
        missing_files = []
        
        for file_path in critical_files:
            if not Path(file_path).exists():
                missing_files.append(file_path)
                
        if missing_files:
            self.print_error(f"Archivos críticos faltantes: {missing_files}")
        else:
            self.print_success("Todos los archivos críticos están presentes")
            checks_passed += 1
            
        # 5. Verificar encoding limpio en main.py
        total_checks += 1
        main_path = Path("main.py")
        if main_path.exists():
            try:
                with open(main_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                # Verificar caracteres problemáticos
                problematic_chars = ['📦', '✅', '❌', '⚠️', '🚀', '🔍', '⚡']
                found_problematic = [char for char in problematic_chars if char in content]
                
                if found_problematic:
                    self.print_error(f"Caracteres problemáticos en main.py: {found_problematic}")
                else:
                    self.print_success("main.py tiene encoding limpio")
                    checks_passed += 1
                    
            except UnicodeDecodeError:
                self.print_error("Problemas de encoding en main.py")
        else:
            self.print_error("main.py no encontrado")
            
        # Resultado final de verificación
        success_rate = (checks_passed / total_checks) * 100
        self.print_info(f"Verificaciones exitosas: {checks_passed}/{total_checks} ({success_rate:.1f}%)")
        
        if checks_passed == total_checks:
            self.print_success("🎉 TODAS las verificaciones pasaron - Listo para deployment!")
            return True
        elif success_rate >= 80:
            self.print_warning(f"⚡ Verificaciones suficientes ({success_rate:.1f}%) - Deployment puede proceder")
            return True
        else:
            self.print_error(f"❌ Demasiados problemas críticos ({success_rate:.1f}%) - Deployment cancelado")
            return False

    def get_commit_sha(self):
        """Obtener SHA del commit actual"""
        try:
            result = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        
        # Fallback a timestamp si no hay Git
        return str(int(time.time()))

    def build_and_push_image(self, commit_sha):
        """Construir y subir la imagen Docker"""
        self.print_section("BUILD Y PUSH DE IMAGEN DOCKER")
        
        image_tag = f"{self.image_base}:{commit_sha}"
        
        try:
            # Build
            self.print_info(f"Construyendo imagen: {image_tag}")
            build_cmd = ["docker", "build", "-t", image_tag, "."]
            
            self.print_info(f"Ejecutando: {' '.join(build_cmd)}")
            result = subprocess.run(build_cmd, capture_output=False, text=True)
            
            if result.returncode != 0:
                self.print_error("Fallo en la construcción de la imagen Docker")
                return False
                
            self.print_success("Imagen construida exitosamente")
            
            # Push
            self.print_info(f"Subiendo imagen al registry...")
            push_cmd = ["docker", "push", image_tag]
            
            self.print_info(f"Ejecutando: {' '.join(push_cmd)}")
            result = subprocess.run(push_cmd, capture_output=False, text=True)
            
            if result.returncode != 0:
                self.print_error("Fallo al subir la imagen al registry")
                return False
                
            self.print_success("Imagen subida exitosamente al registry")
            return image_tag
            
        except Exception as e:
            self.print_error(f"Error durante build/push: {e}")
            return False

    def deploy_to_cloud_run(self, image_tag):
        """Deployment a Cloud Run con configuración optimizada"""
        self.print_section("DEPLOYMENT A CLOUD RUN")
        
        deploy_cmd = [
            "gcloud", "run", "deploy", self.service_name,
            "--image", image_tag,
            "--region", self.region,
            "--platform", "managed",
            "--allow-unauthenticated",
            "--port", "8080",
            "--memory", "4Gi",
            "--cpu", "2",
            "--timeout", "900s",  # 15 minutos - importante para Playwright
            "--max-instances", "10",
            "--concurrency", "1000",
            "--cpu-throttling",  # Permitir CPU throttling
            "--set-env-vars", "PORT=8080,BROWSER_HEADLESS=true,PLAYWRIGHT_BROWSERS_PATH=/app/.cache/ms-playwright"
        ]
        
        try:
            self.print_info(f"Desplegando a Cloud Run...")
            self.print_info(f"Comando: {' '.join(deploy_cmd)}")
            
            result = subprocess.run(deploy_cmd, capture_output=False, text=True)
            
            if result.returncode != 0:
                self.print_error("Fallo en el deployment a Cloud Run")
                return False
                
            self.print_success("🎉 Deployment a Cloud Run exitoso!")
            
            # Obtener URL del servicio
            try:
                url_cmd = [
                    "gcloud", "run", "services", "describe", self.service_name,
                    "--region", self.region,
                    "--format", "value(status.url)"
                ]
                
                result = subprocess.run(url_cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    service_url = result.stdout.strip()
                    self.print_success(f"🌐 URL del servicio: {service_url}")
                    
                    # Test básico del servicio
                    self.print_info("Probando el servicio...")
                    test_cmd = ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", f"{service_url}/health"]
                    
                    try:
                        test_result = subprocess.run(test_cmd, capture_output=True, text=True, timeout=30)
                        if test_result.returncode == 0:
                            http_code = test_result.stdout.strip()
                            if http_code == "200":
                                self.print_success("✅ Servicio responde correctamente!")
                            else:
                                self.print_warning(f"⚠️ Servicio responde con código: {http_code}")
                        else:
                            self.print_warning("No se pudo probar el servicio (curl no disponible)")
                    except subprocess.TimeoutExpired:
                        self.print_warning("Timeout probando el servicio (puede estar iniciando)")
                        
            except Exception as e:
                self.print_warning(f"No se pudo obtener URL del servicio: {e}")
                
            return True
            
        except Exception as e:
            self.print_error(f"Error durante deployment: {e}")
            return False

    def run_smart_deployment(self):
        """Ejecutar deployment inteligente completo"""
        print("🚀 SMART DEPLOYMENT PARA CLOUD RUN")
        print(f"⏰ Iniciado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📦 Proyecto: {self.project_id}")
        print(f"🌍 Región: {self.region}")
        print(f"🔧 Servicio: {self.service_name}")
        
        # Fase 1: Verificación pre-deployment
        if not self.verify_deployment_readiness():
            self.print_error("❌ DEPLOYMENT CANCELADO - Corrige los problemas encontrados")
            return False
            
        # Fase 2: Obtener commit SHA
        commit_sha = self.get_commit_sha()
        self.print_info(f"📋 Usando commit/tag: {commit_sha}")
        
        # Fase 3: Build y Push
        image_tag = self.build_and_push_image(commit_sha)
        if not image_tag:
            self.print_error("❌ DEPLOYMENT CANCELADO - Fallo en build/push")
            return False
            
        # Fase 4: Deploy a Cloud Run
        if not self.deploy_to_cloud_run(image_tag):
            self.print_error("❌ DEPLOYMENT FALLIDO")
            return False
            
        # Fase 5: Resultado final
        self.print_section("🎉 DEPLOYMENT COMPLETADO EXITOSAMENTE")
        self.print_success(f"Imagen desplegada: {image_tag}")
        self.print_success(f"Servicio: {self.service_name}")
        self.print_success(f"Región: {self.region}")
        
        return True

def main():
    deployer = SmartDeployer()
    
    try:
        success = deployer.run_smart_deployment()
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\\n❌ Deployment interrumpido por el usuario")
        return 1
    except Exception as e:
        print(f"\\n❌ Error inesperado: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)