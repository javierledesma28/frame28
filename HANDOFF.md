# HANDOFF · Frame28 · 2026-09-30 (actualizado tras la sesión de la noche)

Traspaso para retomar el proyecto desde otra sesión de Claude Code sin historial de conversación. Lee primero
`CLAUDE.md` (qué es, estructura, convenciones, trampas). Esto es el estado y lo que toca hacer.

## En qué estábamos y por qué

Frame28 (Think28) convierte un clip hablando a cámara en un video montado, vía un plugin de Claude Code + CLI
`frame28` + HyperFrames. El objetivo del usuario (Javier Ledesma) es **iterarlo y compartirlo con otras personas,
incluidas no técnicas**. Por eso los dos últimos bloques de trabajo fueron: (1) más técnicas de montaje sobre su
propio clip de prueba, y (2) distribución: repo público, guía como presentación web en dominio propio e
instaladores de una línea.

Se trabajaba paso a paso: cada feature se prueba con `poc/clip-javier/` (clip real de 10 s del usuario) y se
documenta en skills/README antes de pasar a la siguiente.

## Completado en las sesiones del 24 al 30 de septiembre de 2026

Todo commiteado y en `main` de `https://github.com/javierledesma28/frame28` (público):

- Research: análisis del video de referencia (16 técnicas), evaluación de repos, PoC HyperFrames vs Remotion
  (decisión: HyperFrames), investigación de features con roadmap priorizado (`research/04-roadmap-features.md`).
- Plugin con 5 skills y CLI `frame28` con: `prep` (30 fps + voz limpia −14 LUFS), `transcribe` (faster-whisper,
  4 formatos), `cut plan/apply` (silencios, muletillas, falsos arranques; remapea words/captions/storyboard),
  `audio measure/clean/compare`, `speaker`, `gestures` (MediaPipe → pointers propuestos), `matte` (RVM),
  `storyboard validate/schema`, `build`, `check`, `render`, `doctor`, `brand init/list/show`, `frames`, `sheet`.
- Overlays del storyboard: lower_third, box, kinetic, behind, pointer, card, list_focus, card_words, image,
  brand_card, chart (bar con hero, counter), draw (iconos DrawSVG); `reveal` fade/rise/chars en textos; marca por
  nombre con `brands/think28.json` + logos oficiales.
- Distribución: plugin validado e instalado en local; repo recreado limpio (sin caras ni material de terceros) y
  público; tags y releases `v0.1.0` y `v0.2.0` (2026-09-30); GitHub Pages sobre `docs/` con dominio `frame28.t28.io` (CNAME en Cloudflare,
  HTTPS forzado); guía para no técnicos como deck de 17 slides (`docs/presentacion/`); instaladores
  `docs/install.ps1` (probado en esta máquina, funciona) e `install.sh` (solo sintaxis comprobada; sin Mac a mano).
- Versión **0.2.0** en manifiestos, pyproject y README, etiquetada y publicada como release en GitHub.

## A medias / pendiente inmediato

1. **Asistente de instalación guiado**: HECHA la parte de scripts interactivos (`docs/install.ps1` e `install.sh`:
   pasos numerados con motivo, prompts reintentar/saltar/salir desde el teclado aunque lleguen por `curl | bash` /
   `irm | iex`, modo `-y` / `FRAME28_YES=1`, log en `~/frame28-install.log`, Homebrew y Claude Code se instalan
   si faltan, runtime VC++ en Windows). Probado en Windows en modo silencioso; **install.sh sin probar en Mac real**
   (un usuario del entorno del autor tenía un Mac sin Homebrew: ese es el caso a validar). La parte web también está hecha: `docs/instalar/index.html` (asistente: detecta el sistema, línea con copiar, pasos, checklist) y `docs/instalar.md` (instrucciones para que Claude Code instale por ti). Quedaba en el plan original: Quiere "un instalador
   interactivo que te acompañe, te diga en qué paso estás y te muestre los prompts para aceptar", sin violar
   políticas de Windows/Mac. Un navegador no puede ejecutar comandos locales, así que la respuesta recomendada es:
   - **Claude Code como asistente**: publicar `docs/instalar.md` con instrucciones para el agente y decirle al
     usuario que pegue en Claude Code "Instala Frame28 siguiendo https://frame28.t28.io/instalar.md". Claude
     ejecuta cada paso, explica y **los prompts de permiso de Claude Code son exactamente el "aceptar y sigue"**.
   - **Página web asistente** `docs/instalar/index.html`: detecta el sistema, muestra la línea correcta con botón
     "Copiar", checklist de pasos con lo que se verá en pantalla, enlace a la guía. Sin ejecutar nada.
   - Los scripts ya son idempotentes y muestran el paso actual; se les puede añadir modo `-Interactive` con
     confirmación por paso si se quiere.
3. **Verificar `install.sh` en un Mac real** (Homebrew) y `install.ps1` en un Windows limpio sin winget/Node.

## Próximos pasos priorizados (del roadmap `research/04-roadmap-features.md`)

1. Asistente de instalación guiado (arriba).
2. B-roll por palabra clave (Pexels/Pixabay, licencia registrada) → overlay `broll` con Ken Burns.
3. ~~Subtítulos estilo TikTok/karaoke con presets + exportación SRT/VTT~~ hecho (propio, sin `@remotion/captions`).
4. Reencuadre 9:16 con MediaPipe (ya en el stack) desde clip apaisado (la composición vertical ya existe).
5. Demo de pantalla con zoom-pan (Playwright 1.59 `page.screencast` + `clicks.json` → overlay `screen`).
6. Gráficas ampliadas (line/area/donut/table-reveal) y puertas de calidad (pixelmatch, LUFS, legibilidad).
7. Alineado forzado con guion (stable-ts / WhisperX) para nombres propios y karaoke exacto.

## Hecho además en la sesión del 30 de septiembre (noche)

- Segundo clip real, un anuncio de auriculares de 58 s, montado con todo el pipeline (`poc/clip-auriculares/`, README propio). Salió a la primera salvo el sufijo del contador sobre fondo de acento (corregido en `build.py`).
- `docs/guion-demo.md`: guion de 60 s con qué decir y qué gesto hacer para grabar una demo que luzca todas las técnicas.

## Hecho en la sesión del 30 de septiembre (madrugada): vertical y subtítulos por palabras

- Tercer clip real (`poc/clip-whatsapp/`): vídeo de móvil por WhatsApp, vertical 464×832, voz en inglés, 11,5 s.
  Primer montaje 9:16 (`canvas` 1080×1920). Destapó que gráficas, subtítulos y cajas de cara asumían 1920×1080.
- **Lienzo a medida en todo el pipeline**: `captions.default_canvas()` elige 1920×1080 / 1080×1920 / 1080×1080 por el
  formato del clip; `frame28 speaker` y `frame28 gestures` aceptan `--canvas WxH` y devuelven `bbox_canvas`/`face_box`
  (las claves `*_1080p` quedan como alias). `build` añade la clase `narrow` (< 1400 px de ancho) que compacta chart,
  counter, card y brand_card; los subtítulos por frase envuelven a dos líneas y suben a 200 px en vertical.
- **Subtítulos por palabras**: `caption_style` en el storyboard con presets `pages` (aparecen al decirse, mayúsculas,
  estilo Shorts) y `karaoke` (palabra actual en acento), paginado por puntuación, pausas y `max_words`/`max_chars`;
  `frame28 captions pages` lo previsualiza. Probado en vertical (`out/cliente-a_pages.mp4`, `out/cliente-a_karaoke.mp4`).
- **Exportación SRT/VTT**: `frame28 captions export words.json -o x.srt|.vtt` con ≤ 42 caracteres/línea, 2 líneas,
  1–7 s, corte en puntuación/pausas, aviso si > 17 cps. Los tokens "%"/"€"/"$" sueltos del ASR se pegan a la cifra.
- Manifiesto: Claude Code 2.1.150 rechaza `displayName` en `plugin.json` (eliminado); URLs de marca a t28.io.
- Regresión 16:9 (`poc/clip-javier/storyboard-gsap.json`) construida, comprobada y renderizada sin cambios visibles.
- Pendiente de este bloque: reencuadre automático 9:16 desde un clip apaisado (seguir la cara con MediaPipe) y
  `chart bar` en vertical con más de 3 filas (hoy se compacta pero no se reordena en vertical).

## Hecho después: clip de demo del plugin (`poc/clip-demo/`)

- El guion de `docs/guion-demo.md` grabado (83 s) y montado: 16 overlays, 19 cortes, `out/demo.mp4` (70 s).
- `cut.py`: silencios dentro de palabras estiradas y muletillas condicionadas por pausa (ver README del PoC).
  Regresión comprobada sobre `clip-auriculares` (solo cae el "Bueno," inicial).
- **B-roll hecho** (commit `ed8bc87`): módulo `broll.py` (sugerencia de palabras clave por frase, búsqueda en Pexels y
  Pixabay con claves en `PEXELS_API_KEY`/`PIXABAY_API_KEY` o `~/.config/frame28/keys.json`, descarga con sidecar de
  licencia y recorte con ffmpeg, hoja de candidatos), overlay `broll` en `build.py` (pantalla completa o `pip`,
  `in` vía `data-media-start`, `loop`, Ken Burns, `caption`, `credit` arriba a la derecha; el contenedor NO lleva
  `data-start`, HyperFrames no admite vídeo temporizado dentro de otro elemento temporizado), CLI `frame28 broll
  providers/suggest/search/fetch` y skill `frame28-broll`. Probado el overlay con material sintético (clip-javier);
  **la búsqueda real no está probada: faltan las claves** (el usuario debe registrarse en Pexels y Pixabay).
- En curso: `poc/clip-grabado/` (vídeo promocional-tutorial de YouTube de la marca Cliente A, 3 min 17 s,
  inglés, con música de fondo). Brief de marca en `brief.md`; marca `cliente-a` en `work/brands/` (no versionada:
  logo de terceros). **Primera pasada renderizada** (`out/cliente-a-glass.mp4`, 26 overlays, 7 min 46 s de render) y
  entregada al usuario; storyboard versionado. Lecciones: fondos claros → `kinetic` con `color` oscuro (nuevo campo);
  el rótulo recortaba el título con un wordmark ancho (arreglado: `logo_width`); la segunda línea del rótulo en Space
  Mono aún se queda corta con textos largos (factor 0,66 por carácter es optimista para esa fuente: subir a ~0,72).
  **Segunda pasada** (29 overlays: + "Follow the marker lines", "beautiful frosted effect", check dibujado en "That's it!")
  con el rótulo arreglado de raíz (commit `4e2f8de`).
- **Conocimiento capturado en el plugin** (commit `4e2f8de`): `frame28 brand from-site <url> --name <marca>`
  (`brandsite.py`: colores del CSS y variables `--color-button`, fuente, logo con variantes on_dark/on_accent);
  `lower_third` sin estimar anchos (caja `max-content`, tecleo por `clip-path`); aviso en `build` de `box` fuera del
  lienzo; `kinetic.color`; referencia `frame28-storyboard/references/marca-y-promocional.md` (investigar la marca,
  checklist de storytelling promocional, vídeo ya producido, legibilidad); director con brief de marca y modo vídeo
  producido; trampas nuevas en CLAUDE.md (parches por stdin, vídeo anidado en HyperFrames, no tocar el CLI durante
  un render en segundo plano).

## Problemas conocidos y dudas

- El instalador `install.ps1` **sustituye** una instalación editable del CLI por la de GitHub. En esta máquina se
  restauró con `uv tool install --editable ./plugin/cli --python 3.12 --reinstall` y el marketplace local con
  `claude plugin marketplace remove think28` + `add C:/Workspaces/personal/Skill-Director` + `install`. Si en
  otra máquina se usa el instalador y luego se desarrolla, repetir esto.
- `frame28 doctor` marca la GPU como ausente (onnxruntime CPU) y el modelo RVM como "se descarga solo": normal.
- La detección de gestos usa umbrales heurísticos (mano fuera del torso, dentro del encuadre); en clips donde el
  hablante ocupa poco encuadre habrá que revisar `plugin/cli/frame28/pose.py::_hand_out`.
- Los `chart` y `brand_card` con fondo de acento dan avisos de contraste en `frame28 check` (informativos).
- El deck usa el motor de `deck-fundanet` (skill privada del usuario) rebrandeado: no hay dependencia en el repo,
  los 5 ficheros del motor están copiados en `docs/presentacion/engine/`.
- Duda abierta del usuario: si Frame28 acaba necesitando una interfaz propia sobre el storyboard ("producto")
  además de las skills. Postura actual: skills + CLI, con el Studio de HyperFrames como revisión visual.

## Cómo verificar que todo sigue vivo (5 minutos)

```bash
frame28 doctor
claude plugin validate ./plugin
cd poc/clip-javier && frame28 build storyboard-gsap.json -o f28-gsap && frame28 check f28-gsap && frame28 render f28-gsap -o out/test.mp4
curl -sI https://frame28.t28.io/presentacion/ | head -1     # HTTP/2 200
```
