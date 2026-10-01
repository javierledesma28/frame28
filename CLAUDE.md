# Frame28 · memoria del proyecto para Claude Code

Lee esto antes de tocar nada. Complementa a `HANDOFF.md` (estado, qué se hizo, qué toca ahora) y a
`docs/guia-plugin.md` (ciclo de vida del plugin). Responder siempre en español.

## Qué es

**Frame28** es un producto de **Think28** (marca personal de Javier Ledesma, `https://t28.io`; nada de branding
Fundanet/Semicrol aquí). Convierte un clip de una persona hablando a cámara, o un vídeo ya producido, en un vídeo
montado: rótulos, títulos cinéticos por palabra, texto detrás del hablante, callouts donde señala, pizarras,
gráficas, subtítulos, B-roll, gancho, pasos, antes/después, llamada a la acción y tarjeta de marca. Y a partir de
un vídeo largo: shorts verticales, portada y versión en otro idioma. Todo generado por código, en local, en CPU.

Dos piezas:
- **Plugin de Claude Code** (`plugin/`): ocho skills. `frame28-director` orquesta; `frame28-transcribe`,
  `frame28-cutout`, `frame28-storyboard`, `frame28-broll`, `frame28-shorts`, `frame28-i18n`, `frame28-compose`.
  Claude dirige el montaje (decide qué va en pantalla y escribe el storyboard).
- **CLI Python `frame28`** (`plugin/cli/frame28/`, click): los pasos deterministas. Las skills lo invocan por Bash.

El **contrato** entre ambos es el **storyboard JSON** (`plugin/cli/frame28/STORYBOARD.md` lo documenta;
`frame28 storyboard schema` lo imprime). El agente escribe el storyboard; `frame28 build` lo convierte en una
composición **HyperFrames** (HTML + GSAP) y `frame28 render` la renderiza a MP4. **Nunca se edita el HTML
generado**: se edita el storyboard y se regenera.

Repo público: `https://github.com/javierledesma28/frame28`. Web (GitHub Pages sobre `docs/`, dominio propio con
HTTPS forzado): `https://frame28.t28.io/` → guía `/presentacion/`, asistente de instalación `/instalar/`,
instaladores `/install.ps1` y `/install.sh`, instrucciones para que Claude instale `/instalar.md`, roadmap por
versiones `/roadmap/`.

**Desde el 2026-09-30 Frame28 es también un producto monetizable** del ecosistema Think28, con dominio
**frame28.app** (zona DNS activa en Cloudflare, cuenta T28, plan Free, confirmado el 2026-10-01; el sitio del producto
está **construido** en `site/` y **pendiente de desplegar** en Cloudflare Pages con un token de API que Javier va a
crear: permisos acordados en `HANDOFF.md` §Cloudflare). Se vende como servicio operado por Think28 (Launch, Studio), implantación en el cliente (Team) y,
solo con demanda demostrada, plataforma (Cloud). Primer cliente objetivo: **Cliente A** (nombre en clave: el cliente real no se escribe en ningún fichero del repo ni del sitio; ver HANDOFF §Confidencialidad). Definición, precios propuestos
y plan en `research/07-producto-frame28-app.md`; caminos evaluados en `research/06-monetizacion.md`. El plugin y el
CLI siguen MIT y públicos: son la demo viva y el canal de adopción.

**Regla de trabajo del usuario:** cada aprendizaje de un caso, un vídeo de ejemplo o un diagnóstico se capitaliza en
el plugin (código del CLI, `doctor`, validaciones, skills y referencias), no en docs ni en el HANDOFF. Ante cada
hallazgo: "¿qué parte del CLI o de qué skill cambia para que esto no vuelva a pasar?".

## Estructura

```
.claude-plugin/marketplace.json   este repo es su propio marketplace ("think28", source ./plugin)
plugin/                           EL PLUGIN (solo esto se instala; el resto del repo no se copia)
  .claude-plugin/plugin.json      manifiesto (name frame28; sin displayName: no está en el esquema; una sesión lo vio rechazado,
                                  con 2.1.126 valida, pero no aporta nada)
  skills/frame28-*/SKILL.md       ocho skills; frame28-storyboard/references/ = tecnicas.md, grabacion.md,
                                  ejemplo-storyboard.json, marca-y-promocional.md, ganchos.md
  cli/pyproject.toml              paquete Python (uv); deps: click, numpy, opencv-python-headless, onnxruntime,
                                  faster-whisper, av>=11,<18 (ver Trampas), mediapipe, rapidocr, segno
  cli/frame28/
    __init__.py                   __version__ (única fuente de la versión del CLI; pyproject la lee con hatch), HYPERFRAMES_VERSION, GSAP_VERSION
    env.py                        localiza ffmpeg/uv/npx (WinGet), caché ~/.cache/frame28, modelo RVM; `cuda_ready()` y
                                  `enable_cuda_dlls()` (librerías CUDA del extra `gpu`, para faster-whisper)
    media.py                      probe, prep (30 fps sin audio + voz limpia), sheet, frame_at, cut, fetch_url (yt-dlp vía uvx)
    transcribe.py                 faster-whisper (`--device auto`: GPU NVIDIA si cuBLAS/cuDNN están, si no CPU; si la GPU falla
                                  a mitad repite en CPU) → words.json, captions.json (por frase), words.srt (LF), transcript.json
    cut.py                        jump cuts: silencios (también dentro de palabras estiradas), muletillas, falsos arranques; apply remapea
    audio.py                      measure / clean (highpass, afftdn|rnnoise, loudnorm 2 pasadas) / compare
    matte.py                      RobustVideoMatting (alfa) y speaker_layout (bbox del hablante en el lienzo)
    pose.py                       MediaPipe Pose: track, gestos de señalar → pointers propuestos, face_box
    graphics.py                   RapidOCR: texto ya presente en el vídeo, marca de agua, tarjetas, zonas libres 3x3, colisiones
    reframe.py                    apaisado → 9:16/1:1: crop siguiendo la cara (zona muerta, suavizado) o blur; map_gestures/map_canvas_point
                                  (`reframe-map`: pointers y puntos del lienzo apaisado al vertical sin repetir la detección)
    captions.py                   default_canvas, paginado por palabras (pages/karaoke), cues SRT/VTT legibles, subtítulos por frase
                                  completa (`phrase_captions`, con `sent`) y exportación desde un storyboard (versiones traducidas)
    broll.py                      Pexels/Pixabay (claves en env o ~/.config/frame28/keys.json), sidecar de licencia, recorte
    clips.py                      fábrica de shorts: tramos por momentos, ganchos con la frase real (o la frase más fuerte del tramo),
                                  cut, scaffold, batch (variantes de gancho en lote: storyboard + build + check + render por gancho),
                                  markers (frases de resultado → before_after + draw check + kinetic; promesas → kinetic)
    log.py                        registro de tiempo por orden (.frame28/log.jsonl, FRAME28_LOG) y `frame28 report` (+ `report note`)
    cover.py                      portada/miniatura: composición estática + hyperframes snapshot
    i18n.py                       extract/apply de textos traducidos; retime_words sobre el ritmo original
    brandsite.py                  marca desde la web del cliente (colores CSS, fuente, logo con variantes)
    build.py                      generador storyboard → HyperFrames (overlays, CSS, timeline GSAP, validate, platform_warnings)
    render.py                     check (separa errores/contraste/falsos positivos) y render (+ hoja de contacto que cubre el vídeo entero)
    doctor.py, cli.py, STORYBOARD.md, brands/think28.json + brands/think28/*.svg
  cli/tests/                      pytest (grupo dev): conftest con fixtures de poc/ y datos sintéticos; test_captions, test_cut,
                                  test_clips, test_i18n, test_build, test_reframe, test_log, test_cli, test_release_check
docs/                             GitHub Pages: presentacion/ (deck + engine/), instalar/ (asistente web), instalar.md,
                                  install.ps1, install.sh, guion-demo.md, guia-plugin.md, brand/, CNAME, .nojekyll, index.html
  roadmap/index.html              roadmap por versiones (Think28): los datos viven en el array ROADMAP del propio fichero
                                  (estado hecho/medias/pendiente por ítem); marcadores artifact:head/body para publicarlo como artefacto
scripts/release-check.py          versiones en los cuatro sitios, árbol limpio, tag libre, cuenta gh, plugin validado, pytest en verde y
                                  confidencialidad (términos de `_private/confidencial.txt` en ficheros, historia, tags y releases);
                                  --notes: commits desde el último tag
research/                         01 análisis del vídeo de referencia (resumen), 02 repos, 03 PoC compositores,
                                  04 roadmap de features (18 ítems), 05 vídeo que vende productos DIY (Cliente A),
                                  06 monetización (tres caminos, recomendación), 07 producto Frame28.app (oferta, precios,
                                  Fundadores, KB y curso, sitio, plan de 7 días; la propuesta al cliente vive fuera del repo)
site/                             sitio del producto frame28.app, estático para Cloudflare Pages (root `site`, sin build en el despliegue).
                                  build.py (plantilla común + CONFIG: plazas, buzón, caso público) ensambla src/{es,en}/*.html y convierte
                                  content/condiciones.es.md + terms.en.md → index.html, en/, fundadores/, contacto/, condiciones/, en/founders/,
                                  en/contact/, en/terms/ (HTML commiteado). content/landing.{es,en}.md = referencia editorial.
                                  content/kb/{es,en}/ (8 artículos) y content/curso/{es,en}/ (6 lecciones con guion; `video:` vacío
                                  = pendiente de grabar) → /kb, /curso, /en/kb, /en/course con noindex, tras Cloudflare Access.
                                  functions/api/contact.js (formulario → email con binding send_email), _redirects, _headers, wrangler.toml,
                                  README.md (pasos de despliegue y de Access). Regenerar: `uv run --with markdown python site/build.py`
deploy/                           despliegue de frame28.app en t28server (/opt/frame28): docker-compose.yml (nginx:alpine + cloudflared, sin
                                  puertos), nginx.conf (traduce site/_headers y _redirects; cierra /kb y /curso hasta Access; 503 en /api/contact
                                  hasta el Worker), remote-up.sh (nginx -t antes de recrear), deploy.sh (sube HEAD, backup, hash, comprueba URLs),
                                  .env.example (el token del túnel solo vive en el .env del servidor)
poc/                              casos reales, cada uno con README, storyboard(s) y cuts.json versionados; work/ y out/ NO:
                                  clip-javier (10 s, referencia de regresión), clip-auriculares (anuncio 58 s),
                                  clip-whatsapp (vertical de móvil, inglés), clip-demo (guion de demo 83 s, + vertical),
                                  clip-grabado (tutorial de YouTube de una marca: brief, storyboard, shorts, i18n),
                                  clip-acrilico (segundo tutorial de la misma marca, montado el 2026-10-01 en EN/ES/DE con 6 shorts
                                  y 4 portadas: TODO en carpetas ignoradas, nada versionado todavía; ver HANDOFF §A medias)
_private/                         NO versionado: caras, fotogramas y transcripción del vídeo de referencia; `confidencial.txt` (términos
                                  que `release-check` busca); `cliente-a/` (propuesta, brief, guion y envío que nombran al cliente)
```

## Cómo se ejecuta

Instalación de desarrollo (hecha en esta máquina, Windows 11, sin CUDA):
```bash
uv tool install --editable ./plugin/cli --python 3.12     # CLI editable → ~/.local/bin/frame28
uv tool install --editable "./plugin/cli[gpu]" --python 3.12 --reinstall   # opcional: librerías CUDA (>1 GB) para transcribir en
                                                           # GPU NVIDIA; es lo que hay instalado en esta máquina (2,5 GB en %APPDATA%/uv/tools/frame28)
claude plugin marketplace add C:/Workspaces/personal/Skill-Director   # marketplace local "think28"
claude plugin install frame28@think28 --scope user
claude plugin validate ./plugin                             # SIEMPRE antes de commitear skills
```
Tras editar skills: `claude plugin uninstall frame28@think28 && claude plugin install frame28@think28 --scope user`
(con la misma versión, `update` no refresca el caché). Tras añadir una dependencia al pyproject o cambiar `__version__`:
`uv tool install --editable ./plugin/cli --python 3.12 --reinstall`.

Pipeline manual (lo que hace la skill directora):
```bash
frame28 fetch <url> -o input.mp4           # opcional: YouTube/Vimeo con yt-dlp (uvx, sin instalar)
frame28 prep input.mp4 -o work [--gpu]     # clip 30 fps sin audio, voz limpia a -14 LUFS (+voice_raw.wav), audio16k.wav; --gpu = NVENC
frame28 transcribe work/audio16k.wav -o work --lang es   # --device auto (GPU si `doctor` la da por lista, si no CPU); --script nombres.txt sesga nombres propios
frame28 cut plan work/words.json --audio work/voice.wav -o work/cuts.json && frame28 cut apply work/clip.mp4 work/cuts.json --audio work/voice.wav --words work/words.json --captions work/captions.json -o work/cut
frame28 reframe work/cut/clip.mp4 -o work/cut/vertical.mp4 --path work/cut/reframe.json [--mode blur]   # solo si el destino es vertical
frame28 reframe-map work/cut/reframe.json --gestures work/cut/gestures.json -o work/cut/gestures-vertical.json   # pointers del apaisado al vertical
frame28 speaker work/cut/clip.mp4 ; frame28 gestures work/cut/clip.mp4 --words work/cut/words.json -o work/cut/gestures.json --annotate work/cut/gestos.png
frame28 graphics work/clip.mp4 -o work/graphics.json --annotate work/graphics.png   # vídeos ya producidos
frame28 matte work/cut/clip.mp4 --start 4.3 --end 6.8 -o work/cut/alpha.webm       # solo el tramo con `behind`
frame28 build work/cut/storyboard.json -o work/cut/project [--graphics work/graphics.json] && frame28 check work/cut/project && frame28 render work/cut/project -o out/x.mp4
frame28 cover out/x.mp4 --at 12.0 -o out/cover.png --title "Línea 1|Línea 2" --brand think28
frame28 clips markers work/cut/captions.json --lang es --words work/cut/words.json --side right -o work/cut/markers.json   # overlays propuestos en frases de resultado y promesa
frame28 clips plan work/captions.json --lang es -o work/clips.json   # shorts: cut, reframe, scaffold, build, render
frame28 clips batch work/clips.json s4 --brand think28 --video vertical.mp4 -o out/shorts   # todas las variantes de gancho de una vez
frame28 clips batch work/clips.json s4 --brand think28 --video vertical.mp4 -o out/shorts --keep   # renderiza los storyboard-hook<N>.json ya afinados, sin regenerarlos
frame28 i18n extract work/storyboard.json ; frame28 i18n apply work/storyboard.json strings.en.json --lang en
frame28 captions export work/storyboard.en.json -o out/x-en.srt   # SRT de una versión traducida (subtítulos por frase del storyboard)
frame28 report --rate 60 ; frame28 report note "director" --tokens 12000 --minutes 20   # tiempo por orden y coste del vídeo
```
Pruebas automatizadas: `cd plugin/cli && uv run --group dev pytest` (114 pruebas, ~3 s; módulos puros sin ffmpeg ni
modelos: captions, cut, clips (incluidos `batch --no-render` y `markers`), i18n, build.validate/platform_warnings/build_project,
reframe.map_*, log/report, smoke del CLI con `CliRunner`, fila de confidencialidad de `release-check`; fixtures = `poc/clip-javier/words.json`, los storyboards versionados y `poc/clip-grabado/*.json`).
`scripts/release-check.py` la ejecuta. Cada bug que se arregle lleva su prueba de regresión en `plugin/cli/tests/`.
Lo que no cubre (render, matte, gestos, OCR) se prueba con `frame28 check` + render + mirar la hoja de contacto (`*_sheet.png`).
Regresión rápida: `poc/clip-javier/storyboard-gsap.json` (10 s). Storyboards reales completos: `poc/clip-demo/`
(16 overlays, cortes, vertical), `poc/clip-grabado/` (vídeo producido, marca de cliente, shorts, i18n).

Deck de la guía: editar `docs/presentacion/deck.html`, luego `node engine/build.mjs deck.html --out index.html`
desde `docs/presentacion/` y comprobar en el navegador `FundanetDeck.check()` → `[]`. El build puede dejar CRLF
en `index.html`: normalizar a LF antes de commitear (git lo hace solo, pero deja aviso).

Roadmap: editar el array `ROADMAP` de `docs/roadmap/index.html` (estado `s` de cada ítem: hecho | medias |
pendiente; `next: true` marca el siguiente). Comprobar con `node --check` el script extraído y republicar el
artefacto de claude.ai (URL en HANDOFF) con la variante sin doctype (contenido entre los marcadores
`artifact:head` y `artifact:body`).

Release: `python scripts/release-check.py --notes` (versiones, árbol, rama, tags, cuenta gh, release, CLI, plugin,
pruebas, confidencialidad; `--notes` lista los commits desde el último tag). Notas con el formato de `gh release view v0.4.0`.

## Convenciones

- Idioma: español en docs, skills, mensajes del CLI y commits. Tono Think28: directo, técnico, humano; sin
  "innovador/disruptivo/robusto/holístico".
- Commits: mensaje descriptivo en español + línea `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`.
- Versión y release: `__version__` en `plugin/cli/frame28/__init__.py` (pyproject la lee), `plugin/.claude-plugin/plugin.json`,
  `.claude-plugin/marketplace.json` y el README. `python scripts/release-check.py` antes de etiquetar; `--notes` da el
  punto de partida de las notas. Luego `git tag -a vX.Y.Z`, push del tag y `gh release create` con la cuenta personal.
- Cómo actualizan los usuarios (README §Actualizar y `docs/instalar.md`): `uv tool upgrade frame28` (verificado el
  2026-10-01: reinstala desde el último commit de GitHub en ~15 s aunque la versión no cambie) y `claude plugin marketplace
  update think28 && claude plugin update frame28@think28` (solo actúa si cambió la versión del plugin: por eso cada release
  sube los cuatro sitios). Pendiente: fila de `doctor` que compare con la última release de GitHub y diga esas dos órdenes.
- **Git lo gestiona Claude de principio a fin** (commits, ramas, push, PRs, tags y releases), como en el resto de repos de
  Think28 (Synapse28, TheValley28): Javier no pega comandos. El remoto es **SSH con el alias `github-jl28`**
  (`git@github-jl28:javierledesma28/frame28.git`; clave dedicada sin passphrase de `~/.ssh/config`, creada para que Claude
  Code pueda pushear): `ssh -T git@github-jl28` debe decir «Hi javierledesma28!». `gh` solo hace falta para `gh release` y
  `gh api`: tiene dos cuentas y la activa suele ser la corporativa; `gh auth switch --user javierledesma28` antes y volver
  a dejarla después. Validado el 2026-10-01 tras un 403 por HTTPS (ver Trampas).
- Finales de línea LF (`.gitattributes`); el `words.srt` que importa HyperFrames **solo funciona con LF**.
- `docs/install.ps1` **solo ASCII**: Windows PowerShell 5.1 lee la web en Latin-1.
- Descripciones YAML de las skills entre comillas simples (los `:` rompen el frontmatter y la skill no se dispara).
- Cada overlay del storyboard tiene `id` único; todo `<video>/<audio>` generado lleva `id` (si no, HyperFrames lo
  congela). Capas con z-index explícito: 1 fondo, 2 texto behind, 3 alfa del hablante, 4 overlays, 5 pizarras,
  6 venta (hook/cta/steps), 9 subtítulos.
- Lienzo: `canvas` del storyboard (1920×1080, 1080×1920 o 1080×1080). `speaker`/`gestures` devuelven coordenadas en el
  lienzo que corresponde al formato del clip (`captions.default_canvas`); las claves `*_1080p` son alias antiguos. Con
  ancho < 1400 el generador añade la clase `narrow` (gráficas, contadores y tarjetas compactos). `platform`
  (tiktok/reels/shorts) activa avisos de zonas seguras.
- Salidas, medios (`*.mp4 *.wav *.webm`), `work*/`, `node_modules/`, modelos y `_private/` van en `.gitignore`.
  Caras, logos y material de terceros **nunca** entran en el repo (el historial ya se limpió una vez por esto); la
  marca `cliente-a` vive en `poc/clip-grabado/work/brands/` (no versionada) y se regenera con `frame28 brand from-site`.
- Lo que sí se confirma antes: lo destructivo o irreversible (reescribir historia o `push --force`, borrar ramas o tags ya
  publicados, cambios en el DNS o en el sitio en vivo que afecten a clientes, gastar dinero, instalar software en la
  máquina de Javier). Lo demás se hace, y se explica en pocas frases qué se hizo y cómo se comprueba: Javier quiere
  entender cada etapa, no ejecutarla él.
- Los análisis de negocio (`research/06`, `07`) se versionan en este repo público por decisión del usuario; los
  **precios** de `research/07` §2 están validados por él (2026-10-01). Un cambio de precios se hace ahí primero y
  después en la landing; no se inventan ni redondean cifras en ningún otro sitio.
- Precios y oferta se expresan en USD (el primer cliente es estadounidense); la landing es la fuente pública de
  precios cuando exista; `research/07` es la propuesta.
- Parches al CLI: escribir el parche a un `.py` en el scratchpad y ejecutarlo (ver Trampas), luego `ast.parse`.

## Decisiones técnicas

- **HyperFrames 0.8.72** (Apache-2.0) como compositor, pineado (0.8.105 publicada el 2026-10-01; subir exige pasar las
  regresiones de `poc/clip-javier` y `poc/clip-grabado`); Remotion descartado (licencia de empresa >3 personas).
  PoC comparativa en `research/03-poc-compositores.md`.
- **faster-whisper** (CPU, medium int8) para tiempos por palabra; WhisperX/stable-ts con guion son mejora pendiente.
- **RobustVideoMatting ONNX** (GPL-3, ejecutado como proceso, modelo descargado a `~/.cache/frame28/`) para el
  alfa del hablante; **MediaPipe Pose** (lite, misma caché) para gestos y reencuadre; **RapidOCR** (PaddleOCR en ONNX,
  Apache-2.0, modelos dentro del wheel) para el texto ya presente en vídeos producidos; **segno** (BSD) para QR.
- **GPU opcional, nunca obligatoria**: el extra `frame28[gpu]` (`nvidia-cublas-cu12`, `nvidia-cudnn-cu12`) da a faster-whisper
  las librerías CUDA; `transcribe --device auto` usa la GPU si `env.cuda_ready()` lo confirma (float16) y cae a CPU (int8) si
  falla a mitad. onnxruntime sigue en CPU (matte, OCR). El render se acelera con `--workers`, no con la GPU (`--gpu` solo codifica).
- **GSAP 3.13+** es gratis con plugins: `build.py` carga SplitText/DrawSVG solo cuando el storyboard los usa.
- Limpieza de audio: `highpass 80` + `afftdn` (o `rnnoise` con modelo BSD en caché) + `loudnorm` en dos pasadas.
- Marca por nombre (`"brand": "think28"`) o por ruta (`.json`, también relativa al storyboard); búsqueda `./brands/`
  → `~/.config/frame28/brands/` → incluidas. `frame28 brand from-site <url>` la propone desde la web del cliente.
- La traducción a otro idioma la hace el agente (sin API ni modelo local); el CLI solo extrae, aplica y retiming.
- B-roll solo de Pexels/Pixabay (licencia comercial sin atribución) o material del usuario; licencia en sidecar.
- Instalación para no técnicos: `irm https://frame28.t28.io/install.ps1 | iex` / `curl -fsSL .../install.sh | bash`,
  o "Instala Frame28 siguiendo https://frame28.t28.io/instalar.md" pegado en Claude Code.
- Sitio del producto: frame28.app se sirve desde el **VPS t28server** (Hetzner, Ubuntu 24.04) con el patrón de todos los
  sitios de Think28: `nginx:alpine` + túnel `cloudflared` en `/opt/frame28`, cero puertos abiertos, HTTPS de Cloudflare;
  CNAME apex y `www` → `<id-túnel>.cfargotunnel.com` (proxied). Publicar = commitear y `deploy/deploy.sh` (decidido el
  2026-10-01 por Javier, en lugar de Cloudflare Pages; `site/functions`, `_headers`, `_redirects` y `wrangler.toml` se
  conservan por si algún día se usa Pages). Pendientes sobre esa base: Worker en la ruta `frame28.app/api/contact*` con
  el envío de email (el formulario ya hace `fetch` JSON a `/api/contact`), **Cloudflare Access** con PIN por email sobre
  `/kb`, `/curso`, `/en/kb`, `/en/course` (hasta entonces nginx devuelve 404 ahí) y Turnstile. frame28.t28.io sigue en
  GitHub Pages para el plugin.
- El roadmap público vive en `docs/roadmap/index.html` con sus datos inline; no hay otra copia de los estados.

## Trampas ya sufridas (no repetir)

- **ffmpeg y uv no siempre están en el PATH de la sesión Bash** (y WinGet cambia la carpeta de ffmpeg en cada actualización:
  8.1.1 pasó a 9.0.2): `export PATH="$(ls -d /c/Users/ledes/AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg_*/ffmpeg-*/bin | tail -1):/c/Users/ledes/AppData/Local/Microsoft/WinGet/Packages/astral-sh.uv_Microsoft.Winget.Source_8wekyb3d8bbwe:$HOME/.local/bin:$PATH"`
  (el CLI los localiza solo; la shell no).
- **PyAV**: uv resolvía `av` 19, que rompe faster-whisper (`metadata_errors`); `av` 14 no tiene wheel Windows → pin `<18`.
- **La GPU (RTX 4060 Laptop, 8 GB) ya transcribe**: las librerías CUDA van en el extra `gpu` y `doctor` lo confirma
  («gpu (transcripción) ✓ 1 GPU CUDA con cuBLAS y cuDNN»). **Medido el 2026-10-01**: el mismo audio de 160 s, 42,4 s en
  GPU (float16) frente a 178,7 s en CPU (int8), 4,2× más rápido con un render ocupando la máquina. onnxruntime sigue siendo
  la compilación de CPU (matte y OCR). NVENC en ffmpeg funciona sin instalar nada: `render --gpu` codifica el final, y
  `prep`, `reframe` y `cut apply --gpu` (o `FRAME28_ENCODER=nvenc`) los intermedios (`env.encoder_args`; 5× medido, fichero
  mayor). Nunca por defecto: en la máquina de un usuario todo tiene que ir también por CPU.
- **Consola Windows en cp1252**: el CLI fuerza UTF-8 en stdout; en scripts sueltos evitar `→ ✓` en `print`.
- **Parches por `python - <<'EOF'` (stdin) fallan con no-ASCII y con `\\n`**: Python decodifica stdin en cp1252 y los
  escapes se comen; también los heredoc bash con comillas. Escribir el parche a un `.py` (Write) y ejecutarlo.
- **HyperFrames rechaza tweens de `left/top/width`** (`gsap_non_transform_motion`): animar siempre `x/y/scale/opacity`
  o `clipPath`. El `check` marca `text_occluded` en todo `behind` (falso positivo, `frame28 check` lo separa);
  la previsualización del Studio no respeta el rango de la capa alfa (el render sí); `hyperframes transcribe`
  exige whisper-cpp compilado (no usar; importar `words.srt` con `--preserve-cues` si hace falta).
- **HyperFrames no admite un `<video data-start>` dentro de otro elemento temporizado** (`video_nested_in_timed_element`):
  el contenedor del `broll` no lleva `data-start`; su visibilidad va por opacidad.
- **`.clip` aplica `inset: 0`**: un overlay con alto propio (cta, hook) necesita `inset:auto; height:max-content` o se
  estira hasta el borde del lienzo.
- **Un SVG inline grande (QR) triplica el tiempo de captura**: el QR va como PNG en data URI.
- **`hyperframes snapshot` resuelve el DIR relativo a su propio cwd**: pasar rutas absolutas.
- **No estimar anchos de texto en Python**: el rótulo recortaba títulos según la fuente que cargara el navegador.
  La caja se dimensiona sola (`width: max-content`) y el tecleo es un `clip-path` tweeneado.
- **Cajas de resaltado por línea (hook, portada)**: la caja de la línea siguiente tapaba los descendentes (g, y, p)
  de la anterior. Cada línea lleva `position:relative; z-index` decreciente y algo más de padding inferior.
  Lo contrario también pasa: la caja de arriba tapa la tilde o la diéresis de una **mayúscula** de la línea siguiente
  ("ACRÍLICO" salía "ACRILICO"); `build.highlight_line_height` abre el interlineado cuando hace falta. En portadas,
  parte el título con `|`: una línea que se parte sola no recibe ese tratamiento y pierde los descendentes.
- **Fondos claros**: cinéticos blancos o en acento no se leen (tutoriales cenitales, mesas, telas). `kinetic` tiene
  `color`; usar la tinta de la marca. Acento sobre acento nunca (texto ámbar sobre tarjeta ámbar).
- **Plugin**: el caché copia todo el directorio del plugin → por eso vive en `plugin/`; con la misma versión,
  `claude plugin update` no refresca: desinstalar e instalar.
- **Añadir una dependencia a `pyproject.toml` no la instala**: la instalación editable no relee dependencias.
  `uv tool install --editable ./plugin/cli --python 3.12 --reinstall` (el Python de la herramienta está en
  `%APPDATA%/uv/tools/frame28/Scripts/python.exe`, no en `~/.local/share`).
- **No editar el CLI mientras un render corre en segundo plano**: cada `frame28 …` importa `cli.py` al arrancar y un
  fichero a medias lo tumba. Tampoco lanzar dos cadenas en segundo plano que escriban los mismos ficheros temporales.
- **GitHub Pages con dominio propio**: registrar el CNAME en Pages **después** de crear el DNS (si no, el
  certificado no se emite; se arregla quitando y volviendo a poner el cname por API). `docs/.nojekyll` evita
  fallos de build. Al re-registrar el dominio, GitHub crea commits ("Create CNAME") en `main`: hacer `git pull --rebase`.
- El `.ps1` se sirve como `application/octet-stream` pero `irm` lo devuelve como String en PS 5.1 y 7 (probado).
- El detector de falsos arranques no debe cortar estructuras paralelas ("por aquí hay X, por aquí hay Y"): solo
  repetición inmediata o tras pausa. Whisper no transcribe "eh" y estira la palabra anterior a una pausa: `cut plan`
  busca silencio de audio dentro de palabras de > 0,9 s. Las muletillas ambiguas ("bueno", "pues") solo se cortan
  seguidas de pausa; "este" y "nada" nunca ("este muñeco", "de este a oeste" se cortaban mal).
- **El OCR no distingue un rótulo del editor del texto impreso en un objeto quieto** (`graphics`): para colocar
  overlays da igual (no tapar texto); la clase es orientativa.
- **Un short recortado con `pad` arrastra un residuo de la frase anterior** (0,05–0,15 s): `i18n extract` lo marca
  con `note`/`visible`; traducir solo lo que se oye.
- **`frame28 clips scaffold` con marca por ruta**: se guarda relativa al storyboard del short; construir desde
  cualquier carpeta funciona.
- **La versión vive en cuatro sitios** y el bump a 0.3.0 se olvidó de `__init__.py`: `frame28 --version` siguió diciendo
  0.2.0. Ahora pyproject la lee de `__init__.py` (hatch) y `scripts/release-check.py` comprueba los cuatro; `frame28 doctor`
  avisa si el código y la instalación no coinciden (la instalación editable no relee `__version__`: `--reinstall`).
- **`words.json` y `captions.json` se leen solo con `captions.load_words` / `load_captions`**: aceptan `text` o `word`,
  `start`/`end` en segundos o `startMs`/`endMs` en milisegundos (HyperFrames) y dict con `words` o `segments`, y dan un
  error corto (`TranscriptFormatError`) si faltan tiempos. Leerlos con `json.loads` a pelo es lo que hizo reventar
  `cut plan` con el fixture de clip-javier en milisegundos.
- **El render necesita red**: GSAP y sus plugins se cargan desde jsdelivr (`GSAP_VERSION`, en `__init__.py`); `doctor` lo
  comprueba como fila opcional. "Tu vídeo no sale de tu máquina" sigue siendo cierto: solo se descargan los scripts.
- **Push por HTTPS → 403 «denied to javierledesmasmc»** (2026-10-01): git no se autentica con `gh` sino con Git Credential
  Manager (`credential.helper = manager`), que guarda **una** credencial por host y la última en entrar fue la corporativa;
  `gh auth switch` no cambia eso. Solución aplicada y validada: remoto por SSH `git@github-jl28:…` (como Synapse28). `gh`
  con la corporativa activa sigue dando 403 en `gh release create` y `gh api`: `gh auth switch --user javierledesma28`
  antes (`release-check` lo avisa) y volver a dejarla después.
- **El nombre del cliente se cuela por donde el árbol no mira**: tras anonimizar el árbol y reescribir el historial seguía
  en las notas de la release v0.3.0, en los tags viejos y en una carpeta bajada de la nube sin ignorar dentro del repo (a
  un `git add -A` de publicarse). La fila `confidencialidad` de `release-check` cubre los cuatro sitios; necesita
  `_private/confidencial.txt`. Lo que se baje y nombre al cliente va a `_private/`.
- **Guiones bajos seguidos en el Markdown del sitio** (líneas de firma): Python-Markdown los toma por énfasis y el HTML
  cambia según la versión de la librería, así que el build ensucia el árbol en otra máquina. Escaparlos (`\_`).
- **Lo "entregado fuera del repo" por una sesión en la nube puede no llegar al PC** (pasó con el script de tags, el
  bundle y las notas): lo que el siguiente paso necesite tiene que poder reconstruirse desde el repo.
- **Los segmentos de Whisper no son frases**: cortan cada ~4,5 s y, si la transcripción trae pocas comas, a mitad de
  frase. Con eso los subtítulos se parten mal, los tramos de `clips plan` empiezan a medias y la traducción trabaja
  sobre fragmentos. `transcribe` escribe ahora `captions.json` por frase completa (`captions.phrase_captions`, con
  `sent`); `clips plan --words` hace lo mismo con una transcripción antigua. En `clips markers`, `--words` solo afina
  tiempos (puede ser parcial): no sirve como fuente de frases.
- **La hoja de contacto del render enseñaba solo los primeros 20 s** (un fotograma por segundo, 4×5): en un vídeo de
  160 s la revisión quedaba ciega. `media.sheet_plan` reparte hasta 48 fotogramas por toda la duración.
- **`clips batch` reescribe los storyboards**: tras afinarlos a mano hay que usar `--keep` (o renderizar cada
  `project-hook<N>` a mano); sin él se pierde el afinado.
- **CTA sobre el vídeo en un vertical con blur**: la posición por defecto ("encima de los subtítulos") cae sobre la
  mitad inferior del vídeo y tapa el resultado. `scaffold` lo manda a la franja libre de arriba si hay `reframe.json`.
- **Marca por nombre desde la carpeta de un short**: solo se buscaba junto al proyecto y en su carpeta madre;
  `resolve_brand` sube ahora hasta seis niveles (encuentra `work/brands/` desde `work/clips/<id>/project-hook0/`).
- **Una traducción es más larga y la frase dura lo mismo**: `i18n apply` avisa de los subtítulos por encima de 21
  caracteres por segundo. Se condensa hasta no superar la densidad del original (`captions export <storyboard>` da
  `mean_cps`); el SRT de un idioma traducido sale del storyboard, no de un `words.<lang>.json` que no existe.
- **El sidecar de `frame28 fetch`** (`input.source.json`: título, canal, URL) nombra al dueño del vídeo y no estaba
  ignorado: `*.source.json` en `.gitignore`.
- **Patrones de resultado**: "when you're done" (promesa en futuro) y "perfect for this" (idoneidad) no son el
  momento del resultado; el encendido o el montaje final suelen decirse sin palabra clave ("lights up"): los
  marcadores automáticos son una propuesta y el `before_t` se elige mirando fotogramas del mismo encuadre.
- **Parches con heredoc de bash y comillas simples triples** siguen rompiéndose: escribir el `.py` con Write.
- **El render no se acelera con la GPU, sino con trabajadores**: el tiempo se va en capturar cada fotograma con
  Chrome (~0,4 s por fotograma), que ya usa la GPU del navegador. La captura rápida de HyperFrames no se activa
  porque los overlays animan `clip-path` y máscaras. Medido con el clip de 10 s (16 núcleos, 32 GB): 6 trabajadores
  (por defecto) 81 s; `--workers 10` 68 s; 14, 76 s (se pisan); `--gpu` (NVENC) 73 s; `--workers 10 --gpu` 57 s con
  un fichero un 47 % mayor. Con más de 5 trabajadores hay que subir el heap de Node (`render` lo hace).
- **`check` tarda ~49 s y no hace falta repetirlo** cuando solo cambian textos o posiciones de un storyboard ya
  comprobado (versiones traducidas, re-renders tras revisar): en un vídeo real se pasó 11 veces, el 16 % del tiempo.
- **Trabajar en el CLI mientras hay renders en marcha**: en un worktree de git (`git worktree add <ruta> -b <rama>`);
  los renders siguen importando el código intacto y las pruebas se pasan en la copia. `uv run --project
  <worktree>/plugin/cli frame28 …` ejecuta esa versión desde cualquier carpeta.
- **Cada `frame28 …` escribe `.frame28/log.jsonl` en el directorio actual**: lanzado desde la raíz del repo, el log aparece
  ahí (ignorado). Llegó a estar versionado (lo añadió una sesión en la nube antes de la regla del `.gitignore`) y se quitó
  del índice el 2026-10-01: si reaparece como modificado, es que alguien corrió el CLI desde la raíz, no un cambio real.
- **Un `cd` dentro de un comando Bash cambia el directorio de las órdenes siguientes de la sesión**: `claude plugin validate
  ./plugin` falló buscando `plugin/cli/plugin` tras un `cd plugin/cli` anterior. Rutas absolutas, o el `cd` en el mismo comando.
- **`poc/clip-acrilico/input.source.json` nombra el canal del cliente** y lo único que lo mantiene fuera de `git add -A` es la
  línea `*.source.json` del `.gitignore` (commiteada el 2026-10-01). Las sesiones que descarguen vídeos de clientes deben
  comprobar `git status` antes de añadir nada.
- **El token de API de Cloudflare no ve los túneles** (401/403 en `cfd_tunnel`, también 403 en Pages, Access Organizations
  y Email Routing): el túnel `frame28` y sus *Public Hostnames* se hacen en el panel (Zero Trust → Networks → Tunnels) o se
  añade al token `Cloudflare Tunnel → Edit`. DNS, Access apps, Workers y Turnstile sí van por API. El token del túnel (el del
  `cloudflared … run --token`) se decodifica en base64 y trae el id del túnel; va solo al `.env` del servidor.
- **`sha256sum` en Git Bash escribe `hash *ruta`** (modo binario) y en Linux `hash  ruta`: comparar manifiestos entre PC y
  servidor exige normalizar (`deploy.sh::norm`). Y el alias `t28server` lleva `RequestTTY yes`: sin terminal, cada `ssh`
  avisa de la pseudo-terminal salvo con `-T`.
- **La herramienta de escritura de Claude deja CRLF en Windows**: git los normaliza a LF al commitear (`.gitattributes`), pero
  un script que se ejecute desde el working tree antes de commitear puede fallar; comprobar con `git ls-files --eol`.
- **El HANDOFF puede quedarse atrás en un mismo día**: el del 2026-10-01 (mediodía) decía «árbol limpio» mientras la tarde
  dejó 4 commits sin subir, 8 ficheros sin commitear y una muestra entera renderizada sin anotar. Antes de fiarse, `git status
  -sb`, `git log origin/main..main` y mirar los `.frame28/log.jsonl` de `poc/*/` (son la bitácora real de lo que se ejecutó).
