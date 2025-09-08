# Módulo de Empresas - Sistema de Valorizaciones

## Descripción

Módulo completo para la gestión de empresas contratistas (ejecutoras y supervisoras) y consorcios para el sistema de valorizaciones de obras públicas municipales.

## Características Implementadas

### ✅ Funcionalidades Principales

1. **Gestión de Empresas Individuales**
   - Registro de empresas con información completa
   - Validación de RUC, email, teléfonos
   - Categorización por especialidades y capacidad
   - Estados: ACTIVO, INACTIVO, SUSPENDIDO

2. **Gestión de Consorcios**
   - Creación de consorcios con mínimo 2 empresas
   - Asignación de porcentajes de participación (debe sumar 100%)
   - Designación de empresa líder
   - Asignación de responsabilidades por empresa

3. **Interfaz de Usuario**
   - Tabs separadas para Ejecutoras/Supervisoras
   - Vista de cards con información resumida
   - Búsqueda avanzada con múltiples filtros
   - Modal detallado para visualizar información completa

4. **Validaciones**
   - RUC de 11 dígitos que inicie con "20"
   - Email válido (opcional)
   - Suma exacta de porcentajes en consorcios
   - Campos obligatorios marcados

## Estructura de Archivos

```
src/modules/empresas/
├── Empresas.tsx                    # Componente principal
├── components/
│   ├── FormularioEmpresa.tsx       # Modal para crear/editar empresas
│   ├── FormularioConsorcio.tsx     # Modal para crear consorcios
│   ├── ListaEntidades.tsx          # Lista con filtros y búsqueda
│   ├── DetalleEntidad.tsx          # Vista detallada
│   └── index.ts                    # Exportaciones
└── README.md                       # Esta documentación
```

## Hooks Personalizados

### `useEmpresas()`
- `empresas`: Lista de empresas
- `loading`: Estado de carga
- `error`: Mensajes de error
- `cargarEmpresas()`: Cargar lista con filtros
- `crearEmpresa()`: Crear nueva empresa
- `actualizarEmpresa()`: Actualizar empresa existente
- `eliminarEmpresa()`: Eliminar empresa
- `obtenerEmpresaPorId()`: Obtener empresa específica

### `useConsorcios()`
- `consorcios`: Lista de consorcios
- `loading`: Estado de carga
- `error`: Mensajes de error
- `cargarConsorcios()`: Cargar lista con filtros
- `crearConsorcio()`: Crear nuevo consorcio
- `obtenerConsorcioPorId()`: Obtener consorcio específico

### `useEntidadesContratistas()`
- `entidades`: Vista unificada de empresas y consorcios
- `loading`: Estado de carga
- `error`: Mensajes de error

### `useValidacionesEmpresa()`
- `validarRuc()`: Validar formato RUC
- `validarEmail()`: Validar formato email
- `validarTelefono()`: Validar formato teléfono
- `validarPorcentajesConsorcio()`: Validar suma de porcentajes
- `validarEmpresaForm()`: Validar formulario completo

## Tipos TypeScript

Todos los tipos están definidos en `/src/types/empresa.types.ts`:

- `Empresa`: Empresa individual
- `Consorcio`: Consorcio de empresas
- `EntidadContratistaDetalle`: Vista unificada con datos extendidos
- `EmpresaForm`: Datos del formulario de empresa
- `ConsorcioForm`: Datos del formulario de consorcio
- `CrearConsorcioParams`: Parámetros para crear consorcio
- Tipos de apoyo: `EstadoGeneral`, `TipoEmpresa`, `CategoriaContratista`, `EspecialidadEmpresa`

## Uso del Componente

```tsx
import Empresas from './modules/empresas/Empresas';

function App() {
  return (
    <div>
      <Empresas />
    </div>
  );
}
```

## Funcionalidades Futuras (Pendientes)

1. **Integración con API Backend**
   - Reemplazar mock data con llamadas reales
   - Manejo de estados de carga y errores de red
   - Paginación para listas grandes

2. **Gestión de Documentos**
   - Upload de documentos (RUC, RNP, poderes, etc.)
   - Vista previa de documentos
   - Control de vencimientos

3. **Historial de Cambios**
   - Auditoría completa de modificaciones
   - Vista de versiones anteriores
   - Comentarios en cambios

4. **Exportación de Datos**
   - Exportar a Excel/PDF
   - Reportes personalizados
   - Datos estadísticos

5. **Roles y Permisos**
   - Control de acceso por usuario
   - Diferentes niveles de permisos
   - Aprobaciones de cambios

## Notas Técnicas

- **Framework**: React 18+ con TypeScript
- **Componentes**: Radix UI para elementos base
- **Animaciones**: Framer Motion
- **Iconos**: Lucide React
- **Estilos**: Tailwind CSS
- **Estado**: Hooks locales (preparado para Context/Redux)

## Data Mock

El módulo incluye data de prueba realista:
- 3 empresas de ejemplo con datos completos
- 1 consorcio de ejemplo con 2 empresas participantes
- Especialidades variadas y estados diferentes

Esta data se puede usar para testing y desarrollo antes de conectar con el backend.