# 🚀 CLOUD RUN + TURSO - CONFIGURACIÓN COMPLETA

## 🎯 ARQUITECTURA FINAL

```
Frontend (Vercel) → Backend Completo (Cloud Run) → Turso Database
                         ↓
                 Playwright + CRUD + APIs
                   (Todo unificado)
```

## 🔧 CONFIGURAR VARIABLES DE ENTORNO EN CLOUD RUN

### 1️⃣ Via Google Cloud Console:

1. Ve a **Google Cloud Console** → **Cloud Run**
2. Selecciona tu servicio de backend
3. Click **"EDIT & DEPLOY NEW REVISION"**
4. En **"Variables and Secrets"** → **"ENVIRONMENT VARIABLES"**
5. Agregar:

```bash
TURSO_DATABASE_URL = libsql://registro-de-valorizaciones-eneasjo.aws-us-east-2.turso.io
TURSO_AUTH_TOKEN = eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJhIjoicmVnaXN0cm8tZGUtdmFsb3JpemFjaW9uZXMtZW5lYXNqbyIsImlhdCI6MTcyNDE2NjU2NH0.JfCnDaYNzgJYZ6q8rIYDHQKgdCPzLJSf4IQFrNR-F7ZIhGXMU4B2u-uAUUgqbPP8-mHN5kFO1LfBvkmGkWQPBg
```

6. Click **"DEPLOY"**

### 2️⃣ Via gcloud CLI:

```bash
gcloud run services update tu-servicio \
  --set-env-vars="TURSO_DATABASE_URL=libsql://registro-de-valorizaciones-eneasjo.aws-us-east-2.turso.io,TURSO_AUTH_TOKEN=eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9..."
```

## ✅ VERIFICAR DEPLOYMENT

Una vez que Cloud Run termine el deploy, verificar:

### A) Health Check:
```bash
curl https://tu-cloud-run-url.run.app/health
```

**Esperado:**
```json
{
  "status": "healthy",
  "version": "3.0.0", 
  "architecture": "Cloud Run Completo",
  "services": {
    "playwright": "enabled",
    "turso_database": "connected",
    "crud_apis": "enabled"
  }
}
```

### B) API Info:
```bash
curl https://tu-cloud-run-url.run.app/
```

**Esperado:**
```json
{
  "message": "API de Valorizaciones - Cloud Run Completo",
  "version": "3.0.0",
  "architecture": "Backend Unificado: Playwright + CRUD + Turso",
  "database": "Turso (connected)"
}
```

### C) CRUD Endpoints:
```bash
# Empresas
curl https://tu-cloud-run-url.run.app/api/empresas

# Obras  
curl https://tu-cloud-run-url.run.app/api/obras

# Valorizaciones
curl https://tu-cloud-run-url.run.app/api/valorizaciones
```

### D) Scraping (ya funcionaba):
```bash
# SUNAT
curl https://tu-cloud-run-url.run.app/consulta-ruc/20123456789

# Consolidado
curl https://tu-cloud-run-url.run.app/consulta-ruc-consolidada/20123456789
```

## 🎯 RESULTADO FINAL

**Una sola URL de Cloud Run con:**
- ✅ **Scraping**: Playwright para SUNAT/OSCE
- ✅ **CRUD**: Empresas, obras, valorizaciones  
- ✅ **Database**: Turso SQLite Cloud
- ✅ **APIs**: Todo consolidado en un backend

## 🚨 TROUBLESHOOTING

**Si `turso_database: "disconnected"`:**
1. Verificar variables de entorno están correctas
2. Redeploy Cloud Run
3. Verificar logs: `gcloud run services logs tail tu-servicio`

**Si faltan endpoints CRUD:**
- Verificar que el commit se deployó correctamente
- Revisar logs de build en Cloud Run

## ✅ STATUS ESPERADO

- ✅ **Scraping**: Ya funcionaba antes
- ✅ **CRUD**: Nuevo con este deploy
- ✅ **Database**: Conectada a Turso
- ✅ **Frontend**: Sin cambios (sigue en Vercel)