# Ejemplos de API - Sistema de Generación Automática de Códigos

## 🚀 Crear Obra (Código Automático)

### Endpoint
```http
POST /obras/
Content-Type: application/json
```

### ✅ Ejemplo 1: Centro de Salud
```json
{
    "nombre": "Construcción de Centro de Salud Las Flores",
    "descripcion": "Centro de salud tipo I-3 con capacidad para 50 pacientes diarios",
    "empresa_id": "35582cb8-ab04-474e-926c-5b52cc2f9889",
    "cliente": "Ministerio de Salud",
    "ubicacion": "Av. Las Flores 123, Distrito San Juan",
    "distrito": "San Juan",
    "provincia": "Lima",
    "departamento": "Lima",
    "tipo_obra": "Edificación - Salud",
    "modalidad_ejecucion": "CONTRATA",
    "sistema_contratacion": "SUMA_ALZADA",
    "monto_contractual": 750000.00,
    "fecha_inicio": "2025-03-01",
    "fecha_fin_contractual": "2025-12-31",
    "plazo_contractual": 305,
    "estado_obra": "PLANIFICADA"
}
```

### ✅ Ejemplo 2: Carretera Rural
```json
{
    "nombre": "Mejoramiento de Carretera Rural Norte",
    "descripcion": "Pavimentación de carretera rural tramo Km 0+000 - Km 15+000",
    "empresa_id": "a6be08c9-3037-4a18-a019-32c0cc5ca218",
    "cliente": "Gobierno Regional de Lima",
    "ubicacion": "Carretera Rural Norte KM 0+000",
    "distrito": "San Pedro",
    "provincia": "Lima",
    "departamento": "Lima",
    "tipo_obra": "Transporte - Carreteras",
    "modalidad_ejecucion": "CONTRATA",
    "sistema_contratacion": "PRECIOS_UNITARIOS",
    "monto_contractual": 1200000.00,
    "monto_adicionales": 150000.00,
    "fecha_inicio": "2025-02-15",
    "fecha_fin_contractual": "2025-11-30",
    "plazo_contractual": 288,
    "estado_obra": "EN_PROCESO"
}
```

### ✅ Ejemplo 3: Plaza Principal
```json
{
    "nombre": "Renovación de Plaza Principal",
    "descripcion": "Renovación integral con áreas verdes, bancas y iluminación LED",
    "empresa_id": "3df286aa-98b6-45dc-9039-f8591f2020f8",
    "cliente": "Municipalidad Distrital de San Juan",
    "ubicacion": "Plaza Principal S/N, Centro",
    "distrito": "San Juan",
    "provincia": "Lima",
    "departamento": "Lima",
    "tipo_obra": "Urbanización - Espacios Públicos",
    "modalidad_ejecucion": "ADMINISTRACION_DIRECTA",
    "sistema_contratacion": "SUMA_ALZADA",
    "monto_contractual": 350000.00,
    "fecha_inicio": "2025-01-30",
    "fecha_fin_contractual": "2025-06-30",
    "plazo_contractual": 151,
    "estado_obra": "PLANIFICADA"
}
```

## 📋 Respuesta Esperada

```json
{
    "success": true,
    "message": "Obra creada exitosamente",
    "data": {
        "id": "4e38fd68-e529-4620-bbd4-6c8036029556",
        "codigo": "OBR-001-2025-09271713",
        "nombre": "Construcción de Centro de Salud Las Flores",
        "empresa_id": "35582cb8-ab04-474e-926c-5b52cc2f9889",
        "empresa_nombre": "VIDA SANA ALEMANA SOCIEDAD ANONIMA CERRADA - VIDA SANA ALEMANA S.A.C.",
        "cliente": "Ministerio de Salud",
        "ubicacion": "Av. Las Flores 123, Distrito San Juan",
        "distrito": "San Juan", 
        "provincia": "Lima",
        "departamento": "Lima",
        "tipo_obra": "Edificación - Salud",
        "modalidad_ejecucion": "CONTRATA",
        "sistema_contratacion": "SUMA_ALZADA",
        "monto_contractual": 750000.00,
        "monto_adicionales": 0.00,
        "monto_total": 750000.00,
        "fecha_inicio": "2025-03-01",
        "fecha_fin_contractual": "2025-12-31",
        "plazo_contractual": 305,
        "estado_obra": "PLANIFICADA",
        "porcentaje_avance": 0.00,
        "activo": true,
        "created_at": "2025-09-27T17:13:08.932Z",
        "updated_at": "2025-09-27T17:13:08.932Z",
        "version": 1
    },
    "timestamp": "2025-09-27T17:13:08.932Z"
}
```

## 🔍 Consultar Obra por Código

### Endpoint
```http
GET /obras/codigo/{codigo}
```

### Ejemplo
```http
GET /obras/codigo/OBR-001-2025-09271713
```

## 📋 Listar Obras

### Endpoint
```http
GET /obras/?empresa_id={uuid}&estado=PLANIFICADA&limit=10&offset=0
```

### Ejemplos
```http
GET /obras/
GET /obras/?empresa_id=35582cb8-ab04-474e-926c-5b52cc2f9889
GET /obras/?estado=EN_PROCESO
GET /obras/?empresa_id=35582cb8-ab04-474e-926c-5b52cc2f9889&estado=PLANIFICADA
```

## 🧪 Usando curl

### Crear Obra
```bash
curl -X POST http://localhost:8000/obras/ \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "Construcción de Centro de Salud Las Flores",
    "descripcion": "Centro de salud tipo I-3 con capacidad para 50 pacientes diarios",
    "empresa_id": "35582cb8-ab04-474e-926c-5b52cc2f9889",
    "cliente": "Ministerio de Salud",
    "ubicacion": "Av. Las Flores 123",
    "distrito": "San Juan",
    "provincia": "Lima",
    "departamento": "Lima",
    "tipo_obra": "Edificación - Salud",
    "modalidad_ejecucion": "CONTRATA",
    "sistema_contratacion": "SUMA_ALZADA",
    "monto_contractual": 750000.00,
    "fecha_inicio": "2025-03-01",
    "estado_obra": "PLANIFICADA"
  }'
```

### Consultar Obra
```bash
curl -X GET http://localhost:8000/obras/codigo/OBR-001-2025-09271713
```

### Listar Obras
```bash
curl -X GET "http://localhost:8000/obras/?limit=5"
```

## ⚡ Usando PowerShell

### Crear Obra
```powershell
$body = @{
    nombre = "Construcción de Centro de Salud Las Flores"
    descripcion = "Centro de salud tipo I-3 con capacidad para 50 pacientes diarios"
    empresa_id = "35582cb8-ab04-474e-926c-5b52cc2f9889"
    cliente = "Ministerio de Salud"
    ubicacion = "Av. Las Flores 123"
    distrito = "San Juan"
    provincia = "Lima"
    departamento = "Lima"
    tipo_obra = "Edificación - Salud"
    modalidad_ejecucion = "CONTRATA"
    sistema_contratacion = "SUMA_ALZADA"
    monto_contractual = 750000.00
    fecha_inicio = "2025-03-01"
    estado_obra = "PLANIFICADA"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/obras/" -Method POST -Body $body -ContentType "application/json"
```

## 📊 Estados Válidos

```json
[
    "PLANIFICADA",
    "EN_PROCESO", 
    "PARALIZADA",
    "SUSPENDIDA",
    "TERMINADA",
    "LIQUIDADA",
    "CANCELADA"
]
```

## 🏗️ Modalidades de Ejecución

```json
[
    "ADMINISTRACION_DIRECTA",
    "CONTRATA",
    "CONCESION",
    "ASOCIACION_PUBLICO_PRIVADA"
]
```

## 💰 Sistemas de Contratación

```json
[
    "SUMA_ALZADA",
    "PRECIOS_UNITARIOS",
    "ESQUEMA_MIXTO",
    "COSTO_MAS_PORCENTAJE"
]
```

## ✨ Características del Sistema

- **🔄 Código Automático**: No necesitas enviar el campo `codigo` - se genera automáticamente
- **🆔 Formato Único**: `OBR-{EMPRESA}-{AÑO}-{SECUENCIA}`
- **🏢 Identificación de Empresa**: Número secuencial basado en orden de creación
- **📅 Timestamp**: Secuencia basada en fecha/hora para unicidad
- **✅ Sin Duplicados**: Sistema garantiza códigos únicos
- **🔍 Trazabilidad**: Códigos legibles con información útil

## 🎯 Notas Importantes

1. **Campo `codigo` NO requerido** - Se genera automáticamente
2. **`empresa_id` debe ser UUID válido** de empresa existente y activa
3. **Campos opcionales** - Solo `nombre` y `empresa_id` son obligatorios
4. **Montos calculados** - `monto_total` se calcula automáticamente
5. **Fechas formato ISO** - `"YYYY-MM-DD"`

---

**🚀 Sistema listo para usar - ¡Los códigos se generan automáticamente!** 🎉