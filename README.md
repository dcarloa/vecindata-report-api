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

## Docker (para despliegue)

Este repo incluye un `Dockerfile` para desplegarlo en Google Cloud Run — ver la
sección "Despliegue" más abajo para el proceso completo. Si quieres probar la
imagen localmente antes de desplegar (necesitas Docker instalado):

```bash
docker build -t vecindata-report-api-test .
docker run --rm -p 8080:8080 -e PORT=8080 --env-file .env vecindata-report-api-test
```

(esto pasa tus keys reales de `.env` al contenedor — solo para pruebas
locales, nunca las metas al `Dockerfile` ni a la imagen)

Luego `curl http://localhost:8080/health` debería responder `{"status":"ok"}`.

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
| `OPERATOR_ACCESS_KEY` | No (`""`) | Clave compartida que protege `POST /reports`. Si está vacía (el default), el endpoint queda **sin protección** — cualquiera con la URL puede generar reportes. En producción, configúrala con un valor largo y avísale al operador cuál es (la misma clave que se pide en el panel operador de `vecindata-web`). |

Geocodificación (Nominatim) y puntos de interés (Overpass) no requieren
credenciales.

## Despliegue (Google Cloud Run)

Requiere el proyecto de GCP ya usado para Gemini (o cualquier otro proyecto con
facturación habilitada — el tier gratis de Cloud Run no cobra dentro de sus
límites, pero Google pide una tarjeta vinculada al proyecto).

1. Instala `gcloud` CLI si no lo tienes: https://cloud.google.com/sdk/docs/install
2. Autentícate y selecciona el proyecto:

   ```bash
   gcloud auth login
   gcloud config set project tu-project-id
   ```

   (usa `gcloud projects list` para ver los proyectos disponibles en tu cuenta)

3. Despliega (un solo comando — construye la imagen desde el `Dockerfile` vía
   Cloud Build y la publica):

   ```bash
   gcloud run deploy vecindata-report-api \
     --source . \
     --region us-central1 \
     --allow-unauthenticated \
     --memory 2Gi \
     --cpu 2 \
     --set-env-vars GOOGLE_API_KEY=tu-key,MAPBOX_ACCESS_TOKEN=tu-token,OPENROUTESERVICE_API_KEY=tu-key,OPERATOR_ACCESS_KEY=una-clave-larga-que-tu-eliges,PROVIDER_MODE=free
   ```

   `--memory 2Gi --cpu 2`: el default de Cloud Run (512 MiB) no alcanza para
   lanzar Chromium headless por cada reporte — con el default, el servicio se
   queda sin memoria y el operador ve un 500 sin pista de la causa real.

   Nota: si alguna de tus API keys contiene una coma, el flag `--set-env-vars`
   la va a cortar ahí — en ese caso usa el formato
   `--set-env-vars "^##^K1=v1##K2=v2"` (delimitador alternativo) en vez de
   comas.

   Al terminar, imprime la URL del servicio (algo como
   `https://vecindata-report-api-xxxxx-uc.a.run.app`) — **guárdala**, la
   necesitas para configurar `vecindata-web`.

4. Actualiza `app/main.py`'s `allow_origins` en `CORSMiddleware` para incluir el
   dominio real de Cloudflare Pages una vez que lo tengas (paso 5 de
   `vecindata-web` abajo), y vuelve a correr el comando del paso 3 para
   redesplegar con el CORS correcto.

Para cambiar cualquier variable de entorno después (ej. rotar
`OPERATOR_ACCESS_KEY`), vuelve a correr el mismo comando `gcloud run deploy`
con el nuevo valor — no hace falta reconstruir la imagen si solo cambian
variables de entorno (`gcloud run services update` también sirve para eso).
