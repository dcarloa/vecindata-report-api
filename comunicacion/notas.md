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
