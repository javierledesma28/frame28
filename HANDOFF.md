# HANDOFF · Frame28 · 2026-09-30 (noche: relevamiento completo e higiene de la 0.3.0)

Traspaso para retomar el proyecto desde otra cuenta de Claude Code **sin historial de conversación**. Lee primero
`CLAUDE.md` (qué es, estructura, cómo se ejecuta, convenciones, trampas). Este fichero es el estado, lo hecho y lo
que toca ahora. Todo lo de abajo está commiteado en `main` de `https://github.com/javierledesma28/frame28`.

## 1. En qué estábamos exactamente y por qué

Frame28 (marca Think28 de Javier Ledesma) convierte un clip hablado, o un vídeo ya producido, en un vídeo montado:
plugin de Claude Code (ocho skills) + CLI `frame28` + HyperFrames. En los últimos dos días el foco pasó de "montar
el clip de una persona" a **"vídeo que vende un producto DIY"**, usando como cliente tipo a **Cliente A** (kits de
grabado; tutorial de YouTube de 3 min 17 s, `poc/clip-grabado/`). De ahí salieron: overlays de venta, fábrica de
shorts, portada, versión en otro idioma, detección de gráficos existentes, reencuadre 9:16, marca desde la web.

**Regla de trabajo del usuario (2026-09-30, explícita):** todo lo que se aprende con un caso, un vídeo de ejemplo o
un diagnóstico se **capitaliza en el plugin** (código del CLI, `doctor`, validaciones, skills y sus referencias), no
se queda en un README, una PoC o este fichero. Ante cada hallazgo: "¿qué parte del CLI o de qué skill cambia?".

**Esta sesión** empezó con un relevamiento completo del repo (todo verificado ejecutando: doctor, validación del
plugin, los 11 storyboards, regresión build/check/render de clip-javier, web, releases, dependencias). El resultado
está incorporado abajo (secciones 4 y 5) y en las Trampas de `CLAUDE.md`. De la propuesta de seis puntos se ejecutó
el **punto 1 (higiene y cierre de la 0.3.0)**: tag y release `v0.3.0` publicados con el OK del usuario.

**Punto 2 (entregado en la misma sesión):** (a) el **roadmap visual con versiones** vive en `docs/roadmap/index.html`
(página Think28, datos inline en `ROADMAP`, filtro por estado; se publica en frame28.t28.io/roadmap/ al hacer push y
también como artefacto privado de claude.ai) y (b) el **análisis de monetización** en `research/06-monetizacion.md`
(tres caminos dimensionados, recomendación híbrida por fases, plan de 90 días, decisiones para el usuario).
`research/06` se dejó **sin versionar a propósito**: el repo es público y el usuario decide si se publica.
La recomendación (servicio operado por Think28 con el plugin abierto como canal; plataforma solo con demanda
demostrada) es la que ordena la v0.4.0 del roadmap. Ver sección 5.

## 2. Estado actual (qué existe y funciona)

Versión **0.3.0** en los cuatro sitios: `plugin/cli/frame28/__init__.py` (`__version__`, de donde `pyproject.toml`
la lee con hatch), `plugin/.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` y README.
`python scripts/release-check.py` lo comprueba. Tags/releases publicadas: `v0.1.0`, `v0.2.0` y **`v0.3.0`**
(2026-09-30, commit `f178d0c`, https://github.com/javierledesma28/frame28/releases/tag/v0.3.0, marcada Latest).

CLI `frame28` (todo probado en clips reales, Windows 11, CPU):
`fetch` (yt-dlp vía uvx) · `probe` · `prep` (30 fps, voz limpia −14 LUFS) · `transcribe` (faster-whisper, 4 formatos)
· `cut plan/apply` (silencios también dentro de palabras estiradas, muletillas condicionadas, falsos arranques;
remapea words/captions/storyboard) · `audio measure/clean/compare` · `speaker` · `gestures` (MediaPipe → pointers)
· `matte` (RVM) · `graphics` (RapidOCR: texto en pantalla, marca de agua, tarjetas, zonas libres) · `reframe`
(crop siguiendo la cara / blur) · `captions pages|export` (SRT/VTT) · `broll providers|suggest|search|fetch`
(Pexels/Pixabay; sin claves aún) · `clips plan|cut|scaffold` (fábrica de shorts, ganchos con la frase real)
· `cover` (portada/miniatura) · `i18n extract|apply` · `brand init|list|show|from-site` · `storyboard validate|schema`
· `build [--graphics]` · `check` · `render` · `sheet` · `frames` · `doctor` (también deriva de versión código vs
instalación y red para el CDN de GSAP).

Overlays del storyboard: lower_third, box, kinetic (con `color`), behind, pointer, card, list_focus, card_words,
image, brand_card, chart (bar/counter), draw, broll, hook, cta (QR), steps, before_after; `reveal` fade/rise/chars;
`caption_style` pages/karaoke; `canvas` 16:9/9:16/1:1; `platform` con zonas seguras.

`words.json` y `captions.json` se leen en todo el CLI con `captions.load_words` / `load_captions` (segundos o
milisegundos, `text` o `word`, lista o `segments`; error corto `TranscriptFormatError` si faltan tiempos).

Skills: director, transcribe, cutout, storyboard (+ 5 referencias), broll, shorts, i18n, compose.

Distribución: repo público, GitHub Pages en `frame28.t28.io` (guía deck, asistente web de instalación,
instaladores interactivos Windows/macOS, `instalar.md` para que Claude instale), plugin instalado en local desde el
marketplace local.

Casos reales en `poc/` (cada uno con README, storyboard y cuts.json versionados; medios en `work/`/`out/` no):

| Caso | Qué demuestra | Salida |
|---|---|---|
| clip-javier | referencia de regresión (10 s), brand kit, GSAP, pointers; `words.json` en formato del CLI | `out/*.mp4` |
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
- **30 sep (noche)**: relevamiento completo (46 commits, 142 ficheros, todo verificado ejecutando) e higiene de la
  0.3.0: `__version__` a 0.3.0 y pyproject dinámico (el bump anterior se lo había saltado y `frame28 --version`
  decía 0.2.0); cargador único y tolerante de `words.json`/`captions.json` en los siete puntos que los leían a pelo
  (`cut plan` reventaba con el fixture de clip-javier en milisegundos) con error corto y punto de entrada `cli:run`;
  `doctor` con deriva de versión, HyperFrames pineado, red para GSAP y filas opcionales; `GSAP_VERSION` como
  constante en build y cover; `scripts/release-check.py`; fixture de clip-javier normalizado; `think28.app` (dominio
  muerto) sustituido por `t28.io`; docs al día (displayName sí valida con Claude Code 2.1.126, ruta de ffmpeg
  independiente de la versión de WinGet, guía del plugin con la checklist de release).

## 4. A medias / pendiente inmediato (con ficheros)

1. **Tag y release `v0.3.0`: hechos** (2026-09-30, con el OK del usuario; plugin local reinstalado, caché idéntica al
   repo). Procedimiento que funcionó, para la próxima (desde `main` limpio y con `release-check` en verde):
   ```bash
   gh auth switch --user javierledesma28
   git push origin main
   git tag -a vX.Y.Z -m "Frame28 vX.Y.Z" && git push origin vX.Y.Z
   gh release create vX.Y.Z --repo javierledesma28/frame28 --title "Frame28 vX.Y.Z" --notes-file <notas> --latest
   gh auth switch --user javierledesmasmc     # dejar la cuenta como estaba
   ```
   Notas con el formato de `gh release view v0.3.0` (novedades, mantenimiento, pendiente conocido, instaladores);
   `release-check --notes` da el borrador. Tras publicar: `claude plugin uninstall frame28@think28 &&
   claude plugin install frame28@think28 --scope user`.
2. **Roadmap visual con versionado: hecho** (`docs/roadmap/index.html`, 6 versiones y 53 ítems con estado, esfuerzo,
   valor y referencia a R4/R5/T; el siguiente paso marcado). Mantenerlo: al cerrar un ítem, cambiar su `s` en el
   array `ROADMAP` del propio fichero (los estados y las versiones futuras son la única copia de esa información).
   Pendiente: decidir si se enlaza desde la web (hoy solo se sirve en `/roadmap/`, sin enlace).
3. **Análisis de monetización: hecho** (`research/06-monetizacion.md`, sin versionar hasta que el usuario decida).
   Quedan por responder las seis decisiones de su sección 8 (segmento, oferta y precio, qué sigue abierto, quién
   opera, marca de la oferta, umbrales para la plataforma).
4. **Suite mínima de pruebas** (deuda principal del relevamiento: 4.400 líneas de CLI y cero tests; el bug de
   `cut plan` lo destapó un smoke manual). Módulos puros y rápidos, sin render: `captions` (normalize_words,
   load_captions, pages, export), `cut.plan`/`remap_words`, `clips.plan`/`hooks_for`, `i18n.extract/apply/retime_words`,
   `build.validate`/`platform_warnings`. Fixture: `poc/clip-javier/words.json` y los storyboards versionados.
5. **Claves de Pexels/Pixabay** (las crea el usuario en pexels.com/api y pixabay.com/api/docs; van en
   `~/.config/frame28/keys.json` o variables `PEXELS_API_KEY`/`PIXABAY_API_KEY`). Hasta entonces `broll search`
   no está probado contra la API real (`plugin/cli/frame28/broll.py::search`).
6. **`install.sh` sin probar en un Mac real** sin Homebrew (`docs/install.sh`).
7. Pequeños pendientes técnicos: `reframe map` para convertir `pointer` del original sin repetir `gestures`
   (`reframe.py::map_point` existe, falta el comando); probar `reframe --mode crop` con un hablante que se mueva de
   verdad; `chart bar` en vertical con > 3 filas; `hooks_for` para tramos sin momentos (hoy plantilla de curiosidad:
   se ve en `clips plan` sobre clip-demo, tramo s1 con puntuación negativa).
8. Deuda menor detectada en el relevamiento: el render necesita red (GSAP por CDN en `build.py`/`cover.py`, sin SRI;
   decidir si se empaqueta local); HyperFrames 0.8.72 pineado con 0.8.98 publicada; OpenCV instalado por triplicado
   (`opencv-python`, `contrib` y `headless`, arrastrados por mediapipe y rapidocr; cv2 5.0.0 con pin `>=4.9`);
   `poc/remotion/package-lock.json` versionado aunque Remotion está descartado.

## 5. Próximos pasos priorizados

0. Puntos 1 (higiene, tag y release v0.3.0) y 2 (roadmap visual y monetización) **hechos**. Lo que sigue es el
   primer ítem de la v0.4.0: la suite mínima de pruebas (4.4), y las decisiones de `research/06` sección 8.
1. **Roadmap visual con versiones.** Agrupación aplicada en `docs/roadmap/index.html` (ajustar con el usuario):
   - v0.1.0 (hecho): plugin base, 5 skills, brand kit, gráficas, gestos, release.
   - v0.2.0 (hecho): jump cuts, audio, GSAP, instaladores, web.
   - v0.3.0 (publicada): vertical, subtítulos por palabras, B-roll, `graphics`, `reframe`, venta
     (hook/cta/steps/before_after), shorts, portada, i18n, `brand from-site`, `fetch`, doctor y cargador únicos.
   - v0.4.0 (propuesta): suite mínima de pruebas (4.4), cierre de lo a medias (4.5–4.7), doblaje/TTS
     (Kokoro/Chatterbox, roadmap 14), demo de pantalla con zoom-pan (roadmap 6), decisión sobre render sin red.
   - v0.5.0 (propuesta): puertas de calidad (pixelmatch, LUFS, legibilidad; roadmap 11), gráficas ampliadas (9),
     capítulos y miniaturas por beats (8), alineado forzado con guion (7), HyperFrames al día.
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
3. Suite mínima de pruebas (4.4): la deuda que más crece con cada feature.
4. Cerrar lo a medias antes de abrir la v0.4.0 (4.5–4.7).
5. Render sin red: empaquetar GSAP en el proyecto generado o documentarlo como requisito; depende de la promesa de
   producto que salga del punto 2.
6. HyperFrames 0.8.98 en una rama, con clip-javier y clip-grabado como criterio de aceptación.

## 6. Problemas conocidos y dudas

- El instalador `install.ps1` **sustituye** una instalación editable del CLI por la de GitHub. Se restaura con
  `uv tool install --editable ./plugin/cli --python 3.12 --reinstall` y el marketplace local con
  `claude plugin marketplace remove think28` + `add C:/Workspaces/personal/Skill-Director` + `install`.
- `gh` tiene dos cuentas (personal `javierledesma28`, dueña del repo; corporativa `javierledesmasmc`); si la activa es
  la corporativa el push da 403. `release-check` lo avisa. Ver CLAUDE.md, Convenciones.
- `frame28 doctor` marca como opcionales la GPU (onnxruntime CPU), el modelo RVM ("se descarga solo") y la red para
  GSAP; solo las filas no opcionales bloquean "Todo listo". Si el código y la instalación editable no coinciden,
  `--reinstall`.
- `displayName` en `plugin.json` **sí** valida con Claude Code 2.1.126 (comprobado); se dejó fuera porque no está en
  el esquema y no aporta nada.
- Render en CPU: ~2 min por cada 35 s en vertical 1080×1920; ~8–14 min para 3 min 17 s a 1080p; el `check` de un
  clip de 10 s tarda ~90 s (arranque de HyperFrames y Chrome).
- La detección de gestos usa umbrales heurísticos; en clips donde el hablante ocupa poco encuadre revisar
  `plugin/cli/frame28/pose.py::_hand_out`.
- `graphics` no distingue rótulos del editor de texto impreso en objetos quietos (clase orientativa).
- Los `chart` y `brand_card` con fondo de acento dan avisos de contraste en `frame28 check` (informativos).
- El deck usa el motor de `deck-fundanet` (skill privada del usuario) rebrandeado; los ficheros del motor están
  copiados en `docs/presentacion/engine/`, no hay dependencia externa; `index.html` se reconstruye idéntico desde
  `deck.html` (comprobado).
- Duda abierta del usuario, ahora central: si Frame28 acaba necesitando interfaz propia ("producto") además de
  las skills (sección 5.2).

## 7. Cómo verificar que todo sigue vivo (5 minutos)

```bash
frame28 doctor                                   # fila frame28: código e instalación en la misma versión
claude plugin validate ./plugin
python scripts/release-check.py --notes          # versiones, árbol, tags, cuenta gh, plugin
cd poc/clip-javier && frame28 cut plan words.json --audio voice.wav -o work/cuts.json
cd poc/clip-javier && frame28 build storyboard-gsap.json -o work/f28-gsap && frame28 check work/f28-gsap && frame28 render work/f28-gsap -o out/test.mp4
curl -sI https://frame28.t28.io/presentacion/ | head -1     # HTTP/2 200
```
