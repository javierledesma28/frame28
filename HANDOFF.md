# HANDOFF · Frame28 · 2026-09-30

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
  público; tag y release `v0.1.0`; GitHub Pages sobre `docs/` con dominio `frame28.t28.io` (CNAME en Cloudflare,
  HTTPS forzado); guía para no técnicos como deck de 17 slides (`docs/presentacion/`); instaladores
  `docs/install.ps1` (probado en esta máquina, funciona) e `install.sh` (solo sintaxis comprobada; sin Mac a mano).
- Versión subida a **0.2.0** en manifiestos, pyproject y README (ver "A medias").

## A medias / pendiente inmediato

1. **Tag y release v0.2.0**: los ficheros ya dicen 0.2.0 pero no hay tag. Hacer `git tag -a v0.2.0 -m "Frame28 v0.2.0"`,
   `git push --tags` y `gh release create v0.2.0 --title "Frame28 v0.2.0" --notes "..."` (proponer al usuario antes).
2. **Asistente de instalación guiado** (última petición del usuario, sin empezar). Quiere "un instalador
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
3. Subtítulos estilo TikTok/karaoke con presets + exportación SRT/VTT (`@remotion/captions` es MIT).
4. Reencuadre 9:16 con MediaPipe (ya en el stack) + composición vertical del mismo storyboard.
5. Demo de pantalla con zoom-pan (Playwright 1.59 `page.screencast` + `clicks.json` → overlay `screen`).
6. Gráficas ampliadas (line/area/donut/table-reveal) y puertas de calidad (pixelmatch, LUFS, legibilidad).
7. Alineado forzado con guion (stable-ts / WhisperX) para nombres propios y karaoke exacto.

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
