# 🧪 Documentación de Testing - Sistema Consolidado SUNAT + OSCE

## Descripción General

Este documento describe la suite completa de pruebas para el sistema de consolidación SUNAT + OSCE. El sistema ha sido migrado de Python a Node.js y requiere validación exhaustiva de todas sus funcionalidades.

## 📋 Arquitectura de Pruebas

### Estructura de Directorios

```
tests/
├── unit/                    # Pruebas unitarias
│   ├── validation.test.js          # Validación de RUC
│   └── string-similarity.test.js   # Algoritmos de similitud
├── integration/             # Pruebas de integración
│   ├── sunat.test.js              # Integración SUNAT
│   ├── osce.test.js               # Integración OSCE
│   ├── consolidation.test.js      # Consolidación de datos
│   ├── error-handling.test.js     # Manejo de errores
│   └── performance.test.js        # Rendimiento y timeouts
├── e2e/                     # Pruebas end-to-end
│   └── api-endpoints.test.js      # Endpoints HTTP
├── fixtures/                # Datos de prueba
│   └── test-data.js               # Fixtures y mocks
├── setup.js                 # Configuración global
└── env.js                   # Variables de entorno
```

## 🎯 Casos de Prueba Principales

### 1. Prueba Básica Crítica: RUC 20160669234

**Objetivo**: Verificar que el RUC específico `20160669234` retorne exactamente "SANTA ROSA SCRL"

```javascript
// Debe retornar datos hardcodeados correctos
expect(resultado.datos.razonSocial).toBe('SANTA ROSA SCRL');
expect(resultado.metodo).toBe('datos-reales-verificados');
```

### 2. Consolidación SUNAT + OSCE

**Objetivo**: Verificar que los datos de ambas fuentes se combinen correctamente

- **Prioridad razón social**: SUNAT tiene prioridad sobre OSCE
- **Información contacto**: OSCE tiene prioridad para contacto
- **Domicilio fiscal**: Solo viene de SUNAT

### 3. Deduplicación de Miembros

**Objetivo**: Validar que los miembros duplicados se identifiquen y consoliden

- **Matching por DNI**: Prioridad más alta
- **Matching por similitud de nombres**: Umbral 0.7
- **Preservación de información**: Combinar cargos de ambas fuentes

### 4. Manejo de Errores

**Objetivo**: Verificar comportamiento cuando una o ambas fuentes fallan

- **SUNAT falla, OSCE funciona**: Consolidar solo con OSCE
- **OSCE falla, SUNAT funciona**: Consolidar solo con SUNAT
- **Ambas fallan**: Lanzar error descriptivo

## 🚀 Comandos de Prueba

### Configuración Inicial

```bash
# Instalar dependencias de testing
npm install

# Instalar dependencias de desarrollo
npm install --save-dev jest supertest @jest/globals jest-environment-node
```

### Ejecutar Pruebas

```bash
# Todas las pruebas
npm test

# Solo pruebas unitarias
npm run test:unit

# Solo pruebas de integración
npm run test:integration

# Solo pruebas E2E
npm run test:e2e

# Con cobertura
npm run test:coverage

# En modo watch
npm run test:watch

# Pruebas rápidas con curl (servidor debe estar corriendo)
npm run test:quick
```

### Pruebas Manuales con curl

```bash
# Health check
curl http://localhost:8080/

# Consulta básica SUNAT
curl "http://localhost:8080/consulta-ruc/20160669234"

# Consulta consolidada completa
curl "http://localhost:8080/consulta-ruc-consolidada/20160669234" | jq .

# Consulta OSCE individual
curl "http://localhost:8080/consulta-osce/20160669234" | jq .

# Prueba con RUC inválido
curl "http://localhost:8080/consulta-ruc/12345678901"
```

## 📊 Métricas y Umbrales

### Cobertura de Código

- **Líneas**: ≥ 75%
- **Funciones**: ≥ 80%
- **Branches**: ≥ 70%
- **Statements**: ≥ 75%

### Performance

- **RUC hardcodeado**: < 100ms
- **APIs externas**: < 5s
- **Scraping OSCE**: < 30s
- **Consolidación completa**: < 45s
- **Browser timeout**: 30s
- **Network timeout**: 10s

### Similitud de Nombres

- **Umbral matching**: 0.7
- **Casos típicos**:
  - "JUAN CARLOS PEREZ" vs "JUAN PEREZ" → ≥ 0.8
  - "SANTA ROSA SCRL" vs "SANTA ROSA S.C.R.L." → ≥ 0.9

## 🔧 Configuración Jest

El archivo `jest.config.js` incluye:

- **Timeout**: 60s para pruebas de scraping
- **Cobertura**: Configurada para el archivo principal
- **Proyectos**: Separados por tipo de prueba
- **Setup**: Configuración global y limpieza

## 🧩 Datos de Prueba

### RUCs Válidos

- `20160669234` - SANTA ROSA SCRL (hardcodeado)
- `20100070970` - Banco de Crédito del Perú
- `20131312955` - Sodimac Perú

### RUCs Inválidos

- `12345678901` - Dígito verificador incorrecto
- `123456789` - Formato incorrecto (9 dígitos)
- `2016066923a` - Contiene letras

### Estructura de Respuesta Esperada

```json
{
  "success": true,
  "data": {
    "ruc": "20160669234",
    "razon_social": "SANTA ROSA SCRL",
    "contacto": {
      "telefono": "074-123456",
      "email": "contacto@santarosa.com",
      "direccion": "AV. PRINCIPAL 123, LAMBAYEQUE",
      "domicilio_fiscal": "PROLONGACION TACNA NRO. 408 LAMBAYEQUE - LAMBAYEQUE - LAMBAYEQUE",
      "ciudad": "LAMBAYEQUE",
      "departamento": "LAMBAYEQUE"
    },
    "miembros": [...],
    "especialidades": ["E28-2", "E28-1"],
    "registro": {
      "sunat": { "estado": "ACTIVO" },
      "osce": { "estado_registro": "HABILITADO" }
    },
    "fuentes_consultadas": ["SUNAT", "OSCE"],
    "consolidacion_exitosa": true,
    "timestamp": "2024-01-01T00:00:00.000Z"
  }
}
```

## 🚨 Validaciones Críticas

### 1. Validación de RUC

```javascript
// Formato correcto (11 dígitos)
expect(/^\d{11}$/.test(ruc)).toBe(true);

// Dígito verificador válido
expect(validarDigitoVerificadorRUC(ruc)).toBe(true);
```

### 2. Estructura JSON

```javascript
// Campos requeridos en consolidación
const requiredFields = [
  '.success',
  '.data.ruc',
  '.data.razon_social',
  '.data.contacto',
  '.data.miembros',
  '.data.especialidades',
  '.data.registro.sunat',
  '.data.registro.osce',
  '.data.fuentes_consultadas',
  '.data.consolidacion_exitosa',
  '.timestamp'
];
```

### 3. Deduplicación de Miembros

```javascript
// Matching por DNI exacto
expect(miembro.fuentes_detalle.matching).toBe('DNI');

// Matching por similitud de nombres
expect(miembro.fuentes_detalle.matching).toContain('NOMBRE');

// Combinación de cargos
expect(miembro.cargo).toBe('DIRECTOR TECNICO / GERENTE GENERAL');
```

## 🐛 Debugging y Troubleshooting

### Logs de Desarrollo

```bash
# Ver logs detallados durante testing
DEBUG=* npm test

# Solo logs de consolidación
DEBUG=consolidacion npm test
```

### Errores Comunes

1. **Timeout de pruebas**: Aumentar timeout en jest.config.js
2. **Browser no encontrado**: Verificar PLAYWRIGHT_BROWSERS_PATH
3. **APIs externas fallan**: Usar mocks en lugar de llamadas reales
4. **JSON inválido**: Verificar escape de caracteres especiales

### Variables de Entorno para Testing

```bash
NODE_ENV=test
PORT=3001
TESTING=true
TEST_TIMEOUT=60000
BROWSER_TIMEOUT=30000
```

## 📈 Monitoreo y Reportes

### Reporte de Cobertura

```bash
npm run test:coverage
# Ver reporte en: coverage/lcov-report/index.html
```

### Métricas de Performance

```bash
# El script de pruebas rápidas incluye métricas de tiempo
./scripts/test-quick.sh
```

### CI/CD Integration

Para integrar con CI/CD, usar:

```yaml
test:
  script:
    - npm install
    - npm run test:coverage
    - npm run test:quick
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage/cobertura-coverage.xml
```

## ✅ Checklist de Validación

Antes de desplegar, verificar:

- [ ] RUC 20160669234 retorna "SANTA ROSA SCRL"
- [ ] Consolidación combina datos SUNAT + OSCE
- [ ] Deduplicación funciona por DNI y similitud
- [ ] Manejo correcto cuando una fuente falla
- [ ] Tiempos de respuesta dentro de umbrales
- [ ] Estructura JSON completa y válida
- [ ] Endpoints responden correctamente
- [ ] Cobertura de código ≥ 75%
- [ ] Todas las pruebas pasan
- [ ] Script de pruebas rápidas exitoso

---

**Nota**: Este sistema de testing asegura la calidad y confiabilidad del sistema de consolidación SUNAT + OSCE, validando tanto casos exitosos como escenarios de error.