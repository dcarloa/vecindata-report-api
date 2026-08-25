# Notificaciones de cambios

Carpeta para que los devs (o sus agentes) se avisen entre sí sobre cambios
relevantes en curso, sin depender de Slack/email ni de estar online al mismo
tiempo. Es texto plano versionado en git — se ve con `git pull`, no requiere
ninguna herramienta nueva.

## Cuándo crear una notificación

Cuando el cambio afecta a alguien más que no está mirando tu código en este
momento: un contrato de API, un secreto/env var nuevo o renombrado, una
decisión de arquitectura o de scope, o algo que bloquea o modifica el trabajo
de otra persona. No hace falta para cambios internos que no cruzan esa
frontera (un refactor interno, un fix de un bug aislado).

## Cómo

1. Crea un archivo `AAAA-MM-DD-<slug>.md` en esta carpeta usando
   [`TEMPLATE.md`](./TEMPLATE.md).
2. Commitealo junto con (o inmediatamente después de) el cambio real.
3. La otra persona lo ve la próxima vez que hace `git pull` / revisa el repo.

No hay proceso de "cerrar" una notificación — quedan como historial. Si algo
queda obsoleto, se nota en el propio archivo o en uno nuevo que lo reemplace,
no se borra.

## Antes de empezar a trabajar

Revisa los archivos de esta carpeta con fecha posterior a tu último pull para
ver si hay algo que afecte lo que vas a hacer.
