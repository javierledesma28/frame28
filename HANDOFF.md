# Traspaso — estado del proyecto a 2026-10-01 (PC, noche; cierre tras relevamiento)

Para retomar Frame28 desde otra cuenta de Claude Code **sin historial de conversación**, sobre este mismo
repositorio local (`C:\Workspaces\personal\Skill-Director`, Windows 11). Lee primero [CLAUDE.md](CLAUDE.md) (qué es,
estructura, cómo se ejecuta, convenciones, decisiones, trampas). Este fichero es el estado verificado, lo hecho por
sesiones, lo que quedó a medias, los bloqueos y lo que toca ahora. Lo que no esté aquí o en `CLAUDE.md` no existe para
la sesión siguiente.

**Cómo quedó git al cerrar:** rama `main` = `origin/main` (todo subido), árbol limpio, tag `v0.4.0` en `4e7a6cb`, release
publicada. **Desde el 2026-10-01 (noche) el remoto va por SSH** (`git@github-jl28:javierledesma28/frame28.git`), igual que
los demás repos de Think28, y **git lo gestiona Claude** (commits, ramas, push, PRs, releases): ver `CLAUDE.md` §Convenciones.

## Qué es esto y por qué

**Frame28** es un producto de **Think28** (empresa de Javier Ledesma, `https://t28.io`; nada de branding
Fundanet/Semicrol aquí). Convierte un vídeo de una persona hablando a cámara, o un vídeo ya producido, en el paquete que
hace falta para vender: el largo montado con la marca, shorts verticales con ganchos distintos, portada y ficha de producto,
subtítulos y versiones en otros idiomas con los mismos tiempos. Dos piezas: un **plugin de Claude Code** (ocho skills;
Claude dirige y escribe el storyboard JSON) y un **CLI Python `frame28`** (42 órdenes en 20 módulos; los pasos
deterministas). El compositor es **HyperFrames** (HTML + GSAP), todo en local. El plugin y el CLI son MIT y públicos
(`https://github.com/javierledesma28/frame28`, web `https://frame28.t28.io`).

**Giro del 2026-09-30:** Frame28 es un **producto monetizable** con dominio **frame28.app**. Se vende como servicio operado
por Think28 (Launch 990 USD, Studio 2.490 USD/mes), implantación en el cliente (Team 2.900 + 490 USD/mes) y, solo con
demanda, plataforma (Cloud). Precios **validados por Javier el 2026-10-01** (`research/07` §2 = landing en `site/`).
Primer cliente objetivo: **Cliente A** (nombre en clave, ver §Confidencialidad). **Regla de trabajo de Javier:** todo lo que
se aprende con un caso se capitaliza en el plugin (CLI, `doctor`, validaciones, skills, referencias), no en docs.

**Decisiones del 2026-10-01 (noche):** (1) frame28.app se despliega en el **VPS t28server** por túnel de Cloudflare, no en
Pages; está en vivo (ver §Estado). (2) **Giro de producto**: Frame28 deja de ser un servicio y pasa a ser **una plataforma:
plugin de pago en el Claude Code del cliente + frame28.app como panel de control** (cuenta, membresía, Memoria de marca,
campañas, revisión, aprendizaje), con el plugin autenticado por MCP remoto con OAuth y recibiendo ese contexto. Todo está
en **`research/08-plataforma-frame28-app.md`**: qué cambia, las cuatro piezas, el flujo de punta a punta, la Memoria de
marca (schema v1), campañas y entregables, lo que permite Claude Code (verificado en su documentación), arquitectura y
stack (Next.js + Tailwind + GSAP; FastAPI + MCP en Python; Think28 ID sobre el Entra External ID de Synapse28; Paddle
reutilizado; Postgres con RLS; R2; Docker + túnel), referencias web verificadas, dirección de diseño y copy del hero,
tiers con cifras a validar, plan por fases y **seis decisiones pendientes de Javier (§14)**. La landing en vivo todavía
vende el servicio: reescribirla es la **fase 0**.

## Estado: qué funciona hoy (verificado ejecutando, 2026-10-01 entre las 18:50 y las 19:40)

| Qué | Evidencia |
|---|---|
| Enfoque de producto | **Giro del 2026-10-01 (noche)**: de servicio a plataforma (plugin de pago + frame28.app como panel). Definición en `research/08` con las **seis decisiones de Javier respondidas** y los **precios fijados** (Creator 79 · Brand 199 · Agency 499 USD/mes, anual ×10; Studio 990 pago único y 2.490/mes) y el **control de uso** (§7 bis: el plugin es una cáscara que solo funciona autenticado; el método del director y la Memoria se sirven por MCP según el plan; cuenta gratuita obligatoria para probar). **La landing en vivo ya vende la plataforma** (fase 0 desplegada el 2026-10-01 ~23:05). La plataforma se construye en el repo privado `javierledesma28/frame28-app` (`C:\Workspaces\personal\frame28-app`, inicializado con README, CLAUDE.md, HANDOFF y `docs/plataforma.md`) |
| Identidad (Think28 ID para Frame28) | **Tenant externo `frame28ciam.onmicrosoft.com`** (`e26abf56-cc6a-4338-9fbf-732c7cc9bc94`, Entra External ID, Europa/ES) creado el 2026-10-01 por API con la sesión de `javier@t28.io`; apps `frame28-api` (scope `frame28.access`), `frame28-web`, `frame28-claude-code` (público, PKCE) y `frame28-admin-tools` con preautorización y consentimiento. **Pendientes**: flujo de alta/entrada (Graph 400), secreto de la web, Google, y mover el recurso Azure de `sub-azurehub-prod` a una `sub-frame28-prod` que Javier debe crear en el portal. Todo en `C:\Workspaces\personal\frame28-app` (`docs/identidad.md`, `scripts/identidad/`, su HANDOFF) |
| Versión publicada | **v0.4.0** (release en GitHub, tag en `4e7a6cb`); 0.4.0 en `__init__.py`, `plugin.json`, `marketplace.json`, README |
| CLI | `frame28 --version` 0.4.0 (editable, con extra `gpu`); `frame28 doctor` «Todo listo», incluida la fila nueva **gpu (transcripción) ✓ 1 GPU CUDA con cuBLAS y cuDNN**; opcionales en aspa: gpu (onnxruntime) y claves de B-roll |
| Pruebas | **116 passed en ~3 s** (`cd plugin/cli && uv run --group dev pytest`) |
| Plugin | `claude plugin validate <ruta absoluta>/plugin` pasa; caché instalado 0.4.0 (18:31) **idéntico** a `plugin/skills/`; `claude plugin update frame28@think28` → «already at the latest version (0.4.0)» |
| Storyboards | 11 de 11 versionados válidos (`frame28 storyboard validate`) |
| Regresión | `poc/clip-javier/storyboard-gsap.json`: build sin avisos, check ✓, **render 1 m 16 s con `--workers 10`** (89–105 s con los trabajadores por defecto); hoja de contacto correcta |
| `release-check.py` | 4 bloqueos esperados (árbol, tag local, tag remoto, release «ya existe») hasta subir `__version__`; **confidencialidad: sin rastro** en ficheros, historia, tags y releases |
| Sitio del producto | **Rehecho en Next.js en el repo `frame28-app` (`web/`) y en vivo desde el 2026-10-02 09:33 UTC** con el visto bueno de Javier (entrada animada, comparador, storyboard en vivo); se publica con el `deploy/deploy.sh` de ese repo. El `deploy/deploy.sh` de aquí ya no sube nada salvo con `FRAME28_LEGACY_SITE=1` (vuelta atrás). La landing estática anterior, por si hace falta: `uv run --with markdown python site/build.py` → 40 páginas · plazas Fundadores 25 · caso público False · **48 huecos `[[…]]`** en condiciones; el build es determinista (no ensucia el árbol). En vivo (fila frame28.app) |
| Web del plugin | frame28.t28.io `/`, `/roadmap/`, `/instalar/`, `/install.ps1` → HTTP 200 |
| frame28.app | **EN VIVO desde el 2026-10-01 a las 19:55** desde t28server: `/opt/frame28` con `frame28-web` (nginx) y `frame28-tunnel` arriba, `site/` = HEAD por hash (`deploy/deploy.sh --check`); CNAME `frame28.app` y `www` → túnel `frame28` (id `8d6534bd-e051-4b5f-9a94-8b8c87aa0b8a`), rutas puestas por Javier en el panel. Verificado desde fuera: `/`, `/en/`, `/fundadores/`, `/contacto/`, `/condiciones/` y assets → 200 con CSP, HSTS, nosniff, DENY; `/founders`→`/en/founders/` 301, `/roadmap`→frame28.t28.io 302, `/casos/*`→`/contacto/` 302, `www`→apex 301; `/kb`, `/curso`, `/en/course`, `/src`, `/content` → 404 (a propósito); `/api/contact` → 503 (hasta el Worker) |
| Roadmap | `docs/roadmap/index.html`: 6 versiones, 67 ítems (**42 hechos, 4 a medias, 21 pendientes**; «Página de producto en frame28.app» cerrada el 2026-10-01 al salir en vivo); siguiente: «B-roll probado contra la API real». Artefacto de claude.ai en la versión 6: **republicar** desde la sesión que lo posee (URL en §Qué se ha hecho) |
| Actualización de usuarios | **verificado en un entorno aislado**: `uv tool upgrade frame28` mueve una instalación desde git al último commit en 14 s aunque la versión no cambie; repetir el instalador (`--force`) también. `claude plugin update` solo actúa si cambia la versión del plugin |
| Dependencias | solo `av` 17.1 → 19 desactualizado (pin `<18` deliberado); **HyperFrames 0.8.105 y GSAP 3.15.0** desde el 2026-10-01 (regresiones de clip-javier y clip-grabado en verde) |
| Git | `main` = `origin/main`; CI de GitHub Actions en verde (`tests`, 19 s); **remoto SSH `github-jl28`** (`ssh -T git@github-jl28` → «Hi javierledesma28!», `git ls-remote origin` verificado): el push ya no depende de la credencial HTTPS guardada en Windows, que es la corporativa y daba 403. `gh` tiene la corporativa activa: `gh auth switch --user javierledesma28` solo para `gh release` y `gh api`. La rama obsoleta `origin/main-ky21ae` se borró el 2026-10-02 con el visto bueno de Javier |
| Casos reales | `poc/clip-javier`, `clip-auriculares`, `clip-whatsapp`, `clip-demo`, `clip-grabado` (versionados: README, storyboard, cuts) y **`poc/clip-acrilico` (solo local, nada versionado)** |

## Confidencialidad del primer cliente (regla de Javier, 2026-10-01)

El cliente objetivo **no se nombra en ningún fichero del repo ni del sitio** (el repo es público y la captación va en
paralelo). Nombre en clave: **Cliente A**; producto: **Engraver Pro™**; web: `the-brand.com`; carpetas de sus casos:
`poc/clip-grabado` (primer tutorial) y `poc/clip-acrilico` (segundo); marca local `cliente-a` y la de nombre real en
`poc/clip-grabado/work/brands/` y `poc/clip-acrilico/work/brands/` (ignoradas). Todo lo que lo nombra (propuesta, brief,
guion, paquete de envío, bundle de la historia antigua) vive en `_private/` (ignorado). El sitio publica el caso anónimo
hasta tener permiso escrito (`site/build.py` `CONFIG["case_public"]` + `case_brand`).

Historial reescrito con `git filter-repo` el 2026-10-01 (cero coincidencias en todos los objetos); tags `v0.2.0` y
`v0.3.0` recreados sobre la historia nueva; notas de la release v0.3.0 corregidas.

**Controles permanentes:** (1) la fila bloqueante **confidencialidad** de `scripts/release-check.py` lee
`_private/confidencial.txt` (no versionado; existe en este PC) y busca los términos en ficheros versionados y sin ignorar,
en mensajes y diffs de todos los refs, en tags y en títulos/notas de las releases y descripción del repo; informa del
sitio, nunca del término. (2) `.gitignore` ignora `*.source.json`: el sidecar de `frame28 fetch` nombra al dueño del vídeo
y `poc/clip-acrilico/input.source.json` **solo lo protege esa línea** (commiteada en este cierre). Lo que se baje y nombre
al cliente va a `_private/`, nunca a una carpeta suelta del repo.

## Qué se ha hecho, por sesiones

### 2026-09-24 a 2026-09-29 — research, plugin base, v0.1.0 y v0.2.0
Análisis del vídeo de referencia, repos, PoC HyperFrames vs Remotion, roadmap de 18 features (`research/01`–`04`);
plugin con 5 skills y CLI base; brand kit, gráficas, gestos, jump cuts, limpieza de audio, GSAP con plugins; repo
público, GitHub Pages con dominio, deck de guía, instaladores; releases v0.1.0 y v0.2.0.

### 2026-09-30 (PC) — instalación, subtítulos, caso Cliente A, vídeo que vende, release 0.3.0, roadmap, giro a producto
Instaladores y asistente web; lienzo vertical y cuadrado; subtítulos por palabras y SRT/VTT; B-roll (sin claves);
`fetch`, `brand from-site`, `graphics` (OCR), `reframe`; overlays de venta, fábrica de shorts, ganchos, `cover`,
`i18n`; relevamiento e higiene (versión única, cargador tolerante, `doctor`, `release-check`); tag y release v0.3.0;
roadmap visual; `research/06` (monetización) y `research/07` (producto frame28.app, plan de 7 días).

### 2026-09-30 (nube, noche) — suite de pruebas y `reframe-map`
82 pruebas sobre módulos puros; dos regresiones arregladas; `frame28 reframe-map`.

### 2026-10-01 (nube) — plan de siete días, confidencialidad y preparación de la 0.4.0
Precios validados; textos de la landing ES/EN y contrato base (`site/content/`); sitio completo en `site/` (build.py,
Pages Function del formulario, `_redirects`, `_headers`, `wrangler.toml`, README de despliegue, `og.png`); propuesta al
cliente (privada); anonimizado y reescritura del historial; base de conocimiento (8 artículos ES/EN) y curso (6 lecciones);
`log.py` + `frame28 report`, `clips batch`, ganchos `statement`; brief y plantilla de la segunda muestra (privados);
textos de lanzamiento (`site/content/lanzamiento.md`); release 0.4.0 preparada; `frame28 clips markers`.

### 2026-10-01 (PC, mediodía) — tags, release 0.4.0 y control de confidencialidad
Tags `v0.2.0`/`v0.3.0` recreados y subidos; notas de v0.3.0 corregidas; firma de las condiciones con guiones bajos
escapados; **release v0.4.0 publicada** (`4e7a6cb`); fila de confidencialidad en `release-check` (98 pruebas entonces);
material del caso movido a `poc/clip-grabado/` y `_private/cliente-a/`.

### 2026-10-01 (PC, tarde) — segunda muestra del Cliente A, capitalización y transcripción en GPU
Reconstruido desde `poc/clip-acrilico/.frame28/log.jsonl` (109 órdenes, 2 h de máquina) porque no quedó anotado:
1. **16:18–18:44, `poc/clip-acrilico/` (ignorado):** `fetch` del segundo tutorial → `prep` → `transcribe` (CPU, 179 s,
   `--script work/nombres.txt`) → `graphics` → `clips markers` → storyboard (`work/make_storyboard.py`,
   `work/make_strings.py`) → `clips plan` + 3 shorts (`clips cut` + `reframe --mode blur`) → `clips batch --no-render`
   (el primer intento con `--brand <nombre>` falló; con la ruta `work/brands/<marca>.json` funcionó) → `i18n` ES y DE →
   cinco rondas de revisión (`work/rev*_sheet.png`) → **renders finales de las tres versiones largas con `--workers 10`
   (~455 s cada una, frente a ~700 s sin la opción)**, 6 shorts (`out/shorts/s{1,2,3}-hook{0,1}.mp4`), 4 portadas
   (`out/cover-yt-{en,es,de}.png`, `out/cover-pdp.png`) y 3 SRT. Prueba NVENC vs x264 en `work/gpu/`.
2. **Cuatro commits (17:27–18:28)** que capitalizan esa sesión: subtítulos y tramos por frase completa, hoja de contacto
   del vídeo entero, CTA en la franja libre, `clips batch --keep`, SRT desde un storyboard traducido; aviso de gancho que se
   parte; `render --workers/--gpu`; interlineado con mayúsculas acentuadas. 113 pruebas.
3. **Transcripción en GPU (después de las 18:28, commiteada en este cierre):** extra `frame28[gpu]` en
   `plugin/cli/pyproject.toml` (`nvidia-cublas-cu12`, `nvidia-cudnn-cu12`), `env.cuda_ready()`/`enable_cuda_dlls()`,
   `transcribe --device auto` (cuda/float16 con caída a CPU si la GPU falla a mitad), fila en `doctor`, prueba
   `test_transcribe_device_auto_picks_gpu_only_when_ready`. Librerías instaladas en el entorno de la herramienta; una
   transcripción real en GPU a las 18:42 (`poc/clip-acrilico/work/gpu/asr/`): **42,4 s frente a 178,7 s en CPU** para el
   mismo audio de 160 s (4,2×, con un render ocupando la máquina; medido por la sesión de la tarde).

### 2026-10-01 (PC, noche) — relevamiento completo y cierre
1. **Relevamiento** sin tocar código (estructura, git, 12 comprobaciones ejecutadas: tabla de §Estado). Hallazgos: el
   HANDOFF del mediodía decía «árbol limpio» con 4 commits sin subir y 8 ficheros sin commitear; 98→114 pruebas;
   roadmap 29→30 hechos; la segunda muestra hecha y sin anotar; `.frame28/log.jsonl` versionado por accidente;
   `input.source.json` del cliente protegido solo por una línea sin commitear; sin CI; `uv.lock` ignorado a propósito.
2. **README §Actualizar** (pedido expreso de Javier), `docs/instalar.md` §Para actualizar y una línea en el asistente web
   `docs/instalar/index.html`, con órdenes **verificadas** (ver §Estado). Fila de `doctor` «última release» pendiente.
3. **Permisos del token de Cloudflare** acordados (§Cloudflare); Javier los crea.
4. **Commits de cierre**: `.gitignore` + log fuera del índice; GPU en `transcribe`; docs de actualización; `CLAUDE.md` y
   este traspaso. Memoria de la cuenta de Claude actualizada (no viaja: todo lo duradero está aquí).
5. **Forma de trabajar con git, validada contra Synapse28 y TheValley28** (Javier: «siempre lo has gestionado vos»; en esos
   repos Claude commitea, pushea y abre PRs sin que él pegue comandos): remoto cambiado a SSH `github-jl28`, convención
   escrita en `CLAUDE.md`. El 403 del push por HTTPS era Git Credential Manager con la credencial corporativa guardada, no
   `gh`. Chapita no es un repo git.
6. **Despliegue de frame28.app en t28server** (decisión de Javier: VPS en vez de Cloudflare Pages). Verificado antes: SSH al
   VPS, patrón nginx + cloudflared de tino/ramplas/savia, `/opt/frame28` libre, token de Cloudflare activo (cuenta T28, zona
   `27b1c228…`). Hecho: `deploy/` en el repo (compose, nginx.conf que traduce `_headers`/`_redirects`, remote-up.sh,
   deploy.sh con backup y verificación por hash), CNAME apex y `www` por API al túnel `frame28` que Javier creó en el panel
   (el token no tiene permiso de túneles: 401), `.env` con el token del túnel escrito en el servidor (600), contenedores
   arriba, sitio = HEAD. Tres fallos de Windows por el camino, ya en Trampas de `CLAUDE.md` (CRLF del editor, `*` de
   `sha256sum`, `ssh -T`). Javier puso las dos rutas públicas del túnel en el panel y **frame28.app quedó en vivo a las
   19:55**, verificado desde fuera.
7. **Giro de producto y `research/08`.** Javier trajo su análisis de 22 webs de referencia (`referencias-web-t28.md`, fuera
   del repo) y, al ver la landing, corrigió el enfoque: no «nos envías el vídeo», sino **plugin de pago + frame28.app como
   panel de la marca y las campañas**. Se verificaron los stacks de las 22 webs contra su HTML (la mitad de las ⚠️ cambian),
   la documentación de plugins y MCP de Claude Code (OAuth remoto con cliente preconfigurado, `userConfig` sensible,
   `${CLAUDE_PLUGIN_DATA}`, `bin/` no en claude.ai), lo que Synapse28 ya tiene (FastAPI + RLS, Entra External ID, Paddle
   con filtro por producto) y la capacidad del VPS (7,7 GB RAM, 4 CPU: cabe la app, no un render en la nube). Resultado:
   `research/08-plataforma-frame28-app.md`.
8. **Decisiones, control de uso, fase 0 y repo nuevo.** Javier respondió las seis decisiones (copy sí; precios «propón tú e
   implementemos»; tenant CIAM propio de Frame28; open core; repo `frame28-app`; Cliente A → resuelto como Studio) y planteó
   el **control de uso** («solo quien se autentica y tiene membresía puede usar el plugin»): respuesta en `research/08` §7 bis
   (cáscara + MCP remoto, hooks, licencia en el motor, servidor en tiempo real; cuenta gratuita obligatoria en vez de modo
   anónimo). **Precios fijados** en §11. **Fase 0 desplegada**: landing ES/EN reescrita (hero, tres pasos, terminal de
   ejemplo, Memoria de marca, métricas de la segunda muestra, precios Creator/Brand/Agency + Studio + Open + Cloud, acceso
   anticipado con 25 plazas, FAQ nueva, contacto), `build.py` con las opciones del formulario nuevas y el aviso «versión en
   revisión» en las condiciones (`CONFIG["terms_draft"]`), `site.css` con `.term` y `.notice`; verificado en vivo. **Repo
   `frame28-app`** (privado, creado por Javier) inicializado y subido por SSH con README, CLAUDE.md, HANDOFF y
   `docs/plataforma.md`. Nada de código de la plataforma todavía.
9. **Identidad de Frame28 creada** (en el repo `frame28-app`, con autenticación interactiva de Javier por códigos de dispositivo
   y el resto por API): tenant externo `frame28ciam`, cuatro app registrations con scope, preautorización y consentimiento.
   Lo que no salió: la suscripción `sub-frame28-prod` por API (la cuenta de facturación es MOSP: portal) y el flujo de
   alta/entrada por Graph (400 con permisos correctos; reintentar o centro de administración). Detalle, scripts y pasos en
   `frame28-app/HANDOFF.md`, `docs/identidad.md` y `scripts/identidad/README.md`. `az` quedó con la suscripción por defecto
   `sub-azurehub-prod` y una cuenta de nivel de tenant en `frame28ciam`.

## Lo que toca ahora (en este orden)

**Novedad 2026-10-02: v0.5.0 publicada.** El plugin es una cáscara que entra con la cuenta de Frame28: `.mcp.json` →
`https://frame28.app/mcp` (login de Frame28 ID con email y código; la fachada OAuth del servidor hace que no haga falta
client id) y ocho skills que piden el método a la cuenta con `frame28_start(tarea)`. El método del director (cuerpos de las
skills y las cinco referencias) se mudó al repo privado `frame28-app` (`api/frame28_api/metodo/`), que es ahora la fuente de
verdad: **cambiar el criterio de montaje = editar allí y desplegar**. Probado por Javier en una sesión nueva de la app con
el plugin instalado: `frame28_start` responde con su cuenta, plan Gratis (reglas de demo: marca think28 y «Hecho con
Frame28») y el método. Pendiente de la v0.5 en adelante: hooks de sesión y licencia en el CLI (research/08 §7 bis, capas 2
y 3), planes de pago con Paddle, la Memoria de marca servida por el MCP.

**Memoria de marca en vivo (2026-10-02, repo `frame28-app`)**: cada cuenta de pago guarda la Memoria de sus marcas
(Context Pack v1, versionada, Postgres con seguridad por fila) y el MCP la sirve al plugin (`frame28_memoria`); el método
la usa al montar y tiene una tarea `memoria` para crearla desde la web de la marca. Sin cambios en el plugin público.

**Antes que nada: la plataforma.** Las seis decisiones de `research/08` §14 están respondidas, la **fase 0 está hecha** (la
landing en vivo vende la plataforma) y la **identidad está creada** (tenant `frame28ciam` y sus apps). Lo siguiente vive en el
repo **`frame28-app`** (`C:\Workspaces\personal\frame28-app`, leer su `HANDOFF.md`): (a) cerrar el **flujo de alta/entrada**
(reintento por API o centro de administración) y que Javier cree **`sub-frame28-prod`** en el portal para mover allí el
recurso del tenant, (b) el *spike* de un día (MCP remoto mínimo validando los JWT del tenant → `/mcp` en Claude Code con el
cliente público `frame28-claude-code` → Paddle sandbox), (c) Paddle, R2, email, Google como proveedor, (d) la fase 1. En **este** repo, lo que toca para la plataforma es la
**v0.5 del plugin como cáscara** (`.mcp.json` remoto, `hooks.json`, skills mínimas que llaman a `frame28_start`, `frame28
deliver`, `frame28 context apply`, `frame28 license set/whoami`): se hace cuando el MCP del spike responda. Los puntos
siguientes siguen valiendo; el 3 (formulario, Access, Turnstile) se hace sobre el sitio estático y se hereda en la app.
Pendiente menor de la fase 0: los artículos de la KB y el curso siguen escritos para el servicio (reescribir con la
Memoria de marca cuando exista la app); `og.png` ya está regenerada con el claim de la plataforma.

1. **Revisar la segunda muestra** del Cliente A en movimiento y de oído (lista en `_private/cliente-a/dia6-estado.md`;
   copias en `_private/cliente-a/muestras/`). Hasta entonces no se envía nada.
2. **Token de Cloudflare** (Javier lo crea con los permisos de §Cloudflare y lo deja en la variable de entorno de usuario
   `CLOUDFLARE_API_TOKEN`, más `CLOUDFLARE_ACCOUNT_ID`; hay que reiniciar la app de Claude para que la shell lo vea).
   Primero verificación de solo lectura: `curl -s -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN"
   https://api.cloudflare.com/client/v4/user/tokens/verify` y `npx wrangler whoami`.
3. **Completar frame28.app** (en vivo desde el 2026-10-01, ver §Estado): (c) **Formulario**: Worker en la ruta `frame28.app/api/contact*`
   con el código de `site/functions/api/contact.js` adaptado (`export default { fetch }`) y el binding de email; exige
   Email Routing activo en la zona con `hola@frame28.app` reenviando al buzón real de Javier (permiso del token o panel).
   Hasta entonces nginx devuelve 503 y la página enseña su fallback. (d) **Access** con PIN por email sobre `/kb`, `/curso`,
   `/en/kb`, `/en/course` (organización Zero Trust: permiso `Access: Organizations` en el token o crearla en el panel) y
   quitar las dos líneas de 404 de `deploy/nginx.conf`. (e) **Turnstile** en el formulario. Cada publicación del sitio es
   `deploy/deploy.sh` tras commitear; añadirlo como paso del `release-check`.
4. **Decisiones pendientes de Javier** (preguntadas el 2026-10-01, sin respuesta por falta de tokens):
   - (a) GPU: **resuelta**, medida (42,4 s frente a 178,7 s) y anotada en `CLAUDE.md`.
   - (b) `poc/clip-acrilico`: versionar README + storyboard + `clips.json` anonimizados como los otros casos, o dejar
     todo en `_private/`. En cualquier caso: copiar `out/` (3 MP4, 6 shorts, 4 portadas, 3 SRT) a
     `_private/cliente-a/muestras/` y anotar `frame28 report note "director" --tokens <n>` en `poc/clip-acrilico/`.
5. **KB y curso para la plataforma**: siguen escritos para el servicio (tiers Launch/Studio/Team, «lo que tienes que
   mandar»); se reescriben con la Memoria de marca cuando exista la app. `og.png` ya lleva el claim de la plataforma
   (regenerada el 2026-10-01 desde `site/assets/og.html` con Chrome headless).
6. **Condiciones**: rellenar los 48 `[[…]]` de `site/content/condiciones.es.md` y `terms.en.md` (datos fiscales, fuero,
   buzón, IVA, idioma que prevalece, música, arrastre en Studio, medio de pago), pasarlas por el asesor y regenerar.
7. **Grabar la lección 1** del curso (`site/content/curso/es/01-que-es-frame28.md`), montarla con Frame28 y poner la URL
   en `video:`.
8. **Día 7**: lista previa de `_private/cliente-a/dia7-envio-final.md` y enviar; publicar `site/content/lanzamiento.md`
   el día que el sitio esté en vivo con Access.
9. Claves de Pexels y Pixabay en `~/.config/frame28/keys.json` y una búsqueda real; `clips batch` **con render** sobre
   `poc/clip-demo`; `reframe-map` con un `gestures.json` real.
10. **Deuda pequeña (0.5.0):** decidir sobre versionar `uv.lock`, OpenCV instalado por triplicado en el entorno,
    `onnxruntime-gpu` opcional.

## Qué quedó a medias o sin hacer

1. **GPU** — `transcribe` en GPU medido (4,2×) y NVENC opcional en `prep`/`reframe`/`cut apply` (`--gpu`,
   `env.encoder_args`), sin probar aún en un montaje entero con `--gpu`. Falta `onnxruntime-gpu` para `matte` y OCR: no es
   un `--with` más, porque sustituye al paquete `onnxruntime` del que dependen mediapipe y rapidocr; hay que probarlo en un
   entorno aparte antes de tocar el extra `gpu`.
2. **Caso `poc/clip-acrilico`** — montaje entero solo en `work/` y `out/` (ignorados): `work/storyboard.json`,
   `work/storyboard.{es,de}.json`, `work/strings.{es,de}.json`, `work/clips.sel.json`, `work/clips/s*/storyboard-hook*.json`,
   `work/brief.md`, `work/cta.json`, scripts `work/make_*.py`. Si se borra `work/`, se pierde. Pendiente la decisión (b).
3. **Despliegue de frame28.app** — todo construido; falta el token. `site/functions/api/contact.js:11` lleva el marcador
   `[[verificar en el despliegue]]` sobre la API del Email Service; el formulario solo tiene honeypot (Turnstile previsto).
4. **Condiciones** — 48 huecos `[[…]]` y revisión legal.
5. **Área de clientes** — artículos y guiones hechos; faltan los vídeos del curso y activar Access.
6. **Tarjeta de Frame28 en t28.io** — texto en `site/content/lanzamiento.md`; la web de Think28 no está en este repo.
7. **Sin probar en real** — `broll search/fetch` (sin claves), `clips batch` con render de verdad (hoy se usó con
   `--no-render` y los shorts se renderizaron uno a uno), `reframe-map` con gestos reales, `reframe --mode crop` con
   hablante en movimiento. `clips markers` sí se ejecutó sobre un vídeo real (`poc/clip-acrilico/work/markers.json`).
8. **Comparador de vídeo antes/después para la web** — research del usuario en `research/09-comparador-video.md` y POC en
   `poc/clip-javier/comparador-web/` (`index.html` versionado; el `comparativa_sbs.mp4` de 14 MB no). Pendiente: elegir el
   vídeo de demostración (sin Frame28 / con Frame28), producir el SBS y colocarlo en la landing.
9. **CI** — `.github/workflows/tests.yml` pasa la suite del CLI en cada push (verificada en verde el 2026-10-01; la primera ejecución falló porque el checkout de Actions vive en `/home/runner/work/` y el filtro de conftest excluía rutas con «work»).

## Bloqueos y dudas

| Bloqueo o duda | Dueño | Qué lo desbloquea |
|---|---|---|
| Token de API de Cloudflare: creado y en `CLOUDFLARE_API_TOKEN`, pero sin `Cloudflare Tunnel`, `Access: Organizations`, `Email Routing` ni `Cache Purge` (401/403 comprobados; la purga de `og.png` falló el 2026-10-02 y se resolvió con `?v=` en la URL de `og:image`) | Javier | Añadir esas tres filas al token (y `CLOUDFLARE_ACCOUNT_ID=237f15b5e4fa24ef5465ae87da6986de` al entorno), o hacer esos pasos en el panel |
| Suscripción `sub-frame28-prod` (la API de facturación de la cuenta MOSP no la deja crear) | Javier | Portal → Suscripciones → Agregar; después Claude mueve o vincula `rg-frame28-identity-prod` (ver `frame28-app/HANDOFF.md` punto 2) |
| Flujo de alta/entrada del tenant `frame28ciam` (Graph 400) | Claude / Javier | Reintentar `frame28-app/scripts/identidad/flow_devicecode.py` o crearlo en el centro de administración (dos minutos) |
| «Entrar con Google» en el tenant | Javier | Cliente OAuth en Google Cloud (Think28) con el redirect del tenant (ver `frame28-app/HANDOFF.md` punto 4) |
| Activación del Email Service (beta) y verificación del remitente `hola@frame28.app` | Javier al desplegar | Si la API no lo permite, un paso en el panel; el código solo toca `contact.js::sendMail` |
| Despliegue automático al hacer push | Javier | Conectar GitHub en el panel de Pages (OAuth) o crear un segundo token estrecho (`Cloudflare Pages → Edit`) para una GitHub Action |
| Decisión (b): versionar `clip-acrilico` anonimizado o dejarlo en `_private/` | Javier | Responderla al retomar (las muestras ya están copiadas en `_private/cliente-a/muestras/`) |
| Permiso del Cliente A para publicar el caso | Javier con el cliente | Hasta entonces, versión anónima (`case_public: False`) |
| Claves de Pexels y Pixabay | Javier | pexels.com/api y pixabay.com/api/docs → `~/.config/frame28/keys.json` |
| Commits antiguos cacheados en GitHub tras la reescritura | Javier | Pedir la purga a soporte de GitHub, si se quiere cerrar del todo |
| Términos de la suscripción de Claude para uso profesional | Javier | Revisar los vigentes o pasar la dirección a la API; la cláusula 7 de las condiciones lo asume |
| Decisiones de `research/06` §8 aún abiertas | Javier | Quién opera, umbrales para Cloud y qué sigue abierto |

## Cloudflare: token acordado (2026-10-01, noche)

Token de API personalizado (Mi perfil → Tokens de API → Crear token personalizado), **no** la Global API Key. Nombre
sugerido `frame28-claude-code`. Sin filtro de IP, sin caducidad (Javier lo quiere «para todo el producto, para siempre»; si
se filtra, se rota desde el panel). **Nunca va a un fichero del repo ni al chat**: variable de entorno de usuario
`CLOUDFLARE_API_TOKEN` (+ `CLOUDFLARE_ACCOUNT_ID`, el ID que aparece en la URL del panel) y copia en el gestor personal
(Think28 es personal: 1Password, no el Passwork corporativo).

**Cuenta (recurso: solo la cuenta T28), nivel Edit salvo que se indique:** Cloudflare Pages · Workers Scripts · Workers
Routes · Workers KV Storage · Workers R2 Storage · D1 · Queues · Workers AI · Vectorize · Stream · Cloudflare Images ·
Access: Apps and Policies · Access: Organizations, Identity Providers, and Groups · Access: Service Tokens · Access: Audit
Logs (Read) · Zero Trust · Email Routing Addresses (y «Email Service»/«Email Sending» si el constructor lo ofrece) ·
Turnstile · Account Rulesets · Account Filter Lists · Account Custom Pages · Logs · Account Analytics (Read) · Account
Settings (Read) · Billing (Read) · Notifications. Si aparecen: Workflows · Browser Rendering · Secrets Store.

**Zona (recurso: todas las zonas de la cuenta T28), nivel Edit salvo que se indique:** Zone · Zone Settings · DNS · SSL
and Certificates · Cache Purge (Purge) · Cache Rules · Config Rules · Transform Rules · Single Redirect · Origin Rules ·
Managed Headers · Page Rules · Firewall Services · Zone WAF · Workers Routes · Email Routing Rules · Health Checks ·
Custom Pages · Logs · Analytics (Read).

**Excluido a propósito:** `API Tokens → Edit` (un token que crea tokens es la cuenta entera), `Memberships`, permisos de
usuario (`User Details`), `Billing → Edit`.

Nombres contrastados con `developers.cloudflare.com/fundamentals/api/reference/permissions/` el 2026-10-01; Workflows,
Browser Rendering, Secrets Store y Email Sending no figuraban en esa página.

## Para retomar sin sorpresas

```bash
git fetch origin && git status -sb            # main...origin/main y árbol limpio; si hay `behind`, mirar qué subió otra sesión antes de tocar nada
ssh -T git@github-jl28                        # «Hi javierledesma28!»: el remoto es SSH; si falla, falta la clave id_ed25519_github_jl28 o GitHub la revocó
deploy/deploy.sh --check                      # «el servidor tiene exactamente el site/ de HEAD»; ssh -T t28server "docker ps --filter name=frame28" → web y tunnel Up
curl -sI https://frame28.app/ | head -1       # HTTP/1.1 200 OK (Server: cloudflare); /kb/ → 404 y /api/contact → 503 son a propósito
frame28 doctor                                # "Todo listo."; filas gpu (transcripción) ✓, gpu (onnxruntime) y claves de B-roll en aspa (opcionales)
claude plugin validate C:/Workspaces/personal/Skill-Director/plugin   # Validation passed (ruta absoluta: un `cd` previo en la sesión lo rompe)
(cd plugin/cli && uv run --group dev pytest)  # 116 passed en ~3 s
python scripts/release-check.py --notes       # con la 0.4.0 publicada: tag y release "ya existe" hasta subir __version__; confidencialidad "sin rastro"
uv run --with markdown python site/build.py   # 40 páginas · plazas Fundadores: 5 · caso público: False · huecos en condiciones: 48 (no ensucia el árbol)
cd poc/clip-javier && frame28 build storyboard-gsap.json -o work/f28-gsap && frame28 check work/f28-gsap && frame28 render work/f28-gsap -o out/test.mp4 --workers 10   # ~1 m 16 s de render
curl -sI https://frame28.t28.io/roadmap/ | head -1     # HTTP/2 200
```

Si ffmpeg o uv no están en el PATH de la shell, el CLI los encuentra solo; para la shell, la línea `export PATH` de las
Trampas de `CLAUDE.md`. Si `frame28 --version` no dice 0.4.0: `uv tool install --editable "./plugin/cli[gpu]" --python
3.12 --reinstall`. Si las skills `frame28:*` no aparecen en una sesión nueva: `claude plugin uninstall frame28@think28 &&
claude plugin install frame28@think28 --scope user`. Los `.frame28/log.jsonl` de `poc/*/` son la bitácora real de lo que
se ejecutó en cada caso: léelos antes de creer a este fichero. En la nube no hay HyperFrames ni red al CDN: sirve para
código, pruebas, sitio y docs; los renders y las muestras se hacen en el PC.
