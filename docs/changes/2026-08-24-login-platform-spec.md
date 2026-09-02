# Reemplazo de OPERATOR_ACCESS_KEY por login propio (email + contraseña)

**Fecha:** 2026-08-24
**Autor:** dcarloa
**Repos afectados:** vecindata-report-api, vecindata-web

## Resumen

Se definió y aprobó el diseño para reemplazar la clave compartida
`OPERATOR_ACCESS_KEY` por login individual (email + contraseña, JWT de
sesión). Sin base de datos nueva, sin plataformas de terceros — todo vive en
secretos, igual que hoy. Spec completa en
[`docs/superpowers/specs/2026-08-22-login-platform-design.md`](../superpowers/specs/2026-08-22-login-platform-design.md).

## Archivos / contratos afectados

- Nuevo secreto `OPERATOR_USERS` (JSON: email, password_hash Argon2, role)
  reemplaza `OPERATOR_ACCESS_KEY`.
- Nuevo secreto `JWT_SECRET`.
- Nuevo endpoint `POST /auth/login`.
- `POST /reports` pasa de validar header `X-Operator-Key` a validar
  `Authorization: Bearer <jwt>`.
- Frontend: `AccessGate.tsx` y `reportApi.ts` (vecindata-web) cambian el
  formulario y el header de auth.

## Acción requerida de la otra parte

Si estás implementando esto (o algo relacionado), validalo contra la spec
antes de mergear — en particular los nombres de los secretos, la forma del
JWT (`sub`/`role`/`exp`) y el scope explícitamente excluido (sin
auto-registro, sin recuperación de contraseña por email, sin enforcement de
roles todavía, sin refresh tokens, sin UI de gestión de usuarios). Si
divergiste en algo, dejá una notificación acá explicando por qué antes de
mergear.
