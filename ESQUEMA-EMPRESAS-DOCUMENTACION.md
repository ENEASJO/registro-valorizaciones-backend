# Esquema de Base de Datos - Módulo Empresas

## Resumen Ejecutivo

Este documento describe el diseño completo de la base de datos para el módulo de Empresas del sistema de valorizaciones de obras públicas municipales. El esquema está optimizado para manejar empresas individuales, consorcios, y sus roles como ejecutores o supervisores en diferentes obras.

## Características Principales del Diseño

### ✅ Requisitos Cumplidos

1. **Empresas Ejecutoras y Supervisoras**: Sistema unificado que permite roles diferentes
2. **Consorcios como Regla General**: Diseño optimizado para manejo de consorcios
3. **Empresas Individuales**: Soporte para casos excepcionales sin consorcio
4. **Flexibilidad de Roles**: Un consorcio puede ser ejecutor en una obra y supervisor en otra
5. **Participación Múltiple**: Empresas pueden formar parte de múltiples consorcios
6. **Histórico y Auditoría**: Sistema completo de trazabilidad de cambios
7. **Consultas Eficientes**: Índices optimizados para queries del negocio

## Arquitectura del Esquema

### Tablas Principales

#### 1. `empresas`
- **Propósito**: Registro maestro de empresas individuales
- **Características**: 
  - Datos completos de identificación y contacto
  - Clasificación por categoría de contratista (A, B, C, D, E)
  - Especialidades almacenadas como JSONB para flexibilidad
  - Validación automática de RUC único

```sql
-- Ejemplo de registro
INSERT INTO empresas (ruc, razon_social, categoria_contratista, especialidades)
VALUES ('20123456789', 'CONSTRUCTORA ABC SAC', 'A', '["EDIFICACIONES", "CARRETERAS"]');
```

#### 2. `consorcios`
- **Propósito**: Registro de consorcios formados por múltiples empresas
- **Características**:
  - Empresa líder obligatoria
  - Fechas de constitución y disolución
  - Especialidades combinadas de las empresas participantes

#### 3. `consorcio_empresas`
- **Propósito**: Relación many-to-many entre consorcios y empresas
- **Características**:
  - Porcentajes de participación con validación automática (suma = 100%)
  - Roles y responsabilidades específicas
  - Historial de entrada y salida de empresas

#### 4. `entidades_contratistas`
- **Propósito**: Vista unificada de empresas y consorcios para contratación
- **Características**:
  - Patrón polimórfico para unificar empresas y consorcios
  - Datos denormalizados para consultas rápidas
  - Mantenimiento automático vía triggers

#### 5. `obra_contratistas`
- **Propósito**: Asignación de entidades a obras con roles específicos
- **Características**:
  - Roles: EJECUTOR o SUPERVISOR
  - Datos completos del contrato
  - Una entidad puede tener diferentes roles en diferentes obras

### Tablas de Soporte

#### 6. `empresa_auditoria`
- Registro completo de todos los cambios
- Datos anteriores y nuevos en formato JSON
- Triggers automáticos en todas las tablas principales

#### 7. `empresa_documentos`
- Gestión de documentos adjuntos
- Control de vigencias y vencimientos
- Tipos predefinidos: RUC, RNP, Constitución, etc.

## Funcionalidades Avanzadas

### Sistema de Auditoría Automática

```sql
-- Todos los cambios se registran automáticamente
SELECT 
    operacion, 
    created_at, 
    datos_anteriores->'razon_social' as nombre_anterior,
    datos_nuevos->'razon_social' as nombre_nuevo
FROM empresa_auditoria 
WHERE tabla_origen = 'empresas' AND registro_id = 1;
```

### Validaciones de Integridad

1. **Porcentajes de Consorcio**: La suma nunca puede exceder 100%
2. **Referencias**: Claves foráneas con cascade apropiado
3. **Estados**: Check constraints para valores válidos
4. **Fechas**: Validación de rangos lógicos

### Triggers Inteligentes

1. **Actualización Automática**: `updated_at` se actualiza automáticamente
2. **Sincronización**: `entidades_contratistas` se mantiene sincronizada
3. **Auditoría**: Todos los cambios se registran sin intervención manual

## Optimizaciones de Performance

### Índices Estratégicos

```sql
-- Búsquedas por texto
CREATE INDEX idx_empresas_nombre_search ON empresas USING GIN(
    to_tsvector('spanish', razon_social || ' ' || COALESCE(nombre_comercial, ''))
);

-- Consultas de especialidades
CREATE INDEX idx_empresas_especialidades ON empresas USING GIN(especialidades);

-- Consultas por estado y tipo
CREATE INDEX idx_entidades_tipo_estado_activo ON entidades_contratistas(tipo_entidad, estado, activo);
```

### Consultas Optimizadas

Las vistas preconfiguradas permiten consultas complejas con alto rendimiento:

```sql
-- Vista unificada con toda la información
SELECT * FROM v_entidades_contratistas_detalle 
WHERE nombre_completo ILIKE '%CONSTRUCTOR%';
```

## Patrones de Uso

### 1. Crear un Consorcio

```sql
-- Usar la función predefinida
SELECT crear_consorcio(
    'CONSORCIO NORTE 2024',
    'Consorcio para obras del norte',
    '2024-03-01',
    1,  -- ID empresa líder
    '[
        {"empresa_id": 1, "porcentaje": 70.00, "responsabilidades": ["EJECUCIÓN"]},
        {"empresa_id": 2, "porcentaje": 30.00, "responsabilidades": ["SUPERVISIÓN"]}
    ]'::jsonb,
    1   -- usuario
);
```

### 2. Buscar Entidades Disponibles

```sql
-- Entidades disponibles para una obra específica
SELECT * FROM obtener_entidades_disponibles(
    p_obra_id := 123,
    p_categoria := 'A',
    p_especialidad := 'CARRETERAS'
);
```

### 3. Asignar Contratista a Obra

```sql
INSERT INTO obra_contratistas (obra_id, entidad_contratista_id, rol, numero_contrato)
VALUES (123, 45, 'EJECUTOR', 'CONT-2024-001');
```

## Consideraciones de Escalabilidad

### Particionamiento (Futuro)

El esquema está preparado para particionamiento por fecha en tablas de auditoría:

```sql
-- Ejemplo de partición mensual para auditoría
CREATE TABLE empresa_auditoria_202401 PARTITION OF empresa_auditoria
FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
```

### Archivado de Datos

Sistema de soft-delete con campo `activo` para mantener integridad referencial:

```sql
-- Inactivar en lugar de eliminar
UPDATE empresas SET activo = FALSE WHERE id = 123;
```

## Integración con Frontend

### Tipos TypeScript

El archivo `empresa.types.ts` proporciona:
- Interfaces completas para todas las entidades
- Tipos para formularios y validación
- Interfaces para respuestas de API
- Tipos para filtros y búsquedas

### Endpoints API Sugeridos

```typescript
// Estructura sugerida para la API
GET    /api/empresas              // Listar empresas con filtros
POST   /api/empresas              // Crear empresa
GET    /api/empresas/:id          // Obtener empresa específica
PUT    /api/empresas/:id          // Actualizar empresa
DELETE /api/empresas/:id          // Inactivar empresa

GET    /api/consorcios            // Listar consorcios
POST   /api/consorcios            // Crear consorcio (con empresas)
GET    /api/consorcios/:id        // Obtener consorcio completo
PUT    /api/consorcios/:id        // Actualizar consorcio
DELETE /api/consorcios/:id        // Inactivar consorcio

GET    /api/entidades-contratistas // Búsqueda unificada
GET    /api/entidades-contratistas/disponibles // Para asignación a obras
```

## Casos de Uso Cubiertos

### ✅ Casos Implementados

1. **Empresa Individual como Ejecutor**
   ```sql
   -- Empresa ABC ejecuta obra 123
   INSERT INTO obra_contratistas (obra_id, entidad_contratista_id, rol)
   VALUES (123, (SELECT id FROM entidades_contratistas WHERE empresa_id = 1), 'EJECUTOR');
   ```

2. **Consorcio como Supervisor en una obra y Ejecutor en otra**
   ```sql
   -- Mismo consorcio, diferentes roles
   INSERT INTO obra_contratistas (obra_id, entidad_contratista_id, rol) VALUES
   (123, 15, 'SUPERVISOR'),  -- Obra 123: supervisor
   (124, 15, 'EJECUTOR');    -- Obra 124: ejecutor
   ```

3. **Empresa participa en múltiples consorcios**
   ```sql
   -- Empresa 1 participa en consorcio A y B
   INSERT INTO consorcio_empresas (consorcio_id, empresa_id, porcentaje_participacion) VALUES
   (1, 1, 60.00),  -- 60% en consorcio 1
   (2, 1, 40.00);  -- 40% en consorcio 2
   ```

4. **Trazabilidad completa de cambios**
   ```sql
   -- Ver historial completo de una empresa
   SELECT * FROM empresa_auditoria 
   WHERE tabla_origen = 'empresas' AND registro_id = 1
   ORDER BY created_at DESC;
   ```

## Mantenimiento y Monitoreo

### Scripts de Mantenimiento

```sql
-- Verificar integridad de porcentajes
SELECT * FROM consorcios c
WHERE (
    SELECT SUM(porcentaje_participacion) 
    FROM consorcio_empresas ce 
    WHERE ce.consorcio_id = c.id AND ce.activo = TRUE
) != 100.00;

-- Identificar documentos próximos a vencer
SELECT * FROM empresa_documentos 
WHERE fecha_vencimiento BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '30 days'
AND estado = 'VIGENTE';
```

### Métricas de Performance

```sql
-- Consultas lentas potenciales
SELECT schemaname, tablename, attname, n_distinct, correlation
FROM pg_stats 
WHERE tablename IN ('empresas', 'consorcios', 'entidades_contratistas')
ORDER BY n_distinct DESC;
```

## Consideraciones de Seguridad

1. **Datos Sensibles**: RUC y datos personales tienen índices apropiados
2. **Auditoría**: Registro de IP y user agent en cambios
3. **Soft Delete**: No eliminación física de datos críticos
4. **Validaciones**: Check constraints previenen datos inconsistentes

## Conclusión

Este esquema proporciona una base sólida y escalable para el módulo de Empresas, cumpliendo todos los requisitos del negocio mientras mantiene flexibilidad para futuras extensiones. La combinación de validaciones automáticas, auditoría completa, y optimizaciones de performance aseguran un sistema robusto y mantenible.

### Archivos Entregados

1. **`database-schema.sql`**: Esquema completo con tablas, índices, triggers y datos de prueba
2. **`database-queries-examples.sql`**: Consultas de ejemplo y procedimientos útiles
3. **`src/types/empresa.types.ts`**: Definiciones TypeScript para el frontend
4. **`ESQUEMA-EMPRESAS-DOCUMENTACION.md`**: Esta documentación completa

### Próximos Pasos Sugeridos

1. Implementar la API REST con los endpoints sugeridos
2. Crear componentes de frontend usando los tipos TypeScript
3. Configurar tareas de mantenimiento automático
4. Implementar notificaciones para documentos próximos a vencer
5. Crear dashboard de métricas operativas