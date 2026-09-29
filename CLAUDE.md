# Frame28 · memoria del proyecto para Claude Code

Lee esto antes de tocar nada. Complementa a `HANDOFF.md` (estado y próximos pasos) y a `docs/guia-plugin.md`
(ciclo de vida del plugin). Responder siempre en español.

## Qué es

**Frame28** es un producto de **Think28** (marca personal de Javier Ledesma, `https://t28.io`; nada de branding
Fundanet/Semicrol aquí). Convierte un clip de una persona hablando a cámara en un video montado: rótulo de
identidad, títulos cinéticos por palabra, texto detrás del hablante, callouts donde señala, pizarras, gráficas,
subtítulos y tarjeta de marca. Todo generado por código, en local.

Dos piezas:
- **Plugin de Claude Code** (`plugin/`): cinco skills (`frame28-director` orquesta; `frame28-transcribe`,
  `frame28-cutout`, `frame28-storyboard`, `frame28-compose`). Claude dirige el montaje.
- **CLI Python `frame28`** (`plugin/cli/frame28/`, click): los pasos deterministas. Las skills lo invocan por Bash.

El **contrato** entre ambos es el **storyboard JSON** (`plugin/cli/frame28/STORYBOARD.md` lo documenta;
`frame28 storyboard schema` lo imprime). El agente escribe el storyboard; `frame28 build` lo convierte en una
composición **HyperFrames** (HTML + GSAP) y `frame28 render` la renderiza a MP4. **Nunca se edita el HTML
generado**: se edita el storyboard y se regenera.

Repo público: `https://github.com/javierledesma28/frame28`. Web (GitHub Pages sobre `docs/`, dominio propio con
HTTPS forzado): `https://frame28.t28.io/` → guía `https://frame28.t28.io/presentacion/`, instaladores
`https://frame28.t28.io/install.ps1` y `/install.sh`.

## Estructura

```
.claude-plugin/marketplace.json   este repo es su propio marketplace ("think28", source ./plugin)
plugin/                           EL PLUGIN (solo esto se instala; el resto del repo no se copia)
  .claude-plugin/plugin.json      manifiesto (name frame28)
  skills/frame28-*/SKILL.md       skills; frame28-storyboard/references/ = técnicas, guía de grabación, ejemplo
  cli/pyproject.toml              paquete Python (uv); pin av>=11,<18 (ver Trampas)
  cli/frame28/                    env, media(prep/probe/sheet), transcribe, cut, audio, matte(+speaker), pose(gestures),
                                  captions(páginas por palabra, SRT/VTT, lienzo por defecto), build(generador), render,
                                  doctor, cli, STORYBOARD.md, brands/think28.json + SVG
docs/                             GitHub Pages: presentacion/ (deck), install.ps1, install.sh, CNAME, .nojekyll,
                                  brand/ (logos oficiales), guia-plugin.md, index.html (redirige a la presentación)
research/                         01 resumen del análisis (el completo es privado), 02 repos, 03 PoC, 04 roadmap features
poc/                              pruebas: hyperframes/ y remotion/ (PoC), clip-javier/ (clip real del usuario,
                                  storyboards *.json y proyectos f28-*/ generados). Salidas y medios están en .gitignore
_private/                         NO versionado: caras, fotogramas y transcripción del video de referencia
```

## Cómo se ejecuta

Instalación de desarrollo (ya hecha en esta máquina):
```bash
uv tool install --editable ./plugin/cli --python 3.12     # CLI editable → ~/.local/bin/frame28
claude plugin marketplace add C:/Workspaces/personal/Skill-Director   # marketplace local "think28"
claude plugin install frame28@think28 --scope user          # tras editar skills: marketplace update + install
claude plugin validate ./plugin                             # SIEMPRE antes de commitear skills
```
Pipeline manual (lo que hace la skill directora), sobre `poc/clip-javier/`:
```bash
frame28 prep <clip.mp4> -o work            # clip 30 fps sin audio, voz limpia a -14 LUFS (+voice_raw.wav), audio16k.wav
frame28 transcribe work/audio16k.wav -o work --lang es   # words.json, captions.json, words.srt (LF), transcript.json
frame28 cut plan work/words.json --audio work/voice.wav -o work/cuts.json && frame28 cut apply ... -o work/cut
frame28 speaker work/clip.mp4              # lado libre y bbox del hablante
frame28 gestures work/clip.mp4 --words work/words.json -o work/gestures.json   # pointers propuestos (MediaPipe)
frame28 matte work/clip.mp4 --start 4.3 --end 6.8 -o work/alpha.webm            # solo el tramo con texto detrás
frame28 build storyboard.json -o project && frame28 check project && frame28 render project -o out/x.mp4
```
No hay tests automatizados: la prueba es `frame28 check` + render + mirar la hoja de contacto (`*_sheet.png`).
Storyboards de referencia que funcionan: `poc/clip-javier/storyboard-think28.json` (marca + gráficas),
`storyboard-gsap.json` (reveal rise/chars + draw), `storyboard-auto.json` (pointers de `gestures`).

Deck de la guía: editar `docs/presentacion/deck.html`, luego `node engine/build.mjs deck.html --out index.html`
desde `docs/presentacion/` y comprobar en el navegador `FundanetDeck.check()` → `[]`.

## Convenciones

- Idioma: español en docs, skills, mensajes del CLI y commits. Tono Think28: directo, técnico, humano; sin
  "innovador/disruptivo/robusto/holístico".
- Commits: mensaje descriptivo en español + línea `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`.
- Finales de línea LF (`.gitattributes`); el `words.srt` que importa HyperFrames **solo funciona con LF**.
- `docs/install.ps1` **solo ASCII**: Windows PowerShell 5.1 lee la web en Latin-1.
- Descripciones YAML de las skills entre comillas simples (los `:` rompen el frontmatter y la skill no se dispara).
- Cada overlay del storyboard tiene `id` único; todo `<video>/<audio>` generado lleva `id` (si no, HyperFrames lo
  congela). Capas con z-index explícito: 1 fondo, 2 texto behind, 3 alfa del hablante, 4 overlays, 5 pizarras, 9 subtítulos.
- Lienzo: `canvas` del storyboard (1920×1080, 1080×1920 o 1080×1080). `speaker`/`gestures` devuelven coordenadas en el
  lienzo que corresponde al formato del clip (`captions.default_canvas`); las claves `*_1080p` son alias antiguos. Con
  ancho < 1400 el generador añade la clase `narrow` (gráficas, contadores y tarjetas compactos).
- Salidas, medios (`*.mp4 *.wav *.webm`), `work*/`, `node_modules/`, modelos y `_private/` van en `.gitignore`.
  Caras y material de terceros **nunca** entran en el repo (el historial ya se limpió una vez por esto).
- Acciones persistentes (push, tags, cambios de visibilidad, DNS, instalar cosas en la máquina del usuario) se
  proponen antes de ejecutarlas; el usuario pidió acompañamiento paso a paso.

## Decisiones técnicas

- **HyperFrames 0.8.72** (Apache-2.0) como compositor, pineado; Remotion descartado (licencia de empresa >3 personas).
  PoC comparativa en `research/03-poc-compositores.md`.
- **faster-whisper** (CPU, medium int8) para tiempos por palabra; WhisperX/stable-ts con guion son mejora pendiente.
- **RobustVideoMatting ONNX** (GPL-3, ejecutado como proceso, modelo descargado a `~/.cache/frame28/`) para el
  alfa del hablante; **MediaPipe Pose** (lite, misma caché) para gestos.
- **GSAP 3.13+** es gratis con plugins: `build.py` carga SplitText/DrawSVG solo cuando el storyboard los usa.
- Limpieza de audio: `highpass 80` + `afftdn` (o `rnnoise` con modelo BSD en caché) + `loudnorm` en dos pasadas.
- Marca por nombre (`"brand": "think28"`), orden de búsqueda `./brands/` → `~/.config/frame28/brands/` → incluidas.
- Instalación para no técnicos: `irm https://frame28.t28.io/install.ps1 | iex` / `curl -fsSL .../install.sh | sh`.

## Trampas ya sufridas (no repetir)

- **ffmpeg y uv no siempre están en el PATH de la sesión Bash**: `export PATH="/c/Users/ledes/AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-8.1.1-full_build/bin:/c/Users/ledes/AppData/Local/Microsoft/WinGet/Packages/astral-sh.uv_Microsoft.Winget.Source_8wekyb3d8bbwe:$HOME/.local/bin:$PATH"` (el CLI los localiza solo; la shell no).
- **PyAV**: uv resolvía `av` 19, que rompe faster-whisper (`metadata_errors`); `av` 14 no tiene wheel Windows → pin `<18`.
- **Sin CUDA** en la máquina: faster-whisper y onnxruntime en CPU. No asumir GPU.
- **Consola Windows en cp1252**: el CLI fuerza UTF-8 en stdout; en scripts sueltos evitar `→ ✓` en `print`.
- **Parches a `build.py` con heredoc bash fallan** por las comillas: escribir el parche a un `.py` y ejecutarlo.
- **HyperFrames**: el `check` marca `text_occluded` en todo `behind` (falso positivo, `frame28 check` lo separa);
  la previsualización del Studio no respeta el rango de la capa alfa (el render sí); `hyperframes transcribe`
  exige whisper-cpp compilado (no usar; importar `words.srt` con `--preserve-cues` si hace falta).
- **Plugin**: el caché copia todo el directorio del plugin → por eso vive en `plugin/`; tras editar skills hay que
  `claude plugin marketplace update think28` + `install`.
- **GitHub Pages con dominio propio**: registrar el CNAME en Pages **después** de crear el DNS (si no, el
  certificado no se emite; se arregla quitando y volviendo a poner el cname por API). `docs/.nojekyll` evita
  fallos de build. Al re-registrar el dominio, GitHub crea commits ("Create CNAME") en `main`: hacer `git pull --rebase`.
- El `.ps1` se sirve como `application/octet-stream` pero `irm` lo devuelve como String en PS 5.1 y 7 (probado).
- El detector de falsos arranques no debe cortar estructuras paralelas ("por aquí hay X, por aquí hay Y"): solo
  repetición inmediata o tras pausa.
