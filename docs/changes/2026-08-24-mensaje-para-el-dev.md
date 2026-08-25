# Contexto: reemplazo del login en VecinData

**Fecha:** 2026-08-24
**Autor:** dcarloa
**Repos afectados:** vecindata-report-api, vecindata-web

## Resumen

Estamos migrando el acceso al panel operador de una clave compartida a login
individual (email + contraseña). Antes de que sigas con tu implementación,
acá va la arquitectura actual y el diseño ya aprobado, para que ajustes lo
que ya escribiste o lo valides contra esto.

### Arquitectura actual (antes del cambio)

- Backend: `vecindata-report-api`, FastAPI en Cloud Run, **100% stateless —
  no hay base de datos**. Toda la config vive en `app/config.py`
  (pydantic-settings, lee de env vars / `.env`).
- El acceso a `POST /reports` hoy se valida con una sola clave compartida
  `OPERATOR_ACCESS_KEY`, enviada en el header `X-Operator-Key`
  (`app/main.py`, líneas ~90-93). Sin usuarios individuales.
- Frontend: `vecindata-web`, React en Cloudflare Workers. `AccessGate.tsx`
  pide esa clave, la guarda en `localStorage` (`vecindata_operator_key`) y la
  reenvía en cada request via `reportApi.ts`.

### Diseño aprobado

Spec completa en
[`docs/superpowers/specs/2026-08-22-login-platform-design.md`](../superpowers/specs/2026-08-22-login-platform-design.md).

Decisión clave: **sin base de datos nueva y sin plataformas de terceros** —
se evaluó usar una plataforma de user-management externa y se descartó
(dependencia de infraestructura ajena para un control de acceso crítico del
negocio). Se optó por login propio, mínimo, apoyado en secretos.

- Nuevo secreto `OPERATOR_USERS` (JSON con `email`, `password_hash` en
  Argon2, `role`: `admin`|`operator`) — reemplaza a `OPERATOR_ACCESS_KEY`.
- Nuevo secreto `JWT_SECRET` para firmar tokens HS256.
- Nuevo endpoint `POST /auth/login` — valida email+password contra
  `OPERATOR_USERS`, devuelve `{"token": "<jwt>"}` con `sub`/`role`/`exp` (7
  días). 401 genérico si falla (no revela si el email existe).
- `POST /reports` deja de leer `X-Operator-Key` y pasa a validar
  `Authorization: Bearer <jwt>`.
- Frontend: `AccessGate.tsx` cambia a dos campos (email/password), guarda el
  JWT en `localStorage` bajo `vecindata_session_token` (reemplaza
  `vecindata_operator_key`), y `reportApi.ts` cambia el header a
  `Authorization: Bearer`.
- **Fuera de alcance a propósito** (YAGNI, tamaño real del equipo = 2-3
  usuarios): sin auto-registro, sin recuperación de contraseña por email, sin
  enforcement real de roles todavía (el rol viaja en el JWT pero no se usa
  para autorizar — es para el futuro), sin refresh tokens, sin UI de gestión
  de usuarios (altas/bajas se hacen editando `OPERATOR_USERS` a mano y
  redeployando).
- Aprovisionamiento: un script manual (`scripts/hash_password.py`) genera
  los hashes Argon2 para pegar en el secreto — no se expone por HTTP.

## Archivos / contratos afectados

- `app/config.py`, `app/main.py` (backend)
- `AccessGate.tsx`, `reportApi.ts` (frontend)
- Secretos: `OPERATOR_USERS`, `JWT_SECRET` (nuevos), `OPERATOR_ACCESS_KEY`
  (se elimina al final)

## Acción requerida de la otra parte

Si tu implementación ya cubre esto, perfecto — solo confirmá que coincide en
estos puntos (nombres de secretos, endpoint, formato del JWT, y el scope
excluido arriba). Si divergiste en algo (por ejemplo si agregaste refresh
tokens, DB, o un provider externo), dejá tu propia notificación acá
explicando por qué antes de mergear, porque el diseño fue elegido
específicamente para no agregar infraestructura nueva.
