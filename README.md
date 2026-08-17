# VecinData Report API

Servicio FastAPI que genera un reporte PDF de la zona de una dirección (puntos de
interés cercanos, isócronas a pie, mapa, puntaje de zona y un resumen escrito por
un LLM), a partir de fuentes de datos abiertas.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
playwright install chromium
```

El último paso es obligatorio: el renderizador de PDF usa Playwright con
Chromium headless, y `pip install` **no** descarga el navegador. Sin él,
`render_pdf` falla en tiempo de ejecución.

## Tests

```bash
pytest -v
```

La suite no hace llamadas de red reales (los adaptadores HTTP se simulan con
`respx` o con fakes), pero sí lanza Chromium de verdad para los tests del
renderizador de PDF.

## Servidor de desarrollo

```bash
uvicorn app.main:app --reload
```

Endpoints:

- `GET /health` — verificación de estado.
- `POST /reports` con `{"address": "Calle 100 # 15-20, Bogotá"}` — devuelve el
  PDF (`application/pdf`).

## Variables de entorno

Se leen de un archivo `.env` en la raíz del repo. Ver `.env.example` para la
plantilla completa:

| Variable | Requerida | Descripción |
| --- | --- | --- |
| `GOOGLE_API_KEY` | Sí | Genera el resumen narrativo (Gemini, vía Google GenAI API). |
| `MAPBOX_ACCESS_TOKEN` | Sí | Mapa estático e imagen satelital. |
| `OPENROUTESERVICE_API_KEY` | Sí | Isócronas a pie. |
| `PROVIDER_MODE` | No (`free`) | `free` usa proveedores gratuitos (Nominatim). `paid` es solo un punto de extensión documentado y **no** es un modo utilizable. |
| `CACHE_DIR` | No (`.cache`) | Directorio de caché en disco para respuestas de proveedores. |

Geocodificación (Nominatim) y puntos de interés (Overpass) no requieren
credenciales.
