# Sistema de Notificaciones WhatsApp - Documentación Técnica

## Resumen del Sistema

Sistema automatizado de notificaciones WhatsApp diseñado para informar a contratistas sobre cambios de estado en sus valorizaciones de construcción, eliminando interrupciones constantes por consultas de estado.

## Arquitectura de Datos

### Tablas Principales

| Tabla | Descripción | Registros Estimados |
|-------|-------------|-------------------|
| `whatsapp_configuracion_horarios` | Configuración de horarios laborables | 2-5 |
| `whatsapp_plantillas_mensajes` | Plantillas personalizables de mensajes | 5-20 |
| `whatsapp_contactos` | Contactos WhatsApp de empresas/coordinadores | 50-500 |
| `whatsapp_notificaciones` | Notificaciones principales | 1,000-50,000/mes |
| `whatsapp_historial_notificaciones` | Historial de cambios de estado | 3,000-150,000/mes |
| `whatsapp_metricas_diarias` | Métricas agregadas por día | 365/año |

### Flujo de Datos

```
Valorización → Cambio Estado → Trigger → Notificación → Queue → WhatsApp API
                    ↓                        ↓              ↓
               Plantilla → Render Mensaje → Contactos → Horarios
                    ↓                        ↓              ↓
               Variables → Mensaje Final → Envío → Tracking
```

## Diseño Optimizado

### 1. Índices de Rendimiento

```sql
-- Búsquedas frecuentes optimizadas
idx_whatsapp_notificaciones_envio_pendiente (estado, fecha_programada, prioridad)
idx_whatsapp_notificaciones_valorizacion (valorizacion_id)
idx_whatsapp_contactos_empresa (empresa_id)
idx_whatsapp_plantillas_evento (evento_trigger, estado_valorizacion)
```

**Beneficios:**
- Consultas de notificaciones pendientes: < 10ms
- Búsqueda por valorización: < 5ms
- Filtros por empresa/evento: < 15ms

### 2. Estados y Transiciones

```
PENDIENTE → PROGRAMADA → ENVIANDO → ENVIADA → ENTREGADA → LEIDA
    ↓           ↓           ↓          ↓          ↓
  ERROR ← ─── ─── ────── ─── ── ────── ── ── ── ──
    ↓
CANCELADA/EXPIRADA
```

### 3. Gestión de Horarios

- **Horario Estándar:** L-V 8:00-18:00
- **Emergencias:** 24/7 para notificaciones críticas
- **Configuración por contacto:** Flexibilidad individual
- **Zona horaria:** America/Lima (UTC-5)

### 4. Sistema de Reintentos

| Intento | Intervalo | Prioridad |
|---------|-----------|-----------|
| 1       | Inmediato | Alta: 15min, Media: 30min, Baja: 1h |
| 2       | 30min     | Alta: 15min, Media: 1h, Baja: 2h |
| 3       | 1h        | Alta: 30min, Media: 2h, Baja: 4h |

## Plantillas de Mensajes

### Variables Disponibles

```json
{
  "obra_nombre": "Construcción Edificio Central",
  "empresa_razon_social": "CONSTRUCTORA ABC S.A.C.",
  "valorizacion_numero": "003",
  "valorizacion_periodo": "2025-08",
  "estado_anterior": "EN_REVISION", 
  "estado_actual": "APROBADA",
  "fecha_cambio": "2025-08-23 14:30:00",
  "monto_total": "125,450.00",
  "observaciones": "Valorización aprobada sin observaciones"
}
```

### Ejemplo de Plantilla

```
✅ Valorización #{valorizacion_numero} APROBADA - {obra_nombre}

Felicitaciones {empresa_razon_social},
Su valorización del período {valorizacion_periodo} ha sido APROBADA.

Monto aprobado: S/ {monto_total}
Fecha: {fecha_cambio}

La valorización será procesada para pago según términos contractuales.

Sistema de Valorizaciones
```

## Métricas y Monitoreo

### KPIs Principales

1. **Tasa de Éxito:** > 95%
2. **Tiempo Promedio de Entrega:** < 30 segundos
3. **Tasa de Lectura:** > 80%
4. **Disponibilidad del Sistema:** > 99.5%

### Dashboard de Métricas

- **Notificaciones por día/hora**
- **Estados por tipo de evento** 
- **Rendimiento por empresa**
- **Errores y reintentos**
- **Tiempos de respuesta**

## Casos de Uso Principales

### 1. Valorización Recibida
```
Trigger: Estado BORRADOR → PRESENTADA
Destinatario: Contratista
Prioridad: Media (5)
Timing: Inmediato
```

### 2. Valorización Observada
```
Trigger: Estado EN_REVISION → OBSERVADA  
Destinatario: Contratista
Prioridad: Alta (1)
Timing: Inmediato
Acción: Requiere corrección
```

### 3. Valorización Aprobada
```
Trigger: Estado EN_REVISION → APROBADA
Destinatario: Contratista + Coordinador
Prioridad: Media-Alta (3)  
Timing: Inmediato
Acción: Procesar pago
```

## Configuración de Contactos

### Por Tipo de Contacto

**Contratistas:**
- Reciben notificaciones de sus valorizaciones
- Configuración de horarios respetada
- Múltiples contactos por empresa (principal + secundarios)

**Coordinadores Internos:**
- Reciben resúmenes y alertas importantes
- Pueden recibir notificaciones 24/7
- Configuración granular por tipo de evento

### Validaciones

- Teléfonos: Mínimo 9 dígitos, solo números
- Eventos suscritos: Array JSON de eventos válidos
- Estados: Contactos activos y verificados

## Seguridad y Cumplimiento

### Protección de Datos
- **Encriptación:** Mensajes y datos sensibles
- **Auditoría:** Trazabilidad completa de cambios
- **Retención:** Datos históricos por 2 años
- **Acceso:** Control basado en roles

### Validaciones de Negocio
- **Horarios:** Respeto de días laborables y horarios
- **Duplicados:** Prevención de notificaciones duplicadas
- **Estados:** Validación de transiciones de estado válidas
- **Límites:** Máximo 3 reintentos por notificación

## Rendimiento Esperado

### Volúmenes de Datos
- **100 valorizaciones/día promedio**
- **300-500 notificaciones/día**
- **95% tasa de entrega exitosa**
- **< 1% tasa de error**

### Tiempos de Respuesta
- **Generación de notificación:** < 100ms
- **Renderizado de plantilla:** < 50ms  
- **Cola de envío:** < 1 segundo
- **Entrega WhatsApp:** < 30 segundos

## Comandos de Instalación

### 1. Ejecutar Migración
```bash
cd sql/
python migrate_whatsapp_notifications.py
```

### 2. Verificar Instalación
```sql
-- Verificar tablas creadas
SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'whatsapp_%';

-- Verificar datos iniciales
SELECT * FROM whatsapp_configuracion_horarios;
SELECT codigo, nombre, evento_trigger FROM whatsapp_plantillas_mensajes;
```

### 3. Configurar Primer Contacto
```sql
INSERT INTO whatsapp_contactos (
    empresa_id, nombre, telefono, tipo_contacto, es_principal
) VALUES (
    1, 'Juan Pérez', '987654321', 'CONTRATISTA', TRUE
);
```

## Próximos Desarrollos

### Fase 2 - Funcionalidades Avanzadas
- [ ] **API REST completa** para gestión de plantillas
- [ ] **Worker background** para procesamiento de cola
- [ ] **Dashboard web** para monitoreo en tiempo real
- [ ] **Integración WhatsApp Business API** 
- [ ] **Templates WhatsApp oficiales**

### Fase 3 - Inteligencia
- [ ] **ML para optimización de horarios** de envío
- [ ] **Análisis de patrones** de lectura por empresa
- [ ] **Predicción de resolución** de observaciones
- [ ] **Alertas proactivas** por demoras

### Fase 4 - Integración
- [ ] **Notificaciones SMS** como backup
- [ ] **Email notifications** para documentos
- [ ] **Push notifications** para app móvil
- [ ] **Integración con sistemas ERP** externos

## Contacto y Soporte

Para dudas sobre implementación o configuración del sistema de notificaciones WhatsApp, consultar con el equipo de desarrollo del sistema de valorizaciones.

---

**Fecha de creación:** 2025-08-23  
**Versión:** 1.0  
**Base de datos:** Turso (SQLite)  
**Compatibilidad:** Sistema de Valorizaciones v2.0+