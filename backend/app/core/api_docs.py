"""
Configuración de documentación OpenAPI optimizada para la API de notificaciones WhatsApp
Incluye ejemplos completos, guías de uso y especificaciones técnicas
"""

from typing import Dict, List, Any
from fastapi.openapi.utils import get_openapi
from fastapi import FastAPI

# =====================================================================
# CONFIGURACIÓN DE DOCUMENTACIÓN
# =====================================================================

def get_custom_openapi(app: FastAPI) -> Dict[str, Any]:
    """Generar documentación OpenAPI personalizada y completa"""
    
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="API de Notificaciones WhatsApp - Sistema de Valorizaciones",
        version="2.0.0",
        description=get_api_description(),
        routes=app.routes,
        servers=get_api_servers()
    )
    
    # Agregar configuraciones adicionales
    openapi_schema["info"]["contact"] = get_contact_info()
    openapi_schema["info"]["license"] = get_license_info()
    openapi_schema["info"]["termsOfService"] = "https://empresa.com/terms"
    
    # Agregar componentes de seguridad
    openapi_schema["components"]["securitySchemes"] = get_security_schemes()
    
    # Agregar ejemplos globales
    openapi_schema["components"]["examples"] = get_global_examples()
    
    # Agregar tags con descripciones
    openapi_schema["tags"] = get_api_tags()
    
    # Configurar security global
    openapi_schema["security"] = [{"BearerAuth": []}, {"ApiKeyAuth": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

def get_api_description() -> str:
    """Descripción completa de la API"""
    return """
# API de Notificaciones WhatsApp - Sistema de Valorizaciones

API REST optimizada para el manejo de notificaciones automáticas de WhatsApp Business en el sistema de valorizaciones de construcción.

## 🚀 Características Principales

- **Alta Performance**: Response time < 200ms para consultas simples
- **Escalabilidad**: Soporte para 1000+ notificaciones concurrentes  
- **Rate Limiting**: Protección inteligente contra abuso
- **Caching Avanzado**: Cache multi-nivel con invalidación automática
- **Paginación Eficiente**: Cursor-based pagination para grandes datasets
- **Seguridad Robusta**: Autenticación JWT/API Key + headers de seguridad
- **Monitoring Completo**: Métricas, logs estructurados y health checks

## 🏗️ Arquitectura

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Cliente Web   │    │   API Gateway    │    │  WhatsApp API   │
│   Dashboard     │◄──►│  Rate Limiting   │◄──►│  Business       │
│   Mobile App    │    │  Authentication  │    │  Cloud API      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                    ┌──────────────────┐
                    │  Notifications   │
                    │  Processing      │
                    │  Service         │
                    └──────────────────┘
                                │
                    ┌──────────────────┐
                    │    Database      │
                    │   (Neon/PostgreSQL) │
                    └──────────────────┘
```

## 📊 Flujo de Notificaciones

1. **Trigger**: Cambio de estado en valorización
2. **Procesamiento**: Selección de plantillas y contactos
3. **Programación**: Queue con horarios laborables
4. **Envío**: WhatsApp Business API con retry automático
5. **Tracking**: Estados de entrega, lectura y errores
6. **Métricas**: Análisis de performance y tasas de éxito

## 🔐 Autenticación

Soporta dos métodos de autenticación:

### JWT Bearer Token
```bash
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

### API Key
```bash
Authorization: Bearer wn_api_key_12345...
```

## 📈 Rate Limiting

Límites por endpoint optimizados para uso real:

- **GET /api/notifications**: 100 req/min
- **POST /api/notifications**: 30 req/min
- **GET /api/notifications/metrics**: 60 req/min
- **POST /api/notifications/test**: 10 req/min
- **POST /api/notifications/bulk**: 5 req/min

## 🎯 Casos de Uso Principales

### 1. Notificación Automática
Cuando una valorización cambia de estado, el sistema automáticamente:
- Identifica contactos relevantes (contratista, coordinador)
- Selecciona plantilla de mensaje apropiada
- Programa envío en horario laboral
- Envía notificación y trackea estado

### 2. Notificaciones Masivas
Para cambios que afectan múltiples valorizaciones:
- Procesamiento en lotes optimizado
- Rate limiting inteligente
- Reporting detallado de resultados

### 3. Dashboard de Métricas
Monitoreo en tiempo real de:
- Tasas de envío y entrega
- Performance por evento/estado
- Tendencias y comparaciones
- Alertas de problemas

## 🔄 Estados de Notificación

```
PENDIENTE → PROGRAMADA → ENVIANDO → ENVIADA → ENTREGADA → LEIDA
    │           │           │          │          │
    └───────────┴───────────┴──────────┴──────────┴─────→ ERROR
```

## 📱 Webhooks de WhatsApp

El sistema recibe callbacks automáticos de WhatsApp para tracking de estados:
- Confirmación de entrega
- Confirmación de lectura  
- Notificación de errores
- Estados de mensaje

## 🚦 Health Checks

Monitoreo continuo de:
- Conectividad a base de datos
- Estado de WhatsApp API
- Scheduler de tareas
- Métricas de performance

## 📖 Guías de Integración

Ver secciones específicas en cada endpoint para:
- Ejemplos de código
- Casos de error comunes
- Best practices
- Troubleshooting

---
*Última actualización: Enero 2025 - v2.0.0*
"""

def get_api_servers() -> List[Dict[str, str]]:
    """Configuración de servidores de la API"""
    return [
        {
            "url": "https://api.valoraciones.empresa.com",
            "description": "Servidor de Producción"
        },
        {
            "url": "https://staging-api.valoraciones.empresa.com", 
            "description": "Servidor de Staging"
        },
        {
            "url": "http://localhost:8000",
            "description": "Desarrollo Local"
        }
    ]

def get_contact_info() -> Dict[str, str]:
    """Información de contacto"""
    return {
        "name": "Equipo de Desarrollo - Sistema de Valorizaciones",
        "email": "dev-team@empresa.com",
        "url": "https://docs.valoraciones.empresa.com"
    }

def get_license_info() -> Dict[str, str]:
    """Información de licencia"""
    return {
        "name": "Propietario - Empresa Constructora",
        "url": "https://empresa.com/license"
    }

def get_security_schemes() -> Dict[str, Any]:
    """Esquemas de seguridad para OpenAPI"""
    return {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Token JWT para autenticación de usuarios"
        },
        "ApiKeyAuth": {
            "type": "http", 
            "scheme": "bearer",
            "description": "API Key para integración de sistemas (formato: wn_xxxxx)"
        }
    }

def get_api_tags() -> List[Dict[str, Any]]:
    """Tags de la API con descripciones detalladas"""
    return [
        {
            "name": "Notificaciones WhatsApp",
            "description": """
            **Gestión completa de notificaciones automáticas**
            
            Endpoints principales para crear, listar y administrar notificaciones de WhatsApp.
            Incluye operaciones CRUD completas con filtros avanzados y paginación eficiente.
            
            ### Características:
            - ✅ Cursor-based pagination para grandes datasets
            - ✅ Filtros múltiples (estado, evento, fecha, empresa, contacto)
            - ✅ Operaciones bulk optimizadas  
            - ✅ Validación robusta de datos
            - ✅ Rate limiting por endpoint
            
            ### Flujo típico:
            1. `POST /notifications` - Crear notificación
            2. `GET /notifications` - Listar y monitorear
            3. `PUT /notifications/{id}/status` - Actualizar estado manual
            """,
            "externalDocs": {
                "description": "Guía completa de notificaciones",
                "url": "https://docs.valoraciones.empresa.com/notifications"
            }
        },
        {
            "name": "Métricas y Analytics", 
            "description": """
            **Dashboard de métricas y análisis de performance**
            
            Endpoints especializados para obtener estadísticas, tendencias y métricas
            de performance del sistema de notificaciones.
            
            ### Métricas disponibles:
            - 📊 Tasas de envío, entrega y lectura
            - 📈 Tendencias y comparaciones históricas
            - 🎯 Performance por evento/estado
            - ⏱️ Tiempos de respuesta y SLA
            - 🚨 Alertas y detección de problemas
            
            ### Casos de uso:
            - Dashboards ejecutivos
            - Monitoreo operacional
            - Análisis de efectividad
            - Alertas automáticas
            """,
            "externalDocs": {
                "description": "Guía de métricas y analytics",
                "url": "https://docs.valoraciones.empresa.com/metrics"
            }
        },
        {
            "name": "Health Check",
            "description": """
            **Monitoreo de salud del sistema**
            
            Endpoints para verificar el estado de salud de todos los componentes
            del sistema de notificaciones.
            
            ### Componentes monitoreados:
            - 🗄️ Base de datos (conectividad y performance)
            - 📱 WhatsApp Business API (disponibilidad)
            - ⚙️ Scheduler de tareas (estado de jobs)
            - 🔄 Cache y Redis (si está disponible)
            - 📈 Métricas del sistema
            
            ### Tipos de checks:
            - **Liveness**: Sistema operativo
            - **Readiness**: Listo para recibir tráfico  
            - **Deep**: Verificación completa de dependencias
            """,
            "externalDocs": {
                "description": "Guía de monitoreo",
                "url": "https://docs.valoraciones.empresa.com/monitoring"
            }
        },
        {
            "name": "Webhook",
            "description": """
            **Callbacks de WhatsApp Business API**
            
            Endpoints para recibir y procesar callbacks automáticos de WhatsApp
            sobre el estado de los mensajes enviados.
            
            ### Estados trackados:
            - ✅ **sent**: Mensaje enviado al servidor de WhatsApp
            - ✅ **delivered**: Mensaje entregado al dispositivo del usuario
            - ✅ **read**: Mensaje leído por el usuario
            - ❌ **failed**: Error en entrega o procesamiento
            
            ### Seguridad:
            - Verificación de firma HMAC-SHA256
            - Validación de timestamp (anti-replay)
            - Rate limiting específico para webhooks
            - Logs detallados para auditoría
            
            ### Configuración requerida:
            1. URL del webhook en WhatsApp Business
            2. Token de verificación compartido
            3. Configuración HTTPS con certificado válido
            """,
            "externalDocs": {
                "description": "Configuración de webhooks",
                "url": "https://docs.valoraciones.empresa.com/webhooks"
            }
        },
        {
            "name": "Configuración",
            "description": """
            **Gestión de contactos, plantillas y configuración**
            
            Endpoints para administrar la configuración del sistema:
            contactos de WhatsApp, plantillas de mensajes y configuraciones.
            
            ### Recursos gestionados:
            - 👥 **Contactos**: Usuarios que reciben notificaciones
            - 📝 **Plantillas**: Templates de mensajes personalizables
            - ⚙️ **Configuración**: Horarios, reintentos, etc.
            
            ### Funcionalidades:
            - Búsqueda y filtrado avanzado
            - Validación de números telefónicos
            - Preview de mensajes con variables
            - Configuración de horarios laborables
            """,
            "externalDocs": {
                "description": "Guía de configuración",
                "url": "https://docs.valoraciones.empresa.com/config"
            }
        },
        {
            "name": "Testing y Administración",
            "description": """
            **Herramientas para testing y administración**
            
            Endpoints especializados para pruebas, debugging y administración
            del sistema de notificaciones.
            
            ### Herramientas incluidas:
            - 🧪 **Test Messages**: Envío de mensajes de prueba
            - 🔧 **Admin Tools**: Procesamiento forzado, métricas manuales
            - 📊 **Stats**: Estadísticas detalladas del sistema
            - 🚨 **Troubleshooting**: Herramientas de diagnóstico
            
            ### Casos de uso:
            - Validación de configuración
            - Debugging de problemas
            - Mantenimiento programado
            - Análisis de performance
            """,
            "externalDocs": {
                "description": "Guía de administración",
                "url": "https://docs.valoraciones.empresa.com/admin"
            }
        }
    ]

def get_global_examples() -> Dict[str, Any]:
    """Ejemplos globales para la documentación"""
    return {
        # Ejemplo de notificación exitosa
        "notification_success": {
            "summary": "Notificación creada exitosamente",
            "description": "Ejemplo de respuesta cuando se crea una notificación correctamente",
            "value": {
                "success": True,
                "message": "Se crearon 2 notificaciones exitosamente",
                "data": {
                    "notificaciones_creadas": 2,
                    "notificaciones": [
                        {
                            "id": 1,
                            "valorizacion_id": 123,
                            "evento_trigger": "RECIBIDA",
                            "estado": "PROGRAMADA",
                            "contacto": {
                                "nombre": "Juan Pérez",
                                "telefono": "+51987654321",
                                "tipo": "CONTRATISTA"
                            },
                            "fecha_programada": "2025-01-23T09:00:00Z"
                        }
                    ],
                    "processing_time_ms": 150.2
                },
                "timestamp": "2025-01-23T08:45:00Z",
                "request_id": "req_12345"
            }
        },
        
        # Ejemplo de lista paginada
        "notification_list": {
            "summary": "Lista de notificaciones paginada",
            "description": "Ejemplo de respuesta con cursor-based pagination",
            "value": {
                "success": True,
                "message": "Se encontraron 25 notificaciones",
                "data": {
                    "items": [
                        {
                            "id": 1,
                            "valorizacion_id": 123,
                            "evento_trigger": "APROBADA",
                            "estado": "ENTREGADA",
                            "fecha_enviada": "2025-01-23T09:15:00Z",
                            "fecha_entregada": "2025-01-23T09:15:30Z",
                            "contacto": {
                                "nombre": "Ana García",
                                "telefono": "+51987654321",
                                "empresa_nombre": "Constructora ABC SAC"
                            }
                        }
                    ],
                    "total": 150,
                    "limit": 20,
                    "has_more": True,
                    "next_cursor": "eyJpZCI6MjAsInRzIjoiMjAyNS0wMS0yM1QwOTowMDowMFoifQ==",
                    "filters_applied": 2,
                    "processing_time_ms": 87.3
                },
                "request_id": "req_67890"
            }
        },
        
        # Ejemplo de métricas
        "metrics_response": {
            "summary": "Métricas del sistema",
            "description": "Ejemplo de respuesta de métricas agregadas",
            "value": {
                "success": True,
                "message": "Métricas calculadas para período 2025-01-16 - 2025-01-23",
                "data": {
                    "fecha_inicio": "2025-01-16",
                    "fecha_fin": "2025-01-23",
                    "total_notificaciones": 1520,
                    "total_enviadas": 1485,
                    "total_entregadas": 1450,
                    "total_leidas": 1180,
                    "total_errores": 35,
                    "tasa_envio_porcentaje": 97.7,
                    "tasa_entrega_porcentaje": 95.4,
                    "tasa_lectura_porcentaje": 81.4,
                    "tasa_error_porcentaje": 2.3,
                    "por_evento": {
                        "RECIBIDA": 500,
                        "EN_REVISION": 300,
                        "APROBADA": 420,
                        "RECHAZADA": 200,
                        "OBSERVADA": 100
                    },
                    "tiempo_promedio_entrega_minutos": 2.5,
                    "tendencias": {
                        "total_anterior": 1280,
                        "cambio_porcentual": 18.75,
                        "tendencia": "up"
                    }
                },
                "request_id": "req_metrics_001"
            }
        },
        
        # Ejemplo de error de validación
        "validation_error": {
            "summary": "Error de validación",
            "description": "Ejemplo de respuesta cuando hay errores de validación",
            "value": {
                "success": False,
                "error": "validation_error",
                "message": "Datos de entrada inválidos",
                "details": {
                    "valorizacion_id": ["El ID de valorización debe ser mayor a 0"],
                    "telefono": ["Formato de número telefónico inválido"]
                },
                "timestamp": "2025-01-23T08:45:00Z",
                "request_id": "req_error_001"
            }
        },
        
        # Ejemplo de rate limit
        "rate_limit_error": {
            "summary": "Rate limit excedido",
            "description": "Ejemplo de respuesta cuando se excede el rate limit",
            "value": {
                "success": False,
                "error": "rate_limit_exceeded",
                "message": "Rate limit excedido",
                "details": {
                    "limit": 100,
                    "remaining": 0,
                    "reset_time": 1706002800,
                    "window_seconds": 60
                },
                "timestamp": "2025-01-23T08:45:00Z",
                "request_id": "req_ratelimit_001"
            }
        },
        
        # Ejemplo de health check
        "health_check": {
            "summary": "Estado de salud del sistema",
            "description": "Ejemplo de respuesta de health check completo",
            "value": {
                "success": True,
                "message": "Sistema healthy",
                "data": {
                    "status": "healthy",
                    "timestamp": "2025-01-23T08:45:00Z",
                    "version": "2.0.0",
                    "uptime_seconds": 86400,
                    "components": {
                        "database": {
                            "status": "healthy",
                            "response_time_ms": 15.2,
                            "last_check": "2025-01-23T08:45:00Z"
                        },
                        "whatsapp_api": {
                            "status": "healthy", 
                            "response_time_ms": 250.5,
                            "rate_limit_remaining": 950
                        },
                        "scheduler": {
                            "status": "healthy",
                            "active_jobs": 3,
                            "next_execution": "2025-01-23T09:00:00Z"
                        }
                    },
                    "total_notifications_today": 145,
                    "pending_notifications": 5,
                    "failed_notifications_last_hour": 1
                },
                "request_id": "req_health_001"
            }
        }
    }

def customize_openapi_responses():
    """Personalizar respuestas estándar de la documentación"""
    return {
        "400": {
            "description": "Solicitud inválida - Error de validación",
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                    "example": {"$ref": "#/components/examples/validation_error"}
                }
            }
        },
        "401": {
            "description": "No autorizado - Token inválido o expirado",
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                    "example": {
                        "success": False,
                        "error": "unauthorized",
                        "message": "Token inválido o expirado",
                        "timestamp": "2025-01-23T08:45:00Z"
                    }
                }
            }
        },
        "403": {
            "description": "Prohibido - Permisos insuficientes",
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                    "example": {
                        "success": False,
                        "error": "forbidden", 
                        "message": "Permisos insuficientes para esta operación",
                        "timestamp": "2025-01-23T08:45:00Z"
                    }
                }
            }
        },
        "404": {
            "description": "No encontrado - Recurso no existe",
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                    "example": {
                        "success": False,
                        "error": "not_found",
                        "message": "Recurso no encontrado",
                        "timestamp": "2025-01-23T08:45:00Z"
                    }
                }
            }
        },
        "429": {
            "description": "Rate limit excedido",
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                    "example": {"$ref": "#/components/examples/rate_limit_error"}
                }
            },
            "headers": {
                "X-RateLimit-Limit": {
                    "description": "Límite de requests por ventana",
                    "schema": {"type": "integer"}
                },
                "X-RateLimit-Remaining": {
                    "description": "Requests restantes en ventana actual",
                    "schema": {"type": "integer"}
                },
                "X-RateLimit-Reset": {
                    "description": "Timestamp cuando se resetea el límite",
                    "schema": {"type": "integer"}
                },
                "Retry-After": {
                    "description": "Segundos a esperar antes de retry",
                    "schema": {"type": "integer"}
                }
            }
        },
        "500": {
            "description": "Error interno del servidor",
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                    "example": {
                        "success": False,
                        "error": "internal_server_error",
                        "message": "Error interno del servidor",
                        "timestamp": "2025-01-23T08:45:00Z",
                        "request_id": "req_error_500_001"
                    }
                }
            }
        }
    }

# =====================================================================
# GUÍAS DE INTEGRACIÓN INCLUIDAS EN LA DOCUMENTACIÓN  
# =====================================================================

def get_integration_guides() -> Dict[str, str]:
    """Guías de integración para incluir en la documentación"""
    return {
        "quickstart": """
# 🚀 Guía de Inicio Rápido

## 1. Obtener Credenciales
```bash
# Contactar al administrador para obtener:
API_KEY=wn_your_api_key_here
BASE_URL=https://api.valoraciones.empresa.com
```

## 2. Primera Notificación
```javascript
const response = await fetch(`${BASE_URL}/api/notifications`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${API_KEY}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    valorizacion_id: 123,
    evento_trigger: 'RECIBIDA',
    estado_actual: 'PENDIENTE_REVISION',
    tipo_envio: 'INMEDIATO'
  })
});
```

## 3. Consultar Notificaciones
```javascript
const notifications = await fetch(
  `${BASE_URL}/api/notifications?limit=20&estado=ENVIADA`,
  {
    headers: { 'Authorization': `Bearer ${API_KEY}` }
  }
);
```
        """,
        
        "error_handling": """
# 🚨 Manejo de Errores

## Códigos de Error Comunes
- `400` - Datos inválidos o faltantes
- `401` - Token inválido o expirado
- `403` - Permisos insuficientes  
- `429` - Rate limit excedido
- `500` - Error interno

## Estrategias de Retry
```javascript
async function createNotificationWithRetry(data, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      const response = await createNotification(data);
      return response;
    } catch (error) {
      if (error.status === 429) {
        // Rate limit - esperar y reintentar
        const retryAfter = error.headers['Retry-After'] || 60;
        await sleep(retryAfter * 1000);
        continue;
      }
      
      if (error.status >= 500 && i < maxRetries - 1) {
        // Error del servidor - retry exponencial
        await sleep(Math.pow(2, i) * 1000);
        continue;
      }
      
      throw error; // No reintentar en otros casos
    }
  }
}
```
        """,
        
        "best_practices": """
# ✅ Mejores Prácticas

## 1. Autenticación
- Almacenar tokens de forma segura
- Implementar renovación automática
- No incluir credenciales en logs

## 2. Rate Limiting
- Respetar headers de rate limiting
- Implementar exponential backoff
- Usar batch operations cuando sea posible

## 3. Paginación
- Preferir cursor-based pagination
- Procesar resultados en lotes
- Manejar casos de datos cambiantes

## 4. Monitoring
- Implementar health checks periódicos
- Monitorear métricas de la API
- Configurar alertas para errores

## 5. Seguridad
- Validar webhooks con signatures
- Usar HTTPS en todos los endpoints
- Implementar timeout apropiados
        """
    }