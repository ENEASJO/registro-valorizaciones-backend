# Sistema de Valorizaciones - Municipalidad de San Marcos

Sistema integral para la administración y gestión de valorizaciones de obras públicas municipales, desarrollado específicamente para el Distrito de San Marcos, Provincia de Huari, Región Áncash, Perú.

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

### Frontend
- **React 18** con TypeScript
- **Vite** para desarrollo y build
- **Tailwind CSS** para estilos
- **Framer Motion** para animaciones
- **Recharts** para visualizaciones
- **React Router** para navegación
- **Lucide React** para iconografía

### Librerías Especializadas
- **jsPDF** para generación de PDFs
- **SheetJS (xlsx)** para exportación Excel
- **React Hook Form** para manejo de formularios
- **Zod** para validación de esquemas

### Arquitectura
- **Componentes modulares** reutilizables
- **Hooks personalizados** para lógica de negocio
- **Tipos TypeScript** estrictos
- **Estructura escalable** por módulos

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
npm >= 9.0.0
```

### Instalación
```bash
# Clonar el repositorio
git clone [URL_DEL_REPOSITORIO]
cd valoraciones-app

# Instalar dependencias
npm install

# Iniciar servidor de desarrollo
npm run dev
```

### Scripts disponibles
```bash
npm run dev          # Servidor de desarrollo
npm run build        # Build para producción
npm run preview      # Preview del build
npm run lint         # Análisis de código
```

## 📁 Estructura del Proyecto

```
src/
├── components/          # Componentes reutilizables
│   └── layout/         # Layout principal y navegación
├── hooks/              # Hooks personalizados
├── modules/            # Módulos principales
│   ├── dashboard/      # Dashboard ejecutivo
│   ├── empresas/       # Gestión de empresas
│   ├── obras/          # Administración de obras
│   ├── valorizaciones/ # Sistema de valorizaciones
│   ├── reporte/        # Reportes especializados
│   └── configuracion/  # Configuración del sistema
├── types/              # Definiciones TypeScript
└── utils/              # Utilidades y helpers
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
