# Traspaso — estado del proyecto a 2026-10-01 (PC, noche; cierre tras relevamiento)

Para retomar Frame28 desde otra cuenta de Claude Code **sin historial de conversación**, sobre este mismo
repositorio local (`C:\Workspaces\personal\Skill-Director`, Windows 11). Lee primero [CLAUDE.md](CLAUDE.md) (qué es,
estructura, cómo se ejecuta, convenciones, decisiones, trampas). Este fichero es el estado verificado, lo hecho por
sesiones, lo que quedó a medias, los bloqueos y lo que toca ahora. Lo que no esté aquí o en `CLAUDE.md` no existe para
la sesión siguiente.

**Cómo quedó git al cerrar:** rama `main`, **8 commits por delante de `origin/main`** (4 de la tarde + 4 de este cierre),
**sin push** (acción persistente: la convención del repo es proponerla antes; está lista en §Para retomar). Árbol limpio
tras el último commit. Tag `v0.4.0` en `4e7a6cb`, release publicada.

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

**Decisión del 2026-10-01 (noche):** el despliegue de frame28.app lo hará Claude Code con un **token de API de Cloudflare**
que Javier va a crear (permisos acordados en §Cloudflare). La zona DNS de `frame28.app` ya está activa en Cloudflare
(cuenta T28, plan Free, sin Pages ni Workers conectados).

## Estado: qué funciona hoy (verificado ejecutando, 2026-10-01 entre las 18:50 y las 19:40)

| Qué | Evidencia |
|---|---|
| Versión publicada | **v0.4.0** (release en GitHub, tag en `4e7a6cb`); 0.4.0 en `__init__.py`, `plugin.json`, `marketplace.json`, README |
| CLI | `frame28 --version` 0.4.0 (editable, con extra `gpu`); `frame28 doctor` «Todo listo», incluida la fila nueva **gpu (transcripción) ✓ 1 GPU CUDA con cuBLAS y cuDNN**; opcionales en aspa: gpu (onnxruntime) y claves de B-roll |
| Pruebas | **114 passed en ~3,7 s** (`cd plugin/cli && uv run --group dev pytest`) |
| Plugin | `claude plugin validate <ruta absoluta>/plugin` pasa; caché instalado 0.4.0 (18:31) **idéntico** a `plugin/skills/`; `claude plugin update frame28@think28` → «already at the latest version (0.4.0)» |
| Storyboards | 11 de 11 versionados válidos (`frame28 storyboard validate`) |
| Regresión | `poc/clip-javier/storyboard-gsap.json`: build sin avisos, check ✓, **render 1 m 16 s con `--workers 10`** (89–105 s con los trabajadores por defecto); hoja de contacto correcta |
| `release-check.py` | 4 bloqueos esperados (árbol, tag local, tag remoto, release «ya existe») hasta subir `__version__`; **confidencialidad: sin rastro** en ficheros, historia, tags y releases |
| Sitio del producto | `uv run --with markdown python site/build.py` → 40 páginas · plazas Fundadores 5 · caso público False · **48 huecos `[[…]]`** en condiciones; el build es determinista (no ensucia el árbol). **No desplegado** |
| Web del plugin | frame28.t28.io `/`, `/roadmap/`, `/instalar/`, `/install.ps1` → HTTP 200 |
| frame28.app | zona activa en Cloudflare; `curl` no obtiene respuesta (sin origen): esperado |
| Roadmap | `docs/roadmap/index.html`: 6 versiones, 56 ítems (**30 hechos, 4 a medias, 22 pendientes**); siguiente: «B-roll probado contra la API real» |
| Actualización de usuarios | **verificado en un entorno aislado**: `uv tool upgrade frame28` mueve una instalación desde git al último commit en 14 s aunque la versión no cambie; repetir el instalador (`--force`) también. `claude plugin update` solo actúa si cambia la versión del plugin |
| Dependencias | solo `av` 17.1 → 19 desactualizado (pin `<18` deliberado); HyperFrames 0.8.72 pineado (0.8.105 publicada); GSAP 3.14.2 (3.15.0 publicada) |
| Git | `main` 8 por delante de `origin/main`; `gh` con la cuenta personal `javierledesma28` activa (la correcta para push); rama `origin/main-ky21ae` obsoleta, borrable |
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
   transcripción real en GPU a las 18:42 (`poc/clip-acrilico/work/gpu/asr/`, ficheros completos) **sin medir el tiempo**.

### 2026-10-01 (PC, noche) — relevamiento completo y cierre
1. **Relevamiento** sin tocar código (estructura, git, 12 comprobaciones ejecutadas: tabla de §Estado). Hallazgos: el
   HANDOFF del mediodía decía «árbol limpio» con 4 commits sin subir y 8 ficheros sin commitear; 98→114 pruebas;
   roadmap 29→30 hechos; la segunda muestra hecha y sin anotar; `.frame28/log.jsonl` versionado por accidente;
   `input.source.json` del cliente protegido solo por una línea sin commitear; sin CI; `uv.lock` ignorado a propósito.
2. **README §Actualizar** (pedido expreso de Javier), `docs/instalar.md` §Para actualizar y una línea en el asistente web
   `docs/instalar/index.html`, con órdenes **verificadas** (ver §Estado). Fila de `doctor` «última release» pendiente.
3. **Permisos del token de Cloudflare** acordados (§Cloudflare); Javier los crea.
4. **Commits de cierre** (sin push): `.gitignore` + log fuera del índice; GPU en `transcribe`; docs de actualización;
   `CLAUDE.md` y este traspaso. Memoria de la cuenta de Claude actualizada (no viaja: todo lo duradero está aquí).

## Lo que toca ahora (en este orden)

1. **Push de los 8 commits.** `git fetch origin && git status -sb` (debe seguir `ahead 8`, sin `behind`),
   `gh auth status` (activa `javierledesma28`; si no, `gh auth switch --user javierledesma28`), `git push origin main`.
2. **Token de Cloudflare** (Javier lo crea con los permisos de §Cloudflare y lo deja en la variable de entorno de usuario
   `CLOUDFLARE_API_TOKEN`, más `CLOUDFLARE_ACCOUNT_ID`; hay que reiniciar la app de Claude para que la shell lo vea).
   Primero verificación de solo lectura: `curl -s -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN"
   https://api.cloudflare.com/client/v4/user/tokens/verify` y `npx wrangler whoami`.
3. **Desplegar frame28.app**, proponiendo cada paso antes: `npx wrangler pages project create frame28-app
   --production-branch main` → `npx wrangler pages deploy site/ --project-name frame28-app` → dominio personalizado
   `frame28.app` y `www` (DNS por API) → variables `MAIL_FROM`/`MAIL_TO` y binding `SEND_EMAIL` (si la activación del Email
   Service en beta es solo por panel, pedírselo a Javier) → **Turnstile** en el formulario (`site/functions/api/contact.js`
   y los fragmentos de contacto en `site/src/{es,en}/`) → organización de **Access** con PIN por email y aplicación sobre
   `/kb`, `/curso`, `/en/kb`, `/en/course` (pasos en `site/README.md`; sin Access el área de clientes es pública) → prueba
   real del formulario. Añadir el despliegue como fila/paso de `release-check` o un script `scripts/deploy-site.*`.
4. **Decisiones pendientes de Javier** (preguntadas el 2026-10-01, sin respuesta por falta de tokens):
   - (a) GPU: medir `frame28 transcribe poc/clip-acrilico/work/audio16k.wav -o <tmp> --lang en` en GPU frente a los
     179 s de CPU y dejar el dato en `CLAUDE.md`/`doctor`; o darlo por bueno sin medir.
   - (b) `poc/clip-acrilico`: versionar README + storyboard + `clips.json` anonimizados como los otros casos, o dejar
     todo en `_private/`. En cualquier caso: copiar `out/` (3 MP4, 6 shorts, 4 portadas, 3 SRT) a
     `_private/cliente-a/muestras/` y anotar `frame28 report note "director" --tokens <n>` en `poc/clip-acrilico/`.
5. **Capitalizar la actualización en el plugin:** fila opcional de `doctor` que lea
   `https://api.github.com/repos/javierledesma28/frame28/releases/latest`, compare con `__version__` y, si hay versión
   nueva, imprima `uv tool upgrade frame28` y `claude plugin marketplace update think28 && claude plugin update
   frame28@think28` (misma forma que la fila de red de GSAP en `plugin/cli/frame28/doctor.py`).
6. **Condiciones**: rellenar los 48 `[[…]]` de `site/content/condiciones.es.md` y `terms.en.md` (datos fiscales, fuero,
   buzón, IVA, idioma que prevalece, música, arrastre en Studio, medio de pago), pasarlas por el asesor y regenerar.
7. **Grabar la lección 1** del curso (`site/content/curso/es/01-que-es-frame28.md`), montarla con Frame28 y poner la URL
   en `video:`.
8. **Día 7**: lista previa de `_private/cliente-a/dia7-envio-final.md` y enviar; publicar `site/content/lanzamiento.md`
   el día que el sitio esté en vivo con Access.
9. Claves de Pexels y Pixabay en `~/.config/frame28/keys.json` y una búsqueda real; `clips batch` **con render** sobre
   `poc/clip-demo`; `reframe-map` con un `gestures.json` real.
10. **Deuda pequeña (0.5.0):** CI mínima (GitHub Actions con pytest), HyperFrames 0.8.72 → 0.8.105 pasando las dos
    regresiones, GSAP 3.15, quitar `poc/remotion/package-lock.json` y la rama `origin/main-ky21ae`, decidir sobre
    versionar `uv.lock`, OpenCV instalado por triplicado en el entorno, `onnxruntime-gpu` opcional.

## Qué quedó a medias o sin hacer

1. **GPU en `transcribe`** — código y prueba commiteados; **sin medir** la ganancia. Ficheros: `plugin/cli/frame28/env.py`
   (`cuda_dll_dirs`, `enable_cuda_dlls`, `cuda_ready`), `plugin/cli/frame28/transcribe.py` (`pick_device`, `_run_whisper`,
   caída a CPU), `plugin/cli/frame28/doctor.py` (fila «gpu (transcripción)»), `plugin/cli/pyproject.toml`
   (`[project.optional-dependencies] gpu`), `plugin/cli/tests/test_cli.py` (última prueba). Decisión consciente de
   commitear sin medir para no perder el trabajo al cerrar.
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
8. **Fila de `doctor` «última release»** — propuesta, no hecha (punto 5 de la lista anterior).
9. **Sin CI** — no hay `.github/workflows`; las pruebas solo corren en local y en `release-check`.

## Bloqueos y dudas

| Bloqueo o duda | Dueño | Qué lo desbloquea |
|---|---|---|
| Token de API de Cloudflare | Javier | Crearlo con §Cloudflare y dejarlo en `CLOUDFLARE_API_TOKEN` (variable de usuario de Windows); reiniciar la app |
| Activación del Email Service (beta) y verificación del remitente `hola@frame28.app` | Javier al desplegar | Si la API no lo permite, un paso en el panel; el código solo toca `contact.js::sendMail` |
| Despliegue automático al hacer push | Javier | Conectar GitHub en el panel de Pages (OAuth) o crear un segundo token estrecho (`Cloudflare Pages → Edit`) para una GitHub Action |
| Decisiones (a) GPU medir/no y (b) versionado de `clip-acrilico` | Javier | Responderlas al retomar |
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
git fetch origin && git status -sb            # main...origin/main [ahead 8] y árbol limpio; si hay `behind`, mirar qué subió la nube antes de tocar nada
git log --oneline origin/main..main           # los 8 commits de la tarde y el cierre del 2026-10-01
frame28 doctor                                # "Todo listo."; filas gpu (transcripción) ✓, gpu (onnxruntime) y claves de B-roll en aspa (opcionales)
claude plugin validate C:/Workspaces/personal/Skill-Director/plugin   # Validation passed (ruta absoluta: un `cd` previo en la sesión lo rompe)
(cd plugin/cli && uv run --group dev pytest)  # 114 passed en ~3 s
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
