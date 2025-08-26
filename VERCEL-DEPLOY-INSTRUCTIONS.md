# 🚀 INSTRUCCIONES DEPLOY VERCEL DESDE GITHUB

## ✅ CÓDIGO SUBIDO A GITHUB

**Repositorio:** https://github.com/ENEASJO/registro-valorizaciones
**Commit:** `feat: Configuración backend Vercel sin Playwright`

## 🎯 PRÓXIMOS PASOS MANUALES

### 1️⃣ CONECTAR GITHUB CON VERCEL

1. Ve a **https://vercel.com/dashboard**
2. Click **"Add New..."** → **"Project"**
3. Selecciona **"Import Git Repository"**
4. Busca **"registro-valorizaciones"** y click **"Import"**

### 2️⃣ CONFIGURAR EL PROYECTO

En la configuración del proyecto:

**Build & Output Settings:**
- Build Command: `pip install -r server/requirements.txt`
- Output Directory: `server/`
- Install Command: (dejar vacío)

**Root Directory:**
- Seleccionar: `server/` (directorio del backend)

### 3️⃣ VARIABLES DE ENTORNO

Agregar en **Environment Variables**:

```
TURSO_DATABASE_URL = libsql://registro-de-valorizaciones-eneasjo.aws-us-east-2.turso.io
TURSO_AUTH_TOKEN = eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJhIjoicmVnaXN0cm8tZGUtdmFsb3JpemFjaW9uZXMtZW5lYXNqbyIsImlhdCI6MTcyNDE2NjU2NH0.JfCnDaYNzgJYZ6q8rIYDHQKgdCPzLJSf4IQFrNR-F7ZIhGXMU4B2u-uAUUgqbPP8-mHN5kFO1LfBvkmGkWQPBg
```

**Aplicar a:** Production, Preview, Development

### 4️⃣ DEPLOY

1. Click **"Deploy"**
2. Espera a que termine el build
3. Vercel te dará una URL: `https://registro-valorizaciones-xxx.vercel.app`

## 🔍 VERIFICAR DEPLOY

### Test Endpoints:

```bash
# Health check
curl https://tu-domain.vercel.app/health

# Info API
curl https://tu-domain.vercel.app/

# Empresas
curl https://tu-domain.vercel.app/api/empresas
```

### Esperado:
- ✅ Health check devuelve `{"status": "healthy", "database": "connected"}`
- ✅ API info muestra version "2.0.0" sin Playwright
- ✅ Empresas devuelve lista desde Turso

## 🏗️ ARQUITECTURA FINAL

```
Frontend (Vercel)
    ↓ (scraping)
Cloud Run: https://tu-scraping.run.app
    ↓ (CRUD)  
Vercel Backend: https://tu-backend.vercel.app
    ↓
Turso Database (automático)
```

## 📋 ENDPOINTS RESULTANTES

### **Scraping (Cloud Run)**
- `GET /consulta-ruc/{ruc}` - SUNAT
- `GET /consulta-osce/{ruc}` - OSCE
- `GET /consulta-ruc-consolidada/{ruc}` - Consolidado

### **CRUD (Vercel Backend)**
- `GET /api/empresas` - Listar empresas
- `POST /api/empresas` - Crear empresa
- `GET /api/obras` - Listar obras
- `GET /api/valorizaciones` - Listar valorizaciones

## ✅ STATUS

- ✅ Código en GitHub
- ✅ Backend sin Playwright preparado
- ✅ Turso configurado y funcionando localmente
- 🔄 **Pendiente:** Conectar repo con Vercel Dashboard
- 🔄 **Pendiente:** Configurar variables de entorno
- 🔄 **Pendiente:** Deploy automático

## 🎯 RESULTADO ESPERADO

Una vez deployado tendrás:
1. **Backend CRUD** funcionando en Vercel con Turso
2. **Scraping separado** en Cloud Run (ya funcionando)
3. **Base de datos** en Turso con todos los módulos
4. **Deploy automático** cada vez que hagas push a main