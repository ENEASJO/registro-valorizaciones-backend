#!/usr/bin/env python3
"""
🔍 Sistema de Monitoreo y Diagnóstico de Deployment
Analiza problemas comunes de deployment en Cloud Run
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

def print_section(title):
    print(f"\n{'='*60}")
    print(f"🔍 {title}")
    print('='*60)

def print_error(message):
    print(f"❌ {message}")

def print_success(message):
    print(f"✅ {message}")

def print_warning(message):
    print(f"⚠️  {message}")

def print_info(message):
    print(f"ℹ️  {message}")

def check_dockerfile():
    """Verificar Dockerfile"""
    print_section("ANÁLISIS DEL DOCKERFILE")
    
    dockerfile_path = Path("Dockerfile")
    if not dockerfile_path.exists():
        print_error("Dockerfile no encontrado")
        return False
    
    print_success("Dockerfile encontrado")
    
    with open(dockerfile_path, 'r') as f:
        content = f.read()
    
    checks = [
        ("python:3.11", "Imagen base Python 3.11"),
        ("requirements.txt", "Copia requirements.txt"),
        ("COPY main.py", "Copia main.py"),
        ("COPY app/", "Copia directorio app/"),
        ("PORT", "Variable PORT configurada"),
        ("uvicorn", "Comando uvicorn configurado")
    ]
    
    for check, desc in checks:
        if check in content:
            print_success(f"{desc}")
        else:
            print_error(f"{desc} - NO ENCONTRADO")
    
    return True

def compare_requirements():
    """Comparar requirements.txt vs requirements-cloudrun.txt"""
    print_section("ANÁLISIS DE DEPENDENCIAS")
    
    main_req = Path("requirements.txt")
    cloudrun_req = Path("requirements-cloudrun.txt")
    
    if not main_req.exists():
        print_error("requirements.txt no encontrado")
        return False
    
    if not cloudrun_req.exists():
        print_error("requirements-cloudrun.txt no encontrado")
        return False
    
    # Leer archivos
    with open(main_req, 'r') as f:
        main_deps = set(line.strip() for line in f if line.strip() and not line.startswith('#'))
    
    with open(cloudrun_req, 'r') as f:
        cloudrun_deps = set(line.strip() for line in f if line.strip() and not line.startswith('#'))
    
    print_info(f"requirements.txt: {len(main_deps)} dependencias")
    print_info(f"requirements-cloudrun.txt: {len(cloudrun_deps)} dependencias")
    
    # Dependencias críticas que deben estar en cloudrun
    critical_deps = {
        'fastapi',
        'uvicorn',
        'pydantic', 
        'sqlalchemy',
        'asyncpg',
        'databases',
        'python-dotenv',
        'httpx',
        'requests'
    }
    
    print("\n🔍 Verificando dependencias críticas:")
    missing_critical = []
    
    for dep in critical_deps:
        found = any(dep in line.lower() for line in cloudrun_deps)
        if found:
            print_success(f"{dep}")
        else:
            print_error(f"{dep} - FALTANTE")
            missing_critical.append(dep)
    
    if missing_critical:
        print_error(f"❌ PROBLEMA CRÍTICO: Faltan {len(missing_critical)} dependencias críticas")
        return False
    
    # Dependencias faltantes en cloudrun
    missing_in_cloudrun = []
    for dep in main_deps:
        dep_name = dep.split('==')[0].split('>=')[0].split('<=')[0]
        found = any(dep_name in line for line in cloudrun_deps)
        if not found:
            missing_in_cloudrun.append(dep)
    
    if missing_in_cloudrun:
        print_warning(f"Dependencias faltantes en cloudrun ({len(missing_in_cloudrun)}):")
        for dep in missing_in_cloudrun[:10]:  # Mostrar solo las primeras 10
            print(f"  - {dep}")
        if len(missing_in_cloudrun) > 10:
            print(f"  ... y {len(missing_in_cloudrun) - 10} más")
    
    return len(missing_critical) == 0

def check_main_py():
    """Verificar main.py y imports críticos"""
    print_section("ANÁLISIS DE MAIN.PY")
    
    main_path = Path("main.py")
    if not main_path.exists():
        print_error("main.py no encontrado")
        return False
    
    print_success("main.py encontrado")
    
    with open(main_path, 'r') as f:
        content = f.read()
    
    # Verificar imports críticos
    critical_imports = [
        'from fastapi import FastAPI',
        'from app.core.database import',
        'from app.api.routes.empresas_smart import router',
    ]
    
    for imp in critical_imports:
        if imp in content:
            print_success(f"Import encontrado: {imp}")
        else:
            print_warning(f"Import posiblemente faltante: {imp}")
    
    return True

def check_app_structure():
    """Verificar estructura de la app"""
    print_section("ANÁLISIS DE ESTRUCTURA DE ARCHIVOS")
    
    required_files = [
        "app/__init__.py",
        "app/core/__init__.py", 
        "app/core/database.py",
        "app/models/__init__.py",
        "app/models/empresa.py",
        "app/api/__init__.py",
        "app/api/routes/__init__.py",
        "app/api/routes/empresas_smart.py"
    ]
    
    missing_files = []
    for file in required_files:
        if Path(file).exists():
            print_success(f"{file}")
        else:
            print_error(f"{file} - NO ENCONTRADO")
            missing_files.append(file)
    
    if missing_files:
        print_error(f"❌ Faltan {len(missing_files)} archivos críticos")
        return False
    
    return True

def check_env_variables():
    """Verificar variables de entorno"""
    print_section("ANÁLISIS DE VARIABLES DE ENTORNO")
    
    env_file = Path(".env")
    if env_file.exists():
        print_success(".env encontrado")
        
        with open(env_file, 'r') as f:
            env_content = f.read()
        
        required_vars = [
            'NEON_CONNECTION_STRING',
            'DATABASE_URL'
        ]
        
        for var in required_vars:
            if var in env_content:
                print_success(f"Variable {var} configurada")
            else:
                print_warning(f"Variable {var} podría estar faltante")
    else:
        print_warning(".env no encontrado (normal en Cloud Run)")
    
    return True

def generate_fix_suggestions():
    """Generar sugerencias de corrección"""
    print_section("🔧 SUGERENCIAS DE CORRECCIÓN")
    
    print("1. 🔄 ACTUALIZAR requirements-cloudrun.txt:")
    print("   cp requirements.txt requirements-cloudrun.txt")
    print()
    
    print("2. 🐳 RECONSTRUIR imagen Docker:")
    print("   docker build -t gcr.io/valoraciones-app-cloud-run/registro-valorizaciones:latest .")
    print()
    
    print("3. 📤 PUSH nueva imagen:")  
    print("   docker push gcr.io/valoraciones-app-cloud-run/registro-valorizaciones:latest")
    print()
    
    print("4. 🚀 RE-DEPLOY a Cloud Run:")
    print("   gcloud run deploy registro-valorizaciones --image=gcr.io/valoraciones-app-cloud-run/registro-valorizaciones:latest --region=southamerica-west1")
    print()
    
    print("5. 📋 VERIFICAR deployment:")
    print("   curl https://[URL]/health")

def main():
    print("🚀 DIAGNÓSTICO DE DEPLOYMENT - Cloud Run")
    print(f"⏰ Ejecutado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Lista de verificaciones
    checks = [
        ("Dockerfile", check_dockerfile),
        ("Dependencias", compare_requirements),
        ("Main.py", check_main_py),
        ("Estructura", check_app_structure),
        ("Variables entorno", check_env_variables)
    ]
    
    results = {}
    
    for name, check_func in checks:
        try:
            result = check_func()
            results[name] = result
        except Exception as e:
            print_error(f"Error en verificación {name}: {e}")
            results[name] = False
    
    # Resumen final
    print_section("📊 RESUMEN DE DIAGNÓSTICO")
    
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    
    print(f"✅ Verificaciones exitosas: {passed}/{total}")
    
    failed_checks = [name for name, result in results.items() if not result]
    if failed_checks:
        print_error(f"❌ Verificaciones fallidas: {', '.join(failed_checks)}")
    
    if passed == total:
        print_success("🎉 ¡TODAS LAS VERIFICACIONES PASARON!")
        print_info("El deployment debería funcionar correctamente")
    else:
        print_error("⚠️  PROBLEMAS DETECTADOS - Ver sugerencias de corrección")
        generate_fix_suggestions()
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)