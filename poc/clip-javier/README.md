# Primer clip propio → recut automático (2026-09-29)

Entrada: `C:\Users\ledes\OneDrive\Imágenes\Camera Roll\WIN_20260929_18_05_31_Pro.mp4` (webcam, 1080p60, 10 s, audio a −39 dB).

Pipeline ejecutado a mano, paso a paso, tal como lo harán las skills:

| Paso | Herramienta | Salida |
|---|---|---|
| Normalizar audio y pasar a 30 fps | ffmpeg (`loudnorm`, `fps=30`) | `clip.mp4`, `voice.wav` |
| Transcribir en español con tiempos por palabra | faster-whisper `medium` int8 (CPU, ~30 s) | `words.json`, `words.srt` (27 palabras) |
| Detectar gestos para colocar callouts | fotogramas en 7,3 s y 8,7 s (`_private/poc/clip-javier/gestos.png`, no versionado) | posiciones de "una cosa" (derecha) y "otra" (izquierda) |
| Máscara alfa solo en el tramo del texto detrás (4,3–6,8 s) | RobustVideoMatting ONNX CPU, ratio 0,25 (75 frames, 33 s) | `alpha_4.3.webm` |
| Storyboard + composición | HyperFrames `recut/index.html` | 8 overlays sincronizados con `words.json` |
| Render | `hyperframes render -q high --crf 18` (1 min 11 s) | `recut/out/javier_recut.mp4` |

Observaciones:
- El texto detrás del hablante funciona sobre material propio: pelo y cara limpios. La **mano en movimiento sale semitransparente** (desenfoque de movimiento a 60 fps con poca luz). Consejo de grabación: más luz y gestos algo más lentos en los tramos donde vaya a haber texto detrás.
- Los callouts se colocaron donde señala la mano leyendo dos fotogramas: es el candidato natural para automatizar con detección de pose (MediaPipe) en la skill de storyboard.
- Javier ocupa el tercio izquierdo del encuadre, así que todos los overlays fueron a la derecha. La skill debe detectar dónde está el hablante antes de decidir el layout.
- `check` marca como error el texto detrás (falso positivo conocido) y avisa de contraste bajo del cursor rosa sobre fondo claro.
- `words.json` se normalizó al formato del CLI (segundos) el 2026-09-30. El original del pipeline manual estaba en
  milisegundos (`startMs`/`endMs`, formato de HyperFrames), que `captions.load_words` sigue aceptando; con él `cut plan`
  reventaba con `KeyError` porque leía el JSON a pelo.
