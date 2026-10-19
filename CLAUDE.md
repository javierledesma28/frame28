# Frame28 · motor y plugin (memoria del repo para Claude Code)

**Normas comunes del equipo de agentes** (mandan sobre este fichero en lo que se solapen: autoridad, fuentes de verdad,
backlog, git y worktrees, despliegue, idioma y tono, coautoría, secretos, Cliente A, qué se confirma antes):
@C:/Workspaces/personal/frame28-backlog/NORMAS.md

Aquí solo va lo propio del motor y del plugin: qué hay, cómo se ejecuta, cómo se publica una release, las decisiones
técnicas y las trampas ya sufridas. El estado del momento está en `HANDOFF.md` y en el backlog (F28-N); el ciclo de vida
del plugin, en `docs/guia-plugin.md`; el plan por versiones, en el roadmap (`docs/roadmap/index.html`).

## Qué es

**Frame28** es un producto de **Think28** (`https://t28.io`; aquí solo va la marca Think28). Convierte un clip de una
persona hablando a cámara, o un vídeo ya producido, en un vídeo montado: rótulos, títulos cinéticos por palabra, texto
detrás del hablante, callouts donde señala, pizarras, gráficas, subtítulos, B-roll, gancho, pasos, antes/después, llamada
a la acción y tarjeta de marca. Y a partir de un vídeo largo: shorts verticales, portada y versión en otro idioma. Todo
generado por código y en local; la GPU NVIDIA acelera lo que puede y sin ella todo va por CPU.

Este repo es público y MIT (`https://github.com/javierledesma28/frame28`) y tiene dos piezas:
- **Plugin de Claude Code** (`plugin/`): diez skills. `frame28` es la entrada cuando el usuario nombra Frame28;
  `frame28-memoria` crea o corrige la Memoria de marca y consulta las campañas; `frame28-director` orquesta el montaje;
  `frame28-transcribe`, `frame28-cutout`, `frame28-storyboard`, `frame28-broll`, `frame28-shorts`, `frame28-i18n`,
  `frame28-compose`. Claude dirige el montaje (decide qué va en pantalla y escribe el storyboard).
- **CLI Python `frame28`** (`plugin/cli/frame28/`, click): los pasos deterministas. Las skills lo invocan por Bash.

El **contrato** entre ambos es el **storyboard JSON** (`plugin/cli/frame28/STORYBOARD.md` lo documenta;
`frame28 storyboard schema` lo imprime). El agente escribe el storyboard; `frame28 build` lo convierte en una
composición **HyperFrames** (HTML + GSAP) y `frame28 render` la renderiza a MP4. **Nunca se edita el HTML
generado**: se edita el storyboard y se regenera.

**El método no vive aquí.** Desde la v0.5 las skills son cáscaras (descripción + «llama a `frame28_start` con la tarea») y
el plugin solo trae un `.mcp.json` remoto: el método del director (cuerpos de las skills y referencias), la Memoria de
marca y las campañas los sirve el MCP de frame28.app a las cuentas autenticadas, según su plan. Ese código está en el repo
privado `javierledesma28/frame28-app` (`api/frame28_api/metodo/`): cambiar el criterio de montaje es tarea de ese repo.
frame28.app (landing, panel, MCP, identidad) tampoco vive aquí; producto, planes y precios: `frame28-app/docs/plataforma.md`
(`research/07` y `08` de este repo son históricos).

Web del plugin (GitHub Pages sobre `docs/`, dominio propio con HTTPS forzado): `https://frame28.t28.io/` → guía
`/presentacion/`, asistente de instalación `/instalar/`, instaladores `/install.ps1` y `/install.sh`, instrucciones para
que Claude instale `/instalar.md`, roadmap por versiones `/roadmap/`.

**Regla de trabajo de Javier:** cada aprendizaje de un caso, un vídeo de ejemplo o un diagnóstico se capitaliza en el
motor (código del CLI, `doctor`, validaciones, pruebas) o, si es criterio de montaje, en el método de `frame28-app` (tarea
para su dueño), no en docs ni en el HANDOFF. Ante cada hallazgo: «¿qué cambia para que esto no vuelva a pasar?».

## Estructura

```
.claude-plugin/marketplace.json   este repo es su propio marketplace («think28»): sirve plugin/ desde la rama release
                                  (fuente git-subdir: Claude Code >= 2.1.69, y >= 2.1.288 si git < 2.39; F28-338)
plugin/                           EL PLUGIN (solo esto se instala; el resto del repo no se copia)
  .claude-plugin/plugin.json      manifiesto (name frame28; sin displayName, que no está en el esquema)
  skills/frame28*/SKILL.md        diez cáscaras (el método lo sirve el MCP)
  .mcp.json                       servidor MCP remoto `frame28` → https://frame28.app/mcp (OAuth con Frame28 ID, sin client id)
  cli/pyproject.toml              paquete Python (uv): dependencias con techo de versión mayor (av>=11,<18, ver Trampas);
                                  extras `probado` (versión exacta de cada paquete, la escribe scripts/fijar-dependencias.py)
                                  y `gpu` (CUDA 12 + onnxruntime-gpu; se instala con --excludes excluir-gpu.txt)
  cli/frame28/
    __init__.py                   __version__ (única fuente de la versión del CLI; pyproject la lee con hatch), HYPERFRAMES_VERSION, GSAP_VERSION
    env.py                        localiza ffmpeg/uv/npx (WinGet), caché ~/.cache/frame28, modelos; CUDA (`cuda_ready`,
                                  `enable_cuda_dlls`, `onnx_providers`), NVENC (`nvenc_ready`, `encoder_args`), `npx_cmd`
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
                                  markers (frases de resultado → before_after + draw check + kinetic; promesas → kinetic;
                                  cifras con unidad → chart counter, bar si se comparan, kinetic si son rango o lista)
    log.py                        registro de tiempo por orden (.frame28/log.jsonl, FRAME28_LOG) y `frame28 report` (+ `report note`)
    cover.py                      portada/miniatura: composición estática + hyperframes snapshot
    i18n.py                       extract/apply de textos traducidos; retime_words sobre el ritmo original
    brandsite.py                  marca desde la web del cliente (colores CSS y del logo, fuente con var(--…) resuelto, logo con variantes);
                                  ignora las variables de widgets de terceros (--oke-, --jdgm-…) y los colores por defecto de librerías;
                                  sin logo que lo avale el acento queda `accent_pending` con candidatos y `frame28 brand set` lo guarda (F28-299)
    build.py                      generador storyboard → HyperFrames (overlays, CSS, timeline GSAP, validate, platform_warnings,
                                  marca de agua `watermark` con sus avisos de lo que queda debajo); escapa todo lo que mete en el HTML (F28-84)
    motion.py                     tokens de movimiento de la marca (`motion`: entradas, salidas, curvas, style/avoid con los nombres
                                  de la Memoria) y anclas a la voz (`"word:x"`, `words_at: "auto"`) que build resuelve con words.json (F28-339)
    brandcheck.py                 nota de marca del storyboard antes del render (`storyboard brandcheck`): textos en pantalla
                                  contra la marca, el brief.md del montaje (Memoria + campaña) y la Memoria en JSON
    render.py                     check (separa errores/contraste/falsos positivos) y render (+ hoja de contacto que cubre el vídeo entero)
    imgio.py                      leer y escribir imágenes con rutas con acentos (F28-88)
    doctor.py, cli.py, STORYBOARD.md, brands/think28.json + brands/think28/*.svg
  cli/tests/                      pytest (grupo dev): conftest con fixtures de poc/ y datos sintéticos; un test_<módulo>.py por
                                  módulo del CLI (todos tienen al menos una prueba) más pruebas de pasos, herramientas, textos de
                                  entrada, instaladores, marca de agua, web de docs/ y release-check
docs/                             GitHub Pages: presentacion/ (deck + engine/), instalar/ (asistente web), instalar.md,
                                  install.ps1, install.sh, guion-demo.md, guia-plugin.md, brand/, CNAME, index.html
  roadmap/index.html              roadmap por versiones: los datos viven en el array ROADMAP del propio fichero (estado
                                  hecho/medias/pendiente por ítem); marcadores artifact:head/body para publicarlo como artefacto
scripts/release-check.py          checklist de release (ver «Cómo se publica una release»); --notes: commits desde el último tag
scripts/fijar-dependencias.py     comprueba o rehace el extra `probado` (--escribir tras tocar dependencias, --actualizar)
scripts/prueba-from-site.py       `brand from-site` contra una lista de webs (privada, fuera del repo), con caché
research/                         01 vídeo de referencia, 02 repos, 03 PoC compositores, 04 roadmap de features, 05 vídeo que vende
                                  (Cliente A), 06 monetización, 09 comparador antes/después, 10 referencias web, 11 competencia y
                                  buyer persona, 12 validación DTC; 07 y 08 (producto y plataforma) son históricos
poc/                              casos, cada uno con README, storyboard(s) y cuts.json versionados; work/ y out/ NO:
                                  clip-javier (10 s, referencia de regresión), clip-auriculares (anuncio 58 s),
                                  clip-whatsapp (vertical de móvil, inglés), clip-demo (guion de demo 83 s, + vertical),
                                  clip-tutorial (caso INVENTADO, F28-99: tutorial producido de una marca ficticia de velas;
                                  brief, storyboard, clips, short e i18n; fixture de la suite). Los casos reales del Cliente A
                                  son solo locales: fuera de git por `.git/info/exclude` (el `.gitignore` público los nombraría);
                                  cuáles son, en `_private/cliente-a/casos-locales.md`
_private/                         NO versionado (solo en la carpeta principal): caras, fotogramas y transcripción del vídeo de
                                  referencia; `confidencial.txt` (términos que busca release-check); `cliente-a/`;
                                  `historia-pre-a222.bundle` (copia de la historia anterior a la reescritura del 2026-10-19)
```

## Cómo se ejecuta

Instalación de desarrollo (en el PC de Javier: Windows 11, RTX 4060 con el extra `gpu`):
```bash
uv tool install --editable "./plugin/cli[probado]" --python 3.12     # CLI editable → ~/.local/bin/frame28, versiones probadas
uv tool install --editable "./plugin/cli[gpu,probado]" --python 3.12 --excludes ./plugin/cli/excluir-gpu.txt --reinstall
                                                           # opcional: CUDA 12 + onnxruntime-gpu (unos 3,3 GB) para transcribir, matte
                                                           # y OCR en GPU NVIDIA; sin --excludes quedan onnxruntime y -gpu juntos (F28-116)
claude plugin marketplace add C:/Workspaces/personal/Skill-Director   # marketplace "think28" (el plugin sale de la rama release de GitHub)
claude plugin install frame28@think28 --scope user
claude plugin validate ./plugin                             # SIEMPRE antes de commitear skills (y `claude plugin validate .` para el marketplace)
```
Tras editar skills: probarlas con `claude --plugin-dir ./plugin` (el marketplace sirve el plugin de la rama `release`
de GitHub, no de esta carpeta, F28-91); ya publicadas, `claude plugin uninstall frame28@think28 && claude plugin install
frame28@think28 --scope user` (con la misma versión, `update` no refresca el caché). Tras añadir o cambiar una dependencia
del pyproject: `python scripts/fijar-dependencias.py --escribir` (rehace el extra `probado`), pruebas y
`uv tool install --editable "./plugin/cli[probado]" --python 3.12 --reinstall` (también tras cambiar `__version__`).

Pipeline manual (lo que hace la skill directora):
```bash
frame28 fetch <url> -o input.mp4           # opcional: YouTube/Vimeo con yt-dlp (uvx, sin instalar)
frame28 prep input.mp4 -o work             # clip 30 fps sin audio, voz limpia a -14 LUFS (+voice_raw.wav), audio16k.wav; NVENC si hay GPU (--cpu lo evita)
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

**Pruebas:** `cd plugin/cli && uv run --extra probado --group dev pytest` (unas 370, unos 20 s, con las versiones exactas
que reciben los clientes). Sin modelos ni render y sin necesitar ffmpeg: las pruebas que lo llaman sustituyen ffmpeg y
`run`, y la suite pasa igual con `FRAME28_FFMPEG=/no/existe` (pasarla también así antes de integrar).
`FRAME28_PRUEBA_INSTALACION=1` suma la instalación limpia de punta a punta (~40 s con la caché de uv). En la carpeta
principal salen unas cuantas más que en un worktree: las que recorren `poc/*/storyboard*.json` también encuentran allí los
casos locales del Cliente A.
Fixtures: `poc/clip-javier/words.json`, los storyboards versionados y `poc/clip-tutorial/*.json`. La CI
(`.github/workflows/tests.yml`) pasa la suite en cada push que toque `plugin/cli/`, y `release-check` también. Lo que no
cubre (el render, el alfa de RVM, la detección de gestos y el OCR reales) se prueba con `frame28 check` + render + mirar
la hoja de contacto (`*_sheet.png`). Regresión rápida: `poc/clip-javier/storyboard-gsap.json` (10 s). Storyboards
completos: `poc/clip-demo/` (16 overlays, cortes, vertical), `poc/clip-tutorial/` (vídeo producido con su marca, shorts,
i18n; inventado y sin vídeo).

**Deck de la guía:** editar `docs/presentacion/deck.html`, luego `node engine/build.mjs deck.html --out index.html`
desde `docs/presentacion/` y comprobar en el navegador `Deck.check()` → `[]`. El motor (`engine/`) es neutro: no trae
logo ni marca (F28-109); los pone `think28-brand.css` (`--brand-*`, `.brand-logo`). El build puede dejar CRLF
en `index.html`: normalizar a LF antes de commitear.
Las páginas de `docs/` cargan Google Fonts **sin bloquear el primer pintado** (F28-121: costaba ~0,9 s de FCP móvil):
`<link id="t28-fuentes" … media="print">` + un script de una línea que lo pasa a `all` cuando la hoja ha cargado **y** el
navegador ya registró el `first-contentful-paint` (`PerformanceObserver` de tipo `paint`; sin él, dos
`requestAnimationFrame`; y a los 3 s pase lo que pase) + `<noscript>` de respaldo. Esperar al FCP no sobra: las fuentes
van con prioridad VeryHigh y, si terminan antes del primer pintado observado, Lighthouse las cuenta como bloqueantes y el
FCP simulado salta de ~1,1 a ~2,8 s; con la máquina cargada el fotograma se presenta tarde y los dos
`requestAnimationFrame` no bastaban. Detrás de cada fuente, su reserva con las mismas métricas (`@font-face` con
`size-adjust`): `'Inter Fallback'` (Arial) y `'Space Mono Fallback'` (Courier New al 102 %; con Consolas, 0,550 em frente
a 0,612, la cabecera de /instalar/ cambiaba de una a dos líneas y la página entera bajaba: CLS 0,8). Una página nueva
copia ese bloque de `docs/instalar/index.html`, con los dos `<link rel="icon">` (`/favicon.ico` y
`/brand/think28-isotipo.svg`) y su `meta description`; `tests/test_docs_web.py` lo comprueba.
El motor del deck deja sin maquetar las diapositivas que no se ven (`content-visibility:hidden` salvo `.is-active` e
`.is-exit`): las 19 maquetadas de golpe eran un `Layout` de 473 ms antes del primer pintado. `check()` las maqueta un
momento con la clase `deck-midiendo`; quien añada otra medición de slides ocultas tiene que hacer lo mismo. Por eso
el chequeo automático al cargar solo corre al editar (`file://`, localhost o `?check`): en la página publicada eran
~0,7 s de hilo principal por visita.

**Roadmap:** editar el array `ROADMAP` de `docs/roadmap/index.html` (estado `s` de cada ítem: hecho | medias |
pendiente; `next: true` marca el siguiente; la versión publicada lleva `state: "pub"` y la actual `here: true`). Comprobar
con `node --check` el bloque `<script>` que contiene `const ROADMAP` (el primero de la página es el de las fuentes) y
republicar el artefacto de claude.ai (https://claude.ai/artifact/CxhtKMffGhQRsKUhAqwUS8, «Frame28 Roadmap»; leerlo antes
con la acción read) con la variante sin doctype: el contenido entre los marcadores `artifact:head` y `artifact:body`.

## Cómo se publica una release

Solo con el «sí» de Javier a esa versión, pedido por el Despacho; hasta entonces lo terminado queda en `main` sin
etiquetar. La versión vive en **cuatro sitios**: `__version__` en `plugin/cli/frame28/__init__.py` (pyproject la lee),
`plugin/.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` y el README (cabecera y párrafo de «Estado y
roadmap»). Cada release los sube todos: `claude plugin update` solo actúa si cambió la versión del plugin.

1. En el worktree, rebase sobre `origin/main`; versión en los cuatro sitios; en el roadmap, la versión pasa a `"pub"` con
   `here: true` (quitárselo a la anterior), su parada de la cabecera a `done here` y el contador de releases.
2. Pruebas dos veces (normal y con `FRAME28_FFMPEG=/no/existe`), `claude plugin validate ./plugin` y `claude plugin validate .`.
3. Avance rápido de `main` en la carpeta principal y, **desde ella**, `python -X utf8 scripts/release-check.py --notes`:
   versiones, árbol, rama, tags, cuenta de `gh`, release, CLI, plugin, pruebas, extra `probado`, rama `release` y
   confidencialidad. Desde un worktree no hay `_private/` y la fila de confidencialidad se salta.
4. `git tag -a vX.Y.Z -m "Frame28 vX.Y.Z"` y un solo push atómico de main, tag y rama `release` (de ella instalan el
   instalador, el plugin y `uv tool upgrade`, F28-91):
   `git push --atomic origin main vX.Y.Z 'vX.Y.Z^{}:refs/heads/release'`
5. Notas con el formato de `gh release view v0.6.0` (entradilla, «Qué cambia al actualizar», «Novedades»,
   «Mantenimiento»), para el usuario y en tú; pasar los términos de `_private/confidencial.txt` por el fichero de notas
   antes de publicarlo. `gh auth switch --user javierledesma28`, `gh release create vX.Y.Z --repo
   javierledesma28/frame28 --title "Frame28 vX.Y.Z" --notes-file <notas> --verify-tag` y volver a dejar activa la cuenta
   corporativa (`gh auth switch --user javierledesmasmc`): con ella, `gh release` y `gh api` dan 403.
6. Comprobar en limpio lo que recibe un usuario. Motor: `UV_TOOL_DIR` y `UV_TOOL_BIN_DIR` en una carpeta temporal y
   `uv tool install --python 3.12 "frame28[probado] @ git+https://github.com/javierledesma28/frame28@release#subdirectory=plugin/cli"`
   → `frame28 --version` y `doctor`. Plugin: `CLAUDE_CONFIG_DIR` en una ruta **corta** (`C:/Users/ledes/AppData/Local/Temp/f28vN/cfg`)
   y `claude plugin marketplace add javierledesma28/frame28` + `install`; con una ruta larga (el scratchpad) el clon
   falla con «Filename too long».
7. Republicar el artefacto del roadmap y anotar en la tarea del backlog. `doctor` puede seguir anunciando la release
   anterior hasta 12 h: guarda la consulta a GitHub en `~/.cache/frame28/release.json` (1 h si falla), para no esperar el
   timeout sin red ni gastar el límite de 60 consultas por hora. No es un fallo.

Cómo actualizan los usuarios (README §Actualizar y `docs/instalar.md`): `uv tool upgrade frame28` (reinstala desde
GitHub en ~15 s aunque la versión no cambie; sigue la rama y los extras guardados en `uv-receipt.toml`, así que una
instalación sin `[probado]` no recibe las versiones probadas: el instalador la reinstala y `doctor` lo marca en
«librerías (versiones probadas)»; una anterior a la v0.6 sigue `main` y `doctor` lo marca en «origen del motor») y
`claude plugin marketplace update think28 && claude plugin update frame28@think28`. `frame28 doctor` lo dice solo: filas
«última release (CLI)» y «plugin (Claude Code)» (lee `~/.claude/plugins/installed_plugins.json`), cada una con su orden.

## Convenciones del repo

- Remoto: `git@github-jl28:javierledesma28/frame28.git` (`ssh -T git@github-jl28` → «Hi javierledesma28!»).
- `.gitattributes` fija LF; el `words.srt` que importa HyperFrames **solo funciona con LF**.
- `docs/install.ps1` **solo ASCII**: Windows PowerShell 5.1 lee la web en Latin-1.
- Descripciones YAML de las skills entre comillas simples (los `:` rompen el frontmatter y la skill no se dispara).
- Cada overlay del storyboard tiene `id` único (`validate` exige `^[A-Za-z][\w-]*$`, F28-84); todo `<video>/<audio>`
  generado lleva `id` (si no, HyperFrames lo congela). Capas con z-index explícito: 1 fondo, 2 texto behind, 3 alfa del
  hablante, 4 overlays, 5 pizarras, 6 venta (hook/cta/steps), 9 subtítulos, 20 marca de agua (`"watermark"` en la raíz,
  F28-298: fija de 0 a la duración total y en la zona segura del móvil; también `cover --watermark` y
  `clips scaffold|batch --watermark`).
- Lienzo: `canvas` del storyboard (1920×1080, 1080×1920 o 1080×1080). `speaker`/`gestures` devuelven coordenadas en el
  lienzo que corresponde al formato del clip (`captions.default_canvas`); las claves `*_1080p` son alias antiguos. Con
  ancho < 1400 el generador añade la clase `narrow` (gráficas, contadores y tarjetas compactos). `platform`
  (tiktok/reels/shorts) activa avisos de zonas seguras.
- Salidas, medios (`*.mp4 *.wav *.webm`), `work*/`, `node_modules/`, modelos, `*.source.json` y `_private/` van en
  `.gitignore`. Caras, logos y material de terceros **nunca** entran en el repo. La marca del Cliente A vive en la carpeta
  local de su caso y se regenera con `frame28 brand from-site`. Un caso de cliente no se versiona ni anonimizado: el
  público es inventado (`poc/clip-tutorial`, F28-99), porque la transcripción, el precio o el sector bastan para encontrar
  la marca con una búsqueda.
- Los análisis de negocio de `research/` se versionan en este repo público por decisión de Javier; ninguna cifra de
  precios se escribe aquí: la fuente es `frame28-app/docs/plataforma.md`.

## Decisiones técnicas

- **Qué recibe un cliente** (F28-91): dependencias con techo de versión mayor y un extra `probado` con la versión exacta de
  cada paquete, en todas las plataformas (resolución universal desde Python 3.11), con la que pasó la suite. Extra y no
  `--constraint`: uv guarda los constraints en el receipt tal cual y `uv tool upgrade` los repetiría viejos, mientras que
  el extra viaja en los metadatos del paquete y cada release trae los suyos. El código sale de la rama `release` (no de
  un tag: con `@vX.Y.Z` el upgrade no se movería nunca), que cada release adelanta.
- **HyperFrames 0.8.105** (Apache-2.0) como compositor, pineado (subirlo exige pasar las regresiones de `poc/clip-javier`
  y de un vídeo producido, el caso local del Cliente A); Remotion descartado (licencia de empresa >3 personas). PoC
  comparativa en `research/03-poc-compositores.md`.
- **faster-whisper** (medium; float16 en GPU, int8 en CPU) para tiempos por palabra; WhisperX/stable-ts con guion son
  mejora pendiente.
- **RobustVideoMatting ONNX** (GPL-3; onnxruntime lo carga dentro del CLI, NO es un proceso aparte; el modelo se descarga
  a `~/.cache/frame28/` y no se redistribuye; licencias de todo en `THIRD-PARTY-NOTICES.md`, que hay que tener al día) para el
  alfa del hablante; **MediaPipe Pose** (lite, misma caché) para gestos y reencuadre; **RapidOCR** (PaddleOCR en ONNX,
  Apache-2.0, modelos dentro del wheel) para el texto ya presente en vídeos producidos; **segno** (BSD) para QR.
- **GPU siempre que se pueda, nunca obligatoria** (premisa de Javier, 2026-10-03): el extra `frame28[gpu]` (`nvidia-cublas-cu12`,
  `nvidia-cudnn-cu12`, `onnxruntime-gpu`) da a faster-whisper y a onnxruntime las librerías CUDA; `transcribe --device auto`
  usa la GPU si `env.cuda_ready()` lo confirma y cae a CPU si falla a mitad. La codificación va por NVENC por defecto
  (`FRAME28_ENCODER=auto`: prueba real de 1 s, `env.nvenc_ready`, en caché una semana por ffmpeg) en prep, reframe, cut,
  clips y render; `--cpu` o `FRAME28_ENCODER=cpu` la fuerzan a libx264. Con el extra, matte (RVM) va en CUDA
  (`env.onnx_providers`, `--gpu/--cpu`, `FRAME28_ONNX=auto|gpu|cpu`); el OCR sigue en CPU salvo `--gpu`, porque ahí la
  CPU ganó (F28-116). El render se acelera sobre todo con `--workers` (la GPU solo codifica el final).
- **GSAP 3.13+** es gratis con plugins: `build.py` carga SplitText/DrawSVG solo cuando el storyboard los usa.
- **Todo lo que `build` mete en el HTML va escapado o validado** (F28-84): el storyboard lo escribe el agente a partir de
  transcripciones y webs de clientes, y una inyección ejecutaría JS en el Chrome de check/render. Ids, tiempos, colores y
  rutas se validan; los valores de JS van con `json.dumps`; las rutas son relativas al storyboard y `..` solo al principio.
- Limpieza de audio: `highpass 80` + `afftdn` (o `rnnoise` con modelo BSD en caché) + `loudnorm` en dos pasadas.
- Marca por nombre (`"brand": "think28"`) o por ruta (`.json`, también relativa al storyboard); búsqueda `./brands/`
  → `~/.config/frame28/brands/` → incluidas. `frame28 brand from-site <url>` la propone desde la web del cliente.
- La traducción a otro idioma la hace el agente (sin API ni modelo local); el CLI solo extrae, aplica y retiming.
- B-roll solo de Pexels/Pixabay (licencia comercial sin atribución) o material del usuario; licencia en sidecar.
- Instalación para no técnicos: `irm https://frame28.t28.io/install.ps1 | iex` / `curl -fsSL .../install.sh | bash`,
  o «Instala Frame28 siguiendo https://frame28.t28.io/instalar.md» pegado en Claude Code.
- El roadmap público vive en `docs/roadmap/index.html` con sus datos inline; no hay otra copia de los estados.
- **Identidad**: el plugin entra con Frame28 ID (tenant externo `frame28ciam.onmicrosoft.com`, Microsoft Entra External ID)
  a través de la fachada OAuth del MCP, sin client id en el `.mcp.json`. Identificadores, apps y scripts, en el repo
  `frame28-app` (`docs/identidad.md`); aquí solo se consume.

## Trampas ya sufridas (no repetir)

- **Plugin y su MCP (probado de verdad el 2026-10-02)**: (1) un servidor añadido a mano con la misma URL que el del plugin
  (`claude mcp add … https://frame28.app/mcp`) hace que Claude Code **oculte** `plugin:frame28:frame28`; para probar como un
  cliente, solo el del plugin. (2) Claude Code no abre el navegador desde una consola sin escritorio (SSH, ConPTY): lo dice
  en el registro (`--debug`: «Browser didn't open automatically») y enseña la URL en `/mcp`; las skills lo explican. (3)
  `claude -p` lanzado desde la shell de la app de escritorio responde «401 OAuth access token is invalid»: es el login de
  Claude Code de la terminal contra Anthropic, no Frame28; la prueba con el plugin se hace en una sesión nueva de la app.
  (4) Las versiones viejas de Claude Code no aceptaban nombres de servidores de plugin en `claude mcp get`; las actuales sí
  (`plugin:frame28:frame28`). (5) **`claude mcp login <servidor>` borra la sesión guardada en cuanto empieza, aunque no
  termine**: el 2026-10-08 una prueba con `--no-browser` y la entrada cerrada falló («stdin isn't a terminal») después de
  vaciar el token y desconectó a Javier en todas las sesiones nuevas. Nunca se lanza para comprobar: el estado lo dan
  `claude mcp list` (Connected / Needs authentication) o la fila «cuenta de Frame28» de `doctor`. `--no-browser` exige
  terminal interactiva. (6) La app de escritorio no tiene `/mcp` en la pestaña Code, pero cada sesión suya expone
  `CLAUDE_CODE_EXECPATH` (su propio `claude.exe`, que puede ser más nuevo que el de la terminal) y
  `CLAUDE_CODE_ENTRYPOINT=claude-desktop`. El almacén de credenciales MCP (`~/.claude/.credentials.json` en Windows) es
  común a la terminal y a la app; un MCP de plugin autenticado aparece en las sesiones que empiezan después, no en la que
  ya está abierta (F28-238).
- **ffmpeg y uv no siempre están en el PATH de la sesión Bash** (y WinGet cambia la carpeta de ffmpeg en cada actualización:
  8.1.1 pasó a 9.0.2): `export PATH="$(ls -d /c/Users/ledes/AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg_*/ffmpeg-*/bin | tail -1):/c/Users/ledes/AppData/Local/Microsoft/WinGet/Packages/astral-sh.uv_Microsoft.Winget.Source_8wekyb3d8bbwe:$HOME/.local/bin:$PATH"`
  (el CLI los localiza solo; la shell no).
- **PyAV**: uv resolvía `av` 19, que rompe faster-whisper (`metadata_errors`); `av` 14 no tiene wheel Windows → pin `<18`.
- **La GPU (RTX 4060 Laptop, 8 GB) transcribe**: las librerías CUDA van en el extra `gpu` y `doctor` lo confirma
  («gpu (transcripción) ✓ 1 GPU CUDA con cuBLAS y cuDNN»). **Medido el 2026-10-01**: el mismo audio de 160 s, 42,4 s en
  GPU (float16) frente a 178,7 s en CPU (int8), 4,2× más rápido con un render ocupando la máquina. NVENC en ffmpeg
  funciona sin instalar nada y, desde F28-114, **se usa solo**: el render final y los intermedios de prep, reframe y cut
  (`env.encoder_args`; 5× medido, fichero mayor) salen con `h264_nvenc` si `doctor` dice «codificador NVENC (GPU)». En una
  máquina sin NVIDIA la prueba falla y todo va por CPU sin pedir nada; `--cpu` para comparar o forzar.
- **onnxruntime-gpu y el OCR** (F28-116, medido el 2026-10-14 con la GPU ocupada al 98 % por un juego): (1) `onnxruntime` y
  `onnxruntime-gpu` dan el mismo módulo; con los dos instalados se pisan los ficheros y CUDA queda a suertes. faster-whisper
  pide `onnxruntime` por nombre, así que el extra `gpu` se instala con `--excludes plugin/cli/excluir-gpu.txt` (también como
  URL: uv guarda el nombre excluido en `uv-receipt.toml` y `uv tool upgrade` lo respeta); `doctor` marca los dos juntos
  como fallo y da la orden. `onnxruntime-gpu` < 1.27 (CUDA 12, la misma de ctranslate2; 1.27 pasa a CUDA 13). (2) Sin
  `env.enable_cuda_dlls()` onnxruntime no encuentra cuDNN y **sigue en CPU sin error** (RapidOCR solo avisa): por eso matte
  y graphics informan del proveedor real (`provider`). (3) RVM a 1080p: inferencia 592 → 103 ms por fotograma, pero el
  total solo gana ~20 % (1,2–1,4 → 1,5–1,7 fps): mandan escribir los PNG y codificar el VP9. (4) OCR: 1,2 s por fotograma
  en CPU y 1,5 s en CUDA con los mismos textos; por eso va en CPU salvo `--gpu`. (5) `cudnn_conv_algo_search=DEFAULT` en
  onnxruntime 1.2x con cuDNN 9 es el plan de reserva («Fallback mode. May be extremely slow»): el OCR en CUDA tardó 98,5 s
  frente a 27,7 s en CPU; usar HEURISTIC (EXHAUSTIVE ya no mide algoritmos: solo cambia la heurística). Los avisos de
  onnxruntime salen por stderr en UTF-16: `tr -d '\000'` antes de `grep`.
- **Decodificar en la GPU (NVDEC) no siempre gana** (F28-115, medido el 2026-10-03, prep = fps 30 + NVENC, RTX 4060 + 16
  núcleos): H.264 de 83 s, 14,8 → 11,0 s con la CPU libre y 28,6 → 18,8 s con la CPU ocupada; **AV1** de 160 s, 21,5 → 20,5 s
  libre y **27,1 → 66,4 s ocupada** (dav1d en CPU gana de largo). Y solo con el camino entero en GPU
  (`-hwaccel_output_format cuda` + `scale_cuda`): bajando los fotogramas a memoria, H.264 no ganaba y AV1 pasaba de 21,5 a
  37 s. Por eso `prep` usa NVDEC solo con H.264/HEVC y NVENC activo (`media.gpu_decode_args`, `decoder` en la salida) y, si
  falla, repite por CPU; cut, reframe y AV1 siguen por CPU. Un vídeo de móvil en rango completo sale `yuvj420p` por las dos vías.
- **Consola Windows en cp1252**: el CLI fuerza UTF-8 en stdout; en scripts sueltos, `python -X utf8` o evitar `→ ✓` en `print`.
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
  ("AROMÁTICAS" salía "AROMATICAS"); `build.highlight_line_height` abre el interlineado cuando hace falta. En portadas,
  parte el título con `|`: una línea que se parte sola no recibe ese tratamiento y pierde los descendentes.
- **Fondos claros**: cinéticos blancos o en acento no se leen (tutoriales cenitales, mesas, telas). `kinetic` tiene
  `color`; usar la tinta de la marca. Acento sobre acento nunca (texto en el acento sobre una tarjeta del mismo acento).
- **Plugin**: el caché copia todo el directorio del plugin → por eso vive en `plugin/`; con la misma versión,
  `claude plugin update` no refresca: desinstalar e instalar.
- **Añadir una dependencia a `pyproject.toml` no la instala**: la instalación editable no relee dependencias (ver «Cómo se
  ejecuta»; el Python de la herramienta está en `%APPDATA%/uv/tools/frame28/Scripts/python.exe`, no en `~/.local/share`).
- **No editar el CLI mientras un render corre en segundo plano**: cada `frame28 …` importa `cli.py` al arrancar y un
  fichero a medias lo tumba. Tampoco lanzar dos cadenas en segundo plano que escriban los mismos ficheros temporales. Para
  trabajar en el CLI con renders en marcha, un worktree; `uv run --project <worktree>/plugin/cli frame28 …` ejecuta esa
  versión desde cualquier carpeta.
- **GitHub Pages con dominio propio**: registrar el CNAME en Pages **después** de crear el DNS (si no, el
  certificado no se emite; se arregla quitando y volviendo a poner el cname por API). Al re-registrar el dominio, GitHub
  crea commits ("Create CNAME") en `main`: hacer `git pull --rebase`.
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
  0.2.0. Ahora pyproject la lee de `__init__.py` (hatch) y `release-check` comprueba los cuatro; `frame28 doctor`
  avisa si el código y la instalación no coinciden (la instalación editable no relee `__version__`: `--reinstall`).
- **`words.json` y `captions.json` se leen solo con `captions.load_words` / `load_captions`**: aceptan `text` o `word`,
  `start`/`end` en segundos o `startMs`/`endMs` en milisegundos (HyperFrames) y dict con `words` o `segments`, y dan un
  error corto (`TranscriptFormatError`) si faltan tiempos. Leerlos con `json.loads` a pelo es lo que hizo reventar
  `cut plan` con el fixture de clip-javier en milisegundos.
- **El render necesita red**: GSAP y sus plugins se cargan desde jsdelivr (`GSAP_VERSION`, en `__init__.py`); `doctor` lo
  comprueba como fila opcional. "Tu vídeo no sale de tu máquina" sigue siendo cierto: solo se descargan los scripts.
- **El nombre del cliente se cuela por donde el árbol no mira**: tras anonimizar el árbol seguía en notas de releases, en
  tags viejos y en una carpeta bajada de la nube sin ignorar dentro del repo (a un `git add -A` de publicarse). La fila
  `confidencialidad` de `release-check` busca los términos de `_private/confidencial.txt` en ficheros, historia, tags y
  releases e informa del sitio, nunca del término. Lo que se baje y nombre al cliente va a `_private/`. El
  `input.source.json` de `frame28 fetch` nombra el canal del dueño del vídeo: lo mantienen fuera `*.source.json` en el
  `.gitignore` y, para las carpetas enteras de casos de clientes, `.git/info/exclude`; quien descargue vídeos de clientes
  comprueba `git status` antes de añadir nada.
- **`git grep` no encuentra un término con tilde escrito con clase de caracteres** (`[ií]` no casa con una letra de dos
  bytes en UTF-8): para buscar variantes con y sin tilde, recorrer los ficheros en Python normalizando con `unicodedata`.
- **La historia se reescribió el 2026-10-19** (A-222, `git filter-repo`, una sola vez y con el visto bueno de Javier) para
  quitar el rastro del Cliente A y de la landing antigua. Las ramas y tags locales anteriores contienen la historia vieja: el
  gancho `.git/hooks/pre-push` de este clon (no versionado; lo heredan los worktrees) rechaza cualquier push que la
  contenga y explica el `git rebase --onto` que la arregla. Los SHA viejos siguen accesibles por la API de GitHub hasta
  que soporte purgue la caché (A-306, lo pide Javier); copia completa en `_private/historia-pre-a222.bundle`.
- **Lo «entregado fuera del repo» por una sesión en la nube puede no llegar al PC** (pasó con el script de tags, el
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
- **Patrones de resultado**: "when you're done" (promesa en futuro) y "perfect for this" (idoneidad) no son el
  momento del resultado; el encendido o el montaje final suelen decirse sin palabra clave ("lights up"): los
  marcadores automáticos son una propuesta y el `before_t` se elige mirando fotogramas del mismo encuadre.
- **El render no se acelera con la GPU, sino con trabajadores**: el tiempo se va en capturar cada fotograma con
  Chrome (~0,4 s por fotograma), que ya usa la GPU del navegador. La captura rápida de HyperFrames no se activa
  porque los overlays animan `clip-path` y máscaras. Medido con el clip de 10 s (16 núcleos, 32 GB): 6 trabajadores
  (por defecto) 81 s; `--workers 10` 68 s; 14, 76 s (se pisan); `--gpu` (NVENC) 73 s; `--workers 10 --gpu` 57 s con
  un fichero un 47 % mayor. Con más de 5 trabajadores hay que subir el heap de Node (`render` lo hace).
  F28-117 (2026-10-14, HyperFrames 0.8.105): Chrome con GPU (auto, ANGLE D3D11) y en software (SwiftShader) capturan
  igual de rápido, y la captura rápida forzada (`--experimental-fast-capture`) es 1,6× más lenta con 10 trabajadores:
  no hay nada que encender. Cifras en el docstring de `render.render_args`.
- **`check` tarda ~49 s y no hace falta repetirlo** cuando solo cambian textos o posiciones de un storyboard ya
  comprobado (versiones traducidas, re-renders tras revisar): en un vídeo real se pasó 11 veces, el 16 % del tiempo.
- **Cada `frame28 …` escribe `.frame28/log.jsonl` en el directorio actual**: lanzado desde la raíz del repo, el log aparece
  ahí (ignorado). Si reaparece como modificado, es que alguien corrió el CLI desde la raíz, no un cambio real. Los
  `.frame28/log.jsonl` de `poc/*/` son la bitácora real de lo que se ejecutó en cada caso: antes de fiarse del HANDOFF,
  `git status -sb`, `git log origin/main..main` y esos logs.
- **`cv2.imread`/`imwrite` fallan en silencio con rutas con acentos en Windows**: usar siempre `frame28.imgio` (F28-88).
- **Un `&` en la ruta parte la orden de `npx.cmd`** (`cmd.exe` lo interpreta): invocar npx solo con `env.npx_cmd` (F28-87).
- **Validar rutas del storyboard sin romper los casos locales**: los storyboards de `work/` usan `../clip.mp4`; por eso
  `validate` admite `..` solo al principio de la ruta y la copia de assets nunca escribe fuera del proyecto (F28-84).
