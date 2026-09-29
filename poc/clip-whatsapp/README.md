# Clip vertical de WhatsApp · "30% off" (demo Frame28)

Primer montaje **vertical (9:16)** con Frame28: clip de 11,5 s grabado con el móvil y enviado por WhatsApp
(464×832, 60 fps, voz en inglés), montado como anuncio de un descuento del 30 %.

Qué demuestra:
- `canvas` 1080×1920: el generador acepta cualquier lienzo; el clip se ajusta con `object-fit: cover`.
- Las coordenadas del storyboard se escriben en píxeles del lienzo vertical.
- Un `chart` `counter` a pantalla completa tapa el silencio de 2 s a mitad del clip (el `cut plan` no lo
  confirmó por el ruido de fondo, así que se cubre en vez de cortar).
- Marca *ad hoc* (naranja de la camiseta) pasada como objeto, sin logo: el `lower_third` cae al cursor y la
  `brand_card` va sin logo ni endorsement.

Ficheros: `storyboard.json`, `cuts.json` (vacío: sin cortes). `work/` y `out/` (medios, caras) no se versionan.
Pipeline: `prep` → `transcribe --lang en` → `speaker` → `gestures` (sin gestos de señalar: los `pointer` se
colocaron mirando `frames`) → `build` → `check` → `render` (1 min 19 s).
