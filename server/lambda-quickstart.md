# 🚀 Lambda Playwright - Quick Start Guide

## Comandos Esenciales

### Deploy Completo (Un Solo Comando)
```bash
./deploy-lambda-container.sh
```

### Configuración Rápida de AWS
```bash
# Configurar credenciales
aws configure

# Establecer región
export AWS_REGION=us-east-1
export STAGE=prod
```

### Build y Test Local
```bash
# Solo build
./deploy-lambda-container.sh build-only

# Test local de la imagen
docker run --rm -p 8080:8080 \
  -e DEBUG=true \
  valoraciones-api-lambda:latest
```

### Verificación Post-Deploy
```bash
# Obtener URL
aws cloudformation describe-stacks \
  --stack-name valoraciones-api-playwright-prod-stack \
  --query 'Stacks[0].Outputs[?OutputKey==`FunctionUrl`].OutputValue' \
  --output text

# Test rápido
curl https://YOUR-LAMBDA-URL.amazonaws.com/health
```

## 🔧 Troubleshooting Rápido

### Problema: Timeout
```bash
# Aumentar timeout a 15 minutos
aws lambda update-function-configuration \
  --function-name valoraciones-api-playwright-prod \
  --timeout 900
```

### Problema: Memoria Insuficiente
```bash
# Aumentar a 3GB
aws lambda update-function-configuration \
  --function-name valoraciones-api-playwright-prod \
  --memory-size 3008
```

### Problema: Chromium No Funciona
**Verificar en logs:**
```
✅ Chromium found and accessible
```

**Si no aparece, rebuild:**
```bash
docker build -f Dockerfile.lambda -t valoraciones-api-lambda:fix .
# ... push y update
```

### Ver Logs en Tiempo Real
```bash
aws logs tail /aws/lambda/valoraciones-api-playwright-prod --follow
```

## 📊 Monitoreo Esencial

### Métricas Críticas
- **Duration**: < 2 minutos OK
- **Memory**: < 90% OK  
- **Errors**: < 5% OK
- **Throttles**: 0 ideal

### Comandos de Monitoreo
```bash
# Métricas de los últimos 30 minutos
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Duration \
  --dimensions Name=FunctionName,Value=valoraciones-api-playwright-prod \
  --start-time $(date -u -d '30 minutes ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average,Maximum
```

## 🎯 Tests de Funcionalidad

### Test Health Check
```bash
curl https://YOUR-URL/health | jq '.'
```

### Test SUNAT
```bash
curl "https://YOUR-URL/consulta-ruc/20123456789" | jq '.razon_social'
```

### Test OSCE
```bash
curl "https://YOUR-URL/consulta-osce/20123456789" | jq '.estado_registro'
```

### Test Consolidado
```bash
curl "https://YOUR-URL/consulta-ruc-consolidada/20123456789" | jq '.data.sunat.razon_social'
```

## ⚡ Optimizaciones Rápidas

### Variables de Entorno de Performance
```bash
aws lambda update-function-configuration \
  --function-name valoraciones-api-playwright-prod \
  --environment Variables='{
    "SUNAT_TIMEOUT":"15000",
    "OSCE_TIMEOUT":"20000",
    "PLAYWRIGHT_TIMEOUT":"25000",
    "DEBUG":"false"
  }'
```

### Configurar Reserved Concurrency
```bash
aws lambda put-reserved-concurrency-configuration \
  --function-name valoraciones-api-playwright-prod \
  --reserved-concurrent-executions 5
```

## 🔄 Updates Rápidos

### Update Solo el Código (Sin Rebuild Docker)
```bash
# Para cambios menores en Python
zip -r function.zip . -x "*.git*" "node_modules/*" "*.docker*"
aws lambda update-function-code \
  --function-name valoraciones-api-playwright-prod \
  --zip-file fileb://function.zip
```

### Rollback Inmediato
```bash
# Volver a versión anterior
aws lambda update-function-code \
  --function-name valoraciones-api-playwright-prod \
  --image-uri 123456789012.dkr.ecr.us-east-1.amazonaws.com/valoraciones-api-lambda:previous
```

## 📋 Checklist de 5 Minutos

- [ ] `aws configure` funcionando
- [ ] `docker` funcionando
- [ ] Variables AWS_REGION y STAGE configuradas
- [ ] `./deploy-lambda-container.sh` ejecutado sin errores
- [ ] Health check responde 200
- [ ] Un test de SUNAT funciona

## 🆘 Emergency Commands

### Function Crashed - Reinicio
```bash
aws lambda update-function-configuration \
  --function-name valoraciones-api-playwright-prod \
  --description "Restart $(date)"
```

### High Error Rate - Disable
```bash
aws lambda put-reserved-concurrency-configuration \
  --function-name valoraciones-api-playwright-prod \
  --reserved-concurrent-executions 0
```

### Re-enable
```bash
aws lambda delete-reserved-concurrency-configuration \
  --function-name valoraciones-api-playwright-prod
```

## 💡 Tips Rápidos

1. **Memoria**: Empezar con 2GB, subir si hay timeouts
2. **Timeout**: Máximo 15 minutos, pero optimizar para < 2 minutos
3. **Concurrency**: Limitar a 5 para controlar costos
4. **Logs**: Retention de 14 días suficiente
5. **Monitoreo**: Configurar alarmas en errores > 5%

---

**¿Problemas?** 
1. Revisar logs: `aws logs tail /aws/lambda/YOUR-FUNCTION --follow`
2. Verificar imagen: `docker run -p 8080:8080 IMAGE-NAME`  
3. Test local: `curl localhost:8080/health`