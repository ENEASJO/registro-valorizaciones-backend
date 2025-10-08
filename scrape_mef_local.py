#!/usr/bin/env python3
"""
Script local para scraping MEF Invierte
========================================

Este script se ejecuta DESDE TU PC (IP residencial) para evitar el bloqueo de MEF.

Uso:
    python scrape_mef_local.py <CUI>

Ejemplos:
    python scrape_mef_local.py 2595080
    python scrape_mef_local.py 2595080 --force  # Fuerza actualización aunque ya exista

Requisitos:
    - Internet (tu IP residencial)
    - Python 3.11+
    - Dependencias instaladas (pip install -r requirements.txt)
    - Variable NEON_DATABASE_URL en .env

Flujo:
    1. Recibe CUI como parámetro
    2. Hace scraping a MEF Invierte (funciona porque es tu IP residencial)
    3. Guarda/actualiza datos en Neon PostgreSQL
    4. Railway lee estos datos desde la BD (súper rápido)
"""

import asyncio
import sys
import os
import json
from datetime import datetime
from typing import Optional

# Cargar variables de entorno
from dotenv import load_dotenv
load_dotenv()

# Importar servicios
from databases import Database
from app.services.mef_invierte_service import consultar_cui_mef

# Colores para terminal
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_success(message: str):
    """Print success message in green"""
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")


def print_error(message: str):
    """Print error message in red"""
    print(f"{Colors.RED}❌ {message}{Colors.END}")


def print_info(message: str):
    """Print info message in blue"""
    print(f"{Colors.BLUE}ℹ️  {message}{Colors.END}")


def print_warning(message: str):
    """Print warning message in yellow"""
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")


async def verificar_cui_existe(database: Database, cui: str) -> Optional[dict]:
    """Verifica si el CUI ya existe en la base de datos"""
    try:
        obra = await database.fetch_one(
            """
            SELECT id, codigo, nombre, cui, fecha_actualizacion_mef
            FROM obras
            WHERE cui = :cui
            """,
            {"cui": cui}
        )
        return dict(obra) if obra else None
    except Exception as e:
        print_error(f"Error verificando CUI en BD: {e}")
        return None


async def guardar_datos_mef(database: Database, cui: str, datos_mef: dict, force: bool = False):
    """Guarda o actualiza datos MEF en la base de datos"""

    # Verificar si ya existe
    obra_existente = await verificar_cui_existe(database, cui)

    if obra_existente and not force:
        print_warning(f"CUI {cui} ya existe en la BD (última actualización: {obra_existente['fecha_actualizacion_mef']})")
        print_info("Usa --force para forzar actualización")
        return False

    try:
        if obra_existente:
            # Actualizar obra existente
            await database.execute(
                """
                UPDATE obras
                SET
                    datos_mef = :datos_mef,
                    fecha_actualizacion_mef = NOW()
                WHERE cui = :cui
                """,
                {
                    "cui": cui,
                    "datos_mef": json.dumps(datos_mef)
                }
            )
            print_success(f"Datos MEF actualizados en BD para CUI {cui}")
            print_info(f"Obra: {obra_existente['codigo']} - {obra_existente['nombre']}")
            return True
        else:
            print_warning(f"CUI {cui} no tiene obra asociada en la BD")
            print_info("Los datos fueron scraped correctamente pero NO se guardaron")
            print_info("Primero crea la obra en el sistema, luego ejecuta este script")
            return False

    except Exception as e:
        print_error(f"Error guardando en BD: {e}")
        return False


async def main():
    """Función principal"""

    # Validar argumentos
    if len(sys.argv) < 2:
        print_error("Uso: python scrape_mef_local.py <CUI> [--force]")
        print_info("Ejemplo: python scrape_mef_local.py 2595080")
        sys.exit(1)

    cui = sys.argv[1]
    force = "--force" in sys.argv

    # Validar CUI
    if not cui.isdigit():
        print_error(f"CUI inválido: {cui} (debe ser numérico)")
        sys.exit(1)

    print()
    print(f"{Colors.BOLD}{'=' * 80}{Colors.END}")
    print(f"{Colors.BOLD}SCRAPING MEF INVIERTE - EJECUCIÓN LOCAL{Colors.END}")
    print(f"{Colors.BOLD}{'=' * 80}{Colors.END}")
    print()
    print_info(f"CUI: {cui}")
    print_info(f"Modo: {'Forzar actualización' if force else 'Normal'}")
    print()

    # Conectar a base de datos
    db_url = os.getenv("NEON_DATABASE_URL")
    if not db_url:
        print_error("Variable NEON_DATABASE_URL no encontrada en .env")
        sys.exit(1)

    database = Database(db_url)

    try:
        await database.connect()
        print_success("Conectado a base de datos Neon")
        print()

        # Hacer scraping
        print_info("Iniciando scraping a MEF Invierte...")
        print_warning("Esto puede tomar 30-60 segundos...")
        print()

        inicio = datetime.now()
        resultado = await consultar_cui_mef(cui)
        duracion = (datetime.now() - inicio).total_seconds()

        print()

        if not resultado.get("success"):
            print_error(f"No se encontró información para CUI {cui}")
            print_info(f"Error: {resultado.get('error', 'Desconocido')}")
            sys.exit(1)

        print_success(f"Scraping completado en {duracion:.1f} segundos")
        print()

        # Extraer datos de la respuesta (están dentro de 'data')
        datos_mef = resultado.get('data', {})

        # Mostrar datos obtenidos
        print(f"{Colors.BOLD}DATOS OBTENIDOS:{Colors.END}")
        nombre = datos_mef.get('nombre', 'N/A')
        print(f"  CUI: {datos_mef.get('cui', 'N/A')}")
        print(f"  Nombre: {nombre[:80] if nombre and nombre != 'N/A' else nombre}...")
        print(f"  Estado: {datos_mef.get('estado', 'N/A')}")
        print(f"  Etapa: {datos_mef.get('etapa', 'N/A')}")

        # Formatear costo total actualizado
        costos = datos_mef.get('costos_finales', {})
        costo = costos.get('costo_total_actualizado', 'N/A')
        if isinstance(costo, (int, float)):
            print(f"  Costo Total Actualizado: S/ {costo:,.2f}")
        else:
            print(f"  Costo Total Actualizado: {costo}")
        print()

        # Guardar en BD
        print_info("Guardando datos en base de datos...")
        guardado = await guardar_datos_mef(database, cui, datos_mef, force)

        print()
        print(f"{Colors.BOLD}{'=' * 80}{Colors.END}")

        if guardado:
            print_success("PROCESO COMPLETADO EXITOSAMENTE")
            print()
            print_info("Los usuarios ahora pueden consultar estos datos desde Railway")
            print_info(f"Endpoint: GET /api/v1/mef-invierte/consultar/{cui}")
        else:
            print_warning("SCRAPING EXITOSO PERO NO SE GUARDÓ EN BD")
            print()
            print_info("Los datos fueron obtenidos correctamente desde MEF")
            print_info("Pero no se guardaron porque:")
            print_info("  - El CUI no tiene una obra asociada en la BD")
            print_info("  - Primero crea la obra en el sistema")
            print_info("  - Luego ejecuta este script nuevamente")

        print(f"{Colors.BOLD}{'=' * 80}{Colors.END}")
        print()

    except KeyboardInterrupt:
        print()
        print_warning("Proceso cancelado por el usuario")
        sys.exit(1)

    except Exception as e:
        print()
        print_error(f"Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        await database.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
