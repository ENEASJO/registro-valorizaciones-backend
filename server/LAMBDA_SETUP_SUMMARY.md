# 🚀 AWS Lambda Setup - Resumen Completo

## ✅ Archivos Creados para Lambda

Tu proyecto FastAPI ha sido completamente adaptado para AWS Lambda. Aquí tienes el resumen de todos los archivos creados:

### 📁 Archivos Core Lambda
| Archivo | Descripción | Uso |
|---------|-------------|-----|
| `lambda_function.py` | Entry point principal para Lambda | Handler de AWS Lambda con Mangum |
| `main_lambda.py` | FastAPI optimizada para Lambda | Versión optimizada del main.py original |
| `requirements-lambda.txt` | Dependencias optimizadas | Instalación de packages para Lambda |

### 🔧 Scripts de Deployment  
| Archivo | Descripción | Uso |
|---------|-------------|-----|
| `deploy-lambda.sh` | Script deployment Linux/Mac | `./deploy-lambda.sh` |
| `deploy-lambda.bat` | Script deployment Windows | `deploy-lambda.bat` |
| `test-lambda-local.py` | Testing local pre-deployment | `python test-lambda-local.py` |

### ⚙️ Configuración e Infraestructura
| Archivo | Descripción | Uso |
|---------|-------------|-----|
| `template.yaml` | AWS SAM template | `sam deploy` |
| `samconfig.toml` | Configuración SAM multi-env | Automático con SAM |
| `.env.lambda.template` | Variables de entorno template | Copiar a `.env.lambda` |

### 📚 Documentación
| Archivo | Descripción | Uso |
|---------|-------------|-----|
| `LAMBDA_DEPLOYMENT_GUIDE.md` | Guía completa de deployment | Referencia paso a paso |
| `LAMBDA_SETUP_SUMMARY.md` | Este resumen | Vista general del setup |

## 🎯 Optimizaciones Implementadas

### ⚡ Performance & Cold Start
- **Lazy imports**: Playwright y servicios se importan solo cuando se necesitan
- **Timeouts optimizados**: 15s para persona natural, 10s para jurídica  
- **Memory configuration**: 1024MB recomendado
- **Browser args optimizados**: Para entorno Lambda sin sandbox

### 🔒 Seguridad & CORS  
- **CORS configurado**: Para dominios Vercel y localhost
- **Environment-based config**: Variables diferenciadas por entorno
- **Error handling**: Manejo seguro de errores sin exponer información sensible

### 📦 Package Optimization
- **Dependencias mínimas**: Solo lo necesario en requirements-lambda.txt
- **Mangum integration**: ASGI adapter optimizado para Lambda  
- **File size optimization**: Scripts limpian archivos innecesarios

## 🚀 Métodos de Deployment

### Método 1: Manual Upload (Más Simple)
```bash
# 1. Generar package
./deploy-lambda.sh

# 2. Upload en AWS Console
# - Crear función Lambda
# - Subir ZIP generado
# - Configurar Function URL
# - Configurar variables de entorno
```

### Método 2: AWS SAM (Recomendado)
```bash
# 1. Build
sam build

# 2. Deploy primera vez  
sam deploy --guided

# 3. Deploy subsecuentes
sam deploy
```

## 🔧 Configuración Recomendada Lambda

### Runtime Settings
- **Runtime**: Python 3.11
- **Architecture**: x86_64  
- **Handler**: `lambda_function.lambda_handler`
- **Timeout**: 900 segundos (15 minutos)
- **Memory**: 1024 MB
- **Storage**: 512 MB (default)

### Variables de Entorno
```bash
ENVIRONMENT=production
DEBUG=false
LAMBDA_FUNCTION_NAME=valoraciones-api
PLAYWRIGHT_TIMEOUT=15000
SUNAT_TIMEOUT=10000
OSCE_TIMEOUT=15000
ALLOWED_ORIGINS=https://*.vercel.app,http://localhost:3000,http://localhost:5173
```

### Function URL Configuration
- **Auth type**: NONE (cambiar a AWS_IAM para mayor seguridad)
- **CORS enabled**: Yes
- **Allowed origins**: Tu dominio Vercel
- **Allowed methods**: GET, POST, PUT, DELETE, OPTIONS, PATCH
- **Allowed headers**: *

## 🧪 Testing

### 1. Testing Local Pre-Deployment
```bash
python test-lambda-local.py
```

### 2. Testing Post-Deployment
```bash
# Health check
curl https://your-function-url.lambda-url.us-east-1.on.aws/health

# Consulta RUC 
curl https://your-function-url.lambda-url.us-east-1.on.aws/consulta-ruc/20123456789

# Consulta consolidada
curl https://your-function-url.lambda-url.us-east-1.on.aws/consulta-ruc-consolidada/20123456789
```

## 📊 Endpoints Disponibles

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/` | GET | Info general de la API |
| `/health` | GET | Health check |
| `/consulta-ruc/{ruc}` | GET | Consulta SUNAT |
| `/consulta-osce/{ruc}` | GET | Consulta OSCE |  
| `/consulta-ruc-consolidada/{ruc}` | GET | Consulta combinada |
| `/buscar` | POST | Búsqueda por RUC (body) |
| `/api/v1/empresas/` | GET/POST | CRUD empresas temporal |

## 💰 Costos Estimados 

### Por 1000 consultas/mes:
- **Lambda execution**: ~$0.17
- **Requests**: ~$0.0002
- **CloudWatch logs**: ~$0.005
- **Total mensual**: ~$0.18

### Optimización de costos:
- Reserved concurrency: 10 (para limitar)
- Log retention: 14 días  
- Memory ajustado según uso real
- Monitoring con budget alarms

## 🔍 Troubleshooting Común

### Cold Start Lento
- ✅ Implementado lazy loading
- ✅ Optimized browser args
- 💡 Considerar Provisioned Concurrency si es crítico

### Memory Issues
- ✅ Configurado 1024MB 
- ✅ Browser se cierra correctamente
- 💡 Aumentar a 1536MB si es necesario

### CORS Errors  
- ✅ CORS configurado en Function URL
- ✅ Headers apropiados en responses
- 💡 Verificar dominios exactos en producción

### Timeout Issues
- ✅ Timeout Lambda: 15 minutos
- ✅ Timeouts Playwright optimizados
- ✅ Error handling para timeouts

## 🎉 ¡Listo para Deployment!

Tu FastAPI está completamente optimizado y listo para AWS Lambda. El código mantienes toda la funcionalidad original de consulta RUC SUNAT/OSCE con las siguientes mejoras:

✅ **Serverless-ready**: Sin servidor que mantener  
✅ **Auto-scaling**: Escala automáticamente con demanda  
✅ **Cost-optimized**: Solo pagas por uso real  
✅ **CORS-configured**: Compatible con frontend Vercel  
✅ **Production-ready**: Monitoring y error handling  
✅ **Easy deployment**: Scripts automatizados  

### Próximos Pasos:
1. **Testing local**: `python test-lambda-local.py`
2. **Generate package**: `./deploy-lambda.sh` 
3. **Deploy to AWS**: Subir ZIP a Lambda Console
4. **Configure Function URL**: Activar endpoint público
5. **Update frontend**: Usar nueva Lambda URL
6. **Monitor**: Verificar CloudWatch logs

¡Tu API de valorizaciones ahora es completamente serverless! 🚀