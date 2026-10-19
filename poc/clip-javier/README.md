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

## Frase detrás del hablante palabra a palabra (F28-339, 2026-10-19)

`storyboard-behind2.json`: «DISTINTOS|COMPONENTES» con antetítulo «Vamos a ver», anclados a la voz (`words_at: "auto"`,
`"at": "word:vamos"`) y salida de 1,2 s por desenfoque. Máscara solo del tramo 2,7–7,6 s (`frame28 matte`, 147 fotogramas,
CPU). Render con 10 trabajadores y NVENC: 84 s.

- Cada palabra aparece como mucho un fotograma antes de oírse: «distintos» suena en 4,26 s (fotograma 127,8) y es visible
  desde el 127; «componentes», en 4,58 s (137,4), desde el 137.
- Primera prueba en ámbar sobre la pared: `check` marcó contraste 2,3:1. Segunda, en tinta sobre la estantería: la tinta
  se funde con los libros y la «V» del antetítulo desaparece contra las antenas del router (la máscara estaba limpia: era
  color sobre color, no un fallo del alfa). La buena va en tinta sobre la pared lisa de encima de la cabeza. La regla
  pasó al método: pared lisa, contraste con el fondo y la cabeza tapando como mucho 2 letras.
- El antetítulo al 2,5 % del alto y peso 300 no se leía sobre vídeo: el valor por defecto pasó al 3,2 % y peso 400.
