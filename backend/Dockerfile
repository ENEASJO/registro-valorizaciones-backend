# Dockerfile simplificado para debug - sin Playwright hasta que funcione básico
FROM python:3.11-slim

# Variables de entorno básicas para Cloud Run
ENV PYTHONUNBUFFERED=1

# Directorio de trabajo
WORKDIR /app

# Crear usuario no-root
RUN useradd --create-home --shell /bin/bash app

# Copiar e instalar dependencias básicas (sin Playwright por ahora)
COPY requirements-basic.txt .
RUN pip install --no-cache-dir -r requirements-basic.txt

# Copiar aplicación
COPY main.py .
COPY app/ ./app/

# Dar permisos
RUN chown -R app:app /app
USER app

# Exponer puerto
EXPOSE 8080

# Comando que usa la variable PORT de Cloud Run
CMD exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080} --log-level info