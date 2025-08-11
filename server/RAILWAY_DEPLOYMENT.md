# Guía de Despliegue en Railway - API de Valorizaciones

## 🚀 Preparación Completa para Railway

Esta guía proporciona instrucciones paso a paso para desplegar exitosamente el backend FastAPI en Railway.

## 📋 Pre-requisitos

- Cuenta en Railway (https://railway.app)
- Cuenta en GitHub
- El código debe estar en un repositorio de GitHub

## 🔧 Archivos de Configuración Incluidos

### ✅ Archivos Optimizados para Railway:

1. **`Dockerfile`** - Optimizado para Railway con:
   - Dependencias de Playwright pre-instaladas
   - Configuración específica para Railway
   - Comando de inicio con fallback
   - Variables de entorno dinámicas (`$PORT`)

2. **`railway.toml`** - Configuración específica de Railway:
   - Health checks configurados
   - Variables de entorno predefinidas
   - Configuración de build optimizada

3. **`requirements.txt`** - Dependencias optimizadas:
   - Versiones compatibles con Railway
   - Dependencias mínimas requeridas
   - Redis opcional para cache

4. **`.env.example`** - Template de variables de entorno
5. **`start.py`** - Script de inicio optimizado para Railway

## 🚂 Pasos de Despliegue en Railway

### Paso 1: Conectar Repositorio GitHub

1. **Ir a Railway Dashboard**
   ```
   https://railway.app/dashboard
   ```

2. **Crear Nuevo Proyecto**
   - Click en "New Project"
   - Seleccionar "Deploy from GitHub repo"
   - Autorizar acceso a GitHub si es necesario

3. **Seleccionar Repositorio**
   - Buscar: `valoraciones-app`
   - Click en el repositorio

4. **Configurar Directorio Root**
   - En la configuración del servicio
   - Set "Root Directory" to: `server/`
   - Esto le dice a Railway que use solo la carpeta del backend

### Paso 2: Configurar Variables de Entorno

En el dashboard de Railway, ir a la pestaña "Variables" y configurar:

#### 🔴 VARIABLES CRÍTICAS (Requeridas):

```bash
# Server Configuration
PORT=8000
HOST=0.0.0.0
RAILWAY_ENVIRONMENT=true

# CORS - CRÍTICO para Vercel frontend
ALLOWED_ORIGINS=https://*.vercel.app,https://tu-app.vercel.app,http://localhost:5173,http://localhost:3000
ALLOW_CREDENTIALS=true

# Browser Configuration
BROWSER_HEADLESS=true
MAX_BROWSERS=2
MAX_CONTEXTS_PER_BROWSER=3

# Performance
REQUEST_TIMEOUT=30
SCRAPING_TIMEOUT=25
CACHE_TTL=3600
WEB_CONCURRENCY=1

# Security
SECRET_KEY=genera-una-clave-secreta-aqui-railway-prod-2024

# Logging
LOG_LEVEL=INFO
DEBUG=false
```

#### 🟡 VARIABLES OPCIONALES (Recomendadas):

```bash
# Application Info
APP_NAME=API de Valorizaciones
APP_VERSION=1.0.0
APP_DESCRIPTION=Backend para el sistema de registro de valorizaciones

# Rate Limiting
RATE_LIMIT_REQUESTS=100

# Monitoring
ENABLE_METRICS=true
METRICS_RETENTION=1000

# Browser Args for Railway
BROWSER_ARGS=--no-sandbox,--disable-dev-shm-usage,--disable-blink-features=AutomationControlled
```

### Paso 3: Configurar Build y Deploy

1. **Build Configuration**
   - Railway debería detectar automáticamente el `Dockerfile`
   - Verificar que "Builder" esté set a "Dockerfile"

2. **Health Check**
   - Railway usará automáticamente `/health` (configurado en railway.toml)
   - Timeout: 30 segundos

3. **Deploy**
   - Click "Deploy"
   - Observar los logs durante el build

## 📊 Verificación del Despliegue

### 1. Comprobar Build Logs
```bash
# Logs que debes ver:
✅ Dockerfile detected
✅ Installing Python dependencies
✅ Installing Playwright browsers
✅ Starting server at http://0.0.0.0:$PORT
✅ Health check passing at /health
```

### 2. Probar Endpoints Básicos

Una vez desplegado, probar estas URLs (reemplazar con tu dominio de Railway):

```bash
# Health Check
https://tu-app-railway.app/health

# API Root
https://tu-app-railway.app/

# Consulta RUC de prueba
https://tu-app-railway.app/consulta-ruc/20100047218

# Consulta OSCE de prueba  
https://tu-app-railway.app/consulta-osce/20100047218
```

### 3. Verificar CORS

Desde el frontend en Vercel, hacer una request de prueba:

```javascript
// Test CORS desde tu frontend en Vercel
fetch('https://tu-app-railway.app/health')
  .then(response => response.json())
  .then(data => console.log('CORS OK:', data))
  .catch(error => console.error('CORS Error:', error));
```

## 🔧 Configuración del Frontend (Vercel)

### Actualizar URLs en el Frontend

En tu aplicación de Vercel, actualizar la URL base de la API:

```typescript
// En tu servicio de API
const API_BASE_URL = process.env.NODE_ENV === 'production' 
  ? 'https://tu-app-railway.app'  // ← Tu URL de Railway
  : 'http://localhost:8000';
```

### Variables de Entorno en Vercel

Agregar en Vercel Dashboard → Settings → Environment Variables:

```bash
NEXT_PUBLIC_API_URL=https://tu-app-railway.app
```

## 🚨 Troubleshooting

### Problema: Build Falla por Playwright

**Solución:**
```dockerfile
# Ya incluido en el Dockerfile optimizado:
RUN playwright install --with-deps chromium
```

### Problema: CORS Errors

**Verificar:**
1. Variable `ALLOWED_ORIGINS` incluye tu dominio de Vercel
2. Incluir tanto `*.vercel.app` como tu dominio específico
3. Verificar que `ALLOW_CREDENTIALS=true`

### Problema: Timeout en Requests

**Ajustar en Railway Variables:**
```bash
REQUEST_TIMEOUT=45
SCRAPING_TIMEOUT=35
BROWSER_TIMEOUT=40000
```

### Problema: Out of Memory

**Reducir en Railway Variables:**
```bash
MAX_BROWSERS=1
MAX_CONTEXTS_PER_BROWSER=2
WEB_CONCURRENCY=1
```

## 📈 Optimizaciones Post-Deploy

### 1. Monitoring
- Railway proporciona métricas automáticas
- Monitorear CPU y memoria usage
- Configurar alertas si es necesario

### 2. Scaling
- Railway escala automáticamente
- Para alto tráfico, considerar upgrade de plan

### 3. Performance
- El cache local está habilitado por defecto
- Para mejor performance, agregar Redis (Railway Add-on)

## 🔄 CI/CD Automático

Railway se redespliega automáticamente en cada push a la rama main:

1. **Push al repositorio GitHub**
2. **Railway detecta cambios automáticamente**
3. **Rebuild y redeploy automático**
4. **Health check verification**
5. **Nuevo deployment disponible**

## 📞 Contacto y URLs Importantes

- **Railway Dashboard:** https://railway.app/dashboard
- **Documentación Railway:** https://docs.railway.app
- **Support Railway:** https://help.railway.app

## ✅ Checklist Final

- [ ] Repositorio conectado a Railway
- [ ] Root directory configurado a `server/`
- [ ] Variables de entorno configuradas
- [ ] Build successful
- [ ] Health check passing  
- [ ] CORS configurado para Vercel
- [ ] Frontend actualizado con nueva API URL
- [ ] Endpoints de prueba funcionando
- [ ] Tests desde frontend exitosos

---

¡Tu API está lista para recibir requests desde el frontend en Vercel! 🚀