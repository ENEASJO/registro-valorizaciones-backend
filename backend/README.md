# 🚀 Backend Completo - Sistema de Valorizaciones

Backend unificado con web scraping, CRUD APIs y base de datos en la nube.

## 🎯 ARQUITECTURA UNIFICADA

```
Frontend (Vercel) → Backend Completo (Cloud Run) → Turso Database
                         ↓
        Playwright (Scraping) + CRUD + APIs
              (Todo en una sola aplicación)
```

## ✅ CAPACIDADES

### 🕷️ **Web Scraping**
- **SUNAT**: Consulta de RUCs, razón social, representantes legales
- **OSCE**: Información de proveedores, especialidades, capacidad
- **Playwright**: Navegación automatizada y extracción de datos

### 🗄️ **CRUD Completo**
- **Empresas**: Gestión de empresas consolidadas
- **Obras**: Proyectos de construcción y seguimiento
- **Valorizaciones**: Valuaciones periódicas y control financiero

### 💾 **Base de Datos**
- **Turso**: SQLite Cloud con sincronización automática
- **4 Tablas**: empresas, representantes, obras, valorizaciones
- **Relaciones**: Integridad referencial completa

## 🚀 Inicio Rápido

### 1. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 2. Configurar variables de entorno
```bash
export TURSO_DATABASE_URL="libsql://registro-de-valorizaciones-eneasjo.aws-us-east-2.turso.io"
export TURSO_AUTH_TOKEN="eyJhbGciOiJFZERTQSI..."
```

### 3. Instalar navegadores Playwright
```bash
playwright install chromium
```

### 4. Iniciar servidor
```bash
uvicorn main:app --reload --port 8000
```

## 🌐 ENDPOINTS

### Scraping (Existente)
```bash
GET /consulta-ruc/{ruc}           # SUNAT individual
GET /consulta-osce/{ruc}          # OSCE individual  
GET /consulta-ruc-consolidada/{ruc} # Datos consolidados
POST /buscar                      # Búsqueda legacy
```

### CRUD APIs (Nuevo)
```bash
# Empresas
GET  /api/empresas               # Listar empresas
POST /api/empresas               # Crear empresa

# Obras  
GET  /api/obras                  # Listar obras
POST /api/obras                  # Crear obra
GET  /api/obras?empresa_id=123   # Filtrar por empresa

# Valorizaciones
GET  /api/valorizaciones         # Listar valorizaciones  
POST /api/valorizaciones         # Crear valorización
GET  /api/valorizaciones?obra_id=456 # Filtrar por obra
```

### Utilidades
```bash
GET /health                      # Estado de servicios
GET /                           # Info de la API
```

## 📊 HEALTH CHECK

```bash
curl https://tu-cloud-run-url.run.app/health
```

**Respuesta esperada:**
```json
{
  "status": "healthy",
  "version": "3.0.0",
  "architecture": "Cloud Run Completo", 
  "services": {
    "playwright": "enabled",
    "turso_database": "connected",
    "crud_apis": "enabled"
  },
  "timestamp": "2024-08-23T12:00:00.000000"
}
```

## 🏗️ ESTRUCTURA DEL PROYECTO

```
├── main.py                 # Aplicación FastAPI principal
├── requirements.txt        # Dependencies Python
├── Dockerfile             # Container configuration
├── cloudbuild.yaml        # Build automation
└── app/
    ├── api/routes/         # REST API endpoints
    ├── core/               # Database connections
    ├── models/             # Pydantic models
    └── services/           # Business logic
```

## 🔧 CONFIGURACIÓN

### Variables de Entorno Requeridas
```bash
TURSO_DATABASE_URL=libsql://registro-de-valorizaciones-eneasjo.aws-us-east-2.turso.io
TURSO_AUTH_TOKEN=eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9...
```

### Deploy en Cloud Run
1. **GitHub Integration**: Conectado para deploy automático
2. **Environment Variables**: Configurar Turso credentials
3. **Build**: Dockerfile incluido para containerización
4. **Health Check**: `/health` endpoint disponible

## 🚀 DESARROLLO LOCAL

```bash
# Instalar dependencies
pip install -r requirements.txt

# Instalar Playwright browsers
playwright install chromium

# Configurar variables de entorno
export TURSO_DATABASE_URL="libsql://..."
export TURSO_AUTH_TOKEN="eyJhbGciOiJFZERTQSI..."

# Ejecutar
uvicorn main:app --reload --port 8000
```

## 📈 VERSION HISTORY

- **v3.0.0**: Arquitectura unificada con Playwright + CRUD + Turso
- **v2.0.0**: CRUD APIs agregadas  
- **v1.0.0**: Solo web scraping con Playwright

## 🎯 PRÓXIMOS PASOS

- ✅ **Scraping**: Funcionando en producción
- ✅ **CRUD**: Implementado y probado
- ✅ **Database**: Turso configurado
- 🔄 **Deploy**: Pendiente resolución Cloud Run
- 🎯 **Integration**: Conectar con frontend Vercel

---

**Generado con [Claude Code](https://claude.ai/code)**