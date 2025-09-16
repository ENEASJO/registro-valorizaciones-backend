#!/bin/bash

# Script to check Cloud Run deployment status
# This would normally require gcloud CLI to be installed

SERVICE_NAME="registro-valorizaciones-backend"
REGION="southamerica-west1"
COMMIT_SHA="3fb1f79"

echo "=== Cloud Run Deployment Status Check ==="
echo "Service: $SERVICE_NAME"
echo "Region: $REGION"
echo "Commit: $COMMIT_SHA"
echo ""

# Since gcloud CLI is not available, we'll provide manual instructions
echo "To check the deployment status, run these commands:"
echo ""
echo "1. Install Google Cloud CLI if not already installed:"
echo "   curl https://sdk.cloud.google.com | bash"
echo "   exec -l \$SHELL"
echo ""
echo "2. Authenticate with Google Cloud:"
echo "   gcloud auth login"
echo "   gcloud config set project YOUR_PROJECT_ID"
echo ""
echo "3. Check deployment status:"
echo "   gcloud run services describe $SERVICE_NAME --region=$REGION --format='json(status, spec.template.spec)'"
echo ""
echo "4. Check recent deployments:"
echo "   gcloud run revisions list --service=$SERVICE_NAME --region=$REGION --limit=5 --format='table(name, createdAt, status.conditions[0].message)'"
echo ""
echo "5. Check logs for the deployment:"
echo "   gcloud logging read 'resource.type=\"cloud_run_revision\" resource.labels.service_name=\"registro-valorizaciones-backend\"' --limit=10 --format='text'"
echo ""
echo "=== GitHub Actions Status ==="
echo "Check the GitHub Actions workflow status at:"
echo "https://github.com/ENEASJO/registro-valorizaciones-backend/actions/workflows/ci.yml"
echo ""
echo "Look for workflow runs with commit: $COMMIT_SHA"
echo ""
echo "=== Manual Health Check ==="
echo "To manually test if the deployment is working, check the health endpoint:"
echo "curl https://registro-valorizaciones-backend-<hash>-uc.a.run.app/health"
echo ""
echo "=== Alternative: Check via Git History ==="
echo "The most recent commits show:"
git log --oneline -5