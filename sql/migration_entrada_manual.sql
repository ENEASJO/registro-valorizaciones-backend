-- ====================================================================
-- MIGRACIÓN: Agregar soporte completo para entrada manual de empresas
-- Fecha: 2024-01-27
-- Descripción: Agregar nuevos campos para mejorar la entrada manual
-- ====================================================================

-- 1. Agregar campos para metadatos de entrada manual
ALTER TABLE empresas 
ADD COLUMN IF NOT EXISTS fuente_datos VARCHAR(20) NOT NULL DEFAULT 'SCRAPING' 
CHECK (fuente_datos IN ('MANUAL', 'SCRAPING', 'MIXTO'));

ALTER TABLE empresas 
ADD COLUMN IF NOT EXISTS fuentes_consultadas JSONB DEFAULT NULL;

ALTER TABLE empresas 
ADD COLUMN IF NOT EXISTS requiere_verificacion BOOLEAN NOT NULL DEFAULT FALSE;

ALTER TABLE empresas 
ADD COLUMN IF NOT EXISTS calidad_datos VARCHAR(20) NOT NULL DEFAULT 'BUENA' 
CHECK (calidad_datos IN ('BUENA', 'ACEPTABLE', 'PARCIAL'));

-- 2. Agregar campos adicionales para entrada manual
ALTER TABLE empresas 
ADD COLUMN IF NOT EXISTS pagina_web VARCHAR(255) DEFAULT NULL;

ALTER TABLE empresas 
ADD COLUMN IF NOT EXISTS redes_sociales JSONB DEFAULT NULL;

ALTER TABLE empresas 
ADD COLUMN IF NOT EXISTS sector_economico VARCHAR(100) DEFAULT NULL;

ALTER TABLE empresas 
ADD COLUMN IF NOT EXISTS tamaño_empresa VARCHAR(20) DEFAULT NULL
CHECK (tamaño_empresa IN ('MICRO', 'PEQUEÑA', 'MEDIANA', 'GRANDE', NULL));

-- 3. Actualizar tabla de representantes para entrada manual
ALTER TABLE empresa_representantes 
ADD COLUMN IF NOT EXISTS validado_manualmente BOOLEAN NOT NULL DEFAULT FALSE;

ALTER TABLE empresa_representantes 
ADD COLUMN IF NOT EXISTS requiere_verificacion BOOLEAN NOT NULL DEFAULT FALSE;

ALTER TABLE empresa_representantes 
ADD COLUMN IF NOT EXISTS observaciones_validacion TEXT DEFAULT NULL;

-- 4. Crear índices para mejorar performance en consultas
CREATE INDEX IF NOT EXISTS idx_empresas_fuente_datos ON empresas(fuente_datos);
CREATE INDEX IF NOT EXISTS idx_empresas_requiere_verificacion ON empresas(requiere_verificacion);
CREATE INDEX IF NOT EXISTS idx_empresas_calidad_datos ON empresas(calidad_datos);
CREATE INDEX IF NOT EXISTS idx_representantes_validado ON empresa_representantes(validado_manualmente);

-- 5. Crear vista para empresas que requieren verificación
CREATE OR REPLACE VIEW empresas_requieren_verificacion AS
SELECT 
    e.id,
    e.codigo,
    e.ruc,
    e.razon_social,
    e.fuente_datos,
    e.calidad_datos,
    e.requiere_verificacion,
    e.created_at,
    COUNT(r.id) as total_representantes,
    COUNT(CASE WHEN r.validado_manualmente = FALSE THEN 1 END) as representantes_sin_validar
FROM empresas e
LEFT JOIN empresa_representantes r ON e.id = r.empresa_id
WHERE e.requiere_verificacion = TRUE 
   OR e.calidad_datos IN ('ACEPTABLE', 'PARCIAL')
   OR e.fuente_datos = 'MANUAL'
GROUP BY e.id, e.codigo, e.ruc, e.razon_social, e.fuente_datos, 
         e.calidad_datos, e.requiere_verificacion, e.created_at
ORDER BY e.created_at DESC;

-- 6. Crear vista para estadísticas de entrada de datos
CREATE OR REPLACE VIEW estadisticas_entrada_datos AS
SELECT 
    COUNT(*) as total_empresas,
    COUNT(CASE WHEN fuente_datos = 'MANUAL' THEN 1 END) as empresas_manuales,
    COUNT(CASE WHEN fuente_datos = 'SCRAPING' THEN 1 END) as empresas_scraping,
    COUNT(CASE WHEN fuente_datos = 'MIXTO' THEN 1 END) as empresas_mixtas,
    COUNT(CASE WHEN requiere_verificacion = TRUE THEN 1 END) as requieren_verificacion,
    COUNT(CASE WHEN calidad_datos = 'BUENA' THEN 1 END) as calidad_buena,
    COUNT(CASE WHEN calidad_datos = 'ACEPTABLE' THEN 1 END) as calidad_aceptable,
    COUNT(CASE WHEN calidad_datos = 'PARCIAL' THEN 1 END) as calidad_parcial,
    ROUND(
        COUNT(CASE WHEN fuente_datos = 'MANUAL' THEN 1 END) * 100.0 / 
        NULLIF(COUNT(*), 0), 2
    ) as porcentaje_manual,
    ROUND(
        COUNT(CASE WHEN requiere_verificacion = TRUE THEN 1 END) * 100.0 / 
        NULLIF(COUNT(*), 0), 2
    ) as porcentaje_requiere_verificacion
FROM empresas;

-- 7. Función para actualizar automáticamente la fuente de datos
CREATE OR REPLACE FUNCTION actualizar_fuente_datos()
RETURNS TRIGGER AS $$
BEGIN
    -- Si se están actualizando fuentes_consultadas, actualizar fuente_datos
    IF NEW.fuentes_consultadas IS NOT NULL AND NEW.fuentes_consultadas != OLD.fuentes_consultadas THEN
        -- Contar fuentes consultadas
        DECLARE
            num_fuentes INTEGER;
            tiene_manual BOOLEAN;
        BEGIN
            SELECT jsonb_array_length(NEW.fuentes_consultadas) INTO num_fuentes;
            SELECT NEW.fuentes_consultadas ? 'MANUAL' INTO tiene_manual;
            
            IF tiene_manual AND num_fuentes > 1 THEN
                NEW.fuente_datos = 'MIXTO';
            ELSIF tiene_manual THEN
                NEW.fuente_datos = 'MANUAL';
            ELSE
                NEW.fuente_datos = 'SCRAPING';
            END IF;
        END;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 8. Crear trigger para actualizar fuente_datos automáticamente
DROP TRIGGER IF EXISTS trigger_actualizar_fuente_datos ON empresas;
CREATE TRIGGER trigger_actualizar_fuente_datos
    BEFORE UPDATE ON empresas
    FOR EACH ROW
    EXECUTE FUNCTION actualizar_fuente_datos();

-- 9. Actualizar empresas existentes para establecer valores por defecto
UPDATE empresas 
SET 
    fuente_datos = CASE 
        WHEN fuentes_consultadas IS NOT NULL AND fuentes_consultadas ? 'MANUAL' THEN 'MANUAL'
        ELSE 'SCRAPING'
    END,
    calidad_datos = 'BUENA',
    requiere_verificacion = FALSE
WHERE fuente_datos IS NULL OR fuente_datos = '';

-- 10. Comentarios para documentación
COMMENT ON COLUMN empresas.fuente_datos IS 'Fuente principal de los datos: MANUAL, SCRAPING o MIXTO';
COMMENT ON COLUMN empresas.fuentes_consultadas IS 'JSON array con las fuentes consultadas: ["SUNAT", "OSCE", "MANUAL"]';
COMMENT ON COLUMN empresas.requiere_verificacion IS 'Indica si la empresa requiere verificación manual posterior';
COMMENT ON COLUMN empresas.calidad_datos IS 'Calidad de los datos: BUENA, ACEPTABLE o PARCIAL';
COMMENT ON COLUMN empresas.pagina_web IS 'URL del sitio web corporativo';
COMMENT ON COLUMN empresas.redes_sociales IS 'JSON con redes sociales: {"facebook": "url", "linkedin": "url"}';
COMMENT ON COLUMN empresas.sector_economico IS 'Sector económico al que pertenece la empresa';
COMMENT ON COLUMN empresas.tamaño_empresa IS 'Tamaño de la empresa: MICRO, PEQUEÑA, MEDIANA, GRANDE';

COMMENT ON VIEW empresas_requieren_verificacion IS 'Vista de empresas que requieren verificación manual';
COMMENT ON VIEW estadisticas_entrada_datos IS 'Estadísticas sobre los métodos de entrada de datos';

-- 11. Verificar que la migración se ejecutó correctamente
SELECT 'Migración de entrada manual completada exitosamente' as mensaje;

-- 12. Mostrar estadísticas actuales
SELECT * FROM estadisticas_entrada_datos;