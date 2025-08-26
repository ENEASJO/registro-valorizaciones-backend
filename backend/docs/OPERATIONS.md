# Manual de Operaciones - Sistema de Notificaciones WhatsApp

## Descripción General

Este manual está dirigido a administradores de sistema, ingenieros DevOps y personal técnico responsable del monitoreo, mantenimiento y operación continua del Sistema de Notificaciones WhatsApp en producción.

## Monitoreo del Sistema

### 🏥 Health Checks Automáticos

#### Health Check Principal
```bash
# Verificación básica
curl https://api.valoraciones.com/health

# Verificación detallada con métricas
curl https://api.valoraciones.com/health?detailed=true
```

**Response Saludable:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime_seconds": 3600,
  "components": {
    "database": {
      "status": "connected",
      "response_time_ms": 12.3,
      "active_connections": 5,
      "connection_pool_size": 20
    },
    "whatsapp_api": {
      "status": "healthy",
      "rate_limit_remaining": 847,
      "rate_limit_reset_seconds": 45,
      "last_successful_request": "2025-01-23T14:25:00"
    },
    "scheduler": {
      "status": "running",
      "active_jobs": 3,
      "last_execution": "2025-01-23T14:24:30",
      "next_execution": "2025-01-23T14:25:30"
    },
    "cache": {
      "status": "connected",
      "hit_rate": 0.87,
      "used_memory_mb": 64.2,
      "max_memory_mb": 256
    }
  }
}
```

#### Configurar Monitoreo Automático
```bash
# Script de monitoreo (guardar como /opt/scripts/health_monitor.sh)
#!/bin/bash
API_URL="https://api.valoraciones.com"
WEBHOOK_SLACK="https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"
LOG_FILE="/var/log/whatsapp-notifications/health.log"

check_health() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local response=$(curl -s -w "%{http_code}" -o /tmp/health_response.json "$API_URL/health")
    local http_code="${response: -3}"
    
    if [ "$http_code" = "200" ]; then
        local status=$(jq -r '.status' /tmp/health_response.json)
        if [ "$status" = "healthy" ]; then
            echo "[$timestamp] ✅ System HEALTHY" >> "$LOG_FILE"
            return 0
        else
            echo "[$timestamp] ⚠️  System DEGRADED - Status: $status" >> "$LOG_FILE"
            send_alert "⚠️ Sistema DEGRADADO" "$status"
            return 1
        fi
    else
        echo "[$timestamp] ❌ System DOWN - HTTP: $http_code" >> "$LOG_FILE"
        send_alert "🚨 Sistema CAÍDO" "HTTP $http_code"
        return 2
    fi
}

send_alert() {
    local title="$1"
    local message="$2"
    curl -X POST -H 'Content-type: application/json' \
        --data "{\"text\":\"$title: WhatsApp Notifications API\\n$message\"}" \
        "$WEBHOOK_SLACK"
}

# Ejecutar check
check_health

# Configurar crontab para ejecutar cada 2 minutos
# */2 * * * * /opt/scripts/health_monitor.sh
```

### 📊 Métricas de Sistema

#### Métricas Clave a Monitorear

1. **API Performance**
   - Response Time: < 200ms promedio
   - Error Rate: < 1%
   - Throughput: Requests por minuto
   - Disponibilidad: > 99.9%

2. **WhatsApp Integration**
   - Tasa de entrega: > 95%
   - Rate limits restantes: > 100
   - Errores de API: < 5 por hora
   - Webhooks processing: < 5s latency

3. **Database Performance**
   - Connection pool utilization: < 80%
   - Query execution time: < 100ms
   - Active connections: monitored
   - Disk usage: < 80%

4. **Background Jobs**
   - Queue size: < 50 items
   - Processing time: < 30s por batch
   - Failed jobs: < 5%
   - Scheduler uptime: > 99%

#### Script de Métricas Personalizadas
```bash
#!/bin/bash
# /opt/scripts/collect_metrics.sh

API_URL="https://api.valoraciones.com"
API_KEY="wn_api_monitoring_key"
METRICS_FILE="/var/log/whatsapp-notifications/metrics.log"

collect_api_metrics() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    # Obtener métricas del sistema
    local metrics=$(curl -s -H "X-API-Key: $API_KEY" "$API_URL/api/notifications/metrics/system")
    
    if [ $? -eq 0 ]; then
        echo "[$timestamp] API_METRICS: $metrics" >> "$METRICS_FILE"
        
        # Extraer métricas específicas
        local total_notifications=$(echo "$metrics" | jq -r '.total_notifications_today')
        local error_rate=$(echo "$metrics" | jq -r '.error_rate_percentage')
        local avg_response_time=$(echo "$metrics" | jq -r '.avg_response_time_ms')
        
        # Enviar a sistema de monitoreo (ejemplo: Prometheus)
        echo "whatsapp_notifications_total $total_notifications" | curl -X POST --data-binary @- http://pushgateway:9091/metrics/job/whatsapp_api
        echo "whatsapp_error_rate $error_rate" | curl -X POST --data-binary @- http://pushgateway:9091/metrics/job/whatsapp_api
        echo "whatsapp_response_time_ms $avg_response_time" | curl -X POST --data-binary @- http://pushgateway:9091/metrics/job/whatsapp_api
    fi
}

collect_whatsapp_metrics() {
    # Verificar estado de WhatsApp Business API
    local whatsapp_status=$(curl -s -H "Authorization: Bearer $WHATSAPP_ACCESS_TOKEN" \
        "https://graph.facebook.com/v18.0/$WHATSAPP_PHONE_NUMBER_ID")
    
    if echo "$whatsapp_status" | jq -e '.error' > /dev/null; then
        echo "[$timestamp] WHATSAPP_ERROR: $whatsapp_status" >> "$METRICS_FILE"
    else
        echo "[$timestamp] WHATSAPP_OK" >> "$METRICS_FILE"
    fi
}

# Ejecutar recolección
collect_api_metrics
collect_whatsapp_metrics

# Configurar cron para ejecutar cada 5 minutos
# */5 * * * * /opt/scripts/collect_metrics.sh
```

### 🔍 Logs y Trazabilidad

#### Configuración de Logs Estructurados
```json
{
  "timestamp": "2025-01-23T14:30:00.123Z",
  "level": "INFO",
  "logger": "whatsapp.notifications",
  "message": "Notification sent successfully",
  "context": {
    "request_id": "req_abc123def456",
    "user_id": "user_789",
    "valorizacion_id": 123,
    "notification_id": 456,
    "contacto_id": 789,
    "whatsapp_message_id": "wamid.HBgLNTE5ODc2NTQzMjEV...",
    "duration_ms": 1250,
    "endpoint": "POST /api/notifications"
  },
  "tags": ["notification", "whatsapp", "success"]
}
```

#### Scripts de Análisis de Logs
```bash
#!/bin/bash
# /opt/scripts/analyze_logs.sh

LOG_DIR="/var/log/whatsapp-notifications"
REPORT_FILE="/tmp/daily_report.txt"

# Análisis de errores en últimas 24 horas
analyze_errors() {
    echo "=== ANÁLISIS DE ERRORES - ÚLTIMAS 24 HORAS ===" > "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
    
    # Top 10 errores más frecuentes
    echo "Top 10 Errores:" >> "$REPORT_FILE"
    grep -h '"level":"ERROR"' "$LOG_DIR"/*.log | \
        jq -r '.message' | \
        sort | uniq -c | sort -rn | head -10 >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
    
    # Errores de WhatsApp API
    echo "Errores WhatsApp API:" >> "$REPORT_FILE"
    grep -h 'WHATSAPP_ERROR' "$LOG_DIR"/*.log | \
        jq -r '.context.whatsapp_error_code // "UNKNOWN"' | \
        sort | uniq -c | sort -rn >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
}

# Análisis de performance
analyze_performance() {
    echo "=== ANÁLISIS DE PERFORMANCE ===" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
    
    # Tiempo de respuesta promedio por endpoint
    echo "Tiempo de respuesta promedio por endpoint (ms):" >> "$REPORT_FILE"
    grep -h '"duration_ms"' "$LOG_DIR"/*.log | \
        jq -r '"\(.context.endpoint // "UNKNOWN") \(.context.duration_ms // 0)"' | \
        awk '{
            endpoint[$1] += $2; 
            count[$1]++;
        } END {
            for (e in endpoint) 
                printf "%-30s %6.1f ms\n", e, endpoint[e]/count[e]
        }' >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
}

# Análisis de uso
analyze_usage() {
    echo "=== ANÁLISIS DE USO ===" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
    
    # Requests por hora
    echo "Requests por hora:" >> "$REPORT_FILE"
    grep -h '"timestamp"' "$LOG_DIR"/*.log | \
        jq -r '.timestamp[0:13]' | \
        sort | uniq -c | \
        awk '{print $2 ": " $1 " requests"}' >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
    
    # Top empresas por notificaciones
    echo "Top 10 empresas por notificaciones enviadas:" >> "$REPORT_FILE"
    grep -h 'Notification sent' "$LOG_DIR"/*.log | \
        jq -r '.context.empresa_id // "UNKNOWN"' | \
        sort | uniq -c | sort -rn | head -10 >> "$REPORT_FILE"
}

# Ejecutar análisis
analyze_errors
analyze_performance
analyze_usage

# Enviar reporte por email (opcional)
if command -v mail >/dev/null 2>&1; then
    mail -s "WhatsApp Notifications - Reporte Diario $(date +%Y-%m-%d)" \
         admin@empresa.com < "$REPORT_FILE"
fi

echo "Reporte generado: $REPORT_FILE"
```

## Mantenimiento Preventivo

### 🧹 Limpieza de Datos

#### Script de Limpieza Automática
```sql
-- /opt/scripts/cleanup_old_data.sql
-- Ejecutar diariamente para mantener performance

-- 1. Limpiar notificaciones antiguas (>90 días)
DELETE FROM whatsapp_notificaciones 
WHERE created_at < DATE('now', '-90 days')
  AND estado IN ('ENVIADA', 'ENTREGADA', 'LEIDA', 'ERROR', 'CANCELADA');

-- 2. Limpiar historial de notificaciones (>180 días)
DELETE FROM whatsapp_historial_notificaciones 
WHERE created_at < DATE('now', '-180 days');

-- 3. Mantener solo métricas diarias del último año
DELETE FROM whatsapp_metricas_diarias 
WHERE fecha_metrica < DATE('now', '-365 days');

-- 4. Vacuum para optimizar espacio
VACUUM;

-- 5. Analizar estadísticas para optimizar queries
ANALYZE;

-- Log del mantenimiento
INSERT INTO system_maintenance_log (
    operation, 
    executed_at, 
    details
) VALUES (
    'DATA_CLEANUP',
    datetime('now'),
    'Cleaned old notifications, history, and metrics'
);
```

#### Automatizar Limpieza
```bash
#!/bin/bash
# /opt/scripts/run_cleanup.sh

SCRIPT_DIR="/opt/scripts"
LOG_FILE="/var/log/whatsapp-notifications/maintenance.log"
DB_URL="$TURSO_DATABASE_URL"
DB_TOKEN="$TURSO_AUTH_TOKEN"

run_cleanup() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] Iniciando limpieza de datos..." >> "$LOG_FILE"
    
    # Ejecutar script SQL de limpieza
    if command -v turso >/dev/null 2>&1; then
        turso db shell "$DB_URL" --auth-token "$DB_TOKEN" < "$SCRIPT_DIR/cleanup_old_data.sql"
        echo "[$timestamp] Limpieza completada exitosamente" >> "$LOG_FILE"
    else
        echo "[$timestamp] ERROR: turso CLI no encontrado" >> "$LOG_FILE"
        return 1
    fi
}

# Verificar espacio en disco antes de limpieza
check_disk_space() {
    local disk_usage=$(df /var/log | awk 'NR==2 {print $5}' | sed 's/%//')
    if [ "$disk_usage" -gt 85 ]; then
        echo "[$timestamp] ADVERTENCIA: Espacio en disco al ${disk_usage}%" >> "$LOG_FILE"
    fi
}

check_disk_space
run_cleanup

# Configurar cron para ejecutar diariamente a las 2 AM
# 0 2 * * * /opt/scripts/run_cleanup.sh
```

### 🔧 Optimización de Base de Datos

#### Reindexado Automático
```sql
-- /opt/scripts/reindex_database.sql
-- Ejecutar semanalmente para optimizar performance

-- Reindexar tablas principales
REINDEX idx_whatsapp_notificaciones_envio_pendiente;
REINDEX idx_whatsapp_notificaciones_valorizacion;
REINDEX idx_whatsapp_notificaciones_estado;
REINDEX idx_whatsapp_contactos_empresa;
REINDEX idx_whatsapp_plantillas_evento;

-- Actualizar estadísticas de tablas
ANALYZE whatsapp_notificaciones;
ANALYZE whatsapp_contactos;
ANALYZE whatsapp_plantillas_mensajes;
ANALYZE whatsapp_historial_notificaciones;
ANALYZE whatsapp_metricas_diarias;

-- Verificar integridad de datos
PRAGMA integrity_check;

-- Log del reindexado
INSERT INTO system_maintenance_log (
    operation, 
    executed_at, 
    details
) VALUES (
    'REINDEX',
    datetime('now'),
    'Reindexed main tables and updated statistics'
);
```

### 🔄 Backup y Recuperación

#### Backup Automático
```bash
#!/bin/bash
# /opt/scripts/backup_database.sh

BACKUP_DIR="/opt/backups/whatsapp-notifications"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/whatsapp_notifications_$TIMESTAMP.db"
LOG_FILE="/var/log/whatsapp-notifications/backup.log"

# Crear directorio de backup si no existe
mkdir -p "$BACKUP_DIR"

backup_database() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] Iniciando backup de base de datos..." >> "$LOG_FILE"
    
    if command -v turso >/dev/null 2>&1; then
        # Backup usando Turso CLI
        turso db dump "$TURSO_DATABASE_URL" --auth-token "$TURSO_AUTH_TOKEN" > "$BACKUP_FILE"
        
        if [ $? -eq 0 ]; then
            # Comprimir backup
            gzip "$BACKUP_FILE"
            echo "[$timestamp] Backup completado: ${BACKUP_FILE}.gz" >> "$LOG_FILE"
            
            # Verificar integridad del backup
            verify_backup "${BACKUP_FILE}.gz"
        else
            echo "[$timestamp] ERROR: Backup falló" >> "$LOG_FILE"
            return 1
        fi
    else
        echo "[$timestamp] ERROR: turso CLI no disponible" >> "$LOG_FILE"
        return 1
    fi
}

verify_backup() {
    local backup_file="$1"
    local size=$(stat -c%s "$backup_file")
    
    if [ "$size" -gt 1024 ]; then  # Mínimo 1KB
        echo "[$timestamp] Backup verificado: ${size} bytes" >> "$LOG_FILE"
        
        # Enviar notificación de éxito
        send_backup_notification "✅ Backup exitoso" "$backup_file"
    else
        echo "[$timestamp] ERROR: Backup muy pequeño: ${size} bytes" >> "$LOG_FILE"
        send_backup_notification "❌ Backup falló" "Archivo muy pequeño"
        return 1
    fi
}

cleanup_old_backups() {
    # Mantener solo últimos 7 días de backups
    find "$BACKUP_DIR" -name "*.db.gz" -mtime +7 -delete
    echo "[$timestamp] Backups antiguos eliminados" >> "$LOG_FILE"
}

send_backup_notification() {
    local status="$1"
    local details="$2"
    
    curl -X POST -H 'Content-type: application/json' \
        --data "{\"text\":\"$status: Database Backup\\n$details\"}" \
        "$WEBHOOK_SLACK" 2>/dev/null
}

# Ejecutar backup
backup_database
cleanup_old_backups

# Configurar cron para backup diario a las 3 AM
# 0 3 * * * /opt/scripts/backup_database.sh
```

#### Procedimiento de Recuperación
```bash
#!/bin/bash
# /opt/scripts/restore_database.sh

BACKUP_DIR="/opt/backups/whatsapp-notifications"
LOG_FILE="/var/log/whatsapp-notifications/restore.log"

restore_from_backup() {
    local backup_date="$1"  # Formato: YYYYMMDD_HHMMSS
    local backup_file="$BACKUP_DIR/whatsapp_notifications_${backup_date}.db.gz"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    echo "[$timestamp] Iniciando restauración desde: $backup_file" >> "$LOG_FILE"
    
    if [ ! -f "$backup_file" ]; then
        echo "[$timestamp] ERROR: Archivo de backup no encontrado" >> "$LOG_FILE"
        return 1
    fi
    
    # Descomprimir backup
    gunzip -c "$backup_file" > "/tmp/restore_${backup_date}.db"
    
    # PRECAUCIÓN: Esto reemplazará la base de datos actual
    echo "ADVERTENCIA: Esto reemplazará la base de datos actual."
    echo "Presiona Enter para continuar o Ctrl+C para cancelar..."
    read
    
    # Restaurar usando Turso CLI
    turso db shell "$TURSO_DATABASE_URL" --auth-token "$TURSO_AUTH_TOKEN" < "/tmp/restore_${backup_date}.db"
    
    if [ $? -eq 0 ]; then
        echo "[$timestamp] Restauración completada exitosamente" >> "$LOG_FILE"
        
        # Verificar integridad después de restauración
        verify_restored_database
    else
        echo "[$timestamp] ERROR: Restauración falló" >> "$LOG_FILE"
        return 1
    fi
    
    # Limpiar archivo temporal
    rm -f "/tmp/restore_${backup_date}.db"
}

verify_restored_database() {
    echo "Verificando integridad de base de datos restaurada..."
    
    # Verificar que las tablas principales existen
    local tables=(
        "whatsapp_notificaciones"
        "whatsapp_contactos" 
        "whatsapp_plantillas_mensajes"
        "whatsapp_configuracion_horarios"
        "whatsapp_historial_notificaciones"
        "whatsapp_metricas_diarias"
    )
    
    for table in "${tables[@]}"; do
        local count=$(turso db shell "$TURSO_DATABASE_URL" --auth-token "$TURSO_AUTH_TOKEN" \
            "SELECT COUNT(*) FROM $table;" 2>/dev/null)
        
        if [[ "$count" =~ ^[0-9]+$ ]]; then
            echo "✅ $table: $count registros"
        else
            echo "❌ $table: Error verificando tabla"
        fi
    done
}

# Uso: ./restore_database.sh 20250123_030000
if [ $# -eq 0 ]; then
    echo "Uso: $0 <timestamp_backup>"
    echo "Ejemplo: $0 20250123_030000"
    echo "Backups disponibles:"
    ls -la "$BACKUP_DIR"/whatsapp_notifications_*.db.gz 2>/dev/null | awk '{print $9}' | sed 's/.*whatsapp_notifications_//' | sed 's/.db.gz//'
    exit 1
fi

restore_from_backup "$1"
```

## Troubleshooting

### 🚨 Problemas Comunes y Soluciones

#### 1. Notificaciones No Se Envían

**Síntomas:**
- Notificaciones quedan en estado `PENDIENTE`
- Scheduler aparece como ejecutándose
- No errores obvios en logs

**Diagnóstico:**
```bash
# Verificar notificaciones pendientes
curl -s -H "X-API-Key: $API_KEY" \
  "https://api.valoraciones.com/api/notifications?estado=PENDIENTE&limite=10" | \
  jq '.total'

# Verificar scheduler
curl -s -H "X-API-Key: $API_KEY" \
  "https://api.valoraciones.com/api/notifications/scheduler/status" | \
  jq '.data.scheduler_running'

# Verificar WhatsApp API
curl -s -H "Authorization: Bearer $WHATSAPP_ACCESS_TOKEN" \
  "https://graph.facebook.com/v18.0/$WHATSAPP_PHONE_NUMBER_ID" | \
  jq '.error // "OK"'
```

**Soluciones:**
```bash
# 1. Forzar procesamiento de cola
curl -X POST -H "X-API-Key: $API_KEY" \
  "https://api.valoraciones.com/api/notifications/process-pending?limit=50"

# 2. Reiniciar scheduler
sudo systemctl restart whatsapp-scheduler

# 3. Verificar tokens WhatsApp
echo "Verificar WHATSAPP_ACCESS_TOKEN y WHATSAPP_PHONE_NUMBER_ID"

# 4. Verificar rate limits
curl -s -H "Authorization: Bearer $WHATSAPP_ACCESS_TOKEN" \
  "https://graph.facebook.com/v18.0/$WHATSAPP_PHONE_NUMBER_ID" | \
  jq '.rate_limit'
```

#### 2. High Error Rate en Entregas

**Síntomas:**
- Tasa de error > 5%
- Muchas notificaciones en estado `ERROR`
- Logs muestran errores de WhatsApp API

**Diagnóstico:**
```bash
# Top errores de WhatsApp
grep "WHATSAPP_ERROR" /var/log/whatsapp-notifications/*.log | \
  jq -r '.context.whatsapp_error_code' | \
  sort | uniq -c | sort -rn

# Números telefónicos problemáticos  
grep "Invalid phone" /var/log/whatsapp-notifications/*.log | \
  jq -r '.context.phone_number' | \
  sort | uniq -c | sort -rn
```

**Soluciones:**
```bash
# 1. Limpiar números inválidos
curl -X POST -H "X-API-Key: $API_KEY" \
  "https://api.valoraciones.com/admin/contacts/validate-phones"

# 2. Verificar configuración de horarios
curl -s -H "X-API-Key: $API_KEY" \
  "https://api.valoraciones.com/api/notifications/templates" | \
  jq '[.[] | select(.activo == true)] | length'

# 3. Verificar rate limits y ajustar
echo "Revisar WHATSAPP_RATE_LIMIT_PER_MINUTE en configuración"
```

#### 3. Performance Lento

**Síntomas:**
- Response time > 500ms
- Timeouts en requests
- CPU/Memory alto

**Diagnóstico:**
```bash
# Verificar queries lentas
grep "duration_ms" /var/log/whatsapp-notifications/*.log | \
  jq 'select(.context.duration_ms > 1000)' | \
  jq '.context.endpoint' | \
  sort | uniq -c | sort -rn

# Verificar conexiones de DB
curl -s "https://api.valoraciones.com/health" | \
  jq '.components.database'

# Verificar cache hit rate
curl -s "https://api.valoraciones.com/health" | \
  jq '.components.cache.hit_rate'
```

**Soluciones:**
```bash
# 1. Optimizar base de datos
/opt/scripts/reindex_database.sh

# 2. Limpiar cache
redis-cli -u "$REDIS_URL" FLUSHALL

# 3. Reiniciar servicio con más memoria
sudo systemctl edit whatsapp-notifications
# [Service]
# Environment="MEMORY_LIMIT=1G"

# 4. Verificar índices faltantes
echo "Revisar queries en logs para índices faltantes"
```

#### 4. Webhook Failures

**Síntomas:**
- WhatsApp reporta webhook down
- Estados de mensaje no se actualizan
- 403/500 errors en webhook endpoint

**Diagnóstico:**
```bash
# Verificar webhook endpoint
curl -s "https://api.valoraciones.com/api/notifications/webhook" \
  -H "Content-Type: application/json" \
  -d '{"hub.mode":"subscribe","hub.verify_token":"'$WHATSAPP_VERIFY_TOKEN'","hub.challenge":"test"}'

# Verificar logs de webhook
grep "webhook" /var/log/whatsapp-notifications/*.log | tail -20

# Verificar configuración en Meta
echo "Verificar webhook URL y token en Meta for Developers"
```

**Soluciones:**
```bash
# 1. Verificar token de verificación
echo "WHATSAPP_VERIFY_TOKEN debe coincidir con Meta config"

# 2. Verificar SSL certificate
curl -I "https://api.valoraciones.com/api/notifications/webhook"

# 3. Test webhook manualmente
curl -X POST "https://api.valoraciones.com/api/notifications/webhook" \
  -H "Content-Type: application/json" \
  -d '{
    "entry": [{
      "changes": [{
        "field": "messages",
        "value": {
          "statuses": [{
            "id": "test_message_id",
            "status": "delivered",
            "timestamp": "'$(date +%s)'"
          }]
        }
      }]
    }]
  }'
```

### 🛠️ Herramientas de Diagnóstico

#### Script de Diagnóstico Completo
```bash
#!/bin/bash
# /opt/scripts/system_diagnosis.sh

API_URL="https://api.valoraciones.com"
API_KEY="$MONITORING_API_KEY"
REPORT_FILE="/tmp/system_diagnosis_$(date +%Y%m%d_%H%M%S).txt"

run_diagnosis() {
    echo "=== DIAGNÓSTICO SISTEMA WHATSAPP NOTIFICATIONS ===" > "$REPORT_FILE"
    echo "Fecha: $(date)" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
    
    # 1. Health Check
    echo "1. HEALTH CHECK:" >> "$REPORT_FILE"
    local health=$(curl -s "$API_URL/health")
    echo "$health" | jq '.' >> "$REPORT_FILE" 2>/dev/null || echo "$health" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
    
    # 2. Notificaciones Pendientes
    echo "2. NOTIFICACIONES PENDIENTES:" >> "$REPORT_FILE"
    local pending=$(curl -s -H "X-API-Key: $API_KEY" "$API_URL/api/notifications?estado=PENDIENTE&limite=1")
    local pending_count=$(echo "$pending" | jq -r '.total // "ERROR"')
    echo "Total pendientes: $pending_count" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
    
    # 3. Errores Recientes
    echo "3. ERRORES ÚLTIMAS 24 HORAS:" >> "$REPORT_FILE"
    local errors=$(curl -s -H "X-API-Key: $API_KEY" "$API_URL/api/notifications?estado=ERROR&limite=5")
    echo "$errors" | jq -r '.notificaciones[]? | "\(.created_at) - \(.ultimo_error)"' >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
    
    # 4. Métricas de Performance
    echo "4. MÉTRICAS PERFORMANCE:" >> "$REPORT_FILE"
    local metrics=$(curl -s -H "X-API-Key: $API_KEY" "$API_URL/api/notifications/metrics")
    echo "Tasa de éxito: $(echo "$metrics" | jq -r '.tasa_exito_porcentaje')%" >> "$REPORT_FILE"
    echo "Total notificaciones: $(echo "$metrics" | jq -r '.total_notificaciones')" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
    
    # 5. Status Scheduler
    echo "5. SCHEDULER STATUS:" >> "$REPORT_FILE"
    local scheduler=$(curl -s -H "X-API-Key: $API_KEY" "$API_URL/api/notifications/scheduler/status")
    echo "$scheduler" | jq '.data.scheduler_running, .data.last_execution' >> "$REPORT_FILE" 2>/dev/null
    echo "" >> "$REPORT_FILE"
    
    # 6. Disk Space
    echo "6. DISK SPACE:" >> "$REPORT_FILE"
    df -h /var/log >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
    
    # 7. Memory Usage
    echo "7. MEMORY USAGE:" >> "$REPORT_FILE"
    free -h >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
    
    # 8. Process Status
    echo "8. PROCESS STATUS:" >> "$REPORT_FILE"
    ps aux | grep -E "(whatsapp|notification)" | grep -v grep >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
    
    echo "Diagnóstico completado: $REPORT_FILE"
}

# Función para envío automático de diagnóstico
send_diagnosis() {
    local severity="$1"  # INFO, WARNING, CRITICAL
    
    # Enviar por email
    if command -v mail >/dev/null 2>&1; then
        mail -s "[$severity] Sistema WhatsApp - Diagnóstico $(date +%Y-%m-%d)" \
             admin@empresa.com < "$REPORT_FILE"
    fi
    
    # Enviar a Slack
    local emoji="ℹ️"
    [ "$severity" = "WARNING" ] && emoji="⚠️"
    [ "$severity" = "CRITICAL" ] && emoji="🚨"
    
    curl -X POST -H 'Content-type: application/json' \
        --data "{\"text\":\"$emoji Diagnóstico Sistema WhatsApp\\nVer archivo adjunto para detalles completos\"}" \
        "$WEBHOOK_SLACK"
}

# Ejecutar diagnóstico
run_diagnosis

# Determinar severidad basada en métricas
pending_count=$(curl -s -H "X-API-Key: $API_KEY" "$API_URL/api/notifications?estado=PENDIENTE&limite=1" | jq -r '.total // 0')
error_rate=$(curl -s -H "X-API-Key: $API_KEY" "$API_URL/api/notifications/metrics" | jq -r '.tasa_error_porcentaje // 0')

if (( $(echo "$pending_count > 100" | bc -l) )) || (( $(echo "$error_rate > 10" | bc -l) )); then
    send_diagnosis "CRITICAL"
elif (( $(echo "$pending_count > 50" | bc -l) )) || (( $(echo "$error_rate > 5" | bc -l) )); then
    send_diagnosis "WARNING"  
else
    send_diagnosis "INFO"
fi
```

## Alertas y Notificaciones

### 🚨 Sistema de Alertas

#### Configuración de Alertas
```yaml
# /etc/whatsapp-notifications/alerts.yml
alerts:
  system_down:
    condition: "health_status != 'healthy'"
    severity: "critical"
    cooldown: "5m"
    channels: ["slack", "email", "sms"]
    
  high_error_rate:
    condition: "error_rate_percentage > 5"
    severity: "warning"
    cooldown: "15m"
    channels: ["slack", "email"]
    
  queue_backup:
    condition: "pending_notifications > 100"
    severity: "warning" 
    cooldown: "10m"
    channels: ["slack"]
    
  whatsapp_api_down:
    condition: "whatsapp_api_status != 'healthy'"
    severity: "critical"
    cooldown: "5m"
    channels: ["slack", "email", "sms"]
    
  disk_space_low:
    condition: "disk_usage_percentage > 85"
    severity: "warning"
    cooldown: "30m"
    channels: ["slack", "email"]
```

#### Script de Procesamiento de Alertas
```bash
#!/bin/bash
# /opt/scripts/process_alerts.sh

ALERTS_CONFIG="/etc/whatsapp-notifications/alerts.yml"
ALERTS_STATE="/var/lib/whatsapp-notifications/alerts_state.json"
LOG_FILE="/var/log/whatsapp-notifications/alerts.log"

# Crear archivo de estado si no existe
[ ! -f "$ALERTS_STATE" ] && echo "{}" > "$ALERTS_STATE"

check_system_health() {
    local health=$(curl -s "$API_URL/health")
    local status=$(echo "$health" | jq -r '.status')
    
    if [ "$status" != "healthy" ]; then
        trigger_alert "system_down" "Sistema no saludable: $status" "critical"
    fi
}

check_error_rate() {
    local metrics=$(curl -s -H "X-API-Key: $API_KEY" "$API_URL/api/notifications/metrics")
    local error_rate=$(echo "$metrics" | jq -r '.tasa_error_porcentaje // 0')
    
    if (( $(echo "$error_rate > 5" | bc -l) )); then
        trigger_alert "high_error_rate" "Tasa de error alta: ${error_rate}%" "warning"
    fi
}

check_queue_backup() {
    local pending=$(curl -s -H "X-API-Key: $API_KEY" "$API_URL/api/notifications?estado=PENDIENTE&limite=1")
    local count=$(echo "$pending" | jq -r '.total // 0')
    
    if [ "$count" -gt 100 ]; then
        trigger_alert "queue_backup" "Cola de notificaciones alta: $count pendientes" "warning"
    fi
}

trigger_alert() {
    local alert_type="$1"
    local message="$2" 
    local severity="$3"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    # Verificar cooldown
    local last_alert=$(jq -r ".\"$alert_type\".last_sent // 0" "$ALERTS_STATE")
    local current_time=$(date +%s)
    local cooldown=300  # 5 minutos por defecto
    
    if [ $((current_time - last_alert)) -lt $cooldown ]; then
        return  # En cooldown, no enviar
    fi
    
    # Log de alerta
    echo "[$timestamp] ALERT [$severity] $alert_type: $message" >> "$LOG_FILE"
    
    # Enviar notificaciones
    case "$severity" in
        "critical")
            send_slack_alert "🚨 CRÍTICO" "$message"
            send_email_alert "[CRÍTICO]" "$message"
            ;;
        "warning")
            send_slack_alert "⚠️ ADVERTENCIA" "$message"
            send_email_alert "[ADVERTENCIA]" "$message"
            ;;
        "info")
            send_slack_alert "ℹ️ INFO" "$message"
            ;;
    esac
    
    # Actualizar estado de alertas
    local temp_file=$(mktemp)
    jq ".\"$alert_type\".last_sent = $current_time" "$ALERTS_STATE" > "$temp_file"
    mv "$temp_file" "$ALERTS_STATE"
}

send_slack_alert() {
    local emoji="$1"
    local message="$2"
    
    curl -X POST -H 'Content-type: application/json' \
        --data "{\"text\":\"$emoji WhatsApp Notifications\\n$message\"}" \
        "$WEBHOOK_SLACK" >/dev/null 2>&1
}

send_email_alert() {
    local subject="$1"
    local body="$2"
    
    if command -v mail >/dev/null 2>&1; then
        echo "$body" | mail -s "$subject WhatsApp Notifications - $(date)" admin@empresa.com
    fi
}

# Ejecutar todas las verificaciones
check_system_health
check_error_rate
check_queue_backup

# Configurar cron para ejecutar cada 5 minutos
# */5 * * * * /opt/scripts/process_alerts.sh
```

## Performance Tuning

### 🚀 Optimización de Rendimiento

#### Configuración de Producción
```bash
# /etc/whatsapp-notifications/production.conf

# API Server
export WORKERS=4
export MAX_CONNECTIONS=1000
export KEEPALIVE_TIMEOUT=5
export REQUEST_TIMEOUT=30

# Database
export DB_POOL_SIZE=20
export DB_POOL_MAX_OVERFLOW=10
export DB_POOL_TIMEOUT=30
export DB_POOL_RECYCLE=3600

# Cache
export REDIS_MAX_CONNECTIONS=20
export REDIS_TIMEOUT=10
export CACHE_TTL=300

# WhatsApp API
export WHATSAPP_RATE_LIMIT_PER_MINUTE=1000
export WHATSAPP_TIMEOUT=30
export WHATSAPP_RETRY_ATTEMPTS=3

# Background Jobs
export SCHEDULER_WORKERS=2
export BATCH_SIZE=50
export PROCESSING_INTERVAL=30
```

#### Monitoring Avanzado con Prometheus
```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'whatsapp-notifications'
    static_configs:
      - targets: ['api.valoraciones.com:8000']
    metrics_path: '/metrics'
    scrape_interval: 30s
    
rule_files:
  - "whatsapp_alerts.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093
```

```yaml
# whatsapp_alerts.yml
groups:
- name: whatsapp-notifications
  rules:
  - alert: HighErrorRate
    expr: whatsapp_error_rate_percentage > 5
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "Alta tasa de error en notificaciones WhatsApp"
      
  - alert: QueueBacklog
    expr: whatsapp_pending_notifications > 100
    for: 10m
    labels:
      severity: warning
    annotations:
      summary: "Cola de notificaciones acumulándose"
      
  - alert: APIDown
    expr: up{job="whatsapp-notifications"} == 0
    for: 2m
    labels:
      severity: critical
    annotations:
      summary: "API WhatsApp Notifications no disponible"
```

### 📊 Dashboard con Grafana
```json
{
  "dashboard": {
    "title": "WhatsApp Notifications - Production Dashboard",
    "panels": [
      {
        "title": "Notifications Sent (Rate)",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(whatsapp_notifications_sent_total[5m])",
            "legendFormat": "Notifications/sec"
          }
        ]
      },
      {
        "title": "Success Rate",
        "type": "singlestat",
        "targets": [
          {
            "expr": "whatsapp_success_rate_percentage",
            "legendFormat": "Success %"
          }
        ]
      },
      {
        "title": "Response Time",
        "type": "graph", 
        "targets": [
          {
            "expr": "whatsapp_response_time_ms",
            "legendFormat": "Response Time (ms)"
          }
        ]
      },
      {
        "title": "Queue Size",
        "type": "graph",
        "targets": [
          {
            "expr": "whatsapp_pending_notifications",
            "legendFormat": "Pending Notifications"
          }
        ]
      }
    ]
  }
}
```

## Procedimientos de Emergencia

### 🚑 Plan de Respuesta a Incidentes

#### Severidad 1: Sistema Completamente Caído
```bash
# Procedimiento de emergencia - Severidad 1

# 1. Verificación inicial
curl -f https://api.valoraciones.com/health || echo "Sistema caído confirmado"

# 2. Verificar logs críticos
tail -100 /var/log/whatsapp-notifications/error.log

# 3. Verificar servicios del sistema
systemctl status whatsapp-notifications
systemctl status whatsapp-scheduler
systemctl status redis
systemctl status nginx

# 4. Reinicio de servicios (escalación)
sudo systemctl restart whatsapp-notifications
sudo systemctl restart whatsapp-scheduler

# 5. Verificar conectividad externa
curl -f https://graph.facebook.com/v18.0/me -H "Authorization: Bearer $WHATSAPP_ACCESS_TOKEN"

# 6. Rollback si es necesario (último recurso)
# git checkout HEAD~1
# sudo systemctl restart whatsapp-notifications

# 7. Notificar equipo de emergencia
send_emergency_notification "Sistema completamente caído - Investigando"
```

#### Severidad 2: Degradación de Servicio
```bash
# Procedimiento - Severidad 2

# 1. Identificar componente problemático
/opt/scripts/system_diagnosis.sh

# 2. Verificar métricas específicas
curl -s -H "X-API-Key: $API_KEY" "https://api.valoraciones.com/api/notifications/metrics" | jq

# 3. Acciones correctivas basadas en componente:

# Si es problema de queue:
curl -X POST -H "X-API-Key: $API_KEY" \
  "https://api.valoraciones.com/api/notifications/process-pending?limit=200"

# Si es problema de DB:
/opt/scripts/reindex_database.sh

# Si es problema de cache:
redis-cli -u "$REDIS_URL" FLUSHALL

# Si es problema de WhatsApp API:
# Verificar tokens y rate limits, contactar soporte Meta si necesario
```

#### Contactos de Emergencia
```
Equipo DevOps:
- Primario: +51987654321 (Juan DevOps)
- Secundario: +51976543210 (María SysAdmin) 

Equipo Desarrollo:
- Líder Técnico: +51965432109 (Carlos Tech Lead)
- Backend Developer: +51954321098 (Ana Backend)

Proveedores Externos:
- Soporte Turso: support@turso.tech
- Soporte Meta/WhatsApp: business.facebook.com/help
- Hosting Provider: soporte@empresa-hosting.com

Escalación Ejecutiva:
- CTO: +51943210987 (Roberto CTO)
- Head of Operations: +51932109876 (Patricia Ops)
```

## Conclusión

Este manual de operaciones proporciona las herramientas y procedimientos necesarios para mantener el Sistema de Notificaciones WhatsApp funcionando de manera óptima en producción. 

### Checklist Diario del Administrador
- [ ] Revisar health check matutino
- [ ] Verificar métricas de la noche anterior
- [ ] Revisar logs de errores
- [ ] Confirmar backups exitosos
- [ ] Verificar cola de notificaciones
- [ ] Revisar alertas activas

### Recursos Adicionales
- [Documentación de WhatsApp Business API](https://developers.facebook.com/docs/whatsapp)
- [Guía de Turso](https://docs.turso.tech/)  
- [Manual de FastAPI](https://fastapi.tiangolo.com/)
- [Documentación de Redis](https://redis.io/documentation)

---

**Manual de Operaciones v1.0** - Sistema de Notificaciones WhatsApp  
*Última actualización: 23 de Enero 2025*

**¿Necesitas soporte operativo?** Contacta al equipo DevOps en ops-team@empresa.com