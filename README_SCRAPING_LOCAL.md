# 🏠 Script Local de Scraping MEF Invierte

## Quick Start

```bash
# 1. Instalar dependencias
pip install -r requirements.txt
python -m playwright install chromium

# 2. Configurar .env con NEON_DATABASE_URL

# 3. Ejecutar scraping
python3 scrape_mef_local.py <CUI>

# Ejemplo
python3 scrape_mef_local.py 2595080
```

## ¿Por qué existe este script?

MEF Invierte **bloquea IPs de datacenters** (Railway, AWS, GCP) pero **permite IPs residenciales**.

**Solución:** Ejecutar scraping **desde tu PC** → Guardar en **Neon PostgreSQL** → Railway lee de **caché**.

## Flujo

```
[Tu PC] --scraping--> [MEF Invierte] --datos--> [Neon PostgreSQL]
                                                        ↓
                                            [Railway API lee caché] ⚡ <100ms
```

## Comandos

| Comando | Descripción |
|---------|-------------|
| `python3 scrape_mef_local.py 2595080` | Scraping y guardar |
| `python3 scrape_mef_local.py 2595080 --force` | Forzar actualización |

## Documentación Completa

📖 Ver: [`docs/SCRIPT_SCRAPING_LOCAL_MEF.md`](docs/SCRIPT_SCRAPING_LOCAL_MEF.md)

---

✅ **Funciona:** Tu PC tiene IP residencial
❌ **No funciona:** Railway tiene IP datacenter
🚀 **Resultado:** Datos MEF disponibles desde Railway en <100ms
