# Notas de comunicación con el otro dev

Bitácora para dejar registro de cambios, pendientes y hallazgos que necesitan
sincronizarse entre los dos repos o entre las personas que trabajan en ellos.

---

## 2026-08-24

**Hallazgo:** el sitio en producción (`https://vecindata.dcarloabad.workers.dev`)
corre una versión de `vecindata-web` que **no está en GitHub**
(`dcarloa/vecindata-web`, branch `master` está al día con `origin`, sin
commits pendientes). Alguien desplegó directo con `wrangler deploy` desde un
checkout local que nunca se hizo commit/push.

Funcionalidad que existe en el bundle desplegado pero no en el repo:

- Mapa "Ubicación en el mapa" con botón "Ajustar pin" (Google Maps +
  `AdvancedMarkerElement` arrastrable) en el formulario de reporte.
- Campos de asesor: nombre, WhatsApp, email, frase personalizada.
- Selector de radio de búsqueda.
- Checklist de categorías a mostrar en el reporte.
- Opción "Omitir puntaje de zona en el reporte".

**Bug reportado:** al arrastrar el pin del mapa, se actualizan `lat`/`lon`
pero el campo de texto "Dirección del inmueble" no cambia (no hay reverse
geocoding al soltar el pin) — confirmado leyendo el bundle minificado.

**Pendiente / para el otro dev:** necesitamos el código fuente real de esa
versión (rama, stash, u otra máquina) para no tener que reconstruirla desde
el bundle minificado. Si no aparece, se va a reconstruir desde el bundle y
quedará versionada en git de aquí en adelante.

---

## 2026-09-03

El bug del pin del mapa (arrastrar no actualiza "Dirección del inmueble") ya
está arreglado y en `master` (commits `1a280d8`, `f858bdb`). El build local
(`npm run build`) refleja el fix, pero **no se pudo desplegar a producción**
(`https://vecindata.dcarloabad.workers.dev`): el subdominio `dcarloabad`
pertenece a una cuenta de Cloudflare distinta a la mía (jessicapaolapu), y no
tengo credenciales para desplegar ahí.

**Pendiente / para el otro dev (dcarloa):** necesito que corras
`wrangler deploy` desde la cuenta que controla `dcarloabad.workers.dev`, o
que me pases un API Token de esa cuenta con permiso `Workers Scripts: Edit`
(dash.cloudflare.com → My Profile → API Tokens → plantilla "Edit Cloudflare
Workers"). Mientras tanto, producción sigue sirviendo el bundle viejo con el
bug sin arreglar.

Nota aparte: al intentar desplegar con un token de mi cuenta, Wrangler
registró un subdominio nuevo (`vecindata.vecindata-web.workers.dev`) que no
es el sitio real — queda ahí sin usar, se puede borrar cuando alguien tenga
un minuto (dash.cloudflare.com → Workers & Pages → vecindata-web → Delete).
