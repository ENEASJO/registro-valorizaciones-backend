# Funcionalidad de Consulta RUC con SUNAT

## Descripción

Se ha implementado una funcionalidad completa de consulta RUC con SUNAT que permite:

1. **Validar formato de RUC** (11 dígitos, comienza con 20)
2. **Consultar información en SUNAT** (simulada con datos mock)
3. **Auto-completar formularios** con información oficial
4. **Crear empresas directamente** desde datos de SUNAT
5. **Manejo de errores y advertencias** sobre el estado de las empresas

## Archivos Implementados

### 1. Tipos TypeScript (`/src/types/sunat.types.ts`)
- `ConsultaSunatResponse`: Respuesta de la API de consulta
- `DatosSunat`: Información completa de la empresa
- `RepresentanteLegal`: Datos del representante legal
- `EstadoConsulta`: Estados del proceso de consulta

### 2. Servicio SUNAT (`/src/services/sunatService.ts`)
- `consultarRucSunat()`: Función principal de consulta
- `validarFormatoRuc()`: Validación del formato del RUC
- `obtenerRepresentantePrincipal()`: Helper para obtener representante vigente
- Datos mock pre-configurados para RUCs de ejemplo
- Generación automática de datos para RUCs no configurados

### 3. Hook personalizado (`/src/hooks/useSunat.ts`)
- `useSunat()`: Hook básico para consultas SUNAT
- `useSunatAutocompletar()`: Hook especializado para autocompletado de formularios
- Manejo de estado de loading, errores y datos
- Funciones helper para extraer información específica

### 4. Formulario de Empresa (`/src/modules/empresas/components/FormularioEmpresa.tsx`)
- Botón "Consultar SUNAT" junto al campo RUC
- Modal de confirmación con información detallada
- Auto-completado de campos: razón social, dirección, representante legal
- Indicadores visuales de estado (loading, success, error)
- Advertencias sobre estado de contribuyente y domicilio

### 5. Formulario de Consorcio (`/src/modules/empresas/components/FormularioConsorcio.tsx`)
- Opción para crear nuevas empresas por RUC
- Integración con el listado de empresas existentes
- Modal de confirmación específico para creación de empresas
- Creación automática y agregado al consorcio

## RUCs de Ejemplo Pre-configurados

Los siguientes RUCs están pre-configurados con datos completos:

- **20123456789**: CONSTRUCTORA GENERAL ABC SOCIEDAD ANONIMA CERRADA
- **20987654321**: INGENIERIA Y CONSTRUCCION XYZ EMPRESA INDIVIDUAL DE RESPONSABILIDAD LIMITADA
- **20456789123**: GRUPO CONSTRUCTOR PERU SOCIEDAD ANONIMA
- **20111222333**: CONSTRUCTORA NORTE SOCIEDAD DE RESPONSABILIDAD LIMITADA
- **20444555666**: INVERSIONES Y OBRAS COSTA VERDE SOCIEDAD ANONIMA CERRADA
- **20777888999**: CONSTRUCTORA ANTIGUA SOCIEDAD ANONIMA (estado SUSPENSION TEMPORAL)

## Funcionalidades por Contexto

### 1. Empresas Ejecutoras Individuales
- Campo RUC con botón "Consultar SUNAT"
- Auto-completado de razón social y representante legal
- Validaciones de estado activo y domicilio habido
- Modal de confirmación antes del auto-completado

### 2. Empresas Supervisoras Individuales
- Misma funcionalidad que empresas ejecutoras
- Interfaz diferenciada con colores verdes
- Validaciones específicas para supervisión

### 3. Integrantes de Consorcios (Ejecución y Supervisión)
- Creación de nuevas empresas directamente por RUC
- Verificación de empresas existentes antes de crear duplicados
- Agregado automático al consorcio después de la creación
- Modal específico para creación desde SUNAT

## Flujo de Uso

### Para Empresas Individuales:
1. Ingresar RUC en el campo correspondiente (11 dígitos)
2. Hacer clic en "Consultar SUNAT"
3. Revisar la información encontrada en el modal
4. Confirmar el auto-completado o cancelar
5. Los campos se llenan automáticamente con los datos de SUNAT

### Para Consorcios:
1. Hacer clic en "Crear nueva empresa consultando RUC en SUNAT"
2. Ingresar el RUC de la empresa
3. Hacer clic en "Consultar SUNAT"
4. Revisar la información en el modal de confirmación
5. Confirmar la creación de la empresa
6. La empresa se crea y se agrega automáticamente al consorcio

## Manejo de Errores y Advertencias

### Validaciones de RUC:
- RUC debe tener exactamente 11 dígitos
- RUC debe contener solo números
- RUC debe comenzar con "20" (empresas)

### Advertencias SUNAT:
- ⚠️ Empresa no está en estado ACTIVO
- ⚠️ Domicilio no está HABIDO
- ⚠️ Representante legal podría no estar vigente

### Errores de Conexión:
- Timeout de consulta
- Empresa no encontrada
- Error de formato de datos

## Estados Visuales

### Botón de Consulta:
- **Deshabilitado**: RUC incompleto o inválido
- **Loading**: Animación de spinner durante consulta
- **Success**: Icono de check verde, botón cambia a "Consultado"
- **Error**: Mensaje de error debajo del campo RUC

### Campo RUC:
- **Normal**: Border gris
- **Error**: Border rojo
- **Success**: Border verde con fondo verde claro

### Indicadores:
- **Badge de estado**: Muestra estado del contribuyente (ACTIVO/INACTIVO)
- **Badge de condición**: Muestra condición del domicilio (HABIDO/NO HABIDO)

## Datos Mock Generados

Para RUCs no pre-configurados, el sistema genera automáticamente:
- Razón social basada en patrones comunes
- Nombre comercial derivado
- Dirección con formato estándar peruano
- Representante legal con nombres típicos
- DNI de representante (8 dígitos)
- Ubicación geográfica (Lima, Arequipa, Cusco, etc.)

## Consideraciones Técnicas

### Performance:
- Simulación de delay de API real (1.5-2.5 segundos)
- Cache interno para evitar consultas repetidas
- Validaciones client-side antes de consultar

### UX/UI:
- Modales informativos con detalles completos
- Animaciones suaves con Framer Motion
- Feedback visual inmediato para todas las acciones
- Diseño responsive para móviles y desktop

### Tipos TypeScript:
- Tipado estricto para todas las interfaces
- Validación de tipos en tiempo de compilación
- IntelliSense completo para desarrollo

## Próximas Mejoras

1. **Integración con API real de SUNAT** cuando esté disponible
2. **Cache persistente** para consultas frecuentes
3. **Histórico de consultas** por usuario
4. **Validación de dígito verificador** del RUC
5. **Export/Import de empresas** desde/hacia Excel
6. **Notificaciones push** para cambios de estado en SUNAT

## Soporte y Mantenimiento

La funcionalidad está completamente integrada con el sistema existente y es fácilmente extensible. Los datos mock pueden ser reemplazados por la integración real de SUNAT sin cambiar la interfaz de usuario.

Para agregar nuevos RUCs de ejemplo, simplemente actualizar el objeto `EMPRESAS_MOCK` en `/src/services/sunatService.ts`.