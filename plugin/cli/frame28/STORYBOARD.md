# Formato del storyboard (v1)

Un storyboard es un JSON que describe **qué aparece, cuándo y dónde** sobre el clip del hablante. Lo escribe el agente
(o una persona) y `frame28 build` lo convierte en una composición HyperFrames. Coordenadas en píxeles de un lienzo
1920×1080; tiempos en segundos desde el inicio del clip.

```json
{
  "version": 1,
  "meta": { "title": "Mi video", "lang": "es" },
  "canvas": { "width": 1920, "height": 1080, "fps": 30 },
  "source": { "video": "assets/clip.mp4", "audio": "assets/voice.wav", "duration": 10.0 },
  "brand": { "accent": "#EA77A1", "ink": "#111111", "paper": "#FFFFFC" },
  "speaker": { "side": "left" },
  "captions": [ { "start": 0.5, "end": 2.86, "text": "Bueno, bueno, bueno. Esta es una frase." } ],
  "overlays": [ ... ]
}
```

- `duration` (raíz, opcional): duración total si es mayor que la del clip, p. ej. para una `brand_card` de cierre sobre negro.
- `source.video`: clip a 30 fps **sin audio** (lo produce `frame28 prep`). `source.audio`: voz normalizada. Rutas relativas al storyboard.
- `brand`: opcional. Un objeto con `accent`, `ink`, `paper`, `grey`, `sans`, `mono`, `caption_font_size`, **o un nombre de marca incluida** (`"brand": "think28"`), o la ruta a tu propio `brand.json`.
- `captions`: subtítulos por frase (de `captions.json`). Se dibujan en caja negra centrada abajo.

## Tipos de overlay

Todos llevan `type`, `id` (único, sin espacios), `start`, `end` (segundos; el elemento existe solo en ese rango).
`at` es el instante de la animación de entrada (por defecto `start`). Los tiempos de palabras salen de `words.json`.

| type | Campos | Qué es (técnica del análisis) |
|---|---|---|
| `lower_third` | `x`, `y`, `title`, `subtitle?` | Tarjeta de identidad monoespaciada que se escribe carácter a carácter (T1). |
| `box` | `x`, `y`, `text`, `at?` | Frase corta en caja con esquinas de encuadre (T7). Aparece con pop. |
| `kinetic` | `x`, `y`, `size?` (124), `lines: [[{text, at, accent?}]]` | Tipografía cinética: cada palabra entra en su `at` (T2). Una lista por línea. `accent: true` la pinta con el color de acento. |
| `behind` | `text`, `at?`, `size?` (240), `matte`, `matte_start?`, `matte_end?` | Palabra gigante **detrás** del hablante (T3). `matte` es el WebM con alfa de `frame28 matte`; `matte_start/end` su rango en el clip (por defecto `start/end`). |
| `pointer` | `dot: [x,y]`, `box: [x,y]`, `text`, `at?` | Callout con punto, línea que crece y caja (T6). Ponlo donde el hablante señala; la línea se calcula sola. |
| `card` | `bg` (black/white/accent), `title: {text, at?, size?}`, `subtitle?: {text, at?, size?}` | Pizarra a pantalla completa con título (T5). Tapa al hablante. |
| `list_focus` | `bg?`, `label?` ("New"), `size?` (96), `items: [{text, at}]` | Lista donde el foco salta de ítem en ítem al decirse cada uno (T5). |
| `card_words` | `bg?`, `size?` (118), `lines: [[{text, at, accent?, initial?}]]` | Pizarra con frase palabra a palabra; `initial: true` colorea la inicial (T2/T5). |
| `image` | `src`, `x`, `y`, `w`, `at?` | Imagen o captura que entra con pop: UI, logo, foto (T8). |
| `brand_card` | `bg?` (black/accent/white), `logo?` (on_dark/on_light/on_accent/isotipo; por defecto según `bg`), `logo_width?`, `title?`, `subtitle?`, `endorsement?`, `at?` | Tarjeta de marca de apertura o cierre: logo, título, tagline y endorsement (por defecto los de la marca). |

## Marcas

`"brand": "think28"` usa la marca incluida (amarillo `#F5C500`, Inter, Space Mono, isotipo "28" en el rótulo).
`frame28 brand init mimarca --accent "#0D4F87" --logo logo.svg` crea `./brands/mimarca.json`; `frame28 brand list` las enumera.
El `lower_third` muestra el isotipo de la marca; las `card` con `bg: accent` usan su color; la `brand_card` usa logo, tagline y endorsement.

## Capas (z-index) que aplica el generador

1 fondo (clip) · 2 texto `behind` · 3 vídeo alfa del hablante · 4 overlays sobre el hablante · 5 pizarras · 9 subtítulos.

## Reglas de dirección (resumen; detalle en la skill `frame28-storyboard`)

- Un evento visual cada 2–4 s; nada de tramos de más de 8 s sin overlay.
- Cada overlay dice **una** cosa; máximo 3–4 palabras en cajas, 2 líneas en cinéticos.
- Overlays en el lado **libre** del encuadre (`frame28 speaker` lo devuelve); pizarras cuando el hablante no aporta.
- `behind` solo con fondo fijo, hablante centrado y sin gestos rápidos en ese tramo.
- Animaciones de 0,15–0,5 s; los tiempos de entrada son los de la palabra que los dispara.
