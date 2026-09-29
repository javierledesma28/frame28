---
name: frame28-director
description: 'Convierte un clip de una persona hablando a cámara en un video de presentación con rótulos, títulos cinéticos, texto detrás del hablante, callouts donde señala, pizarras y subtítulos sincronizados con la voz. Usar cuando el usuario entregue un video (o audio + video) y quiera "el video montado", "un explainer", "un launch video", "estilo founder video", o pida overlays/gráficas/subtítulos sincronizados. Orquesta las demás skills frame28-*.'
---

# Frame28 · Director

Eres el director de montaje. El usuario trae un clip; tú lo conviertes en un video terminado siguiendo este
flujo. Cada paso deja ficheros en un directorio de trabajo `work/` junto al clip; no repitas pasos ya hechos.

## 0. Entorno (una vez por máquina)

```bash
frame28 doctor
```
Si `frame28` no existe: `uv tool install --editable <plugin>/cli` (o `pip install -e <plugin>/cli`). Si falta
ffmpeg o Node, di exactamente qué instalar (el `doctor` lo imprime) y para.

## 1. Preparar y entender el material

```bash
frame28 prep <clip> -o work            # clip.mp4 (30 fps, sin audio), voice.wav (limpia y a −14 LUFS), audio16k.wav, probe.json
frame28 speaker work/clip.mp4          # side: left|center|right, free_side, bbox_1080p
frame28 sheet work/clip.mp4 -o work/sheet.png --every 1
```
Tras transcribir (paso 2), detecta los gestos de señalar y sus palabras:
```bash
frame28 gestures work/clip.mp4 --words work/words.json -o work/gestures.json --annotate work/gestos.png
```
`pointer_suggestions` trae los overlays `pointer` ya colocados (dot en la punta del dedo, box fuera de la cara,
`at` en la palabra "aquí/esto/este"). Usa los de `confidence: high` tal cual; los `low` solo si al mirar
`work/gestos.png` el gesto es realmente de señalar. `face_box_1080p` es la zona que ningún overlay debe tapar.
`prep` limpia la voz por defecto (graves fuera, reducción de ruido `afftdn`, sonoridad a −14 LUFS) y deja el
original en `voice_raw.wav`; el JSON de salida trae las medidas antes/después. Si el ruido es fuerte (ventilador,
calle) repite con `frame28 audio clean work/voice_raw.wav -o work/voice.wav --denoise rnnoise` y compara con
`frame28 audio compare work/voice_raw.wav work/voice.wav -o work/audio.png`. Para podcast o vertical, `--lufs -16`.

Mira `work/sheet.png` (Read) para conocer encuadre, luz, fondo y gestos. Anota: dónde está el hablante, qué lado
queda libre, si el fondo es fijo (necesario para `behind`), si hay gestos de señalar (candidatos a `pointer`).

## 2. Transcribir con tiempos por palabra → skill `frame28-transcribe`

```bash
frame28 transcribe work/audio16k.wav -o work --lang es      # words.json, captions.json, words.srt, transcript.json
```
Lee `work/transcript.txt` y `work/words.json`. Si el usuario tiene guion, pásalo con `--script guion.txt`.
Corrige en `words.json` los nombres propios mal reconocidos antes de seguir (el ASR falla justo en marcas y nombres).

## 2b. Jump cuts (opcional, recomendado en clips de más de 30 s)

```bash
frame28 cut plan work/words.json --audio work/voice.wav -o work/cuts.json
```
Propone quitar silencios de más de 0,6 s, muletillas ("eh", "mmm") y falsos arranques (misma frase repetida
tras una pausa). Lee la lista con el usuario si hay dudas: cada tramo lleva su motivo. Para aplicarlos:
```bash
frame28 cut apply work/clip.mp4 work/cuts.json --audio work/voice.wav --words work/words.json --captions work/captions.json -o work/cut
```
Deja en `work/cut/` el clip y la voz cortados (fundidos de 30 ms, sin clics) y `words.json`/`captions.json`
con los tiempos ya reajustados. **A partir de aquí trabaja sobre `work/cut/`** (speaker, gestures, matte,
storyboard). Si ya existía un storyboard, `--storyboard` lo remapea; si un corte cae dentro de un `behind`,
regenera su máscara sobre el clip cortado.

## 3. Decidir el storyboard → skill `frame28-storyboard`

Escribe `work/storyboard.json` siguiendo `frame28 storyboard schema` y las reglas de dirección de la skill
`frame28-storyboard`. Los `at` de cada palabra salen de `words.json`; las posiciones, del lado libre que devolvió
`frame28 speaker`; los callouts `pointer`, de `work/gestures.json`. Si un gesto no se detectó, mira el fotograma:

```bash
frame28 frames work/clip.mp4 -t 7.3 -o work/frames
```

Si el storyboard usa `behind`, genera la máscara **solo** para ese tramo → skill `frame28-cutout`:
```bash
frame28 matte work/clip.mp4 --start 4.3 --end 6.8 -o work/alpha_4.3.webm
```

Valida: `frame28 storyboard validate work/storyboard.json`.

## 4. Construir, comprobar y renderizar → skill `frame28-compose`

```bash
frame28 build work/storyboard.json -o work/project
frame28 check work/project
frame28 render work/project -o out/<nombre>.mp4
```
`check` separa errores reales, avisos de contraste y el falso positivo `text_occluded` (el texto detrás del hablante
siempre lo dispara; ignóralo). Corrige solo los errores reales y los contrastes que afecten a texto importante.

## 5. Revisar como un director

Mira la hoja de contacto `out/<nombre>_sheet.png`. Comprueba: (a) ningún overlay tapa la cara, (b) cada
overlay entra cuando se dice su palabra, (c) el texto detrás no se ve "delante", (d) subtítulos legibles, (e) ritmo:
nada de tramos de más de 8 s sin evento. Si algo falla, edita **el storyboard** (nunca el HTML generado) y
repite el paso 4. Entrega el MP4 y resume en dos líneas qué overlays lleva.

## Qué no hacer

- No editar `index.html` a mano: se regenera desde el storyboard.
- No usar `behind` con fondo en movimiento, hablante muy descentrado o gestos rápidos en ese tramo.
- No transcribir con `hyperframes transcribe` (exige whisper-cpp compilado); usa `frame28 transcribe`.
- No renderizar el clip original a 60 fps: `prep` lo pasa a 30 fps por algo (mitad de frames, mismo resultado).

## Referencia

- Catálogo de técnicas y por qué funcionan: `../frame28-storyboard/references/tecnicas.md`
- Guía de grabación para el usuario: `../frame28-storyboard/references/grabacion.md`
