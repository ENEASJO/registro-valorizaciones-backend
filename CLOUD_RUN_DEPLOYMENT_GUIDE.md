# Guía de Despliegue en Google Cloud Run

Esta guía te ayudará a desplegar el backend del Sistema de Valorizaciones en Google Cloud Run con integración MCP para base de datos.

## 🛠️ Prerrequisitos

### 1. Herramientas Necesarias
```bash
# Google Cloud SDK
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# Docker
# Instalar desde: https://docs.docker.com/get-docker/

# Git (para CI/CD)
sudo apt-get install git  # Ubuntu/Debian
brew install git          # macOS
```

### 2. Configuración Inicial
```bash
# Autenticar con Google Cloud
gcloud auth login

# Configurar proyecto
gcloud config set project TU-PROYECTO-ID

# Configurar región por defecto
gcloud config set compute/region us-central1
```

## 🗄️ Configuración de Base de Datos

### Opción A: Cloud SQL (Recomendado para Producción)

```bash
# 1. Crear instancia Cloud SQL
gcloud sql instances create valoraciones-db \
    --database-version=POSTGRES_14 \
    --tier=db-f1-micro \
    --region=us-central1 \
    --storage-type=SSD \
    --storage-size=10GB

# 2. Configurar contraseña del usuario postgres
gcloud sql users set-password postgres \
    --instance=valoraciones-db \
    --password=TU-PASSWORD-SEGURO

# 3. Crear base de datos
gcloud sql databases create valorizaciones \
    --instance=valoraciones-db

# 4. Obtener string de conexión
gcloud sql instances describe valoraciones-db \
    --format="value(connectionName)"
```

### Opción B: Supabase (Para Desarrollo)

1. Crear proyecto en [Supabase](https://supabase.com)
2. Obtener URL y keys del proyecto
3. Ejecutar el schema SQL desde `supabase-schema.sql`

## 🚀 Despliegue Manual

### 1. Configurar Variables de Entorno

```bash
# Copiar y editar archivo de configuración
cp server/.env.cloudrun.example server/.env

# Editar variables según tu configuración
nano server/.env
```

**Variables principales:**
```env
GOOGLE_CLOUD_PROJECT=tu-proyecto-id
GOOGLE_CLOUD_REGION=us-central1
CLOUD_SQL_INSTANCE_NAME=valoraciones-db
CLOUD_SQL_DATABASE_NAME=valorizaciones
CLOUD_SQL_USER=postgres
CLOUD_SQL_PASSWORD=tu-password-seguro
```

### 2. Ejecutar Script de Despliegue

```bash
# Ir al directorio del servidor
cd server

# Ejecutar script de despliegue
./deploy-cloudrun.sh
```

### 3. Verificar Despliegue

El script mostrará la URL del servicio desplegado. Verifica los endpoints:

- **Health Check**: `https://tu-servicio.run.app/health`
- **MCP Manifest**: `https://tu-servicio.run.app/mcp/manifest`
- **API Documentation**: `https://tu-servicio.run.app/docs`

## 🔄 CI/CD Automático con Cloud Build

### 1. Configurar Cloud Build

```bash
# Habilitar API de Cloud Build
gcloud services enable cloudbuild.googleapis.com

# Crear trigger de Cloud Build
gcloud builds triggers create github \
    --repo-name=tu-repositorio \
    --repo-owner=tu-usuario \
    --branch-pattern="^main$" \
    --build-config=server/cloudbuild.yaml
```

### 2. Configurar Variables de Build

En la consola de Google Cloud, configura las variables de sustitución en Cloud Build:

- `_REGION`: us-central1
- `_CLOUD_SQL_INSTANCE`: valoraciones-db
- `_DATABASE_NAME`: valorizaciones

### 3. Configurar Secrets

Para variables sensibles, usa Secret Manager:

```bash
# Crear secrets
echo -n "tu-password-seguro" | gcloud secrets create cloud-sql-password --data-file=-

# Otorgar permisos a Cloud Build
gcloud projects add-iam-policy-binding TU-PROYECTO-ID \
    --member="serviceAccount@cloudbuild.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

## 🧪 Configuración del MCP

### 1. Verificar MCP Tools

Una vez desplegado, verifica que el MCP esté funcionando:

```bash
# Obtener manifiesto MCP
curl https://tu-servicio.run.app/mcp/manifest

# Verificar health del MCP
curl https://tu-servicio.run.app/mcp/health

# Obtener estadísticas
curl https://tu-servicio.run.app/mcp/stats
```

### 2. Usar MCP Tools

Los siguientes endpoints MCP están disponibles:

- **Consultar Empresas**: `GET /mcp/empresas?ruc=20123456789`
- **Consultar Obras**: `GET /mcp/obras?estado=en_ejecucion`
- **Consultar Valorizaciones**: `GET /mcp/valorizaciones?obra_id=uuid`
- **Ejecutar Query SQL**: `POST /mcp/query`

### 3. Ejemplo de Uso en Claude Code

Para configurar el MCP en Claude Code:

```json
{
  "mcpServers": {
    "valoraciones-db": {
      "command": "npx",
      "args": ["@modelcontextprotocol/server-fetch"],
      "env": {
        "FETCH_BASE_URL": "https://tu-servicio.run.app/mcp"
      }
    }
  }
}
```

## 🔧 Configuración del Frontend

### 1. Actualizar Variables de Entorno en Vercel

En tu proyecto de Vercel, configura:

```env
VITE_API_BASE_URL=https://tu-servicio.run.app
VITE_MCP_BASE_URL=https://tu-servicio.run.app/mcp
```

### 2. Actualizar CORS

El backend ya está configurado para aceptar requests desde Vercel. Si necesitas dominios adicionales, actualiza las variables de entorno:

```env
ALLOWED_ORIGINS=https://tu-frontend.vercel.app,https://otro-dominio.com
```

## 🐛 Troubleshooting

### Problemas Comunes

1. **Error de autenticación con Cloud SQL**
   ```bash
   # Verificar que el servicio tenga permisos
   gcloud projects add-iam-policy-binding TU-PROYECTO-ID \
       --member="serviceAccount:tu-servicio@tu-proyecto.iam.gserviceaccount.com" \
       --role="roles/cloudsql.client"
   ```

2. **Timeout en requests de scraping**
   - Aumentar memoria y CPU en Cloud Run
   - Verificar que Playwright esté instalado correctamente

3. **MCP no responde**
   - Verificar variables de base de datos
   - Revisar logs de Cloud Run

### Comandos de Diagnóstico

```bash
# Ver logs del servicio
gcloud run services logs read valoraciones-backend --region=us-central1

# Ver logs en tiempo real
gcloud run services logs tail valoraciones-backend --region=us-central1

# Describir servicio
gcloud run services describe valoraciones-backend --region=us-central1

# Probar conexión a base de datos
gcloud sql connect valoraciones-db --user=postgres
```

## 📊 Monitoreo

### 1. Métricas de Cloud Run

En la consola de Google Cloud, puedes monitorear:
- Requests por minuto
- Latencia
- Errores
- Uso de CPU y memoria

### 2. Logs Estructurados

El backend genera logs estructurados que puedes consultar:

```bash
# Filtrar por severity
gcloud logging read 'resource.type="cloud_run_revision" AND severity="ERROR"'

# Filtrar por MCP
gcloud logging read 'resource.type="cloud_run_revision" AND textPayload:"MCP"'
```

## 🔐 Seguridad

### 1. IAM y Permisos

- El servicio usa la cuenta de servicio por defecto de Cloud Run
- Solo necesita permisos para Cloud SQL
- El acceso público está habilitado para la API

### 2. Secrets Management

- Usa Google Secret Manager para contraseñas
- No hardcodees secrets en el código
- Rota las contraseñas regularmente

### 3. Network Security

- Cloud Run está detrás de Google's Load Balancer
- SSL/TLS automático
- DDoS protection incluido

## 📈 Escalamiento

### 1. Configuración de Instancias

```bash
# Actualizar configuración de escalamiento
gcloud run services update valoraciones-backend \
    --min-instances=1 \
    --max-instances=50 \
    --concurrency=100 \
    --region=us-central1
```

### 2. Optimización de Performance

- Usar conexión pooling para la base de datos
- Implementar cache para consultas frecuentes
- Optimizar queries SQL

## 🎉 ¡Listo!

Tu backend ahora está desplegado en Google Cloud Run con:

✅ **MCP Server** para base de datos  
✅ **Auto-escalamiento** según demanda  
✅ **SSL/TLS** automático  
✅ **Integración** con Cloud SQL  
✅ **Monitoreo** y logs integrados  
✅ **CI/CD** con Cloud Build  

El MCP está listo para usar en Claude Code y el frontend puede consumir la API desde Vercel.