# Login propio (email + contraseña) en reemplazo de la clave de operador compartida

**Fecha:** 2026-08-22
**Repos afectados:** `vecindata-report-api` (backend), `vecindata-web` (frontend)
**Estado:** Aprobado, pendiente de implementación

## Contexto

Hoy VecinData controla el acceso al panel operador con una sola clave
compartida (`OPERATOR_ACCESS_KEY`), enviada por el frontend en el header
`X-Operator-Key` y guardada en `localStorage` bajo `vecindata_operator_key`
(`AccessGate.tsx`). El backend la compara en texto plano contra el valor
configurado (`main.py:92`). No hay usuarios individuales ni base de datos —
`vecindata-report-api` es hoy 100% stateless.

Se evaluó reemplazar esto por una plataforma de user-management de terceros
(`hx0Ventures user-mgmt`, propiedad del manager del dueño en otra compañía).
Se descartó: el dueño no tiene acceso admin ahí (depende de un tercero para
cualquier cambio de usuarios/roles/keys), y acoplar el control de acceso de
una herramienta que es su propio negocio a infraestructura ajena es un riesgo
de continuidad y de gobernanza de datos que no se justifica frente al tamaño
real del problema (un puñado de usuarios internos).

## Objetivo

Reemplazar la clave compartida por cuentas individuales (email + contraseña)
con un campo de rol (`admin` | `operator`) disponible para uso futuro, sin
agregar una base de datos ni dependencias externas nuevas.

## Fuera de alcance (YAGNI, explícitamente descartado)

- Auto-registro de usuarios.
- Recuperación de contraseña por email (no hay infraestructura de envío de
  correo en este repo).
- Enforcement de permisos distintos por rol — el rol viaja en el token para
  que agregarlo en el futuro sea trivial, pero hoy `admin` y `operator`
  tienen exactamente las mismas capacidades.
- Refresh tokens — el JWT dura 7 días; al expirar, se vuelve a pedir login,
  igual que hoy ocurre con un 401.
- Gestión de usuarios vía API/UI — agregar o quitar una cuenta se hace
  editando el secreto `OPERATOR_USERS` y redeployando, igual que se hace hoy
  con `OPERATOR_ACCESS_KEY`.

## Diseño

### Backend (`vecindata-report-api`)

**Nuevo secreto `OPERATOR_USERS`** (Secret Manager / env var), JSON:

```json
[
  {"email": "dcarloabad@gmail.com", "password_hash": "$argon2id$...", "role": "admin"},
  {"email": "jessicapaolapu@gmail.com", "password_hash": "$argon2id$...", "role": "operator"}
]
```

**Nuevo secreto `JWT_SECRET`**: string aleatorio usado para firmar/verificar
los tokens (HS256).

**Nuevo endpoint `POST /auth/login`**

- Request: `{"email": str, "password": str}`
- Busca el email en `OPERATOR_USERS`, verifica el password contra
  `password_hash` con Argon2.
- Si es válido: responde `{"token": "<jwt>"}`. El JWT incluye
  `sub` (email), `role`, `exp` (ahora + 7 días).
- Si no es válido (email no existe o password incorrecto): `401` con el
  mismo mensaje genérico en ambos casos, para no filtrar qué emails existen.
- Sin rate limiting propio en esta primera versión — el universo de usuarios
  es conocido y pequeño; si se vuelve necesario se agrega después.

**`POST /reports` cambia su verificación de acceso**

- Deja de leer `X-Operator-Key`.
- Lee `Authorization: Bearer <jwt>`, verifica firma y expiración con
  `JWT_SECRET`.
- Si falta el header, el token es inválido, o expiró: `401`.
- `settings.operator_access_key` y el header `X-Operator-Key` se eliminan
  del código (incluyendo el `WARNING` de arranque que advertía de acceso
  público).

**Nuevas dependencias** (`pyproject.toml`): `argon2-cffi`, `pyjwt`.

**Script auxiliar** (uso manual, no expuesto por HTTP): un script chico
(p. ej. `scripts/hash_password.py`) que tome una contraseña por stdin/arg y
devuelva el hash Argon2 a pegar en `OPERATOR_USERS`. Vive en el repo pero no
se ejecuta en producción.

### Frontend (`vecindata-web`)

**`AccessGate.tsx`**

- Cambia el formulario de un solo campo "Clave de acceso" a dos campos:
  email y contraseña.
- Al enviar, llama a `POST /auth/login`. Si responde 200, guarda el
  `token` recibido en `localStorage` bajo una nueva clave
  `vecindata_session_token` (reemplaza `vecindata_operator_key`).
- Si responde 401, muestra el mismo mensaje de error que hoy
  ("Clave incorrecta..." → se actualiza el texto a "Email o contraseña
  incorrectos.").

**`reportApi.ts`**

- El header cambia de `X-Operator-Key: accessKey` a
  `Authorization: Bearer <token>`.
- El manejo de 401 ya existente (`ReportApiError` con `status: 401` →
  `onAccessDenied` limpia el storage y vuelve a pedir login) se mantiene sin
  cambios estructurales, solo el nombre del dato que se limpia.

**Props/tipos**: todo lugar que hoy pasa `accessKey: string` (`OperatorPage`,
`BatchGenerator`, etc.) pasa a llamarse `sessionToken` para reflejar que ya
no es una clave estática compartida sino un token de sesión por usuario. Es
un rename mecánico, no cambia el flujo de props.

## Aprovisionamiento inicial

1. El dueño corre `scripts/hash_password.py` localmente para generar el hash
   de su propia contraseña y el de Jessica.
2. Pega ambas entradas en el secreto `OPERATOR_USERS` (Secret Manager) junto
   con `JWT_SECRET` (un valor aleatorio nuevo).
3. Comparte la contraseña elegida con Jessica por el mismo canal informal ya
   usado para compartir credenciales anteriormente.
4. Tras confirmar que el login funciona en producción para ambas cuentas, se
   elimina `OPERATOR_ACCESS_KEY` del entorno de Cloud Run.

## Testing

Backend (TDD, siguiendo el patrón ya usado en este repo):

- `POST /auth/login` con credenciales válidas → 200 + JWT bien formado
  (decodifica, contiene `sub`/`role`/`exp` correctos).
- `POST /auth/login` con email inexistente → 401, mensaje genérico.
- `POST /auth/login` con password incorrecto → 401, mismo mensaje genérico.
- `POST /reports` sin header `Authorization` → 401.
- `POST /reports` con JWT inválido/mal firmado → 401.
- `POST /reports` con JWT expirado → 401.
- `POST /reports` con JWT válido → 200 (comportamiento actual sin cambios).

Frontend:

- `AccessGate` renderiza los dos campos (email + password) en vez del
  campo único.
- Submit exitoso llama a `POST /auth/login` y guarda el token devuelto.
- Submit con 401 muestra el mensaje de error y no guarda nada.
- `reportApi.generateReport` envía `Authorization: Bearer <token>` en vez de
  `X-Operator-Key`.
- Un 401 en `generateReport` sigue disparando `onAccessDenied` igual que hoy.

## Riesgos aceptados

- Sin recuperación de contraseña: si alguien la olvida, el dueño genera una
  nueva con el script y actualiza el secreto manualmente. Aceptable al
  tamaño actual del equipo.
- Sin rotación automática de `JWT_SECRET`: si se compromete, se rota
  manualmente (invalida todas las sesiones activas, fuerza re-login).
