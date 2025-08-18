# Configuración de Variables de Entorno en Vercel

## 🎯 Variables CRÍTICAS para Cloud Run con Playwright

Ve a: **Vercel Dashboard > Tu Proyecto > Settings > Environment Variables**

### Variables a configurar:

| Variable | Valor | Descripción |
|----------|--------|-------------|
| `VITE_BACKEND_URL` | `https://valoraciones-backend-503600768755.us-central1.run.app` | Backend Cloud Run con Playwright |
| `VITE_ENVIRONMENT` | `production` | Entorno de producción |
| `VITE_API_TIMEOUT` | `45000` | Timeout para Playwright (45 segundos) |
| `VITE_RETRY_ATTEMPTS` | `2` | Número de reintentos |
| `VITE_LOG_LEVEL` | `error` | Nivel de logging |
| `VITE_DEBUG` | `false` | Debug deshabilitado |

## 🚀 Después de configurar:

1. **Redeploy** el proyecto en Vercel
2. O espera el **auto-deploy** del próximo push a main

## ✅ Verificación:

Una vez desplegado, puedes probar:
- Health check: `https://tu-app.vercel.app`
- Console del navegador debe mostrar la URL correcta
- Consultas RUC deben usar Cloud Run automáticamente

## 🎯 Resultado esperado:

Tu frontend en Vercel se conectará automáticamente a Cloud Run para:
- ✅ Extracción de datos SUNAT
- ✅ Extracción de consorcios OSCE con Playwright
- ✅ Consultas consolidadas