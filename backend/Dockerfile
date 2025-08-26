# Dockerfile optimizado para Cloud Run con Playwright
FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

# ESTRATEGIA: Instalar dependencies como root, browsers como pwuser
# La imagen base ya tiene los system dependencies para Playwright

# Configurar variables globales
ENV DEBIAN_FRONTEND=noninteractive
ENV PLAYWRIGHT_BROWSERS_PATH=/home/pwuser/.cache/ms-playwright

# Como ROOT: Instalar dependencias Python y system packages adicionales si es necesario
COPY requirements-cloudrun.txt .
RUN pip install --no-cache-dir -r requirements-cloudrun.txt

# Crear directorios con permisos correctos
RUN mkdir -p /app/logs /app/cache /home/pwuser/.cache/ms-playwright && \
    chown -R pwuser:pwuser /home/pwuser/.cache /app

# CAMBIAR A USUARIO NO ROOT
USER pwuser

# Configurar environment para pwuser
ENV HOME=/home/pwuser
ENV PLAYWRIGHT_BROWSERS_PATH=/home/pwuser/.cache/ms-playwright

# CRITICAL FIX: Instalar solo browsers sin --with-deps (system deps ya están instalados)
# La imagen base mcr.microsoft.com/playwright/python ya tiene las dependencias del sistema
RUN playwright install chromium

# Verificar que chromium se instaló correctamente
RUN ls -la $PLAYWRIGHT_BROWSERS_PATH/
RUN find $PLAYWRIGHT_BROWSERS_PATH -name "chrome" -type f 2>/dev/null | head -1 || echo "Chrome executable location check"

# Copiar código de aplicación
COPY --chown=pwuser:pwuser . /app/
WORKDIR /app

# Configurar port para Cloud Run
ENV PORT=8080
EXPOSE 8080

# Health check para Cloud Run
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8080/health', timeout=5)" || exit 1

# Comando de inicio con configuraciones optimizadas para Cloud Run
# Versión restaurada con funcionalidad completa e imports seguros
CMD ["uvicorn", "main_restored:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]