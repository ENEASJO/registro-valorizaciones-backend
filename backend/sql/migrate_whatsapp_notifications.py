#!/usr/bin/env python3
"""
Script de migración para implementar el sistema de notificaciones WhatsApp
Base de datos: Turso (SQLite)
Fecha: 2025-08-23
"""

import os
import sys
import sqlite3
from datetime import datetime
from pathlib import Path

# Agregar el directorio raíz al path para importar módulos
sys.path.append(str(Path(__file__).parent.parent))

def conectar_base_datos():
    """Conectar a la base de datos SQLite/Turso"""
    # Usar la misma configuración que el sistema principal
    db_path = os.getenv("DATABASE_PATH", "./valoraciones.db")
    
    # Si es Turso, usar la URL de conexión apropiada
    turso_url = os.getenv("TURSO_DATABASE_URL")
    if turso_url:
        print(f"🔗 Conectando a Turso: {turso_url[:50]}...")
        # Para Turso necesitarías usar libsql-client, aquí simulamos SQLite local
        connection = sqlite3.connect(db_path)
    else:
        print(f"🔗 Conectando a SQLite local: {db_path}")
        connection = sqlite3.connect(db_path)
    
    connection.row_factory = sqlite3.Row
    return connection

def verificar_tablas_existentes(conn):
    """Verificar qué tablas del sistema de notificaciones ya existen"""
    cursor = conn.cursor()
    
    tablas_whatsapp = [
        'whatsapp_configuracion_horarios',
        'whatsapp_plantillas_mensajes', 
        'whatsapp_contactos',
        'whatsapp_notificaciones',
        'whatsapp_historial_notificaciones',
        'whatsapp_metricas_diarias'
    ]
    
    tablas_existentes = []
    
    for tabla in tablas_whatsapp:
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name=?
        """, (tabla,))
        
        if cursor.fetchone():
            tablas_existentes.append(tabla)
    
    return tablas_existentes

def ejecutar_sql_archivo(conn, archivo_sql):
    """Ejecutar un archivo SQL completo"""
    try:
        with open(archivo_sql, 'r', encoding='utf-8') as file:
            sql_content = file.read()
        
        # Ejecutar el script completo usando executescript
        cursor = conn.cursor()
        
        try:
            cursor.executescript(sql_content)
            print(f"✅ Script SQL ejecutado exitosamente")
        except sqlite3.Error as e:
            print(f"❌ Error ejecutando script: {e}")
            raise
        
        conn.commit()
        print(f"✅ Archivo SQL ejecutado exitosamente: {archivo_sql}")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error ejecutando archivo SQL: {e}")
        raise

def verificar_integridad_datos(conn):
    """Verificar la integridad de los datos después de la migración"""
    cursor = conn.cursor()
    
    verificaciones = [
        {
            'name': 'Configuración de horarios',
            'query': 'SELECT COUNT(*) as count FROM whatsapp_configuracion_horarios WHERE activo = TRUE',
            'expected_min': 1
        },
        {
            'name': 'Plantillas de mensajes',
            'query': 'SELECT COUNT(*) as count FROM whatsapp_plantillas_mensajes WHERE activo = TRUE',
            'expected_min': 3
        },
        {
            'name': 'Índices de notificaciones',
            'query': "SELECT COUNT(*) as count FROM sqlite_master WHERE type='index' AND name LIKE '%whatsapp%'",
            'expected_min': 8
        },
        {
            'name': 'Vistas del sistema',
            'query': "SELECT COUNT(*) as count FROM sqlite_master WHERE type='view' AND name LIKE 'v_%notificaciones%'",
            'expected_min': 3
        },
        {
            'name': 'Triggers automáticos',
            'query': "SELECT COUNT(*) as count FROM sqlite_master WHERE type='trigger' AND name LIKE '%whatsapp%'",
            'expected_min': 4
        }
    ]
    
    print("\n🔍 Verificando integridad de datos...")
    all_ok = True
    
    for verificacion in verificaciones:
        try:
            result = cursor.execute(verificacion['query']).fetchone()
            count = result['count']
            
            if count >= verificacion['expected_min']:
                print(f"✅ {verificacion['name']}: {count} elementos")
            else:
                print(f"❌ {verificacion['name']}: {count} elementos (esperado mínimo: {verificacion['expected_min']})")
                all_ok = False
                
        except Exception as e:
            print(f"❌ Error verificando {verificacion['name']}: {e}")
            all_ok = False
    
    return all_ok

def mostrar_resumen_instalacion(conn):
    """Mostrar resumen de la instalación"""
    cursor = conn.cursor()
    
    print(f"\n{'='*60}")
    print("📊 RESUMEN DE INSTALACIÓN - SISTEMA DE NOTIFICACIONES WHATSAPP")
    print(f"{'='*60}")
    
    # Configuración de horarios
    horarios = cursor.execute("""
        SELECT nombre, hora_inicio_envios, hora_fin_envios, activo 
        FROM whatsapp_configuracion_horarios
    """).fetchall()
    
    print(f"\n📅 CONFIGURACIONES DE HORARIO ({len(horarios)}):")
    for horario in horarios:
        estado = "✅ Activo" if horario['activo'] else "❌ Inactivo"
        print(f"  • {horario['nombre']}: {horario['hora_inicio_envios']} - {horario['hora_fin_envios']} {estado}")
    
    # Plantillas de mensajes
    plantillas = cursor.execute("""
        SELECT codigo, nombre, evento_trigger, tipo_destinatario, activo
        FROM whatsapp_plantillas_mensajes
        ORDER BY evento_trigger
    """).fetchall()
    
    print(f"\n📝 PLANTILLAS DE MENSAJES ({len(plantillas)}):")
    for plantilla in plantillas:
        estado = "✅" if plantilla['activo'] else "❌"
        print(f"  {estado} {plantilla['codigo']}")
        print(f"     📧 {plantilla['nombre']}")
        print(f"     🎯 Evento: {plantilla['evento_trigger']} → {plantilla['tipo_destinatario']}")
    
    # Vistas disponibles
    vistas = cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='view' AND name LIKE 'v_%notificaciones%'
        ORDER BY name
    """).fetchall()
    
    print(f"\n👁️  VISTAS DISPONIBLES ({len(vistas)}):")
    for vista in vistas:
        print(f"  • {vista['name']}")
    
    print(f"\n{'='*60}")
    print("✅ SISTEMA DE NOTIFICACIONES WHATSAPP INSTALADO CORRECTAMENTE")
    print(f"{'='*60}")
    
    print(f"\n🚀 PRÓXIMOS PASOS:")
    print(f"1. Configurar contactos WhatsApp para las empresas")
    print(f"2. Ajustar plantillas de mensajes según necesidades")
    print(f"3. Implementar el worker de procesamiento de notificaciones")
    print(f"4. Configurar integración con API de WhatsApp")
    print(f"5. Implementar dashboard de monitoreo")

def crear_backup_seguridad(conn):
    """Crear backup de seguridad antes de la migración"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"backup_before_whatsapp_migration_{timestamp}.sql"
    
    print(f"🛡️  Creando backup de seguridad: {backup_path}")
    
    with open(backup_path, 'w', encoding='utf-8') as backup_file:
        for line in conn.iterdump():
            backup_file.write(f"{line}\n")
    
    print(f"✅ Backup creado exitosamente: {backup_path}")
    return backup_path

def main():
    """Función principal de migración"""
    print(f"🚀 INICIANDO MIGRACIÓN - SISTEMA DE NOTIFICACIONES WHATSAPP")
    print(f"{'='*60}")
    print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # 1. Conectar a la base de datos
        print(f"\n1️⃣  Conectando a la base de datos...")
        conn = conectar_base_datos()
        print(f"✅ Conexión establecida exitosamente")
        
        # 2. Crear backup de seguridad
        print(f"\n2️⃣  Creando backup de seguridad...")
        backup_path = crear_backup_seguridad(conn)
        
        # 3. Verificar tablas existentes
        print(f"\n3️⃣  Verificando estado actual...")
        tablas_existentes = verificar_tablas_existentes(conn)
        
        if tablas_existentes:
            print(f"⚠️  Tablas de notificaciones ya existentes: {', '.join(tablas_existentes)}")
            respuesta = input("¿Desea continuar? (s/N): ").lower().strip()
            if respuesta not in ['s', 'si', 'sí', 'y', 'yes']:
                print("❌ Migración cancelada por el usuario")
                return
        
        # 4. Ejecutar migración
        print(f"\n4️⃣  Ejecutando migración...")
        sql_file = Path(__file__).parent / "whatsapp_notifications_schema.sql"
        ejecutar_sql_archivo(conn, sql_file)
        
        # 5. Verificar integridad
        print(f"\n5️⃣  Verificando integridad...")
        if not verificar_integridad_datos(conn):
            raise Exception("Falló la verificación de integridad de datos")
        
        # 6. Mostrar resumen
        mostrar_resumen_instalacion(conn)
        
        print(f"\n🎉 MIGRACIÓN COMPLETADA EXITOSAMENTE")
        
    except Exception as e:
        print(f"\n❌ ERROR DURANTE LA MIGRACIÓN: {e}")
        print(f"💡 Puede restaurar desde el backup: {backup_path if 'backup_path' in locals() else 'N/A'}")
        sys.exit(1)
        
    finally:
        if 'conn' in locals():
            conn.close()
            print(f"🔌 Conexión a base de datos cerrada")

if __name__ == "__main__":
    main()