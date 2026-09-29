# Roadmap de features y repos a integrar (investigación 2026-09-29)

Investigación hecha con búsqueda web verificando estrellas, actividad y licencia. Criterio: solo lo que puede correr
dentro del flujo de un plugin de Claude Code (skills que llaman a CLIs/Python/Node locales o APIs cloud opcionales),
bien mantenido y con licencia compatible (MIT/Apache/BSD/MPL; GPL solo como proceso externo; no comercial descartado).

## Resumen ejecutivo

- **El ecosistema se ha movido mucho en 2026.** HyperFrames ya tiene ~54k estrellas (Apache-2.0) y HeyGen publica skills oficiales que se solapan parcialmente con Frame28 (`talking-head-recut`, `hyperframes-media`, `embedded-captions`). `browser-use/video-use` (MIT, ~27k) hace edición por transcripción con Claude Code, y `OpenMontage` (AGPL, ~62k) es un "estudio agéntico" completo. Frame28 debe diferenciarse por lo que ya hace bien y ninguno hace: matting por fotograma, detección de señalamiento con pose, storyboard JSON tipado, español nativo y puertas de calidad.
- **Tres cambios de licencia que condicionan decisiones:** GSAP 3.13+ es 100 % gratis con todos los plugins (SplitText, MorphSVG, DrawSVG…); Piper TTS pasó a GPL-3; los pesos de CrisperWhisper, MusicGen, Stable Audio Open, F5-TTS, RMBG-2.0 y Qwen-Image-2.1 son **no comerciales**.
- **Las mayores ganancias con menor esfuerzo:** jump cuts por transcripción + normalización de loudness, B-roll por palabra clave (Pexels/Pixabay), demo de pantalla con zoom automático (Playwright 1.59 `page.screencast`), reencuadre 9:16 con el MediaPipe que ya tenemos, y exportación SRT/VTT/capítulos.

## 1. Captura de pantalla / UI para demos y limpieza de imágenes

- **Playwright `page.screencast` (v1.59, Apache-2.0)**: API de screencast con `showActions()`, `show_chapter()`, `show_overlay()` y captura de frames. Encaje: `frame28 screen record --script demo.yaml` que guarda el vídeo sin zoom y un `clicks.json`; el zoom-pan **no se hornea**: se convierte en keyframes de un overlay `screen` (cámara GSAP con `scale`/`transform-origin`). Fuentes: [release 1.59](https://newreleases.io/project/npm/playwright/release/1.59.0), [class Screencast](https://playwright.dev/java/docs/api/class-screencast).
- **paldom/screenshooter** (MIT, recién publicado): recorder Playwright con cursor bezier, ripples, spotlight, máscaras de privacidad, zoom. Referencia de diseño de YAML, no dependencia: [repo](https://github.com/paldom/screenshooter).
- **Recordly** (AGPL-3.0, ~32k, Electron): auto-zoom por cursor, sin CLI ni headless; solo como app externa para escritorio: [repo](https://github.com/webadderallorg/Recordly).
- Escritorio en Windows: `ffmpeg -f gdigrab/ddagrab` + `pynput` (LGPL, proceso externo) al mismo `clicks.json`.
- **rembg** (MIT, ~22.8k) con `birefnet-general` (BiRefNet MIT) para recortar product shots → overlay `image`. Evitar Bria RMBG-2.0 (CC-BY-NC).

## 2. B-roll, stock e imágenes generadas

| Fuente | Contenido | Licencia |
|---|---|---|
| Pexels | fotos + vídeo | Pexels License (comercial, sin atribución) |
| Pixabay | fotos, vídeo, música y SFX | Pixabay Content License |
| Unsplash | solo fotos | Unsplash License (app de producción con aprobación) |

Encaje: `frame28 broll suggest` lee la transcripción, extrae 1–3 palabras clave por beat y consulta Pexels/Pixabay; el agente elige entre miniaturas y escribe un overlay `broll` con `src`, `in/out`, `fit`, `ken-burns`, guardando URL y licencia. MoneyPrinterTurbo (MIT, ~112k) tiene ese flujo.

Imágenes generadas: local en 8 GB VRAM solo FLUX.1 [schnell] (Apache) cuantizado o SDXL; FLUX.2 klein 4B (Apache) pide ~13 GB; Qwen-Image-2.1 pasó a no comercial. Cloud: OpenAI Images (salida propia, comercial), Stability (Community License < 1 M$, exige "Powered by"). Encaje: `frame28 asset gen --provider openai|stability|comfy`.

## 3. Audio

- **Jump cuts:** auto-editor (Unlicense) corta silencios; las muletillas hay que hacerlas sobre `words.json` (huecos > N ms, lista de muletillas en español, repeticiones en < 800 ms). CrisperWhisper las transcribe pero sus pesos son no comerciales. Copiar de `video-use` (MIT): fundidos de 30 ms en cada corte y verificación de bordes. Encaje: `frame28 cut plan` → `cuts.json`.
- **Loudness y ruido:** ffmpeg `loudnorm` 2 pasadas / ffmpeg-normalize (MIT), pyloudnorm (MIT) para medir; DeepFilterNet (MIT/Apache, CPU en Windows), RNNoise (BSD-3) vía `arnndn`. Encaje: `frame28 audio clean --denoise deepfilter --lufs -14`.
- **TTS / doblaje:** Kokoro-82M (Apache, 3 voces ES; espeak-ng GPL como proceso externo), Chatterbox Multilingual (MIT, clonación de voz, 23 idiomas), ElevenLabs (cloud). Piper ahora GPL-3; F5-TTS no comercial. Encaje: `frame28 tts` y `frame28 dub --lang en`.
- **Música y SFX:** ACE-Step (Apache) generativa local; Pixabay Music/SFX y Freesound (filtro CC0); librosa (ISC) para beats. MusicGen, Stable Audio Open, Essentia y Jamendo gratuito descartados por licencia. Encaje: `frame28 music add --duck`, `beats.json`.

## 4. Elementos cinematográficos dentro de HyperFrames

Regla: cada elemento debe ser función pura del tiempo (`seek(t)`), sin rAF libre ni aleatoriedad sin semilla.

- **GSAP 3.13+ gratis con plugins**: SplitText (máscaras por línea), DrawSVG (iconos que se dibujan), MorphSVG, ScrambleText, MotionPath. Esfuerzo S, valor alto. [GSAP 3.13](https://gsap.com/blog/3-13/).
- **Lottie:** usar `@lottiefiles/dotlottie-web` (MIT, activo) con `setFrame()`; `lottie-web` casi parado. Emoji animados: Noto Animated Emoji (CC-BY-4.0, atribución).
- **Rough.js** (MIT, ~20.6k) con `seed` + DrawSVG → overlay `annotate` (círculo, subrayado, flecha) que reutiliza la detección de señalar.
- **Fondos shader:** `@paper-design/shaders` (MIT, WebGL2, uniform de tiempo por el adapter).
- **Three.js** (MIT) con reloj manual; **tsParticles** solo con semilla y pre-bake; **Lucide** (ISC) animado con DrawSVG.

## 5. Gráficas y datos deterministas

| Librería | Licencia | Determinismo en `seek` | Uso |
|---|---|---|---|
| D3 | ISC | total (SVG estático + GSAP anima atributos) | base |
| Observable Plot | ISC | SVG estático | prototipado |
| Apache ECharts | Apache-2.0 | `animation:false` + `setOption(data(t))` | Sankey, treemap, mapas |
| Chart.js | MIT | `animation:false` + `update('none')` | sencillo, canvas |
| Vega-Lite | BSD-3 | SVG estático (pesado) | spec JSON |

Encaje: ampliar `chart` con `line`, `area`, `donut`, `stat-tiles`, `table-reveal`, `map`; `Intl.NumberFormat('es-ES')`. Revisar antes el `data-chart` del catálogo de HyperFrames.

## 6. Inteligencia de edición

- **Beats:** sentence-transformers (Apache) `paraphrase-multilingual-MiniLM-L12-v2` en CPU + corte por caída de similitud.
- **Palabras clave:** KeyBERT (MIT) + spaCy `es_core_news_md` (MIT); Claude decide, el modelo local prefiltra.
- **Retakes:** frases con similitud > 0.9 en 60 s → quedarse con la última.
- **Cambios de plano:** PySceneDetect (BSD-3).
- **Diarización:** pyannote.audio 3.1 (MIT, token HF) o WhisperX (BSD-2) → `speaker` en `words.json`.
- **Reencuadre 9:16:** MediaPipe Face Detection (Apache, ya en el stack) + suavizado → `object-position` en composición vertical. Evitar Autocrop-vertical (YOLOv8 AGPL).
- **Subtítulos TikTok:** `@remotion/captions` es MIT y funciona sin Remotion (`createTikTokStyleCaptions`) → presets `karaoke`, `pages`, `2-words-upper`.
- **Traducción:** Argos Translate (MIT, offline), DeepL API Free (500k car./mes) o Claude.

## 7. Entrega

Vertical/cuadrado con el mismo storyboard y safe zones; miniaturas con `hyperframes snapshot`; capítulos `00:00 Título` desde beats; SRT/VTT con pysubs2 (MIT); YouTube Data API v3 (apps no verificadas solo suben en privado, ~6 vídeos/día); GIF con ffmpeg `palettegen`.

## 8. Puertas de calidad

`hyperframes check --snapshots` + `snapshot --at` en los puntos medios de cada overlay; regresión visual con pixelmatch (ISC); LUFS/true-peak con pyloudnorm; subtítulos: CPS ≤ 17, ≤ 42 caracteres por línea, 1–7 s, sin solapes, contraste ≥ 4.5:1 sobre el fotograma real, safe zone; ningún texto tapando la cara (usar la máscara del matting) salvo `behind`; cortes con margen ≥ 80 ms de la palabra.

## 9. Proyectos de los que tomar ideas

| Proyecto | Estrellas / licencia | Qué tomar | Qué evitar |
|---|---|---|---|
| [browser-use/video-use](https://github.com/browser-use/video-use) | ~27.6k / MIT | edición transcript-first, silencios+muletillas, fades 30 ms, subtítulos 2 palabras, `project.md` persistente, autoevaluación | depende de ElevenLabs Scribe |
| [OpenMontage](https://github.com/calesthio/OpenMontage) | ~61.9k / AGPL-3 | pipeline research→proposal→script→scene_plan→assets→edit→compose; proveedores plugables | no copiar código |
| HeyGen hyperframes skills (`talking-head-recut`, `hyperframes-media`) | Apache-2.0 | competidor directo; reutilizar su catálogo | duplicar lo que ya trae |
| [OpenCut](https://github.com/OpenCut-app/OpenCut) | ~48.7k / MIT | rewrite Rust con Editor API/MCP anunciados | no integrar aún |
| [MoneyPrinterTurbo](https://github.com/harry0703/MoneyPrinterTurbo) | ~112k / MIT | flujo keyword → stock → TTS → subtítulos | calidad "content farm" |
| AutoCut (mli) | ~7.4k | UX: marcar frases en Markdown y cortar el vídeo | — |
| [auto-editor](https://github.com/wyattblue/auto-editor) | ~4.2k / Unlicense | exportar EDL/Premiere/Resolve | — |
| [Claude-Code-Video-Toolkit](https://github.com/wilwaldon/Claude-Code-Video-Toolkit) | — | perfiles de marca, ciclo multi-sesión | centrado en Remotion |

## Roadmap priorizado

| # | Feature | Valor | Esfuerzo | Repo(s) / API | Licencia | Riesgo |
|---|---|---|---|---|---|---|
| 1 | Jump cuts por transcripción (silencios, muletillas ES, retakes) + fades 30 ms + verificación de bordes | Muy alto | M | propio sobre `words.json`; ideas de video-use, auto-editor | MIT / Unlicense | falsos positivos; Whisper omite disfluencias |
| 2 | Audio clean + loudness (DeepFilterNet, loudnorm 2 pasadas, pyloudnorm) | Alto | S | DeepFilterNet, ffmpeg-normalize, pyloudnorm | MIT/Apache | bajo |
| 3 | GSAP 3.13+ plugins (SplitText, DrawSVG, MorphSVG, ScrambleText) + Rough.js `annotate` | Alto | S–M | gsap, roughjs | gratis comercial, MIT | determinismo en seek |
| 4 | B-roll por palabra clave (Pexels/Pixabay) + overlay `broll` + Ken Burns + licencia registrada | Alto | M | Pexels, Pixabay, KeyBERT/spaCy | Pexels/Pixabay License, MIT | rate limits, relevancia |
| 5 | Captions estilo TikTok/karaoke + SRT/VTT con reglas de legibilidad | Alto | S | @remotion/captions, pysubs2 | MIT | bajo |
| 6 | Demo de pantalla con zoom-pan (Playwright screencast + clicks.json → overlay `screen`; escritorio con ffmpeg + pynput) | Alto | M–L | Playwright, ffmpeg, pynput | Apache, LGPL ext., MIT | sincronía click↔frame |
| 7 | Reencuadre 9:16/1:1 con MediaPipe + safe zones + composición vertical | Alto | M | MediaPipe, ffmpeg | Apache | saltos al suavizar |
| 8 | Capítulos + miniaturas + descripción (beats por embeddings, snapshot) | Medio-alto | S–M | sentence-transformers, hyperframes snapshot | Apache | bajo |
| 9 | Gráficas ampliadas (line/area/donut/stat-tiles/table-reveal) con D3 + ECharts | Medio-alto | M | d3, echarts | ISC, Apache | determinismo canvas |
| 10 | Lottie/emoji/shaders (dotlottie-web, Noto Animated Emoji, paper-design/shaders) | Medio | S–M | dotlottie-web, noto-emoji, @paper-design/shaders | MIT, CC-BY-4.0, MIT | atribución |
| 11 | Puertas de calidad (pixelmatch, LUFS, CPS/contraste/safe-zone, solape con máscara) | Medio-alto | M | pixelmatch, pyloudnorm, hyperframes check | ISC, MIT, Apache | umbrales ruidosos |
| 12 | Música y SFX (Pixabay/Freesound CC0, ducking, beats con librosa) | Medio | S–M | Pixabay, Freesound, librosa | Content License, CC0, ISC | Jamendo/MusicGen no aptos |
| 13 | Diarización para entrevistas → rótulos por hablante | Medio | M | whisperX, pyannote | BSD-2, MIT | token HF, CPU lento |
| 14 | TTS narración (Kokoro ES) y doblaje con clon de voz (Chatterbox) + traducción | Medio; alto para versión EN | M–L | kokoro, chatterbox-multilingual, argos-translate | Apache (espeak-ng GPL ext.), MIT | calidad voces ES; realinear overlays |
| 15 | Imágenes generadas (OpenAI/Stability; ComfyUI FLUX.1-schnell opcional) | Medio | S cloud / L local | OpenAI API, Stability, ComfyUI | propia / Community / Apache | 8 GB VRAM |
| 16 | Publicación YouTube (privado hasta verificar app) + GIF preview | Bajo-medio | S | google-api-python-client | Apache | apps no verificadas |
| 17 | Música generativa local (ACE-Step) | Bajo | M | ACE-Step | Apache | VRAM |
| 18 | Three.js / Rive | Bajo | M | three, rive-wasm | MIT | Rive editor SaaS |

**Descartados por licencia:** CrisperWhisper (pesos), MusicGen, Stable Audio Open, F5-TTS, Bria RMBG-2.0, Qwen-Image-2.1, Essentia, Ultralytics/YOLOv8 (AGPL), Recordly y OpenMontage/OpenChatCut (AGPL; solo ideas), Piper (GPL-3; proceso externo), Jamendo gratuito, Remotion core (licencia de empresa; `@remotion/captions` sí es MIT).

**Posicionamiento:** como HeyGen ya cubre "Whisper → overlays HTML → render", Frame28 se enuncia como *director de montaje en español con recorte del hablante, detección de gestos, B-roll y demo de pantalla, cortes por transcripción y puertas de calidad, todo local en Windows/macOS*, reutilizando el catálogo y el CLI de HyperFrames en lugar de reimplementarlos.
