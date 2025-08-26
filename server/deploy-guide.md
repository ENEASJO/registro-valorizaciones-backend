# Guía de Despliegue - Sistema de Valorizaciones

## 🚀 Configuración para Producción

### Backend (Vercel)

1. **Configurar variables de entorno en Vercel:**
   ```bash
   vercel env add TURSO_DATABASE_URL
   # Usar: libsql://registro-de-valorizaciones-eneasjo.aws-us-east-2.turso.io
   
   vercel env add TURSO_AUTH_TOKEN
   # Usar el token JWT de Turso
   ```

2. **Desplegar backend:**
   ```bash
   cd /home/usuario/PROYECTOS/registro-valorizaciones/server
   vercel --prod
   ```

### Frontend (Vercel - separado)

1. **Actualizar URL del backend en el frontend:**
   ```javascript
   // En el archivo de configuración del frontend
   const API_BASE_URL = process.env.NODE_ENV === 'production' 
     ? 'https://tu-backend.vercel.app' 
     : 'http://localhost:8000'
   ```

2. **Desplegar frontend:**
   ```bash
   cd /home/usuario/PROYECTOS/registro-valorizaciones/client
   vercel --prod
   ```

## ✅ Estado Actual

### Local (Funcionando ✅)
- ✅ Base de datos Turso conectada
- ✅ 4 tablas creadas (empresas, representantes, obras, valorizaciones)
- ✅ CRUD completo implementado
- ✅ Endpoints funcionando
- ✅ Test completo exitoso

### Pendiente de Despliegue
- 📦 Backend en Vercel con variables de entorno Turso
- 🌐 Frontend actualizado con nueva URL del backend
- 🔗 Conexión frontend-backend en producción

## 📋 Comandos de Verificación

### Verificar estado local:
```bash
python test_complete_system.py
```

### Verificar endpoints después del despliegue:
```bash
curl https://tu-backend.vercel.app/health
curl https://tu-backend.vercel.app/api/empresas
```

## 🏗️ Arquitectura Final

```
Frontend (Vercel) → Backend (Vercel) → Turso Database (Cloud)
     ↓                   ↓                    ↓
Vite/React         FastAPI/Python      SQLite en la nube
```

## 🔑 Variables de Entorno Requeridas

```bash
TURSO_DATABASE_URL=libsql://registro-de-valorizaciones-eneasjo.aws-us-east-2.turso.io
TURSO_AUTH_TOKEN=eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9...
```

## 🌐 URLs Esperadas (después del despliegue)

- Backend: `https://registro-valorizaciones-server.vercel.app`
- Frontend: `https://registro-valorizaciones.vercel.app`
- Base de datos: Turso (ya configurada)

## ⚠️ Notas Importantes

1. Las variables de entorno deben configurarse tanto para `development`, `preview`, y `production`
2. El frontend debe actualizarse para usar la URL del backend en producción
3. Verificar CORS en producción
4. Cloud Run solo mantiene Playwright (scraping) - el resto va a Vercel