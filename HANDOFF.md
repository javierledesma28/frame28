# HANDOFF · Frame28 · 2026-09-30 (cierre de sesión, tarde)

Traspaso para retomar el proyecto desde otra cuenta de Claude Code **sin historial de conversación**. Lee primero
`CLAUDE.md` (qué es, estructura, cómo se ejecuta, convenciones, trampas). Este fichero es el estado, lo hecho y lo
que toca ahora. Todo lo de abajo está commiteado en `main` de `https://github.com/javierledesma28/frame28`.

## 1. En qué estábamos exactamente y por qué

Frame28 (marca Think28 de Javier Ledesma) convierte un clip hablado, o un vídeo ya producido, en un vídeo montado:
plugin de Claude Code (ocho skills) + CLI `frame28` + HyperFrames. En los últimos dos días el foco pasó de "montar
el clip de una persona" a **"vídeo que vende un producto DIY"**, usando como cliente tipo a **Cliente A** (kits de
grabado; tutorial de YouTube de 3 min 17 s, `poc/clip-grabado/`). De ahí salieron: overlays de venta, fábrica de
shorts, portada, versión en otro idioma, detección de gráficos existentes, reencuadre 9:16, marca desde la web.

**La última petición del usuario, interrumpida por falta de tokens** (es lo primero que hay que retomar):

> "Ármame un artefacto gráfico para entender en dónde estamos, cuáles son cada uno de los eventos que tenemos en
> el roadmap, cómo quedarían los versionados en cada uno de ellos y empecemos a trabajar en el primero. Aunque me
> gustaría primero que dimensionemos bien todo porque quizás me gustaría primero preparar o ver cómo vamos a hacer
> para que este plugin pueda ser monetizable. Para ello necesito que me ayudes a pensar si es mejor mantenerlo
> como plugin, montarlo como producto dentro de una plataforma, o ya me dirás tú."

Es decir, dos entregables antes de seguir con features: (a) un **artefacto visual del roadmap con versiones**
(hecho / en curso / pendiente, agrupado por versión) y (b) un **análisis de monetización** (plugin vs producto en
plataforma vs servicio) con recomendación. Ver sección 5.

## 2. Estado actual (qué existe y funciona)

Versión en ficheros: **0.3.0** (manifiesto, marketplace, pyproject, README). Tags/releases publicadas: `v0.1.0`,
`v0.2.0`. **El tag y la release `v0.3.0` NO están hechos** (proponer al usuario; el bump es solo de ficheros).

CLI `frame28` (todo probado en clips reales, Windows 11, CPU):
`fetch` (yt-dlp vía uvx) · `probe` · `prep` (30 fps, voz limpia −14 LUFS) · `transcribe` (faster-whisper, 4 formatos)
· `cut plan/apply` (silencios también dentro de palabras estiradas, muletillas condicionadas, falsos arranques;
remapea words/captions/storyboard) · `audio measure/clean/compare` · `speaker` · `gestures` (MediaPipe → pointers)
· `matte` (RVM) · `graphics` (RapidOCR: texto en pantalla, marca de agua, tarjetas, zonas libres) · `reframe`
(crop siguiendo la cara / blur) · `captions pages|export` (SRT/VTT) · `broll providers|suggest|search|fetch`
(Pexels/Pixabay; sin claves aún) · `clips plan|cut|scaffold` (fábrica de shorts, ganchos con la frase real)
· `cover` (portada/miniatura) · `i18n extract|apply` · `brand init|list|show|from-site` · `storyboard validate|schema`
· `build [--graphics]` · `check` · `render` · `sheet` · `frames` · `doctor`.

Overlays del storyboard: lower_third, box, kinetic (con `color`), behind, pointer, card, list_focus, card_words,
image, brand_card, chart (bar/counter), draw, broll, hook, cta (QR), steps, before_after; `reveal` fade/rise/chars;
`caption_style` pages/karaoke; `canvas` 16:9/9:16/1:1; `platform` con zonas seguras.

Skills: director, transcribe, cutout, storyboard (+ 5 referencias), broll, shorts, i18n, compose.

Distribución: repo público, GitHub Pages en `frame28.t28.io` (guía deck, asistente web de instalación,
instaladores interactivos Windows/macOS, `instalar.md` para que Claude instale), plugin instalado en local desde el
marketplace local.

Casos reales en `poc/` (cada uno con README, storyboard y cuts.json versionados; medios en `work/`/`out/` no):

| Caso | Qué demuestra | Salida |
|---|---|---|
| clip-javier | referencia de regresión (10 s), brand kit, GSAP, pointers | `out/*.mp4` |
| clip-auriculares | anuncio 58 s: cortes, gestos, contadores, behind, marca | `out/auriculares.mp4` |
| clip-whatsapp | vertical de móvil, inglés, subtítulos por palabras | `out/cliente-a_*.mp4` |
| clip-demo | guion de demo 83 s → 70 s; versión vertical con `reframe` | `out/demo.mp4`, `out/demo_vertical.mp4` |
| clip-grabado | vídeo producido de una marca: brief, 29 overlays, `graphics`, shorts (3 ganchos), portada, español | `out/cliente-a-glass.mp4`, `out/shorts/`, `out/cover-*.png` |

## 3. Completado, por sesiones

- **24–29 sep**: research (análisis del vídeo de referencia, repos, PoC HyperFrames vs Remotion, roadmap de 18
  features), plugin con 5 skills y CLI base, brand kit, gráficas, gestos, jump cuts, limpieza de audio, GSAP,
  repo público limpio, GitHub Pages con dominio, deck de guía, instaladores, releases v0.1.0 y v0.2.0.
- **30 sep (madrugada)**: anuncio de auriculares; guion de demo; instaladores interactivos y asistente web;
  lienzo a medida (vertical/cuadrado); subtítulos por palabras (`pages`/`karaoke`) y SRT/VTT; demo del plugin
  montada; `cut plan` más fino; B-roll (overlay, CLI, skill; sin claves).
- **30 sep (mañana)**: caso Cliente A: `fetch`, brief de marca, `brand from-site`, dos pasadas del montaje, rótulo
  sin recortes, `kinetic.color`, avisos de cajas fuera del lienzo, referencia marca-y-promocional; `graphics`
  (OCR + zonas libres + colisiones); `reframe` (crop/blur) con la demo en vertical.
- **30 sep (tarde)**: investigación "vídeo que vende DIY" (`research/05`); overlays hook/cta/steps/before_after;
  zonas seguras por plataforma; fábrica de shorts (`clips`) + skill; referencia de ganchos; tres variantes de short
  renderizadas; `cover` (16:9, 9:16, 1:1); `i18n` + skill (short en español); descendentes visibles en hook y
  portada (aviso del usuario); ganchos con la frase real del hablante; bump a 0.3.0 en ficheros.

## 4. A medias / pendiente inmediato (con ficheros)

0. **Crear el tag `v0.3.0` y la release en GitHub** (dejado pendiente a propósito por el usuario al cerrar la sesión;
   los ficheros ya están en 0.3.0, commit `27f43cc`). Comandos, desde `main` actualizado y con la cuenta
   `javierledesma28` activa en `gh`:
   ```bash
   git tag -a v0.3.0 -m "Frame28 v0.3.0" && git push origin v0.3.0
   gh release create v0.3.0 --repo javierledesma28/frame28 --title "Frame28 v0.3.0" --notes-file <notas> --latest
   ```
   Notas: lo de la sección 3 desde v0.2.0 (vertical y reencuadre, subtítulos por palabras y SRT/VTT, B-roll,
   `graphics`, overlays de venta, shorts, portada, i18n, `brand from-site`, `fetch`); formato como en v0.2.0.

1. **Artefacto gráfico del roadmap con versionado** (petición interrumpida; ver sección 5). No hay nada escrito
   aún; los datos están en `research/04-roadmap-features.md` (18 ítems con valor/esfuerzo), `research/05` (8 mejoras,
   6 hechas) y la sección 3 de este fichero. Formato: la skill de decks del usuario (`docs/presentacion/engine/`,
   motor copiado, brand `think28-brand.css`) o un HTML/SVG suelto en `docs/roadmap/`.
2. **Análisis de monetización** (ver sección 5). Sin empezar.
3. **Tag y release v0.3.0**: ficheros ya en 0.3.0; falta `git tag -a v0.3.0`, push del tag y `gh release create`
   con notas (proponerlo; el usuario aprueba las acciones persistentes). Notas: todo lo de la sección 3 desde v0.2.0.
4. **Claves de Pexels/Pixabay** (las crea el usuario en pexels.com/api y pixabay.com/api/docs; van en
   `~/.config/frame28/keys.json` o variables `PEXELS_API_KEY`/`PIXABAY_API_KEY`). Hasta entonces `broll search`
   no está probado contra la API real (`plugin/cli/frame28/broll.py::search`).
5. **`install.sh` sin probar en un Mac real** sin Homebrew (`docs/install.sh`).
6. Pequeños pendientes técnicos: `reframe map` para convertir `pointer` del original sin repetir `gestures`
   (`reframe.py::map_point` existe, falta el comando); probar `reframe --mode crop` con un hablante que se mueva de
   verdad; `chart bar` en vertical con > 3 filas; `hooks_for` para tramos sin momentos (hoy plantilla de curiosidad).

## 5. Próximos pasos priorizados

1. **Roadmap visual con versiones.** Propuesta de agrupación para el artefacto (ajustar con el usuario):
   - v0.1.0 (hecho): plugin base, 5 skills, brand kit, gráficas, gestos, release.
   - v0.2.0 (hecho): jump cuts, audio, GSAP, instaladores, web.
   - v0.3.0 (hecho en ficheros, sin tag): vertical, subtítulos por palabras, B-roll, `graphics`, `reframe`, venta
     (hook/cta/steps/before_after), shorts, portada, i18n, `brand from-site`, `fetch`.
   - v0.4.0 (propuesta): doblaje/TTS (Kokoro/Chatterbox, roadmap 14), demo de pantalla con zoom-pan (roadmap 6),
     `reframe map`, B-roll probado con claves.
   - v0.5.0 (propuesta): puertas de calidad (pixelmatch, LUFS, legibilidad; roadmap 11), gráficas ampliadas (9),
     capítulos y miniaturas por beats (8), alineado forzado con guion (7).
   - v1.0.0: interfaz sobre el storyboard (Studio o web) si la decisión de producto lo pide.
2. **Monetización: pensar antes de construir.** Marco para la conversación (no decidido):
   - *Plugin abierto + valor alrededor*: el plugin y el CLI siguen MIT (ya son públicos; retirar la licencia no cierra
     lo publicado). Se cobra por marca/plantillas premium (brand packs, ganchos por sector), por servicio de
     montaje (Think28 monta vídeos para marcas como Cliente A con el plugin como herramienta interna), o por
     formación. Ventaja: cero infraestructura, coherente con el estado actual. Riesgo: el plugin en sí no factura.
   - *Producto en plataforma*: una web donde el cliente sube el clip y recibe el vídeo (render en servidor: Chrome
     headless + ffmpeg + modelos; hoy todo corre en local y tarda 2–14 min por vídeo en CPU). Requiere colas, GPU o
     paciencia, almacenamiento, cuentas, pagos (Stripe), y una interfaz sobre el storyboard. Ventaja: es lo que una
     empresa como Cliente A compraría sin instalar nada. Riesgo: obra grande; la dependencia de Claude Code
     desaparece y el "director" pasaría a ser la API de Claude (coste por vídeo).
   - *Híbrido por fases*: mantener el plugin como canal de adopción y demo, y montar un servicio gestionado para
     2–3 clientes de referencia (Cliente A como primero) con el pipeline actual, antes de invertir en plataforma.
     Es la recomendación por defecto salvo que el usuario quiera producto desde ya.
   - Preguntas a resolver con el usuario: a quién se vende (marcas DTC, agencias, creadores), precio por vídeo o
     suscripción, qué parte debe seguir abierta, si Think28 opera el servicio, y si la licencia de HyperFrames
     (Apache-2.0) y de los modelos (RVM GPL-3 como proceso, RapidOCR Apache, MediaPipe Apache) permiten el uso
     comercial previsto (sí, con RVM ejecutado como proceso externo y sin enlazarlo).
3. Tag y release v0.3.0 (tras 1 y 2, o antes si el usuario lo pide).
4. Roadmap técnico según la agrupación aprobada (v0.4.0 primero).

## 6. Problemas conocidos y dudas

- El instalador `install.ps1` **sustituye** una instalación editable del CLI por la de GitHub. Se restaura con
  `uv tool install --editable ./plugin/cli --python 3.12 --reinstall` y el marketplace local con
  `claude plugin marketplace remove think28` + `add C:/Workspaces/personal/Skill-Director` + `install`.
- `gh` tiene dos cuentas (personal `javierledesma28`, dueña del repo; corporativa `javierledesmasmc`); si la activa es
  la corporativa el push da 403. Ver CLAUDE.md, Convenciones.
- `frame28 doctor` marca la GPU como ausente (onnxruntime CPU) y el modelo RVM como "se descarga solo": normal.
- Render en CPU: ~2 min por cada 35 s en vertical 1080×1920; ~8–14 min para 3 min 17 s a 1080p.
- La detección de gestos usa umbrales heurísticos; en clips donde el hablante ocupa poco encuadre revisar
  `plugin/cli/frame28/pose.py::_hand_out`.
- `graphics` no distingue rótulos del editor de texto impreso en objetos quietos (clase orientativa).
- Los `chart` y `brand_card` con fondo de acento dan avisos de contraste en `frame28 check` (informativos).
- El deck usa el motor de `deck-fundanet` (skill privada del usuario) rebrandeado; los ficheros del motor están
  copiados en `docs/presentacion/engine/`, no hay dependencia externa.
- Duda abierta del usuario, ahora central: si Frame28 acaba necesitando interfaz propia ("producto") además de
  las skills (sección 5.2).

## 7. Cómo verificar que todo sigue vivo (5 minutos)

```bash
frame28 doctor
claude plugin validate ./plugin
cd poc/clip-javier && frame28 build storyboard-gsap.json -o work/f28-gsap && frame28 check work/f28-gsap && frame28 render work/f28-gsap -o out/test.mp4
curl -sI https://frame28.t28.io/presentacion/ | head -1     # HTTP/2 200
```
