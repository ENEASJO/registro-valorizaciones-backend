# API Reference - Sistema de Notificaciones WhatsApp

## Descripción General

La API del Sistema de Notificaciones WhatsApp proporciona endpoints completos para gestionar notificaciones automáticas, contactos, plantillas y métricas. Está construida con **FastAPI** y sigue estándares REST con documentación OpenAPI automática.

**Base URL**: `https://api.valoraciones.empresa.com`  
**Versión**: `v1.0`  
**Formato**: `JSON`  
**Autenticación**: `JWT Bearer Token` + `API Keys`

## Autenticación

### JWT Bearer Token
```bash
# Obtener token (endpoint no implementado en este ejemplo)
curl -X POST "/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "password"}'

# Usar token en requests
curl -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

### API Keys (Recomendado para Integración)
```bash
# Header de autenticación
curl -H "X-API-Key: wn_api_prod_12345abcdef..."

# Query parameter (alternativo)
curl "https://api.valoraciones.com/api/notifications?api_key=wn_api_prod_12345..."
```

## Endpoints Principales

### 📡 Health Check y Status

#### `GET /health`
Verificar estado del sistema y sus componentes.

**Request:**
```bash
curl -X GET "https://api.valoraciones.com/health"
```

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-01-23T12:00:00.000000",
  "components": {
    "database": {
      "status": "connected",
      "response_time_ms": 15.2
    },
    "whatsapp_api": {
      "status": "healthy",
      "rate_limit_remaining": 950
    },
    "scheduler": {
      "status": "running",
      "active_jobs": 3
    },
    "cache": {
      "status": "connected",
      "hit_rate": 0.85
    }
  }
}
```

**Estados posibles:**
- `healthy`: Todos los componentes funcionando
- `degraded`: Algunos componentes con problemas menores
- `unhealthy`: Componentes críticos fallando

---

### 📨 Gestión de Notificaciones

#### `POST /api/notifications`
Crear nueva notificación WhatsApp.

**Request:**
```bash
curl -X POST "https://api.valoraciones.com/api/notifications" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "valorizacion_id": 123,
    "plantilla_id": 1,
    "contacto_id": 456,
    "evento_trigger": "APROBADA",
    "estado_actual": "APROBADA",
    "estado_anterior": "EN_REVISION",
    "tipo_envio": "INMEDIATO",
    "variables_extra": {
      "monto_total": "50000.00",
      "observaciones": "Valorización aprobada sin observaciones"
    }
  }'
```

**Request Schema:**
```typescript
{
  valorizacion_id: number,           // ID de valorización (requerido)
  plantilla_id?: number,             // ID plantilla específica (opcional)
  contacto_id?: number,              // ID contacto específico (opcional)  
  evento_trigger: "RECIBIDA" | "EN_REVISION" | "OBSERVADA" | "APROBADA" | "RECHAZADA",
  estado_actual: string,             // Estado actual de valorización
  estado_anterior?: string,          // Estado anterior (opcional)
  tipo_envio: "INMEDIATO" | "PROGRAMADO",
  variables_extra?: {                // Variables adicionales para plantilla
    [key: string]: any
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Notificación creada exitosamente",
  "data": {
    "notificaciones_creadas": 2,
    "notificaciones": [
      {
        "id": 789,
        "codigo_notificacion": "WA-20250123-ABC123",
        "contacto_nombre": "Juan Pérez",
        "contacto_telefono": "51987654321",
        "mensaje": "✅ Valorización #VAL-000123 APROBADA - Obra Central...",
        "estado": "PENDIENTE",
        "fecha_programada": "2025-01-23T14:30:00"
      }
    ]
  }
}
```

#### `GET /api/notifications`
Listar notificaciones con filtros y paginación.

**Request:**
```bash
curl -G "https://api.valoraciones.com/api/notifications" \
  -H "Authorization: Bearer $TOKEN" \
  -d "pagina=1" \
  -d "limite=20" \
  -d "estado=ENVIADA" \
  -d "evento=APROBADA" \
  -d "valorizacion_id=123" \
  -d "fecha_desde=2025-01-01" \
  -d "fecha_hasta=2025-01-31"
```

**Query Parameters:**
- `pagina` (int): Número de página (default: 1)
- `limite` (int): Elementos por página (1-100, default: 20)
- `estado` (string): Filtrar por estado
- `evento` (string): Filtrar por evento trigger
- `valorizacion_id` (int): Filtrar por ID de valorización
- `fecha_desde` (date): Fecha desde (YYYY-MM-DD)
- `fecha_hasta` (date): Fecha hasta (YYYY-MM-DD)

**Response:**
```json
{
  "notificaciones": [
    {
      "id": 789,
      "codigo_notificacion": "WA-20250123-ABC123",
      "valorizacion_id": 123,
      "evento_trigger": "APROBADA",
      "estado_actual": "APROBADA",
      "estado_anterior": "EN_REVISION",
      "mensaje_renderizado": "✅ Valorización aprobada...",
      "estado": "ENVIADA",
      "fecha_envio": "2025-01-23T14:30:00",
      "fecha_entrega": "2025-01-23T14:30:15",
      "fecha_lectura": "2025-01-23T14:35:20",
      "contacto_nombre": "Juan Pérez",
      "contacto_telefono": "51987654321",
      "plantilla_nombre": "Valorización Aprobada - Contratista",
      "intentos_envio": 1,
      "prioridad": 3,
      "created_at": "2025-01-23T14:25:00"
    }
  ],
  "total": 45,
  "pagina": 1,
  "limite": 20,
  "total_paginas": 3
}
```

#### `PUT /api/notifications/{notification_id}/status`
Actualizar estado de notificación manualmente.

**Request:**
```bash
curl -X PUT "https://api.valoraciones.com/api/notifications/789/status" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "nuevo_estado": "ENVIADA",
    "motivo": "Enviado manualmente por administrador"
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "Estado actualizado exitosamente",
  "data": {
    "id": 789,
    "estado_anterior": "PENDIENTE",
    "estado_nuevo": "ENVIADA",
    "fecha_cambio": "2025-01-23T14:30:00"
  }
}
```

#### `POST /api/notifications/bulk`
Crear múltiples notificaciones en batch.

**Request:**
```bash
curl -X POST "https://api.valoraciones.com/api/notifications/bulk" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "valorizacion_ids": [123, 124, 125],
    "evento_trigger": "RECIBIDA",
    "estado_actual": "PRESENTADA",
    "variables_comunes": {
      "fecha_recepcion": "2025-01-23"
    }
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "Notificaciones bulk creadas exitosamente",
  "data": {
    "procesadas": 3,
    "exitosas": 3,
    "fallidas": 0,
    "notificaciones_creadas": 6,
    "detalle": [
      {"valorizacion_id": 123, "notificaciones": 2, "status": "success"},
      {"valorizacion_id": 124, "notificaciones": 2, "status": "success"},
      {"valorizacion_id": 125, "notificaciones": 2, "status": "success"}
    ]
  }
}
```

---

### 📊 Métricas y Estadísticas

#### `GET /api/notifications/metrics`
Obtener métricas consolidadas de notificaciones.

**Request:**
```bash
curl -G "https://api.valoraciones.com/api/notifications/metrics" \
  -H "Authorization: Bearer $TOKEN" \
  -d "fecha_inicio=2025-01-01" \
  -d "fecha_fin=2025-01-31" \
  -d "include_trends=true"
```

**Response:**
```json
{
  "fecha": "2025-01-23",
  "periodo": {
    "inicio": "2025-01-01T00:00:00",
    "fin": "2025-01-31T23:59:59"
  },
  "total_notificaciones": 1250,
  "total_enviadas": 1180,
  "total_entregadas": 1150,
  "total_leidas": 920,
  "total_errores": 35,
  "tasa_exito_porcentaje": 94.4,
  "tasa_entrega_porcentaje": 97.5,
  "tasa_lectura_porcentaje": 80.0,
  "por_evento": {
    "APROBADA": 450,
    "OBSERVADA": 320,
    "RECIBIDA": 280,
    "EN_REVISION": 150,
    "RECHAZADA": 50
  },
  "por_estado": {
    "ENVIADA": 1180,
    "ENTREGADA": 1150,
    "LEIDA": 920,
    "ERROR": 35,
    "PENDIENTE": 35
  },
  "tendencias": {
    "envios_por_dia": [45, 52, 38, 67, 44],
    "tasa_lectura_promedio": 78.5,
    "tiempo_respuesta_promedio_minutos": 2.3
  }
}
```

#### `GET /api/notifications/metrics/daily`
Obtener métricas diarias detalladas.

**Request:**
```bash
curl -G "https://api.valoraciones.com/api/notifications/metrics/daily" \
  -H "Authorization: Bearer $TOKEN" \
  -d "fecha_inicio=2025-01-01" \
  -d "fecha_fin=2025-01-31"
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "fecha": "2025-01-23",
      "total_enviadas": 52,
      "total_entregadas": 48,
      "total_leidas": 38,
      "total_errores": 2,
      "tasa_exito_porcentaje": 96.15,
      "tasa_error_porcentaje": 3.85,
      "tiempo_promedio_envio_minutos": 1.8,
      "por_evento": {
        "recibidas": 15,
        "en_revision": 8,
        "observadas": 12,
        "aprobadas": 14,
        "rechazadas": 3
      }
    }
  ]
}
```

#### `GET /api/notifications/metrics/empresa/{empresa_id}`
Métricas específicas por empresa.

**Request:**
```bash
curl -G "https://api.valoraciones.com/api/notifications/metrics/empresa/123" \
  -H "Authorization: Bearer $TOKEN" \
  -d "fecha_inicio=2025-01-01"
```

**Response:**
```json
{
  "empresa_id": 123,
  "empresa_nombre": "CONSTRUCTORA ABC S.A.C.",
  "periodo": {
    "inicio": "2025-01-01T00:00:00",
    "fin": "2025-01-23T23:59:59"
  },
  "total_notificaciones": 85,
  "total_valorizaciones": 12,
  "promedio_notificaciones_por_valorizacion": 7.1,
  "tasa_lectura_porcentaje": 92.5,
  "tiempo_promedio_lectura_minutos": 15.3,
  "contactos_activos": 3,
  "eventos_mas_frecuentes": [
    {"evento": "APROBADA", "cantidad": 28},
    {"evento": "OBSERVADA", "cantidad": 22},
    {"evento": "RECIBIDA", "cantidad": 18}
  ],
  "performance": {
    "tasa_entrega": 98.8,
    "tasa_respuesta": 85.2,
    "satisfaccion_estimada": "ALTA"
  }
}
```

---

### 🧪 Testing y Administración

#### `POST /api/notifications/test`
Enviar mensaje de prueba para validar configuración.

**Request:**
```bash
curl -X POST "https://api.valoraciones.com/api/notifications/test" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "51987654321",
    "message": "Mensaje de prueba del sistema de notificaciones",
    "include_timestamp": true
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "Mensaje de prueba enviado exitosamente",
  "data": {
    "phone_number": "51987654321",
    "formatted_phone": "51987654321",
    "message_id": "wamid.HBgLNTE5ODc2NTQzMjEVAgARGBI2...",
    "status": "sent",
    "whatsapp_response": {
      "messaging_product": "whatsapp",
      "contacts": [...],
      "messages": [...]
    },
    "sent_at": "2025-01-23T14:30:00"
  }
}
```

#### `POST /api/notifications/process-pending`
Forzar procesamiento de notificaciones pendientes.

**Request:**
```bash
curl -X POST "https://api.valoraciones.com/api/notifications/process-pending?limit=50" \
  -H "Authorization: Bearer $TOKEN"
```

**Response:**
```json
{
  "success": true,
  "message": "Procesamiento completado: 23 notificaciones",
  "data": {
    "processed": 23,
    "sent": 20,
    "failed": 2,
    "deferred": 1,
    "processing_time_seconds": 15.7,
    "details": {
      "successful_notifications": [789, 790, 791],
      "failed_notifications": [
        {"id": 792, "error": "Rate limit exceeded"},
        {"id": 793, "error": "Invalid phone number"}
      ],
      "deferred_notifications": [794]
    }
  }
}
```

#### `GET /api/notifications/scheduler/status`
Estado del scheduler de background jobs.

**Response:**
```json
{
  "success": true,
  "data": {
    "scheduler_running": true,
    "last_execution": "2025-01-23T14:25:00",
    "next_execution": "2025-01-23T14:30:00",
    "jobs": {
      "pending_notifications": {
        "active": true,
        "interval_seconds": 60,
        "last_run": "2025-01-23T14:25:00",
        "success_count": 145,
        "error_count": 3
      },
      "metrics_calculation": {
        "active": true,
        "interval_seconds": 3600,
        "last_run": "2025-01-23T14:00:00",
        "success_count": 24,
        "error_count": 0
      }
    },
    "system_load": {
      "cpu_percent": 15.3,
      "memory_percent": 42.1,
      "queue_size": 12
    }
  }
}
```

---

### 👥 Gestión de Contactos

#### `GET /api/notifications/contacts`
Listar contactos WhatsApp configurados.

**Request:**
```bash
curl -G "https://api.valoraciones.com/api/notifications/contacts" \
  -H "Authorization: Bearer $TOKEN" \
  -d "activo=true" \
  -d "tipo=CONTRATISTA" \
  -d "empresa_id=123"
```

**Response:**
```json
[
  {
    "id": 456,
    "empresa_id": 123,
    "empresa_razon_social": "CONSTRUCTORA ABC S.A.C.",
    "nombre": "Juan Pérez",
    "cargo": "Gerente de Proyecto",
    "telefono": "51987654321",
    "email": "juan.perez@constructora.com",
    "tipo_contacto": "CONTRATISTA",
    "es_principal": true,
    "recibe_notificaciones": true,
    "eventos_suscritos": ["RECIBIDA", "OBSERVADA", "APROBADA", "RECHAZADA"],
    "horario_configuracion_id": 1,
    "activo": true,
    "verificado": true,
    "created_at": "2025-01-15T10:00:00",
    "estadisticas": {
      "notificaciones_recibidas": 25,
      "notificaciones_leidas": 22,
      "tasa_lectura": 88.0,
      "ultima_actividad": "2025-01-23T13:45:00"
    }
  }
]
```

#### `POST /api/notifications/contacts`
Crear nuevo contacto WhatsApp.

**Request:**
```bash
curl -X POST "https://api.valoraciones.com/api/notifications/contacts" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "empresa_id": 123,
    "nombre": "María García",
    "cargo": "Coordinadora Técnica",
    "telefono": "987654321",
    "email": "maria.garcia@constructora.com",
    "tipo_contacto": "CONTRATISTA",
    "es_principal": false,
    "eventos_suscritos": ["OBSERVADA", "RECHAZADA"],
    "horario_configuracion_id": 1
  }'
```

#### `PUT /api/notifications/contacts/{contact_id}`
Actualizar contacto existente.

**Request:**
```bash
curl -X PUT "https://api.valoraciones.com/api/notifications/contacts/456" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "telefono": "51976543210",
    "eventos_suscritos": ["RECIBIDA", "OBSERVADA", "APROBADA"],
    "activo": true
  }'
```

#### `DELETE /api/notifications/contacts/{contact_id}`
Desactivar contacto.

**Request:**
```bash
curl -X DELETE "https://api.valoraciones.com/api/notifications/contacts/456" \
  -H "Authorization: Bearer $TOKEN"
```

---

### 📝 Gestión de Plantillas

#### `GET /api/notifications/templates`
Listar plantillas de mensajes.

**Request:**
```bash
curl -G "https://api.valoraciones.com/api/notifications/templates" \
  -H "Authorization: Bearer $TOKEN" \
  -d "activo=true" \
  -d "evento=APROBADA"
```

**Response:**
```json
[
  {
    "id": 1,
    "codigo": "VAL_APROBADA_CONTRATISTA",
    "nombre": "Valorización Aprobada - Contratista",
    "descripcion": "Notifica la aprobación de valorización al contratista",
    "evento_trigger": "APROBADA",
    "estado_valorizacion": "APROBADA",
    "tipo_destinatario": "CONTRATISTA",
    "asunto": "✅ Valorización #{valorizacion_numero} APROBADA - {obra_nombre}",
    "mensaje_texto": "Felicitaciones {empresa_razon_social}...",
    "variables_disponibles": [
      "obra_nombre", "empresa_razon_social", "valorizacion_numero",
      "valorizacion_periodo", "estado_actual", "fecha_cambio", "monto_total"
    ],
    "es_inmediato": true,
    "prioridad": 3,
    "activo": true,
    "created_at": "2025-01-15T10:00:00",
    "estadisticas": {
      "veces_utilizada": 127,
      "tasa_entrega": 95.3,
      "tasa_lectura": 82.1
    }
  }
]
```

#### `POST /api/notifications/templates`
Crear nueva plantilla de mensaje.

**Request:**
```bash
curl -X POST "https://api.valoraciones.com/api/notifications/templates" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "codigo": "CUSTOM_TEMPLATE_001",
    "nombre": "Plantilla Personalizada",
    "descripcion": "Plantilla para casos especiales",
    "evento_trigger": "OBSERVADA",
    "estado_valorizacion": "OBSERVADA",
    "tipo_destinatario": "CONTRATISTA",
    "mensaje_texto": "Estimado {empresa_razon_social}...",
    "prioridad": 2,
    "activo": true
  }'
```

#### `GET /api/notifications/templates/{template_id}/preview`
Vista previa de plantilla con variables.

**Request:**
```bash
curl -X POST "https://api.valoraciones.com/api/notifications/templates/1/preview" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "variables": {
      "empresa_razon_social": "CONSTRUCTORA TEST S.A.C.",
      "valorizacion_numero": "VAL-000123",
      "obra_nombre": "Construcción Edificio Central",
      "monto_total": "50,000.00",
      "fecha_cambio": "23/01/2025 14:30"
    }
  }'
```

**Response:**
```json
{
  "success": true,
  "data": {
    "asunto_renderizado": "✅ Valorización #VAL-000123 APROBADA - Construcción Edificio Central",
    "mensaje_renderizado": "Felicitaciones CONSTRUCTORA TEST S.A.C.,\n\nSu valorización #VAL-000123 ha sido APROBADA.\n\nMonto aprobado: S/ 50,000.00\nFecha: 23/01/2025 14:30\n\nSaludos cordiales,\nSistema de Valorizaciones",
    "longitud_caracteres": 187,
    "variables_utilizadas": ["empresa_razon_social", "valorizacion_numero", "obra_nombre", "monto_total", "fecha_cambio"],
    "variables_faltantes": [],
    "validacion": {
      "valida": true,
      "longitud_ok": true,
      "variables_ok": true
    }
  }
}
```

---

### 📞 Webhooks WhatsApp

#### `GET /api/notifications/webhook`
Endpoint de verificación de webhook (Meta).

**Usado por Meta para verificar el webhook durante configuración inicial.**

#### `POST /api/notifications/webhook`
Endpoint receptor de webhooks de WhatsApp.

**Payload típico de WhatsApp:**
```json
{
  "entry": [
    {
      "id": "PHONE_NUMBER_ID",
      "changes": [
        {
          "value": {
            "messaging_product": "whatsapp",
            "metadata": {
              "display_phone_number": "51987654321",
              "phone_number_id": "PHONE_NUMBER_ID"
            },
            "statuses": [
              {
                "id": "wamid.HBgLNTE5ODc2NTQzMjEVAgARGBI2...",
                "status": "delivered",
                "timestamp": "1674480000",
                "recipient_id": "51987654321",
                "conversation": {
                  "id": "CONVERSATION_ID",
                  "expiration_timestamp": "1674566400"
                },
                "pricing": {
                  "billable": true,
                  "pricing_model": "CBP",
                  "category": "business_initiated"
                }
              }
            ]
          },
          "field": "messages"
        }
      ]
    }
  ]
}
```

**Response:**
```json
{
  "status": "processed",
  "events": 1
}
```

---

## Códigos de Error

### Errores HTTP Estándar

| Código | Descripción | Causa Común |
|--------|-------------|-------------|
| `400` | Bad Request | Parámetros inválidos, JSON malformado |
| `401` | Unauthorized | Token JWT inválido o expirado |
| `403` | Forbidden | Sin permisos para recurso |
| `404` | Not Found | Recurso no encontrado |
| `422` | Unprocessable Entity | Validación de datos falló |
| `429` | Too Many Requests | Rate limit excedido |
| `500` | Internal Server Error | Error interno del servidor |

### Errores de Negocio Específicos

```json
{
  "success": false,
  "error": {
    "code": "WHATSAPP_ERROR",
    "message": "Error enviando mensaje WhatsApp",
    "details": {
      "whatsapp_error_code": 131026,
      "whatsapp_message": "Message undeliverable",
      "retry_after_seconds": 30
    },
    "timestamp": "2025-01-23T14:30:00",
    "request_id": "req_abc123"
  }
}
```

**Códigos de Error Específicos:**

- `VALIDATION_ERROR`: Error en validación de datos
- `WHATSAPP_ERROR`: Error en API de WhatsApp
- `NOTIFICATION_ERROR`: Error en procesamiento de notificación
- `DATABASE_ERROR`: Error en base de datos
- `RATE_LIMIT_EXCEEDED`: Límite de requests excedido
- `TEMPLATE_NOT_FOUND`: Plantilla no encontrada
- `CONTACT_NOT_FOUND`: Contacto no encontrado
- `PHONE_INVALID`: Número telefónico inválido

## Rate Limiting

### Límites por Endpoint

| Endpoint | Límite | Ventana |
|----------|---------|---------|
| `GET /api/notifications` | 100 req/min | Por usuario |
| `POST /api/notifications` | 30 req/min | Por usuario |
| `GET /api/notifications/metrics` | 60 req/min | Por usuario |
| `POST /api/notifications/test` | 10 req/min | Por usuario |
| `POST /api/notifications/bulk` | 5 req/min | Por usuario |

### Headers de Rate Limiting

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1674480060
X-RateLimit-Policy: 100;w=60
```

### Response cuando se excede límite

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded",
    "retry_after_seconds": 45
  }
}
```

## Paginación

### Cursor-based Pagination (Recomendado)

**Request:**
```bash
curl -G "https://api.valoraciones.com/api/notifications" \
  -d "limit=20" \
  -d "cursor=eyJpZCI6Nzg5LCJ0aW1lc3RhbXAiOiIyMDI1LTAxLTIzVDE0OjMwOjAwIn0="
```

**Response:**
```json
{
  "data": [...],
  "pagination": {
    "limit": 20,
    "has_more": true,
    "next_cursor": "eyJpZCI6ODA5LCJ0aW1lc3RhbXAiOiIyMDI1LTAxLTIzVDE1OjAwOjAwIn0=",
    "prev_cursor": "eyJpZCI6NzY5LCJ0aW1lc3RhbXAiOiIyMDI1LTAxLTIzVDE0OjAwOjAwIn0="
  }
}
```

### Offset-based Pagination (Alternativo)

**Request:**
```bash
curl -G "https://api.valoraciones.com/api/notifications" \
  -d "pagina=2" \
  -d "limite=20"
```

## Webhooks Salientes (Opcional)

### Configurar Webhook de Eventos

```bash
curl -X POST "https://api.valoraciones.com/api/webhooks" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://tu-sistema.com/webhooks/whatsapp-events",
    "events": ["notification.sent", "notification.delivered", "notification.read"],
    "secret": "tu-secret-para-validacion"
  }'
```

### Payload de Webhook Saliente

```json
{
  "event": "notification.delivered",
  "timestamp": "2025-01-23T14:30:00",
  "data": {
    "notification_id": 789,
    "valorizacion_id": 123,
    "evento_trigger": "APROBADA",
    "contacto_id": 456,
    "whatsapp_message_id": "wamid.HBgLNTE5ODc2NTQzMjEV...",
    "status": "delivered",
    "delivered_at": "2025-01-23T14:30:15"
  },
  "signature": "sha256=abc123def456..."
}
```

## SDKs y Bibliotecas Cliente

### JavaScript/TypeScript
```typescript
import { WhatsAppNotificationsClient } from '@empresa/whatsapp-notifications-sdk';

const client = new WhatsAppNotificationsClient({
  apiUrl: 'https://api.valoraciones.com',
  apiKey: 'wn_api_prod_12345...',
});

// Crear notificación
const notification = await client.notifications.create({
  valorizacion_id: 123,
  evento_trigger: 'APROBADA',
  estado_actual: 'APROBADA',
});

// Obtener métricas
const metrics = await client.metrics.get({
  fecha_inicio: '2025-01-01',
  fecha_fin: '2025-01-31'
});
```

### Python
```python
from whatsapp_notifications_sdk import WhatsAppNotificationsClient

client = WhatsAppNotificationsClient(
    api_url='https://api.valoraciones.com',
    api_key='wn_api_prod_12345...'
)

# Crear notificación
notification = await client.notifications.create(
    valorizacion_id=123,
    evento_trigger='APROBADA',
    estado_actual='APROBADA'
)

# Obtener métricas
metrics = await client.metrics.get(
    fecha_inicio='2025-01-01',
    fecha_fin='2025-01-31'
)
```

### cURL Examples Collection

Colección completa de ejemplos en cURL para testing:

```bash
#!/bin/bash
# WhatsApp Notifications API - Test Suite

# Configuración
API_URL="https://api.valoraciones.com"
API_KEY="wn_api_prod_12345..."
HEADERS="Authorization: Bearer $API_KEY"

# 1. Health Check
echo "🏥 Health Check..."
curl -s "$API_URL/health" | jq

# 2. Crear notificación
echo "📨 Crear notificación..."
curl -s -X POST "$API_URL/api/notifications" \
  -H "$HEADERS" \
  -H "Content-Type: application/json" \
  -d '{
    "valorizacion_id": 123,
    "evento_trigger": "APROBADA",
    "estado_actual": "APROBADA",
    "variables_extra": {"monto_total": "50000.00"}
  }' | jq

# 3. Listar notificaciones
echo "📋 Listar notificaciones..."
curl -s -G "$API_URL/api/notifications" \
  -H "$HEADERS" \
  -d "limite=5" \
  -d "estado=ENVIADA" | jq

# 4. Obtener métricas
echo "📊 Obtener métricas..."
curl -s -G "$API_URL/api/notifications/metrics" \
  -H "$HEADERS" \
  -d "fecha_inicio=2025-01-01" | jq

# 5. Mensaje de prueba
echo "🧪 Enviar mensaje de prueba..."
curl -s -X POST "$API_URL/api/notifications/test" \
  -H "$HEADERS" \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "51987654321",
    "message": "Test message from API"
  }' | jq
```

## Documentación Interactiva

### Swagger UI
**URL**: `https://api.valoraciones.com/docs`

Interface web interactiva con:
- Explorador de endpoints
- Esquemas de datos
- Testing en vivo
- Ejemplos de código
- Autenticación integrada

### ReDoc
**URL**: `https://api.valoraciones.com/redoc`

Documentación estática optimizada para lectura con:
- Navegación lateral
- Búsqueda integrada
- Ejemplos detallados
- Schemas expandidos

### OpenAPI Specification
**URL**: `https://api.valoraciones.com/openapi.json`

Especificación OpenAPI 3.0 completa para generar clientes automáticamente.

## Soporte y Recursos

### Endpoints de Soporte
- **Status Page**: `https://status.valoraciones.com`
- **Documentation**: `https://docs.valoraciones.com`
- **GitHub Issues**: `https://github.com/empresa/whatsapp-notifications/issues`

### Contacto Técnico
- **Email**: api-support@valoraciones.com
- **Slack**: #whatsapp-notifications
- **Horas de Soporte**: L-V 9:00-18:00 (Lima)

### Changelog y Versioning
- **Changelog**: `https://api.valoraciones.com/changelog`
- **API Version**: Versionado semántico (v1.0, v1.1, v2.0)
- **Backward Compatibility**: Garantizada por 12 meses

---

**API Reference v1.0** - Sistema de Notificaciones WhatsApp  
*Última actualización: 23 de Enero 2025*