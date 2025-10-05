# 🚄 Deployment en Railway - Resumen Ejecutivo

## 📏 Checklist de Migración

### ✅ Antes del Deploy

- [ ] Cuenta en Railway creada
- [ ] Repositorio GitHub conectado a Railway
- [ ] Base de datos Neon funcionando
- [ ] Variables de entorno preparadas

### ✅ Archivos de Configuración

Los siguientes archivos ya están creados y listos:

- ✅ `Dockerfile.railway` - Dockerfile optimizado para Railway
- ✅ `railway.json` - Configuración JSON de Railway
- ✅ `railway.toml` - Configuración TOML de Railway
- ✅ `.env.railway.example` - Template de variables de entorno
- ✅ `.gitignore` - Actualizado con exclusiones de Railway

### ✅ Durante el Deploy

1. **Crear Proyecto en Railway**
   - Ir a https://railway.app
   - "New Project" → "Deploy from GitHub repo"
   - Seleccionar `registro-valorizaciones-backend`

2. **Configurar Variables de Entorno**

   Variables CRÍTICAS (copiar de Cloud Run):
   ```
   NEON_CONNECTION_STRING=postgresql://...
   ENVIRONMENT=production
   DEBUG=false
   LOG_LEVEL=INFO
   ```

3. **Configurar Build**
   - Railway detectará automáticamente `railway.toml`
   - Verificar que use `Dockerfile.railway`

4. **Primer Deploy**
   - Railway desplegará automáticamente
   - Monitorear logs en el dashboard

### ✅ Después del Deploy

- [ ] Verificar endpoint `/health`
- [ ] Probar endpoint `/`
- [ ] Probar endpoint de empresas
- [ ] Probar consulta RUC (Playwright)
- [ ] Actualizar URL en frontend (Vercel)
- [ ] Verificar CORS
- [ ] Probar flujo completo de valorizaciones

---

## 🔧 Variables de Entorno Requeridas

### Críticas (sin estas el sistema no funciona)

```bash
NEON_CONNECTION_STRING=postgresql://user:password@ep-xxx.neon.tech/valoraciones?sslmode=require
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
HOST=0.0.0.0
BROWSER_HEADLESS=true
```

### Opcionales

```bash
ENABLE_PROXY_MIDDLEWARE=false
APIS_NET_PE_TOKEN=tu-token
WHATSAPP_API_TOKEN=tu-token
WHATSAPP_PHONE_NUMBER_ID=tu-phone-id
```

⚠️ **Nota:** Railway configura `PORT` automáticamente, NO la agregues manualmente.

---

## 🚀 Comandos Rápidos

### Deploy Manual con Railway CLI

```bash
# Instalar CLI
npm i -g @railway/cli

# Login
railway login

# Link al proyecto
railway link

# Deploy
railway up
```

### Verificación Post-Deploy

```bash
# Obtén tu URL de Railway
RAILWAY_URL="https://tu-app.up.railway.app"

# Health check
curl $RAILWAY_URL/health

# API root
curl $RAILWAY_URL/

# Consulta RUC (requiere Playwright)
curl -X POST $RAILWAY_URL/api/consulta-ruc \
  -H "Content-Type: application/json" \
  -d '{"ruc": "20123456789"}'
```

---

## 📊 Diferencias Cloud Run → Railway

| Aspecto | Cloud Run | Railway |
|---------|-----------|---------|
| **Setup** | Complejo (cloudbuild.yaml) | Simple (railway.toml) |
| **CI/CD** | Google Cloud Build | GitHub automático |
| **Puerto** | Manual ($PORT) | Automático ($PORT) |
| **Logs** | Cloud Logging | Dashboard integrado |
| **Healthcheck** | Config manual | railway.toml |
| **Precio** | ~$20-40/mes | $5-20/mes |

---

## 🐛 Problemas Comunes y Soluciones

### 1. Build falla con Playwright

**Error:** `playwright install chromium` falla

**Solución:** Verifica que `Dockerfile.railway` tenga todas las dependencias:
```dockerfile
RUN apt-get update && apt-get install -y \
  ca-certificates curl wget libasound2 libatk1.0-0 ...
```

### 2. Healthcheck timeout

**Error:** Healthcheck falla después de 100s

**Solución:** Aumenta timeout en `railway.toml`:
```toml
healthcheckTimeout = 300
```

### 3. CORS errors desde Vercel

**Error:** Frontend no puede conectar al backend

**Solución:** Verifica CORS en `main.py`:
```python
allow_origins=["*"]  # O tu dominio específico
```

### 4. Error de conexión a Neon

**Error:** `connection refused` o `SSL required`

**Solución:** Agrega `?sslmode=require` al final de `NEON_CONNECTION_STRING`:
```
postgresql://user:pass@host/db?sslmode=require
```

---

## 📱 Actualizar Frontend

Después de desplegar en Railway, actualiza el frontend:

### En Vercel

1. Ve a tu proyecto en Vercel
2. Settings → Environment Variables
3. Edita `VITE_BACKEND_URL`:
   ```
   VITE_BACKEND_URL=https://tu-app.up.railway.app
   ```
4. Redeploy el frontend

### En .env.production (local)

```bash
VITE_BACKEND_URL=https://tu-app.up.railway.app
```

---

## 📚 Documentación Adicional

- **Guía Completa:** Ver `RAILWAY_MIGRATION_GUIDE.md`
- **Railway Docs:** https://docs.railway.app
- **Playwright en Railway:** Funciona out-of-the-box con Dockerfile

---

## ✅ Checklist Final

- [ ] Backend desplegado en Railway
- [ ] Todas las variables de entorno configuradas
- [ ] Healthcheck pasando
- [ ] Endpoints funcionando
- [ ] Playwright funcionando (consulta RUC)
- [ ] Frontend actualizado con nueva URL
- [ ] CORS configurado correctamente
- [ ] Monitoreo activado en Railway
- [ ] Documentación actualizada

---

## 🎯 Próximos Pasos Opcionales

1. **Dominio Personalizado**
   - Settings → Networking → Custom Domain
   - Agrega tu dominio

2. **Métricas y Alertas**
   - Dashboard → Metrics
   - Configura alertas por email

3. **Staging Environment**
   - Crea un segundo servicio para staging
   - Usa la misma base de datos Neon con schema diferente

4. **Backups Automatizados**
   - Neon tiene backups automáticos
   - Railway tiene snapshots del servicio

---

**¡Listo para producción! 🚀**

Si necesitas ayuda, consulta `RAILWAY_MIGRATION_GUIDE.md` o la documentación de Railway.
