# Configuración de Deployment Optimizada

## Problema
Cuando se actualiza el frontend, también se ejecuta el deployment del backend en Cloud Run, haciendo el proceso más lento.

## Solución

### 1. Google Cloud Build (Backend)
- **Trigger name:** registro-valorizaciones
- **Included files filter:** `backend/**`
- **Ignored files filter:** `frontend/**,*.md,README.md,.vercel/**`

### 2. Vercel (Frontend) 
- **Root Directory:** `frontend/`
- **Build Command:** `npm run build`
- **Output Directory:** `dist`

## Instrucciones

### Configurar Cloud Build Trigger:
1. Ir a Google Cloud Console
2. Cloud Build → Triggers
3. Buscar trigger "registro-valorizaciones"
4. Click "Edit"
5. En "Source" agregar:
   - **Included files filter:** `backend/**`
   - **Ignored files filter:** `frontend/**,*.md,README.md,.vercel/**`
6. Guardar

### Verificar Vercel:
1. Ir a Vercel Dashboard
2. Proyecto: registro-valorizaciones
3. Settings → General
4. **Root Directory:** `frontend/` (si no está configurado)

## Resultado
- Cambios en `frontend/` → Solo deployment Vercel
- Cambios en `backend/` → Solo deployment Cloud Run
- Deployments más rápidos y eficientes