# Dockerfile estable con Playwright para Cloud Run
FROM python:3.11-slim

# Librerías necesarias para Playwright
RUN apt-get update && apt-get install -y --no-install-recommends \
  ca-certificates curl wget \
  libasound2 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 \
  libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libxrender1 libxkbcommon0 \
  libpango-1.0-0 libnss3 libxcb1 libx11-6 libxext6 libxi6 libxcursor1 \
  libgbm1 libxss1 libcairo2 libcairo-gobject2 \
  fonts-liberation libgtk-3-0 \
  && rm -rf /var/lib/apt/lists/*

# Usuario no-root para Playwright
RUN useradd --create-home --shell /bin/bash app

# Variables de entorno
ENV PYTHONUNBUFFERED=1 \
    BROWSER_HEADLESS=true \
    PLAYWRIGHT_BROWSERS_PATH=/app/.cache/ms-playwright

# Directorio de trabajo
WORKDIR /app

# Crear directorio para Playwright browsers
RUN mkdir -p /app/.cache/ms-playwright && \
    chown -R app:app /app

# Copiar e instalar dependencias de Python
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

# Instalar browsers de Playwright
RUN python -m playwright install chromium

# Copiar aplicación completa con servicios
COPY main.py main.py
COPY app/ app/

# Cambiar a usuario no-root
USER app

# Exponer puerto
EXPOSE 8080

# Comando simple que funciona
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]