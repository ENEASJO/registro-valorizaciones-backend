# Guía de Integración - Sistema de Notificaciones WhatsApp

## Descripción General

Este sistema proporciona notificaciones automáticas por WhatsApp para cambios de estado en valorizaciones de construcción. Utiliza la WhatsApp Business API oficial de Meta.

## Arquitectura del Sistema

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Valorizaciones │───▶│ Notification     │───▶│ WhatsApp        │
│  Service        │    │ Middleware       │    │ Business API    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                 │
                                 ▼
                       ┌──────────────────┐
                       │ Scheduler        │
                       │ Service          │
                       └──────────────────┘
                                 │
                                 ▼
                       ┌──────────────────┐
                       │ Database         │
                       │ (Notifications)  │
                       └──────────────────┘
```

## Configuración Inicial

### 1. Configurar WhatsApp Business API

1. **Crear aplicación en Meta for Developers:**
   - Visite https://developers.facebook.com/
   - Cree una nueva aplicación
   - Agregue el producto "WhatsApp Business API"

2. **Obtener credenciales:**
   ```bash
   WHATSAPP_ACCESS_TOKEN="EAAxxxxx..."  # Token permanente
   WHATSAPP_PHONE_NUMBER_ID="123456789"  # ID del número registrado
   WHATSAPP_VERIFY_TOKEN="mi_token_verificacion"  # Token personalizado
   ```

3. **Configurar webhook:**
   - URL: `https://tu-dominio.com/api/notifications/webhook`
   - Eventos: `messages`, `message_deliveries`, `message_reads`

### 2. Variables de Entorno

Copie `.env.example` a `.env` y configure:

```bash
# WhatsApp Business API
WHATSAPP_ACCESS_TOKEN="tu_token_aqui"
WHATSAPP_PHONE_NUMBER_ID="tu_numero_id"
WHATSAPP_VERIFY_TOKEN="tu_token_verificacion"

# Configuración de horarios
WHATSAPP_WORK_HOURS_START="08:00"
WHATSAPP_WORK_HOURS_END="18:00"
WHATSAPP_TIMEZONE="America/Lima"

# Redis para background tasks
REDIS_URL="redis://localhost:6379/0"
```

### 3. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 4. Inicializar Base de Datos

Ejecute el script de migración:

```bash
python sql/migrate_whatsapp_notifications.py
```

## Uso del Sistema

### Integración Automática

El sistema se integra automáticamente con cambios de valorizaciones:

```python
from app.services.notification_middleware import notify_valorizacion_change

# En su servicio de valorizaciones:
async def actualizar_estado_valorizacion(valorizacion_id, nuevo_estado):
    # Lógica de actualización...
    
    # Crear notificaciones automáticas
    await notify_valorizacion_change(
        valorizacion_id=valorizacion_id,
        estado_anterior="EN_REVISION",
        estado_nuevo=nuevo_estado,
        empresa_id=123,
        monto_total=50000.0,
        observaciones="Correcciones menores requeridas"
    )
```

### Uso con Decorador

```python
from app.services.notification_middleware import notify_on_status_change

class ValorizacionService:
    @notify_on_status_change
    async def update_status(self, valorizacion_id, nuevo_estado, **kwargs):
        # Su lógica existente
        old_status = self.get_current_status(valorizacion_id)
        result = self.update_valorizacion_status(valorizacion_id, nuevo_estado)
        
        # El decorador creará automáticamente las notificaciones
        return {
            "valorizacion_id": valorizacion_id,
            "estado_anterior": old_status,
            "estado_nuevo": nuevo_estado,
            "empresa_id": kwargs.get("empresa_id"),
            "success": True
        }
```

### API Endpoints

#### Crear Notificación Manual

```bash
POST /api/notifications
```

```json
{
  "valorizacion_id": 123,
  "plantilla_id": 1,
  "contacto_id": 456,
  "evento_trigger": "APROBADA",
  "estado_actual": "APROBADA",
  "tipo_envio": "INMEDIATO"
}
```

#### Listar Notificaciones

```bash
GET /api/notifications?pagina=1&limite=20&estado=ENVIADA
```

#### Enviar Mensaje de Prueba

```bash
POST /api/notifications/test
```

```json
{
  "phone_number": "51987654321",
  "message": "Mensaje de prueba del sistema"
}
```

#### Obtener Métricas

```bash
GET /api/notifications/metrics?fecha_inicio=2025-01-01&fecha_fin=2025-01-31
```

## Configuración de Contactos

### Agregar Contactos WhatsApp

Los contactos se gestionan a través de la base de datos:

```sql
INSERT INTO whatsapp_contactos (
    empresa_id, nombre, telefono, tipo_contacto,
    recibe_notificaciones, eventos_suscritos
) VALUES (
    123, 'Juan Pérez', '51987654321', 'CONTRATISTA',
    TRUE, '["RECIBIDA","OBSERVADA","APROBADA"]'
);
```

### Configurar Horarios

```sql
INSERT INTO whatsapp_configuracion_horarios (
    nombre, descripcion, hora_inicio_envios, hora_fin_envios
) VALUES (
    'Horario Extendido', 'Para notificaciones urgentes',
    '07:00:00', '20:00:00'
);
```

## Plantillas de Mensaje

### Plantilla de Ejemplo

```sql
INSERT INTO whatsapp_plantillas_mensajes (
    codigo, nombre, evento_trigger, estado_valorizacion,
    tipo_destinatario, mensaje_texto, prioridad
) VALUES (
    'VAL_CUSTOM', 'Valorización Personalizada', 'APROBADA', 'APROBADA',
    'CONTRATISTA', 
    'Estimado {empresa_razon_social},

Su valorización #{valorizacion_numero} ha sido APROBADA.

Monto: S/ {monto_total}
Fecha: {fecha_cambio}

Próximo paso: Espere el cronograma de pagos.

Saludos,
Sistema de Valorizaciones',
    3
);
```

### Variables Disponibles

- `{obra_nombre}`: Nombre del proyecto
- `{empresa_razon_social}`: Nombre de la empresa
- `{valorizacion_numero}`: Número de valorización
- `{valorizacion_periodo}`: Período (MM/YYYY)
- `{estado_actual}`: Estado actual
- `{estado_anterior}`: Estado anterior
- `{fecha_cambio}`: Fecha del cambio
- `{monto_total}`: Monto en soles
- `{observaciones}`: Comentarios adicionales
- `{contacto_nombre}`: Nombre del contacto

## Monitoreo y Métricas

### Verificar Estado del Sistema

```bash
GET /api/notifications/scheduler/status
```

### Métricas Diarias

```bash
GET /api/notifications/metrics/daily?fecha_inicio=2025-01-01
```

### Forzar Procesamiento

```bash
POST /api/notifications/process-pending?limit=100
```

## Webhooks de WhatsApp

### Configuración en Meta

1. **URL del Webhook:** `https://tu-dominio.com/api/notifications/webhook`
2. **Token de Verificación:** El valor de `WHATSAPP_VERIFY_TOKEN`
3. **Eventos Suscritos:**
   - `messages`
   - `message_deliveries` 
   - `message_reads`

### Estados de Mensaje

El sistema rastrea automáticamente:

- **ENVIADA**: WhatsApp recibió el mensaje
- **ENTREGADA**: Mensaje llegó al dispositivo
- **LEIDA**: Usuario leyó el mensaje
- **ERROR**: Fallo en entrega

## Troubleshooting

### Problemas Comunes

1. **Error 403 en Webhook:**
   - Verificar `WHATSAPP_VERIFY_TOKEN`
   - Confirmar URL del webhook

2. **Mensajes no se envían:**
   - Verificar `WHATSAPP_ACCESS_TOKEN`
   - Confirmar `WHATSAPP_PHONE_NUMBER_ID`
   - Revisar rate limits

3. **Números inválidos:**
   - Solo números peruanos (+51)
   - Formato: 51987654321 (sin +)

4. **Scheduler no funciona:**
   - Verificar `REDIS_URL`
   - Confirmar `BACKGROUND_TASKS_ENABLED=true`

### Logs de Depuración

```python
import logging
logging.getLogger('app.services.whatsapp_service').setLevel(logging.DEBUG)
logging.getLogger('app.services.notification_service').setLevel(logging.DEBUG)
```

## Seguridad

### Validación de Webhooks

El sistema valida automáticamente:
- Token de verificación
- Firma de payload (si configurada)
- Rate limiting

### Datos Sensibles

- Números telefónicos se enmascaran en logs
- Tokens se mantienen en variables de entorno
- Mensajes se validan antes del envío

## Limitaciones

### WhatsApp Business API

- **Rate Limit:** 1000 mensajes/segundo (tier gratuito)
- **Longitud:** 1024 caracteres máximo
- **Horarios:** Respetar horarios laborales locales

### Sistema

- **Reintentos:** Máximo 3 intentos por mensaje
- **Retención:** Datos se conservan 90 días
- **Contactos:** Validación automática de números peruanos

## Ejemplos de Integración

### Frontend React

```javascript
// Enviar mensaje de prueba
const sendTestMessage = async () => {
  const response = await fetch('/api/notifications/test', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      phone_number: '51987654321',
      message: 'Mensaje de prueba'
    })
  });
  const result = await response.json();
  console.log(result);
};
```

### Dashboard de Métricas

```javascript
// Obtener métricas del último mes
const getMetrics = async () => {
  const endDate = new Date().toISOString().split('T')[0];
  const startDate = new Date(Date.now() - 30*24*60*60*1000)
    .toISOString().split('T')[0];
  
  const response = await fetch(
    `/api/notifications/metrics?fecha_inicio=${startDate}&fecha_fin=${endDate}`
  );
  return response.json();
};
```

## Soporte

Para soporte técnico:
1. Revisar logs del sistema
2. Verificar configuración de variables de entorno
3. Probar conectividad con WhatsApp Business API
4. Consultar documentación oficial de Meta

---

**Versión:** 1.0.0  
**Última actualización:** 2025-08-23