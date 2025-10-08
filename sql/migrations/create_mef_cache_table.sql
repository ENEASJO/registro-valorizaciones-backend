-- Crear tabla de caché MEF
-- Esta tabla guarda datos MEF temporalmente antes de crear obras

CREATE TABLE IF NOT EXISTS mef_cache (
    cui VARCHAR(20) PRIMARY KEY,
    datos_mef JSONB NOT NULL,
    fecha_scraping TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ultima_actualizacion TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índice para búsquedas rápidas
CREATE INDEX IF NOT EXISTS idx_mef_cache_fecha ON mef_cache(fecha_scraping DESC);

-- Comentarios
COMMENT ON TABLE mef_cache IS 'Caché temporal de datos MEF Invierte antes de crear obras';
COMMENT ON COLUMN mef_cache.cui IS 'Código Único de Inversiones';
COMMENT ON COLUMN mef_cache.datos_mef IS 'Datos completos scraped desde MEF Invierte';
COMMENT ON COLUMN mef_cache.fecha_scraping IS 'Fecha del scraping inicial';
COMMENT ON COLUMN mef_cache.ultima_actualizacion IS 'Última actualización de los datos';
