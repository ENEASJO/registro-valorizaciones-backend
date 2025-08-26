# Guía de Despliegue - Sistema Consolidado SUNAT + OSCE

## Descripción del Sistema

Sistema consolidado que realiza scraping en tiempo real de:
- **SUNAT**: Consulta de datos básicos de empresas usando Playwright
- **OSCE**: Extracción de especialidades e integrantes de empresas contratistas
- **Consolidación**: Deduplicación inteligente y combinación de datos

### Características Principales

- ✅ **Scraping Real**: Playwright con Chromium para consultas auténticas
- ✅ **Consultas Paralelas**: SUNAT y OSCE en paralelo para máximo rendimiento
- ✅ **Deduplicación Inteligente**: Algoritmo de similitud para miembros/integrantes
- ✅ **Escalabilidad**: Optimizado para Google Cloud Run
- ✅ **Monitoreo Completo**: Métricas, logs y alertas configuradas
- ✅ **Alta Disponibilidad**: Timeout de 10 minutos, autoscaling automático

## Prerrequisitos

### 1. Herramientas Requeridas
```bash
# Google Cloud CLI
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
gcloud init

# Docker
# Instalar desde: https://docs.docker.com/get-docker/

# Verificar instalaciones
gcloud version
docker --version
```

### 2. Configuración de Proyecto GCP
```bash
# Configurar proyecto
export PROJECT_ID="valoraciones-sunat"  # Cambiar por tu proyecto
gcloud config set project $PROJECT_ID

# Verificar facturación habilitada
gcloud billing projects describe $PROJECT_ID

# Habilitar APIs necesarias
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

## Despliegue Paso a Paso

### Método 1: Despliegue Automático (Recomendado)

```bash
# 1. Hacer ejecutable el script
chmod +x cloud-run-deploy.sh

# 2. Ejecutar despliegue completo
./cloud-run-deploy.sh
```

El script automatiza:
- Construcción de imagen Docker optimizada
- Subida a Google Container Registry
- Despliegue con configuración optimizada
- Configuración de permisos de acceso

### Método 2: Despliegue Manual

#### Paso 1: Construir Imagen
```bash
PROJECT_ID="valoraciones-sunat"
SERVICE_NAME="valoraciones-consolidado-scraper"
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"

# Construir imagen
docker build -f Dockerfile.cloudrun -t $IMAGE_NAME .

# Subir imagen
docker push $IMAGE_NAME
```

#### Paso 2: Desplegar a Cloud Run
```bash
gcloud run deploy $SERVICE_NAME \
    --image $IMAGE_NAME \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --memory 4Gi \
    --cpu 2 \
    --timeout 600s \
    --concurrency 5 \
    --max-instances 10 \
    --min-instances 0 \
    --set-env-vars NODE_ENV=production,TZ=America/Lima \
    --execution-environment gen2
```

## Configuración de Recursos

### Especificaciones Optimizadas

| Recurso | Valor | Justificación |
|---------|-------|---------------|
| **Memoria** | 4GB | Playwright + múltiples browsers + Node.js |
| **CPU** | 2 vCPUs | Procesamiento paralelo SUNAT + OSCE |
| **Timeout** | 600s (10 min) | Consultas complejas con scraping |
| **Concurrencia** | 5 | Balance entre rendimiento y recursos |
| **Min Instancias** | 0 | Ahorro de costos en periodos inactivos |
| **Max Instancias** | 10 | Escalabilidad para picos de tráfico |

### Variables de Entorno Críticas

```bash
NODE_ENV=production
TZ=America/Lima
PLAYWRIGHT_BROWSERS_PATH=/usr/lib/playwright
NODE_OPTIONS=--max-old-space-size=1536
SUNAT_TIMEOUT=30000
OSCE_TIMEOUT=45000
CONSOLIDATION_TIMEOUT=60000
```

## Optimización Avanzada

### Ejecutar Optimizaciones Adicionales
```bash
# Hacer ejecutable el script de optimización
chmod +x cloud-run-optimize.sh

# Aplicar optimizaciones avanzadas
./cloud-run-optimize.sh
```

Aplica:
- Autoscaling optimizado
- CPU always-allocated para respuestas rápidas
- Labels para monitoreo
- Variables de entorno adicionales
- Configuración de logging estructurado

## Endpoints Disponibles

### Endpoints Principales

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/health` | GET | Health check del servicio |
| `/consulta-ruc-consolidada/{ruc}` | GET | **Consulta consolidada SUNAT + OSCE** |
| `/consulta-ruc/{ruc}` | GET | Consulta básica solo SUNAT |
| `/consulta-osce/{ruc}` | GET | Consulta individual solo OSCE |

### Ejemplos de Uso

```bash
# Health Check
curl https://your-service-url/health

# Consulta Consolidada (Principal)
curl https://your-service-url/consulta-ruc-consolidada/20160669234

# Timing de consulta
time curl https://your-service-url/consulta-ruc-consolidada/20160669234
```

### Respuesta de Consulta Consolidada

```json
{
  "success": true,
  "data": {
    "ruc": "20160669234",
    "razon_social": "SANTA ROSA SCRL",
    "contacto": {
      "telefono": "",
      "email": "",
      "direccion": "",
      "domicilio_fiscal": "PROLONGACION TACNA NRO. 408..."
    },
    "miembros": [
      {
        "nombre": "NOMBRE REPRESENTANTE",
        "cargo": "GERENTE GENERAL",
        "tipo_documento": "DNI",
        "numero_documento": "12345678",
        "fuente": "AMBOS",
        "fuentes_detalle": {
          "matching": "DNI"
        }
      }
    ],
    "especialidades": ["ESP001", "ESP002"],
    "fuentes_consultadas": ["SUNAT", "OSCE"],
    "consolidacion_exitosa": true,
    "timestamp": "2025-01-14T..."
  }
}
```

## Monitoreo y Observabilidad

### Logs en Tiempo Real
```bash
# Ver logs del servicio
gcloud run services logs tail valoraciones-consolidado-scraper --region=us-central1

# Filtrar logs de errores
gcloud run services logs tail valoraciones-consolidado-scraper --region=us-central1 --filter="severity>=ERROR"
```

### Métricas Clave a Monitorear

1. **Latencia**: P95 < 45 segundos para consultas consolidadas
2. **Error Rate**: < 5% de consultas fallidas
3. **Memoria**: Uso promedio < 80% de 4GB asignadas
4. **CPU**: Picos < 90% sostenido
5. **Instancias**: Escalado según demanda (0-10)

### Alertas Configuradas

- **Error Rate Alto**: > 10% por 5 minutos
- **Latencia Alta**: P95 > 45 segundos
- **Memoria Crítica**: > 90% por 3 minutos
- **CPU Alta**: > 80% por 10 minutos

## Troubleshooting

### Problemas Comunes

#### 1. Error de Construcción Docker
```bash
# Limpiar cache de Docker
docker system prune -a

# Reconstruir sin cache
docker build --no-cache -f Dockerfile.cloudrun -t IMAGE_NAME .
```

#### 2. Timeout en Consultas
- Verificar que el timeout esté configurado en 600s
- Revisar logs para identificar consultas específicas lentas
- Considerar aumentar recursos si es necesario

#### 3. Errores de Playwright
```bash
# Verificar logs específicos
gcloud run services logs tail SERVICE_NAME --filter="playwright"

# Verificar configuración de browser
curl https://your-service-url/health
```

#### 4. Escalado de Instancias
```bash
# Verificar configuración de autoscaling
gcloud run services describe SERVICE_NAME --region=REGION --format="export"
```

### Logs de Debug

```bash
# Habilitar logs detallados
gcloud run services update SERVICE_NAME \
    --set-env-vars DEBUG_PLAYWRIGHT=true,LOG_LEVEL=debug
```

## Costos Estimados

### Configuración Base (Uso Moderado)

- **Cómputo**: ~$15-30/mes (estimado para 1000 consultas/día)
- **Egress**: ~$5-10/mes
- **Container Registry**: ~$1-2/mes
- **Monitoring**: Incluido en tier gratuito

### Optimización de Costos

1. **Min Instances = 0**: Ahorro durante períodos inactivos
2. **CPU Throttling**: Reducir CPU cuando no esté en uso
3. **Memory Optimization**: 4GB necesarios para Playwright
4. **Request Timeout**: 10 minutos apropiado para scraping

## Seguridad

### Medidas Implementadas

1. **Usuario No-Root**: Container ejecuta con usuario `appuser`
2. **Sandboxing**: Chromium con `--no-sandbox` para Cloud Run
3. **HTTPS Only**: Todas las comunicaciones cifradas
4. **Headers de Seguridad**: Configurados automáticamente
5. **Rate Limiting**: Protección contra abuso

### Variables Sensibles

```bash
# Variables que NO deben exponerse
# (Ninguna actualmente - sistema usa scraping público)

# Variables de configuración seguras
NODE_ENV=production  # ✅ Segura
PLAYWRIGHT_BROWSERS_PATH=/usr/lib/playwright  # ✅ Segura
```

## Actualizaciones

### Despliegue de Nueva Versión

```bash
# 1. Actualizar código
# 2. Reconstruir y desplegar
./cloud-run-deploy.sh

# 3. Verificar deployment
curl https://your-service-url/health
```

### Rollback de Emergencia

```bash
# Listar revisiones
gcloud run revisions list --service=SERVICE_NAME --region=REGION

# Rollback a revisión anterior
gcloud run services update-traffic SERVICE_NAME \
    --to-revisions REVISION_NAME=100 \
    --region=REGION
```

## Soporte y Contacto

### Recursos Adicionales

- **Logs**: https://console.cloud.google.com/run/detail/us-central1/SERVICE_NAME/logs
- **Métricas**: https://console.cloud.google.com/run/detail/us-central1/SERVICE_NAME/metrics
- **Cloud Run Docs**: https://cloud.google.com/run/docs
- **Playwright Docs**: https://playwright.dev/

### Comandos de Utilidad

```bash
# Ver configuración actual
gcloud run services describe SERVICE_NAME --region=REGION

# Actualizar configuración específica
gcloud run services update SERVICE_NAME --memory=2Gi --region=REGION

# Ver todas las revisiones
gcloud run revisions list --service=SERVICE_NAME --region=REGION

# Obtener URL del servicio
gcloud run services describe SERVICE_NAME --region=REGION --format="value(status.url)"
```

---

**Versión**: 2.0  
**Última Actualización**: 2025-01-14  
**Sistema**: Consolidado SUNAT + OSCE  
**Plataforma**: Google Cloud Run + Node.js 20 + Playwright