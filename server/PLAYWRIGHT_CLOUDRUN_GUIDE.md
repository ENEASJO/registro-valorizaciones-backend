# Guía de Playwright en Google Cloud Run

## Resumen de cambios implementados

Este documento describe las optimizaciones realizadas en el Dockerfile para hacer funcionar Playwright correctamente en Google Cloud Run.

## Problemas resueltos

### 1. Fuentes faltantes
**Problema original:** 
- `ttf-unifont` y `ttf-ubuntu-font-family` no existen en repositorios Debian Slim

**Solución implementada:**
```dockerfile
# Fuentes compatibles con Debian
fonts-liberation \
fonts-dejavu-core \
fonts-freefont-ttf \
fonts-noto-core \
fonts-noto-cjk \
```

### 2. Dependencias de sistema para Chromium
**Optimizaciones:**
- Instalación completa de dependencias de X11 y GTK
- Inclusión de `xvfb` para entorno sin pantalla
- Configuración de librerías de audio y multimedia

### 3. Configuración de usuario no-root
**Cambio crítico:**
```dockerfile
# Instalar Playwright browser como usuario no-root
USER app
RUN playwright install chromium
```

### 4. Variables de entorno específicas
```dockerfile
ENV BROWSER_HEADLESS=true \
    PLAYWRIGHT_BROWSERS_PATH=/home/app/.cache/ms-playwright \
    PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=0 \
    PLAYWRIGHT_CHROMIUM_ARGS="--no-sandbox,--disable-setuid-sandbox,--disable-dev-shm-usage,--disable-gpu,--no-first-run,--no-zygote,--disable-background-timer-throttling,--disable-backgrounding-occluded-windows,--disable-renderer-backgrounding"
```

## Configuración de Cloud Run

### Recursos recomendados
- **Memoria:** 4Gi (aumentado desde 2Gi para Playwright)
- **CPU:** 2 vCPUs
- **Concurrency:** 20 (reducido para estabilidad)
- **Timeout:** 900 segundos
- **Execution Environment:** gen2 (requerido para Playwright)

### Variables de entorno críticas
```bash
BROWSER_HEADLESS=true
PLAYWRIGHT_BROWSERS_PATH=/home/app/.cache/ms-playwright
PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=0
```

## Troubleshooting

### Verificar instalación de Playwright
```bash
# Dentro del contenedor
playwright --version
playwright install --dry-run chromium
```

### Logs comunes de error y soluciones

#### Error: "Browser not found"
```bash
# Verificar permisos
ls -la /home/app/.cache/ms-playwright/

# Reinstalar browser
playwright install chromium
```

#### Error: "Failed to launch browser"
Verificar argumentos de Chromium en variables de entorno:
```bash
--no-sandbox
--disable-setuid-sandbox
--disable-dev-shm-usage
--disable-gpu
```

#### Error: "Font not found"
Verificar fuentes instaladas:
```bash
fc-list | grep -i liberation
fc-list | grep -i dejavu
```

### Comandos de debugging

#### Ver logs de Cloud Run
```bash
gcloud run services logs read valoraciones-backend --region us-central1
```

#### Logs en tiempo real
```bash
gcloud run services logs tail valoraciones-backend --region us-central1
```

#### Test local del contenedor
```bash
docker build -f Dockerfile.cloudrun -t test-playwright .
docker run -p 8080:8080 -e PORT=8080 test-playwright
```

## Validación post-deployment

### Endpoints de prueba
1. **Health check:** `https://[service-url]/health`
2. **Test RUC:** `https://[service-url]/api/ruc/20100070970`
3. **Test OSCE:** `https://[service-url]/api/osce/search?ruc=20100070970`

### Script de validación automática
El script `deploy-cloudrun.sh` incluye validaciones automáticas:
- Health check básico
- Test de endpoint que usa web scraping
- Verificación de logs de Playwright

## Optimizaciones implementadas

### Multi-stage build
- Reducción del tamaño final de imagen
- Separación de dependencias de sistema y aplicación

### Limpieza de archivos temporales
```dockerfile
RUN find /home/app/.cache/ms-playwright -type f -name "*.log" -delete 2>/dev/null || true \
    && find /home/app/.cache/ms-playwright -type f -name "*.tmp" -delete 2>/dev/null || true
```

### Configuración de permisos óptima
- Usuario no-root para seguridad
- Permisos específicos para directorios de Playwright
- Configuración de TMPDIR personalizado

## Monitoreo recomendado

### Métricas clave de Cloud Run
- **Request latency:** Monitor para timeouts de web scraping
- **Memory utilization:** Playwright consume ~500MB-1GB por instancia
- **Error rate:** Vigilar errores 5xx relacionados con browser failures

### Alertas sugeridas
- Memory utilization > 80%
- Request latency > 30 segundos
- Error rate > 5%

## Próximos pasos

1. **Caché de browsers:** Considerar volumen persistente para browsers
2. **Pool de browsers:** Implementar reutilización de instancias
3. **Métricas personalizadas:** Agregar telemetría específica de Playwright
4. **Scaling automático:** Configurar auto-scaling basado en carga de web scraping

## Contacto y soporte

Para problemas específicos de Playwright en Cloud Run:
1. Revisar logs detallados
2. Verificar configuración de variables de entorno
3. Validar permisos de usuario no-root
4. Confirmar instalación correcta de dependencias de sistema