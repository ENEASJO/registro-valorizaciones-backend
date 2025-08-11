# Guía de Deployment AWS Lambda - API de Valorizaciones

Esta guía explica cómo desplegar la API FastAPI de valorizaciones en AWS Lambda con Function URL.

## 📋 Tabla de Contenidos

- [Prerrequisitos](#prerrequisitos)
- [Arquitectura](#arquitectura)
- [Métodos de Deployment](#métodos-de-deployment)
- [Configuración](#configuración)
- [Testing](#testing)
- [Monitoreo](#monitoreo)
- [Troubleshooting](#troubleshooting)

## 🔧 Prerrequisitos

### Software Requerido
- Python 3.11+
- AWS CLI configurado
- AWS SAM CLI (opcional, para deployment con SAM)
- Docker (opcional, para testing local)

### Credenciales AWS
```bash
aws configure
# Ingresa tu Access Key ID, Secret Access Key, región y formato
```

### Permisos IAM Requeridos
- `lambda:*`
- `iam:CreateRole`, `iam:AttachRolePolicy`
- `logs:*`
- `cloudformation:*` (para SAM)

## 🏗️ Arquitectura

```
Frontend (Vercel) → Function URL → Lambda → Playwright → SUNAT/OSCE
                                      ↓
                                  CloudWatch
```

### Componentes:
- **AWS Lambda**: Ejecuta la API FastAPI
- **Function URL**: Endpoint público HTTPS
- **CloudWatch**: Logs y monitoreo
- **Playwright**: Web scraping para SUNAT/OSCE

## 🚀 Métodos de Deployment

### Método 1: Upload Manual (Más Simple)

#### Paso 1: Generar Package ZIP
```bash
# Linux/Mac
./deploy-lambda.sh

# Windows
deploy-lambda.bat
```

#### Paso 2: Crear Función Lambda
1. Ve a AWS Lambda Console
2. Clic en "Create function"
3. Selecciona "Author from scratch"
4. Configuración:
   - **Name**: `valoraciones-api`
   - **Runtime**: Python 3.11
   - **Architecture**: x86_64

#### Paso 3: Upload Code
1. En la función creada, ve a "Code" tab
2. Clic en "Upload from" → ".zip file"
3. Selecciona el archivo `valoraciones-api-deployment.zip`
4. Espera a que se procese

#### Paso 4: Configurar Function URL
1. Ve a "Configuration" → "Function URL"
2. Clic en "Create function URL"
3. Configuración:
   - **Auth type**: NONE
   - **CORS**: Configurar según necesidades
   - **Allowed origins**: `https://*.vercel.app,http://localhost:3000`
   - **Allowed methods**: `GET,POST,PUT,DELETE,OPTIONS,PATCH`
   - **Allow headers**: `*`

#### Paso 5: Configurar Variables de Entorno
Ve a "Configuration" → "Environment variables":

```
ENVIRONMENT=production
DEBUG=false
LAMBDA_FUNCTION_NAME=valoraciones-api
PLAYWRIGHT_TIMEOUT=15000
SUNAT_TIMEOUT=10000
OSCE_TIMEOUT=15000
ALLOWED_ORIGINS=https://*.vercel.app,http://localhost:3000,http://localhost:5173
```

#### Paso 6: Configurar Resources
- **Timeout**: 15 minutos (900 segundos)
- **Memory**: 1024 MB
- **Ephemeral storage**: 512 MB (default)

### Método 2: AWS SAM (Recomendado para Producción)

#### Paso 1: Instalar SAM CLI
```bash
# Mac
brew install aws-sam-cli

# Windows
# Descargar desde: https://github.com/aws/aws-sam-cli/releases/

# Linux
pip install aws-sam-cli
```

#### Paso 2: Build y Deploy
```bash
# Build
sam build

# Deploy primera vez
sam deploy --guided

# Deploy subsecuentes
sam deploy

# Deploy a staging
sam deploy --config-env staging

# Deploy a producción
sam deploy --config-env prod
```

#### Paso 3: Testing Local (Opcional)
```bash
# Instalar dependencias
pip install -r requirements-lambda.txt

# Ejecutar localmente
sam local start-api

# Test endpoint
curl http://localhost:3000/health
```

## ⚙️ Configuración Detallada

### Variables de Entorno

| Variable | Descripción | Valor Recomendado |
|----------|-------------|-------------------|
| `ENVIRONMENT` | Entorno de ejecución | `production` |
| `DEBUG` | Modo debug | `false` |
| `LAMBDA_FUNCTION_NAME` | Nombre de la función | `valoraciones-api` |
| `PLAYWRIGHT_TIMEOUT` | Timeout Playwright | `15000` |
| `SUNAT_TIMEOUT` | Timeout SUNAT | `10000` |
| `OSCE_TIMEOUT` | Timeout OSCE | `15000` |
| `ALLOWED_ORIGINS` | Orígenes CORS | `https://*.vercel.app` |

### Configuración Lambda Recomendada

| Setting | Valor | Justificación |
|---------|-------|---------------|
| **Memory** | 1024 MB | Balance performance/costo para Playwright |
| **Timeout** | 900s (15 min) | Tiempo suficiente para scraping |
| **Architecture** | x86_64 | Compatibilidad con Playwright |
| **Runtime** | Python 3.11 | Última versión estable |
| **Reserved Concurrency** | 10 | Limitar costos |

### Configuración CORS

Para permitir requests desde tu frontend en Vercel:

```json
{
  "AllowCredentials": true,
  "AllowHeaders": ["*"],
  "AllowMethods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
  "AllowOrigins": [
    "https://*.vercel.app",
    "https://valoraciones-app-*.vercel.app",
    "http://localhost:3000",
    "http://localhost:5173"
  ],
  "MaxAge": 86400
}
```

## 🧪 Testing

### 1. Health Check
```bash
curl https://your-function-url.lambda-url.us-east-1.on.aws/health
```

### 2. Consulta RUC
```bash
curl https://your-function-url.lambda-url.us-east-1.on.aws/consulta-ruc/20123456789
```

### 3. Consulta OSCE
```bash
curl https://your-function-url.lambda-url.us-east-1.on.aws/consulta-osce/20123456789
```

### 4. Consulta Consolidada
```bash
curl https://your-function-url.lambda-url.us-east-1.on.aws/consulta-ruc-consolidada/20123456789
```

## 📊 Monitoreo

### CloudWatch Metrics Importantes
- **Duration**: Tiempo de ejecución
- **Errors**: Número de errores
- **Throttles**: Requests limitados
- **Concurrent Executions**: Ejecuciones concurrentes

### CloudWatch Logs
Ubicación: `/aws/lambda/valoraciones-api`

### Alarmas Configuradas
- **Errors**: > 5 errores en 5 minutos
- **Duration**: > 5 minutos promedio
- **Throttles**: > 0 throttles

## 🔧 Troubleshooting

### Problema: Cold Start Lento
**Síntomas**: Primera request toma >10 segundos
**Soluciones**:
- Usar Provisioned Concurrency (costo adicional)
- Implementar warming strategy
- Optimizar imports en código

### Problema: Timeout
**Síntomas**: Requests fallan con timeout
**Soluciones**:
- Aumentar timeout Lambda a 15 minutos
- Optimizar selectores Playwright
- Implementar retry logic

### Problema: Memory Limit
**Síntomas**: OutOfMemoryError
**Soluciones**:
- Aumentar memory a 1536 MB o más
- Cerrar browser correctamente
- Implementar browser pooling

### Problema: CORS Errors
**Síntomas**: Browser bloquea requests
**Soluciones**:
- Verificar Function URL CORS config
- Agregar domain específico a AllowOrigins
- Verificar preflight OPTIONS requests

### Problema: Import Errors
**Síntomas**: Module not found errors
**Soluciones**:
- Verificar requirements-lambda.txt
- Rebuilding package ZIP
- Verificar estructura de directorios

## 🔒 Seguridad

### Recomendaciones de Producción
1. **Function URL Auth**: Considerar cambiar de NONE a AWS_IAM
2. **CORS**: Especificar dominios exactos en lugar de wildcards
3. **Environment Variables**: Usar AWS Secrets Manager para datos sensibles
4. **VPC**: Considerar ejecutar en VPC para mayor aislamiento
5. **Rate Limiting**: Implementar rate limiting en application layer

### Variables Sensibles
Si necesitas manejar datos sensibles (API keys, passwords):

```bash
# Crear secret
aws secretsmanager create-secret --name "valoraciones-api/config" --secret-string '{"api_key":"your-key"}'

# Dar permisos a Lambda
# Agregar política IAM: secretsmanager:GetSecretValue
```

## 💰 Costos Estimados

### Componentes de Costo
- **Lambda execution**: $0.0000166667 por GB-segundo
- **Lambda requests**: $0.20 por 1M requests
- **CloudWatch Logs**: $0.50 por GB almacenado
- **Function URL**: Sin costo adicional

### Estimación Mensual (1000 requests/mes)
- Execution (1024MB, 10s avg): ~$0.17
- Requests: ~$0.0002  
- Logs (aprox 10MB): ~$0.005
- **Total**: ~$0.18/mes

### Optimización de Costos
1. Ajustar memory según uso real
2. Configurar log retention (7-14 días)
3. Usar reserved concurrency para limitar
4. Monitoring con alarmas de budget

## 📚 Referencias

- [AWS Lambda Python Runtime](https://docs.aws.amazon.com/lambda/latest/dg/lambda-python.html)
- [Lambda Function URLs](https://docs.aws.amazon.com/lambda/latest/dg/lambda-urls.html)
- [AWS SAM Documentation](https://docs.aws.amazon.com/serverless-application-model/)
- [Mangum Documentation](https://mangum.io/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

---

## 📞 Soporte

Si encuentras problemas durante el deployment:

1. Revisa los logs en CloudWatch
2. Verifica la configuración de variables de entorno
3. Asegúrate de que los permisos IAM sean correctos
4. Consulta la sección de troubleshooting arriba

¡El deployment está optimizado para simplicidad y funciona out-of-the-box con la configuración recomendada!