# 🚀 Guía de Migración a Lambda Container con Playwright

## Resumen Ejecutivo

Esta guía documenta la migración completa del backend desde la versión mock actual a una implementación completa con web scraping real de SUNAT y OSCE usando AWS Lambda Container con Playwright.

### Estado Actual vs. Estado Objetivo

| Aspecto | Estado Actual | Estado Objetivo |
|---------|---------------|-----------------|
| **Backend** | AWS Lambda con datos mock | AWS Lambda Container con Playwright |
| **Datos** | Datos estáticos predefinidos | Web scraping real de SUNAT/OSCE |
| **Arquitectura** | ZIP deployment | Docker Container deployment |
| **Capacidades** | Limitada a datos mock | Scraping dinámico en tiempo real |
| **Performance** | ~1-2 segundos | ~10-30 segundos (scraping real) |
| **URL Lambda** | `https://uazzhllimzceeg2p2xlds2z2re0ylkna.lambda-url.us-east-1.on.aws` | Misma URL (actualizada) |

## 📂 Archivos de Migración Preparados

### Archivos Principales
- `/server/main_lambda.py` - API FastAPI optimizada para Lambda Container
- `/server/lambda_function.py` - Entry point de Lambda con Mangum
- `/server/lambda_config.py` - Configuración específica de Playwright para Lambda
- `/server/Dockerfile.lambda` - Container optimizado con Playwright
- `/server/requirements-lambda-container.txt` - Dependencias completas

### Servicios de Scraping
- `/server/app/services/sunat_service_lambda.py` - Scraping SUNAT optimizado
- `/server/app/services/osce_service_lambda.py` - Scraping OSCE optimizado

### Scripts de Deployment
- `/server/deploy-lambda-container.sh` - Script automatizado de deployment
- `/server/migrate-to-playwright.sh` - Script de migración completa
- `/server/template-container.yaml` - CloudFormation template

### Testing
- `/server/test-consolidado-lambda.py` - Suite de pruebas para endpoints

## 🔧 Configuración Técnica

### Optimizaciones de Playwright para Lambda

```python
# Configuración optimizada en lambda_config.py
CHROMIUM_ARGS = [
    '--no-sandbox',
    '--disable-setuid-sandbox',
    '--disable-dev-shm-usage',
    '--single-process',  # Crítico para Lambda
    '--disable-gpu',
    '--disable-software-rasterizer',
    # ... más optimizaciones
]
```

### Configuración de CORS

```python
# CORS actualizado para Vercel en main_lambda.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "https://registro-valorizaciones.vercel.app",
        "https://*.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    max_age=3600
)
```

### Recursos de Lambda Recomendados

```yaml
# En template-container.yaml
MemorySize: 2048  # MB - Necesario para Playwright
Timeout: 900      # 15 minutos - Para operaciones de scraping
ReservedConcurrencyLimit: 5  # Control de costos
```

## 🚀 Proceso de Deployment

### Opción 1: Deployment Automatizado (Recomendado)

```bash
cd /home/usuario/PROYECTOS/registro-valorizaciones/server

# 1. Configurar AWS CLI
aws configure
# Ingresar Access Key, Secret Key, Region (us-east-1), Output (json)

# 2. Ejecutar script de migración
./migrate-to-playwright.sh

# 3. Ejecutar deployment automatizado
./deploy-lambda-container.sh
```

### Opción 2: Deployment Manual

```bash
# 1. Crear repositorio ECR
aws ecr create-repository --repository-name valoraciones-api-lambda --region us-east-1

# 2. Obtener Account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# 3. Login a ECR
aws ecr get-login-password --region us-east-1 | \
docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

# 4. Construir imagen
docker build -f Dockerfile.lambda -t valoraciones-api-lambda:latest .

# 5. Tag y push
docker tag valoraciones-api-lambda:latest $ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/valoraciones-api-lambda:latest
docker push $ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/valoraciones-api-lambda:latest

# 6. Deploy con CloudFormation
aws cloudformation deploy \
  --template-file template-container.yaml \
  --stack-name valoraciones-api-playwright-stack \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides \
    FunctionName=valoraciones-api-playwright \
    Stage=prod \
    MemorySize=2048 \
    Timeout=900
```

## 🧪 Testing Post-Deployment

### 1. Health Check
```bash
curl https://uazzhllimzceeg2p2xlds2z2re0ylkna.lambda-url.us-east-1.on.aws/health
```

### 2. Consulta SUNAT
```bash
curl "https://uazzhllimzceeg2p2xlds2z2re0ylkna.lambda-url.us-east-1.on.aws/consulta-ruc/20100070970"
```

### 3. Consulta OSCE
```bash
curl "https://uazzhllimzceeg2p2xlds2z2re0ylkna.lambda-url.us-east-1.on.aws/consulta-osce/20100070970"
```

### 4. Consulta Consolidada (Principal)
```bash
curl "https://uazzhllimzceeg2p2xlds2z2re0ylkna.lambda-url.us-east-1.on.aws/consulta-ruc-consolidada/20100070970"
```

### 5. Suite de Pruebas Automatizada
```bash
cd /home/usuario/PROYECTOS/registro-valorizaciones/server
python3 test-consolidado-lambda.py
```

## 🌐 Configuración Frontend

### Variables de Entorno Actualizadas

```bash
# .env.production (ya configurado)
VITE_BACKEND_URL=https://uazzhllimzceeg2p2xlds2z2re0ylkna.lambda-url.us-east-1.on.aws
VITE_ENVIRONMENT=production
VITE_API_TIMEOUT=45000  # Aumentado para scraping
VITE_RETRY_ATTEMPTS=2
```

### Actualización en src/config/api.ts

```typescript
// Timeout optimizado para Playwright
export const API_TIMEOUT = parseInt(import.meta.env.VITE_API_TIMEOUT || '45000');
export const RETRY_ATTEMPTS = parseInt(import.meta.env.VITE_RETRY_ATTEMPTS || '2');
```

## 📊 Endpoints Disponibles

| Endpoint | Método | Descripción | Tiempo Estimado |
|----------|--------|-------------|-----------------|
| `/health` | GET | Health check | ~1s |
| `/consulta-ruc/{ruc}` | GET | Solo datos SUNAT | ~10-15s |
| `/consulta-osce/{ruc}` | GET | Solo datos OSCE | ~15-25s |
| `/consulta-ruc-consolidada/{ruc}` | GET | SUNAT + OSCE | ~20-35s |
| `/buscar` | POST | Búsqueda RUC | ~10-15s |
| `/docs` | GET | Documentación API | ~1s (solo dev) |

## ⚡ Optimizaciones Implementadas

### 1. Lazy Loading
```python
# Importaciones bajo demanda para reducir cold start
def lazy_import_playwright():
    global async_playwright, PlaywrightTimeoutError
    from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
```

### 2. Browser Configuration
```python
# Args optimizados para Lambda Container
browser_args = [
    '--no-sandbox',
    '--disable-dev-shm-usage',
    '--single-process',
    '--disable-gpu',
    # ... más optimizaciones
]
```

### 3. Timeout Management
```python
# Timeouts diferenciados por tipo de consulta
timeout_persona_natural = 25000  # Más tiempo para personas naturales
timeout_persona_juridica = 20000  # Menos tiempo para jurídicas
```

### 4. Error Handling
```python
# Manejo robusto de errores con fallbacks
try:
    resultado = await scraping_real()
except Exception as e:
    logger.error(f"Error en scraping: {e}")
    return error_response_with_context()
```

## 🔍 Monitoring y Debugging

### CloudWatch Logs
```bash
# Monitorear logs en tiempo real
aws logs tail /aws/lambda/valoraciones-api-playwright-prod --follow
```

### Métricas Importantes
- **Duration**: Tiempo de ejecución (objetivo: <30s)
- **Errors**: Rate de errores (objetivo: <5%)
- **Memory Usage**: Uso de memoria (objetivo: <80% de 2GB)
- **Cold Starts**: Frecuencia de cold starts

### Debug Screenshots
```python
# En caso de error, se captura screenshot (solo en DEBUG=true)
if os.getenv('DEBUG', 'false').lower() == 'true':
    await page.screenshot(path=f'/tmp/error_{ruc}.png')
```

## 🚨 Consideraciones Importantes

### 1. Costos
- Lambda con 2GB RAM: ~$0.0000166667 por GB-segundo
- Scraping promedio 20s: ~$0.00067 por consulta
- ECR storage: ~$0.10 por GB por mes

### 2. Límites
- Timeout máximo: 15 minutos
- Memoria máxima: 10GB (usando 2GB)
- Payload máximo: 6MB
- Concurrencia: 5 (configurado para control de costos)

### 3. Reliability
- Reintentos automáticos en caso de timeout
- Fallback a datos básicos si scraping falla
- Circuit breaker para sitios caídos

## 📋 Checklist de Migración

### Pre-Deployment
- [x] ✅ Verificar archivos de configuración
- [x] ✅ Actualizar CORS para Vercel
- [x] ✅ Configurar variables de entorno frontend
- [x] ✅ Preparar scripts de deployment
- [x] ✅ Crear suite de pruebas

### Deployment
- [ ] 🔄 Configurar AWS CLI con credenciales
- [ ] 🔄 Ejecutar script de migración
- [ ] 🔄 Validar construcción de imagen Docker
- [ ] 🔄 Push a ECR repository
- [ ] 🔄 Deploy con CloudFormation
- [ ] 🔄 Verificar Function URL activa

### Post-Deployment
- [ ] 🔄 Ejecutar health check
- [ ] 🔄 Probar endpoint consolidado
- [ ] 🔄 Validar scraping SUNAT
- [ ] 🔄 Validar scraping OSCE
- [ ] 🔄 Monitorear logs CloudWatch
- [ ] 🔄 Deploy frontend a Vercel

### Validation
- [ ] 🔄 Probar desde frontend Vercel
- [ ] 🔄 Verificar CORS funcionando
- [ ] 🔄 Validar timeouts apropiados
- [ ] 🔄 Confirmar manejo de errores
- [ ] 🔄 Testing con RUCs reales

## 🎯 Resultados Esperados

### Antes (Datos Mock)
```json
{
  "success": true,
  "data": {
    "ruc": "20123456789",
    "razon_social": "CONSTRUCTORA TEST S.R.L.",
    "fuente": "CONSOLIDADO_MOCK"
  }
}
```

### Después (Scraping Real)
```json
{
  "success": true,
  "data": {
    "ruc": "20100070970",
    "razon_social": "BANCO DE CREDITO DEL PERU",
    "estado_sunat": "ACTIVO",
    "sunat_info": {
      "domicilio_fiscal": "AV. CANAVAL Y MOREYRA NRO. 522...",
      "representantes": [...]
    },
    "osce_info": {
      "especialidades": [...],
      "integrantes": [...],
      "estado_registro": "HABILITADO"
    },
    "fuentes_consultadas": ["SUNAT", "OSCE"]
  }
}
```

## 📞 Soporte y Troubleshooting

### Errores Comunes

1. **Cold Start Timeout**
   - Aumentar timeout en template-container.yaml
   - Verificar optimizaciones de Playwright

2. **Memory Issues**
   - Aumentar MemorySize a 3008 MB si es necesario
   - Revisar args de Chromium

3. **CORS Errors**
   - Verificar allow_origins en main_lambda.py
   - Comprobar configuración de Function URL

4. **Scraping Failures**
   - Revisar logs CloudWatch
   - Verificar conectividad a SUNAT/OSCE
   - Comprobar User-Agent y headers

### Logs de Debug
```bash
# Ver logs específicos de función
aws logs filter-log-events \
  --log-group-name /aws/lambda/valoraciones-api-playwright-prod \
  --filter-pattern "ERROR"
```

---

**¡Migración preparada exitosamente! 🎉**

La infraestructura está lista para migrar de datos mock a web scraping real con máxima reliability y performance.