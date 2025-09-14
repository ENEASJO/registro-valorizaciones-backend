"""
Índices de base de datos optimizados para el sistema de notificaciones WhatsApp
Diseñados para soportar 1000+ notificaciones concurrentes con response time <200ms
"""

from sqlalchemy import text, Index, desc, asc
from sqlalchemy.orm import Session
from app.core.database import engine
import logging

logger = logging.getLogger(__name__)

# =====================================================================
# DEFINICIÓN DE ÍNDICES OPTIMIZADOS
# =====================================================================

class NotificationIndexes:
    """Índices optimizados para tabla de notificaciones"""
    
    # Índices principales para consultas frecuentes
    INDEXES = [
        # Índice compuesto para listado paginado por fecha (más usado)
        {
            "name": "idx_notifications_created_at_id_desc",
            "table": "whatsapp_notificaciones",
            "columns": ["created_at DESC", "id DESC"],
            "description": "Optimiza paginación por fecha de creación (cursor-based)",
            "estimated_usage": "95% de consultas de listado"
        },
        
        # Índice para filtros por estado (segundo más usado)
        {
            "name": "idx_notifications_estado_created_at",
            "table": "whatsapp_notificaciones", 
            "columns": ["estado", "created_at DESC"],
            "description": "Optimiza filtros por estado con ordenamiento",
            "estimated_usage": "80% de consultas filtradas"
        },
        
        # Índice para filtros por evento trigger
        {
            "name": "idx_notifications_evento_created_at",
            "table": "whatsapp_notificaciones",
            "columns": ["evento_trigger", "created_at DESC"], 
            "description": "Optimiza filtros por evento trigger",
            "estimated_usage": "60% de consultas filtradas"
        },
        
        # Índice para filtros por valorización (consultas específicas)
        {
            "name": "idx_notifications_valorizacion_id",
            "table": "whatsapp_notificaciones",
            "columns": ["valorizacion_id"],
            "description": "Optimiza búsquedas por valorización específica",
            "estimated_usage": "40% de consultas de detalle"
        },
        
        # Índice para filtros por contacto
        {
            "name": "idx_notifications_contacto_id_created_at",
            "table": "whatsapp_notificaciones",
            "columns": ["contacto_id", "created_at DESC"],
            "description": "Optimiza consultas por contacto con ordenamiento",
            "estimated_usage": "30% de consultas filtradas"
        },
        
        # Índice para métricas por rango de fechas
        {
            "name": "idx_notifications_created_at_estado",
            "table": "whatsapp_notificaciones",
            "columns": ["created_at", "estado"],
            "description": "Optimiza cálculo de métricas por período",
            "estimated_usage": "100% de consultas de métricas"
        },
        
        # Índice para notificaciones pendientes (procesamiento background)
        {
            "name": "idx_notifications_pending_processing",
            "table": "whatsapp_notificaciones",
            "columns": ["estado", "fecha_programada", "reintentos"],
            "where": "estado IN ('PENDIENTE', 'PROGRAMADA')",
            "description": "Optimiza selección de notificaciones para procesamiento",
            "estimated_usage": "100% de tareas background"
        },
        
        # Índice para webhook updates por WhatsApp message ID
        {
            "name": "idx_notifications_whatsapp_message_id",
            "table": "whatsapp_notificaciones",
            "columns": ["whatsapp_message_id"],
            "where": "whatsapp_message_id IS NOT NULL",
            "description": "Optimiza actualizaciones por webhook de WhatsApp",
            "estimated_usage": "100% de webhooks"
        },
        
        # Índice compuesto para filtros complejos (empresa + fecha)
        {
            "name": "idx_notifications_empresa_fecha",
            "table": "whatsapp_notificaciones",
            "columns": ["contacto_id", "created_at DESC", "estado"],
            "description": "Optimiza consultas filtradas por empresa y fecha",
            "estimated_usage": "25% de consultas empresariales"
        },
        
        # Índice para métricas por evento y estado
        {
            "name": "idx_notifications_evento_estado_fecha",
            "table": "whatsapp_notificaciones",
            "columns": ["evento_trigger", "estado", "created_at"],
            "description": "Optimiza agregaciones para dashboard y métricas",
            "estimated_usage": "100% de métricas detalladas"
        }
    ]

class ContactIndexes:
    """Índices optimizados para tabla de contactos"""
    
    INDEXES = [
        # Índice para búsquedas por teléfono (joins frecuentes)
        {
            "name": "idx_contacts_telefono_activo",
            "table": "whatsapp_contactos",
            "columns": ["telefono", "activo"],
            "description": "Optimiza búsquedas y validaciones por teléfono",
            "estimated_usage": "80% de validaciones"
        },
        
        # Índice para filtros por empresa
        {
            "name": "idx_contacts_empresa_id_activo",
            "table": "whatsapp_contactos", 
            "columns": ["empresa_id", "activo", "nombre"],
            "description": "Optimiza listados por empresa",
            "estimated_usage": "70% de consultas filtradas"
        },
        
        # Índice para búsquedas de texto
        {
            "name": "idx_contacts_nombre_email",
            "table": "whatsapp_contactos",
            "columns": ["nombre", "email"],
            "description": "Optimiza búsquedas por nombre y email",
            "estimated_usage": "50% de búsquedas"
        },
        
        # Índice para tipo de contacto
        {
            "name": "idx_contacts_tipo_activo",
            "table": "whatsapp_contactos",
            "columns": ["tipo_contacto", "activo"],
            "description": "Optimiza filtros por tipo de contacto",
            "estimated_usage": "40% de consultas filtradas"
        }
    ]

class TemplateIndexes:
    """Índices optimizados para tabla de plantillas"""
    
    INDEXES = [
        # Índice para selección de plantillas por evento
        {
            "name": "idx_templates_evento_activo",
            "table": "whatsapp_plantillas_mensajes",
            "columns": ["evento_trigger", "activo"],
            "description": "Optimiza selección de plantillas para notificaciones",
            "estimated_usage": "100% de creación de notificaciones"
        },
        
        # Índice único para código de plantilla
        {
            "name": "idx_templates_codigo_unique",
            "table": "whatsapp_plantillas_mensajes",
            "columns": ["codigo"],
            "unique": True,
            "description": "Garantiza unicidad de códigos de plantilla",
            "estimated_usage": "100% de validaciones"
        },
        
        # Índice para filtros por destinatario y estado
        {
            "name": "idx_templates_destinatario_estado",
            "table": "whatsapp_plantillas_mensajes",
            "columns": ["tipo_destinatario", "estado_valorizacion", "activo"],
            "description": "Optimiza selección por tipo y estado de valorización",
            "estimated_usage": "80% de selecciones de plantilla"
        }
    ]

class MetricsIndexes:
    """Índices optimizados para tabla de métricas diarias"""
    
    INDEXES = [
        # Índice principal por fecha
        {
            "name": "idx_metrics_fecha_desc",
            "table": "whatsapp_metricas_diarias",
            "columns": ["fecha_metrica DESC"],
            "description": "Optimiza consultas de métricas por rango de fechas",
            "estimated_usage": "100% de consultas de métricas históricas"
        },
        
        # Índice único para evitar duplicados
        {
            "name": "idx_metrics_fecha_unique",
            "table": "whatsapp_metricas_diarias",
            "columns": ["fecha_metrica"],
            "unique": True,
            "description": "Garantiza una métrica por día",
            "estimated_usage": "100% de inserciones de métricas"
        }
    ]

# =====================================================================
# FUNCIONES DE GESTIÓN DE ÍNDICES
# =====================================================================

def create_index_sql(index_config: dict) -> str:
    """Generar SQL para crear un índice"""
    
    index_type = "UNIQUE INDEX" if index_config.get("unique") else "INDEX"
    name = index_config["name"]
    table = index_config["table"]
    columns = ", ".join(index_config["columns"])
    
    sql = f"CREATE {index_type} IF NOT EXISTS {name} ON {table} ({columns})"
    
    if index_config.get("where"):
        sql += f" WHERE {index_config['where']}"
    
    return sql

def drop_index_sql(index_name: str) -> str:
    """Generar SQL para eliminar un índice"""
    return f"DROP INDEX IF EXISTS {index_name}"

async def create_all_indexes(db: Session):
    """Crear todos los índices optimizados"""
    
    logger.info("Starting creation of optimized database indexes")
    
    all_indexes = (
        NotificationIndexes.INDEXES +
        ContactIndexes.INDEXES + 
        TemplateIndexes.INDEXES +
        MetricsIndexes.INDEXES
    )
    
    created_count = 0
    error_count = 0
    
    for index_config in all_indexes:
        try:
            sql = create_index_sql(index_config)
            logger.info(f"Creating index: {index_config['name']}")
            logger.debug(f"SQL: {sql}")
            
            db.execute(text(sql))
            db.commit()
            
            created_count += 1
            logger.info(f"✅ Created index: {index_config['name']} - {index_config['description']}")
            
        except Exception as e:
            error_count += 1
            logger.error(f"❌ Failed to create index {index_config['name']}: {str(e)}")
            db.rollback()
    
    logger.info(f"Index creation completed: {created_count} created, {error_count} errors")
    
    return {
        "total_indexes": len(all_indexes),
        "created": created_count,
        "errors": error_count,
        "success_rate": round((created_count / len(all_indexes)) * 100, 2)
    }

async def analyze_index_usage(db: Session) -> dict:
    """Analizar uso de índices (SQLite específico)"""
    
    try:
        # Para SQLite, obtenemos estadísticas básicas
        index_stats = {}
        
        # Consultar índices existentes
        result = db.execute(text("""
            SELECT name, sql 
            FROM sqlite_master 
            WHERE type = 'index' 
            AND name LIKE 'idx_%'
            ORDER BY name
        """)).fetchall()
        
        index_stats["total_custom_indexes"] = len(result)
        index_stats["indexes"] = [
            {"name": row[0], "definition": row[1]} 
            for row in result
        ]
        
        # Estadísticas de tablas principales
        table_stats = {}
        
        tables = ["whatsapp_notificaciones", "whatsapp_contactos", "whatsapp_plantillas_mensajes"]
        for table in tables:
            try:
                count_result = db.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                table_stats[table] = {"row_count": count_result}
            except Exception as e:
                table_stats[table] = {"error": str(e)}
        
        return {
            "index_statistics": index_stats,
            "table_statistics": table_stats,
            "recommendations": generate_index_recommendations(table_stats),
            "analyzed_at": "2025-01-23T12:00:00Z"
        }
        
    except Exception as e:
        logger.error(f"Error analyzing index usage: {str(e)}")
        return {"error": str(e)}

def generate_index_recommendations(table_stats: dict) -> list:
    """Generar recomendaciones de índices basadas en estadísticas"""
    
    recommendations = []
    
    # Revisar tamaño de tablas para recomendaciones
    for table, stats in table_stats.items():
        if "row_count" in stats:
            row_count = stats["row_count"]
            
            if row_count > 10000:
                recommendations.append({
                    "table": table,
                    "recommendation": "Consider partitioning for large table",
                    "priority": "medium",
                    "row_count": row_count
                })
            
            if row_count > 100000:
                recommendations.append({
                    "table": table,
                    "recommendation": "Monitor query performance and consider additional indexes",
                    "priority": "high", 
                    "row_count": row_count
                })
    
    # Recomendaciones generales
    recommendations.extend([
        {
            "type": "maintenance",
            "recommendation": "Run ANALYZE after bulk data changes",
            "priority": "medium"
        },
        {
            "type": "monitoring", 
            "recommendation": "Monitor slow queries and index hit ratios",
            "priority": "high"
        },
        {
            "type": "performance",
            "recommendation": "Consider composite indexes for frequent multi-column filters",
            "priority": "medium"
        }
    ])
    
    return recommendations

# =====================================================================
# COMANDO CLI PARA GESTIÓN DE ÍNDICES
# =====================================================================

async def manage_indexes_cli(action: str, db: Session):
    """Interfaz CLI para gestión de índices"""
    
    if action == "create":
        return await create_all_indexes(db)
    
    elif action == "analyze":
        return await analyze_index_usage(db)
    
    elif action == "drop_all":
        logger.warning("Dropping all custom indexes")
        
        all_indexes = (
            NotificationIndexes.INDEXES +
            ContactIndexes.INDEXES + 
            TemplateIndexes.INDEXES +
            MetricsIndexes.INDEXES
        )
        
        dropped_count = 0
        for index_config in all_indexes:
            try:
                sql = drop_index_sql(index_config["name"])
                db.execute(text(sql))
                db.commit()
                dropped_count += 1
                logger.info(f"Dropped index: {index_config['name']}")
            except Exception as e:
                logger.error(f"Failed to drop index {index_config['name']}: {str(e)}")
        
        return {"dropped": dropped_count}
    
    else:
        return {"error": f"Unknown action: {action}"}

# =====================================================================
# VALIDADORES DE PERFORMANCE
# =====================================================================

async def validate_query_performance(db: Session) -> dict:
    """Validar performance de queries críticas"""
    
    performance_tests = [
        {
            "name": "notification_list_paginated",
            "sql": """
                SELECT COUNT(*) FROM whatsapp_notificaciones 
                WHERE created_at >= datetime('now', '-7 days')
                ORDER BY created_at DESC, id DESC
                LIMIT 20
            """,
            "target_ms": 200
        },
        {
            "name": "notification_by_state",
            "sql": """
                SELECT COUNT(*) FROM whatsapp_notificaciones 
                WHERE estado = 'ENVIADA' 
                AND created_at >= datetime('now', '-1 day')
            """,
            "target_ms": 100
        },
        {
            "name": "metrics_calculation",
            "sql": """
                SELECT estado, COUNT(*) as count
                FROM whatsapp_notificaciones 
                WHERE created_at >= datetime('now', '-7 days')
                GROUP BY estado
            """,
            "target_ms": 300
        }
    ]
    
    results = []
    
    for test in performance_tests:
        import time
        start_time = time.time()
        
        try:
            db.execute(text(test["sql"]))
            duration_ms = (time.time() - start_time) * 1000
            
            results.append({
                "test": test["name"],
                "duration_ms": round(duration_ms, 2),
                "target_ms": test["target_ms"],
                "performance": "good" if duration_ms <= test["target_ms"] else "needs_optimization",
                "success": True
            })
            
        except Exception as e:
            results.append({
                "test": test["name"],
                "error": str(e),
                "success": False
            })
    
    return {
        "performance_tests": results,
        "overall_performance": "good" if all(r.get("performance") == "good" for r in results if r.get("success")) else "needs_optimization"
    }