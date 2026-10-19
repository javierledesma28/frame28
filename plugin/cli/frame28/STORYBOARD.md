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
- `watermark` (raíz, opcional): marca de agua fija en **todos** los fotogramas, de 0 a la duración total (también sobre
  pizarras y tarjetas de cierre), por encima de todo. Un texto (`"watermark": "Frame28 Studio"`) o un objeto
  `{"text": "Frame28 Studio", "position": "br", "opacity": 0.9}`: `position` `br` (por defecto), `bl`, `tr` o `tl`; `opacity`
  de 0.3 a 1. Texto blanco en píldora oscura: se lee sobre fondo claro y oscuro. En vertical para redes (`tiktok`, `reels`,
  `shorts` o sin `platform`) las esquinas son las de la zona segura: `br` en el borde derecho justo encima de la columna de
  iconos, `tl`/`tr` bajo la franja superior, `bl` sobre la inferior. `build` avisa si un overlay o los subtítulos quedan
  debajo. Sin el campo no se pinta nada. Cuándo se pone lo decide el plan, no el storyboard: no la quites ni la tapes.
  Portadas: `frame28 cover --watermark "Frame28 Studio"`; shorts: `frame28 clips scaffold|batch --watermark "Frame28 Studio"`.
- `source.video`: clip a 30 fps **sin audio** (lo produce `frame28 prep`). `source.audio`: voz normalizada. Rutas relativas al storyboard.
- `brand`: opcional. Un objeto con `accent`, `ink`, `paper`, `grey`, `sans`, `mono`, `caption_font_size`, `on_accent` (color del texto sobre el acento en hook, cta, steps, tarjetas y etiquetas; si falta, se elige por contraste WCAG la tinta o el blanco, el que dé 4,5:1), **o un nombre de marca incluida** (`"brand": "think28"`), o la ruta a tu propio `brand.json`.
- `canvas`: tamaño del lienzo. El clip se ajusta con *cover* (se recorta lo que sobre). Con lienzo estrecho (< 1400 px de
  ancho) el generador compacta gráficas, contadores y tarjetas (`.narrow`). `frame28 speaker` y `frame28 gestures` devuelven
  sus coordenadas en el lienzo que corresponde al formato del clip (o el que pases con `--canvas 1080x1920`).
- `platform` (opcional): `tiktok`, `reels`, `shorts`, `youtube` o `pdp`. En vertical, `frame28 build` avisa de overlays que caen
  bajo la interfaz del móvil (columna derecha de iconos, franja inferior, franja superior) y de subtítulos demasiado bajos.
- `words` (opcional): ruta al `words.json` contra el que se resuelven las anclas a la voz (`"word:…"`, ver más abajo). Si
  falta, se usa `caption_style.words` y, si tampoco está, `words.json` junto al storyboard.
- `captions`: subtítulos por frase (de `captions.json`). Se dibujan en caja negra centrada abajo (preset `phrase`).
- `caption_style` (opcional): subtítulos **por palabras** en vez de por frase. `{"preset": "pages" | "karaoke", "words":
  "words.json", "max_words": 4, "max_chars": 22, "size": 72, "bottom": 200, "uppercase": true, "backdrop": "auto"}`.
  `backdrop`: `auto` (por defecto: mira el vídeo y, si la franja de los subtítulos es clara, los pone sobre caja), `box`
  (caja semitransparente), `stroke` (contorno negro) o `none` (solo sombra). `pages` = grupos de 2–4
  palabras que van apareciendo al decirse (estilo TikTok/Shorts); `karaoke` = la página entera visible y la palabra actual
  en color de acento. `frame28 captions pages work/words.json` muestra el paginado antes de renderizar. Con `caption_style`
  el bloque `captions` se ignora.

## Tipos de overlay

Todos llevan `type`, `id` (único, sin espacios), `start`, `end` (segundos; el elemento existe solo en ese rango).
`at` es el instante de la animación de entrada (por defecto `start`). Los tiempos de palabras salen de `words.json`.
`x`, `y` son siempre la **esquina superior izquierda** del elemento en el lienzo, no su centro (`box`, `kinetic`, `steps`,
`draw`, `image`, `lower_third`…): para centrar un rótulo de ancho `w`, `x = (ancho del lienzo - w) / 2`.

**Anclas a la voz.** En `start`, `end`, `at`, `matte_start` y `matte_end` (también en los `at` de líneas, ítems y títulos, en
`words_at` y en `kicker.at`) puedes escribir `"word:palabra"` en vez de segundos: `build` lo resuelve con el `words.json`
(sin mayúsculas, tildes ni puntuación). En `start`/`at` vale el inicio de la palabra menos 0,04 s (la letra ya está cuando
suena); en `end`, su final. Varias palabras seguidas (`"word:por aquí"`) entran con la primera y, en `end`, acaban con
la última. Si se dice más de una vez,
manda el tramo del overlay; si sigue siendo ambigua, `build` se para y pide `"word:aquí#2"` (la segunda vez que se dice).
Una palabra que no se dice nunca se convierte en un tiempo: el error lista las parecidas. Con `source.audio`, el inicio de
cada palabra se pega antes al arranque real de la voz: Whisper, tras una pausa, pone la palabra siguiente dentro del
silencio (entraría antes de decirse) o unas décimas tarde. `frame28 cut apply` deja las
anclas como están (se resuelven contra el `words.json` ya cortado) e `i18n apply` las fija en segundos antes de traducir.

| type | Campos | Qué es (técnica del análisis) |
|---|---|---|
| `lower_third` | `x`, `y`, `title`, `subtitle?` | Tarjeta de identidad monoespaciada que se escribe carácter a carácter (T1). La caja mide lo que mide el texto (sin recortes con logos anchos o fuentes distintas). |
| `box` | `x`, `y`, `text`, `at?` | Frase corta en caja con esquinas de encuadre (T7). Aparece con pop. |
| `kinetic` | `x`, `y`, `size?` (124), `color?` (CSS; para fondos claros, pone sombra clara), `lines: [[{text, at, accent?}]]` | Tipografía cinética: cada palabra entra en su `at` (T2). Una lista por línea. `accent: true` la pinta con el color de acento. |
| `behind` | `text`, `at?`, `size?` (240), `matte`, `matte_start?`, `matte_end?`; frase palabra a palabra: `words_at`, `kicker?`, `enter?`, `out?` (ver abajo) | Palabra gigante **detrás** del hablante (T3). `matte` es el WebM con alfa de `frame28 matte`; `matte_start/end` su rango en el clip (por defecto `start/end`). |
| `pointer` | `dot: [x,y]`, `box: [x,y]`, `text`, `at?` | Callout con punto, línea que crece y caja (T6). Ponlo donde el hablante señala; la línea se calcula sola. |
| `card` | `bg` (black/white/accent), `title: {text, at?, size?}`, `subtitle?: {text, at?, size?}` | Pizarra a pantalla completa con título (T5). Tapa al hablante. |
| `list_focus` | `bg?`, `label?` ("New"), `size?` (96), `items: [{text, at}]` | Lista donde el foco salta de ítem en ítem al decirse cada uno (T5). |
| `card_words` | `bg?`, `size?` (118), `lines: [[{text, at, accent?, initial?}]]` | Pizarra con frase palabra a palabra; `initial: true` colorea la inicial (T2/T5). |
| `image` | `src`, `x`, `y`, `w`, `at?` | Imagen o captura que entra con pop: UI, logo, foto (T8). |
| `chart` (kind `bar`) | `series: [{label, value, group?}]`, `hero?` (label ganador), `title?`, `subtitle?`, `unit?`, `decimals?`, `sort?` (asc/desc), `stagger?`, `bg?` o `panel?: {x,y,w,h?}` | Barras horizontales agrupadas que crecen una a una; la fila `hero` se destaca con caja al final (T10c). A pantalla completa (`bg`) o como panel flotante junto al hablante (`panel`). |
| `chart` (kind `counter`) | `value`, `prefix?`, `suffix?`, `decimals?`, `duration?` (s), `label?`, `subtitle?`, `bg?` o `panel?` | Cifra grande que cuenta desde 0 (T10f): "100×", "$42", "3 clientes". |
| `draw` | `x`, `y`, `w`, `h?`, `icon?` (check, circle-check, circle, arrow-right, arrow-up-right, arrow-down, zap, star, x, plus, heart, underline) o `paths?` (lista de `d`) o `src?` (SVG), `color?`, `stroke_width?`, `duration?`, `at?` | Icono o trazo que se dibuja solo (DrawSVG). Para marcar, subrayar o señalar con estilo "a mano". |
| `broll` | `src` (vídeo o imagen, relativo al storyboard), `pip?: {x,y,w,h}` (ventana; sin `pip` tapa todo el lienzo), `in?` (segundo del clip por el que empieza), `loop?`, `ken_burns?: {from, to, pan: left/right/up/down}`, `caption?`, `credit?`, `fade?`, `at?` | Plano de apoyo (stock o propio) mientras la voz sigue. A pantalla completa para ilustrar; en ventana para no perder al hablante. Los de stock salen de `frame28 broll search/fetch`, que guarda la licencia. |
| `hook` | `text` o `lines: [..]`, `bg?` (accent/black/white/none), `size?`, `x?`, `y?`, `w?`, `color?`, `at?` | Gancho de los primeros 1–3 s: líneas grandes con resaltado por línea, estilo Shorts. Va arriba, en zona segura. |
| `cta` | `title?`, `price?`, `old_price?`, `discount?`, `code?`, `code_label?`, `line?` ("Link in bio"), `url?` (genera QR; `qr: false` lo quita), `bg?`, `x?`, `y?`, `w?`, `at?` | Llamada a la acción: precio con anterior tachado, descuento, código de cupón y QR (segno, local). Por defecto una banda encima de los subtítulos. |
| `steps` | `items: [{label, at}]`, `total?`, `x?`, `y?`, `size?` | Píldora de progreso "2 / 3 · Trace with a marker" que cambia en cada `at`. Para tutoriales: el espectador sabe cuánto queda. |
| `before_after` | `before`/`after` (imágenes) o `before_t`/`after_t` (segundos del propio clip: el build extrae los fotogramas), `x?`, `y?`, `w?`, `h?`, `label_before?`, `label_after?`, `duration?`, `at?` | Antes/después con barrido de izquierda a derecha y etiquetas. El momento "sale bien". |
| `brand_card` | `bg?` (black/accent/white), `logo?` (on_dark/on_light/on_accent/isotipo; por defecto según `bg`), `logo_width?`, `title?`, `subtitle?`, `endorsement?`, `at?` | Tarjeta de marca de apertura o cierre: logo, título, tagline y endorsement (por defecto los de la marca). |

## Frase detrás del hablante (`behind` con `words_at`)

Con `words_at`, `kicker`, `enter` u `out`, el `behind` pasa a ser una **frase de 1 a 4 palabras** que entra palabra a
palabra cuando se dice y sale despacio, desenfocándose. Sin esos campos sigue siendo la palabra única de siempre.

```json
{ "type": "behind", "id": "bh", "start": 2.7, "end": 7.5, "text": "DISTINTOS|COMPONENTES", "words_at": "auto",
  "kicker": { "text": "Vamos a ver", "at": "word:vamos" }, "x": 0.72, "y": 0.28, "fit": 0.5, "color": "ink",
  "matte": "alpha.webm", "matte_start": 2.7, "matte_end": 7.6 }
```

- `text`: la frase; `|` parte líneas. `words_at`: `"auto"` (busca las palabras, en orden, en lo que se dice entre
  `start - 1` y `end`) o una lista con un tiempo o un ancla por palabra. Con una cifra o una palabra que no se dice tal
  cual («3», «IA»), `auto` se para y enseña lo que se oye: pon la lista a mano.
- `kicker`: antetítulo pequeño encima de la frase, un texto o `{text, at?, size?, tracking?, weight?, color?}`. Su `at`
  por defecto es medio segundo antes de la primera palabra; tamaño 3,2 % del alto, peso 400, espaciado 0,3 em.
- `x`, `y`: **centro** de la frase en fracción del lienzo (0–1; por defecto 0.5 y 0.28). `fit` (0.2–0.98, por defecto
  0.85): fracción del ancho que ocupa la línea más larga; el tamaño lo ajusta el navegador con la fuente real, con techo
  del 42 % del alto en una línea y del 30 % en varias. `size` en píxeles lo fija y desactiva el ajuste.
- `color`: `accent`, `ink`, `paper` o un color CSS (blanco por defecto). `weight` y `tracking` (por defecto los
  `display_weight`/`display_tracking` de la marca). `halo: false` quita la sombra difusa.
- `enter`: `fade_word` (por defecto), `rise` (sube desde detrás de una máscara) o `chars` (letras escalonadas). `out`:
  `blur` (por defecto) o `fade`; `out_dur` en segundos (por defecto el token `exit_ms` de la marca). La salida termina
  en `end`; el antetítulo empieza a irse `exit_stagger_ms` antes.
- `build` avisa si la frase completa queda quieta menos de `hold_min` (1,5 s) antes de salir, si la máscara del hablante
  no cubre lo que se ve (entrada del antetítulo y salida incluidas) y si hay dos `behind` a menos de 20 s.

## Revelado de texto (`reveal`)

`kinetic`, `behind`, `card.title` y `brand_card` aceptan `"reveal"`: `"fade"` (por defecto, sube y aparece),
`"rise"` (cada palabra sube desde detrás de una máscara, estilo *launch video*) o `"chars"` (las letras entran
escalonadas, SplitText de GSAP). Los tiempos siguen siendo los `at` de cada palabra.

## Marcas

`"brand": "think28"` usa la marca incluida (amarillo `#F5C500`, Inter, Space Mono, isotipo "28" en el rótulo).
`frame28 brand init mimarca --accent "#0D4F87" --logo logo.svg` crea `./brands/mimarca.json`; `frame28 brand from-site https://cliente.com --name cliente`
la propone a partir de la web (colores del CSS y del logo, fuente, logo con variantes para fondo oscuro y de acento); si no encuentra el acento
con certeza lo deja «a confirmar» con candidatos (`accent_pending`) y `build` se niega hasta `frame28 brand set cliente --accent "#RRGGBB"`,
que guarda lo que elija el usuario (también `--font`, `--ink`, `--tagline`); `frame28 brand list` las enumera.
El `lower_third` muestra el isotipo de la marca; las `card` con `bg: accent` usan su color; la `brand_card` usa logo, tagline y endorsement.

Tipografía y movimiento de la marca: `display_weight` (100–1000) y `display_tracking` (`-0.035em`, `2px`) para los
titulares; `motion` con los tokens de tiempo en milisegundos y las curvas de GSAP. Hoy los usa el `behind` con frase:

| token | por defecto | qué es |
|---|---|---|
| `enter_ms` | `standard_ms` o 200 | entrada de cada palabra (rápida: 100–400) |
| `exit_ms` | 1200 | salida lenta (700–1400 recomendado) |
| `exit_blur_px` | 28 | desenfoque al final de la salida |
| `ease_in` / `ease_out` | `power1.out` / `sine.inOut` | curvas de GSAP (`expo.out`, `back.out(1.7)`, `none`…) |
| `exit_stagger_ms` | 300 | adelanto de la salida del antetítulo |
| `kicker_ms` | `slow_ms` o 500 | entrada del antetítulo |
| `word_stagger_ms`, `char_stagger_ms` | 300, 20 | escalonado si no hay `words_at` / entre letras con `chars` |
| `style` | `editorial` | `sober`, `editorial` o `promotional`: los mismos estilos que la Memoria y la campaña (ritmo; lo lee el director). `promotional` entra más rápido (`fast_ms` o 120 ms) y sale más despacio (1400 ms) salvo que la marca fije `enter_ms`/`exit_ms` |
| `avoid` | — | efectos que la marca no quiere (`behind`, `cards_3d`, `camera`, `transitions`, `live_photos`, `brand_open`); `build` avisa si hay un `behind` |

`fast_ms`, `standard_ms` y `slow_ms` (los del brand kit) se aceptan como base. Un token desconocido, fuera de rango o una
curva que no es de GSAP paran el `build`.

## Nota de marca (antes del render)

`frame28 storyboard brandcheck <storyboard>` puntúa de 0 a 100 los textos en pantalla contra la marca y lista cada fallo
con su arreglo; sale con código 1 si hay errores o la nota no llega a `--min` (90). Reglas: `voice.avoid` y
`voice.max_words_per_sentence` del JSON de marca, el `brief.md` del montaje (lo busca junto al storyboard o más arriba:
«Nunca digas», reglas legales, ganchos prohibidos, glosario, lo que la campaña tiene que decir y lo que no) y, con
`--memoria`, la Memoria en JSON. Errores: claims legales, palabras prohibidas, ganchos prohibidos, acento sobre acento.
Avisos: glosario en el idioma de `meta.lang`, frases largas, cajas con demasiadas palabras, lo que la campaña pide y no
sale, contraste bajo y zonas seguras. De los subtítulos (la voz) solo avisa si dicen un claim legal. `storyboard
validate` enseña la nota en una línea.

## Capas (z-index) que aplica el generador

1 fondo (clip) · 2 texto `behind` · 3 vídeo alfa del hablante · 4 overlays sobre el hablante · 5 pizarras · 6 venta (hook,
cta, steps) · 9 subtítulos · 20 marca de agua (`watermark`).

## Reglas de dirección (resumen; detalle en la skill `frame28-storyboard`)

- Un evento visual cada 2–4 s; nada de tramos de más de 8 s sin overlay.
- Cada overlay dice **una** cosa; máximo 3–4 palabras en cajas, 2 líneas en cinéticos.
- Overlays en el lado **libre** del encuadre (`frame28 speaker` lo devuelve); pizarras cuando el hablante no aporta.
- `behind` solo con fondo fijo, hablante centrado y sin gestos rápidos en ese tramo. La frase, uno cada ~20 s como
  mucho, en el tercio superior, con la cabeza tapando 2 letras como mucho y en un color que contraste con la pared
  (sobre fondos claros, `ink`).
- Entradas rápidas (0,1–0,4 s) en la palabra que las dispara, con ancla a la voz; salidas lentas (0,7–1,4 s) con
  desenfoque o fundido.
