# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

Project scope and goals
- Backend for Registro de Valorizaciones built with FastAPI and Python 3.11.
- Integrates with Neon (PostgreSQL) and uses Playwright for SUNAT/OSCE data extraction.
- Deployed to Google Cloud Run; CI/CD via GitHub Actions.

Common commands (PowerShell-friendly)
- Setup (Windows PowerShell)
  ```bash path=null start=null
  # Create and activate virtualenv
  python -m venv .venv
  .\.venv\Scripts\Activate.ps1
  
  # Install dependencies
  pip install -r requirements.txt
  
  # Install Playwright browsers for local scraping (needed for OSCE/SUNAT flows)
  python -m playwright install chromium
  ```

- Run the API locally (uvicorn)
  ```bash path=null start=null
  # Default dev port
  uvicorn main:app --reload --port 8000
  
  # Match Cloud Run’s port contract (used in Docker/Cloud Run)
  uvicorn main:app --host 0.0.0.0 --port 8080 --log-level info
  ```

- Environment variables commonly used
  ```bash path=null start=null
  # Required for Neon-backed features
  $env:NEON_CONNECTION_STRING = "postgresql://USER:PASSWORD@HOST/DB?sslmode=require"
  
  # Optional: enable proxy header handling on Cloud Run
  $env:ENABLE_PROXY_MIDDLEWARE = "true"
  
  # Cloud Run reads PORT; uvicorn command above defaults to 8080
  $env:PORT = "8080"
  ```

- Tests (pytest)
  ```bash path=null start=null
  # Run all tests (as in CI)
  pytest -v
  
  # Run a single file
  pytest -v tests\test_uuid_handling.py
  
  # Run a single test function
  pytest -v tests\test_uuid_handling.py::test_uuid_roundtrip
  
  # Filter by keyword
  pytest -v -k osce
  ```

- Lint/type checks (pre-commit hooks present)
  ```bash path=null start=null
  # One-time install
  pip install pre-commit
  pre-commit install
  
  # Run all hooks on the full repo
  pre-commit run --all-files
  ```
  Notes:
  - Custom hooks are configured in .pre-commit-config.yaml (UUID/schema and route checks). If a referenced script is missing, the corresponding hook will fail; run specific hooks or update the config accordingly.

- Docker (local container build/run)
  ```bash path=null start=null
  # Build image (includes Playwright browser install)
  docker build -t valoraciones-backend:local .
  
  # Run container (exposes 8080 by default)
  docker run --rm -p 8080:8080 ^
    -e NEON_CONNECTION_STRING=$env:NEON_CONNECTION_STRING ^
    valoraciones-backend:local
  ```

- CI parity (what GitHub Actions does)
  ```bash path=null start=null
  # Python 3.11, install deps, then:
  pytest -v
  ```

Highlights from README and docs
- FastAPI + Playwright backend, targeting Cloud Run; Neon (PostgreSQL) as the primary data store.
- Ports used: 8000 for local dev; 8080 for Docker/Cloud Run.
- Frontend exists under frontend/ (Vercel), but this repository’s operational focus is backend.
- Docs include WhatsApp notification system architecture and API reference under docs/; backend here contains the service and routes used by that subsystem.

High-level architecture and flow
- Entrypoint
  - main.py defines the FastAPI application, CORS, optional proxy headers middleware for Cloud Run, basic root and /health endpoints, and includes routers.
  - Uvicorn is used to serve the app (see Dockerfile and commands above). Running python main.py alone won’t start a server; use uvicorn.

- API layer (app/api/routes)
  - empresas.py: CRUD and listing for companies (empresas) using Neon. Validates RUC, prepares representative/contact data, and delegates persistence to EmpresaServiceNeon.
  - osce.py: Endpoints for OSCE lookups using the OSCEService (Playwright). Note: If these routes are not included by main.py, they must be registered to be exposed.
  - Additional debug and simplified routes exist (e.g., debug_empresa.py, debug_logs.py) and specialized flows for notifications.

- Services layer (app/services)
  - empresa_service_neon.py: Direct Neon Postgres access via psycopg2. Provides:
    - guardar_empresa(datos): upsert to empresas and insert related representantes_legales/contactos_empresa; logs extensively and returns the empresa UUID.
    - listar_empresas(limit): fetches recent empresas with representatives and contacts.
    - obtener_empresa_por_ruc(ruc): fetches a single empresa with related data.
    - eliminar_empresa(identificador): accepts either UUID or RUC, resolves to UUID, then deletes.
    - Tables referenced include empresas, representantes_legales, contactos_empresa.
  - osce_service.py: Playwright-based extraction against https://apps.osce.gob.pe/perfilprov-ui/ with multiple strategies and timeouts. Produces rich EmpresaOSCE responses, including specialties, members, and contact info. Requires chromium to be installed via Playwright.
  - sunat_service_improved and consolidation_service: Used by main.py to provide improved SUNAT data and consolidated SUNAT+OSCE responses.

- Core and infrastructure (app/core)
  - config.py: Centralized settings via pydantic-settings. Reads from .env by default. Includes CORS, logging, WhatsApp, Redis, and scheduler-related toggles.
  - database.py: Async SQLAlchemy engine/session setup. Uses NEON_CONNECTION_STRING if present (converted to async form), falling back to SQLite (sqlite+aiosqlite) for local. Provides async session dependency and init/close helpers. Note: empresa_service_neon uses psycopg2 directly (synchronous connection) in parallel with this async engine.

- Middleware and monitoring
  - proxy_headers.py: Recommended on Cloud Run (ENABLE_PROXY_MIDDLEWARE=true) to correctly interpret forwarded headers before CORS.
  - caching.py, rate_limiting.py, validation.py: Optimizations and request protection (per-route adoption as needed).
  - monitoring/health_checker.py: Health probe utilities beyond the basic /health endpoint.

- Notifications subsystem (WhatsApp)
  - Routes under app/api/routes/notifications*.py use SQLAlchemy models and services (notification_service, whatsapp_service, scheduler_service) to schedule, send, and track WhatsApp messages. Configuration is driven by settings in app/core/config.py (e.g., WHATSAPP_* and Redis settings).

- CI/CD
  - .github/workflows/ci.yml runs pytest -v on Python 3.11, builds Docker image, and deploys to Cloud Run with appropriate resources and environment variables (NEON_CONNECTION_STRING).

Working effectively in this repo
- Local Neon access
  - Set NEON_CONNECTION_STRING before hitting endpoints that rely on Neon. Without it, empresa_service_neon falls back to a hard-coded connection string (not recommended for development).

- Playwright requirements
  - For OSCE/SUNAT scraping paths and tests that exercise them, ensure chromium is installed: python -m playwright install chromium.

- Router exposure
  - If you add new routers under app/api/routes, remember to include them in main.py (app.include_router(...)). Several routes exist that are not registered by default in main.py; register them to expose their endpoints.

- Indexing hints (Warp)
  - Consider excluding large/binary artifacts from indexing for faster and more relevant context (create .warpindexingignore):
  ```bash path=null start=null
  valoraciones.db
  *.tar.gz
  sql/*.db
  ```

Frontend (si aplica)
- Ubicación prevista: frontend/
- Requisitos: Node.js >= 18
- Notas importantes:
  - En este repo existen indicios de frontend (frontend/src/…), pero no se incluye package.json ni configuración de Vite en esta copia. Si el subproyecto no está inicializado, estos comandos no aplicarán hasta que se agreguen esos archivos.
  - Las variables VITE_* del archivo .env.example están pensadas para el frontend (Vercel/Vite). Crea frontend/.env.local con las claves VITE_* que necesites.

- Comandos comunes (PowerShell)
  ```bash path=null start=null
  # Entrar a la carpeta del frontend
  cd frontend

  # Instalar dependencias (requiere package.json)
  npm install

  # Correr en desarrollo (Vite por defecto usa el puerto 5173)
  npm run dev

  # Build de producción (salida típica: dist/)
  npm run build

  # Correr un test individual (si hay configuración de tests)
  npm test -- --watch
  ```

- Variables de entorno (Vite)
  ```bash path=null start=null
  # Crea frontend/.env.local con contenido similar:
  VITE_ENVIRONMENT=development
  VITE_BACKEND_URL=http://localhost:8000
  VITE_LOG_LEVEL=error

  # Para producción (Vercel), usa valores del .env.example del repo:
  VITE_ENVIRONMENT=production
  VITE_BACKEND_URL=https://registro-valorizaciones-503600768755.southamerica-west1.run.app
  VITE_API_TIMEOUT=45000
  VITE_RETRY_ATTEMPTS=2
  VITE_DEBUG=false
  ```

- Despliegue (Vercel, según docs del repo)
  - Root Directory: frontend/
  - Build Command: npm run build
  - Output Directory: dist

Workflows rápidos en Warp
- Desarrollo local (dos pestañas/panes)
  ```bash path=null start=null
  # Pestaña 1: Backend (en la raíz del backend)
  python -m venv .venv
  .\.venv\Scripts\Activate.ps1
  pip install -r requirements.txt
  # Si usarás scraping OSCE/SUNAT
  python -m playwright install chromium
  # Variables mínimas (ajusta con tus credenciales seguras)
  # $env:NEON_CONNECTION_STRING = "postgresql://USER:PASSWORD@HOST/DB?sslmode=require"
  uvicorn main:app --reload --port 8000
  ```
  ```bash path=null start=null
  # Pestaña 2: Frontend (en la carpeta frontend)
  cd frontend
  npm install
  # .env.local debe tener VITE_BACKEND_URL=http://localhost:8000
  npm run dev
  ```
- Tests backend
  ```bash path=null start=null
  pytest -v
  ```
- Docker backend local
  ```bash path=null start=null
  docker build -t valoraciones-backend:local .
  docker run --rm -p 8080:8080 ^
    -e NEON_CONNECTION_STRING=$env:NEON_CONNECTION_STRING ^
    valoraciones-backend:local
  ```

Ejemplos rápidos de llamadas a endpoints (PowerShell)
- Variables comunes
  ```bash path=null start=null
  $base = "http://localhost:8000"
  ```

- Health check
  ```bash path=null start=null
  Invoke-RestMethod "$base/health"
  ```

- Información de la API (routers y dependencias)
  ```bash path=null start=null
  Invoke-RestMethod "$base/api/info"
  ```
  Nota: El campo dependencies incluye neon_connectivity con uno de estos estados:
  - ok: conexión a Neon verificada (SELECT 1)
  - failed: hubo error al conectar (se muestra mensaje abreviado)
  - skipped: no hay NEON_CONNECTION_STRING o no está disponible psycopg2

- Consulta SUNAT (POST /consultar-ruc)
  ```bash path=null start=null
  $body = @{ ruc = "20100070970" } | ConvertTo-Json
  Invoke-RestMethod -Uri "$base/consultar-ruc" -Method POST -ContentType "application/json" -Body $body
  ```

- Consulta consolidada SUNAT+OSCE (GET /consulta-ruc-consolidada/{ruc})
  ```bash path=null start=null
  Invoke-RestMethod "$base/consulta-ruc-consolidada/20100070970"
  ```

- Empresas: obtener por RUC (GET /empresas/ruc/{ruc})
  ```bash path=null start=null
  Invoke-RestMethod "$base/empresas/ruc/20100070970"
  ```

- Empresas: listar con búsqueda y paginación (GET /empresas?search=&per_page=)
  ```bash path=null start=null
  Invoke-RestMethod "$base/empresas?search=CONSTRUCTORA&per_page=5"
  ```

- Notificaciones WhatsApp: listar (GET /api/notifications)
  ```bash path=null start=null
  Invoke-RestMethod "$base/api/notifications?pagina=1&limite=10"
  ```

- Notificaciones WhatsApp: actualizar estado (PUT /api/notifications/{id}/status)
  ```bash path=null start=null
  $body = @{ nuevo_estado = "ENVIADA"; motivo = "Prueba manual" } | ConvertTo-Json
  Invoke-RestMethod -Uri "$base/api/notifications/1/status" -Method PUT -ContentType "application/json" -Body $body
  ```

- OSCE: consultar por RUC (POST /api/v1/osce/consultar)
  Nota: estos endpoints están habilitados por defecto. Si personalizas main.py, asegúrate de mantener app.include_router(osce_router).
  ```bash path=null start=null
  $osce = @{ ruc = "20100070970" } | ConvertTo-Json
  Invoke-RestMethod -Uri "$base/api/v1/osce/consultar" -Method POST -ContentType "application/json" -Body $osce
  ```

- OSCE (modo diagnóstico): POST /api/v1/osce/consultar-debug
  Devuelve { empresa, debug } con pasos del scraping cuando DEBUG_ENDPOINTS=true.
  ```bash path=null start=null
  $env:DEBUG_ENDPOINTS = "true"
  $osce = @{ ruc = "20100070970" } | ConvertTo-Json
  Invoke-RestMethod -Uri "$base/api/v1/osce/consultar-debug" -Method POST -ContentType "application/json" -Body $osce
  ```

- Debug headers (GET /debug/headers) para revisar cabeceras y proxy en Cloud Run
  ```bash path=null start=null
  Invoke-RestMethod "$base/debug/headers"
  ```

- Ping Neon bajo demanda (GET /debug/neon-ping)
  Requiere habilitar DEBUG_ENDPOINTS=true antes de levantar la app.
  ```bash path=null start=null
  $env:DEBUG_ENDPOINTS = "true"
  uvicorn main:app --reload --port 8000

  Invoke-RestMethod "$base/debug/neon-ping"
  ```

- Ping Playwright (GET /debug/playwright-ping)
  Verifica que Playwright (chromium) esté instalado y puede lanzar/cerrar el navegador.
  ```bash path=null start=null
  # Si no tienes chromium aún:
  python -m playwright install chromium

  $env:DEBUG_ENDPOINTS = "true"
  uvicorn main:app --reload --port 8000

  Invoke-RestMethod "$base/debug/playwright-ping"
  ```

## Scripts de integración (manuales)
- Ubicación: `scripts/integration/`
- Scripts disponibles:
  - `endpoint_manual.py`
  - `simple_endpoint_manual.py`
  - `neon_connection_manual.py`
  - `sql_directo_manual.py`
- Todos requieren variables de entorno adecuadas (por ejemplo, `NEON_CONNECTION_STRING`).
- Ejemplo de uso (PowerShell):
  ```bash path=null start=null
  $env:NEON_CONNECTION_STRING = "postgresql://USER:PASSWORD@HOST/DB?sslmode=require"
  python .\scripts\integration\neon_connection_manual.py
  ```

## Otros scripts
- Operaciones/DevOps: `scripts/ops/`
  - `check_deployment.sh`, `deploy-manual-fixed.sh`, `verify-cloudbuild-config.sh`, `fix-cloudbuild-trigger.sh`
- CI local/manual: `scripts/ci/`
  - `test_deployment.sh`
