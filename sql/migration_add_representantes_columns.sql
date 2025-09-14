-- Migration script to add missing columns to representantes_legales table
-- This script should be run to update the database schema

-- Add es_principal column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'representantes_legales'
                   AND column_name = 'es_principal') THEN
        ALTER TABLE representantes_legales ADD COLUMN es_principal BOOLEAN DEFAULT false;
        RAISE NOTICE 'Column es_principal added to representantes_legales';
    END IF;
END $$;

-- Add activo column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'representantes_legales'
                   AND column_name = 'activo') THEN
        ALTER TABLE representantes_legales ADD COLUMN activo BOOLEAN DEFAULT true;
        RAISE NOTICE 'Column activo added to representantes_legales';
    END IF;
END $$;

-- Update the stored function to include the new parameters
CREATE OR REPLACE FUNCTION insertar_representante_legal(
    p_empresa_id UUID,
    p_nombre VARCHAR(500),
    p_cargo VARCHAR(200) DEFAULT NULL,
    p_tipo_documento VARCHAR(50) DEFAULT 'DNI',
    p_numero_documento VARCHAR(50) DEFAULT NULL,
    p_participacion VARCHAR(100) DEFAULT NULL,
    p_fuente VARCHAR(50) DEFAULT 'SUNAT',
    p_es_principal BOOLEAN DEFAULT false,
    p_activo BOOLEAN DEFAULT true
)
RETURNS UUID AS $$
DECLARE
    v_representante_id UUID;
BEGIN
    INSERT INTO representantes_legales (
        empresa_id, nombre, cargo, tipo_documento,
        numero_documento, participacion, fuente, es_principal, activo, creado_en
    ) VALUES (
        p_empresa_id, p_nombre, p_cargo, p_tipo_documento,
        p_numero_documento, p_participacion, p_fuente, p_es_principal, p_activo, CURRENT_TIMESTAMP
    ) RETURNING id INTO v_representante_id;

    RETURN v_representante_id;
END;
$$ LANGUAGE plpgsql;