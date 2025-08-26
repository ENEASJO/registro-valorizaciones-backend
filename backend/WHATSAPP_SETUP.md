# 📱 Configuración de WhatsApp Business API

## Resumen

Este documento proporciona instrucciones paso a paso para configurar el **Sistema de Notificaciones WhatsApp** en producción. El sistema está completamente implementado y listo para usar.

## ✅ Estado del Sistema

- ✅ **Base de datos migrada** - 6 tablas WhatsApp creadas con éxito
- ✅ **API endpoints implementados** - Rutas para crear y gestionar notificaciones
- ✅ **Servicios WhatsApp implementados** - Integración con WhatsApp Business API
- ✅ **Plantillas de mensajes** - 5 plantillas predefinidas para todos los estados
- ✅ **Documentación completa** - Guías para usuarios, desarrolladores y administradores

## 🚀 Pasos para Configuración en Producción

### 1. Configurar Meta for Developers

1. Ve a [Meta for Developers](https://developers.facebook.com/)
2. Crea una nueva aplicación o usa una existente
3. Añade el producto **WhatsApp Business API**
4. Obtén los siguientes valores:

```bash
# Desde Meta for Developers > WhatsApp > API Setup
WHATSAPP_ACCESS_TOKEN="tu_token_de_acceso_permanente"
WHATSAPP_PHONE_NUMBER_ID="tu_phone_number_id"
WHATSAPP_VERIFY_TOKEN="tu_token_verificacion_personalizado"
```

### 2. Configurar Variables de Entorno en Cloud Run

```bash
# Base de datos
DATABASE_URL="libsql://tu-database.turso.io"

# WhatsApp Business API
WHATSAPP_API_URL="https://graph.facebook.com/v18.0"
WHATSAPP_ACCESS_TOKEN="tu_token_de_acceso"
WHATSAPP_PHONE_NUMBER_ID="tu_phone_number_id"
WHATSAPP_VERIFY_TOKEN="tu_token_verificacion_2025"
WHATSAPP_WEBHOOK_ENDPOINT="/api/notifications/webhook"

# Rate Limiting (ajustar según tu plan)
WHATSAPP_RATE_LIMIT_PER_MINUTE=100
WHATSAPP_RETRY_ATTEMPTS=3
WHATSAPP_RETRY_DELAY_SECONDS=30

# Horarios de trabajo (Perú)
WHATSAPP_WORK_HOURS_START="08:00"
WHATSAPP_WORK_HOURS_END="18:00" 
WHATSAPP_TIMEZONE="America/Lima"

# Seguridad
SECRET_KEY="clave_secreta_produccion_muy_segura"
```

### 3. Configurar Webhook en Meta

1. En Meta for Developers > WhatsApp > Configuration
2. Configura el webhook URL: `https://tu-dominio.com/api/notifications/webhook`
3. Token de verificación: usa el mismo valor de `WHATSAPP_VERIFY_TOKEN`
4. Suscríbete a eventos: `messages`, `message_status`

### 4. Configurar Contactos WhatsApp

Ejecuta este script para añadir contactos de prueba:

```python
# Ejemplo de configuración de contactos
POST /api/notifications/contacts
{
    "empresa_id": 1,
    "nombre": "Juan Pérez",
    "cargo": "Gerente de Proyecto", 
    "telefono": "51987654321",
    "email": "juan.perez@constructora.com",
    "tipo_contacto": "CONTRATISTA",
    "es_principal": true,
    "recibe_notificaciones": true,
    "eventos_suscritos": ["RECIBIDA", "EN_REVISION", "OBSERVADA", "APROBADA"]
}
```

### 5. Probar el Sistema

```bash
# 1. Crear una notificación de prueba
curl -X POST "https://tu-dominio.com/api/notifications" \
  -H "Content-Type: application/json" \
  -d '{
    "valorizacion_id": 1,
    "evento_trigger": "RECIBIDA", 
    "contacto_telefono": "51987654321",
    "variables": {
      "obra_nombre": "Obra de Prueba",
      "empresa_razon_social": "Constructora ABC SAC",
      "valorizacion_numero": "001",
      "valorizacion_periodo": "Enero 2025",
      "monto_total": "50000.00"
    }
  }'

# 2. Verificar estado de la notificación
curl "https://tu-dominio.com/api/notifications?estado=ENVIADA"

# 3. Ver métricas del sistema
curl "https://tu-dominio.com/api/notifications/metrics"
```

## 📊 URLs del Sistema

Una vez configurado, tendrás acceso a:

- **API Principal**: `https://tu-dominio.com/api/notifications`
- **Webhook WhatsApp**: `https://tu-dominio.com/api/notifications/webhook`
- **Métricas**: `https://tu-dominio.com/api/notifications/metrics`
- **Documentación**: `https://tu-dominio.com/docs`

## 🔧 Configuración de Plantillas

El sistema incluye 5 plantillas predefinidas:

1. **VAL_RECIBIDA_CONTRATISTA** - Notifica recepción de valorización
2. **VAL_EN_REVISION_CONTRATISTA** - Notifica inicio de revisión
3. **VAL_OBSERVADA_CONTRATISTA** - Notifica observaciones ⚠️
4. **VAL_APROBADA_CONTRATISTA** - Notifica aprobación ✅
5. **VAL_RECHAZADA_CONTRATISTA** - Notifica rechazo ❌

### Personalizar Plantillas

```sql
-- Ejemplo: Actualizar plantilla de valorización observada
UPDATE whatsapp_plantillas_mensajes 
SET mensaje_texto = 'Tu mensaje personalizado aquí con {variables}'
WHERE codigo = 'VAL_OBSERVADA_CONTRATISTA';
```

## 🚨 Integración con Sistema de Valorizaciones

### Opción 1: Automática (Recomendado)

Añade este decorador a tus endpoints de valorización:

```python
from app.services.notification_service import auto_notify_valorizacion

@auto_notify_valorizacion
async def actualizar_estado_valorizacion(id: int, nuevo_estado: str):
    # Tu lógica existente
    pass
```

### Opción 2: Manual

```python
from app.services.notification_service import NotificationService

# En tu lógica de cambio de estado
notification_service = NotificationService()
await notification_service.crear_notificacion_automatica(
    valorizacion_id=valorizacion.id,
    evento_trigger="OBSERVADA",
    estado_anterior="EN_REVISION", 
    estado_actual="OBSERVADA"
)
```

### Opción 3: API REST

```bash
curl -X POST "https://tu-dominio.com/api/notifications/auto" \
  -H "Content-Type: application/json" \
  -d '{
    "valorizacion_id": 123,
    "evento_trigger": "APROBADA",
    "estado_anterior": "EN_REVISION",
    "estado_actual": "APROBADA"
  }'
```

## 📈 Monitoreo y Métricas

### Dashboard de Métricas

```bash
# Métricas generales del sistema
GET /api/notifications/metrics

# Estadísticas por empresa
GET /api/notifications/metrics/empresa/{empresa_id}

# Notificaciones pendientes
GET /api/notifications?estado=PENDIENTE

# Errores recientes
GET /api/notifications?estado=ERROR&limit=10
```

### Health Check

```bash
# Verificar estado del sistema
GET /health

# Verificar conexión WhatsApp
GET /api/notifications/health
```

## 🛠️ Troubleshooting

### Problema: Mensajes no se envían

1. Verificar token de acceso: `WHATSAPP_ACCESS_TOKEN`
2. Verificar ID de teléfono: `WHATSAPP_PHONE_NUMBER_ID`
3. Comprobar límites de rate: `WHATSAPP_RATE_LIMIT_PER_MINUTE`
4. Revisar horarios: `WHATSAPP_WORK_HOURS_START/END`

```bash
# Ver logs de errores
SELECT * FROM whatsapp_notificaciones 
WHERE estado = 'ERROR' 
ORDER BY created_at DESC LIMIT 10;
```

### Problema: Webhook no funciona

1. Verificar URL del webhook en Meta
2. Comprobar token de verificación: `WHATSAPP_VERIFY_TOKEN`
3. Verificar que el endpoint sea accesible públicamente

```bash
# Probar webhook manualmente
curl -X GET "https://tu-dominio.com/api/notifications/webhook?hub.verify_token=tu_token&hub.challenge=test"
```

## 📞 Soporte

- **Documentación técnica**: `/docs/OPERATIONS.md`
- **API Reference**: `/docs/API_REFERENCE.md`
- **Guía de usuario**: `/docs/USER_GUIDE.md`
- **Emergencias**: Ver contactos en documentación principal

## 🎯 Próximos Pasos

1. ✅ Sistema implementado y migrado
2. ⏳ Configurar credenciales de Meta for Developers
3. ⏳ Probar envío de notificaciones en producción
4. ⏳ Configurar monitoreo y alertas
5. ⏳ Entrenar usuarios finales

---

**Sistema de Notificaciones WhatsApp v1.0**  
*Implementado: 23 de Agosto 2025*  
*Estado: ✅ Listo para producción*