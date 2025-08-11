# AWS Lambda Container Deployment con Playwright

## Guía Completa para Deployment de API de Valorizaciones con Web Scraping

Esta documentación cubre el deployment de la API de Valorizaciones usando AWS Lambda Container con Playwright para mantener la funcionalidad completa de web scraping de SUNAT y OSCE.

## 📋 Tabla de Contenidos

1. [Visión General](#visión-general)
2. [Arquitectura](#arquitectura)
3. [Prerequisites](#prerequisites)
4. [Configuración](#configuración)
5. [Build y Deployment](#build-y-deployment)
6. [Monitoring y Troubleshooting](#monitoring-y-troubleshooting)
7. [Optimizaciones](#optimizaciones)
8. [FAQ](#faq)

## 🎯 Visión General

### ¿Por qué Container en lugar de ZIP?

**Problema**: Playwright requiere navegadores (Chromium) que no se pueden incluir en un deployment ZIP de Lambda por limitaciones de tamaño y dependencias del sistema.

**Solución**: AWS Lambda Container permite incluir todas las dependencias necesarias, incluyendo Chromium, en una imagen Docker optimizada.

### Funcionalidades Mantenidas

✅ **Web Scraping SUNAT**: Consulta automática de información empresarial  
✅ **Web Scraping OSCE**: Consulta automática de proveedores del estado  
✅ **Consolidación de Datos**: Combina información de ambas fuentes  
✅ **API FastAPI Completa**: Todos los endpoints disponibles  
✅ **Performance Optimizada**: Configuración específica para Lambda  

## 🏗️ Arquitectura

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │────│  Lambda Function │────│  External APIs  │
│   (Vercel)      │    │   Container      │    │  SUNAT / OSCE   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                       ┌──────────────────┐
                       │   ECR Repository │
                       │   Docker Image   │
                       └──────────────────┘
```

### Componentes Principales

- **Dockerfile.lambda**: Configuración optimizada para Lambda
- **template-container.yaml**: CloudFormation template
- **lambda_config.py**: Configuraciones específicas de Playwright
- **Services optimizados**: SUNAT y OSCE con reintentos y timeouts
- **deploy-lambda-container.sh**: Script automatizado de deployment

## 🔧 Prerequisites

### Software Requerido

```bash
# AWS CLI v2
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Docker
sudo apt-get update
sudo apt-get install docker.io
sudo usermod -aG docker $USER

# SAM CLI (opcional pero recomendado)
pip install aws-sam-cli

# Verificar instalación
aws --version
docker --version
sam --version
```

### Configuración AWS

```bash
# Configurar credenciales AWS
aws configure

# Variables de entorno (opcional)
export AWS_REGION=us-east-1
export AWS_PROFILE=default
```

### Permisos IAM Requeridos

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "lambda:*",
        "ecr:*",
        "cloudformation:*",
        "iam:CreateRole",
        "iam:AttachRolePolicy",
        "iam:PassRole",
        "logs:*"
      ],
      "Resource": "*"
    }
  ]
}
```

## ⚙️ Configuración

### Estructura de Archivos

```
server/
├── Dockerfile.lambda                 # Container optimizado para Lambda
├── template-container.yaml           # CloudFormation template
├── requirements-lambda-container.txt # Dependencies completas
├── lambda_config.py                  # Configuraciones Playwright
├── deploy-lambda-container.sh        # Script de deployment
├── main_lambda.py                    # FastAPI optimizada
├── lambda_function.py                # Entry point Lambda
└── app/
    └── services/
        ├── sunat_service_lambda.py   # SUNAT optimizado
        └── osce_service_lambda.py    # OSCE optimizado
```

### Variables de Entorno

| Variable | Default | Descripción |
|----------|---------|-------------|
| `STAGE` | `prod` | Ambiente (dev/staging/prod) |
| `AWS_REGION` | `us-east-1` | Región AWS |
| `FUNCTION_NAME` | `valoraciones-api-playwright` | Nombre de la función |
| `MEMORY_SIZE` | `2048` | Memoria en MB (mínimo para Playwright) |
| `TIMEOUT` | `900` | Timeout en segundos (máximo 15min) |
| `ECR_REPOSITORY` | `valoraciones-api-lambda` | Repositorio ECR |

### Configuración de Playwright

```python
# lambda_config.py - Configuración automática
CHROMIUM_ARGS = [
    '--no-sandbox',
    '--disable-dev-shm-usage',
    '--single-process',      # Crítico para Lambda
    '--disable-gpu',
    '--disable-dev-tools',
    # ... más optimizaciones
]

TIMEOUTS = {
    "navigation": 20000,
    "total_operation": 120000
}
```

## 🚀 Build y Deployment

### Deployment Automático

```bash
# Full deployment (recomendado)
./deploy-lambda-container.sh

# Solo build (para testing)
./deploy-lambda-container.sh build-only

# Solo deploy (imagen existe)
./deploy-lambda-container.sh deploy-only

# Solo test
./deploy-lambda-container.sh test
```

### Deployment Manual

#### 1. Crear Repositorio ECR

```bash
aws ecr create-repository --repository-name valoraciones-api-lambda
```

#### 2. Build de la Imagen

```bash
# Login a ECR
aws ecr get-login-password --region us-east-1 | \
    docker login --username AWS --password-stdin \
    123456789012.dkr.ecr.us-east-1.amazonaws.com

# Build
docker build -f Dockerfile.lambda -t valoraciones-api-lambda:latest .

# Tag para ECR
docker tag valoraciones-api-lambda:latest \
    123456789012.dkr.ecr.us-east-1.amazonaws.com/valoraciones-api-lambda:latest

# Push
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/valoraciones-api-lambda:latest
```

#### 3. Deploy CloudFormation

```bash
sam deploy \
    --template-file template-container.yaml \
    --stack-name valoraciones-api-prod-stack \
    --capabilities CAPABILITY_IAM \
    --parameter-overrides \
        Stage=prod \
        FunctionName=valoraciones-api-playwright \
        MemorySize=2048 \
        Timeout=900
```

### Verificación del Deployment

```bash
# Obtener URL de la función
aws cloudformation describe-stacks \
    --stack-name valoraciones-api-prod-stack \
    --query 'Stacks[0].Outputs[?OutputKey==`FunctionUrl`].OutputValue' \
    --output text

# Test health check
curl https://your-lambda-url.amazonaws.com/health
```

## 📊 Monitoring y Troubleshooting

### CloudWatch Logs

```bash
# Ver logs en tiempo real
aws logs tail /aws/lambda/valoraciones-api-playwright-prod --follow

# Buscar errores específicos
aws logs filter-log-events \
    --log-group-name /aws/lambda/valoraciones-api-playwright-prod \
    --filter-pattern "ERROR"
```

### Métricas Importantes

- **Duration**: Duración de ejecución (objetivo: < 120s)
- **Memory**: Uso de memoria (objetivo: < 90%)
- **Errors**: Tasa de errores (objetivo: < 5%)
- **Cold Start**: Tiempo de arranque en frío

### Problemas Comunes

#### 1. Timeout en Scraping

```bash
# Aumentar timeout
aws lambda update-function-configuration \
    --function-name valoraciones-api-playwright-prod \
    --timeout 900
```

#### 2. Memoria Insuficiente

```bash
# Aumentar memoria
aws lambda update-function-configuration \
    --function-name valoraciones-api-playwright-prod \
    --memory-size 3008
```

#### 3. Chromium No Encontrado

Verificar variables de entorno:
```bash
# En lambda_config.py
PLAYWRIGHT_BROWSERS_PATH="/var/task/playwright_browsers"
PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH="/var/task/playwright_browsers/chromium-1112/chrome-linux/chrome"
```

#### 4. Error de Permisos

```bash
# En Dockerfile.lambda
RUN chmod -R 755 ${LAMBDA_TASK_ROOT}
```

## 🚄 Optimizaciones

### Performance

1. **Single Process**: `--single-process` es crítico en Lambda
2. **Memory**: Mínimo 2GB para Playwright estable
3. **Timeouts**: Configuración escalonada según operación
4. **Context Reuse**: Un contexto por operación

### Costos

1. **Reserved Concurrency**: Limitar a 5 ejecuciones simultáneas
2. **Memory Optimization**: Balance entre performance y costo
3. **Timeout Optimization**: No exceder tiempo necesario
4. **Log Retention**: 14 días para equilibrar debug y costo

### Seguridad

1. **IAM Roles**: Permisos mínimos necesarios
2. **VPC**: Opcional para mayor seguridad
3. **Environment Variables**: Encripción en tránsito
4. **Container Scanning**: ECR escanea vulnerabilidades

## 🔄 Updates y Maintenance

### Actualizar Código

```bash
# 1. Build nueva imagen
docker build -f Dockerfile.lambda -t valoraciones-api-lambda:v2.0 .

# 2. Push con nuevo tag
docker tag valoraciones-api-lambda:v2.0 \
    123456789012.dkr.ecr.us-east-1.amazonaws.com/valoraciones-api-lambda:v2.0
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/valoraciones-api-lambda:v2.0

# 3. Update Lambda function
aws lambda update-function-code \
    --function-name valoraciones-api-playwright-prod \
    --image-uri 123456789012.dkr.ecr.us-east-1.amazonaws.com/valoraciones-api-lambda:v2.0
```

### Rollback

```bash
# Volver a versión anterior
aws lambda update-function-code \
    --function-name valoraciones-api-playwright-prod \
    --image-uri 123456789012.dkr.ecr.us-east-1.amazonaws.com/valoraciones-api-lambda:latest
```

## 📋 Checklist de Deployment

### Pre-deployment

- [ ] AWS CLI configurado
- [ ] Docker instalado y funcionando
- [ ] Permisos IAM correctos
- [ ] Variables de entorno configuradas
- [ ] Código testeado localmente

### Deployment

- [ ] Repositorio ECR creado
- [ ] Imagen Docker construida exitosamente
- [ ] Test de imagen local pasado
- [ ] Push a ECR exitoso
- [ ] CloudFormation stack desplegado
- [ ] Function URL obtenida

### Post-deployment

- [ ] Health check responde 200
- [ ] Test de endpoint SUNAT
- [ ] Test de endpoint OSCE  
- [ ] Test de endpoint consolidado
- [ ] CloudWatch logs funcionando
- [ ] Alarmas configuradas

## 🤔 FAQ

### ¿Por qué usar Container en lugar de Layers?

Los layers de Lambda tienen limitación de 250MB descomprimido, insuficiente para Playwright + Chromium (~300MB+). Containers permiten hasta 10GB.

### ¿Cuánto cuesta ejecutar esto?

**Estimación para 1000 requests/día:**
- Lambda: ~$20/mes (con 2GB RAM, 60s promedio)
- Data Transfer: ~$1/mes  
- CloudWatch: ~$2/mes
- **Total**: ~$23/mes

### ¿Qué pasa con cold starts?

Cold starts con containers son ~3-5 segundos. Mitigation:
1. Provisioned Concurrency (para casos críticos)
2. Warming functions (CloudWatch Events)
3. Optimización de imagen Docker

### ¿Cómo debugear problemas de scraping?

1. Activar DEBUG en variables de entorno
2. Screenshots se guardan en `/tmp/`
3. Usar CloudWatch logs para traces
4. Test local con Docker: `docker run -p 8000:8080 image`

### ¿Es seguro para producción?

Sí, considerando:
- Timeouts apropiados
- Error handling robusto
- Monitoring completo
- Rollback strategy
- Rate limiting en frontend

---

## 📞 Soporte

Para problemas o mejoras, revisar:

1. **CloudWatch Logs**: Primer punto de diagnóstico
2. **Health Check**: `/health` endpoint
3. **ECR Repository**: Verificar imagen disponible
4. **IAM Permissions**: Confirmar permisos
5. **Network**: Conectividad a SUNAT/OSCE

---

**🎉 Con esta configuración tienes una API completamente funcional con web scraping en AWS Lambda, manteniendo toda la funcionalidad original pero con la escalabilidad y eficiencia del cloud.**