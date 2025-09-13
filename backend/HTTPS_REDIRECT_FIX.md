# HTTPS Redirect Fix for Cloud Run

## Problem Identified

The backend was redirecting HTTPS requests to HTTP, causing 307 redirect loops in Cloud Run. This occurred because:

1. **Cloud Run** terminates SSL and forwards requests to containers as HTTP
2. **Cloud Run** sets `X-Forwarded-Proto: https` header
3. **FastAPI application** was not handling proxy headers correctly
4. **Application** perceived requests as HTTP and generated redirects with HTTP URLs

## Solution Implemented

### 1. Created Proxy Headers Middleware

**File**: `/home/usuario/PROYECTOS/registro-valorizaciones/backend/app/middleware/proxy_headers.py`

This middleware:
- Detects `X-Forwarded-Proto` headers and updates the request scheme
- Handles `X-Forwarded-Host` and `X-Forwarded-Port` headers
- Prevents HTTPS redirect loops in proxy environments
- Updates request scope to reflect the original protocol

### 2. Updated Main Application

**File**: `/home/usuario/PROYECTOS/registro-valorizaciones/backend/main.py`

Changes made:
- Added import for `Request` from FastAPI
- Added proxy headers middleware with environment variable control
- Added debug endpoint `/debug/headers` for testing
- Added configurable middleware via `ENABLE_PROXY_MIDDLEWARE` environment variable

### 3. Updated Deployment Configuration

**File**: `/home/usuario/PROYECTOS/registro-valorizaciones/backend/cloudbuild.yaml`

Added environment variable:
- `ENABLE_PROXY_MIDDLEWARE=true`

### 4. Created Test Script

**File**: `/home/usuario/PROYECTOS/registro-valorizaciones/backend/test_proxy_fix.py`

Script to test:
- Proxy headers functionality
- Empresas endpoint that was causing redirects
- Debug information collection

## Deployment Instructions

### 1. Deploy to Cloud Run

```bash
cd /home/usuario/PROYECTOS/registro-valorizaciones/backend

# Deploy using the updated configuration
gcloud builds submit --config=cloudbuild.yaml .
```

### 2. Test the Deployment

After deployment, test the fix:

```bash
# Test the debug endpoint
curl https://registro-valorizaciones-503600768755.southamerica-west1.run.app/debug/headers

# Test the empresas endpoint
curl https://registro-valorizaciones-503600768755.southamerica-west1.run.app/api/empresas/

# Run the comprehensive test
python test_proxy_fix.py
```

### 3. Expected Results

The debug endpoint should show:
- `scheme`: "https"
- `scope_scheme`: "https"
- `proxy_handled`: true
- `x-proxy-handled`: "true" in headers
- `x-forwarded-proto`: "https" in headers

The empresas endpoint should return:
- Status code: 200
- No redirect headers
- Proper JSON response

## Environment Variables

- `ENABLE_PROXY_MIDDLEWARE`: Set to `true` to enable proxy headers middleware (default)
- Can be disabled by setting to `false` for local development

## How It Works

1. **Request Flow**: HTTPS → Cloud Run (terminates SSL) → HTTP to container
2. **Middleware Detection**: Reads `X-Forwarded-Proto: https`
3. **Scheme Update**: Updates `request.scope["scheme"]` to "https"
4. **URL Generation**: FastAPI now generates URLs with HTTPS scheme
5. **No Redirects**: No more 307 redirects to HTTP

## Files Modified

1. `app/middleware/proxy_headers.py` - New middleware
2. `main.py` - Added middleware and debug endpoint
3. `cloudbuild.yaml` - Added environment variable
4. `test_proxy_fix.py` - Test script

## Rollback Plan

If issues occur, disable the middleware by:
1. Setting `ENABLE_PROXY_MIDDLEWARE=false` in cloudbuild.yaml
2. Redeploying
3. Or removing the middleware from main.py entirely