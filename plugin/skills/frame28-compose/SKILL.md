---
name: frame28-compose
description: 'Construye la composición HyperFrames a partir de un storyboard JSON de Frame28, la valida y la renderiza a MP4 con hoja de contacto de revisión. Usar cuando exista un storyboard (o haya que ajustar uno) y se quiera el video final; también para re-renderizar tras cambiar textos, tiempos o posiciones.'
---

# Frame28 · Componer y renderizar

```bash
frame28 storyboard validate work/storyboard.json
frame28 build work/storyboard.json -o work/project     # index.html + assets copiados (regenerable)
frame28 check work/project                             # lint + runtime + layout + contraste de HyperFrames
frame28 render work/project -o out/video.mp4           # MP4 + out/video_sheet.png
```

## Cómo leer `check`

- `errors`: hay que arreglarlos (en el storyboard) antes de renderizar. Típico: asset que no existe.
- `contrast_warnings`: texto claro sobre fondo claro. Arreglos en el storyboard: cambiar a `card` sobre fondo,
  mover el overlay a una zona oscura, o usar `box` (lleva fondo semitransparente) en vez de `kinetic`.
- `known_false_positives`: `text_occluded` sobre un `behind` es esperado; ignóralo.

## Render

- 1080p a 30 fps, CRF 18, ~1 min por cada 10–20 s de video en un portátil con GPU. Usa `--quality draft` para
  iterar y `high` para entregar.
- El render usa Chrome headless (se descarga solo la primera vez) y ffmpeg (debe estar en PATH; el CLI lo añade).
- Siempre revisa `*_sheet.png` antes de entregar. Para ver un instante concreto: `frame28 frames out/video.mp4 -t 7.5 -o out/f`.

## Cuando algo se ve mal

| Síntoma | Causa | Arreglo |
|---|---|---|
| Overlay tapa la cara | posición en el lado del hablante | `frame28 speaker` → usa `free_side`; mueve `x` |
| Texto detrás se ve delante | máscara no cubre el rango | `matte_start/end` deben cubrir `start/end` del `behind` |
| Palabra entra tarde/pronto | `at` mal | copia `start` de esa palabra en `words.json` |
| Vídeo congelado en el render | (no debería) elemento de vídeo sin `id` | regenera con `build`; no edites el HTML |
| Sin audio | `source.audio` ausente | añade `voice.wav` al storyboard |

Para previsualizar con scrubbing y editar en vivo: `cd work/project && npx --yes hyperframes@0.8.72 preview --background`
(abre `http://127.0.0.1:3002`). Es para revisar; el render es la verdad (la previsualización a veces no respeta el
rango temporal de la capa alfa).
