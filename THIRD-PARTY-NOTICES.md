# Avisos de terceros · Frame28

Frame28 (el CLI `frame28` y el plugin de Claude Code de este repositorio) es MIT, © 2026 Think28. Usa estas piezas de
terceros. Ninguna se copia dentro de este repositorio: las dependencias de Python las instala `uv` desde PyPI, las de
render las descarga `npx` al usarlas y los modelos se descargan a `~/.cache/frame28/` la primera vez que hacen falta,
desde su origen y con la suma SHA-256 comprobada.

Las licencias se han revisado en el origen de cada pieza; lo marcado «a confirmar» está pendiente de una revisión legal.

## Dependencias de Python (`plugin/cli/pyproject.toml`)

| Paquete | Para qué | Licencia |
|---|---|---|
| click | línea de órdenes | BSD-3-Clause |
| numpy | cálculo numérico | BSD-3-Clause |
| opencv-python-headless | lectura de vídeo e imagen | Apache-2.0 (OpenCV); el wheel incluye FFmpeg, LGPL-2.1 |
| onnxruntime | ejecuta los modelos ONNX (RVM, OCR) | MIT |
| faster-whisper (y CTranslate2) | transcripción con tiempos por palabra | MIT |
| av (PyAV) | audio para faster-whisper | BSD-3-Clause; el wheel incluye FFmpeg, LGPL-2.1 |
| mediapipe | pose y gestos | Apache-2.0 |
| rapidocr | texto presente en el vídeo (PaddleOCR en ONNX, modelos dentro del wheel) | Apache-2.0 |
| segno | códigos QR | BSD-3-Clause |
| nvidia-cublas-cu12, nvidia-cudnn-cu12 (extra `gpu`, opcional) | transcripción en GPU NVIDIA | licencia de NVIDIA para sus librerías redistribuibles |

## Modelos que se descargan al usarse

| Modelo | Orden que lo usa | Origen | Licencia |
|---|---|---|---|
| RobustVideoMatting `rvm_mobilenetv3_fp32.onnx` | `frame28 matte` | github.com/PeterL1n/RobustVideoMatting | **GPL-3.0** |
| MediaPipe Pose Landmarker lite | `frame28 gestures`, `speaker`, `reframe` | storage.googleapis.com/mediapipe-models | Apache-2.0 |
| RNNoise (`sh.rnnn`, de GregorR/rnnoise-models) | `frame28 audio clean --denoise rnnoise` | github.com/GregorR/rnnoise-models | BSD-3-Clause (la de RNNoise; a confirmar en ese repositorio) |
| Whisper (versión CTranslate2 de Systran) | `frame28 transcribe` | huggingface.co/Systran | MIT |

**Sobre RobustVideoMatting (GPL-3.0).** El modelo se descarga del repositorio original en el momento de usarlo y
`onnxruntime` lo carga **dentro del propio proceso del CLI** (no en un proceso aparte). Frame28 no incluye ni
redistribuye los pesos ni el código de RVM; el CLI solo ejecuta el fichero ONNX que el usuario descarga. Si se
distribuyera el modelo junto a Frame28 (por ejemplo, en un instalador sin conexión), aplicaría la GPL-3.0 a esa
distribución. Revisión legal pendiente.

## Render (se descarga al usarse)

| Pieza | Para qué | Licencia |
|---|---|---|
| HyperFrames (`npx hyperframes@0.8.105`) | compositor HTML → vídeo | Apache-2.0 |
| GSAP y sus plugins (SplitText, DrawSVG), desde jsdelivr | animación de los overlays | «Standard No Charge License» de GSAP/Webflow: gratis, también para uso comercial, con la excepción de herramientas que compitan con Webflow. **A confirmar** con un abogado que un producto como Frame28 no cae en esa excepción |
| Chrome headless (lo gestiona HyperFrames) | captura de los fotogramas | BSD-3-Clause (Chromium) |

## Programas que instala el usuario (no se distribuyen con Frame28)

| Programa | Licencia |
|---|---|
| FFmpeg | LGPL-2.1 o GPL según la compilación (la de winget, Gyan, es GPL) |
| Node.js | MIT |
| uv | Apache-2.0 o MIT |
| Git | GPL-2.0 |
| yt-dlp (vía `uvx`, solo en `frame28 fetch`) | Unlicense |

## Fuentes de la marca Think28 incluida

Inter y Space Mono, desde Google Fonts: SIL Open Font License 1.1.
