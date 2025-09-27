-- Esquema para tabla de obras con generación automática de códigos
-- Base de datos: PostgreSQL (Neon)

-- Crear tabla obras si no existe
CREATE TABLE IF NOT EXISTS obras (
    -- Campos principales
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(50) UNIQUE NOT NULL,
    nombre VARCHAR(500) NOT NULL,
    descripcion TEXT,
    
    -- Empresa ejecutora (FK)
    empresa_id INTEGER NOT NULL,
    cliente VARCHAR(255),
    
    -- Ubicación
    ubicacion TEXT,
    distrito VARCHAR(100),
    provincia VARCHAR(100),
    departamento VARCHAR(100),
    ubigeo VARCHAR(6),
    
    -- Características técnicas
    modalidad_ejecucion VARCHAR(50),
    sistema_contratacion VARCHAR(50),
    tipo_obra VARCHAR(100),
    
    -- Montos (usando DECIMAL para precisión)
    monto_contractual DECIMAL(15,2) DEFAULT 0.00,
    monto_adicionales DECIMAL(15,2) DEFAULT 0.00,
    monto_total DECIMAL(15,2) DEFAULT 0.00,
    
    -- Fechas y plazos
    fecha_inicio DATE,
    fecha_fin_contractual DATE,
    fecha_fin_real DATE,
    plazo_contractual INTEGER, -- días
    plazo_total INTEGER, -- días
    
    -- Estado y avance
    estado_obra VARCHAR(50) DEFAULT 'PLANIFICADA' NOT NULL,
    porcentaje_avance DECIMAL(5,2) DEFAULT 0.00 CHECK (porcentaje_avance >= 0 AND porcentaje_avance <= 100),
    observaciones TEXT,
    
    -- Campos de auditoría
    activo BOOLEAN DEFAULT true NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    version INTEGER DEFAULT 1 NOT NULL,
    
    -- Constraints
    CONSTRAINT fk_obras_empresa FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    CONSTRAINT chk_obras_estado CHECK (estado_obra IN ('PLANIFICADA', 'EN_PROCESO', 'PARALIZADA', 'SUSPENDIDA', 'TERMINADA', 'LIQUIDADA', 'CANCELADA')),
    CONSTRAINT chk_obras_modalidad CHECK (modalidad_ejecucion IS NULL OR modalidad_ejecucion IN ('ADMINISTRACION_DIRECTA', 'CONTRATA', 'CONCESION', 'ASOCIACION_PUBLICO_PRIVADA')),
    CONSTRAINT chk_obras_sistema CHECK (sistema_contratacion IS NULL OR sistema_contratacion IN ('SUMA_ALZADA', 'PRECIOS_UNITARIOS', 'ESQUEMA_MIXTO', 'COSTO_MAS_PORCENTAJE')),
    CONSTRAINT chk_obras_montos_positivos CHECK (
        monto_contractual >= 0 AND 
        monto_adicionales >= 0 AND 
        monto_total >= 0
    ),
    CONSTRAINT chk_obras_fechas CHECK (
        fecha_fin_contractual IS NULL OR 
        fecha_inicio IS NULL OR 
        fecha_fin_contractual >= fecha_inicio
    ),
    CONSTRAINT chk_obras_plazos_positivos CHECK (
        plazo_contractual IS NULL OR plazo_contractual >= 0
    )
);

-- Índices para optimizar consultas
CREATE INDEX IF NOT EXISTS idx_obras_codigo ON obras(codigo);
CREATE INDEX IF NOT EXISTS idx_obras_empresa_id ON obras(empresa_id);
CREATE INDEX IF NOT EXISTS idx_obras_estado ON obras(estado_obra);
CREATE INDEX IF NOT EXISTS idx_obras_activo ON obras(activo);
CREATE INDEX IF NOT EXISTS idx_obras_created_at ON obras(created_at);
CREATE INDEX IF NOT EXISTS idx_obras_nombre ON obras USING gin(to_tsvector('spanish', nombre));

-- Índice compuesto para consultas frecuentes
CREATE INDEX IF NOT EXISTS idx_obras_empresa_estado_activo ON obras(empresa_id, estado_obra, activo);

-- Trigger para actualizar automáticamente updated_at
CREATE OR REPLACE FUNCTION update_obras_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_obras_updated_at
    BEFORE UPDATE ON obras
    FOR EACH ROW
    EXECUTE FUNCTION update_obras_updated_at();

-- Trigger para calcular monto_total automáticamente
CREATE OR REPLACE FUNCTION calculate_obras_monto_total()
RETURNS TRIGGER AS $$
BEGIN
    NEW.monto_total = COALESCE(NEW.monto_contractual, 0) + COALESCE(NEW.monto_adicionales, 0);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_obras_calculate_total
    BEFORE INSERT OR UPDATE OF monto_contractual, monto_adicionales ON obras
    FOR EACH ROW
    EXECUTE FUNCTION calculate_obras_monto_total();

-- Función para generar código único de obra (backup si falla la aplicación)
CREATE OR REPLACE FUNCTION generar_codigo_obra(p_empresa_id INTEGER)
RETURNS VARCHAR(50) AS $$
DECLARE
    v_codigo VARCHAR(50);
    v_año INTEGER;
    v_secuencia VARCHAR(8);
    v_empresa_str VARCHAR(3);
    v_exists BOOLEAN;
    v_counter INTEGER := 0;
BEGIN
    v_año := EXTRACT(YEAR FROM NOW());
    v_empresa_str := LPAD(p_empresa_id::TEXT, 3, '0');
    
    LOOP
        -- Generar secuencia basada en timestamp + contador
        v_secuencia := LPAD(
            (EXTRACT(MONTH FROM NOW())::INTEGER * 1000000 + 
             EXTRACT(DAY FROM NOW())::INTEGER * 10000 + 
             EXTRACT(HOUR FROM NOW())::INTEGER * 100 + 
             EXTRACT(MINUTE FROM NOW())::INTEGER + 
             v_counter)::TEXT, 
            8, '0'
        );
        
        v_codigo := 'OBR-' || v_empresa_str || '-' || v_año || '-' || v_secuencia;
        
        -- Verificar si el código ya existe
        SELECT EXISTS(SELECT 1 FROM obras WHERE codigo = v_codigo) INTO v_exists;
        
        IF NOT v_exists THEN
            EXIT;
        END IF;
        
        v_counter := v_counter + 1;
        
        -- Evitar bucle infinito
        IF v_counter > 999 THEN
            RAISE EXCEPTION 'No se pudo generar un código único para la obra';
        END IF;
    END LOOP;
    
    RETURN v_codigo;
END;
$$ LANGUAGE plpgsql;

-- Comentarios en la tabla
COMMENT ON TABLE obras IS 'Tabla principal para almacenar información de obras de construcción';
COMMENT ON COLUMN obras.codigo IS 'Código único generado automáticamente con formato OBR-EMP-YYYY-SECUENCIA';
COMMENT ON COLUMN obras.estado_obra IS 'Estado actual de la obra: PLANIFICADA, EN_PROCESO, PARALIZADA, SUSPENDIDA, TERMINADA, LIQUIDADA, CANCELADA';
COMMENT ON COLUMN obras.porcentaje_avance IS 'Porcentaje de avance físico de la obra (0-100)';
COMMENT ON COLUMN obras.version IS 'Campo de versión para control de concurrencia optimista';

-- Insertar datos de ejemplo (opcional - comentar en producción)
/*
INSERT INTO obras (
    codigo, nombre, descripcion, empresa_id, cliente,
    ubicacion, distrito, provincia, departamento,
    modalidad_ejecucion, sistema_contratacion, tipo_obra,
    monto_contractual, estado_obra
) VALUES 
(
    'OBR-001-2025-00001',
    'Construcción de Centro de Salud',
    'Construcción de centro de salud tipo I-3 con capacidad para 50 pacientes diarios',
    1,
    'Ministerio de Salud',
    'Av. Principal 123, Distrito Centro',
    'Centro',
    'Lima',
    'Lima',
    'CONTRATA',
    'SUMA_ALZADA',
    'Edificación - Salud',
    500000.00,
    'PLANIFICADA'
),
(
    'OBR-001-2025-00002',
    'Mejoramiento de Carretera Rural',
    'Mejoramiento y pavimentación de carretera rural tramo Km 0+000 - Km 5+000',
    1,
    'Gobierno Regional',
    'Carretera Rural Norte',
    'San Juan',
    'Lima',
    'Lima',
    'CONTRATA',
    'PRECIOS_UNITARIOS',
    'Transporte - Carreteras',
    1200000.00,
    'EN_PROCESO'
);
*/