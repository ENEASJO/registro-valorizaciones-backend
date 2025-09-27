#!/usr/bin/env python3
"""
🔍 Sistema Avanzado de Diagnóstico de Deployment - Simulando GitHub MCP
Analiza en profundidad los problemas de deployment en Cloud Run
"""

import os
import sys
import json
import subprocess
from datetime import datetime
from pathlib import Path
import re

class DeploymentAnalyzer:
    def __init__(self):
        self.errors_found = []
        self.warnings_found = []
        self.suggestions = []
        
    def print_section(self, title):
        print(f"\n{'='*80}")
        print(f"🔍 {title}")
        print('='*80)

    def print_error(self, message):
        print(f"❌ {message}")
        self.errors_found.append(message)

    def print_success(self, message):
        print(f"✅ {message}")

    def print_warning(self, message):
        print(f"⚠️  {message}")
        self.warnings_found.append(message)

    def print_info(self, message):
        print(f"ℹ️  {message}")

    def analyze_git_status(self):
        """Analizar el estado actual del repositorio"""
        self.print_section("ANÁLISIS DEL REPOSITORIO GIT")
        
        try:
            # Verificar si hay cambios sin commit
            result = subprocess.run(['git', 'status', '--porcelain'], 
                                  capture_output=True, text=True, cwd='.')
            
            if result.returncode == 0:
                if result.stdout.strip():
                    self.print_warning("Hay cambios sin commit en el repositorio")
                    changes = result.stdout.strip().split('\n')
                    for change in changes[:10]:  # Mostrar solo los primeros 10
                        print(f"   {change}")
                    if len(changes) > 10:
                        print(f"   ... y {len(changes) - 10} archivos más")
                else:
                    self.print_success("Repositorio limpio - todos los cambios están committeados")
                    
                # Verificar último commit
                result = subprocess.run(['git', 'log', '-1', '--pretty=format:%h %s'], 
                                      capture_output=True, text=True, cwd='.')
                if result.returncode == 0:
                    self.print_info(f"Último commit: {result.stdout}")
                    
                # Verificar si estamos sincronizados con origin
                result = subprocess.run(['git', 'status', '-b', '--porcelain'], 
                                      capture_output=True, text=True, cwd='.')
                if result.returncode == 0:
                    status_lines = result.stdout.split('\n')
                    branch_line = status_lines[0] if status_lines else ""
                    if "ahead" in branch_line:
                        self.print_warning("Tienes commits locales sin push")
                    elif "behind" in branch_line:
                        self.print_warning("Tu rama local está desactualizada")
                    else:
                        self.print_success("Rama sincronizada con origin/main")
                        
        except FileNotFoundError:
            self.print_error("Git no está instalado o no disponible")
        except Exception as e:
            self.print_error(f"Error analizando Git: {e}")

    def analyze_dockerfile_deep(self):
        """Análisis profundo del Dockerfile"""
        self.print_section("ANÁLISIS PROFUNDO DEL DOCKERFILE")
        
        dockerfile_path = Path("Dockerfile")
        if not dockerfile_path.exists():
            self.print_error("Dockerfile no encontrado")
            return False
            
        with open(dockerfile_path, 'r') as f:
            content = f.read()
            
        # Verificaciones específicas para Cloud Run
        checks = [
            # Básicos
            ("FROM python:", "Imagen base Python definida"),
            ("WORKDIR", "Directorio de trabajo configurado"),
            ("COPY requirements", "Copia de requirements"),
            ("RUN pip install", "Instalación de dependencias"),
            ("COPY main.py", "Copia de archivo principal"),
            ("COPY app/", "Copia de directorio de aplicación"),
            ("EXPOSE", "Puerto expuesto"),
            ("CMD", "Comando de inicio definido"),
            
            # Específicos para Cloud Run
            ("PORT", "Variable PORT para Cloud Run"),
            ("uvicorn", "Servidor uvicorn configurado"),
            ("--host 0.0.0.0", "Host configurado para contenedores"),
            
            # Playwright específicos
            ("apt-get update", "Actualización de paquetes del sistema"),
            ("playwright install", "Instalación de navegadores Playwright"),
            ("PLAYWRIGHT_BROWSERS_PATH", "Variable de entorno Playwright"),
            
            # Seguridad
            ("useradd", "Usuario no-root creado"),
            ("USER app", "Ejecutando como usuario no-root"),
        ]
        
        passed = 0
        total = len(checks)
        
        for check, desc in checks:
            if check in content:
                self.print_success(f"{desc}")
                passed += 1
            else:
                self.print_warning(f"{desc} - Posiblemente faltante")
                
        # Verificar orden de comandos
        lines = content.split('\n')
        dockerfile_structure = []
        for line in lines:
            line = line.strip()
            if line.startswith(('FROM', 'WORKDIR', 'COPY', 'RUN', 'EXPOSE', 'CMD', 'USER')):
                dockerfile_structure.append(line.split()[0])
                
        self.print_info(f"Estructura del Dockerfile: {' -> '.join(dockerfile_structure)}")
        
        return passed >= total * 0.8  # Al menos 80% de las verificaciones

    def analyze_requirements_comprehensive(self):
        """Análisis comprehensivo de requirements"""
        self.print_section("ANÁLISIS COMPREHENSIVO DE REQUIREMENTS")
        
        # Leer ambos archivos
        main_req = Path("requirements.txt")
        cloudrun_req = Path("requirements-cloudrun.txt")
        
        if not main_req.exists():
            self.print_error("requirements.txt no encontrado")
            return False
            
        if not cloudrun_req.exists():
            self.print_error("requirements-cloudrun.txt no encontrado")
            return False
            
        with open(main_req, 'r') as f:
            main_deps = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            
        with open(cloudrun_req, 'r') as f:
            cloudrun_deps = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            
        self.print_info(f"requirements.txt: {len(main_deps)} dependencias")
        self.print_info(f"requirements-cloudrun.txt: {len(cloudrun_deps)} dependencias")
        
        # Verificar que son idénticos
        if set(main_deps) == set(cloudrun_deps):
            self.print_success("Archivos de requirements son idénticos")
        else:
            self.print_warning("Diferencias encontradas entre archivos de requirements")
            main_set = set(main_deps)
            cloudrun_set = set(cloudrun_deps)
            
            missing_in_cloudrun = main_set - cloudrun_set
            extra_in_cloudrun = cloudrun_set - main_set
            
            if missing_in_cloudrun:
                self.print_warning(f"Faltantes en cloudrun ({len(missing_in_cloudrun)}):")
                for dep in list(missing_in_cloudrun)[:5]:
                    print(f"   - {dep}")
                    
            if extra_in_cloudrun:
                self.print_warning(f"Extras en cloudrun ({len(extra_in_cloudrun)}):")
                for dep in list(extra_in_cloudrun)[:5]:
                    print(f"   + {dep}")
                    
        # Verificar dependencias críticas para el sistema inteligente
        critical_for_smart_system = [
            'fastapi', 'uvicorn', 'pydantic', 'sqlalchemy', 'asyncpg', 
            'databases', 'python-dotenv', 'httpx', 'requests', 
            'playwright', 'python-multipart', 'psycopg2-binary'
        ]
        
        print("\n🧠 Verificando dependencias del sistema inteligente:")
        missing_critical = []
        
        for dep_name in critical_for_smart_system:
            found = any(dep_name in dep.lower() for dep in cloudrun_deps)
            if found:
                self.print_success(f"{dep_name}")
            else:
                self.print_error(f"{dep_name} - CRÍTICA FALTANTE")
                missing_critical.append(dep_name)
                
        if missing_critical:
            self.suggestions.append(f"Agregar dependencias críticas faltantes: {', '.join(missing_critical)}")
            
        return len(missing_critical) == 0

    def analyze_main_py_deep(self):
        """Análisis profundo de main.py"""
        self.print_section("ANÁLISIS PROFUNDO DE MAIN.PY")
        
        main_path = Path("main.py")
        if not main_path.exists():
            self.print_error("main.py no encontrado")
            return False
            
        try:
            with open(main_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError as e:
            self.print_error(f"Error de encoding en main.py: {e}")
            return False
            
        # Verificar imports críticos
        critical_imports = [
            'from fastapi import FastAPI',
            'from app.core.database',
            'from app.api.routes.empresas_smart',
            'from app.api.routes.empresas',
            'FastAPI(',
            'app.include_router'
        ]
        
        print("\n🔍 Verificando imports críticos:")
        for imp in critical_imports:
            if imp in content:
                self.print_success(f"✓ {imp}")
            else:
                self.print_warning(f"? {imp}")
                
        # Verificar estructura de la app
        if 'app = FastAPI(' in content:
            self.print_success("Aplicación FastAPI inicializada")
        else:
            self.print_error("Aplicación FastAPI no encontrada")
            
        # Verificar que no haya caracteres problemáticos
        problematic_chars = ['📦', '✅', '❌', '⚠️', '🚀', '🔍', '⚡']
        found_problematic = []
        
        for char in problematic_chars:
            if char in content:
                found_problematic.append(char)
                
        if found_problematic:
            self.print_error(f"Caracteres problemáticos encontrados: {found_problematic}")
            self.suggestions.append("Ejecutar fix_encoding.py para limpiar caracteres")
            return False
        else:
            self.print_success("Sin caracteres problemáticos de encoding")
            
        # Verificar endpoints básicos
        basic_endpoints = ['@app.get("/")', '@app.get("/health")']
        for endpoint in basic_endpoints:
            if endpoint in content:
                self.print_success(f"Endpoint básico: {endpoint}")
            else:
                self.print_warning(f"Endpoint básico faltante: {endpoint}")
                
        return True

    def analyze_app_structure_deep(self):
        """Análisis profundo de la estructura de la aplicación"""
        self.print_section("ANÁLISIS PROFUNDO DE ESTRUCTURA")
        
        # Archivos críticos del sistema inteligente
        critical_files = [
            "app/__init__.py",
            "app/core/__init__.py",
            "app/core/database.py",
            "app/models/__init__.py", 
            "app/models/empresa.py",
            "app/api/__init__.py",
            "app/api/routes/__init__.py",
            "app/api/routes/empresas.py",
            "app/api/routes/empresas_smart.py",  # Crítico para sistema inteligente
            "app/services/empresa_service_neon.py",
            "app/services/sunat_service_improved.py"
        ]
        
        missing_files = []
        existing_files = []
        
        for file_path in critical_files:
            if Path(file_path).exists():
                existing_files.append(file_path)
                self.print_success(f"{file_path}")
                
                # Verificar que no esté vacío
                try:
                    size = Path(file_path).stat().st_size
                    if size == 0:
                        self.print_warning(f"{file_path} está vacío")
                    elif size < 100:
                        self.print_warning(f"{file_path} es muy pequeño ({size} bytes)")
                except:
                    pass
            else:
                missing_files.append(file_path)
                self.print_error(f"{file_path} - NO ENCONTRADO")
                
        # Verificar el contenido del router inteligente
        smart_router_path = Path("app/api/routes/empresas_smart.py")
        if smart_router_path.exists():
            try:
                with open(smart_router_path, 'r', encoding='utf-8') as f:
                    smart_content = f.read()
                    
                # Verificar endpoints del sistema inteligente
                smart_endpoints = [
                    '/validar-ruc', '/crear-automatica', '/crear-manual',
                    '/crear-dual', '/crear-con-fallback', '/validar-datos-manuales'
                ]
                
                print(f"\n🧠 Verificando endpoints del sistema inteligente:")
                for endpoint in smart_endpoints:
                    if endpoint in smart_content:
                        self.print_success(f"Endpoint: {endpoint}")
                    else:
                        self.print_warning(f"Endpoint posiblemente faltante: {endpoint}")
                        
            except Exception as e:
                self.print_error(f"Error leyendo empresas_smart.py: {e}")
        
        if missing_files:
            self.suggestions.append(f"Crear archivos faltantes: {', '.join(missing_files[:3])}")
            
        return len(missing_files) == 0

    def analyze_environment_variables(self):
        """Analizar variables de entorno"""
        self.print_section("ANÁLISIS DE VARIABLES DE ENTORNO")
        
        env_file = Path(".env")
        if env_file.exists():
            self.print_success(".env encontrado")
            
            try:
                with open(env_file, 'r') as f:
                    env_content = f.read()
                    
                required_vars = [
                    'NEON_CONNECTION_STRING',
                    'DATABASE_URL'
                ]
                
                for var in required_vars:
                    if var in env_content and not env_content.split(f'{var}=')[1].split('\n')[0].strip() in ['', '""', "''"]:
                        self.print_success(f"Variable {var} configurada")
                    else:
                        self.print_warning(f"Variable {var} vacía o faltante")
                        
            except Exception as e:
                self.print_error(f"Error leyendo .env: {e}")
        else:
            self.print_info(".env no encontrado (normal en Cloud Run)")
            self.print_info("Cloud Run debería tener variables configuradas en el servicio")
            
        return True

    def simulate_github_actions_check(self):
        """Simular verificaciones que haría GitHub Actions"""
        self.print_section("SIMULACIÓN DE GITHUB ACTIONS")
        
        # Verificar si existe configuración de GitHub Actions
        github_workflows = Path(".github/workflows")
        if github_workflows.exists():
            self.print_success("Directorio de GitHub Actions encontrado")
            
            workflow_files = list(github_workflows.glob("*.yml")) + list(github_workflows.glob("*.yaml"))
            if workflow_files:
                self.print_info(f"Workflows encontrados: {len(workflow_files)}")
                for workflow in workflow_files:
                    print(f"   - {workflow.name}")
            else:
                self.print_warning("No se encontraron archivos de workflow")
        else:
            self.print_warning("No hay configuración de GitHub Actions")
            
        # Simular build del contenedor
        self.print_info("Simulando verificaciones de build...")
        
        # Verificar si Docker está disponible
        try:
            result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                self.print_success(f"Docker disponible: {result.stdout.strip()}")
                
                # Intentar un dry-run del build
                self.print_info("Verificando sintaxis del Dockerfile...")
                result = subprocess.run(['docker', 'build', '--no-cache', '--dry-run', '.'], 
                                      capture_output=True, text=True, timeout=30)
                if result.returncode == 0:
                    self.print_success("Dockerfile sintácticamente correcto")
                else:
                    self.print_error("Problema en Dockerfile:")
                    print(f"   {result.stderr}")
                    
            else:
                self.print_warning("Docker no disponible para verificación")
                
        except (FileNotFoundError, subprocess.TimeoutExpired):
            self.print_warning("Docker no disponible o timeout en verificación")
            
        return True

    def generate_deployment_report(self):
        """Generar reporte completo de deployment"""
        self.print_section("REPORTE FINAL DE DEPLOYMENT")
        
        total_errors = len(self.errors_found)
        total_warnings = len(self.warnings_found)
        
        print(f"📊 ERRORES ENCONTRADOS: {total_errors}")
        for i, error in enumerate(self.errors_found, 1):
            print(f"   {i}. {error}")
            
        print(f"\n⚠️  ADVERTENCIAS: {total_warnings}")
        for i, warning in enumerate(self.warnings_found, 1):
            print(f"   {i}. {warning}")
            
        print(f"\n💡 SUGERENCIAS DE CORRECCIÓN: {len(self.suggestions)}")
        for i, suggestion in enumerate(self.suggestions, 1):
            print(f"   {i}. {suggestion}")
            
        # Determinar el estado del deployment
        if total_errors == 0:
            if total_warnings == 0:
                print(f"\n🎉 ESTADO: DEPLOYMENT LISTO")
                print(f"   No se encontraron problemas críticos")
            else:
                print(f"\n✅ ESTADO: DEPLOYMENT PROBABLEMENTE EXITOSO")
                print(f"   Solo advertencias menores encontradas")
        else:
            print(f"\n❌ ESTADO: DEPLOYMENT FALLARÁ")
            print(f"   Se deben corregir {total_errors} errores críticos")
            
        return total_errors == 0

    def run_complete_analysis(self):
        """Ejecutar análisis completo"""
        print("🔍 ANÁLISIS AVANZADO DE DEPLOYMENT - Simulando GitHub MCP")
        print(f"⏰ Ejecutado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Ejecutar todos los análisis
        analyses = [
            ("Repositorio Git", self.analyze_git_status),
            ("Dockerfile Avanzado", self.analyze_dockerfile_deep),
            ("Requirements Comprehensivo", self.analyze_requirements_comprehensive),
            ("Main.py Profundo", self.analyze_main_py_deep),
            ("Estructura Profunda", self.analyze_app_structure_deep),
            ("Variables de Entorno", self.analyze_environment_variables),
            ("GitHub Actions Simulado", self.simulate_github_actions_check)
        ]
        
        results = {}
        for name, analysis_func in analyses:
            try:
                result = analysis_func()
                results[name] = result
            except Exception as e:
                self.print_error(f"Error en análisis {name}: {e}")
                results[name] = False
                
        # Generar reporte final
        success = self.generate_deployment_report()
        
        return success

def main():
    analyzer = DeploymentAnalyzer()
    success = analyzer.run_complete_analysis()
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)