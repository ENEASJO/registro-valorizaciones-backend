# Guía de Integración - Sistema de Notificaciones WhatsApp

## Descripción General

Esta guía te ayudará a integrar el Sistema de Notificaciones WhatsApp con tu sistema existente de valorizaciones. La integración está diseñada para ser **no invasiva**, **fácil de implementar** y **altamente personalizable** según tus necesidades específicas.

## Arquitectura de Integración

```
┌─────────────────────────┐    ┌─────────────────────────┐    ┌─────────────────────────┐
│   Tu Sistema Existente  │    │   Notification          │    │   WhatsApp Business     │
│                         │    │   Middleware            │    │   API                   │
│  ┌───────────────────┐  │    │                         │    │                         │
│  │ Valorizaciones    │  │    │  ┌───────────────────┐  │    │  ┌───────────────────┐  │
│  │ Service           │──┼────┼─▶│ Event Handler     │  │    │  │ Message Delivery  │  │
│  └───────────────────┘  │    │  └───────────────────┘  │    │  └───────────────────┘  │
│                         │    │           │             │    │           │             │
│  ┌───────────────────┐  │    │  ┌───────────────────┐  │    │  ┌───────────────────┐  │
│  │ Database          │  │    │  │ Template Engine   │  │    │  │ Status Tracking   │  │
│  │ Updates           │──┼────┼─▶│ & Queue           │──┼────┼─▶│ & Webhooks        │  │
│  └───────────────────┘  │    │  └───────────────────┘  │    │  └───────────────────┘  │
└─────────────────────────┘    └─────────────────────────┘    └─────────────────────────┘
                                          │
                              ┌─────────────────────────┐
                              │   Background Jobs       │
                              │                         │
                              │  • Scheduler Service    │
                              │  • Retry Logic          │
                              │  • Work Hours Control   │
                              │  • Metrics Collection   │
                              └─────────────────────────┘
```

## Estrategias de Integración

### Opción 1: Integración Automática con Decorador (Recomendado)

La forma más sencilla de integrar es usando el decorador que automáticamente crea notificaciones cuando los estados cambian.

```python
from app.services.notification_middleware import notify_on_status_change
from app.core.database import get_db

class ValorizacionService:
    """Tu servicio existente de valorizaciones"""
    
    @notify_on_status_change
    async def update_status(
        self, 
        valorizacion_id: int, 
        nuevo_estado: str, 
        **kwargs
    ) -> dict:
        """
        Tu método existente - el decorador se encarga del resto
        """
        # Tu lógica existente
        old_status = self.get_current_status(valorizacion_id)
        
        # Actualizar estado en tu base de datos
        success = self.update_valorizacion_status(valorizacion_id, nuevo_estado)
        
        if not success:
            raise ValueError("Error actualizando estado")
        
        # Retorna información para el decorador
        return {
            "valorizacion_id": valorizacion_id,
            "estado_anterior": old_status,
            "estado_nuevo": nuevo_estado,
            "empresa_id": kwargs.get("empresa_id"),
            "monto_total": kwargs.get("monto_total", 0.0),
            "observaciones": kwargs.get("observaciones", ""),
            "success": True
        }

# Uso del servicio (sin cambios en tu código existente)
service = ValorizacionService()
await service.update_status(
    valorizacion_id=123,
    nuevo_estado="APROBADA",
    empresa_id=456,
    monto_total=50000.0,
    observaciones="Aprobada sin observaciones"
)
```

### Opción 2: Integración Manual con Helper

Para mayor control, puedes llamar directamente al servicio de notificaciones.

```python
from app.services.notification_middleware import notify_valorizacion_change
from app.models.whatsapp_notifications import EventoTrigger

class ValorizacionService:
    """Tu servicio existente"""
    
    async def approve_valorizacion(self, valorizacion_id: int, empresa_id: int):
        """Aprobar valorización con notificación manual"""
        
        # Tu lógica existente
        old_status = "EN_REVISION"
        new_status = "APROBADA"
        
        # Actualizar en tu base de datos
        self.update_valorizacion_status(valorizacion_id, new_status)
        
        # Crear notificaciones WhatsApp
        await notify_valorizacion_change(
            valorizacion_id=valorizacion_id,
            evento_trigger=EventoTrigger.APROBADA,
            estado_anterior=old_status,
            estado_nuevo=new_status,
            empresa_id=empresa_id,
            variables_extra={
                "monto_total": "50000.00",
                "fecha_aprobacion": "23/01/2025",
                "responsable_aprobacion": "Juan Pérez"
            }
        )
```

### Opción 3: Integración por API REST

Si prefieres integración vía HTTP calls, puedes usar los endpoints REST.

```python
import httpx
from typing import Dict, Any

class ValorizacionNotificationClient:
    """Cliente para integración via API REST"""
    
    def __init__(self, api_url: str, api_key: str):
        self.api_url = api_url
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    async def create_notification(
        self,
        valorizacion_id: int,
        evento: str,
        estado_actual: str,
        estado_anterior: str = None,
        variables: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Crear notificación via API REST"""
        
        payload = {
            "valorizacion_id": valorizacion_id,
            "evento_trigger": evento,
            "estado_actual": estado_actual,
            "estado_anterior": estado_anterior,
            "tipo_envio": "INMEDIATO",
            "variables_extra": variables or {}
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/api/notifications",
                json=payload,
                headers=self.headers,
                timeout=30.0
            )
            return response.json()

# Uso del cliente
client = ValorizacionNotificationClient(
    api_url="https://api.valoraciones.com",
    api_key="tu-api-key-aqui"
)

# En tu servicio existente
await client.create_notification(
    valorizacion_id=123,
    evento="APROBADA",
    estado_actual="APROBADA",
    estado_anterior="EN_REVISION",
    variables={
        "monto_total": "50000.00",
        "empresa_razon_social": "CONSTRUCTORA ABC S.A.C.",
        "fecha_aprobacion": "23/01/2025"
    }
)
```

## Configuración de Contactos

### Gestión de Contactos por Empresa

```python
from app.core.database import get_db
from app.models.whatsapp_notifications import WhatsAppContactosDB

async def setup_empresa_contacts(empresa_id: int, contactos_data: list):
    """
    Configurar contactos de WhatsApp para una empresa
    """
    db = next(get_db())
    
    for contacto in contactos_data:
        # Validar número telefónico
        from app.services.whatsapp_service import whatsapp_service
        is_valid, formatted_phone, error = whatsapp_service.validate_phone_number(
            contacto["telefono"]
        )
        
        if not is_valid:
            print(f"⚠️  Número inválido para {contacto['nombre']}: {error}")
            continue
        
        # Crear contacto
        contacto_db = WhatsAppContactosDB(
            empresa_id=empresa_id,
            nombre=contacto["nombre"],
            cargo=contacto.get("cargo", ""),
            telefono=formatted_phone,
            email=contacto.get("email", ""),
            tipo_contacto="CONTRATISTA",
            es_principal=contacto.get("es_principal", False),
            eventos_suscritos=json.dumps(contacto.get(
                "eventos", 
                ["RECIBIDA", "OBSERVADA", "APROBADA", "RECHAZADA"]
            )),
            horario_configuracion_id=1  # Horario estándar
        )
        
        db.add(contacto_db)
    
    db.commit()
    db.close()
    print(f"✅ Configurados {len(contactos_data)} contactos para empresa {empresa_id}")

# Ejemplo de uso
contactos_empresa_123 = [
    {
        "nombre": "Juan Pérez",
        "cargo": "Gerente de Proyecto", 
        "telefono": "987654321",
        "email": "juan.perez@constructora.com",
        "es_principal": True,
        "eventos": ["RECIBIDA", "OBSERVADA", "APROBADA", "RECHAZADA"]
    },
    {
        "nombre": "María García",
        "cargo": "Coordinadora Técnica",
        "telefono": "976543210", 
        "es_principal": False,
        "eventos": ["OBSERVADA", "RECHAZADA"]  # Solo notificaciones importantes
    }
]

await setup_empresa_contacts(123, contactos_empresa_123)
```

### Script de Migración de Contactos Existentes

```python
import json
from app.core.database import get_db
from app.models.whatsapp_notifications import WhatsAppContactosDB
from app.services.whatsapp_service import whatsapp_service

async def migrate_existing_contacts():
    """
    Migrar contactos existentes desde tu sistema actual
    """
    db = next(get_db())
    
    # Supongamos que tienes una tabla 'empresas_contactos' existente
    # Adapta esta query a tu estructura de datos
    from sqlalchemy import text
    
    existing_contacts = db.execute(text("""
        SELECT 
            e.id as empresa_id,
            e.razon_social,
            c.nombre,
            c.telefono,
            c.email,
            c.cargo,
            CASE WHEN c.es_contacto_principal = 1 THEN 1 ELSE 0 END as es_principal
        FROM empresas e 
        INNER JOIN contactos c ON e.id = c.empresa_id
        WHERE c.activo = 1 AND c.telefono IS NOT NULL
    """)).fetchall()
    
    migrated_count = 0
    error_count = 0
    
    for contact in existing_contacts:
        try:
            # Validar número telefónico
            is_valid, formatted_phone, error = whatsapp_service.validate_phone_number(
                contact.telefono
            )
            
            if not is_valid:
                print(f"⚠️  {contact.nombre}: {error}")
                error_count += 1
                continue
            
            # Verificar si ya existe
            existing = db.query(WhatsAppContactosDB).filter(
                WhatsAppContactosDB.empresa_id == contact.empresa_id,
                WhatsAppContactosDB.telefono == formatted_phone
            ).first()
            
            if existing:
                print(f"⏭️  {contact.nombre}: Ya existe")
                continue
            
            # Crear nuevo contacto WhatsApp
            whatsapp_contact = WhatsAppContactosDB(
                empresa_id=contact.empresa_id,
                nombre=contact.nombre,
                cargo=contact.cargo,
                telefono=formatted_phone,
                email=contact.email,
                tipo_contacto="CONTRATISTA",
                es_principal=bool(contact.es_principal),
                eventos_suscritos=json.dumps([
                    "RECIBIDA", "OBSERVADA", "APROBADA", "RECHAZADA"
                ]),
                horario_configuracion_id=1,
                activo=True,
                recibe_notificaciones=True
            )
            
            db.add(whatsapp_contact)
            migrated_count += 1
            print(f"✅ {contact.nombre} ({contact.razon_social})")
            
        except Exception as e:
            print(f"❌ Error con {contact.nombre}: {str(e)}")
            error_count += 1
    
    db.commit()
    db.close()
    
    print(f"\n📊 Migración completada:")
    print(f"   ✅ Migrados: {migrated_count}")
    print(f"   ❌ Errores: {error_count}")

# Ejecutar migración
await migrate_existing_contacts()
```

## Personalización de Plantillas

### Crear Plantillas Personalizadas

```sql
-- Plantilla personalizada para observaciones críticas
INSERT INTO whatsapp_plantillas_mensajes (
    codigo, nombre, descripcion, evento_trigger, estado_valorizacion,
    tipo_destinatario, mensaje_texto, prioridad, activo
) VALUES (
    'OBS_CRITICA_CUSTOM',
    'Observación Crítica - Empresa Específica',
    'Plantilla personalizada para observaciones que requieren atención inmediata',
    'OBSERVADA',
    'OBSERVADA', 
    'CONTRATISTA',
    '🔴 ACCIÓN URGENTE REQUERIDA - {obra_nombre}

Estimado {empresa_razon_social},

Su valorización #{valorizacion_numero} presenta OBSERVACIONES CRÍTICAS que requieren atención INMEDIATA.

📋 DETALLES:
• Obra: {obra_nombre}
• Período: {valorizacion_periodo}  
• Monto: S/ {monto_total}
• Fecha: {fecha_cambio}

⚠️  OBSERVACIONES CRÍTICAS:
{observaciones}

📞 CONTACTO INMEDIATO:
Para resolución urgente, comunicarse con:
• Área Técnica: (01) 123-4567
• Email: tecnico@empresa.com
• Horario: L-V 8:00-18:00

⏰ PLAZO: 48 horas para subsanar
❗ Después de este plazo, la valorización será RECHAZADA automáticamente.

Atentamente,
Sistema de Valorizaciones',
    1,  -- Prioridad alta
    TRUE
);

-- Plantilla para aprobaciones con monto alto
INSERT INTO whatsapp_plantillas_mensajes (
    codigo, nombre, descripcion, evento_trigger, estado_valorizacion,
    tipo_destinatario, mensaje_texto, prioridad, activo
) VALUES (
    'APROB_MONTO_ALTO',
    'Aprobación Monto Alto',
    'Plantilla especial para valorizaciones aprobadas de monto elevado',
    'APROBADA',
    'APROBADA',
    'CONTRATISTA',
    '🎉 VALORIZACIÓN APROBADA - MONTO ALTO 🎉

¡Felicitaciones {empresa_razon_social}!

Su valorización #{valorizacion_numero} ha sido APROBADA por un monto significativo.

💰 DETALLES DE APROBACIÓN:
• Obra: {obra_nombre}
• Período: {valorizacion_periodo}
• Monto APROBADO: S/ {monto_total}
• Fecha de aprobación: {fecha_cambio}

📅 CRONOGRAMA DE PAGO:
• Emisión de factura: 3 días hábiles
• Procesamiento: 7-10 días hábiles  
• Pago programado: 15-20 días hábiles

📋 PRÓXIMOS PASOS:
1. Emitir factura según términos contractuales
2. Adjuntar sustento técnico requerido
3. Coordinar con área de tesorería

👥 Su equipo dedicado:
• Coordinador: coordinador@empresa.com
• Tesorería: pagos@empresa.com

¡Excelente trabajo en este proyecto!

Saludos cordiales,
Sistema de Valorizaciones',
    3,
    TRUE
);
```

### Plantillas Dinámicas por Empresa

```python
from app.models.whatsapp_notifications import WhatsAppPlantillasMensajesDB

async def create_custom_template_for_empresa(
    empresa_id: int,
    template_data: dict
) -> int:
    """
    Crear plantilla personalizada para empresa específica
    """
    db = next(get_db())
    
    # Generar código único
    codigo = f"{template_data['evento']}_{empresa_id}_{datetime.now().strftime('%Y%m%d')}"
    
    plantilla = WhatsAppPlantillasMensajesDB(
        codigo=codigo,
        nombre=f"{template_data['nombre']} - Empresa {empresa_id}",
        descripcion=template_data.get("descripcion", ""),
        evento_trigger=template_data["evento"],
        estado_valorizacion=template_data["estado"],
        tipo_destinatario=template_data.get("destinatario", "CONTRATISTA"),
        mensaje_texto=template_data["mensaje"],
        prioridad=template_data.get("prioridad", 5),
        activo=True
    )
    
    db.add(plantilla)
    db.commit()
    template_id = plantilla.id
    db.close()
    
    return template_id

# Ejemplo de uso
template_data = {
    "evento": "APROBADA",
    "estado": "APROBADA",
    "nombre": "Aprobación VIP Cliente Premium",
    "mensaje": """🌟 VALORIZACIÓN VIP APROBADA 🌟

Distinguido cliente {empresa_razon_social},

Es un placer informarle que su valorización #{valorizacion_numero} ha sido APROBADA bajo nuestro programa VIP.

💎 BENEFICIOS VIP APLICADOS:
• Procesamiento prioritario
• Pago acelerado (7 días)
• Línea directa de atención
• Gerente de cuenta dedicado

📊 RESUMEN EJECUTIVO:
• Obra: {obra_nombre}
• Monto: S/ {monto_total}
• Fecha: {fecha_cambio}

Su satisfacción es nuestra prioridad.

Cordialmente,
Equipo VIP - Valorizaciones""",
    "prioridad": 2
}

template_id = await create_custom_template_for_empresa(123, template_data)
```

## Configuración de Horarios Personalizados

### Horarios por Tipo de Cliente

```python
from app.models.whatsapp_notifications import WhatsAppConfiguracionHorariosDB
import json

async def setup_custom_schedules():
    """
    Configurar horarios personalizados para diferentes tipos de clientes
    """
    db = next(get_db())
    
    horarios_config = [
        {
            "nombre": "Cliente Premium 24/7",
            "descripcion": "Horario extendido para clientes premium",
            "dias_laborables": ["LUNES","MARTES","MIERCOLES","JUEVES","VIERNES","SABADO"],
            "hora_inicio": "06:00:00",
            "hora_fin": "22:00:00",
            "reintentos": 5,
            "intervalo": 15
        },
        {
            "nombre": "Horario Internacional",
            "descripcion": "Para empresas con operaciones internacionales", 
            "dias_laborables": ["LUNES","MARTES","MIERCOLES","JUEVES","VIERNES"],
            "hora_inicio": "05:00:00",
            "hora_fin": "20:00:00",
            "reintentos": 4,
            "intervalo": 20
        },
        {
            "nombre": "Emergencias",
            "descripcion": "Solo para notificaciones críticas",
            "dias_laborables": ["LUNES","MARTES","MIERCOLES","JUEVES","VIERNES","SABADO","DOMINGO"],
            "hora_inicio": "00:00:00", 
            "hora_fin": "23:59:59",
            "reintentos": 10,
            "intervalo": 5
        }
    ]
    
    for config in horarios_config:
        horario = WhatsAppConfiguracionHorariosDB(
            nombre=config["nombre"],
            descripcion=config["descripcion"],
            dias_laborables=json.dumps(config["dias_laborables"]),
            hora_inicio_envios=config["hora_inicio"],
            hora_fin_envios=config["hora_fin"],
            zona_horaria="America/Lima",
            reintentos_maximos=config["reintentos"],
            intervalo_reintento_minutos=config["intervalo"],
            activo=True
        )
        db.add(horario)
    
    db.commit()
    db.close()
    print("✅ Horarios personalizados configurados")

await setup_custom_schedules()
```

## Integración con Triggers de Base de Datos

### Trigger Automático en Tu Base de Datos

```sql
-- Ejemplo para PostgreSQL
CREATE OR REPLACE FUNCTION trigger_whatsapp_notification()
RETURNS TRIGGER AS $$
BEGIN
    -- Solo procesar cambios de estado
    IF OLD.estado != NEW.estado THEN
        
        -- Insertar en tabla de cola para procesamiento asíncrono
        INSERT INTO whatsapp_notification_queue (
            valorizacion_id,
            evento_trigger,
            estado_anterior, 
            estado_nuevo,
            empresa_id,
            monto_total,
            observaciones,
            created_at
        ) VALUES (
            NEW.id,
            NEW.estado,
            OLD.estado,
            NEW.estado,
            NEW.empresa_id,
            NEW.monto_total,
            NEW.observaciones,
            NOW()
        );
        
        -- Log del cambio
        RAISE NOTICE 'WhatsApp notification queued for valorization %', NEW.id;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Crear trigger
DROP TRIGGER IF EXISTS whatsapp_notification_trigger ON valorizaciones;
CREATE TRIGGER whatsapp_notification_trigger
    AFTER UPDATE ON valorizaciones
    FOR EACH ROW
    EXECUTE FUNCTION trigger_whatsapp_notification();
```

### Procesador de Cola de Notificaciones

```python
import asyncio
from datetime import datetime
from sqlalchemy import text
from app.services.notification_service import notification_service
from app.models.whatsapp_notifications import EventoTrigger

class NotificationQueueProcessor:
    """Procesador de cola de notificaciones desde tu base de datos"""
    
    def __init__(self):
        self.running = False
        self.interval = 30  # segundos
    
    async def process_queue(self):
        """Procesar cola de notificaciones pendientes"""
        db = next(get_db())
        
        try:
            # Obtener notificaciones pendientes de la cola
            pending_notifications = db.execute(text("""
                SELECT 
                    id, valorizacion_id, evento_trigger,
                    estado_anterior, estado_nuevo, empresa_id,
                    monto_total, observaciones
                FROM whatsapp_notification_queue 
                WHERE processed = false
                ORDER BY created_at ASC
                LIMIT 50
            """)).fetchall()
            
            processed_count = 0
            
            for notification in pending_notifications:
                try:
                    # Mapear evento a enum
                    evento_trigger = EventoTrigger(notification.evento_trigger)
                    
                    # Crear notificaciones WhatsApp
                    notifications = await notification_service.create_notification(
                        db=db,
                        valorizacion_id=notification.valorizacion_id,
                        evento_trigger=evento_trigger,
                        estado_actual=notification.estado_nuevo,
                        estado_anterior=notification.estado_anterior,
                        variables_extra={
                            "monto_total": str(notification.monto_total or 0),
                            "observaciones": notification.observaciones or "",
                            "empresa_id": notification.empresa_id
                        }
                    )
                    
                    # Marcar como procesada
                    db.execute(text("""
                        UPDATE whatsapp_notification_queue 
                        SET processed = true, processed_at = NOW(),
                            notifications_created = :count
                        WHERE id = :id
                    """), {
                        "id": notification.id,
                        "count": len(notifications)
                    })
                    
                    processed_count += 1
                    
                except Exception as e:
                    # Log error y marcar como error
                    print(f"❌ Error procesando notificación {notification.id}: {e}")
                    db.execute(text("""
                        UPDATE whatsapp_notification_queue 
                        SET error_message = :error, error_count = error_count + 1
                        WHERE id = :id
                    """), {
                        "id": notification.id,
                        "error": str(e)
                    })
            
            db.commit()
            
            if processed_count > 0:
                print(f"✅ Procesadas {processed_count} notificaciones de cola")
                
        except Exception as e:
            db.rollback()
            print(f"❌ Error procesando cola: {e}")
        finally:
            db.close()
    
    async def start_queue_processor(self):
        """Iniciar procesador en loop continuo"""
        self.running = True
        print("🚀 Iniciando procesador de cola de notificaciones...")
        
        while self.running:
            await self.process_queue()
            await asyncio.sleep(self.interval)
    
    def stop_queue_processor(self):
        """Detener procesador"""
        self.running = False
        print("⏹️  Deteniendo procesador de cola...")

# Uso del procesador
processor = NotificationQueueProcessor()

# Ejecutar como servicio background
async def run_notification_processor():
    await processor.start_queue_processor()

# Ejecutar en script separado
if __name__ == "__main__":
    asyncio.run(run_notification_processor())
```

## Integración con Webhooks

### Webhook Receiver para Tu Sistema

```python
from fastapi import APIRouter, Request, HTTPException, Depends
from app.services.notification_service import notification_service

webhook_router = APIRouter(prefix="/webhooks")

@webhook_router.post("/valorizaciones/status-change")
async def handle_valorizacion_status_change(request: Request):
    """
    Webhook para recibir cambios de estado desde tu sistema
    """
    try:
        payload = await request.json()
        
        # Validar payload
        required_fields = ["valorizacion_id", "estado_nuevo", "empresa_id"]
        for field in required_fields:
            if field not in payload:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Campo requerido: {field}"
                )
        
        # Mapear evento desde tu sistema
        estado_map = {
            "PRESENTADA": "RECIBIDA",
            "EN_REVISION": "EN_REVISION", 
            "OBSERVADA": "OBSERVADA",
            "APROBADA": "APROBADA",
            "ANULADA": "RECHAZADA"
        }
        
        evento = estado_map.get(payload["estado_nuevo"])
        if not evento:
            return {"message": f"Estado {payload['estado_nuevo']} no requiere notificación"}
        
        # Crear notificaciones
        db = next(get_db())
        notifications = await notification_service.create_notification(
            db=db,
            valorizacion_id=payload["valorizacion_id"],
            evento_trigger=EventoTrigger(evento),
            estado_actual=payload["estado_nuevo"],
            estado_anterior=payload.get("estado_anterior"),
            variables_extra={
                "monto_total": str(payload.get("monto_total", 0)),
                "observaciones": payload.get("observaciones", ""),
                "obra_nombre": payload.get("obra_nombre", ""),
                "empresa_razon_social": payload.get("empresa_razon_social", "")
            }
        )
        
        return {
            "message": "Notificaciones creadas exitosamente",
            "notifications_created": len(notifications),
            "valorizacion_id": payload["valorizacion_id"]
        }
        
    except Exception as e:
        print(f"❌ Error en webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Ejemplo de como llamar al webhook desde tu sistema
import httpx

async def notify_whatsapp_system(valorizacion_data: dict):
    """Notificar al sistema de WhatsApp sobre cambio de estado"""
    
    webhook_url = "http://localhost:8000/webhooks/valorizaciones/status-change"
    
    payload = {
        "valorizacion_id": valorizacion_data["id"],
        "estado_anterior": valorizacion_data["estado_anterior"],
        "estado_nuevo": valorizacion_data["estado_nuevo"],
        "empresa_id": valorizacion_data["empresa_id"],
        "monto_total": valorizacion_data["monto_total"],
        "observaciones": valorizacion_data.get("observaciones", ""),
        "obra_nombre": valorizacion_data.get("obra_nombre", ""),
        "empresa_razon_social": valorizacion_data.get("empresa_razon_social", "")
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                webhook_url,
                json=payload,
                timeout=30.0
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Notificaciones creadas: {result['notifications_created']}")
                return result
            else:
                print(f"❌ Error webhook: {response.status_code} - {response.text}")
                return None
                
    except Exception as e:
        print(f"❌ Error llamando webhook: {e}")
        return None
```

## Testing de la Integración

### Test Automatizado de Integración

```python
import pytest
import asyncio
from app.services.notification_service import notification_service
from app.models.whatsapp_notifications import EventoTrigger

class TestNotificationIntegration:
    """Tests para verificar la integración"""
    
    @pytest.fixture
    async def setup_test_data(self):
        """Preparar datos de prueba"""
        db = next(get_db())
        
        # Crear empresa de prueba
        test_empresa = {
            "id": 99999,
            "razon_social": "EMPRESA TEST S.A.C."
        }
        
        # Crear contacto de prueba
        test_contacto = WhatsAppContactosDB(
            empresa_id=99999,
            nombre="Test User",
            telefono="51987654321",
            tipo_contacto="CONTRATISTA", 
            eventos_suscritos='["APROBADA", "OBSERVADA"]',
            activo=True,
            recibe_notificaciones=True
        )
        
        db.add(test_contacto)
        db.commit()
        db.close()
        
        return {"empresa_id": 99999, "contacto_id": test_contacto.id}
    
    async def test_notification_creation(self, setup_test_data):
        """Test creación de notificaciones"""
        db = next(get_db())
        
        # Crear notificación de prueba
        notifications = await notification_service.create_notification(
            db=db,
            valorizacion_id=88888,
            evento_trigger=EventoTrigger.APROBADA,
            estado_actual="APROBADA",
            estado_anterior="EN_REVISION",
            variables_extra={
                "monto_total": "25000.00",
                "observaciones": "Test de integración"
            }
        )
        
        assert len(notifications) > 0
        assert notifications[0]["estado"] == "PENDIENTE"
        
        db.close()
    
    async def test_webhook_integration(self, setup_test_data):
        """Test integración via webhook"""
        import httpx
        
        webhook_payload = {
            "valorizacion_id": 88888,
            "estado_nuevo": "APROBADA",
            "estado_anterior": "EN_REVISION",
            "empresa_id": 99999,
            "monto_total": 25000.00,
            "observaciones": "Test webhook"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8000/webhooks/valorizaciones/status-change",
                json=webhook_payload
            )
        
        assert response.status_code == 200
        result = response.json()
        assert result["notifications_created"] > 0
    
    async def test_decorator_integration(self, setup_test_data):
        """Test integración con decorador"""
        
        @notify_on_status_change
        async def mock_update_status(valorizacion_id, nuevo_estado, **kwargs):
            # Simular tu método existente
            return {
                "valorizacion_id": valorizacion_id,
                "estado_anterior": "EN_REVISION",
                "estado_nuevo": nuevo_estado,
                "empresa_id": kwargs.get("empresa_id"),
                "success": True
            }
        
        # Ejecutar método con decorador
        result = await mock_update_status(
            valorizacion_id=88888,
            nuevo_estado="APROBADA",
            empresa_id=99999,
            monto_total=25000.00
        )
        
        assert result["success"] == True
        # El decorador debería haber creado notificaciones

# Ejecutar tests
pytest.main(["-v", "test_integration.py"])
```

### Test Manual de Extremo a Extremo

```python
async def run_end_to_end_test():
    """Test completo de extremo a extremo"""
    print("🧪 Iniciando test de integración completo...\n")
    
    # 1. Test de configuración
    print("1. Verificando configuración...")
    from app.services.whatsapp_service import whatsapp_service
    
    is_valid, phone, error = whatsapp_service.validate_phone_number("987654321")
    assert is_valid, f"Error validación teléfono: {error}"
    print("   ✅ Validación de teléfonos OK")
    
    # 2. Test de plantillas
    print("2. Verificando plantillas...")
    db = next(get_db())
    plantillas = db.query(WhatsAppPlantillasMensajesDB).filter(
        WhatsAppPlantillasMensajesDB.activo == True
    ).count()
    assert plantillas > 0, "No hay plantillas activas"
    print(f"   ✅ {plantillas} plantillas activas")
    
    # 3. Test de creación de notificaciones
    print("3. Creando notificaciones de prueba...")
    notifications = await notification_service.create_notification(
        db=db,
        valorizacion_id=77777,
        evento_trigger=EventoTrigger.APROBADA,
        estado_actual="APROBADA",
        estado_anterior="EN_REVISION"
    )
    print(f"   ✅ Creadas {len(notifications)} notificaciones")
    
    # 4. Test de métricas
    print("4. Verificando métricas...")
    metrics = await notification_service.get_notification_metrics(db)
    print(f"   ✅ Métricas calculadas: {metrics['totales']['total']} total")
    
    # 5. Test de API REST
    print("5. Probando API REST...")
    import httpx
    
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8000/health")
        assert response.status_code == 200
        health = response.json()
        assert health["status"] == "healthy"
    print("   ✅ API REST funcionando")
    
    db.close()
    print("\n🎉 Test de integración completado exitosamente!")
    print("   🔗 Sistema listo para integración en producción")

# Ejecutar test
await run_end_to_end_test()
```

## Métricas y Monitoreo de la Integración

### Dashboard de Integración

```python
async def get_integration_metrics() -> dict:
    """Obtener métricas específicas de integración"""
    db = next(get_db())
    
    # Métricas de notificaciones por fuente
    from sqlalchemy import func
    
    # Por evento trigger
    eventos_stats = db.query(
        WhatsAppNotificacionesDB.evento_trigger,
        func.count().label('total'),
        func.avg(
            func.julianday(WhatsAppNotificacionesDB.fecha_envio) - 
            func.julianday(WhatsAppNotificacionesDB.created_at)
        ).label('avg_delay_days')
    ).group_by(WhatsAppNotificacionesDB.evento_trigger).all()
    
    # Por empresa
    empresa_stats = db.query(
        WhatsAppContactosDB.empresa_id,
        func.count(WhatsAppNotificacionesDB.id).label('notifications'),
        func.avg(
            case((WhatsAppNotificacionesDB.estado == 'LEIDA', 1), else_=0)
        ).label('read_rate')
    ).join(
        WhatsAppNotificacionesDB,
        WhatsAppContactosDB.id == WhatsAppNotificacionesDB.contacto_id
    ).group_by(WhatsAppContactosDB.empresa_id).all()
    
    # Tiempos de respuesta por tipo
    response_times = db.query(
        WhatsAppNotificacionesDB.evento_trigger,
        func.avg(
            (func.julianday(WhatsAppNotificacionesDB.fecha_entrega) - 
             func.julianday(WhatsAppNotificacionesDB.fecha_envio)) * 24 * 60  # minutos
        ).label('avg_delivery_minutes')
    ).filter(
        WhatsAppNotificacionesDB.fecha_entrega.isnot(None)
    ).group_by(WhatsAppNotificacionesDB.evento_trigger).all()
    
    db.close()
    
    return {
        "eventos": {row.evento_trigger: {
            "total": row.total,
            "avg_delay_days": float(row.avg_delay_days or 0)
        } for row in eventos_stats},
        
        "empresas": {row.empresa_id: {
            "notifications": row.notifications,
            "read_rate": float(row.read_rate or 0)
        } for row in empresa_stats},
        
        "response_times": {row.evento_trigger: 
            float(row.avg_delivery_minutes or 0) 
            for row in response_times}
    }

# Generar reporte de integración
metrics = await get_integration_metrics()
print("📊 Métricas de Integración:")
print(f"   📈 Eventos más frecuentes: {max(metrics['eventos'].items(), key=lambda x: x[1]['total'])}")
print(f"   🏆 Empresa más activa: {max(metrics['empresas'].items(), key=lambda x: x[1]['notifications'])}")
print(f"   ⚡ Tiempo promedio entrega: {sum(metrics['response_times'].values())/len(metrics['response_times']):.1f} min")
```

## Casos de Uso Específicos por Industria

### Integración para Construcción Civil

```python
class ConstruccionIntegration:
    """Integración específica para construcción civil"""
    
    async def handle_valorizacion_progress(
        self,
        valorizacion_id: int,
        progress_percentage: float,
        milestone: str
    ):
        """Manejar progreso de valorización de obra"""
        
        if progress_percentage >= 75 and milestone == "ESTRUCTURA":
            # Notificar progreso significativo
            await notify_valorizacion_change(
                valorizacion_id=valorizacion_id,
                evento_trigger=EventoTrigger.EN_REVISION,
                estado_actual="REVISION_FINAL",
                estado_anterior="EN_PROGRESO",
                variables_extra={
                    "progreso_porcentaje": str(progress_percentage),
                    "hito_actual": milestone,
                    "proxima_fase": "ACABADOS"
                }
            )
    
    async def handle_material_shortage(
        self,
        valorizacion_id: int,
        material_faltante: str,
        impacto_cronograma: int  # días
    ):
        """Manejar falta de materiales que impacta valorización"""
        
        if impacto_cronograma > 7:  # Más de una semana de retraso
            await notify_valorizacion_change(
                valorizacion_id=valorizacion_id,
                evento_trigger=EventoTrigger.OBSERVADA,
                estado_actual="OBSERVADA",
                estado_anterior="EN_REVISION",
                variables_extra={
                    "tipo_observacion": "FALTA_MATERIALES",
                    "material_faltante": material_faltante,
                    "dias_retraso": str(impacto_cronograma),
                    "accion_requerida": "ABASTECIMIENTO_URGENTE"
                }
            )
```

### Integración para Servicios Profesionales

```python
class ServiciosProfesionalesIntegration:
    """Integración para servicios de consultoría e ingeniería"""
    
    async def handle_deliverable_approval(
        self,
        valorizacion_id: int,
        deliverable_type: str,
        client_feedback: str
    ):
        """Manejar aprobación de entregables"""
        
        await notify_valorizacion_change(
            valorizacion_id=valorizacion_id,
            evento_trigger=EventoTrigger.APROBADA,
            estado_actual="APROBADA",
            estado_anterior="REVISION_CLIENTE",
            variables_extra={
                "tipo_entregable": deliverable_type,
                "feedback_cliente": client_feedback,
                "siguiente_entregable": self._get_next_deliverable(deliverable_type)
            }
        )
```

## Mejores Prácticas de Integración

### 1. Gestión de Errores
```python
import logging
from functools import wraps

def handle_integration_errors(func):
    """Decorador para manejar errores de integración"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logging.error(f"Error integración WhatsApp en {func.__name__}: {e}")
            # No fallar tu sistema principal por errores de WhatsApp
            return {"success": False, "error": str(e)}
    return wrapper

@handle_integration_errors
async def your_business_method():
    # Tu lógica de negocio aquí
    await notify_whatsapp_system()  # Puede fallar sin afectar tu sistema
```

### 2. Configuración por Ambiente
```python
from app.core.config import settings

class IntegrationConfig:
    """Configuración de integración por ambiente"""
    
    @property
    def notifications_enabled(self) -> bool:
        return settings.ENVIRONMENT == "production"
    
    @property
    def test_mode(self) -> bool:
        return settings.ENVIRONMENT in ["development", "testing"]
    
    async def create_notification_if_enabled(self, **kwargs):
        if not self.notifications_enabled:
            print(f"[TEST] Would create notification: {kwargs}")
            return
        
        return await notification_service.create_notification(**kwargs)

# Uso
config = IntegrationConfig()
await config.create_notification_if_enabled(
    valorizacion_id=123,
    evento_trigger=EventoTrigger.APROBADA,
    estado_actual="APROBADA"
)
```

### 3. Rate Limiting en Integración
```python
import asyncio
from collections import deque
from datetime import datetime, timedelta

class IntegrationRateLimiter:
    """Rate limiter para evitar spam desde tu sistema"""
    
    def __init__(self, max_requests: int = 10, window_minutes: int = 1):
        self.max_requests = max_requests
        self.window = timedelta(minutes=window_minutes)
        self.requests = deque()
    
    async def check_rate_limit(self) -> bool:
        """Verificar si se puede hacer request"""
        now = datetime.now()
        
        # Limpiar requests antiguos
        while self.requests and self.requests[0] < now - self.window:
            self.requests.popleft()
        
        # Verificar límite
        if len(self.requests) >= self.max_requests:
            return False
        
        # Registrar request
        self.requests.append(now)
        return True
    
    async def wait_if_needed(self):
        """Esperar si se alcanzó el límite"""
        while not await self.check_rate_limit():
            await asyncio.sleep(5)  # Esperar 5 segundos

# Usar en tu integración
rate_limiter = IntegrationRateLimiter(max_requests=5, window_minutes=1)

async def safe_notification_call():
    await rate_limiter.wait_if_needed()
    return await notification_service.create_notification(...)
```

¡Tu integración está completa! 🎉 

## Próximos Pasos

1. **[API Reference](./API_REFERENCE.md)** - Documentación detallada de endpoints
2. **[Manual de Operaciones](./OPERATIONS.md)** - Monitoreo y mantenimiento  
3. **[Guía de Usuario](./USER_GUIDE.md)** - Para contratistas y coordinadores

---

**¿Necesitas ayuda con la integración?** Contacta al equipo técnico en dev-team@empresa.com