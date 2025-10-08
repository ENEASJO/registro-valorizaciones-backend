-- Migración: Agregar campos para datos MEF Invierte en tabla obras
-- Fecha: 2025-01-07
-- Propósito: Cachear datos scraped desde MEF Invierte para consulta rápida

-- Agregar campos para MEF Invierte
ALTER TABLE obras
ADD COLUMN IF NOT EXISTS cui VARCHAR(20),
ADD COLUMN IF NOT EXISTS datos_mef JSONB,
ADD COLUMN IF NOT EXISTS fecha_actualizacion_mef TIMESTAMP WITH TIME ZONE;

-- Crear índice para búsqueda por CUI
CREATE INDEX IF NOT EXISTS idx_obras_cui ON obras(cui);

-- Crear índice GIN para búsquedas en JSONB
CREATE INDEX IF NOT EXISTS idx_obras_datos_mef ON obras USING gin(datos_mef);

-- Comentarios
COMMENT ON COLUMN obras.cui IS 'Código Único de Inversiones del MEF';
COMMENT ON COLUMN obras.datos_mef IS 'Datos completos scraped desde MEF Invierte (formato JSON)';
COMMENT ON COLUMN obras.fecha_actualizacion_mef IS 'Última vez que se actualizaron los datos desde MEF';
