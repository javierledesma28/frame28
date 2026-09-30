# Formato del storyboard (v1)

Un storyboard es un JSON que describe **qué aparece, cuándo y dónde** sobre el clip del hablante. Lo escribe el agente
(o una persona) y `frame28 build` lo convierte en una composición HyperFrames. Coordenadas en píxeles del lienzo
(`canvas`: 1920×1080 por defecto; 1080×1920 para vertical, 1080×1080 cuadrado); tiempos en segundos desde el inicio del clip.

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
- `canvas`: tamaño del lienzo. El clip se ajusta con *cover* (se recorta lo que sobre). Con lienzo estrecho (< 1400 px de
  ancho) el generador compacta gráficas, contadores y tarjetas (`.narrow`). `frame28 speaker` y `frame28 gestures` devuelven
  sus coordenadas en el lienzo que corresponde al formato del clip (o el que pases con `--canvas 1080x1920`).
- `captions`: subtítulos por frase (de `captions.json`). Se dibujan en caja negra centrada abajo (preset `phrase`).
- `caption_style` (opcional): subtítulos **por palabras** en vez de por frase. `{"preset": "pages" | "karaoke", "words":
  "words.json", "max_words": 4, "max_chars": 22, "size": 72, "bottom": 200, "uppercase": true}`. `pages` = grupos de 2–4
  palabras que van apareciendo al decirse (estilo TikTok/Shorts); `karaoke` = la página entera visible y la palabra actual
  en color de acento. `frame28 captions pages work/words.json` muestra el paginado antes de renderizar. Con `caption_style`
  el bloque `captions` se ignora.

## Tipos de overlay

Todos llevan `type`, `id` (único, sin espacios), `start`, `end` (segundos; el elemento existe solo en ese rango).
`at` es el instante de la animación de entrada (por defecto `start`). Los tiempos de palabras salen de `words.json`.

| type | Campos | Qué es (técnica del análisis) |
|---|---|---|
| `lower_third` | `x`, `y`, `title`, `subtitle?` | Tarjeta de identidad monoespaciada que se escribe carácter a carácter (T1). La caja mide lo que mide el texto (sin recortes con logos anchos o fuentes distintas). |
| `box` | `x`, `y`, `text`, `at?` | Frase corta en caja con esquinas de encuadre (T7). Aparece con pop. |
| `kinetic` | `x`, `y`, `size?` (124), `color?` (CSS; para fondos claros, pone sombra clara), `lines: [[{text, at, accent?}]]` | Tipografía cinética: cada palabra entra en su `at` (T2). Una lista por línea. `accent: true` la pinta con el color de acento. |
| `behind` | `text`, `at?`, `size?` (240), `matte`, `matte_start?`, `matte_end?` | Palabra gigante **detrás** del hablante (T3). `matte` es el WebM con alfa de `frame28 matte`; `matte_start/end` su rango en el clip (por defecto `start/end`). |
| `pointer` | `dot: [x,y]`, `box: [x,y]`, `text`, `at?` | Callout con punto, línea que crece y caja (T6). Ponlo donde el hablante señala; la línea se calcula sola. |
| `card` | `bg` (black/white/accent), `title: {text, at?, size?}`, `subtitle?: {text, at?, size?}` | Pizarra a pantalla completa con título (T5). Tapa al hablante. |
| `list_focus` | `bg?`, `label?` ("New"), `size?` (96), `items: [{text, at}]` | Lista donde el foco salta de ítem en ítem al decirse cada uno (T5). |
| `card_words` | `bg?`, `size?` (118), `lines: [[{text, at, accent?, initial?}]]` | Pizarra con frase palabra a palabra; `initial: true` colorea la inicial (T2/T5). |
| `image` | `src`, `x`, `y`, `w`, `at?` | Imagen o captura que entra con pop: UI, logo, foto (T8). |
| `chart` (kind `bar`) | `series: [{label, value, group?}]`, `hero?` (label ganador), `title?`, `subtitle?`, `unit?`, `decimals?`, `sort?` (asc/desc), `stagger?`, `bg?` o `panel?: {x,y,w,h?}` | Barras horizontales agrupadas que crecen una a una; la fila `hero` se destaca con caja al final (T10c). A pantalla completa (`bg`) o como panel flotante junto al hablante (`panel`). |
| `chart` (kind `counter`) | `value`, `prefix?`, `suffix?`, `decimals?`, `duration?` (s), `label?`, `subtitle?`, `bg?` o `panel?` | Cifra grande que cuenta desde 0 (T10f): "100×", "$42", "3 clientes". |
| `draw` | `x`, `y`, `w`, `h?`, `icon?` (check, circle-check, circle, arrow-right, arrow-up-right, arrow-down, zap, star, x, plus, heart, underline) o `paths?` (lista de `d`) o `src?` (SVG), `color?`, `stroke_width?`, `duration?`, `at?` | Icono o trazo que se dibuja solo (DrawSVG). Para marcar, subrayar o señalar con estilo "a mano". |
| `broll` | `src` (vídeo o imagen, relativo al storyboard), `pip?: {x,y,w,h}` (ventana; sin `pip` tapa todo el lienzo), `in?` (segundo del clip por el que empieza), `loop?`, `ken_burns?: {from, to, pan: left/right/up/down}`, `caption?`, `credit?`, `fade?`, `at?` | Plano de apoyo (stock o propio) mientras la voz sigue. A pantalla completa para ilustrar; en ventana para no perder al hablante. Los de stock salen de `frame28 broll search/fetch`, que guarda la licencia. |
| `brand_card` | `bg?` (black/accent/white), `logo?` (on_dark/on_light/on_accent/isotipo; por defecto según `bg`), `logo_width?`, `title?`, `subtitle?`, `endorsement?`, `at?` | Tarjeta de marca de apertura o cierre: logo, título, tagline y endorsement (por defecto los de la marca). |

## Revelado de texto (`reveal`)

`kinetic`, `behind`, `card.title` y `brand_card` aceptan `"reveal"`: `"fade"` (por defecto, sube y aparece),
`"rise"` (cada palabra sube desde detrás de una máscara, estilo *launch video*) o `"chars"` (las letras entran
escalonadas, SplitText de GSAP). Los tiempos siguen siendo los `at` de cada palabra.

## Marcas

`"brand": "think28"` usa la marca incluida (amarillo `#F5C500`, Inter, Space Mono, isotipo "28" en el rótulo).
`frame28 brand init mimarca --accent "#0D4F87" --logo logo.svg` crea `./brands/mimarca.json`; `frame28 brand from-site https://cliente.com --name cliente`
la propone a partir de la web (colores del CSS, fuente, logo con variantes para fondo oscuro y de acento); `frame28 brand list` las enumera.
El `lower_third` muestra el isotipo de la marca; las `card` con `bg: accent` usan su color; la `brand_card` usa logo, tagline y endorsement.

## Capas (z-index) que aplica el generador

1 fondo (clip) · 2 texto `behind` · 3 vídeo alfa del hablante · 4 overlays sobre el hablante · 5 pizarras · 9 subtítulos.

## Reglas de dirección (resumen; detalle en la skill `frame28-storyboard`)

- Un evento visual cada 2–4 s; nada de tramos de más de 8 s sin overlay.
- Cada overlay dice **una** cosa; máximo 3–4 palabras en cajas, 2 líneas en cinéticos.
- Overlays en el lado **libre** del encuadre (`frame28 speaker` lo devuelve); pizarras cuando el hablante no aporta.
- `behind` solo con fondo fijo, hablante centrado y sin gestos rápidos en ese tramo.
- Animaciones de 0,15–0,5 s; los tiempos de entrada son los de la palabra que los dispara.
