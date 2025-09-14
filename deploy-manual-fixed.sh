#!/bin/bash

# Script de deploy manual para Cloud Run - Versión corregida
# Corrige los problemas identificados en el error FAILED_PRECONDITION

set -e

# Configuración
PROJECT_ID="valoraciones-app-cloud-run"
SERVICE_NAME="registro-valorizaciones"
REGION="southamerica-west1"
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"

# Obtener commit SHA o usar timestamp
if git rev-parse --git-dir > /dev/null 2>&1; then
    COMMIT_SHA=$(git rev-parse --short HEAD)
    echo "🔗 Usando commit SHA: $COMMIT_SHA"
else
    COMMIT_SHA=$(date +%s)
    echo "⏰ Usando timestamp: $COMMIT_SHA"
fi

TAG="$IMAGE_NAME:$COMMIT_SHA"

echo "🚀 Deploy manual de $SERVICE_NAME"
echo "   Project: $PROJECT_ID"
echo "   Image: $TAG"
echo "   Region: $REGION"
echo

# Verificar que estamos en el directorio correcto
if [ ! -f "Dockerfile" ]; then
    echo "❌ Error: Dockerfile no encontrado en el directorio actual"
    echo "   Asegúrate de ejecutar este script desde el directorio backend/"
    exit 1
fi

if [ ! -f "requirements-cloudrun.txt" ]; then
    echo "❌ Error: requirements-cloudrun.txt no encontrado"
    exit 1
fi

if [ ! -f "main.py" ]; then
    echo "❌ Error: main.py no encontrado"
    exit 1
fi

# Configurar proyecto
echo "1️⃣ Configurando proyecto..."
gcloud config set project $PROJECT_ID

# Construir imagen
echo
echo "2️⃣ Construyendo imagen Docker..."
echo "Comando: docker build -t $TAG ."
docker build -t $TAG .

# Configurar autenticación para Container Registry
echo
echo "3️⃣ Configurando autenticación para Container Registry..."
gcloud auth configure-docker gcr.io --quiet

# Push imagen
echo
echo "4️⃣ Subiendo imagen a Container Registry..."
docker push $TAG

# Deploy a Cloud Run
echo
echo "5️⃣ Desplegando a Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --image=$TAG \
    --region=$REGION \
    --platform=managed \
    --allow-unauthenticated \
    --port=8080 \
    --memory=4Gi \
    --cpu=2 \
    --timeout=900s \
    --max-instances=10 \
    --set-env-vars="PORT=8080,BROWSER_HEADLESS=true"

# Obtener URL del servicio
echo
echo "6️⃣ Obteniendo URL del servicio..."
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)")

echo
echo "✅ Deploy completado exitosamente!"
echo "🌐 URL del servicio: $SERVICE_URL"
echo "🏷️  Imagen desplegada: $TAG"
echo
echo "🔍 Para verificar el servicio:"
echo "   curl $SERVICE_URL/health"
echo
echo "📊 Para ver logs:"
echo "   gcloud logs tail --format=\"value(timestamp,severity,textPayload)\" --filter=\"resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME\" --limit=50"