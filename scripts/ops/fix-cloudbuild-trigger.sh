#!/bin/bash

# Script para reconfigurar el trigger de Cloud Build
# Soluciona el error FAILED_PRECONDITION configurando correctamente el trigger

set -e

PROJECT_ID="valoraciones-app-cloud-run"
TRIGGER_NAME="deploy-backend-auto"
REGION="southamerica-west1"
REPO_NAME="registro-valorizaciones"

echo "🔧 Reconfigurando trigger de Cloud Build..."
echo "Project: $PROJECT_ID"
echo "Trigger: $TRIGGER_NAME"
echo "Region: $REGION"
echo

# Configurar proyecto
gcloud config set project $PROJECT_ID

# Eliminar trigger existente si existe (para recrearlo limpiamente)
echo "1️⃣ Verificando trigger existente..."
if gcloud builds triggers list --region=$REGION --filter="name:$TRIGGER_NAME" --format="value(id)" | head -1 | grep -q .; then
    EXISTING_TRIGGER_ID=$(gcloud builds triggers list --region=$REGION --filter="name:$TRIGGER_NAME" --format="value(id)" | head -1)
    echo "⚠️  Trigger existente encontrado: $EXISTING_TRIGGER_ID"
    echo "¿Desea eliminarlo y recrearlo? (y/N)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo "Eliminando trigger existente..."
        gcloud builds triggers delete $EXISTING_TRIGGER_ID --region=$REGION --quiet
        echo "✅ Trigger eliminado"
    else
        echo "❌ Cancelado por el usuario"
        exit 1
    fi
fi

# Crear nuevo trigger
echo
echo "2️⃣ Creando nuevo trigger..."

# Crear archivo temporal de configuración
cat > /tmp/cloudbuild-trigger.yaml << EOF
name: $TRIGGER_NAME
description: "Auto deploy backend on push to main"

github:
  owner: "tu-usuario-github"  # REEMPLAZA CON TU USUARIO
  name: "$REPO_NAME"
  push:
    branch: "^main$"

includedFiles:
  - "backend/**"

ignoredFiles:
  - "frontend/**"
  - "docs/**"
  - "*.md"

filename: "backend/cloudbuild.yaml"

substitutions:
  _SERVICE_NAME: "registro-valorizaciones"
  _REGION: "$REGION"
EOF

echo "⚠️  IMPORTANTE: Debes editar el archivo de configuración para especificar tu usuario de GitHub"
echo "   Archivo: /tmp/cloudbuild-trigger.yaml"
echo "   Línea a cambiar: owner: \"tu-usuario-github\""
echo
echo "Presiona Enter cuando hayas editado el archivo..."
read -r

# Crear trigger
gcloud builds triggers create github \
    --config=/tmp/cloudbuild-trigger.yaml \
    --region=$REGION

echo
echo "3️⃣ Verificando nuevo trigger..."
TRIGGER_ID=$(gcloud builds triggers list --region=$REGION --filter="name:$TRIGGER_NAME" --format="value(id)" | head -1)
echo "✅ Nuevo trigger creado: $TRIGGER_ID"

# Mostrar configuración
gcloud builds triggers describe $TRIGGER_ID --region=$REGION

# Limpiar archivo temporal
rm -f /tmp/cloudbuild-trigger.yaml

echo
echo "✅ Reconfiguración completada!"
echo
echo "🔍 Para probar el trigger:"
echo "   1. Haz push de cambios a la rama main"
echo "   2. Verifica en Cloud Build Console:"
echo "      https://console.cloud.google.com/cloud-build/builds?project=$PROJECT_ID"
echo
echo "📋 Para crear el trigger manualmente desde la consola:"
echo "   1. Ve a Cloud Build > Triggers"
echo "   2. Conecta tu repositorio GitHub"
echo "   3. Configura:"
echo "      - Nombre: $TRIGGER_NAME"
echo "      - Evento: Push a rama"
echo "      - Rama: ^main$"
echo "      - Archivo: backend/cloudbuild.yaml"
echo "      - Filtros incluidos: backend/**"