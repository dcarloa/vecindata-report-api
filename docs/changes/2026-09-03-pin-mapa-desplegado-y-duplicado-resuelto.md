# Fix del pin del mapa desplegado a producción; se resolvió un choque con trabajo local sin pushear

**Fecha:** 2026-09-03
**Autor:** dcarloa
**Repos afectados:** vecindata-web

## Resumen

Dos cosas:

1. **Deploy hecho.** Corrí `wrangler deploy` desde mi cuenta de Cloudflare.
   Producción (`https://vecindata.dcarloabad.workers.dev`) ya sirve el
   bundle nuevo (`index-Dn9nYvqV.js`), con el fix del `dragend` incluido.
2. **Encontré por qué el pin "vivía en producción pero no en git":** tenía
   29 commits locales sin pushear en `vecindata-web` (nunca los subí a
   `origin`), y ahí ya existía esta misma funcionalidad — un componente
   `PinMap` compartido por el formulario individual y la carga masiva por
   CSV, más completo que `MapPositionPicker`. Por eso no aparecía en tu
   `git log`: no era que faltara reconstruirla, es que yo no la había
   publicado.

## Qué hice con el conflicto

Al mergear tu rama con la mía, `ReportForm.tsx`/`googlePlaces.ts` quedaron
en conflicto real (dos implementaciones de lo mismo). Resolví quedándome
con `PinMap`/`googleMap.ts` (la más completa) y le apliqué tu fix real —
`google.maps.event.addListener` en vez de
`marker.addEventListener("dragend", ...)`, que era la causa raíz correcta
que encontraste. Borré `MapPositionPicker` por quedar redundante. Tests y
`tsc --noEmit` en verde antes de pushear.

## Pendiente de tu lado

- El subdominio suelto `vecindata.vecindata-web.workers.dev` que quedó de
  tu intento de deploy vive en tu cuenta de Cloudflare — bórralo cuando
  tengas un minuto (dash.cloudflare.com → Workers & Pages → esa entrada →
  Delete). No lo puedo tocar yo.
- De acá en más voy a pushear seguido para que esto no se repita.

## Acción requerida de la otra parte

Ninguna — solo aviso. Si notás algo raro en el pin en producción, avisá acá.
