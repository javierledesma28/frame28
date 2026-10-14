# frame28-memoria · evaluación del 2026-10-14 (F28-110)

## Activación

20 consultas de `trigger_queries.json` (10 sí, 10 no; 12 de entrenamiento y 8 de validación), clasificadas por
subagentes con las descripciones reales de las diez skills del plugin y tres genéricas (pdf, docx, frontend-design),
barajadas con una semilla por pasada. `claude -p` no sirve desde la app de escritorio (401), de ahí los subagentes.

| Versión de la descripción | Pasada | Modelo | Entrenamiento | Validación |
|---|---|---|---|---|
| 1 | 1 | Opus | 12/12 | 8/8 |
| 1 | 2 | Sonnet | 12/12 | 8/8 |
| 1 | 3 | Haiku | 11/12 | 8/8 |
| 2 | 4 | Haiku | 9/12 | 6/8 |
| 2 | 5 | Haiku | 12/12 | 8/8 |
| 2 | 6 | Sonnet | 12/12 | 8/8 |

- El fallo de la versión 1 (Haiku): «saca los colores y el logo de esta web para el rótulo del vídeo que estoy montando»
  iba a memoria. La versión 2 añade esa frontera al «No usar» (marca para el vídeo en curso → frame28-director).
- Los cinco fallos de la pasada 4 van todos a la skill de entrada `frame28` («mi marca», «mis campañas» sin nombrar
  Frame28), cuya descripción pone esos ejemplos. Esa skill las lleva a la misma tarea (`frame28_start` con `memoria`, o
  `frame28_campanas`), así que el resultado para el usuario es el mismo. No se toca su descripción (probada en F28-239).
- Ningún falso positivo de la versión 2 en las 60 clasificaciones: montar una campaña, shorts, manuales de identidad,
  Canva, fichas de Amazon y la marca para un vídeo suelto no la disparan.

## Calidad

Los tres casos de `evals.json`, con la skill cargada y sin ella, con Sonnet y Haiku, pidiendo el plan de llamadas (sin
ejecutar; las herramientas del MCP descritas como en `server.py`).

| Caso | Con skill (Sonnet / Haiku) | Sin skill (Sonnet / Haiku) |
|---|---|---|
| 1 crear la Memoria | `frame28_start("memoria")` primero, nada inventado / igual | igual; Sonnet lanza en paralelo un WebFetch de la web antes de tener el método / igual |
| 2 brief de campaña | `frame28_campana(acme-kits, black-friday)`, sin montar / igual | igual / igual |
| 3 crear campaña sin cuenta | estudio de frame28.app; `mcp login plugin:frame28:frame28` o `/mcp`, sesión nueva; no lanza login para comprobar / igual | estudio; solo `/mcp` (no existe en la app de escritorio) y «puede que» haga falta una sesión nueva / `/mcp` y sesión nueva |

Con las herramientas a la vista, las descripciones del MCP ya enrutan bien: la skill aporta sobre todo la activación sin
nombrar Frame28 y el camino de entrada que funciona en la app de escritorio.
