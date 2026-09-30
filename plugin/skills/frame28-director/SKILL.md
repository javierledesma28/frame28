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

Si el material es un enlace (YouTube, Vimeo…): `frame28 fetch <url> -o input.mp4` lo descarga a 1080p con yt-dlp
(sin instalar nada: usa `uvx` si hace falta) y deja `input.source.json` con título y origen.

**Si el vídeo es de una marca o vende algo** (tutorial de producto, anuncio, lanzamiento): antes de decidir nada,
investiga la marca en su web y escribe `work/brief.md` (qué venden, promesas literales, precio, prueba social,
colores); `frame28 brand from-site <url> --name <marca>` propone la marca con logo. El montaje debe reforzar el
argumento de venta, no decorar. Guía completa: `../frame28-storyboard/references/marca-y-promocional.md`.

**Vídeo ya producido** (voz en off, manos, gráficos propios, cortes de plano): se monta igual, pero sáltate
`speaker`, `gestures` y `behind`, y localiza lo que ya hay en pantalla:
```bash
frame28 graphics work/clip.mp4 -o work/graphics.json --annotate work/graphics.png   # OCR en CPU, ~1 s por segundo de vídeo
```
Devuelve los textos en pantalla con su caja y su tramo (marca de agua, rótulos del editor, subtítulos quemados,
texto impreso en objetos), las tarjetas a pantalla completa (color plano: tarjeta final, transiciones) y la
ocupación de una rejilla 3×3 con ventanas libres por zona. Mira `graphics.png` y coloca tus overlays en zonas y
momentos libres; en el paso 4 usa `frame28 build --graphics work/graphics.json` para que avise de colisiones.
Si `burned_subtitles` es true, no pongas `captions`. Sobre fondos claros usa `kinetic` con `color` oscuro.

```bash
frame28 prep <clip> -o work            # clip.mp4 (30 fps, sin audio), voice.wav (limpia y a −14 LUFS), audio16k.wav, probe.json
frame28 speaker work/clip.mp4          # side: left|center|right, free_side, bbox_canvas (píxeles del lienzo)
frame28 sheet work/clip.mp4 -o work/sheet.png --every 1
```
Tras transcribir (paso 2), detecta los gestos de señalar y sus palabras:
```bash
frame28 gestures work/clip.mp4 --words work/words.json -o work/gestures.json --annotate work/gestos.png
```
`pointer_suggestions` trae los overlays `pointer` ya colocados (dot en la punta del dedo, box fuera de la cara,
`at` en la palabra "aquí/esto/este"). Usa los de `confidence: high` tal cual; los `low` solo si al mirar
`work/gestos.png` el gesto es realmente de señalar. `face_box` es la zona que ningún overlay debe tapar.
**Lienzo**: `speaker` y `gestures` devuelven coordenadas en el lienzo que toca por formato (clip apaisado →
1920×1080, vertical → 1080×1920, cuadrado → 1080×1080; `canvas` en la salida). Si quieres otro, `--canvas 1080x1920`
en ambos y el mismo `canvas` en el storyboard. Un clip vertical de móvil se monta en vertical: no lo apaises.
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
Propone quitar silencios de más de 0,6 s (también los que Whisper esconde *dentro* de una palabra estirada),
muletillas ("eh", "mmm"; y "bueno", "pues", "o sea"… solo si les sigue una pausa) y falsos arranques (misma frase
repetida tras una pausa). Lee la lista con el usuario si hay dudas: cada tramo lleva su motivo. Para aplicarlos:
```bash
frame28 cut apply work/clip.mp4 work/cuts.json --audio work/voice.wav --words work/words.json --captions work/captions.json -o work/cut
```
Deja en `work/cut/` el clip y la voz cortados (fundidos de 30 ms, sin clics) y `words.json`/`captions.json`
con los tiempos ya reajustados. Si el plan sale vacío por ruido de fondo y aun así hay un silencio largo, tápalo
con una `card` o un `counter` a pantalla completa en el storyboard. **A partir de aquí trabaja sobre `work/cut/`** (speaker, gestures, matte,
storyboard). Si ya existía un storyboard, `--storyboard` lo remapea; si un corte cae dentro de un `behind`,
regenera su máscara sobre el clip cortado.

## 2c. Vertical (Reels, Shorts, TikTok) desde un clip apaisado

Si el destino es vertical y el clip es 16:9, reencuadra **después de los cortes** y antes de speaker/gestures/matte:
```bash
frame28 reframe work/cut/clip.mp4 -o work/cut/vertical.mp4 --path work/cut/reframe.json          # sigue al hablante
frame28 reframe work/cut/clip.mp4 -o work/cut/vertical.mp4 --mode blur                            # 16:9 entero sobre fondo desenfocado
```
`crop` recorta una ventana 9:16 de altura completa que sigue la cara (MediaPipe) con zona muerta y suavizado, como
un operador de cámara: los gestos hacia los lados se pierden (mira `moving_samples` y la hoja de contacto).
`blur` conserva todo el encuadre y deja dos franjas libres (`free_bands`) para overlays y subtítulos. A partir de
aquí todo (speaker, gestures, matte, storyboard con `canvas` 1080×1920, `caption_style` `pages`) va sobre el clip
vertical. Un clip que ya es vertical no necesita este paso.

## 2d. Shorts a partir del vídeo largo → skill `frame28-shorts`

Si el usuario quiere clips para redes además del vídeo entero (o en vez de él): `frame28 clips plan` propone los
tramos con más momentos de venta y tres ganchos por tramo; `clips cut` + `reframe` + `clips scaffold` dejan cada
short montado de partida (gancho, subtítulos por palabras, CTA). Detalle en la skill `frame28-shorts`.

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

Si un tramo de más de 6 s no tiene nada visual que aportar (el hablante explica algo abstracto, un lugar, un
proceso), pon un plano de apoyo → skill `frame28-broll`: material propio del usuario o stock de Pexels/Pixabay con
licencia registrada (`frame28 broll suggest/search/fetch`), escrito como overlay `broll` (pantalla completa o `pip`).
Uno o dos por minuto como mucho.

Valida: `frame28 storyboard validate work/storyboard.json`.

## 4. Construir, comprobar y renderizar → skill `frame28-compose`

```bash
frame28 build work/storyboard.json -o work/project
frame28 check work/project
frame28 render work/project -o out/<nombre>.mp4
```
`check` separa errores reales, avisos de contraste y el falso positivo `text_occluded` (el texto detrás del hablante
siempre lo dispara; ignóralo). Corrige solo los errores reales y los contrastes que afecten a texto importante.

Si el video va a una plataforma con subtítulos propios (YouTube, LinkedIn), exporta además el fichero:
```bash
frame28 captions export work/words.json -o out/<nombre>.srt     # o .vtt; ≤ 42 caracteres/línea, 1–7 s, avisa si > 17 cps
```

## 5. Revisar como un director

Mira la hoja de contacto `out/<nombre>_sheet.png`. Comprueba: (a) ningún overlay tapa la cara, (b) cada
overlay entra cuando se dice su palabra, (c) el texto detrás no se ve "delante", (d) subtítulos legibles, (e) ritmo:
nada de tramos de más de 8 s sin evento. Si algo falla, edita **el storyboard** (nunca el HTML generado) y
repite el paso 4. Entrega el MP4 y resume en dos líneas qué overlays lleva.

## 6. Portada y miniatura

Cada vídeo entregado lleva su portada: la miniatura decide el clic. Un fotograma del propio vídeo (el resultado,
el producto en manos, la cara con expresión) más un título de dos líneas con resaltado, insignia y logo:
```bash
frame28 cover out/video.mp4 --at 103.0 -o out/cover-yt.png --title "Engrave GLASS|the easy way" \
        --subtitle "No cracks. No slipping." --badge TUTORIAL --brand <marca> --ring 1180,560,300 --focus 0.62,0.5 --zoom 1.1
frame28 cover out/short.mp4 --at 1.0 -o out/cover-short.png --title "Frame28.|Graba, habla y listo." --size 1080x1920 --brand <marca>
```
`--size` 1280x720 (YouTube), 1080x1920 (Shorts/Reels/TikTok: título en el tercio superior), 1080x1080 (ficha de
producto: título abajo). `--ring x,y,r` dibuja un aro de acento sobre el producto; `--focus` y `--zoom` centran el
recorte del fondo. Reglas: 3–6 palabras por título, nada de frases enteras; el título repite el gancho del vídeo,
no el nombre de la marca (el logo ya está); mira el PNG antes de entregar, el texto no debe tapar el objeto.

## 7. Otro idioma → skill `frame28-i18n`

Con el vídeo aprobado, la segunda lengua cuesta minutos: `frame28 i18n extract` saca los textos, los traduces con
criterio de subtitulado, `frame28 i18n apply --lang xx` los devuelve al storyboard con los mismos tiempos (y
regenera los subtítulos por palabras sobre el ritmo original), y se vuelve a construir y renderizar.

## Qué no hacer

- No editar `index.html` a mano: se regenera desde el storyboard.
- No usar `behind` con fondo en movimiento, hablante muy descentrado o gestos rápidos en ese tramo.
- No transcribir con `hyperframes transcribe` (exige whisper-cpp compilado); usa `frame28 transcribe`.
- No renderizar el clip original a 60 fps: `prep` lo pasa a 30 fps por algo (mitad de frames, mismo resultado).

## Referencia

- Catálogo de técnicas y por qué funcionan: `../frame28-storyboard/references/tecnicas.md`
- Guía de grabación para el usuario: `../frame28-storyboard/references/grabacion.md`
