#!/bin/bash

# Script para verificar la configuración de Cloud Build
# Verifica permisos, triggers y configuraciones necesarias

set -e

PROJECT_ID="valoraciones-app-cloud-run"
TRIGGER_ID="b8e48e77-efe3-4359-be19-0ced16ec1735"
REGION="southamerica-west1"

echo "🔍 Verificando configuración de Cloud Build..."
echo "Project ID: $PROJECT_ID"
echo "Trigger ID: $TRIGGER_ID"
echo "Region: $REGION"
echo

# Verificar si gcloud está configurado
echo "1. Verificando configuración de gcloud..."
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI no está instalado"
    exit 1
fi

# Verificar proyecto actual
CURRENT_PROJECT=$(gcloud config get-value project 2>/dev/null || echo "")
if [ "$CURRENT_PROJECT" != "$PROJECT_ID" ]; then
    echo "⚠️  Proyecto actual: $CURRENT_PROJECT (esperado: $PROJECT_ID)"
    echo "Configurando proyecto..."
    gcloud config set project $PROJECT_ID
fi

# Verificar APIs habilitadas
echo
echo "2. Verificando APIs necesarias..."
REQUIRED_APIS=(
    "cloudbuild.googleapis.com"
    "run.googleapis.com"
    "containerregistry.googleapis.com"
)

for api in "${REQUIRED_APIS[@]}"; do
    if gcloud services list --enabled --filter="name:$api" --format="value(name)" | grep -q "$api"; then
        echo "✅ $api habilitada"
    else
        echo "❌ $api NO habilitada"
        echo "Habilitando $api..."
        gcloud services enable $api
    fi
done

# Verificar permisos del servicio Cloud Build
echo
echo "3. Verificando permisos del servicio Cloud Build..."
BUILD_SERVICE_ACCOUNT=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")@cloudbuild.gserviceaccount.com
echo "Service Account: $BUILD_SERVICE_ACCOUNT"

# Verificar roles necesarios
REQUIRED_ROLES=(
    "roles/run.admin"
    "roles/iam.serviceAccountUser"
    "roles/storage.admin"
)

for role in "${REQUIRED_ROLES[@]}"; do
    if gcloud projects get-iam-policy $PROJECT_ID --flatten="bindings[].members" --format="table(bindings.role)" --filter="bindings.members:$BUILD_SERVICE_ACCOUNT AND bindings.role:$role" | grep -q "$role"; then
        echo "✅ Role $role asignado"
    else
        echo "❌ Role $role NO asignado"
        echo "Asignando role $role..."
        gcloud projects add-iam-policy-binding $PROJECT_ID \
            --member="serviceAccount:$BUILD_SERVICE_ACCOUNT" \
            --role="$role"
    fi
done

# Verificar triggers
echo
echo "4. Verificando triggers de Cloud Build..."
if gcloud builds triggers describe $TRIGGER_ID --region=$REGION &>/dev/null; then
    echo "✅ Trigger encontrado"
    gcloud builds triggers describe $TRIGGER_ID --region=$REGION --format="yaml"
else
    echo "❌ Trigger no encontrado o inaccesible"
    echo "Listando triggers disponibles..."
    gcloud builds triggers list --region=$REGION
fi

# Verificar Container Registry
echo
echo "5. Verificando Container Registry..."
if gsutil ls gs://artifacts.$PROJECT_ID.appspot.com &>/dev/null; then
    echo "✅ Container Registry configurado"
else
    echo "⚠️  Container Registry puede necesitar inicialización"
fi

# Verificar Cloud Run service
echo
echo "6. Verificando servicio de Cloud Run..."
if gcloud run services describe registro-valorizaciones --region=$REGION &>/dev/null; then
    echo "✅ Servicio Cloud Run existe"
    echo "Estado actual:"
    gcloud run services describe registro-valorizaciones --region=$REGION --format="value(status.url,status.conditions[0].type)"
else
    echo "⚠️  Servicio Cloud Run no existe o inaccesible"
fi

echo
echo "✅ Verificación completada"