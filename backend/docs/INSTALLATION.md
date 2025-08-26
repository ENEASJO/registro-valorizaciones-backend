# Guía de Instalación y Configuración - Sistema de Notificaciones WhatsApp

## Descripción General

Esta guía te llevará paso a paso por la instalación completa del Sistema de Notificaciones WhatsApp, desde los prerrequisitos hasta tener el sistema funcionando en producción. El proceso completo toma aproximadamente **30-45 minutos** para un desarrollador experimentado.

## Prerrequisitos Técnicos

### Requisitos del Sistema
```bash
# Sistema Operativo
Ubuntu 20.04+ / macOS 11+ / Windows 11 + WSL2

# Python
Python 3.9+ (recomendado: Python 3.11)
pip 21.0+
virtualenv o conda

# Base de Datos
Turso Account (SQLite cloud)
Alternativa: SQLite local para desarrollo

# Servicios Externos
WhatsApp Business API (Meta for Developers)
Redis 6.0+ (para cache y background jobs)
```

### Cuentas y Servicios Requeridos

#### 1. WhatsApp Business API
1. **Crear cuenta en Meta for Developers**
   - Ir a https://developers.facebook.com/
   - Crear una aplicación de tipo "Business"
   - Añadir producto "WhatsApp Business API"

2. **Configurar número de teléfono**
   - Registrar número de teléfono empresarial
   - Verificar número via SMS/llamada
   - Completar verificación de negocio

3. **Obtener credenciales**
   ```bash
   WHATSAPP_ACCESS_TOKEN="EAAxxxxxxxxxxxx"
   WHATSAPP_PHONE_NUMBER_ID="123456789012345"  
   WHATSAPP_VERIFY_TOKEN="tu_token_custom_aqui"
   ```

#### 2. Turso Database (Recomendado)
1. **Crear cuenta en Turso**
   - Ir a https://turso.tech/
   - Crear cuenta gratuita
   - Crear nueva base de datos

2. **Obtener credenciales**
   ```bash
   turso auth login
   turso db create valoraciones-whatsapp
   turso db show valoraciones-whatsapp
   ```

3. **Generar token de acceso**
   ```bash
   turso db tokens create valoraciones-whatsapp
   ```

#### 3. Redis (Para producción)
```bash
# Opción 1: Redis Cloud (recomendado)
# Crear cuenta en https://redis.io/try-free/
# Obtener REDIS_URL

# Opción 2: Redis local
sudo apt install redis-server
redis-server --daemonize yes
```

## Instalación Local (Desarrollo)

### Paso 1: Preparar Entorno
```bash
# Clonar repositorio
git clone <repository-url>
cd valoraciones-backend-clean

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# Actualizar pip
pip install --upgrade pip

# Instalar dependencias
pip install -r requirements.txt
```

### Paso 2: Configurar Variables de Entorno
```bash
# Crear archivo de configuración
cp .env.example .env

# Editar configuración
nano .env
```

#### Configuración .env Completa
```bash
# === CONFIGURACIÓN BÁSICA ===
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG
API_TITLE="Sistema Notificaciones WhatsApp"
API_VERSION="1.0.0"

# === BASE DE DATOS ===
# Turso (Producción)
TURSO_DATABASE_URL="libsql://valoraciones-whatsapp-usuario.turso.io"  
TURSO_AUTH_TOKEN="eyJhbGciOiJFZERTQSIs..."

# SQLite Local (Desarrollo)
# DATABASE_URL="sqlite:///./whatsapp_notifications.db"

# === WHATSAPP BUSINESS API ===
WHATSAPP_API_URL="https://graph.facebook.com/v18.0"
WHATSAPP_ACCESS_TOKEN="EAAxxxxxxxxxxxxxxxxx"
WHATSAPP_PHONE_NUMBER_ID="123456789012345"
WHATSAPP_VERIFY_TOKEN="mi_token_verificacion_custom"

# Configuración de límites
WHATSAPP_RATE_LIMIT_PER_MINUTE=100
WHATSAPP_RETRY_ATTEMPTS=3
WHATSAPP_RETRY_DELAY_SECONDS=30

# Configuración de horarios
WHATSAPP_WORK_HOURS_START="08:00"
WHATSAPP_WORK_HOURS_END="18:00"
WHATSAPP_TIMEZONE="America/Lima"

# === REDIS (CACHE Y BACKGROUND JOBS) ===
# Redis Cloud
REDIS_URL="redis://default:password@redis-server:6379"

# Redis Local  
# REDIS_URL="redis://localhost:6379/0"

# === SEGURIDAD ===
JWT_SECRET_KEY="tu-jwt-secret-key-super-seguro-aqui"
JWT_ALGORITHM="HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60

# API Keys para autenticación
API_KEY_PREFIX="wn_api"
API_KEYS="wn_api_dev_12345:desarrollo,wn_api_prod_67890:produccion"

# === BACKGROUND TASKS ===
BACKGROUND_TASKS_ENABLED=true
SCHEDULER_INTERVAL_SECONDS=60
METRICS_CALCULATION_ENABLED=true

# === LOGGING Y MONITORING ===
LOG_FORMAT=json  # json | console
LOG_FILE_ENABLED=true
LOG_FILE_PATH="./logs/whatsapp-notifications.log"

# Tracing distribuido (opcional)
TRACING_ENABLED=false
JAEGER_ENDPOINT="http://jaeger:14268"

# === RATE LIMITING ===
RATE_LIMITING_ENABLED=true
RATE_LIMIT_REDIS_URL="${REDIS_URL}"

# === CORS (para frontend) ===
CORS_ORIGINS="http://localhost:3000,https://valoraciones.empresa.com"
CORS_CREDENTIALS=true
CORS_METHODS="GET,POST,PUT,DELETE"
CORS_HEADERS="*"
```

### Paso 3: Inicializar Base de Datos
```bash
# Crear directorio para logs
mkdir -p logs

# Ejecutar migración de base de datos
python sql/migrate_whatsapp_notifications.py

# Verificar instalación
python -c "
from app.core.database import get_db
from sqlalchemy import text
db = next(get_db())
result = db.execute(text('SELECT COUNT(*) FROM whatsapp_configuracion_horarios'))
print(f'Configuraciones creadas: {result.scalar()}')
db.close()
"
```

### Paso 4: Verificar Configuración WhatsApp
```bash
# Script de verificación
python -c "
import asyncio
from app.services.whatsapp_service import whatsapp_service

async def test_whatsapp():
    try:
        profile = await whatsapp_service.get_business_profile()
        print('✅ WhatsApp Business API configurado correctamente')
        print(f'   Nombre: {profile.get(\"name\", \"N/A\")}')
        print(f'   Número: {profile.get(\"display_phone_number\", \"N/A\")}')
    except Exception as e:
        print(f'❌ Error configuración WhatsApp: {e}')

asyncio.run(test_whatsapp())
"
```

### Paso 5: Iniciar Servidor de Desarrollo
```bash
# Opción 1: Uvicorn directo (recomendado desarrollo)
uvicorn main:app --reload --port 8000 --log-level debug

# Opción 2: Con script personalizado
python -m uvicorn main:app --reload --port 8000

# Opción 3: Gunicorn (para simular producción)
gunicorn main:app -w 1 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Paso 6: Verificar Instalación
```bash
# Health check básico
curl http://localhost:8000/health

# Respuesta esperada:
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-01-23T12:00:00.000000",
  "components": {
    "database": {"status": "connected"},
    "whatsapp_api": {"status": "configured"},
    "scheduler": {"status": "running"},
    "cache": {"status": "connected"}
  }
}

# Documentación interactiva
open http://localhost:8000/docs

# Enviar mensaje de prueba
curl -X POST "http://localhost:8000/api/notifications/test" \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "51987654321",
    "message": "Mensaje de prueba - Sistema configurado correctamente"
  }'
```

## Configuración de Webhook WhatsApp

### Paso 1: Configurar URL Pública
```bash
# Para desarrollo local - usar ngrok
npm install -g ngrok
ngrok http 8000

# Obtener URL pública
# https://abc123.ngrok.io -> usar como base para webhook
```

### Paso 2: Configurar Webhook en Meta
1. **Ir a Meta for Developers**
   - Seleccionar tu aplicación WhatsApp
   - Ir a "WhatsApp > Configuration > Webhooks"

2. **Configurar Webhook URL**
   ```
   URL: https://tu-dominio.com/api/notifications/webhook
   Verify Token: [mismo valor que WHATSAPP_VERIFY_TOKEN]
   ```

3. **Suscribir a Eventos**
   - `messages`: Para mensajes recibidos  
   - `message_deliveries`: Para estados de entrega
   - `message_reads`: Para confirmaciones de lectura

### Paso 3: Verificar Webhook
```bash
# El webhook debería verificarse automáticamente
# Revisar logs para confirmación
tail -f logs/whatsapp-notifications.log | grep webhook
```

## Instalación en Staging/Producción

### Usando Docker (Recomendado)

#### Paso 1: Construir Imagen
```bash
# Crear Dockerfile si no existe
cat > Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

# Crear usuario no-root
RUN useradd --create-home --shell /bin/bash app
RUN chown -R app:app /app
USER app

# Comando de inicio
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

# Construir imagen
docker build -t whatsapp-notifications:1.0.0 .
```

#### Paso 2: Docker Compose para Producción
```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  api:
    image: whatsapp-notifications:1.0.0
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
      - DEBUG=false
      - REDIS_URL=redis://redis:6379
    env_file:
      - .env.prod
    depends_on:
      - redis
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    restart: unless-stopped

  scheduler:
    image: whatsapp-notifications:1.0.0
    command: python start_whatsapp_scheduler.py
    environment:
      - ENVIRONMENT=production
      - DEBUG=false
    env_file:
      - .env.prod
    depends_on:
      - redis
      - api
    restart: unless-stopped

volumes:
  redis_data:
```

#### Paso 3: Despliegue
```bash
# Crear archivo de producción
cp .env .env.prod
# Editar .env.prod con credenciales de producción

# Inicializar base de datos de producción
ENVIRONMENT=production python sql/migrate_whatsapp_notifications.py

# Levantar servicios
docker-compose -f docker-compose.prod.yml up -d

# Verificar estado
docker-compose -f docker-compose.prod.yml ps
docker-compose -f docker-compose.prod.yml logs api
```

### Deploy en Google Cloud Run

#### Paso 1: Preparar Proyecto
```bash
# Instalar gcloud CLI
curl https://sdk.cloud.google.com | bash
gcloud auth login
gcloud config set project tu-proyecto-id

# Habilitar APIs necesarias
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable secretmanager.googleapis.com
```

#### Paso 2: Configurar Secretos
```bash
# Crear secretos para credenciales sensibles
echo -n "tu-whatsapp-access-token" | gcloud secrets create whatsapp-access-token --data-file=-
echo -n "tu-turso-auth-token" | gcloud secrets create turso-auth-token --data-file=-
echo -n "tu-jwt-secret-key" | gcloud secrets create jwt-secret-key --data-file=-
echo -n "tu-redis-url" | gcloud secrets create redis-url --data-file=-
```

#### Paso 3: Deploy con Cloud Build
```yaml
# cloudbuild.yaml
steps:
  # Build imagen
  - name: 'gcr.io/cloud-builders/docker'
    args: [
      'build', 
      '-t', 'gcr.io/$PROJECT_ID/whatsapp-notifications:$COMMIT_SHA',
      '.'
    ]

  # Push imagen
  - name: 'gcr.io/cloud-builders/docker'
    args: [
      'push', 
      'gcr.io/$PROJECT_ID/whatsapp-notifications:$COMMIT_SHA'
    ]

  # Deploy a Cloud Run
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: 'gcloud'
    args: [
      'run', 'deploy', 'whatsapp-notifications',
      '--image', 'gcr.io/$PROJECT_ID/whatsapp-notifications:$COMMIT_SHA',
      '--region', 'us-central1',
      '--platform', 'managed',
      '--allow-unauthenticated',
      '--memory', '1Gi',
      '--cpu', '1',
      '--min-instances', '1',
      '--max-instances', '10',
      '--set-env-vars', 'ENVIRONMENT=production,DEBUG=false',
      '--set-secrets', '/secrets/whatsapp-token=whatsapp-access-token:latest,/secrets/turso-token=turso-auth-token:latest,/secrets/jwt-secret=jwt-secret-key:latest,/secrets/redis-url=redis-url:latest'
    ]
```

#### Paso 4: Ejecutar Deploy
```bash
# Trigger build
gcloud builds submit --config cloudbuild.yaml

# Obtener URL de servicio
gcloud run services describe whatsapp-notifications --region us-central1 --format 'value(status.url)'
```

## Configuración de Background Jobs

### Usando Celery + Redis
```bash
# Instalar dependencias adicionales
pip install celery[redis]==5.3.4

# Configurar Celery
mkdir -p app/celery
cat > app/celery/celery_app.py << 'EOF'
from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "whatsapp_notifications",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=['app.celery.tasks']
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='America/Lima',
    enable_utc=True,
    broker_connection_retry_on_startup=True
)
EOF

# Crear tareas
cat > app/celery/tasks.py << 'EOF'
from celery import current_task
from .celery_app import celery_app
from app.services.notification_service import notification_service
from app.core.database import get_db

@celery_app.task(bind=True, name='send_pending_notifications')
def send_pending_notifications_task(self):
    db = next(get_db())
    try:
        result = notification_service.send_pending_notifications(db, limit=50)
        return result
    finally:
        db.close()

@celery_app.task(bind=True, name='calculate_daily_metrics')
def calculate_daily_metrics_task(self):
    from app.services.scheduler_service import scheduler_service
    db = next(get_db())
    try:
        result = scheduler_service.calculate_daily_metrics(db)
        return result
    finally:
        db.close()
EOF

# Iniciar worker Celery
celery -A app.celery.celery_app worker --loglevel=info

# Iniciar scheduler Celery Beat (en otra terminal)
celery -A app.celery.celery_app beat --loglevel=info
```

### Scheduler Simple (Alternativa)
```bash
# Usar el scheduler incluido
python start_whatsapp_scheduler.py

# Como servicio systemd (Linux)
sudo tee /etc/systemd/system/whatsapp-scheduler.service << 'EOF'
[Unit]
Description=WhatsApp Notifications Scheduler
After=network.target

[Service]
Type=simple
User=app
WorkingDirectory=/app
Environment=PATH=/app/venv/bin
ExecStart=/app/venv/bin/python start_whatsapp_scheduler.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable whatsapp-scheduler
sudo systemctl start whatsapp-scheduler
```

## Configuración de Monitoreo

### Logs Estructurados
```bash
# Configurar logrotate
sudo tee /etc/logrotate.d/whatsapp-notifications << 'EOF'
/app/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    create 644 app app
    postrotate
        systemctl reload whatsapp-notifications
    endscript
}
EOF
```

### Health Checks Automáticos
```bash
# Script de health check
cat > scripts/health_check.sh << 'EOF'
#!/bin/bash
HEALTH_URL="${API_URL:-http://localhost:8000}/health"
WEBHOOK_URL="https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"

response=$(curl -s -o /dev/null -w "%{http_code}" "$HEALTH_URL")

if [ "$response" != "200" ]; then
    # Enviar alerta a Slack
    curl -X POST -H 'Content-type: application/json' \
        --data '{"text":"🚨 WhatsApp Notifications API DOWN - Status: '"$response"'"}' \
        "$WEBHOOK_URL"
    
    echo "CRITICAL: API health check failed with status $response"
    exit 1
else
    echo "OK: API is healthy"
fi
EOF

chmod +x scripts/health_check.sh

# Configurar cron para monitoreo cada 5 minutos
echo "*/5 * * * * /app/scripts/health_check.sh" | crontab -
```

## Solución de Problemas Comunes

### Error: "WhatsApp Access Token inválido"
```bash
# Verificar token
curl -H "Authorization: Bearer $WHATSAPP_ACCESS_TOKEN" \
  "https://graph.facebook.com/v18.0/$WHATSAPP_PHONE_NUMBER_ID"

# Regenerar token si es necesario en Meta for Developers
```

### Error: "Database connection failed"
```bash
# Verificar conexión Turso
python -c "
import libsql_client
client = libsql_client.create_client(
    url='$TURSO_DATABASE_URL',
    auth_token='$TURSO_AUTH_TOKEN'
)
result = client.execute('SELECT 1')
print('✅ Database connected')
"

# Para SQLite local
python -c "
import sqlite3
conn = sqlite3.connect('./whatsapp_notifications.db')
cursor = conn.execute('SELECT 1')
print('✅ SQLite connected')
"
```

### Error: "Redis connection refused"
```bash
# Verificar Redis
redis-cli -u "$REDIS_URL" ping

# Respuesta esperada: PONG

# Instalar Redis localmente si es necesario
sudo apt update && sudo apt install redis-server
sudo systemctl start redis-server
```

### Performance Issues
```bash
# Verificar índices de base de datos
python -c "
from app.core.database import get_db
from sqlalchemy import text
db = next(get_db())
indexes = db.execute(text('SELECT name FROM sqlite_master WHERE type=\"index\" AND name LIKE \"idx_%\"')).fetchall()
print(f'Índices creados: {len(indexes)}')
for idx in indexes:
    print(f'  - {idx[0]}')
"

# Verificar performance de queries
python -c "
import time
from app.services.notification_service import notification_service
from app.core.database import get_db

db = next(get_db())
start = time.time()
metrics = notification_service.get_notification_metrics(db)
end = time.time()
print(f'Métricas query time: {(end-start)*1000:.2f}ms')
"
```

## Verificación Final de Instalación

### Checklist Completo
```bash
# Script de verificación completa
python << 'EOF'
import asyncio
import sys
from datetime import datetime

async def verify_installation():
    print("🔍 Verificando instalación completa...\n")
    
    # 1. Imports
    try:
        from app.core.database import get_db
        from app.services.whatsapp_service import whatsapp_service
        from app.services.notification_service import notification_service
        print("✅ Imports correctos")
    except ImportError as e:
        print(f"❌ Error en imports: {e}")
        return False
    
    # 2. Database
    try:
        db = next(get_db())
        from sqlalchemy import text
        result = db.execute(text('SELECT COUNT(*) FROM whatsapp_configuracion_horarios'))
        count = result.scalar()
        print(f"✅ Base de datos: {count} configuraciones cargadas")
        db.close()
    except Exception as e:
        print(f"❌ Error base de datos: {e}")
        return False
    
    # 3. WhatsApp API
    try:
        is_valid, formatted, error = whatsapp_service.validate_phone_number("987654321")
        if is_valid:
            print(f"✅ WhatsApp service: Validación OK")
        else:
            print(f"⚠️  WhatsApp service: {error}")
    except Exception as e:
        print(f"❌ Error WhatsApp service: {e}")
        return False
    
    # 4. Notification Service
    try:
        db = next(get_db())
        metrics = await notification_service.get_notification_metrics(db)
        print(f"✅ Notification service: Métricas disponibles")
        db.close()
    except Exception as e:
        print(f"❌ Error notification service: {e}")
        return False
    
    print(f"\n🎉 Instalación verificada exitosamente - {datetime.now()}")
    print("📚 Documentación: http://localhost:8000/docs")
    print("🏥 Health check: http://localhost:8000/health")
    return True

if __name__ == "__main__":
    success = asyncio.run(verify_installation())
    sys.exit(0 if success else 1)
EOF
```

### Test de Integración Completo
```bash
# Ejecutar test de extremo a extremo
python << 'EOF'
import asyncio
import json
from app.core.database import get_db
from app.services.notification_service import notification_service
from app.models.whatsapp_notifications import EventoTrigger

async def integration_test():
    print("🧪 Test de integración completo...\n")
    
    db = next(get_db())
    
    # Simular creación de notificación
    notifications = await notification_service.create_notification(
        db=db,
        valorizacion_id=999,
        evento_trigger=EventoTrigger.APROBADA,
        estado_actual="APROBADA",
        estado_anterior="EN_REVISION",
        variables_extra={
            "monto_total": "50000.00",
            "observaciones": "Test de integración"
        }
    )
    
    print(f"✅ Creadas {len(notifications)} notificaciones de prueba")
    
    # Verificar métricas
    metrics = await notification_service.get_notification_metrics(db)
    print(f"✅ Métricas calculadas: {metrics['totales']['total']} total")
    
    db.close()
    print("\n🎉 Test de integración exitoso!")

asyncio.run(integration_test())
EOF
```

¡Felicitaciones! 🎉 El sistema está instalado y funcionando correctamente.

## Próximos Pasos

1. **[Guía de Integración](./INTEGRATION.md)** - Integrar con tu sistema de valorizaciones
2. **[API Reference](./API_REFERENCE.md)** - Documentación completa de endpoints  
3. **[Manual de Operaciones](./OPERATIONS.md)** - Monitoreo y mantenimiento
4. **[Guía de Usuario](./USER_GUIDE.md)** - Para contratistas y coordinadores

---

**¿Necesitas ayuda?** Contacta al equipo de desarrollo en dev-team@empresa.com