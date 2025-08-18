# Pasos para Desplegar Backend de Valoraciones en Google Cloud Run

## PASO 1: Autenticación con Google Cloud

1. **Abrir una nueva terminal** y navegar al directorio del proyecto:
```bash
cd "/home/joeleneas/Desktop/PROYECTOS/REGISTRO DE VALORIZACIONES/valoraciones-app/server"
```

2. **Configurar PATH para gcloud**:
```bash
export PATH="./google-cloud-sdk/bin:$PATH"
```

3. **Autenticarse con Google Cloud**:
```bash
gcloud auth login
```
   - Se abrirá un navegador web
   - Inicia sesión con tu cuenta de Google que tiene acceso al proyecto
   - Autoriza el acceso cuando se solicite

4. **Configurar el proyecto**:
```bash
gcloud config set project valoraciones-app-cloud-run
gcloud config set compute/region us-central1
```

5. **Verificar configuración**:
```bash
gcloud config list
```

## PASO 2: Ejecutar el Despliegue

Una vez autenticado, ejecuta el script de despliegue:

```bash
./deploy-valoraciones-cloudrun.sh
```

## PASO 3: Configuración del Proyecto (Si es necesario)

Si el proyecto "valoraciones-app-cloud-run" no existe, créalo:

```bash
gcloud projects create valoraciones-app-cloud-run --name="Valoraciones App Cloud Run"
```

Luego habilita la facturación (requerido para Cloud Run):
- Ve a la Consola de Google Cloud
- Selecciona el proyecto "valoraciones-app-cloud-run"
- Ve a "Facturación" y vincula una cuenta de facturación

## PASO 4: Verificación Post-Despliegue

El script automáticamente:
- ✅ Construye la imagen Docker usando `Dockerfile.cloudrun`
- ✅ Sube la imagen a Google Container Registry
- ✅ Despliega en Cloud Run con la configuración especificada:
  - Memoria: 4Gi
  - CPU: 2
  - Puerto: 8080
  - Concurrencia: 50
  - Max instancias: 10
  - Timeout: 900s
  - Allow unauthenticated: true
- ✅ Verifica el funcionamiento del servicio
- ✅ Proporciona la URL final para configuración MCP

## Configuración Específica Aplicada

```bash
--memory 4Gi \
--cpu 2 \
--max-instances 10 \
--min-instances 0 \
--concurrency 50 \
--timeout 900 \
--port 8080 \
--execution-environment gen2 \
--allow-unauthenticated \
--set-env-vars "ENVIRONMENT=production,BROWSER_HEADLESS=true,PLAYWRIGHT_BROWSERS_PATH=/home/app/.cache/ms-playwright"
```

## URLs Resultantes

Una vez desplegado, tendrás acceso a:

- **URL base**: `https://valoraciones-backend-[hash]-uc.a.run.app`
- **Health check**: `/health`
- **MCP Manifest**: `/mcp/manifest`
- **MCP Health**: `/mcp/health`
- **Endpoints MCP**: `/mcp/empresas`, `/mcp/obras`, `/mcp/valorizaciones`, `/mcp/query`, `/mcp/stats`
- **Web Scraping**: `/consulta-ruc/{ruc}`, `/consulta-osce/{ruc}`, `/consulta-ruc-consolidada/{ruc}`

## Troubleshooting

Si encuentras errores:

1. **Error de autenticación**:
```bash
gcloud auth list
gcloud auth login --no-launch-browser
```

2. **Error de permisos**:
```bash
gcloud projects add-iam-policy-binding valoraciones-app-cloud-run \
    --member="user:tu-email@gmail.com" \
    --role="roles/run.admin"
```

3. **Ver logs del servicio**:
```bash
gcloud run services logs read valoraciones-backend --region us-central1
```

4. **Ver logs en tiempo real**:
```bash
gcloud run services logs tail valoraciones-backend --region us-central1
```

## Comando de Despliegue Manual (Alternativo)

Si prefieres ejecutar el despliegue paso a paso:

```bash
# 1. Construir imagen
docker build -f Dockerfile.cloudrun -t gcr.io/valoraciones-app-cloud-run/valoraciones-backend .

# 2. Subir imagen
docker push gcr.io/valoraciones-app-cloud-run/valoraciones-backend

# 3. Desplegar
gcloud run deploy valoraciones-backend \
    --image gcr.io/valoraciones-app-cloud-run/valoraciones-backend \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --memory 4Gi \
    --cpu 2 \
    --max-instances 10 \
    --concurrency 50 \
    --timeout 900 \
    --port 8080 \
    --execution-environment gen2
```

La URL resultante será la que necesitas para configurar el MCP de base de datos.