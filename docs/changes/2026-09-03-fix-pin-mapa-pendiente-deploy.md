# Fix del pin del mapa listo, pendiente de deploy a producción

**Fecha:** 2026-09-03
**Autor:** jessicapaolapu
**Repos afectados:** vecindata-web

## Resumen

El bug reportado el 2026-08-24 (arrastrar el pin del mapa actualizaba
`lat`/`lon` pero no el campo "Dirección del inmueble") ya está arreglado y
mergeado en `master` de `vecindata-web` (commits `1a280d8`, `f858bdb`). El
build local (`npm run build`) refleja el fix, pero **no pude desplegarlo a
producción**.

## Archivos / contratos afectados

- `vecindata-web`: build de producción en
  `https://vecindata.dcarloabad.workers.dev` — sigue sirviendo el bundle
  viejo (`index-Cd0qacXA.js`) con el bug sin arreglar.
- El subdominio `dcarloabad.workers.dev` vive en una cuenta de Cloudflare que
  no es la mía (jessicapaolapu) — no tengo credenciales para desplegar ahí.

## Acción requerida de la otra parte

Necesito que corras `wrangler deploy` desde `vecindata-web` (con `npm run
build` primero) usando la cuenta de Cloudflare que controla
`dcarloabad.workers.dev`, o que me pases un API Token de esa cuenta con
permiso `Workers Scripts: Edit` (dash.cloudflare.com → My Profile → API
Tokens → plantilla "Edit Cloudflare Workers") para hacerlo yo.

Nota aparte: al probar el deploy con un token de mi propia cuenta, Wrangler
registró un subdominio nuevo sin usar (`vecindata.vecindata-web.workers.dev`)
que se puede borrar desde el dashboard de esa cuenta cuando alguien tenga un
minuto — no afecta producción.
