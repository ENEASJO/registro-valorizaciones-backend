# 📊 Sistema de Registro de Valorizaciones
<!-- Force Vercel deployment -->

Sistema integral para gestión de empresas, obras y valorizaciones con extracción automatizada de datos desde SUNAT y OSCE.

## 🚀 Características Principales

- **🏢 Gestión de Empresas**: Registro completo con datos de SUNAT y OSCE
- **🏗️ Control de Obras**: Seguimiento de proyectos y contratos
- **💰 Valorizaciones**: Registro mensual de avances de obra
- **🤖 Extracción Automatizada**: Web scraping de SUNAT y OSCE con Playwright
- **⚡ Optimizaciones TURBO**: Extracción OSCE en 3-8 segundos
- **🔄 Base de Datos Neon**: PostgreSQL escalable y confiable

## 🏗️ Arquitectura

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FRONTEND      │    │    BACKEND      │    │   DATABASE      │
│   (Vercel)      │◄──►│  (Cloud Run)    │◄──►│     (Neon)      │
│                 │    │                 │    │                 │
│ - React 18      │    │ - FastAPI       │    │ - PostgreSQL    │
│ - TypeScript    │    │ - Python 3.11   │    │ - Row Level     │
│ - Vite          │    │ - Playwright    │    │   Security      │
│ - Tailwind CSS  │    │ - Async/Await   │    │ - Real-time     │
└─────────────────┘    └─────────────────┘    └─────────────────┘

                              │
                    ┌─────────┼─────────┐
                    │                   │
          ┌─────────▼─────────┐ ┌───────▼───────┐
          │      SUNAT        │ │     OSCE      │
          │  Web Scraping     │ │ Web Scraping  │
          │                   │ │  (Optimized)  │
          └───────────────────┘ └───────────────┘
```

## 📁 Estructura del Proyecto

```
registro-valorizaciones/
├── 📂 backend/
│   ├── 📂 app/
│   │   ├── 📂 api/routes/          # Rutas de API
│   │   ├── 📂 services/            # Lógica de negocio
│   │   │   ├── empresa_service_neon.py
│   │   │   ├── osce_turbo_service.py
│   │   │   └── precache_service.py
│   │   └── 📂 utils/               # Utilidades
│   ├── 📄 main.py                  # Aplicación FastAPI
│   ├── 📄 requirements.txt         # Dependencias Python
│   └── 📄 Dockerfile              # Imagen Docker
├── 📂 frontend/
│   ├── 📂 src/
│   │   ├── 📂 components/          # Componentes React
│   │   ├── 📂 modules/             # Módulos por funcionalidad
│   │   ├── 📂 config/              # Configuración
│   │   └── 📄 main.tsx            # Punto de entrada
│   ├── 📄 package.json            # Dependencias Node.js
│   ├── 📄 vite.config.ts          # Configuración Vite
│   └── 📄 vercel.json            # Configuración Vercel
├── 📂 database/
│   └── 📄 schema.sql              # Esquema Neon PostgreSQL
├── 📂 scripts/
│   └── 📄 setup-neon.py           # Scripts de configuración
├── 📄 .mcp.json                   # Configuración MCP Neon
├── 📄 cloudbuild.yaml            # CI/CD Google Cloud
└── 📄 README.md                   # Este archivo
```

## 🏛️ Descripción del Proyecto

Este sistema permite la gestión completa del ciclo de vida de valorizaciones de obras públicas municipales, incluyendo el registro de empresas contratistas, supervisión de obras y generación de reportes especializados conforme a la normativa peruana.

## 🌟 Características Principales

### 📊 Dashboard Ejecutivo
- **Métricas en tiempo real** con actualización automática
- **Mapa de calor** por localidades de San Marcos (Centros Poblados, Caseríos, Zona Urbana)
- **Gráficos interactivos** de inversión y avance de obras
- **Alertas inteligentes** para seguimiento crítico
- **Timeline de obras** con estados en tiempo real

### 🏢 Gestión de Empresas Contratistas
- **Empresas Ejecutoras**: Registro y gestión de empresas constructoras
- **Empresas Supervisoras**: Administración de consultoras especializadas
- **Formación de Consorcios** con validación de participaciones
- **Control de capacidad contractual** y especialidades

### 🏗️ Administración de Obras Públicas
- **Registro integral** de proyectos de infraestructura
- **Asignación automática** de ley aplicable (Ley N° 30225 / Ley N° 32069)
- **Gestión de profesionales** responsables por especialidad
- **Seguimiento de avances** y cronogramas
- **Control presupuestario** en tiempo real

### 💰 Sistema de Valorizaciones
- **Valorización de Ejecución**: Para obras ejecutadas
- **Valorización de Supervisión**: Para servicios de consultoría
- **Cálculos automáticos** según normativa peruana
- **Deducciones automáticas**: IGV, Retención, Amortización, Adelantos
- **Validaciones** conforme a reglamentos municipales

### 📈 Reportes Profesionales
- **Reportes de Avance**: Análisis S-curve y desviaciones
- **Reportes Financieros**: KPIs y análisis económico
- **Reportes Contractuales**: Seguimiento de contratos
- **Reportes Gerenciales**: Dashboard ejecutivo
- **Exportación** a PDF y Excel con formato profesional

### ⚙️ Configuración del Sistema
- **Parámetros municipales** configurables
- **Tipos de obra** y categorías
- **Especialidades profesionales**
- **Configuración de deducciones** según normativa

## 🏛️ Contexto Territorial

### Distrito de San Marcos
El sistema está diseñado específicamente para la estructura territorial del Distrito de San Marcos:

- **Zona Urbana**: Barrios del centro de San Marcos
- **Centros Poblados**: Huaripampa, Challhuayaco, Gaucho, Carhuayoc
- **Caseríos Independientes**: Pujun, Huanico, y otros

## 🛠️ Tecnologías Utilizadas

### Frontend (React + TypeScript)
**Ubicación:** `src/`  
**Deploy:** Vercel  
**Puerto local:** 5173

- **React 18** con TypeScript
- **Vite** para desarrollo y build
- **Tailwind CSS** para estilos
- **Neon PostgreSQL** para base de datos

### Backend (FastAPI + Python)
**Ubicación:** `backend/`  
**Deploy:** Google Cloud Run  
**Puerto local:** 8000

- **FastAPI** + Uvicorn
- **Playwright** para web scraping SUNAT/OSCE
- **Neon PostgreSQL** para base de datos
- **Redis** para caché y optimización

## 📋 Marco Normativo

El sistema cumple con la normativa peruana:
- **Ley N° 30225** - Ley de Contrataciones del Estado (pre-2025)
- **Ley N° 32069** - Nueva Ley de Contrataciones del Estado (2025+)
- **Reglamentos municipales** específicos
- **Procedimientos OSCE** aplicables

## 🚀 Instalación y Desarrollo

### Prerrequisitos
```bash
Node.js >= 18.0.0
Python >= 3.9.0
```

### Frontend
```bash
# Entrar a carpeta frontend
cd frontend

# Instalar dependencias
npm install

# Iniciar servidor de desarrollo (Puerto 5173)
npm run dev
```

### Backend
```bash
# Entrar a carpeta backend
cd backend

# Crear entorno virtual (recomendado)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Instalar dependencias
pip install -r requirements.txt

# Iniciar servidor
python main.py
```

### Desarrollo Local
1. **Backend:** `cd backend && python main.py` (puerto 8000)
2. **Frontend:** `npm run dev` (puerto 5173)

## 🌐 URLs de Producción
- **Frontend:** https://registro-valorizaciones.vercel.app
- **Backend:** https://valoraciones-backend-[hash].a.run.app

## 📁 Estructura Detallada

### Frontend (`src/`)
```
src/
├── components/          # Componentes reutilizables
├── hooks/              # Hooks personalizados
├── modules/            # Módulos principales
│   ├── dashboard/      # Dashboard ejecutivo
│   ├── empresas/       # Gestión de empresas con consulta RUC
│   ├── obras/          # Administración de obras
│   ├── valorizaciones/ # Sistema de valorizaciones
│   └── reporte/        # Reportes especializados
├── types/              # Definiciones TypeScript
└── utils/              # Utilidades y helpers
```

### Backend (`backend/`)
```
backend/
├── app/
│   ├── api/routes/     # Endpoints REST
│   ├── core/          # Configuración y base de datos
│   ├── models/        # Modelos de datos
│   ├── services/      # Lógica de negocio
│   └── utils/         # Utilidades
├── main.py           # Punto de entrada
└── requirements.txt  # Dependencias Python
```

## 🎨 Características de UX/UI

- **Diseño responsive** para todos los dispositivos
- **Tema coherente** con colores municipales
- **Animaciones fluidas** para mejor experiencia
- **Navegación intuitiva** con breadcrumbs
- **Feedback visual** en todas las acciones
- **Modo oscuro** disponible

## 🔐 Seguridad

- **Validaciones** en frontend y preparado para backend
- **Sanitización** de inputs de usuario
- **Manejo seguro** de datos sensibles
- **Preparado** para autenticación y autorización

## 🚀 Características Avanzadas

- **Actualización en tiempo real** del dashboard
- **Búsquedas instantáneas** con filtros avanzados
- **Exportación masiva** de datos
- **Sistema de notificaciones** inteligente
- **Métricas de rendimiento** integradas

## 📞 Soporte

Sistema desarrollado para la **Municipalidad Distrital de San Marcos**
- **Distrito**: San Marcos
- **Provincia**: Huari  
- **Región**: Áncash, Perú

## 📄 Licencia

Este proyecto ha sido desarrollado específicamente para uso municipal y gubernamental.

## 🤝 Contribuciones

Este es un sistema especializado para administración pública municipal. Las contribuciones deben seguir las normas y procedimientos establecidos por la entidad.

---

**Desarrollado con ❤️ para el desarrollo municipal del Distrito de San Marcos** 🏔️
