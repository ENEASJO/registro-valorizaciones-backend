-- Esquema para la tabla de empresas en Neon PostgreSQL
-- Este esquema permite almacenar la información completa de empresas consultadas

-- Habilitar extensiones necesarias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Tabla principal de empresas
CREATE TABLE IF NOT EXISTS empresas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ruc VARCHAR(11) UNIQUE NOT NULL,
    razon_social VARCHAR(500) NOT NULL,
    email VARCHAR(255),
    telefono VARCHAR(100),
    direccion TEXT,
    departamento VARCHAR(100),
    provincia VARCHAR(100),
    distrito VARCHAR(100),
    estado VARCHAR(50) DEFAULT 'ACTIVO',
    
    -- Datos de scraping (JSON)
    datos_sunat JSONB DEFAULT '{}',
    datos_osce JSONB DEFAULT '{}',
    fuentes_consultadas TEXT[] DEFAULT '{}',
    
    -- Metadatos
    creado_en TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    actualizado_en TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Índices para optimizar consultas
    CONSTRAINT ruc_valido CHECK (LENGTH(ruc) = 11 AND ruc ~ '^[0-9]+$'),
    CONSTRAINT email_valido CHECK (email IS NULL OR email ~* '^[A-Za-z0-9._%-]+@[A-Za-z0-9.-]+[.][A-Za-z]+$')
);

-- Tabla para representantes legales (soporta múltiples representantes por empresa)
CREATE TABLE IF NOT EXISTS representantes_legales (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    empresa_id UUID NOT NULL REFERENCES empresas(id) ON DELETE CASCADE,
    nombre VARCHAR(500) NOT NULL,
    cargo VARCHAR(200),
    tipo_documento VARCHAR(50) DEFAULT 'DNI',
    numero_documento VARCHAR(50),
    participacion VARCHAR(100),
    fuente VARCHAR(50) DEFAULT 'SUNAT',
    
    -- Metadatos
    creado_en TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Índices
    CONSTRAINT documento_valido CHECK (numero_documento IS NULL OR LENGTH(numero_documento) > 0)
);

-- Tabla para contactos adicionales
CREATE TABLE IF NOT EXISTS contactos_empresa (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    empresa_id UUID NOT NULL REFERENCES empresas(id) ON DELETE CASCADE,
    telefono VARCHAR(100),
    email VARCHAR(255),
    direccion TEXT,
    tipo_contacto VARCHAR(50) DEFAULT 'PRINCIPAL',
    fuente VARCHAR(50) DEFAULT 'CONSOLIDADO',
    
    -- Metadatos
    creado_en TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Índices para mejorar rendimiento
CREATE INDEX IF NOT EXISTS idx_empresas_ruc ON empresas(ruc);
CREATE INDEX IF NOT EXISTS idx_empresas_razon_social ON empresas(razon_social);
CREATE INDEX IF NOT EXISTS idx_empresas_estado ON empresas(estado);
CREATE INDEX IF NOT EXISTS idx_representantes_empresa_id ON representantes_legales(empresa_id);
CREATE INDEX IF NOT EXISTS idx_representantes_documento ON representantes_legales(numero_documento);
CREATE INDEX IF NOT EXISTS idx_contactos_empresa_id ON contactos_empresa(empresa_id);

-- Índices para búsqueda en JSON
CREATE INDEX IF NOT EXISTS idx_empresas_datos_sunat ON empresas USING GIN(datos_sunat);
CREATE INDEX IF NOT EXISTS idx_empresas_datos_osce ON empresas USING GIN(datos_osce);

-- Trigger para actualizar timestamp automáticamente
CREATE OR REPLACE FUNCTION actualizar_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.actualizado_en = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_empresas_actualizado_en
    BEFORE UPDATE ON empresas
    FOR EACH ROW
    EXECUTE FUNCTION actualizar_timestamp();

-- Función para insertar empresa con representantes (útil para el servicio)
CREATE OR REPLACE FUNCTION insertar_empresa_completa(
    p_ruc VARCHAR(11),
    p_razon_social VARCHAR(500),
    p_email VARCHAR(255) DEFAULT NULL,
    p_telefono VARCHAR(100) DEFAULT NULL,
    p_direccion TEXT DEFAULT NULL,
    p_departamento VARCHAR(100) DEFAULT NULL,
    p_provincia VARCHAR(100) DEFAULT NULL,
    p_estado VARCHAR(50) DEFAULT 'ACTIVO',
    p_datos_sunat JSONB DEFAULT '{}',
    p_datos_osce JSONB DEFAULT '{}',
    p_fuentes_consultadas TEXT[] DEFAULT '{}'
)
RETURNS UUID AS $$
DECLARE
    v_empresa_id UUID;
BEGIN
    -- Insertar empresa principal
    INSERT INTO empresas (
        ruc, razon_social, email, telefono, direccion, 
        departamento, provincia, estado, 
        datos_sunat, datos_osce, fuentes_consultadas
    ) VALUES (
        p_ruc, p_razon_social, p_email, p_telefono, p_direccion,
        p_departamento, p_provincia, p_estado,
        p_datos_sunat, p_datos_osce, p_fuentes_consultadas
    ) RETURNING id INTO v_empresa_id;
    
    RETURN v_empresa_id;
END;
$$ LANGUAGE plpgsql;

-- Función para insertar representante legal
CREATE OR REPLACE FUNCTION insertar_representante_legal(
    p_empresa_id UUID,
    p_nombre VARCHAR(500),
    p_cargo VARCHAR(200) DEFAULT NULL,
    p_tipo_documento VARCHAR(50) DEFAULT 'DNI',
    p_numero_documento VARCHAR(50) DEFAULT NULL,
    p_participacion VARCHAR(100) DEFAULT NULL,
    p_fuente VARCHAR(50) DEFAULT 'SUNAT'
)
RETURNS UUID AS $$
DECLARE
    v_representante_id UUID;
BEGIN
    INSERT INTO representantes_legales (
        empresa_id, nombre, cargo, tipo_documento, 
        numero_documento, participacion, fuente
    ) VALUES (
        p_empresa_id, p_nombre, p_cargo, p_tipo_documento,
        p_numero_documento, p_participacion, p_fuente
    ) RETURNING id INTO v_representante_id;
    
    RETURN v_representante_id;
END;
$$ LANGUAGE plpgsql;

-- Permisos (ajustar según necesidad)
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO PUBLIC;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO PUBLIC;

-- Comentarios para documentación
COMMENT ON TABLE empresas IS 'Tabla principal para almacenar información de empresas consultadas';
COMMENT ON TABLE representantes_legales IS 'Tabla para almacenar representantes legales de empresas';
COMMENT ON TABLE contactos_empresa IS 'Tabla para almacenar información de contacto adicional de empresas';