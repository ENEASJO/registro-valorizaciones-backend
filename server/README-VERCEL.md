# 🚀 Backend Vercel - Sistema de Valorizaciones

## 📋 ARQUITECTURA SEPARADA

```
Frontend (Vercel) → Cloud Run (Playwright) → Datos temporales
                  → Vercel Backend (CRUD) → Turso Database
```

## 🔧 CONFIGURACIÓN VERCEL

### Variables de Entorno Requeridas:
```
TURSO_DATABASE_URL=libsql://registro-de-valorizaciones-eneasjo.aws-us-east-2.turso.io
TURSO_AUTH_TOKEN=eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9...
```

## 📁 ARCHIVOS PRINCIPALES

- `main_vercel.py` - Backend principal (SIN PLAYWRIGHT)
- `requirements.txt` - Dependencias optimizadas para Vercel
- `vercel.json` - Configuración de deploy
- `app/` - Módulos CRUD y servicios Turso

## 🎯 ENDPOINTS DISPONIBLES

### CRUD (Base de datos):
- `GET /api/empresas` - Listar empresas
- `POST /api/empresas` - Crear empresa
- `GET /api/obras` - Listar obras
- `POST /api/obras` - Crear obra
- `GET /api/valorizaciones` - Listar valorizaciones
- `POST /api/valorizaciones` - Crear valorización

### Utilidad:
- `GET /health` - Health check
- `GET /` - Info de la API

## 🚀 DEPLOY DESDE GITHUB

1. **Conectar repositorio en Vercel Dashboard**
2. **Configurar variables de entorno** (TURSO_DATABASE_URL, TURSO_AUTH_TOKEN)
3. **Deploy automático** al hacer push

## ⚠️ IMPORTANTE

- Este backend **NO tiene Playwright** (optimizado para Vercel)
- Para scraping usar **Cloud Run separado**
- Base de datos: **Turso SQLite Cloud**
- Arquitectura: **Microservicios separados**

## 🔗 URLs ESPERADAS

- Backend Vercel: `https://tu-backend.vercel.app`
- Scraping Cloud Run: `https://tu-scraping.run.app`
- Database: Turso Cloud (automático)

## ✅ ESTADO

- ✅ Backend sin Playwright configurado
- ✅ Turso database funcionando localmente
- ✅ CRUD completo implementado
- 🔄 Listo para deploy desde GitHub