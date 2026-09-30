---
name: frame28-broll
description: 'Elige y coloca planos de apoyo (B-roll) en un video hablado: sugiere palabras clave por frase, busca vídeos o fotos de stock en Pexels y Pixabay con la licencia registrada, o usa material propio del usuario, y los escribe como overlays `broll` del storyboard de Frame28. Usar cuando el usuario pida "imágenes de apoyo", "B-roll", "planos recurso", "que se vea lo que digo", o cuando un tramo largo del clip no tenga nada visual que aportar.'
---

# Frame28 · B-roll

El B-roll es un plano que se ve **mientras la voz sigue**: ilustra lo que se dice cuando el hablante no aporta
(un tramo de 6–10 s explicando algo abstracto, un lugar, un objeto que no tiene a mano). Se usa con moderación: uno
o dos por minuto en un *founder video*; más, y deja de ser un video de la persona.

## Fuentes, en este orden

1. **Material propio del usuario**: capturas de su producto, fotos, clips de su móvil. Siempre mejor que el stock.
   Pregunta si tiene algo antes de buscar. Se usa tal cual como `src` (vídeo mp4/webm o imagen).
2. **Stock con licencia comercial y sin atribución obligatoria**: Pexels y Pixabay a través del CLI. Hace falta
   una clave gratuita por proveedor (`frame28 broll providers` dice cuáles hay y dónde ponerlas). Sin claves no
   se busca: díselo al usuario y sigue con material propio.

## Flujo

```bash
frame28 broll providers                                     # ¿hay claves?
frame28 broll suggest work/captions.json --lang es          # palabras clave por frase (punto de partida)
frame28 broll search "city traffic night" --kind video --orientation landscape --per-page 8 \
        -o work/broll/traffic.json --sheet work/broll/traffic.png
frame28 broll fetch work/broll/traffic.json pexels-123456 -o work/broll --in 2 --duration 5
```

- Las consultas van **en inglés y concretas** ("woman typing laptop close-up", no "trabajo"): es lo que indexan
  los bancos. Traduce tú las palabras clave de `suggest`.
- `--orientation` según el `canvas` del storyboard (`portrait` para vertical).
- Mira la hoja `--sheet` (Read) y elige por lo que se ve, no por el título: luz parecida a la del clip, sin texto
  incrustado, sin caras protagonistas que compitan con el hablante, movimiento suave.
- `fetch` descarga el original, deja un `<id>.json` con autor, página y licencia (obligatorio conservarlo con el
  proyecto) y, con `--in/--duration`, un `<id>_cut.mp4` sin audio a 30 fps listo para el overlay.

## Cómo se escribe en el storyboard

```json
{ "type": "broll", "id": "br1", "start": 41.3, "end": 46.5, "at": 41.34,
  "src": "broll/pexels-123456_cut.mp4", "ken_burns": { "from": 1.0, "to": 1.1, "pan": "left" },
  "caption": "90 minutos de edición", "credit": "Pexels · Nombre Autor" }
```

- Sin `pip` tapa todo el lienzo (capa 5, como una pizarra); con `pip: {x, y, w, h}` es una ventana junto al
  hablante (capa 4), en el lado libre y fuera de la cara.
- `in` recorta el punto de entrada del clip de stock si no se recortó al descargar; `loop` si es más corto que el tramo.
- `ken_burns` da vida a las fotos y suaviza los vídeos estáticos: escala de 1,0 a 1,08–1,15 y paneo opcional.
- `caption` rotula la idea en una frase corta (el subtítulo de la voz sigue debajo); `credit` es opcional en Pexels y
  Pixabay, pero queda bien y es honesto.
- Duración: 3–6 s a pantalla completa; hasta 10 s en ventana. Entra en la palabra que lo motiva (`at`) con fundido
  de 0,25 s. No pongas B-roll sobre un `behind`, un `pointer` ni una `card`.

## Qué no hacer

- No descargar de sitios sin licencia clara ni "de Google". Solo Pexels, Pixabay o material del usuario.
- No usar stock con logotipos, marcas o personas reconocibles como protagonistas.
- No tapar al hablante en los primeros 3 s ni en el cierre con marca.
