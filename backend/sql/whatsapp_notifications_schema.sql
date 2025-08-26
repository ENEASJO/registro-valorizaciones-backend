-- =====================================================================
-- SCHEMA PARA SISTEMA DE NOTIFICACIONES WHATSAPP
-- Base de datos: Turso (SQLite)
-- Fecha: 2025-08-23
-- Descripción: Sistema automatizado de notificaciones WhatsApp para 
--              cambios de estado en valorizaciones de construcción
-- =====================================================================

-- =====================================================================
-- 1. TABLA DE CONFIGURACIÓN DE HORARIOS LABORABLES
-- =====================================================================
CREATE TABLE IF NOT EXISTS whatsapp_configuracion_horarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre VARCHAR(100) NOT NULL UNIQUE,
    descripcion TEXT,
    
    -- Configuración de días laborables (JSON array)
    dias_laborables TEXT NOT NULL DEFAULT '["LUNES","MARTES","MIERCOLES","JUEVES","VIERNES"]',
    
    -- Horarios de envío
    hora_inicio_envios TIME NOT NULL DEFAULT '08:00:00',
    hora_fin_envios TIME NOT NULL DEFAULT '18:00:00',
    
    -- Configuración de zona horaria
    zona_horaria VARCHAR(50) NOT NULL DEFAULT 'America/Lima',
    
    -- Configuración de reintentos
    reintentos_maximos INTEGER NOT NULL DEFAULT 3,
    intervalo_reintento_minutos INTEGER NOT NULL DEFAULT 30,
    
    -- Estados
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    
    -- Auditoría
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER,
    updated_by INTEGER
);

-- Trigger para actualizar updated_at automáticamente
CREATE TRIGGER IF NOT EXISTS trigger_update_whatsapp_configuracion_horarios
    AFTER UPDATE ON whatsapp_configuracion_horarios
    FOR EACH ROW
BEGIN
    UPDATE whatsapp_configuracion_horarios 
    SET updated_at = CURRENT_TIMESTAMP 
    WHERE id = NEW.id;
END;

-- =====================================================================
-- 2. TABLA DE PLANTILLAS DE MENSAJES
-- =====================================================================
CREATE TABLE IF NOT EXISTS whatsapp_plantillas_mensajes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo VARCHAR(50) NOT NULL UNIQUE,
    nombre VARCHAR(200) NOT NULL,
    descripcion TEXT,
    
    -- Configuración de eventos
    evento_trigger VARCHAR(50) NOT NULL,
    estado_valorizacion VARCHAR(50) NOT NULL,
    
    -- Configuración de destinatarios
    tipo_destinatario VARCHAR(50) NOT NULL, -- 'CONTRATISTA', 'COORDINADOR_INTERNO'
    
    -- Contenido del mensaje
    asunto VARCHAR(255),
    mensaje_texto TEXT NOT NULL,
    mensaje_html TEXT,
    
    -- Variables disponibles (JSON array de strings)
    variables_disponibles TEXT DEFAULT '["obra_nombre","empresa_razon_social","valorizacion_numero","valorizacion_periodo","estado_anterior","estado_actual","fecha_cambio","monto_total","observaciones"]',
    
    -- Configuración de envío
    es_inmediato BOOLEAN NOT NULL DEFAULT TRUE,
    requiere_confirmacion BOOLEAN NOT NULL DEFAULT FALSE,
    prioridad INTEGER NOT NULL DEFAULT 5, -- 1=Alta, 5=Media, 10=Baja
    
    -- Estados
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    
    -- Auditoría
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER,
    updated_by INTEGER,
    
    -- Constraints
    CONSTRAINT check_evento_valido CHECK (
        evento_trigger IN ('RECIBIDA', 'EN_REVISION', 'OBSERVADA', 'APROBADA', 'RECHAZADA')
    ),
    CONSTRAINT check_estado_valido CHECK (
        estado_valorizacion IN ('BORRADOR', 'PRESENTADA', 'EN_REVISION', 'OBSERVADA', 'APROBADA', 'PAGADA', 'ANULADA')
    ),
    CONSTRAINT check_destinatario_valido CHECK (
        tipo_destinatario IN ('CONTRATISTA', 'COORDINADOR_INTERNO', 'AMBOS')
    ),
    CONSTRAINT check_prioridad_valida CHECK (
        prioridad BETWEEN 1 AND 10
    )
);

-- Trigger para actualizar updated_at
CREATE TRIGGER IF NOT EXISTS trigger_update_whatsapp_plantillas_mensajes
    AFTER UPDATE ON whatsapp_plantillas_mensajes
    FOR EACH ROW
BEGIN
    UPDATE whatsapp_plantillas_mensajes 
    SET updated_at = CURRENT_TIMESTAMP 
    WHERE id = NEW.id;
END;

-- =====================================================================
-- 3. TABLA DE CONTACTOS WHATSAPP
-- =====================================================================
CREATE TABLE IF NOT EXISTS whatsapp_contactos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Relaciones con entidades existentes
    empresa_id INTEGER,
    obra_id INTEGER,
    usuario_id INTEGER, -- Para coordinadores internos
    
    -- Datos del contacto
    nombre VARCHAR(255) NOT NULL,
    cargo VARCHAR(100),
    telefono VARCHAR(20) NOT NULL,
    email VARCHAR(100),
    
    -- Configuración del contacto
    tipo_contacto VARCHAR(50) NOT NULL, -- 'CONTRATISTA', 'COORDINADOR_INTERNO'
    es_principal BOOLEAN NOT NULL DEFAULT FALSE,
    
    -- Configuración de notificaciones
    recibe_notificaciones BOOLEAN NOT NULL DEFAULT TRUE,
    eventos_suscritos TEXT DEFAULT '["RECIBIDA","EN_REVISION","OBSERVADA","APROBADA","RECHAZADA"]', -- JSON array
    horario_configuracion_id INTEGER DEFAULT 1,
    
    -- Estados
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    verificado BOOLEAN NOT NULL DEFAULT FALSE,
    
    -- Auditoría
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER,
    updated_by INTEGER,
    
    -- Foreign Keys
    FOREIGN KEY (empresa_id) REFERENCES empresas(id) ON DELETE CASCADE,
    FOREIGN KEY (horario_configuracion_id) REFERENCES whatsapp_configuracion_horarios(id),
    
    -- Constraints
    CONSTRAINT check_tipo_contacto_valido CHECK (
        tipo_contacto IN ('CONTRATISTA', 'COORDINADOR_INTERNO')
    ),
    CONSTRAINT check_telefono_formato CHECK (
        LENGTH(telefono) >= 9 AND telefono GLOB '[0-9]*'
    )
);

-- Trigger para actualizar updated_at
CREATE TRIGGER IF NOT EXISTS trigger_update_whatsapp_contactos
    AFTER UPDATE ON whatsapp_contactos
    FOR EACH ROW
BEGIN
    UPDATE whatsapp_contactos 
    SET updated_at = CURRENT_TIMESTAMP 
    WHERE id = NEW.id;
END;

-- =====================================================================
-- 4. TABLA PRINCIPAL DE NOTIFICACIONES WHATSAPP
-- =====================================================================
CREATE TABLE IF NOT EXISTS whatsapp_notificaciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo_notificacion VARCHAR(50) NOT NULL UNIQUE,
    
    -- Relaciones
    valorizacion_id INTEGER NOT NULL,
    plantilla_id INTEGER NOT NULL,
    contacto_id INTEGER NOT NULL,
    horario_configuracion_id INTEGER DEFAULT 1,
    
    -- Información del evento
    evento_trigger VARCHAR(50) NOT NULL,
    estado_anterior VARCHAR(50),
    estado_actual VARCHAR(50) NOT NULL,
    fecha_evento TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Contenido del mensaje (renderizado)
    asunto_renderizado VARCHAR(500),
    mensaje_renderizado TEXT NOT NULL,
    variables_utilizadas TEXT, -- JSON con variables y valores usados
    
    -- Configuración de envío
    tipo_envio VARCHAR(20) NOT NULL DEFAULT 'INMEDIATO', -- 'INMEDIATO', 'PROGRAMADO'
    fecha_programada TIMESTAMP,
    prioridad INTEGER NOT NULL DEFAULT 5,
    
    -- Estado de la notificación
    estado VARCHAR(20) NOT NULL DEFAULT 'PENDIENTE',
    fecha_cambio_estado TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Información de envío
    fecha_envio TIMESTAMP,
    fecha_entrega TIMESTAMP,
    fecha_lectura TIMESTAMP,
    
    -- Manejo de errores y reintentos
    intentos_envio INTEGER NOT NULL DEFAULT 0,
    max_reintentos INTEGER NOT NULL DEFAULT 3,
    ultimo_error TEXT,
    fecha_ultimo_error TIMESTAMP,
    
    -- Información técnica WhatsApp
    whatsapp_message_id VARCHAR(100),
    whatsapp_status VARCHAR(50),
    whatsapp_timestamp TIMESTAMP,
    metadata_whatsapp TEXT, -- JSON con información adicional de WhatsApp
    
    -- Auditoría
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER,
    
    -- Foreign Keys
    FOREIGN KEY (plantilla_id) REFERENCES whatsapp_plantillas_mensajes(id),
    FOREIGN KEY (contacto_id) REFERENCES whatsapp_contactos(id),
    FOREIGN KEY (horario_configuracion_id) REFERENCES whatsapp_configuracion_horarios(id),
    
    -- Constraints
    CONSTRAINT check_evento_trigger_valido CHECK (
        evento_trigger IN ('RECIBIDA', 'EN_REVISION', 'OBSERVADA', 'APROBADA', 'RECHAZADA')
    ),
    CONSTRAINT check_tipo_envio_valido CHECK (
        tipo_envio IN ('INMEDIATO', 'PROGRAMADO')
    ),
    CONSTRAINT check_estado_notificacion_valido CHECK (
        estado IN ('PENDIENTE', 'PROGRAMADA', 'ENVIANDO', 'ENVIADA', 'ENTREGADA', 'LEIDA', 'ERROR', 'CANCELADA', 'EXPIRADA')
    ),
    CONSTRAINT check_prioridad_valida CHECK (
        prioridad BETWEEN 1 AND 10
    ),
    CONSTRAINT check_intentos_validos CHECK (
        intentos_envio >= 0 AND intentos_envio <= max_reintentos
    )
);

-- Trigger para actualizar updated_at
CREATE TRIGGER IF NOT EXISTS trigger_update_whatsapp_notificaciones
    AFTER UPDATE ON whatsapp_notificaciones
    FOR EACH ROW
BEGIN
    UPDATE whatsapp_notificaciones 
    SET updated_at = CURRENT_TIMESTAMP,
        fecha_cambio_estado = CASE 
            WHEN NEW.estado != OLD.estado THEN CURRENT_TIMESTAMP 
            ELSE OLD.fecha_cambio_estado 
        END
    WHERE id = NEW.id;
END;

-- =====================================================================
-- 5. TABLA DE HISTORIAL DE NOTIFICACIONES
-- =====================================================================
CREATE TABLE IF NOT EXISTS whatsapp_historial_notificaciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    notificacion_id INTEGER NOT NULL,
    
    -- Información del cambio
    estado_anterior VARCHAR(20),
    estado_nuevo VARCHAR(20) NOT NULL,
    fecha_cambio TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Detalles del cambio
    motivo_cambio VARCHAR(100),
    descripcion_cambio TEXT,
    codigo_error VARCHAR(50),
    mensaje_error TEXT,
    
    -- Información técnica
    metadata_cambio TEXT, -- JSON con información adicional
    
    -- Auditoría
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER,
    
    -- Foreign Keys
    FOREIGN KEY (notificacion_id) REFERENCES whatsapp_notificaciones(id) ON DELETE CASCADE
);

-- =====================================================================
-- 6. TABLA DE ESTADÍSTICAS Y MÉTRICAS
-- =====================================================================
CREATE TABLE IF NOT EXISTS whatsapp_metricas_diarias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha_metrica DATE NOT NULL,
    
    -- Contadores por estado
    total_pendientes INTEGER NOT NULL DEFAULT 0,
    total_enviadas INTEGER NOT NULL DEFAULT 0,
    total_entregadas INTEGER NOT NULL DEFAULT 0,
    total_leidas INTEGER NOT NULL DEFAULT 0,
    total_errores INTEGER NOT NULL DEFAULT 0,
    total_canceladas INTEGER NOT NULL DEFAULT 0,
    
    -- Contadores por tipo de evento
    total_recibidas INTEGER NOT NULL DEFAULT 0,
    total_en_revision INTEGER NOT NULL DEFAULT 0,
    total_observadas INTEGER NOT NULL DEFAULT 0,
    total_aprobadas INTEGER NOT NULL DEFAULT 0,
    total_rechazadas INTEGER NOT NULL DEFAULT 0,
    
    -- Métricas de rendimiento
    tiempo_promedio_envio_segundos INTEGER,
    tiempo_promedio_entrega_segundos INTEGER,
    tasa_exito_porcentaje DECIMAL(5,2),
    tasa_error_porcentaje DECIMAL(5,2),
    
    -- Auditoría
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Unique constraint para evitar duplicados por fecha
    UNIQUE(fecha_metrica)
);

-- =====================================================================
-- ÍNDICES PARA OPTIMIZACIÓN DE CONSULTAS
-- =====================================================================

-- Índices para whatsapp_notificaciones (tabla principal)
CREATE INDEX IF NOT EXISTS idx_whatsapp_notificaciones_valorizacion ON whatsapp_notificaciones(valorizacion_id);
CREATE INDEX IF NOT EXISTS idx_whatsapp_notificaciones_estado ON whatsapp_notificaciones(estado);
CREATE INDEX IF NOT EXISTS idx_whatsapp_notificaciones_fecha_evento ON whatsapp_notificaciones(fecha_evento);
CREATE INDEX IF NOT EXISTS idx_whatsapp_notificaciones_fecha_programada ON whatsapp_notificaciones(fecha_programada);
CREATE INDEX IF NOT EXISTS idx_whatsapp_notificaciones_contacto ON whatsapp_notificaciones(contacto_id);
CREATE INDEX IF NOT EXISTS idx_whatsapp_notificaciones_prioridad ON whatsapp_notificaciones(prioridad);
CREATE INDEX IF NOT EXISTS idx_whatsapp_notificaciones_codigo ON whatsapp_notificaciones(codigo_notificacion);

-- Índice compuesto para consultas de notificaciones pendientes/programadas
CREATE INDEX IF NOT EXISTS idx_whatsapp_notificaciones_envio_pendiente 
ON whatsapp_notificaciones(estado, fecha_programada, prioridad) 
WHERE estado IN ('PENDIENTE', 'PROGRAMADA');

-- Índices para whatsapp_contactos
CREATE INDEX IF NOT EXISTS idx_whatsapp_contactos_empresa ON whatsapp_contactos(empresa_id);
CREATE INDEX IF NOT EXISTS idx_whatsapp_contactos_obra ON whatsapp_contactos(obra_id);
CREATE INDEX IF NOT EXISTS idx_whatsapp_contactos_tipo ON whatsapp_contactos(tipo_contacto);
CREATE INDEX IF NOT EXISTS idx_whatsapp_contactos_activo ON whatsapp_contactos(activo, recibe_notificaciones);
CREATE INDEX IF NOT EXISTS idx_whatsapp_contactos_telefono ON whatsapp_contactos(telefono);

-- Índices para whatsapp_plantillas_mensajes
CREATE INDEX IF NOT EXISTS idx_whatsapp_plantillas_evento ON whatsapp_plantillas_mensajes(evento_trigger, estado_valorizacion);
CREATE INDEX IF NOT EXISTS idx_whatsapp_plantillas_activo ON whatsapp_plantillas_mensajes(activo);
CREATE INDEX IF NOT EXISTS idx_whatsapp_plantillas_destinatario ON whatsapp_plantillas_mensajes(tipo_destinatario);

-- Índices para whatsapp_historial_notificaciones
CREATE INDEX IF NOT EXISTS idx_whatsapp_historial_notificacion ON whatsapp_historial_notificaciones(notificacion_id);
CREATE INDEX IF NOT EXISTS idx_whatsapp_historial_fecha ON whatsapp_historial_notificaciones(fecha_cambio);

-- Índices para whatsapp_metricas_diarias
CREATE INDEX IF NOT EXISTS idx_whatsapp_metricas_fecha ON whatsapp_metricas_diarias(fecha_metrica);

-- =====================================================================
-- DATOS INICIALES - CONFIGURACIÓN DE HORARIOS
-- =====================================================================
INSERT OR IGNORE INTO whatsapp_configuracion_horarios (
    id, nombre, descripcion, dias_laborables, hora_inicio_envios, hora_fin_envios,
    zona_horaria, reintentos_maximos, intervalo_reintento_minutos, activo
) VALUES (
    1, 
    'Horario Estándar', 
    'Horario estándar de oficina para envío de notificaciones WhatsApp',
    '["LUNES","MARTES","MIERCOLES","JUEVES","VIERNES"]',
    '08:00:00',
    '18:00:00',
    'America/Lima',
    3,
    30,
    TRUE
);

INSERT OR IGNORE INTO whatsapp_configuracion_horarios (
    id, nombre, descripcion, dias_laborables, hora_inicio_envios, hora_fin_envios,
    zona_horaria, reintentos_maximos, intervalo_reintento_minutos, activo
) VALUES (
    2, 
    'Emergencias 24/7', 
    'Configuración para notificaciones de emergencia sin restricciones de horario',
    '["LUNES","MARTES","MIERCOLES","JUEVES","VIERNES","SABADO","DOMINGO"]',
    '00:00:00',
    '23:59:59',
    'America/Lima',
    5,
    15,
    TRUE
);

-- =====================================================================
-- DATOS INICIALES - PLANTILLAS DE MENSAJES
-- =====================================================================

-- Plantilla para valorización recibida
INSERT OR IGNORE INTO whatsapp_plantillas_mensajes (
    codigo, nombre, descripcion, evento_trigger, estado_valorizacion, tipo_destinatario,
    asunto, mensaje_texto, variables_disponibles, es_inmediato, prioridad, activo
) VALUES (
    'VAL_RECIBIDA_CONTRATISTA',
    'Valorización Recibida - Notificación a Contratista',
    'Notifica al contratista que su valorización fue recibida y está en proceso',
    'RECIBIDA',
    'PRESENTADA',
    'CONTRATISTA',
    'Valorización #{valorizacion_numero} Recibida - {obra_nombre}',
    'Estimado/a {empresa_razon_social},

Su valorización #{valorizacion_numero} correspondiente al período {valorizacion_periodo} de la obra "{obra_nombre}" ha sido RECIBIDA exitosamente.

Estado: {estado_actual}
Monto: S/ {monto_total}
Fecha de recepción: {fecha_cambio}

La valorización entrará en proceso de revisión. Le mantendremos informado sobre cualquier cambio de estado.

Saludos cordiales,
Sistema de Valorizaciones',
    '["obra_nombre","empresa_razon_social","valorizacion_numero","valorizacion_periodo","estado_actual","fecha_cambio","monto_total"]',
    TRUE,
    5,
    TRUE
);

-- Plantilla para valorización en revisión
INSERT OR IGNORE INTO whatsapp_plantillas_mensajes (
    codigo, nombre, descripcion, evento_trigger, estado_valorizacion, tipo_destinatario,
    asunto, mensaje_texto, variables_disponibles, es_inmediato, prioridad, activo
) VALUES (
    'VAL_EN_REVISION_CONTRATISTA',
    'Valorización en Revisión - Notificación a Contratista',
    'Notifica que la valorización está siendo revisada por el equipo técnico',
    'EN_REVISION',
    'EN_REVISION',
    'CONTRATISTA',
    'Valorización #{valorizacion_numero} en Revisión - {obra_nombre}',
    'Estimado/a {empresa_razon_social},

Su valorización #{valorizacion_numero} del período {valorizacion_periodo} está siendo revisada por nuestro equipo técnico.

Obra: {obra_nombre}
Estado actual: {estado_actual}
Monto: S/ {monto_total}
Fecha de inicio de revisión: {fecha_cambio}

El proceso de revisión puede tomar entre 3 a 5 días hábiles. Le notificaremos cualquier observación o cuando la revisión esté completa.

Saludos cordiales,
Sistema de Valorizaciones',
    '["obra_nombre","empresa_razon_social","valorizacion_numero","valorizacion_periodo","estado_actual","fecha_cambio","monto_total"]',
    TRUE,
    5,
    TRUE
);

-- Plantilla para valorización observada
INSERT OR IGNORE INTO whatsapp_plantillas_mensajes (
    codigo, nombre, descripcion, evento_trigger, estado_valorizacion, tipo_destinatario,
    asunto, mensaje_texto, variables_disponibles, es_inmediato, prioridad, activo
) VALUES (
    'VAL_OBSERVADA_CONTRATISTA',
    'Valorización Observada - Notificación a Contratista',
    'Notifica que la valorización tiene observaciones que deben ser subsanadas',
    'OBSERVADA',
    'OBSERVADA',
    'CONTRATISTA',
    '🔴 ACCIÓN REQUERIDA - Valorización #{valorizacion_numero} Observada - {obra_nombre}',
    'Estimado/a {empresa_razon_social},

Su valorización #{valorizacion_numero} del período {valorizacion_periodo} presenta observaciones que requieren ser subsanadas.

Obra: {obra_nombre}
Estado: {estado_actual}
Monto: S/ {monto_total}
Fecha de observación: {fecha_cambio}

OBSERVACIONES:
{observaciones}

Por favor, subsane las observaciones y presente nuevamente la valorización corregida a la brevedad posible.

Para consultas o aclaraciones, comuníquese con el área técnica.

Saludos cordiales,
Sistema de Valorizaciones',
    '["obra_nombre","empresa_razon_social","valorizacion_numero","valorizacion_periodo","estado_actual","fecha_cambio","monto_total","observaciones"]',
    TRUE,
    1,
    TRUE
);

-- Plantilla para valorización aprobada
INSERT OR IGNORE INTO whatsapp_plantillas_mensajes (
    codigo, nombre, descripcion, evento_trigger, estado_valorizacion, tipo_destinatario,
    asunto, mensaje_texto, variables_disponibles, es_inmediato, prioridad, activo
) VALUES (
    'VAL_APROBADA_CONTRATISTA',
    'Valorización Aprobada - Notificación a Contratista',
    'Notifica la aprobación de la valorización y próximos pasos para el pago',
    'APROBADA',
    'APROBADA',
    'CONTRATISTA',
    '✅ Valorización #{valorizacion_numero} APROBADA - {obra_nombre}',
    'Felicitaciones {empresa_razon_social},

Su valorización #{valorizacion_numero} correspondiente al período {valorizacion_periodo} ha sido APROBADA.

Obra: {obra_nombre}
Estado: {estado_actual}
Monto aprobado: S/ {monto_total}
Fecha de aprobación: {fecha_cambio}

La valorización aprobada será procesada para pago según los términos contractuales. En breve recibirá información sobre el cronograma de pagos.

¡Gracias por su trabajo en este proyecto!

Saludos cordiales,
Sistema de Valorizaciones',
    '["obra_nombre","empresa_razon_social","valorizacion_numero","valorizacion_periodo","estado_actual","fecha_cambio","monto_total"]',
    TRUE,
    3,
    TRUE
);

-- Plantilla para valorización rechazada
INSERT OR IGNORE INTO whatsapp_plantillas_mensajes (
    codigo, nombre, descripcion, evento_trigger, estado_valorizacion, tipo_destinatario,
    asunto, mensaje_texto, variables_disponibles, es_inmediato, prioridad, activo
) VALUES (
    'VAL_RECHAZADA_CONTRATISTA',
    'Valorización Rechazada - Notificación a Contratista',
    'Notifica el rechazo de la valorización con motivos específicos',
    'RECHAZADA',
    'ANULADA',
    'CONTRATISTA',
    '❌ Valorización #{valorizacion_numero} RECHAZADA - {obra_nombre}',
    'Estimado/a {empresa_razon_social},

Su valorización #{valorizacion_numero} del período {valorizacion_periodo} ha sido RECHAZADA.

Obra: {obra_nombre}
Estado: {estado_actual}
Monto: S/ {monto_total}
Fecha de rechazo: {fecha_cambio}

MOTIVOS DEL RECHAZO:
{observaciones}

Por favor, revise los motivos del rechazo, corrija los aspectos señalados y presente una nueva valorización si corresponde.

Para mayor información y aclaraciones, comuníquese con el área técnica.

Saludos cordiales,
Sistema de Valorizaciones',
    '["obra_nombre","empresa_razon_social","valorizacion_numero","valorizacion_periodo","estado_actual","fecha_cambio","monto_total","observaciones"]',
    TRUE,
    1,
    TRUE
);

-- =====================================================================
-- VISTAS PARA CONSULTAS FRECUENTES
-- =====================================================================

-- Vista para notificaciones pendientes de envío
CREATE VIEW IF NOT EXISTS v_notificaciones_pendientes AS
SELECT 
    n.id,
    n.codigo_notificacion,
    n.valorizacion_id,
    n.evento_trigger,
    n.estado_actual,
    n.mensaje_renderizado,
    n.fecha_programada,
    n.prioridad,
    n.intentos_envio,
    n.max_reintentos,
    c.nombre AS contacto_nombre,
    c.telefono AS contacto_telefono,
    c.tipo_contacto,
    p.nombre AS plantilla_nombre,
    h.zona_horaria,
    h.hora_inicio_envios,
    h.hora_fin_envios,
    h.dias_laborables
FROM whatsapp_notificaciones n
INNER JOIN whatsapp_contactos c ON n.contacto_id = c.id
INNER JOIN whatsapp_plantillas_mensajes p ON n.plantilla_id = p.id
INNER JOIN whatsapp_configuracion_horarios h ON n.horario_configuracion_id = h.id
WHERE n.estado IN ('PENDIENTE', 'PROGRAMADA')
    AND c.activo = TRUE
    AND c.recibe_notificaciones = TRUE
    AND n.intentos_envio < n.max_reintentos
ORDER BY n.prioridad ASC, n.fecha_programada ASC;

-- Vista para estadísticas de notificaciones
CREATE VIEW IF NOT EXISTS v_estadisticas_notificaciones AS
SELECT 
    DATE(n.created_at) as fecha,
    COUNT(*) as total_notificaciones,
    COUNT(CASE WHEN n.estado = 'ENVIADA' THEN 1 END) as total_enviadas,
    COUNT(CASE WHEN n.estado = 'ENTREGADA' THEN 1 END) as total_entregadas,
    COUNT(CASE WHEN n.estado = 'LEIDA' THEN 1 END) as total_leidas,
    COUNT(CASE WHEN n.estado = 'ERROR' THEN 1 END) as total_errores,
    ROUND(
        (COUNT(CASE WHEN n.estado IN ('ENVIADA', 'ENTREGADA', 'LEIDA') THEN 1 END) * 100.0) / COUNT(*), 
        2
    ) as tasa_exito_porcentaje
FROM whatsapp_notificaciones n
GROUP BY DATE(n.created_at)
ORDER BY fecha DESC;

-- Vista para resumen por empresa
CREATE VIEW IF NOT EXISTS v_resumen_notificaciones_empresa AS
SELECT 
    c.empresa_id,
    COUNT(n.id) as total_notificaciones,
    COUNT(CASE WHEN n.estado = 'ENVIADA' THEN 1 END) as enviadas,
    COUNT(CASE WHEN n.estado = 'ENTREGADA' THEN 1 END) as entregadas,
    COUNT(CASE WHEN n.estado = 'LEIDA' THEN 1 END) as leidas,
    COUNT(CASE WHEN n.estado = 'ERROR' THEN 1 END) as errores,
    MAX(n.created_at) as ultima_notificacion
FROM whatsapp_notificaciones n
INNER JOIN whatsapp_contactos c ON n.contacto_id = c.id
WHERE c.tipo_contacto = 'CONTRATISTA'
GROUP BY c.empresa_id;

-- =====================================================================
-- TRIGGERS ADICIONALES PARA LÓGICA DE NEGOCIO
-- =====================================================================

-- Trigger para generar código único de notificación
CREATE TRIGGER IF NOT EXISTS trigger_generate_codigo_notificacion
    AFTER INSERT ON whatsapp_notificaciones
    FOR EACH ROW
    WHEN NEW.codigo_notificacion IS NULL OR NEW.codigo_notificacion = ''
BEGIN
    UPDATE whatsapp_notificaciones 
    SET codigo_notificacion = 'WA-' || strftime('%Y%m%d', 'now') || '-' || printf('%06d', NEW.id)
    WHERE id = NEW.id;
END;

-- Trigger para crear historial automáticamente al cambiar estado
CREATE TRIGGER IF NOT EXISTS trigger_crear_historial_estado
    AFTER UPDATE OF estado ON whatsapp_notificaciones
    FOR EACH ROW
    WHEN OLD.estado != NEW.estado
BEGIN
    INSERT INTO whatsapp_historial_notificaciones (
        notificacion_id, estado_anterior, estado_nuevo, motivo_cambio
    ) VALUES (
        NEW.id, OLD.estado, NEW.estado, 'Cambio automático de estado'
    );
END;

-- =====================================================================
-- COMENTARIOS FINALES
-- =====================================================================
/*
CONSIDERACIONES DE DISEÑO:

1. ESCALABILIDAD:
   - Índices optimizados para consultas frecuentes
   - Particionamiento implícito por fechas
   - Campos JSON para flexibilidad sin comprometer performance

2. INTEGRIDAD DE DATOS:
   - Constraints que validan estados y tipos
   - Foreign keys con cascada apropiada
   - Triggers para auditoría automática

3. OPERABILIDAD:
   - Vistas para consultas comunes
   - Campos de auditoría completos
   - Manejo robusto de errores y reintentos

4. FLEXIBILIDAD:
   - Plantillas configurables por evento
   - Horarios personalizables por contacto
   - Metadatos en JSON para extensibilidad

5. RENDIMIENTO:
   - Índices compuestos para consultas específicas
   - Triggers optimizados para no impactar DML
   - Estadísticas pre-calculadas diarias

6. MONITOREO:
   - Métricas automatizadas
   - Historial completo de cambios
   - Vistas para dashboard de estadísticas

PRÓXIMOS PASOS:
1. Implementar procedimientos de limpieza de datos antiguos
2. Configurar alertas para tasa de errores alta
3. Implementar dashboard de monitoreo
4. Crear API endpoints para gestión de plantillas
5. Implementar worker para procesamiento de cola de envíos
*/