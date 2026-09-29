# Investigación de repos open source para Skill-Director

**Fecha:** 2026-09-24. Estrellas, última actividad y licencia verificadas contra la API de GitHub ese día.
**Contexto:** ver `01-analisis-video-referencia.md` para el catálogo de técnicas (T1–T16) que estas herramientas deben cubrir.

---

## 0. Hallazgo principal antes de entrar por categorías

Hay dos cambios de escenario respecto a 2024-2025 que condicionan todo el diseño:

1. **[HyperFrames](https://github.com/heygen-com/hyperframes)** (HeyGen, creado en marzo 2026): ~52,8k ⭐, Apache-2.0, TypeScript, push diario. "Write HTML. Render video. Built for agents." Composiciones = HTML con `data-start`/`data-duration`/`data-track-index` + GSAP/CSS/Lottie; render determinista con Puppeteer + FFmpeg; 21 skills para Claude Code, incluida **`/talking-head-recut`**, que hace exactamente el formato que buscamos: coger un vídeo de presentador y superponerle tarjetas sincronizadas al transcript (títulos cinéticos, lower-thirds, *data callouts*, pull-quotes, PiP "speaker en la esquina mientras un gráfico llena el frame"). Es el competidor directo de Remotion sin la licencia de empresa.
2. **[remotion-dev/skills](https://github.com/remotion-dev/skills)** (~4,7k ⭐, 12 skills, `npx skills add remotion-dev/skills`, >126k instalaciones en skills.sh): Remotion ha apostado oficialmente por que los agentes escriban las composiciones. Pero la licencia sigue siendo el freno (ver §1).

Ambos son "agent-first" y ambos existen como skills de Claude Code, así que Skill-Director no debería reimplementar el compositor: debería **orquestar** uno de ellos (o los dos detrás de una spec común) y aportar lo que ninguno trae: transcripción/alineado en español, recorte del presentador, capturas de pantalla scriptadas y la traducción transcript → storyboard.

---

## 1. Frameworks de composición programática

| Repo | ⭐ | Última act. | Licencia | Lenguaje | Veredicto |
|---|---|---|---|---|---|
| [remotion-dev/remotion](https://github.com/remotion-dev/remotion) | 60,3k | 24-09-2026 | Propia ("Remotion License") | TS/React | Ecosistema más maduro; determinista por frame (`useCurrentFrame`); Player, Studio, Lambda. **Caveat licencia** |
| [heygen-com/hyperframes](https://github.com/heygen-com/hyperframes) | 52,8k | 24-09-2026 | Apache-2.0 | TS/HTML | Nativo para agentes, sin React, GSAP; 6 meses de vida → API en movimiento; upsell a render cloud de HeyGen (opcional) |
| [motion-canvas/motion-canvas](https://github.com/motion-canvas/motion-canvas) | 19,2k | jul-2026 (mantenimiento) | MIT | TS | Autor original retirado; web caída; comunidad en [canvas-commons](https://github.com/canvas-commons/canvas-commons) (244 ⭐). Generadores `yield*`, menos natural para un LLM que React |
| [redotvideo/revideo](https://github.com/redotvideo/revideo) | 4,1k | jul-2026 | MIT | TS | Fork de Motion Canvas con API de render; comunidad pequeña, ritmo bajo |
| [diffusionstudio/core](https://github.com/diffusionstudio/core) | 1,2k | nov-2025 | MPL-2.0 | TS | WebCodecs en navegador sobre Mediabunny; sin actividad en 10 meses |
| [Vanilagy/mediabunny](https://github.com/Vanilagy/mediabunny) | 7,2k | 23-09-2026 | MPL-2.0 | TS | Toolkit de demux/mux/convert puro TS; Remotion 5 migra a él. Útil como utilidad, no compositor |
| [mifi/editly](https://github.com/mifi/editly) | 5,5k | may-2025 | MIT | TS | Declarativo sobre ffmpeg; parado |
| [Zulko/moviepy](https://github.com/Zulko/moviepy) | 14,9k | ago-2026 | MIT | Python | Vivo pero "maintainers wanted"; render lento por frame; válido para glue, no para motion graphics |
| Manim Community | — | activo | MIT | Python | Animación matemática; no encaja con el estilo "creator" |
| [theatre-js/theatre](https://github.com/theatre-js/theatre) | 12,7k | ago-2024 (público) | Apache-2.0 | TS | Desarrollo movido a repo privado hacia 1.0; descartar |
| [ncounterspecialist/twick](https://github.com/ncounterspecialist/twick) | 533 | jun-2026 | "Other" | TS/React | SDK de editor con timeline; pequeño |
| [OpenCut-app/OpenCut](https://github.com/opencut-app/opencut) | 90,6k | 24-09-2026 | MIT | TS + Rust | NLE tipo CapCut con core Rust, **modo headless y MCP server (161 tools)**. No es compositor programático, pero sirve como destino de entrega/edición humana |

**Licencia Remotion** (verificado en [License FAQ](https://www.remotion.dev/docs/license/faq) y [pricing](https://www.remotion.dev/docs/license/pricing)): gratis para individuos y organizaciones de **≤3 personas** incluso con uso comercial; a partir de ahí Company License: Creators 25 $/asiento/mes, Automators 0,01 $/render con mínimo 100 $/mes, Enterprise desde 500 $/mes. En la [migración a 5.0](https://www.remotion.dev/docs/5-0-migration) la telemetría por `licenseKey` pasa a ser obligatoria para Automators. Consecuencia: para un proyecto personal Remotion es gratis; si el pipeline se usa en Semicrol (>3 personas) hay que pagar o usar HyperFrames.

**¿Cuál es mejor para composiciones escritas por un LLM?** Remotion sigue teniendo la mejor semántica para un modelo (React declarativo, `interpolate`/`spring`, `Sequence`, todo determinista por frame) y la mayor base de ejemplos en su corpus. HyperFrames tiene la ventaja de que "el vídeo es HTML" (el LLM ya domina HTML+CSS+GSAP), licencia Apache y skills con flujos completos. Recomendación: definir una **spec de escena en JSON propia** y tener dos adaptadores; empezar por HyperFrames por licencia y madurez de su skill de talking-head, y mantener Remotion como segundo backend.

Fuentes de comparación: [PkgPulse](https://www.pkgpulse.com/guides/remotion-vs-motion-canvas-vs-revideo-programmatic-video-2026), [RenderComp](https://rendercomp.com/blog/remotion-vs-revideo-comparison/), [HN sobre Motion Canvas](https://news.ycombinator.com/item?id=47191103), [Remotion updates 2026](https://autoae.online/blog/remotion-updates-2026).

---

## 2. Speech-to-text con timestamps por palabra

| Repo / servicio | ⭐ | Última act. | Licencia | Cómo obtiene los timestamps | Notas ES/EN |
|---|---|---|---|---|---|
| [m-bain/whisperX](https://github.com/m-bain/whisperX) | 24,2k | ago-2026 | BSD-2 | faster-whisper + **alineado forzado wav2vec2** (±50 ms vs ±500 ms de Whisper) + pyannote | Modelo de alineado ES por defecto `VOXPOPULI_ASR_BASE_10K_ES`; el alineado por caracteres **no alinea dígitos ni símbolos** → normalizar números a texto antes o interpolar; diarización requiere token HF |
| [SYSTRAN/faster-whisper](https://github.com/SYSTRAN/faster-whisper) | 25,5k | nov-2025 | MIT | `word_timestamps=True` por DTW sobre cross-attention | Rápido (CTranslate2); actividad frenada; precisión de palabra 100-400 ms. **Ya instalado en esta máquina** (pero sin libs CUDA: cublas64_12 ausente) |
| [ggml-org/whisper.cpp](https://github.com/ggml-org/whisper.cpp) | 53,9k | 24-09-2026 | MIT | Token timestamps + DTW opcional | Lo instala `@remotion/install-whisper-cpp`; el [hilo #2307](https://github.com/ggml-org/whisper.cpp/discussions/2307) documenta la fragilidad de los timestamps por token |
| [jianfch/stable-ts](https://github.com/jianfch/stable-ts) | 2,3k | may-2026 | MIT | Refina timestamps de Whisper; **alineado forzado de texto conocido** | Muy útil si ya tienes el **guion**: `align()` alinea texto exacto → sin errores de ASR |
| [linto-ai/whisper-timestamped](https://github.com/linto-ai/whisper-timestamped) | — | — | AGPL-3.0 | DTW cross-attention multilingüe | Ojo AGPL |
| [nyrahealth/CrisperWhisper](https://github.com/nyrahealth/CrisperWhisper) | 1,4k | 22-09-2026 | No comercial | Fine-tune para timestamps verbatim | Sobre todo EN/DE; licencia excluye uso corporativo |
| NVIDIA [Parakeet-TDT 0.6B v3](https://huggingface.co/nvidia/parakeet-tdt-0.6b-v3) / [Canary-1B v2](https://arxiv.org/html/2509.14128v2) | — | may-2026 | CC-BY-4.0 | Timestamps de palabra **nativos** | 25 lenguas europeas incl. español; muy rápido; WER algo peor con acentos/vocabulario técnico ([comparativa](https://amiralabs.com/blog/whisper-parakeet-canary-qwen3-asr-broadcast-model-selection)) |
| Deepgram Nova-3 | cloud | — | — | Word timestamps nativos, diarización | [Español soportado](https://deepgram.com/learn/deepgram-expands-nova-3-with-spanish-french-and-portuguese-support); ~0,0043 $/min batch |
| Azure AI Speech | cloud | — | — | `wordLevelTimestampsEnabled` | Batch da forma *display* y *lexical*; **tiempo real solo lexical** ([Q&A](https://learn.microsoft.com/en-us/answers/questions/2142206/does-real-time-azure-speech-to-text-support-provid)) |
| OpenAI | cloud | — | — | Solo **`whisper-1`** con `timestamp_granularities=word`; `gpt-4o-transcribe` **no da word timestamps** ([docs](https://developers.openai.com/api/docs/guides/speech-to-text)) | `@remotion/openai-whisper` convierte a `Caption` |

**Recomendación:** WhisperX (large-v3, alineado ES/EN) como default local en GPU; si el vídeo se graba a partir de un guion, **stable-ts `align()`** con el texto del guion elimina el problema de reconocimiento y deja solo el de tiempos. Fallback cloud: Deepgram Nova-3. Normalizar todo al tipo `Caption` de Remotion (`text/startMs/endMs/timestampMs/confidence`), que HyperFrames también consume vía su skill de captions.

---

## 3. Segmentación / matting del presentador ("texto detrás del speaker", técnica T3)

| Repo | ⭐ | Última act. | Licencia | Rendimiento / calidad |
|---|---|---|---|---|
| [PeterL1n/RobustVideoMatting](https://github.com/PeterL1n/RobustVideoMatting) | 9,5k | abr-2024 | **GPL-3.0** | Recurrente con memoria temporal, sin trimap: 1080p 104 fps / 4K 76 fps en 1080Ti; ONNX, TensorRT, CoreML, TF.js. Mejor pelo y consistencia temporal que MODNet ([paper](https://arxiv.org/pdf/2108.11515)). Mejor coste/beneficio para *talking head* con cámara fija |
| [pq-yang/MatAnyone](https://github.com/pq-yang/MatAnyone) (CVPR 2025) | 1,6k | mar-2026 | S-Lab (**no comercial**) | Propagación de memoria; máscara inicial de SAM/SAM2; calidad superior en bordes, más lento; hay [nodo ComfyUI](https://www.runcomfy.com/comfyui-nodes/TrentNodes/mat-anyone-matte) |
| [FudanCVL/SAM2Matting](https://github.com/FudanCVL/SAM2Matting) (ECCV 2026) | 136 | jun-2026 | "Other" | SAM2/SAM3 + cabezas de matting; SOTA en vídeo; muy nuevo |
| [facebookresearch/sam2](https://github.com/facebookresearch/sam2) | 19,9k | may-2026 | Apache-2.0 | Máscaras binarias con tracking, no alpha suave → bordes duros sin post-proceso |
| [ZhengPeng7/BiRefNet](https://github.com/ZhengPeng7/BiRefNet) | 4,2k | sep-2026 | MIT | Imagen a imagen: 17 fps a 1024² en 4090. En vídeo parpadea si no se suaviza temporalmente |
| [ZHKKKe/MODNet](https://github.com/ZHKKKe/MODNet) | 4,4k | may-2024 | Apache-2.0 | 67 fps 1080Ti; peor coherencia temporal |
| BackgroundMattingV2 | — | — | MIT | Requiere foto del fondo vacío → descartable |
| MediaPipe Selfie Segmentation | — | activo | Apache-2.0 | Máscara 256×256 en CPU; para preview, no para 1080p final |
| [danielgatis/rembg](https://github.com/danielgatis/rembg) | 24,9k | sep-2026 | MIT | Solo imágenes (backends u2net/BiRefNet); para las capturas/imágenes que "pop in" |

**Recomendación:** RVM vía ONNX Runtime CUDA/TensorRT produce un **vídeo alpha** (PNG sequence o ProRes 4444/WebM VP9 con alpha) en tiempo casi real en una RTX de consumo. Por ser GPL, ejecutarlo como **proceso externo** que emite ficheros, sin enlazar su código en el skill. El compositor apila: fondo (desenfocado/degradado) → texto/gráficos → capa alpha del presentador. MatAnyone solo para pases de calidad en el proyecto personal (licencia no comercial).

---

## 4. Gráficos animados dentro del compositor (técnicas T10a–f)

| Librería | ⭐ | Licencia | Encaje |
|---|---|---|---|
| D3 (layouts + SVG React) | — | ISC | **Primera opción**: calcular escalas/paths con D3 y renderizar `<path>/<rect>` cuyos valores dependen de `useCurrentFrame()` o de un timeline GSAP. Determinista |
| [recharts/recharts](https://github.com/recharts/recharts) | 27,6k | MIT | Rápido de escribir para un LLM, pero su animación es por reloj → **desactivar `isAnimationActive`** y alimentar los datos interpolados por frame |
| [apache/echarts](https://github.com/apache/echarts) | 67,4k | Apache-2.0 | Canvas y animación temporal; forzar determinismo es costoso |
| Chart.js / Plotly | — | MIT | Mismo problema de animación por reloj; Plotly demasiado pesado |
| [rough-stuff/rough-notation](https://github.com/rough-stuff/rough-notation) + Rough.js | 9,7k | MIT | Estilo "a mano" para subrayados/círculos; estable |
| [airbnb/lottie-web](https://github.com/airbnb/lottie-web) + `@remotion/lottie` | 32,1k | MIT | Remotion usa `goToAndStop()` → determinista ([doc](https://www.remotion.dev/docs/lottie/)); HyperFrames lo soporta nativamente |
| [rive-app/rive-wasm](https://github.com/rive-app/rive-wasm) | 968 | MIT | Runtime activo; iconos/mograph interactivos |

Guía: [RenderComp sobre bar charts/contadores en Remotion](https://rendercomp.com/blog/data-visualization-animations-remotion-bar-charts-counters/).

---

## 5. Captions y tipografía cinética (T2, T13, T15)

- **[@remotion/captions](https://www.remotion.dev/docs/captions/)**: tipo `Caption`, `parseSrt`/`serializeSrt`, [`createTikTokStyleCaptions`](https://www.remotion.dev/docs/captions/create-tiktok-style-captions) (agrupa en páginas con tokens `fromMs/toMs`). Formato pivote ideal.
- [remotion-dev/template-tiktok](https://github.com/remotion-dev/template-tiktok): instala whisper.cpp y genera captions palabra a palabra; cambiar `WHISPER_MODEL` a uno sin `.en` para español.
- `@remotion/install-whisper-cpp`, `@remotion/openai-whisper`, `@remotion/whisper-web` (experimental, WASM).
- HyperFrames: skill `/embedded-captions`.
- [unconv/captacity](https://github.com/unconv/captacity) (Python, MoviePy, resaltado de palabra actual) y [tmoroney/auto-subs](https://github.com/tmoroney/auto-subs): referencias, no adopción.
- Colecciones para agentes: [reactvideoeditor/remotion-templates](https://github.com/reactvideoeditor/remotion-templates) (81 componentes), [ali-abassi/remotion-templates](https://github.com/ali-abassi/remotion-templates).

---

## 6. Proyectos agénticos / LLM → vídeo

| Repo | ⭐ | Última act. | Licencia | Qué hace | Encaje |
|---|---|---|---|---|---|
| [calesthio/OpenMontage](https://github.com/calesthio/OpenMontage) | 61,1k | 06-09-2026 | **AGPL-3.0** | 12 pipelines (Talking Head, Screen Demo, Animated Explainer…), 100+ tools Python, 700+ ficheros de skill; render por Remotion, HyperFrames o FFmpeg; funciona sin API de pago (Piper TTS) | Referencia de arquitectura de skills y "quality gates"; AGPL impide embeberlo |
| [heygen-com/hyperframes](https://github.com/heygen-com/hyperframes) | 52,8k | hoy | Apache-2.0 | Ver §0 | Adoptar |
| [remotion-dev/skills](https://github.com/remotion-dev/skills) | 4,7k | hoy | — | 12 skills oficiales | Adoptar (backend Remotion) |
| [FireRedTeam/FireRed-OpenStoryline](https://github.com/FireRedTeam/FireRed-OpenStoryline) | 3,4k | jul-2026 | Apache-2.0 | Agente de edición por intención | Referencia de planning LLM |
| [nebrass/hve-video-director](https://github.com/nebrass/hve-video-director) | 105 | 22-09-2026 | MIT | Skill de Claude Code: 6 fases, capturas con Chrome DevTools, escenas HTML, ElevenLabs | Muy cercano en espíritu; pequeño |
| [itsNairr/Remotion-AI-Video-Editor](https://github.com/itsNairr/Remotion-AI-Video-Editor) | — | — | — | NLE Remotion + copiloto que muta el AST del timeline | Idea útil: el LLM edita una spec, no código |
| [harry0703/MoneyPrinterTurbo](https://github.com/harry0703/MoneyPrinterTurbo) | 125k | hoy | MIT | Shorts con stock footage + TTS | Otro género |
| [RayVentura/ShortGPT](https://github.com/RayVentura/ShortGPT) | 8k | feb-2025 | MIT | Parado | Descartar |
| Editores tipo Descript: [OpenCut](https://github.com/opencut-app/opencut) 90,6k MIT (headless + MCP), [Cap](https://github.com/CapSoftware/Cap) 22,7k AGPL/MIT mixto, [Screenity](https://github.com/alyssaxuu/screenity) 18,7k GPL-3 | | | | OpenCut como salida opcional para retoque humano |

---

## 7. Captura de pantalla scriptada (T8, T9, capturas de producto)

- **Playwright `recordVideo`**: WebM/VP8, **25 fps y bitrate fijado a 1 Mbit/s** en Chromium ([issue #31424](https://github.com/microsoft/playwright/issues/31424)) → inservible para máster. Alternativas: `page.screencast` (1.59), **capturas frame a frame** a 60 fps (enfoque de [demo-video-skill](https://github.com/surajshetty3416/demo-video-skill), MIT, Playwright+Pillow+ffmpeg), o CDP `Page.startScreencast`.
- [ashrafchowdury/programatic-demo](https://github.com/ashrafchowdury/programatic-demo) (MIT, sep-2026): Playwright registra un **click log JSON** (posición, tiempo, bounding rect) + WebM; Remotion sintetiza la cámara desde el log (clusters de clicks → keyframes: establecer ≥600 ms, lead-in, hold ≥1,3 s, trail out) con motion blur y cursor vectorial. Diseño a copiar.
- [ThePatriczek/playwright-recast](https://github.com/ThePatriczek/playwright-recast) (MIT): traces de Playwright → demo con TTS, subtítulos, zoom con easing. [mcpware/pagecast](https://github.com/mcpware/pagecast): grabación vía MCP.
- Apps de escritorio: [Recordly](https://github.com/webadderallorg/Recordly) 31,1k ⭐ **AGPL-3.0** (auto-zoom y cursor suavizado, sin headless); [OpenScreen](https://github.com/siddharthvaddem/openscreen) 40k MIT **archivado jun-2026** (fork [EtienneLescot](https://github.com/EtienneLescot/openscreen)); [ScreenArc](https://github.com/tamnguyenvan/screenarc) GPL-3; [Kap](https://github.com/wulkano/Kap) MIT parado; OBS para grabar al presentador.

## 8. Auto-zoom estilo Screen Studio

Recordly, OpenScreen ([PR #67](https://github.com/siddharthvaddem/openscreen/pull/67)), programatic-demo, [connerkward/screenstudio-alternative-skill](https://github.com/connerkward/screenstudio-alternative-skill) (MIT, Python headless), [imbhargav5/open-recorder](https://github.com/imbhargav5/open-recorder) (Swift), [FollowCursor](https://sabbour.me/2026/03/23/building-followcursor.html). **Conclusión:** como controlamos el navegador, no hace falta detectar el cursor por visión: el skill de captura emite el log de eventos y el compositor genera la cámara (patrón programatic-demo).

---

## 9. Pipeline "creator" moderno y su mapeo open source

| Paso del creador | Herramienta comercial típica | Pieza open source |
|---|---|---|
| Grabar presentador (4K, fondo liso) | Cámara + OBS/Ecamm | OBS |
| Grabar pantalla con zooms | Screen Studio | Playwright screenshots 60 fps + click log → cámara programática |
| Transcribir y cortar por texto | Descript | WhisperX / stable-ts; cortes con FFmpeg/Mediabunny |
| Recorte del presentador para texto detrás | After Effects Roto Brush / CapCut | RVM (alpha) → capa en compositor |
| Overlays, gráficos, callouts, kinetic text | After Effects + plantillas | HyperFrames (HTML+GSAP) o Remotion (React); D3/Recharts; Lottie |
| Captions animadas | Submagic/CapCut | `@remotion/captions` / `/embedded-captions` |
| Render y export | Premiere | FFmpeg (HyperFrames/Remotion lo envuelven) |
| Retoque humano final | Premiere/CapCut | OpenCut (headless/MCP) opcional |

---

## 10. Shortlist final (top 8) para adoptar

1. **[heygen-com/hyperframes](https://github.com/heygen-com/hyperframes)**: compositor por defecto (Apache-2.0, agent-native, `/talking-head-recut`, `/embedded-captions`).
2. **[remotion-dev/remotion](https://github.com/remotion-dev/remotion) + [remotion-dev/skills](https://github.com/remotion-dev/skills) + `@remotion/captions`**: segundo backend y formato `Caption` como pivote (licencia de empresa si >3 personas).
3. **[m-bain/whisperX](https://github.com/m-bain/whisperX)** (+ **[jianfch/stable-ts](https://github.com/jianfch/stable-ts)** `align()` cuando hay guion): transcripción y alineado ES/EN; fallback Parakeet-TDT v3 o Deepgram Nova-3.
4. **[PeterL1n/RobustVideoMatting](https://github.com/PeterL1n/RobustVideoMatting)** (ONNX/TensorRT, como subproceso por GPL): alpha del presentador; MatAnyone para calidad en uso personal.
5. **Playwright + patrón [programatic-demo](https://github.com/ashrafchowdury/programatic-demo)**: capturas 60 fps + click log → cámara con zoom/pan.
6. **D3 (+ Recharts sin animación) / GSAP**: gráficos deterministas por frame; **lottie-web** para mograph enlatado.
7. **FFmpeg + [Vanilagy/mediabunny](https://github.com/Vanilagy/mediabunny)**: cortes por transcript, mux de alpha, normalización de audio.
8. **[calesthio/OpenMontage](https://github.com/calesthio/OpenMontage)**: solo como referencia de arquitectura de skills/quality gates (AGPL: no embeber); **[OpenCut](https://github.com/opencut-app/opencut)** headless como salida opcional.

## 11. División propuesta en skills de Claude Code

| Skill | Entrada → Salida | Repos que envuelve | Técnicas del video que cubre |
|---|---|---|---|
| **`transcribe-and-align`** | vídeo/audio (+ guion opcional) → `captions.json` (formato `Caption`), `words.srt`, silencios y muletillas | WhisperX, stable-ts, FFmpeg; opción Deepgram/Parakeet | T2, T13, T15 (insumo) |
| **`storyboard-from-transcript`** | `captions.json` + brief → `storyboard.json` (escenas, beats, tipo de overlay, tiempos en ms, datos de cada gráfico) | Solo LLM + validación de esquema; checklist tipo OpenMontage | Reglas de ritmo (§5 del análisis) |
| **`speaker-cutout`** | vídeo del presentador → vídeo alpha (WebM VP9 alpha o PNG seq) + fondo desenfocado | RVM ONNX (subproceso), opcional MatAnyone; FFmpeg | T3, T11 |
| **`screen-capture`** | script de pasos Playwright → frames 60 fps + `events.json` + `camera.json` | Playwright, patrón programatic-demo, rembg | T8, T9 |
| **`chart-motion`** | spec de gráfico → componente React/HTML determinista | D3, Recharts (animación off), rough-notation, Lottie | T10a–f, T12 |
| **`compose-render`** | `storyboard.json` + assets → composición HyperFrames (o Remotion) → MP4 | HyperFrames CLI / Remotion `renderMedia`; `createTikTokStyleCaptions`; FFmpeg | T1, T4–T7, T14, montaje final |
| **`brand-kit`** (transversal) | tokens de marca consumidos por los anteriores | — | §3 del análisis |
| **`hand-off`** (opcional) | MP4 + spec → proyecto OpenCut | OpenCut headless/MCP | — |

**Caveats transversales:** GPL/AGPL en RVM, Recordly, OpenMontage, whisper-timestamped (procesos externos o solo referencia); licencia no comercial en MatAnyone y CrisperWhisper; Remotion exige Company License para equipos >3; HyperFrames tiene 6 meses (fijar versión); WhisperX no alinea dígitos (normalizar números a palabras antes de alinear); Playwright `recordVideo` no vale para el máster.
