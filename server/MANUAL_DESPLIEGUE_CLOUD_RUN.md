# Manual de Despliegue - Playwright en Cloud Run

## ✅ Estado Actual del Proyecto

**FUNCIONA LOCALMENTE**: La extracción de datos de consorcios desde OSCE está funcionando perfectamente en el entorno local.

### Test Exitoso Local
```bash
cd server
python3 test_enhanced_osce_specific.py
```

**Resultados del Test:**
- ✅ **Razón Social**: CORPORACION ALLIN RURAJ S.A.C.
- ✅ **Integrantes del Consorcio**: 2/2 extraídos correctamente
  - SILVA SIGUEÑAS JULIO ROGER (DNI: 7523236) - GERENTE GENERAL
  - BLAS BERNACHEA ANDRU STALIN (DNI: 71918858) - SOCIO
- ✅ **Email**: rvcontabilidad.ap@gmail.com
- ✅ **Especialidades**: CATEGORIA A

## 🚀 Pasos para Desplegar en Cloud Run

### 1. Autenticación con Google Cloud
```bash
# Autenticar con Google Cloud (requiere navegador)
gcloud auth login

# Verificar configuración
gcloud config list

# Configurar proyecto si es necesario
gcloud config set project valoraciones-app-cloud-run
```

### 2. Habilitar APIs necesarias
```bash
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

### 3. Ejecutar despliegue automatizado
```bash
cd server
chmod +x deploy-valoraciones-cloudrun.sh
./deploy-valoraciones-cloudrun.sh
```

### 4. Configuración específica para Playwright

El proyecto ya incluye todas las optimizaciones para Cloud Run:

#### Dockerfile.cloudrun - Configuración Optimizada
- ✅ **Multi-stage build** para reducir tamaño
- ✅ **Dependencias del sistema** para Chromium
- ✅ **Fuentes compatibles** con Debian
- ✅ **Usuario no-root** para seguridad
- ✅ **Variables de entorno** específicas para Playwright

#### Variables de Entorno Críticas
```bash
BROWSER_HEADLESS=true
PLAYWRIGHT_BROWSERS_PATH=/home/app/.cache/ms-playwright
PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=0
PLAYWRIGHT_CHROMIUM_ARGS="--no-sandbox,--disable-setuid-sandbox,--disable-dev-shm-usage,--disable-gpu,--no-first-run,--no-zygote"
```

#### Recursos Cloud Run
- **Memoria**: 4Gi (requerido para Playwright)
- **CPU**: 2 vCPUs
- **Timeout**: 900 segundos
- **Concurrency**: 50
- **Execution Environment**: gen2

## 🧪 Endpoints para Probar Extracción de Consorcios

Una vez desplegado, probar estos endpoints:

### 1. Health Check
```bash
curl https://valoraciones-backend-503600768755.us-central1.run.app/health
```

### 2. Consulta OSCE - Extracción de Consorcios
```bash
# RUC de prueba que funciona localmente
curl "https://valoraciones-backend-503600768755.us-central1.run.app/consulta-osce/20606881666"
```

### 3. Consulta consolidada (SUNAT + OSCE)
```bash
curl "https://valoraciones-backend-503600768755.us-central1.run.app/consulta-ruc-consolidada/20606881666"
```

### 4. Gestión de Empresas
```bash
# Listar empresas
curl "https://valoraciones-backend-503600768755.us-central1.run.app/api/empresas"

# Crear empresa
curl -X POST "https://valoraciones-backend-503600768755.us-central1.run.app/api/empresas" \
  -H "Content-Type: application/json" \
  -d '{"ruc":"20606881666","razon_social":"CORPORACION ALLIN RURAJ S.A.C."}'
```

## 🔧 Troubleshooting

### Si el despliegue falla por autenticación:
```bash
# Re-autenticar
gcloud auth application-default login

# Verificar permisos
gcloud projects get-iam-policy valoraciones-app-cloud-run
```

### Si Playwright falla en Cloud Run:
```bash
# Ver logs
gcloud run services logs read valoraciones-backend --region us-central1

# Logs en tiempo real
gcloud run services logs tail valoraciones-backend --region us-central1
```

### Errores comunes y soluciones:
1. **"Browser not found"**: Verificar que PLAYWRIGHT_BROWSERS_PATH esté configurado
2. **"Permission denied"**: Verificar usuario no-root en Dockerfile
3. **"Timeout"**: Aumentar timeout o reducir concurrency

## 📊 Métricas de Éxito

Una vez desplegado, verificar:
- ✅ Health check responde 200
- ✅ Endpoint OSCE extrae integrantes de consorcios
- ✅ Response time < 30 segundos
- ✅ No errores 5xx en logs

## 🎯 Objetivo Cumplido

Con este despliegue podrás:
1. **Automatizar extracción** de datos de consorcios desde OSCE
2. **Evitar entrada manual** de información de integrantes
3. **Obtener datos actualizados** directamente de la fuente oficial
4. **Integrar** con tu frontend en Vercel

La funcionalidad ya está probada y funcionando localmente. Solo falta completar el despliegue en Cloud Run.