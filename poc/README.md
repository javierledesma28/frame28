# PoC: las mismas tres escenas en HyperFrames y en Remotion

Resultados y decisión en [`../research/03-poc-compositores.md`](../research/03-poc-compositores.md).

## Estructura

| Ruta | Qué es |
|---|---|
| `assets/` | Material común: `speaker_a.mp4` (clip frontal), `speaker_a_alpha.webm` (máscara alfa VP9), `alpha_png/` (misma máscara como PNG), `voice_c.wav` (voz normalizada), `words_c.json` (tiempos por palabra), `ref_c.mp4` (referencia) |
| `tools/rvm_matte.py` | Matting con RobustVideoMatting ONNX → PNG RGBA. Modelo `rvm_mobilenetv3_fp32.onnx` (descargar de los releases de PeterL1n/RobustVideoMatting, no está en el repo) |
| `hyperframes/` | Proyecto HyperFrames: todo en `index.html` (HTML + CSS + GSAP) |
| `remotion/` | Proyecto Remotion: `src/Poc.tsx` (3 escenas), `src/PocPng.tsx` (variante con secuencia PNG), `src/theme.ts` (tokens y datos) |
| `out/` | `poc_remotion.mp4`, `poc_hyperframes.mp4`, `comparativa_remotion_vs_hyperframes.png` |

## Reproducir

```bash
# Máscara alfa (CPU, ~25 s para 84 frames)
python tools/rvm_matte.py assets/speaker_a.mp4 assets/alpha_png tools/rvm_mobilenetv3_fp32.onnx 0.4
ffmpeg -framerate 30 -i assets/alpha_png/f_%04d.png -c:v libvpx-vp9 -pix_fmt yuva420p -b:v 0 -crf 20 -auto-alt-ref 0 assets/speaker_a_alpha.webm
```

```bash
# HyperFrames
cd hyperframes && npx --yes hyperframes@0.8.72 check && npx --yes hyperframes@0.8.72 render -o out/poc_hyperframes.mp4 -q high --crf 18
```

```bash
# Remotion
cd remotion && npm install && npx remotion render src/index.ts poc out/poc_remotion.mp4 --crf 18
```

## Gotchas verificados

- **Remotion**: declarar `zIndex` explícito en cada capa dentro de `AbsoluteFill`; sin él, la capa del hablante quedó debajo del texto en parte de los frames.
- **HyperFrames**: todo `<video>`/`<audio>` con `data-start` necesita `id`, o el render lo congela/silencia. El comprobador de layout marca el texto detrás del hablante como error (falso positivo).
- **Ambos**: `z-index: -1` en un hijo lo manda detrás del fondo de la escena; usar `isolation: isolate` en el contenedor.
