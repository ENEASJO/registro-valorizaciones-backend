#!/bin/bash

# Script to test if the deployment is working
SERVICE_NAME="registro-valorizaciones-backend"
REGION="southamerica-west1"

echo "=== Testing Cloud Run Deployment ==="
echo ""

# Check if we can get the service URL
echo "Getting service URL..."
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format='value(status.url)' 2>/dev/null || echo "")

if [ -n "$SERVICE_URL" ]; then
    echo "✓ Service URL found: $SERVICE_URL"

    # Test health endpoint
    echo ""
    echo "Testing health endpoint..."
    HEALTH_RESPONSE=$(curl -s "$SERVICE_URL/health" 2>/dev/null || echo "Connection failed")

    if [[ "$HEALTH_RESPONSE" == *"healthy"* ]]; then
        echo "✓ Health endpoint is responding"
        echo "Response: $HEALTH_RESPONSE"
    else
        echo "✗ Health endpoint not responding properly"
        echo "Response: $HEALTH_RESPONSE"
    fi

    # Test empresas endpoint (GET)
    echo ""
    echo "Testing empresas endpoint..."
    EMPRESAS_RESPONSE=$(curl -s "$SERVICE_URL/api/v1/empresas/" 2>/dev/null || echo "Connection failed")

    if [[ "$EMPRESAS_RESPONSE" == *"200"* ]] || [[ "$EMPRESAS_RESPONSE" == *"[]" ]] || [[ "$EMPRESAS_RESPONSE" == *"*"* ]]; then
        echo "✓ Empresas endpoint is responding"
        echo "Response: $EMPRESAS_RESPONSE"
    else
        echo "✗ Empresas endpoint not responding properly"
        echo "Response: $EMPRESAS_RESPONSE"
    fi

else
    echo "✗ Could not get service URL"
    echo "Please ensure gcloud CLI is installed and authenticated"
    echo "Run: gcloud run services describe $SERVICE_NAME --region=$REGION"
fi

echo ""
echo "=== Deployment Verification Complete ==="