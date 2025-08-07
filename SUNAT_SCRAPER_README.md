# Scraper SUNAT - Implementación Real

Este documento describe la implementación del scraper real para consultar RUC en SUNAT, reemplazando los datos mock anteriores.

## Descripción

El sistema ahora incluye:
- **Servidor Backend**: API Express que realiza scraping real de la página de SUNAT
- **Cliente Frontend**: Servicio actualizado que consume la API real
- **Fallback**: Sistema de respaldo con datos generados para desarrollo

## Arquitectura

```
Frontend (React) → Backend API (Express) → Scraper (Puppeteer) → SUNAT Website
                      ↓
               Datos reales extraídos
```

## Instalación y Configuración

### 1. Instalar Dependencias
```bash
npm install
```

### 2. Iniciar Servidor Backend
```bash
# Opción 1: Usando el script
./start-backend.sh

# Opción 2: Manual
cd server && node sunat-api.js
```

### 3. Iniciar Frontend
```bash
# En otra terminal
npm run dev
```

## Endpoints de la API

### POST /api/consultar-ruc
Consulta los datos de una empresa por RUC.

**Request:**
```json
{
  "ruc": "20123456789"
}
```

**Response (Éxito):**
```json
{
  "success": true,
  "data": {
    "ruc": "20123456789",
    "razon_social": "EMPRESA EJEMPLO S.A.C.",
    "nombre_comercial": "Empresa Ejemplo",
    "estado_contribuyente": "ACTIVO",
    "condicion_domicilio": "HABIDO",
    "distrito": "LIMA",
    "provincia": "LIMA",
    "departamento": "LIMA",
    "direccion_completa": "AV. EJEMPLO NRO. 123 LIMA - LIMA - LIMA",
    "representantes_legales": [
      {
        "tipo_documento": "DNI",
        "numero_documento": "12345678",
        "nombre_completo": "JUAN PEREZ GARCIA",
        "cargo": "GERENTE GENERAL",
        "vigente": true
      }
    ]
  }
}
```

**Response (Error):**
```json
{
  "success": false,
  "error": "No se encontraron datos para el RUC proporcionado"
}
```

### GET /health
Health check del servidor.

**Response:**
```json
{
  "status": "OK",
  "timestamp": "2025-01-XX..."
}
```

## Características del Scraper

### Robustez
- **Reintentos automáticos**: Hasta 3 intentos por consulta
- **Múltiples selectores**: Busca elementos con diferentes estrategias
- **Manejo de errores**: Captura y reporta errores específicos
- **Timeout configurado**: Evita consultas colgadas

### Optimización
- **Bloqueo de recursos**: No carga imágenes ni CSS innecesarios
- **User Agent real**: Evita detección de bot básica
- **Navegación eficiente**: Usa networkidle para mejor sincronización

### Seguridad
- **Validación de entrada**: Verifica formato de RUC
- **Límite de tiempo**: Timeout en operaciones largas
- **Limpieza de recursos**: Cierra navegador automáticamente

## Casos de Error Manejados

1. **RUC inválido**: Formato incorrecto o no empresarial
2. **RUC no encontrado**: No existe en SUNAT
3. **Timeout**: La página tarda mucho en responder
4. **Error de red**: Problemas de conectividad
5. **Página cambiada**: Estructura HTML modificada
6. **Bot bloqueado**: Detección anti-scraping

## Fallback y Desarrollo

Si el servidor backend no está disponible, el frontend automáticamente usa datos generados para no interrumpir el desarrollo.

## Uso desde el Frontend

El servicio se usa igual que antes:

```typescript
import { consultarRucSunat } from '../services/sunatService';

const resultado = await consultarRucSunat('20123456789');
if (resultado.success) {
  console.log(resultado.data.razon_social);
} else {
  console.error(resultado.error);
}
```

## Pruebas

### Probar API directamente:
```bash
curl -X POST http://localhost:3001/api/consultar-ruc \
  -H "Content-Type: application/json" \
  -d '{"ruc": "20123456789"}'
```

### Probar desde navegador:
1. Abrir http://localhost:5173 (Vite dev server)
2. Ir al módulo de empresas
3. Usar la funcionalidad de consulta RUC

## Monitoreo

El servidor muestra logs detallados:
- Consultas iniciadas
- Pasos del scraping
- Errores encontrados
- Datos extraídos

## Limitaciones Conocidas

1. **Dependiente de SUNAT**: Si cambian la estructura, requiere actualización
2. **Velocidad**: Más lento que una API oficial (2-5 segundos por consulta)
3. **Rate limiting**: SUNAT puede limitar consultas frecuentes
4. **CAPTCHA**: Si implementan protección adicional, requerirá ajustes

## Actualización del Código

### Archivos modificados:
- `/src/services/sunatService.ts`: Cliente actualizado
- `/server/sunat-api.js`: Nuevo servidor backend
- `/package.json`: Dependencias agregadas

### Archivos nuevos:
- `/server/package.json`: Configuración del servidor
- `/start-backend.sh`: Script de inicio

## Troubleshooting

### "Error de conexión al consultar SUNAT"
- Verificar que el servidor backend esté ejecutándose
- Comprobar puerto 3001 libre
- Revisar logs del servidor

### "No se encontraron datos"
- Verificar que el RUC sea válido
- Comprobar conectividad a SUNAT
- Revisar si SUNAT cambió su estructura

### "Timeout"
- Mejorar conexión a internet
- Aumentar timeout en el código
- Reintentar la consulta

### Scraping bloqueado
- Verificar user agent
- Agregar delay entre consultas
- Usar proxy si es necesario

## Mantenimiento

Para mantener el scraper funcionando:

1. **Monitorear cambios en SUNAT**: Revisar periódicamente si cambia la estructura
2. **Actualizar selectores**: Modificar si cambian los elementos HTML
3. **Ajustar configuración**: Timeouts, reintentos según necesidad
4. **Logs de error**: Revisar regularmente para detectar problemas

Este scraper proporciona una solución robusta y funcional para integrar datos reales de SUNAT en el sistema de valorización.