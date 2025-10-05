# 🚄 Guía de Migración a Railway

Esta guía te ayudará a migrar el backend de Google Cloud Run a Railway.

## 📋 Índice

1. [Prerrequisitos](#prerrequisitos)
2. [Configuración en Railway](#configuración-en-railway)
3. [Diferencias con Cloud Run](#diferencias-con-cloud-run)
4. [Despliegue](#despliegue)
5. [Verificación](#verificación)
6. [Troubleshooting](#troubleshooting)

---

## 📦 Prerrequisitos

- Cuenta en [Railway](https://railway.app)
- Base de datos Neon PostgreSQL configurada
- Repositorio GitHub conectado (recomendado para CI/CD automático)

---

## 🚀 Configuración en Railway

### Paso 1: Crear Nuevo Proyecto

1. Ve a [railway.app](https://railway.app)
2. Click en **"New Project"**
3. Selecciona **"Deploy from GitHub repo"**
4. Autoriza acceso a tu repositorio
5. Selecciona el repositorio `registro-valorizaciones-backend`

### Paso 2: Configurar Variables de Entorno

En el dashboard de Railway, ve a **Variables** y agrega:

#### Variables Requeridas

```bash
# Base de datos (CRÍTICO)
NEON_CONNECTION_STRING=postgresql://user:password@ep-xxx.neon.tech/valoraciones?sslmode=require

# Configuración básica
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
HOST=0.0.0.0

# Playwright
BROWSER_HEADLESS=true
PLAYWRIGHT_BROWSERS_PATH=/app/.cache/ms-playwright
```

#### Variables Opcionales

```bash
# Middleware de proxy (no necesario en Railway)
ENABLE_PROXY_MIDDLEWARE=false

# API externa para RUC
APIS_NET_PE_TOKEN=tu-token

# WhatsApp (si aplica)
WHATSAPP_API_TOKEN=tu-token
WHATSAPP_PHONE_NUMBER_ID=tu-phone-id

# Redis (si agregas servicio Redis en Railway)
REDIS_URL=redis://default:password@red-xxx.railway.internal:6379
```

⚠️ **Nota:** Railway configura automáticamente la variable `PORT`, no es necesario agregarla.

### Paso 3: Configurar Dockerfile

Railway usará automáticamente `Dockerfile.railway`. Si quieres usar el Dockerfile estándar:

1. Ve a **Settings** → **Build**
2. En **Dockerfile Path** ingresa: `Dockerfile.railway`

O renombra `Dockerfile.railway` a `Dockerfile` (recomendado).

### Paso 4: Configurar Healthcheck

Railway leerá automáticamente `railway.toml`, pero puedes configurar manualmente:

1. Ve a **Settings** → **Deploy**
2. **Healthcheck Path:** `/health`
3. **Healthcheck Timeout:** `300` segundos

### Paso 5: Configurar Dominio (Opcional)

Railway genera un dominio automático: `xxx.up.railway.app`

Para dominio personalizado:
1. Ve a **Settings** → **Networking**
2. Click en **Generate Domain** o agrega tu dominio custom
3. Copia la URL generada para actualizar el frontend

---

## 🔄 Diferencias con Cloud Run

| Característica | Cloud Run | Railway |
|----------------|-----------|---------||
| **Puerto** | Variable `PORT` manual | Variable `PORT` automática |
| **Proxy Headers** | Middleware requerido | No necesario |
| **Memoria** | 4Gi configurado en cloudbuild.yaml | Configurable en Settings |
| **CPU** | 2 cores + CPU boost | Configurable según plan |
| **Timeout** | 900s | Sin límite estricto |
| **Scaling** | 0-10 instancias | Según plan (Pro: ilimitado) |
| **Healthcheck** | Configurado en deploy | Configurado en railway.toml |
| **CI/CD** | Google Cloud Build | GitHub Actions automático |
| **Región** | southamerica-west1 | us-west1 (default) o configurable |

### Cambios Importantes en el Código

✅ **Ya implementado en el código actual:**
- Variable `PORT` con fallback: `${PORT:-8080}`
- Playwright lazy loading para inicio rápido
- CORS flexible para diferentes orígenes
- Middleware de proxy headers configurable (desactivado para Railway)

❌ **No necesitas cambiar:**
- `main.py` - Compatible con Railway
- `requirements.txt` - Funciona igual
- Rutas y servicios - Sin cambios

---

## 📤 Despliegue

### Opción 1: Despliegue Automático (Recomendado)

Railway se sincroniza automáticamente con GitHub:

1. Haz push a la rama `main`:
   ```bash
   git add .
   git commit -m "Configura Railway deployment"
   git push origin main
   ```

2. Railway detecta el cambio y despliega automáticamente

3. Monitorea el build en el dashboard de Railway

### Opción 2: Despliegue Manual con Railway CLI

```bash
# Instalar Railway CLI
npm i -g @railway/cli

# Login
railway login

# Linkear proyecto
railway link

# Deploy
railway up
```

### Opción 3: Despliegue desde Dashboard

1. Ve al dashboard de Railway
2. Click en **Deploy** → **Trigger Deploy**

---

## ✅ Verificación

### 1. Verificar el Build

En Railway dashboard:
- **Build Logs**: Verifica que Playwright se instale correctamente
- **Deploy Logs**: Verifica que uvicorn inicie sin errores

### 2. Verificar Endpoints

Obtén la URL de Railway (ejemplo: `https://xxx.up.railway.app`) y prueba:

```bash
# Health check
curl https://tu-app.up.railway.app/health

# Endpoint de prueba
curl https://tu-app.up.railway.app/

# API de empresas
curl https://tu-app.up.railway.app/api/empresas
```

### 3. Verificar Playwright

Prueba un endpoint que use web scraping:

```bash
# Consulta RUC (SUNAT)
curl -X POST https://tu-app.up.railway.app/api/consulta-ruc \
  -H "Content-Type: application/json" \
  -d '{"ruc": "20123456789"}'
```

### 4. Actualizar Frontend

Actualiza la variable de entorno en Vercel:

```bash
# .env.production (frontend)
VITE_BACKEND_URL=https://tu-app.up.railway.app
```

Redeploya el frontend en Vercel para que use la nueva URL.

---

## 🐛 Troubleshooting

### Problema: Build falla al instalar Playwright

**Solución:**
```dockerfile
# Asegúrate de que Dockerfile.railway tenga:
RUN apt-get update && apt-get install -y --no-install-recommends \
  ca-certificates curl wget \
  libasound2 libatk1.0-0 ... (todas las dependencias)
```

### Problema: Error "Address already in use"

**Solución:**
Railway maneja `$PORT` automáticamente. Verifica que el `CMD` use:
```dockerfile
CMD exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}
```

### Problema: Timeout en healthcheck

**Solución:**
Aumenta el timeout en `railway.toml`:
```toml
[deploy]
healthcheckTimeout = 300
```

O deshabilita temporalmente el healthcheck en Settings.

### Problema: CORS errors desde frontend

**Solución:**
Verifica que CORS permita tu dominio de Vercel:
```python
# main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # O especifica: ["https://tu-frontend.vercel.app"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Problema: Conexión a Neon falla

**Solución:**
1. Verifica que `NEON_CONNECTION_STRING` esté correcta
2. Asegúrate de incluir `?sslmode=require`
3. Verifica que Neon permita conexiones desde Railway (generalmente sí)

### Problema: Playwright no encuentra browsers

**Solución:**
Verifica que el Dockerfile instale chromium:
```dockerfile
RUN python -m playwright install chromium
```

Y que las variables de entorno estén configuradas:
```bash
PLAYWRIGHT_BROWSERS_PATH=/app/.cache/ms-playwright
BROWSER_HEADLESS=true
```

---

## 📊 Comparación de Costos

### Cloud Run (Estimado)
- **Compute:** ~$20-40/mes (4GB RAM, 2 vCPU)
- **Requests:** Variable según tráfico
- **Bandwidth:** Incluido

### Railway
- **Hobby Plan:** $5/mes + $0.000463/GB-hr
- **Pro Plan:** $20/mes (incluye más recursos)
- **Starter Plan:** $5/mes crédito gratis

💡 **Recomendación:** Empieza con Hobby Plan para desarrollo/pruebas, luego escala a Pro si necesitas.

---

## 🎯 Próximos Pasos

1. ✅ Despliega en Railway
2. ✅ Verifica todos los endpoints
3. ✅ Actualiza frontend con nueva URL
4. ✅ Configura monitoreo (Railway tiene métricas integradas)
5. ✅ Configura alertas en Railway Settings
6. 📏 Actualiza documentación del proyecto
7. 🔐 Configura secretos adicionales si son necesarios

---

## 📞 Soporte

- **Railway Docs:** https://docs.railway.app
- **Railway Discord:** https://discord.gg/railway
- **Playwright Docs:** https://playwright.dev

---

## 📏 Notas Adicionales

### Railway vs Cloud Run: ¿Por qué migrar?

✅ **Ventajas de Railway:**
- Setup más simple y rápido
- CI/CD automático con GitHub
- Interface más intuitiva
- Mejor precio para proyectos pequeños/medianos
- Soporte excelente para Dockerfile
- Métricas y logs integrados

⚠️ **Consideraciones:**
- Menos escalabilidad automática que Cloud Run
- Menos regiones disponibles
- Límites de recursos según plan

### Compatibilidad con Playwright

Railway soporta Playwright perfectamente con Dockerfile. El Dockerfile incluye todas las dependencias necesarias para que Chromium headless funcione sin problemas.

### Monitoreo

Railway incluye:
- **Metrics:** CPU, Memory, Network
- **Logs:** Real-time deployment y runtime logs
- **Uptime:** Monitoring automático
- **Alerts:** Configurables por email/webhook

---

**¡Migración completada! 🎉**

Si encuentras problemas, revisa los logs en Railway Dashboard o consulta la documentación oficial.
