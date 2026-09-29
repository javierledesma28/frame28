---
name: frame28-transcribe
description: 'Transcribe un clip o audio con tiempos por palabra (faster-whisper, español o inglés) y deja los cuatro ficheros que Frame28 y HyperFrames consumen (words.json, captions.json, words.srt, transcript.json). Usar cuando haga falta saber cuándo se dice cada palabra: subtítulos, tipografía cinética, sincronizar overlays, karaoke.'
---

# Frame28 · Transcribir y alinear

```bash
frame28 prep <clip> -o work                       # si aún no existe work/audio16k.wav
frame28 transcribe work/audio16k.wav -o work --lang es --model medium
```

Salidas en `work/`:

| Fichero | Formato | Para qué |
|---|---|---|
| `words.json` | `[{text, start, end, prob}]` en segundos | fuente de verdad de los `at` del storyboard |
| `captions.json` | `[{start, end, text}]` por frase | bloque `captions` del storyboard |
| `words.srt` | una palabra por cue, **LF** | importable en HyperFrames: `npx hyperframes transcribe words.srt --preserve-cues` |
| `transcript.json` | `[{text, start, end, id}]` | el formato nativo de HyperFrames |
| `transcript.txt` | texto plano | para leer el discurso de un vistazo |

## Reglas que aprendimos a golpes

- **Limpia y normaliza siempre el audio antes** (`prep` lo hace: graves, ruido y −14 LUFS): las capturas de webcam
  vienen a −40 dB y el VAD se come frases enteras. `frame28 audio measure` dice en qué estado está un fichero.
- **Revisa nombres propios y marcas** en `transcript.txt`: es donde falla el ASR ("ChatGBT", "GEV"). Corrige el
  `text` en `words.json`; los tiempos siguen valiendo. Si hay guion, `--script guion.txt` reduce los fallos.
- **Los tiempos de faster-whisper son aproximados** (100–400 ms): valen para overlays y subtítulos. Para karaoke
  palabra a palabra muy rápido, usa WhisperX o `stable-ts align` con el guion (pendiente de integrar).
- **Palabras con el mismo `start`** consecutivo son un artefacto: reparte el intervalo a partes iguales.
- Modelo: `medium` int8 en CPU ≈ 1,5× tiempo real. `small` si prima la velocidad; `large-v3` solo con GPU.
- Los dígitos ("42", "$") no se alinean bien: en el guion escríbelos en palabras.
