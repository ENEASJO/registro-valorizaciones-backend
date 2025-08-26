# Sistema de Consolidación SUNAT + OSCE

## Descripción General

Este sistema migra la funcionalidad de consolidación de datos del sistema Python original a Node.js, manteniendo la misma lógica de negocio y estructura de respuesta. Combina datos de SUNAT y OSCE con deduplicación inteligente de miembros.

## Arquitectura

### Componentes Principales

1. **Consulta SUNAT**: Usa Playwright para scraping real + APIs externas como fallback
2. **Consulta OSCE**: Implementa scraping web completo usando Playwright
3. **Consolidación**: Combina datos de ambas fuentes con lógica de prioridades
4. **Deduplicación**: Algoritmo inteligente que identifica miembros duplicados por DNI o similitud de nombres

### Flujo de Procesamiento

```
RUC Request
    ↓
┌─────────────┬─────────────┐
│   SUNAT     │    OSCE     │
│  (Paralelo) │ (Paralelo)  │
└─────────────┴─────────────┘
    ↓
Consolidación de Datos
    ↓
Deduplicación de Miembros
    ↓
Respuesta Unificada
```

## API Endpoints

### 1. Health Check
```
GET /health
```
Respuesta:
```json
{
  "status": "OK",
  "service": "valoraciones-consolidado-cloudrun",
  "version": "10.0",
  "features": ["SUNAT + OSCE consolidation"]
}
```

### 2. Consulta Consolidada (Principal)
```
GET /consulta-ruc-consolidada/:ruc
```

Respuesta exitosa:
```json
{
  "success": true,
  "data": {
    "ruc": "20160669234",
    "razon_social": "SANTA ROSA SCRL",
    "contacto": {
      "telefono": "",
      "email": "",
      "direccion": "",
      "domicilio_fiscal": "PROLONGACION TACNA NRO. 408 LAMBAYEQUE"
    },
    "miembros": [
      {
        "nombre": "JUAN PEREZ",
        "cargo": "GERENTE GENERAL",
        "fuente": "SUNAT",
        "numero_documento": "12345678"
      }
    ],
    "especialidades": ["Construcción", "Consultoría"],
    "registro": {
      "sunat": { "estado": "ACTIVO" },
      "osce": { "estado_registro": "HABILITADO" }
    },
    "fuentes_consultadas": ["SUNAT", "OSCE"],
    "fuentes_con_errores": [],
    "consolidacion_exitosa": true
  },
  "fuente": "CONSOLIDADO",
  "version": "10.0-nodejs"
}
```

### 3. Consulta SUNAT Individual
```
GET /consulta-ruc/:ruc
```

### 4. Consulta OSCE Individual
```
GET /consulta-osce/:ruc
```

## Lógica de Consolidación

### Prioridades de Datos

1. **Razón Social**: SUNAT > OSCE
2. **Contacto**: OSCE > SUNAT (más detallado)
3. **Miembros**: Deduplicación inteligente combinando ambas fuentes
4. **Especialidades**: Solo OSCE

### Deduplicación de Miembros

El sistema identifica miembros duplicados usando:

1. **Matching por DNI** (prioridad alta): Coincidencia exacta de número de documento
2. **Matching por nombre** (similitud): Algoritmo de Levenshtein + análisis de tokens
   - Umbral de similitud: 70%
   - Limpieza de nombres: normalización, eliminación de caracteres especiales
   - Análisis de tokens: comparación palabra por palabra

### Manejo de Errores

- Si una fuente falla, continúa con la otra
- Si ambas fallan, devuelve error con detalles
- Errores se registran en `observaciones` y `fuentes_con_errores`

## Casos de Uso Específicos

### RUC 20160669234 (SANTA ROSA SCRL)

Este RUC está configurado con datos reales verificados:
```json
{
  "razonSocial": "SANTA ROSA SCRL",
  "direccion": "PROLONGACION TACNA NRO. 408 LAMBAYEQUE - LAMBAYEQUE - LAMBAYEQUE",
  "estado": "ACTIVO",
  "condicion": "HABIDO"
}
```

## Pruebas

### Script de Prueba Automática
```bash
node test_consolidacion.js
```

### Script de Prueba Simple
```bash
./test_simple.sh
```

### Prueba Manual
```bash
curl http://localhost:8080/consulta-ruc-consolidada/20160669234 | jq .
```

## Diferencias con el Sistema Python

### Mantenido
- Estructura de respuesta idéntica
- Lógica de consolidación y deduplicación
- Prioridades de fuentes de datos
- Manejo de errores gracioso

### Mejorado
- Implementación nativa de similitud de strings (sin dependencias externas)
- Scraping OSCE más robusto con múltiples estrategias
- Logging detallado del proceso de consolidación
- Mejor manejo de timeouts y errores de red

## Configuración para Cloud Run

El sistema está optimizado para Google Cloud Run con:
- Browser Chromium configurado para contenedores
- Timeouts apropiados para el entorno serverless
- Logging estructurado para Cloud Logging
- Manejo eficiente de memoria y recursos

## Monitoreo

### Logs Clave
- `🔄 Iniciando consolidación para RUC: {ruc}`
- `✅ Datos SUNAT obtenidos exitosamente`
- `✅ Datos OSCE obtenidos exitosamente`
- `📊 Consolidación: {n} miembros únicos, {n} especialidades`

### Métricas de Éxito
- `consolidacion_exitosa: true`
- `fuentes_consultadas.length > 0`
- `fuentes_con_errores.length === 0` (ideal)

## Dependencias

- `express`: Servidor web
- `cors`: Manejo CORS
- `playwright`: Automatización de navegador para scraping
- Node.js 18+ (fetch nativo)