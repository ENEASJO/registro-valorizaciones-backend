# API Consultor RUC SUNAT - Modular

API FastAPI modularizada para consultar información de empresas peruanas en SUNAT mediante web scraping.

## 🏗️ Arquitectura Modular

```
server/
├── app/
│   ├── models/          # Modelos Pydantic
│   │   └── ruc.py
│   ├── services/        # Lógica de negocio
│   │   └── sunat_service.py
│   ├── api/            # Endpoints y rutas
│   │   ├── routes/
│   │   │   └── ruc.py
│   │   └── dependencies.py
│   ├── core/           # Configuración
│   │   ├── config.py
│   │   └── logging.py
│   └── utils/          # Utilidades
│       ├── validators.py
│       ├── exceptions.py
│       └── response_handler.py
├── main.py             # Aplicación principal
├── requirements.txt    # Dependencias
├── .env.example       # Configuración de ejemplo
└── run.py             # Script de inicio
```

## 🚀 Inicio Rápido

### 1. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 2. Configurar entorno
```bash
cp .env.example .env
# Editar .env según tus necesidades
```

### 3. Instalar navegadores Playwright
```bash
python -m playwright install chromium
```

### 4. Iniciar servidor
```bash
# Opción 1: Script de desarrollo
python run.py

# Opción 2: Uvicorn directo
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Opción 3: Python main
python main.py
```

## 📡 Endpoints

### Nuevo Endpoint Modular (Recomendado)
```http
POST /api/v1/buscar
Content-Type: application/json

{
  "ruc": "20123456789"
}
```

### Endpoint Legacy (Compatibilidad)
```http
POST /buscar
Content-Type: application/json

{
  "ruc": "20123456789"
}
```

### Endpoints Informativos
- `GET /` - Información básica
- `GET /api/v1/health` - Estado del servicio
- `GET /docs` - Documentación Swagger (solo en desarrollo)
- `GET /redoc` - Documentación ReDoc (solo en desarrollo)

## 🔧 Configuración

### Variables de Entorno (.env)

```bash
# Aplicación
APP_NAME=Consultor RUC SUNAT
DEBUG=true
PORT=8000

# CORS
ALLOWED_ORIGINS=*

# Scraping
HEADLESS_BROWSER=true
BROWSER_TIMEOUT=30000

# Logging
LOG_LEVEL=INFO
```

## 🏛️ Componentes Principales

### 📋 Modelos (app/models/ruc.py)
- **RUCInput**: Validación de entrada con RUC de 11 dígitos
- **RepresentanteLegal**: Información de representantes
- **EmpresaInfo**: Respuesta completa con validaciones
- **ErrorResponse**: Manejo estandarizado de errores

### 🔧 Servicios (app/services/sunat_service.py)
- **SUNATService**: Lógica de scraping modularizada
- Navegación asíncrona con Playwright
- Extracción robusta de datos
- Manejo de errores específicos

### 🛣️ Rutas (app/api/routes/ruc.py)
- Endpoints RESTful organizados
- Documentación automática
- Manejo de errores centralizado
- Validación de entrada automática

### ⚙️ Configuración (app/core/)
- **config.py**: Configuración por ambiente
- **logging.py**: Sistema de logging estructurado
- Soporte para variables de entorno

### 🔨 Utilidades (app/utils/)
- **validators.py**: Validaciones de RUC y documentos
- **exceptions.py**: Excepciones personalizadas
- **response_handler.py**: Respuestas HTTP estandarizadas

## 🔐 Validaciones

### RUC
- Exactamente 11 dígitos numéricos
- Debe comenzar con 1 o 2 (personas jurídicas)
- Validación automática en entrada

### Representantes
- Nombres válidos (no headers de tabla)
- Documentos de identidad opcionales
- Cargos y fechas estructurados

## 🚦 Estados de Respuesta

- `200 OK` - Consulta exitosa
- `400 Bad Request` - Error de validación
- `404 Not Found` - RUC no encontrado
- `408 Request Timeout` - Timeout en consulta
- `422 Unprocessable Entity` - Error de datos
- `500 Internal Server Error` - Error interno

## 🔍 Ejemplo de Respuesta

```json
{
  "ruc": "20123456789",
  "razon_social": "EMPRESA EJEMPLO S.A.C.",
  "representantes": [
    {
      "tipo_doc": "DNI",
      "numero_doc": "12345678",
      "nombre": "JUAN CARLOS PEREZ LOPEZ",
      "cargo": "GERENTE GENERAL",
      "fecha_desde": "01/01/2020"
    }
  ],
  "total_representantes": 1
}
```

## 🛡️ Características de Seguridad

- Validación estricta de entrada
- Sanitización de datos
- Rate limiting configurable
- Headers de seguridad
- Logging de requests
- Manejo seguro de errores

## 🔄 Migración desde Versión Anterior

La nueva versión mantiene **compatibilidad total** con el endpoint anterior (`POST /buscar`). No se requieren cambios en el frontend existente.

### Recomendaciones:
1. Usar el nuevo endpoint `/api/v1/buscar` para nuevas implementaciones
2. Configurar variables de entorno en `.env`
3. Revisar logs para detectar uso del endpoint legacy

## 🧪 Testing

```bash
# Instalar dependencias de desarrollo
pip install pytest pytest-asyncio httpx

# Ejecutar tests (cuando estén implementados)
pytest tests/
```

## 🚀 Producción

### Configuraciones Recomendadas:
```bash
DEBUG=false
RELOAD=false
HEADLESS_BROWSER=true
LOG_LEVEL=WARNING
ALLOWED_ORIGINS=https://tudominio.com
SECRET_KEY=tu-clave-secreta-muy-fuerte
```

### Deploy:
```bash
# Con Gunicorn
pip install gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker

# Con Docker (ejemplo)
# FROM python:3.11-slim
# ... (Dockerfile personalizado)
```

## 📝 Logs

Los logs se guardan en:
- **Consola**: Logs normales
- **Archivo**: `app.log` (en modo DEBUG)

Niveles: DEBUG, INFO, WARNING, ERROR, CRITICAL

## 🤝 Contribución

1. Seguir la estructura modular existente
2. Agregar validaciones apropiadas
3. Documentar cambios en docstrings
4. Mantener compatibilidad con API existente
5. Usar async/await donde sea apropiado

## 📄 Licencia

[Especificar licencia según sea necesario]