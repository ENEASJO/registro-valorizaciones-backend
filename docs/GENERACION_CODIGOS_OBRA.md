# Sistema de Generación Automática de Códigos de Obra

## Descripción

El sistema genera automáticamente códigos únicos para las obras siguiendo un patrón estructurado y legible. Esto elimina la necesidad de que el usuario ingrese manualmente el código y garantiza la unicidad.

## Patrón de Códigos

### Formato
```
{PREFIJO}-{EMPRESA}-{AÑO}-{SECUENCIA}
```

### Ejemplos
- `OBR-001-2025-12270845` - Obra de empresa 1, año 2025
- `OBR-123-2025-12270846` - Obra de empresa 123, año 2025
- `VAL-OBR-001-2025-12270845-001` - Primera valorización de la obra

### Componentes

1. **PREFIJO** (3 caracteres)
   - `OBR` - Para obras
   - `VAL` - Para valorizaciones
   - Personalizable según tipo de entidad

2. **EMPRESA** (3 dígitos con padding de ceros)
   - ID de la empresa ejecutora
   - Formato: `001`, `123`, `999`

3. **AÑO** (4 dígitos)
   - Año actual de creación
   - Formato: `2025`, `2026`, etc.

4. **SECUENCIA** (8 dígitos)
   - Basado en timestamp del momento de creación
   - Formato: `MMDDHHMM` (Mes, Día, Hora, Minuto)
   - Garantiza unicidad temporal

## Implementación

### 1. Generador de Códigos (`codigo_generator.py`)

```python
from app.utils.codigo_generator import CodigoGenerator

# Generar código de obra
codigo = CodigoGenerator.generar_codigo_obra(
    empresa_id=1, 
    prefijo="OBR"
)
# Resultado: "OBR-001-2025-12270845"

# Validar código
es_valido = CodigoGenerator.validar_codigo_obra("OBR-001-2025-12270845")
# Resultado: True

# Extraer información
info = CodigoGenerator.extraer_info_codigo("OBR-001-2025-12270845")
# Resultado: {
#     "prefijo": "OBR",
#     "empresa_id": 1,
#     "año": 2025,
#     "secuencia": "12270845",
#     "codigo_completo": "OBR-001-2025-12270845"
# }
```

### 2. Servicio de Obras (`obra_service_neon.py`)

```python
from app.services.obra_service_neon import ObraServiceNeon
from app.models.obra import ObraCreate

# Crear obra (código se genera automáticamente)
obra_data = ObraCreate(
    nombre="Centro de Salud Las Flores",
    empresa_id=1,
    cliente="MINSA",
    monto_contractual=500000.00
)

obra = await ObraServiceNeon.crear_obra(obra_data)
# El código se genera automáticamente: "OBR-001-2025-12270845"
```

### 3. Modelo de Obra (`obra.py`)

El modelo `ObraCreate` ya **NO requiere** el campo `codigo` - se genera automáticamente:

```python
# ✅ CORRECTO - No incluir código
obra_nueva = {
    "nombre": "Construcción de Colegio",
    "empresa_id": 1,
    "cliente": "MINEDU",
    "monto_contractual": 800000.00
}

# ❌ INCORRECTO - No es necesario enviar código
obra_nueva = {
    "codigo": "OBR-001-2025-12270845",  # Se ignora
    "nombre": "Construcción de Colegio",
    "empresa_id": 1
}
```

## API Endpoints

### Crear Obra
```http
POST /obras/
Content-Type: application/json

{
    "nombre": "Construcción de Centro de Salud",
    "empresa_id": 1,
    "cliente": "Ministerio de Salud",
    "ubicacion": "Av. Principal 123",
    "distrito": "San Juan",
    "provincia": "Lima", 
    "departamento": "Lima",
    "modalidad_ejecucion": "CONTRATA",
    "sistema_contratacion": "SUMA_ALZADA",
    "tipo_obra": "Edificación - Salud",
    "monto_contractual": 500000.00,
    "fecha_inicio": "2025-01-15",
    "fecha_fin_contractual": "2025-12-15",
    "plazo_contractual": 365
}
```

### Respuesta
```json
{
    "success": true,
    "message": "Obra creada exitosamente",
    "data": {
        "id": 1,
        "codigo": "OBR-001-2025-12270845",
        "nombre": "Construcción de Centro de Salud",
        "empresa_id": 1,
        "empresa_nombre": "Constructora ABC S.A.C.",
        "cliente": "Ministerio de Salud",
        "monto_total": 500000.00,
        "estado_obra": "PLANIFICADA",
        "created_at": "2025-01-27T16:45:00Z"
    },
    "timestamp": "2025-01-27T16:45:00.123Z"
}
```

## Base de Datos

### Tabla obras
```sql
CREATE TABLE obras (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(50) UNIQUE NOT NULL,  -- Generado automáticamente
    nombre VARCHAR(500) NOT NULL,
    empresa_id INTEGER NOT NULL,
    -- ... otros campos
    
    CONSTRAINT fk_obras_empresa FOREIGN KEY (empresa_id) REFERENCES empresas(id)
);

-- Índices para optimización
CREATE INDEX idx_obras_codigo ON obras(codigo);
CREATE INDEX idx_obras_empresa_id ON obras(empresa_id);
```

### Triggers Automáticos
- **Actualización de `updated_at`**: Se actualiza automáticamente en cada modificación
- **Cálculo de `monto_total`**: Se calcula automáticamente como suma de contractual + adicionales

## Ventajas del Sistema

### ✅ Para el Usuario
- **Sin errores manuales**: No hay riesgo de códigos duplicados o mal formados
- **Consistencia**: Todos los códigos siguen el mismo patrón
- **Simplicidad**: Solo completa los datos de la obra, sin preocuparse por el código
- **Legibilidad**: Códigos fáciles de leer e interpretar

### ✅ Para el Sistema
- **Unicidad garantizada**: Imposible tener códigos duplicados
- **Trazabilidad**: Códigos contienen información sobre empresa y fecha
- **Escalabilidad**: Soporte para millones de obras sin conflictos
- **Mantenibilidad**: Lógica centralizada y reutilizable

## Casos de Uso

### Crear Obra Simple
```python
obra = await ObraServiceNeon.crear_obra(ObraCreate(
    nombre="Mejoramiento de Plaza Principal",
    empresa_id=5,
    monto_contractual=150000.00
))
# Código generado: "OBR-005-2025-12271030"
```

### Buscar Obra por Código
```python
obra = await ObraServiceNeon.obtener_obra_por_codigo("OBR-005-2025-12271030")
```

### Validar Código Externamente
```python
# Validar formato
if CodigoGenerator.validar_codigo_obra(codigo_recibido):
    info = CodigoGenerator.extraer_info_codigo(codigo_recibido)
    empresa_id = info["empresa_id"]
```

## Consideraciones de Producción

### Concurrencia
- La secuencia basada en timestamp maneja múltiples creaciones simultáneas
- En caso de colisión (muy improbable), el sistema reintenta automáticamente

### Respaldo en Base de Datos
- Función SQL `generar_codigo_obra()` disponible como respaldo
- Los triggers garantizan consistencia de datos

### Monitoreo
- Logs detallados en cada generación de código
- Métricas de unicidad y performance disponibles

### Migración de Datos Existentes
Si tienes obras sin código, puedes ejecutar:
```sql
UPDATE obras 
SET codigo = generar_codigo_obra(empresa_id) 
WHERE codigo IS NULL OR codigo = '';
```

## Soporte Futuro

El sistema está preparado para:
- **Múltiples tipos de entidad**: Valorizaciones, contratos, etc.
- **Prefijos personalizados**: Por región, tipo de proyecto, etc.
- **Formatos alternativos**: Diferentes patrones según necesidades
- **Integración con sistemas externos**: APIs para generar códigos

---

**Fecha de implementación**: 27 de enero de 2025  
**Versión**: 1.0  
**Autor**: Sistema de Registro de Valorizaciones