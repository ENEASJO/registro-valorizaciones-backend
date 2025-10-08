# 🏠 Script Local de Scraping MEF Invierte

## 📋 ¿Qué es este script?

`scrape_mef_local.py` es una herramienta que ejecutas **DESDE TU PC** para hacer scraping de datos del MEF Invierte y guardarlos directamente en la base de datos Neon PostgreSQL.

### ✅ ¿Por qué funciona desde tu PC?

MEF Invierte **bloquea IPs de datacenters** (Railway, Render, AWS, etc.) pero **permite IPs residenciales**. Al ejecutar el script desde tu PC, usas tu IP residencial y el scraping funciona perfectamente.

---

## 🚀 Instalación y Configuración

### Requisitos Previos

1. **Python 3.11+** instalado
2. **Internet** (tu conexión residencial)
3. **Acceso a base de datos Neon** (variable en `.env`)

### Instalación de Dependencias

```bash
cd registro-valorizaciones-backend

# Instalar dependencias Python
pip install -r requirements.txt

# Instalar navegador Playwright (IMPORTANTE)
python -m playwright install chromium
```

### Configurar `.env`

Asegúrate de tener la variable de conexión a Neon en tu archivo `.env`:

```bash
NEON_DATABASE_URL=postgresql://neondb_owner:npg_...@ep-fancy-river-acd46jxk-pooler.sa-east-1.aws.neon.tech/neondb?sslmode=require
```

---

## 💻 Cómo Usar el Script

### Sintaxis Básica

```bash
python3 scrape_mef_local.py <CUI> [--force]
```

### Parámetros

- `<CUI>` (requerido): Código Único de Inversiones (7 dígitos)
- `--force` (opcional): Fuerza actualización aunque ya existan datos

---

## 📝 Ejemplos de Uso

### Ejemplo 1: Scraping de CUI nuevo

```bash
python3 scrape_mef_local.py 2595080
```

**Salida esperada:**
```
================================================================================
SCRAPING MEF INVIERTE - EJECUCIÓN LOCAL
================================================================================

ℹ️  CUI: 2595080
ℹ️  Modo: Normal

✅ Conectado a base de datos Neon

ℹ️  Iniciando scraping a MEF Invierte...
⚠️  Esto puede tomar 30-60 segundos...

✅ Scraping completado en 4.2 segundos

DATOS OBTENIDOS:
  CUI: 2595080
  Nombre: CONSTRUCCION DE MURO DE CONTENCION; REPARACION DE PTAR...
  Estado: EN REGISTRO
  Etapa: Ejecución física (C)
  Costo Total Actualizado: S/ 873,012.88

ℹ️  Guardando datos en base de datos...
⚠️  CUI 2595080 no tiene obra asociada en la BD
ℹ️  Los datos fueron scraped correctamente pero NO se guardaron
ℹ️  Primero crea la obra en el sistema, luego ejecuta este script

================================================================================
⚠️  SCRAPING EXITOSO PERO NO SE GUARDÓ EN BD
================================================================================
```

### Ejemplo 2: Actualizar datos de obra existente

```bash
# Primero crear la obra en el sistema con CUI 2595080
# Luego ejecutar:
python3 scrape_mef_local.py 2595080
```

**Salida esperada:**
```
================================================================================
SCRAPING MEF INVIERTE - EJECUCIÓN LOCAL
================================================================================

ℹ️  CUI: 2595080
ℹ️  Modo: Normal

✅ Conectado a base de datos Neon
✅ Scraping completado en 4.5 segundos

DATOS OBTENIDOS:
  CUI: 2595080
  Nombre: CONSTRUCCION DE MURO DE CONTENCION; REPARACION DE PTAR...
  Estado: EN REGISTRO
  Etapa: Ejecución física (C)
  Costo Total Actualizado: S/ 873,012.88

ℹ️  Guardando datos en base de datos...
✅ Datos MEF actualizados en BD para CUI 2595080
ℹ️  Obra: OBR-001 - Construcción Muro Contención

================================================================================
✅ PROCESO COMPLETADO EXITOSAMENTE

ℹ️  Los usuarios ahora pueden consultar estos datos desde Railway
ℹ️  Endpoint: GET /api/v1/mef-invierte/consultar/2595080
================================================================================
```

### Ejemplo 3: Forzar actualización

Si ya existe data pero quieres actualizarla:

```bash
python3 scrape_mef_local.py 2595080 --force
```

---

## 🔄 Flujo de Trabajo Recomendado

### Escenario 1: Crear Obra Nueva con Datos MEF

1. **Ejecutar scraping local:**
   ```bash
   python3 scrape_mef_local.py 2595080
   ```

2. **Crear obra en el sistema:**
   - Ir al frontend
   - Crear nueva obra
   - Asignar CUI: 2595080
   - Guardar obra

3. **Volver a ejecutar scraping:**
   ```bash
   python3 scrape_mef_local.py 2595080
   ```

4. **Ahora los datos están en BD** y disponibles desde Railway

### Escenario 2: Actualizar Obra Existente

1. **Ejecutar scraping con --force:**
   ```bash
   python3 scrape_mef_local.py 2595080 --force
   ```

2. **Los datos se actualizan automáticamente** en la BD

3. **Usuarios consultan datos actualizados** desde Railway:
   ```bash
   curl https://registro-valorizaciones-backend-production.up.railway.app/api/v1/mef-invierte/consultar/2595080
   ```

---

## 📊 Datos Extraídos por el Script

El script extrae **TODA la información** de la Ficha de Ejecución de MEF Invierte:

### Datos Básicos
- CUI
- Nombre de la inversión
- Estado (EN REGISTRO, VIABLE, etc.)
- Etapa (Ejecución física, Formulación, etc.)
- Fecha de registro

### Responsabilidad Funcional
- Función
- División funcional
- Grupo funcional
- Sector responsable

### Articulación con PMI
- Servicio público
- Indicador de brecha
- Espacio geográfico
- Contribución de cierre de brechas

### Institucionalidad
- OPMI (Oficina de Programación Multianual de Inversiones)
- UF (Unidad Formuladora)
- UEI (Unidad Ejecutora de Inversiones)
- UEP (Unidad Ejecutora Presupuestal)

### Expediente Técnico
- Metas físicas (MURO DE CONTENCION, PTAR, etc.)
- Modalidad de ejecución
- Fechas por componente (inicio, término, entrega)
- Costos detallados:
  - Expediente técnico
  - Supervisión
  - Liquidación
  - Costo de inversión actualizado

### Modificaciones Durante Ejecución
- Documentos de modificación (RGDUR, ADENDA, INF)
- Fechas modificadas por componente
- Costos actualizados tras modificaciones

### Costos Finales
- Costo total actualizado ✅
- Costo de control concurrente
- Costo de controversias
- Monto de carta fianza

---

## ⚠️ Mensajes de Error y Soluciones

### Error 1: `ModuleNotFoundError: No module named 'playwright'`

**Causa:** Playwright no está instalado

**Solución:**
```bash
pip install playwright
python -m playwright install chromium
```

### Error 2: `Variable NEON_DATABASE_URL no encontrada en .env`

**Causa:** Falta configurar la conexión a base de datos

**Solución:**
1. Verificar que existe el archivo `.env`
2. Agregar la variable:
   ```bash
   NEON_DATABASE_URL=postgresql://...
   ```

### Error 3: `CUI inválido: ABC123 (debe ser numérico)`

**Causa:** CUI debe ser 7 dígitos numéricos

**Solución:**
```bash
# Correcto
python3 scrape_mef_local.py 2595080

# Incorrecto
python3 scrape_mef_local.py ABC123
```

### Error 4: `No se encontró información para CUI 2595080`

**Causa:** El CUI no existe en MEF Invierte

**Solución:**
1. Verificar el CUI en https://ofi5.mef.gob.pe/invierte/consultapublica/consultainversiones
2. Usar un CUI válido y registrado

### Error 5: Timeout durante scraping

**Causa:** MEF Invierte está lento o no responde

**Solución:**
1. Esperar unos minutos
2. Intentar nuevamente
3. Verificar conexión a internet

---

## 🔒 Seguridad

### ¿Es seguro?

✅ **SÍ**, el script:
- Solo hace **lectura** desde MEF Invierte
- Solo **actualiza** datos en tabla `obras` de tu BD
- No modifica ningún dato en MEF Invierte
- No expone credenciales (usa `.env`)

### ¿Qué permisos necesita?

- **Lectura:** Acceso a internet para scraping MEF
- **Escritura:** Conexión a base de datos Neon (solo tabla `obras`)

---

## 📈 Performance

| Operación | Tiempo Promedio |
|-----------|-----------------|
| Scraping MEF | 4-8 segundos |
| Guardar en BD | <100ms |
| **Total** | **4-8 segundos** |

**Comparado con Railway:**
- Railway (datacenter IP): ❌ Timeout 30-120s
- Tu PC (IP residencial): ✅ 4-8 segundos

---

## 🎯 Recomendaciones

1. **Ejecutar desde tu PC:** Nunca desde Railway o cloud (será bloqueado)
2. **Verificar CUI antes:** Asegúrate de que el CUI existe en MEF
3. **Usar --force solo cuando necesites:** Para no sobreescribir datos innecesariamente
4. **Mantener .env privado:** No subir a GitHub ni compartir
5. **Ejecutar cuando haya cambios:** Ampliaciones, modificaciones, etc.

---

## 🔗 Integración con Railway

Una vez que ejecutas el script y guardas los datos:

1. **Backend Railway lee de BD:**
   ```bash
   GET /api/v1/mef-invierte/consultar/2595080
   ```

2. **Respuesta súper rápida (<100ms):**
   ```json
   {
     "success": true,
     "found": true,
     "cui": "2595080",
     "data": {
       "cui": "2595080",
       "nombre": "CONSTRUCCION DE MURO DE CONTENCION...",
       "estado": "EN REGISTRO",
       "costos_finales": {
         "costo_total_actualizado": 873012.88
       }
     },
     "cache_info": {
       "ultima_actualizacion": "2025-01-07T15:30:00Z",
       "fuente": "Base de datos (caché)"
     }
   }
   ```

3. **Usuarios felices:** Datos de MEF en <100ms 🚀

---

## 📚 Referencias

- **Guía completa:** `docs/MEF_IP_WHITELIST_GUIDE.md`
- **Diagnóstico MEF blocking:** `docs/DIAGNOSTICO_MEF_BLOCKING.md`
- **Servicio MEF:** `app/services/mef_invierte_service.py`
- **Endpoints API:** `app/api/routes/mef_invierte.py`

---

## ✅ Checklist Rápido

Antes de ejecutar el script, verifica:

- [ ] Python 3.11+ instalado
- [ ] Playwright instalado (`python -m playwright install chromium`)
- [ ] `.env` configurado con `NEON_DATABASE_URL`
- [ ] Conexión a internet activa
- [ ] CUI válido (7 dígitos numéricos)

---

## 🎓 Preguntas Frecuentes

### ¿Puedo ejecutar esto desde Railway?

**No.** Railway usa IP de datacenter que MEF bloquea. Solo funciona desde tu PC.

### ¿Qué pasa si mi IP cambia?

No hay problema. El script usa tu IP actual, no necesita configuración.

### ¿Puedo scraping múltiples CUIs a la vez?

No directamente. Ejecuta el script múltiples veces:

```bash
python3 scrape_mef_local.py 2595080
python3 scrape_mef_local.py 2595081
python3 scrape_mef_local.py 2595082
```

### ¿Los datos quedan guardados para siempre?

Sí, hasta que ejecutes el script nuevamente con `--force`. Los datos en la BD persisten.

### ¿Cuánto cuesta?

**Gratis.** No usa APIs de pago ni proxies. Solo tu internet y tu PC.

---

**¡Listo para usar!** 🚀
