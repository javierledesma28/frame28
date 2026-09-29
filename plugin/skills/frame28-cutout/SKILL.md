---
name: frame28-cutout
description: 'Recorta al hablante del fondo (máscara alfa por fotograma con RobustVideoMatting) para poner texto o gráficas detrás de la persona, hacer PiP limpio o cambiar el fondo. Usar cuando el storyboard tenga overlays `behind` o el usuario pida "texto detrás de mí", "recortarme", "quitar el fondo", "efecto de que el título pasa por detrás".'
---

# Frame28 · Recorte del hablante

```bash
frame28 matte work/clip.mp4 --start 4.3 --end 6.8 -o work/alpha_4.3.webm
frame28 speaker work/clip.mp4        # bbox del hablante y lado libre (usa el mismo modelo, 6 fotogramas)
```

- Genera **solo el tramo** que lo necesita (`--start/--end` con 0,2 s de margen a cada lado): en CPU va a
  2–3,5 fps a 1080p, así que 3 s de tramo son ~30 s de cálculo; el clip entero de 60 s serían 10 min.
- Salida: WebM VP9 con canal alfa (`yuva420p`), que HyperFrames y Chrome reproducen con transparencia. Con
  `--keep-png dir` conserva la secuencia PNG RGBA por si hace falta retocar.
- El modelo (`rvm_mobilenetv3_fp32.onnx`, 15 MB, GPL-3.0) se descarga solo a `~/.cache/frame28/` y se ejecuta
  como proceso separado; no se enlaza su código.
- Con GPU NVIDIA: `uv pip install onnxruntime-gpu` en el entorno del CLI y `doctor` mostrará CUDA; el matting pasa a tiempo real.

## Qué sale bien y qué no

- Bien: pelo, barba, hombros, fondo fijo, hablante quieto o con gestos lentos.
- Mal: **manos en movimiento rápido** (salen semitransparentes por el desenfoque), fondo en movimiento, cambios
  de plano dentro del tramo, luz muy baja. Si el fotograma de control (`frame28 frames`) muestra halos, cambia el
  tramo o pide otra toma con más luz.
- Para verificar el alfa con ffmpeg hay que forzar el decodificador: `ffmpeg -c:v libvpx-vp9 -i alpha.webm ...`;
  el decodificador nativo descarta el canal alfa y parece que "no recortó".
