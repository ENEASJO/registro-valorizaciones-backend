# Dockerfile ultra-optimizado para Cloud Run - Chrome for Testing
FROM python:3.11-slim

# Librerías optimizadas para Chrome/Playwright en Cloud Run
RUN apt-get update && apt-get install -y --no-install-recommends \
  ca-certificates curl unzip wget gnupg xvfb \
  libasound2 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 \
  libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libxrender1 libxkbcommon0 \
  libpango-1.0-0 libnss3 libxcb1 libx11-6 libxext6 libxi6 libxcursor1 \
  libgbm1 libxss1 libcairo2 libcairo-gobject2 \
  fonts-liberation libgtk-3-0 libgdk-pixbuf-2.0-0 libgdk-pixbuf2.0-common \
  && rm -rf /var/lib/apt/lists/*

# Usuario no-root (necesario para Playwright)
RUN useradd --create-home --shell /bin/bash app

# Variables de entorno - PERMITIR que Playwright descargue browsers
ENV PYTHONUNBUFFERED=1 \
    PORT=8080 \
    BROWSER_HEADLESS=true \
    PLAYWRIGHT_BROWSERS_PATH=/app/.cache/ms-playwright

# Crear directorio de trabajo
WORKDIR /app

# Crear directorio para Playwright browsers con permisos correctos
RUN mkdir -p /app/.cache/ms-playwright && \
    chown -R app:app /app

# Copiar y instalar dependencias
COPY requirements-cloudrun.txt .
RUN pip install --no-cache-dir -r requirements-cloudrun.txt

# Instalar browsers de Playwright en el directorio correcto
# Instalar como root pero en la ubicación accesible por el usuario app
RUN python -m playwright install chromium && \
    python -m playwright install-deps chromium

# Copiar código de aplicación
COPY --chown=app:app . /app/

# Cambiar a usuario no-root
USER app

# Configurar port para Cloud Run
EXPOSE 8080

# Health check para Cloud Run (comentado para Cloud Build)
# HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
#   CMD python -c "import requests; requests.get('http://localhost:8080/health', timeout=5)" || exit 1

# Comando de inicio optimizado para Cloud Run
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]