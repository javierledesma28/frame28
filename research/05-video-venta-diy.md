# Vídeo que vende productos "hazlo tú mismo" · qué funciona y qué debe hacer Frame28 (investigación 2026-09-30)

Caso de referencia: **Cliente A** (kits de grabado y marroquinería; Engraver Pro™ a 69,99 $; 650 000 clientes; DTC
por Shopify; venta apoyada en TikTok, creadores y YouTube). Su promesa en todos los productos es la misma:
*cualquiera puede hacerlo con sus manos, hoy, y queda bien a la primera*. El vídeo tiene que demostrarlo.

## 1. Qué publica Cliente A y qué le funciona (YouTube, 10 700 suscriptores)

Vídeos largos (3–4 min), ordenados por visualizaciones:

| Vídeo | Duración | Vistas |
|---|---|---|
| Tutorial de vidrio (Easy DIY) | 3:17 | 17 000 |
| Bienvenida de Cliente A! | 0:35 | 5 000 |
| Tutorial de acrilico (Step-By-Step) | 2:40 | 3 800 |
| Tutorial de piel · Engraving Basics | 3:56 | 3 500 |
| What Exactly Is Engraving? Discover Your New Favorite Hobby | 1:46 | 547 |
| Which Stone Is Best for Engraving? | 3:44 | 453 |
| Upgrade These 5 Anniversary Gifts With Only ONE TOOL | 3:52 | 161 |
| 3 Leather Birthday Gifts That Look WAY More Expensive… | 3:38 | 160 |
| Live workshops (30–36 min) | — | 250–400 |

Shorts, los más vistos:

| Short | Vistas |
|---|---|
| Transformacion 1 | 73 000 |
| Riesgo 1 (Big Mistake?) | 35 000 |
| I Tried Engraving This huevo gigante and This Is What Happened | 25 000 |
| Engraving Pen Art That Actually Protects Your Stuff | 22 000 |
| This is how you can get an award NO ONE else has | 18 000 |
| This DIY Bottle Glow-Up Keeps Getting Better · Clay, an Engraving Pen and My Keys… | 8 600 |
| From Chaos to Aesthetic Mug Transformation | 7 000 |
| This DIY Leather Wallet Changed My Mind · This One Tool Saved Everything | 6 000 |
| Historia personal 1 | 5 100 |

Lo que se lee en los números:

1. **El tutorial por material gana de calle** (vidrio, acrílico, piel, piedra): 10× las vistas de las listas de
   regalos. El título promete facilidad y exclusividad: "The ONLY tutorial you need", "Easiest way", "without
   ruining it", "step-by-step". Es el formato que reduce la duda "¿sabré hacerlo?".
2. **Los shorts multiplican por 5–10 el alcance del largo** y los que funcionan tienen un gancho de
   transformación o de riesgo: *trash → worth keeping*, *chaos → aesthetic*, *with ZERO practice (big mistake?)*,
   *priceless or worthless: you decide*, *this hobby fixed my screen time problem*. Persona, primera persona,
   resultado visible.
3. **El vídeo de bienvenida de 35 s** ("First time here?") es el segundo más visto: corto, orientado a "empieza hoy".
4. Las ideas de regalo por ocasión (Día de la Madre, 4 de julio) rinden poco en YouTube: son contenido de
   calendario, no de conversión.
5. Los directos de 30 minutos existen para la comunidad, no para vender.

## 2. Qué dice la práctica del sector (fuentes al final)

- **Estructura que convierte** (respuesta directa): gancho → problema → solución/demostración → valor → prueba
  social → llamada a la acción. El gancho va en los primeros 3 s; el *hook rate* mediano es 28 % en Meta y 33 % en
  TikTok, los mejores 45–55 %; por debajo de 25 %, el arranque está mal. El *hold rate* a 15 s sano es 15–25 %.
- **Tipos de gancho** con ejemplos medidos: curiosidad, negativo (dolor), prueba social, antes/después,
  beneficio, urgencia, dato, precio, texto manuscrito, lista de tres pasos.
- **Más del 70 % del vídeo social se ve sin sonido**: el texto en pantalla y los subtítulos no son adorno, son el
  mensaje.
- **Formatos UGC que más convierten en tienda**: reseñas y testimonios, unboxing, tutoriales paso a paso,
  antes/después, problema/solución. Vídeo en ficha de producto: hasta 80 % más conversión; tutoriales: +17 % de
  ingreso por cliente; integrar UGC: ~30 % de mejora de conversión.
- **Fatiga**: un anuncio que gasta se agota en 7–14 días. Hace falta **volumen de variantes** (mismo cuerpo,
  ganchos distintos), no una pieza perfecta.
- Para marcas DIY/manualidades: tutoriales y demos en ficha de producto (conversión), descubrimiento de producto en
  portada, testimonios y unboxing para confianza, vídeos transaccionales tras la compra.

## 3. Traducción a la promesa de Cliente A

El vídeo que vende un Engraver Pro tiene que hacer sentir tres cosas, en este orden:

| Sensación | Cómo se enseña | Overlay de Frame28 |
|---|---|---|
| "Esto es para mí" (gancho) | 3 s con transformación, riesgo o dolor: *De basura a…*, *sin práctica*, *¿lo estropearé?* | `hook` (texto grande, zona segura, 1–3 s) |
| "Yo puedo" (demostración) | pasos numerados, material corto, velocidad y broca dichas, primer plano de manos | `steps` (progreso 1/3), `box`, `pointer`, `list_focus` |
| "Sale bien" (resultado) | antes/después, "That's it!", el objeto terminado en manos | `before_after`, `draw` check, `kinetic` |
| "Otros lo hicieron" (prueba) | 650K makers, 4,7★, reseña en texto | `counter`, `card` |
| "Ahora" (acción) | precio con descuento, código, "link in bio", QR, garantía 60 días | `cta` (precio + código + QR) |

## 4. Qué debe hacer Frame28 para una empresa así (prioridad por impacto/esfuerzo)

| # | Mejora | Por qué | Esfuerzo |
|---|---|---|---|
| 1 | **Overlays de venta**: `hook`, `cta` (precio, código, QR, "link in bio"), `steps` (progreso), `before_after` (dos instantes del mismo vídeo con barrido) | Son los cuatro momentos de la estructura que convierte y hoy se improvisan con `box`/`kinetic` | S–M |
| 2 | **Fábrica de shorts**: de un tutorial largo, N clips verticales de 15–45 s con gancho, subtítulos por palabras y cierre de CTA; variantes de gancho para rotar cada 7–14 días | Es donde está el alcance (shorts 5–10× el largo) y la cura de la fatiga de creativos | M |
| 3 | **Zonas seguras de plataforma** (TikTok/Reels/Shorts: iconos a la derecha, descripción abajo, barra superior): el generador avisa y la skill coloca | El 70 % se ve sin sonido y en el móvil; un texto bajo los iconos no existe | S |
| 4 | **Biblioteca de ganchos** en la skill de storyboard: los 10 tipos con plantillas en ES/EN y las frases del propio Cliente A que funcionaron | Que el agente escriba ganchos que ya han demostrado tirar | S |
| 5 | **Portada/miniatura** a partir de un fotograma + título + marca (YouTube 1280×720, Shorts vertical) | La miniatura decide el clic; hoy no la hacemos | M |
| 6 | **Versión en otro idioma** del mismo montaje: subtítulos y textos traducidos por el agente, mismos tiempos | Venden en varios mercados; el coste marginal es casi cero | S (flujo) |
| 7 | **Cuadrado 1:1 para ficha de producto** con el mismo storyboard (ya soportado por `canvas`) | El vídeo en PDP es el que más convierte | S (docs) |
| 8 | **Marcadores de resultado**: detectar en la transcripción las frases de resultado ("that's it", "turned out", "look at this") y proponer ahí el `before_after` y el check | Automatiza el momento "sale bien" | S |

Pendiente que no depende de Frame28: testimonios reales (necesitan clientes grabando), unboxing (material propio).

## Fuentes

- Canal de YouTube de Cliente A (listado con yt-dlp, 2026-09-30): vídeos y shorts con duración y vistas.
- Segwise, "Best DTC Ad Creative Hooks for 2026: Types, Examples, and Benchmarks": https://segwise.ai/blog/dtc-ad-creative-hooks
- Motion, "Best DTC Meta ad hooks 2025" y "How to write UGC ad scripts": https://motionapp.com/blog/best-dtc-meta-ad-hooks-2025 · https://motionapp.com/blog/how-to-write-ugc-ad-scripts
- Videowise, "8 Types of UGC Videos to Scale Ecommerce Revenue and CVR": https://videowise.com/live-commerce/8-types-of-ugc-videos-to-scale-ecommerce-revenue-and-cvr
- Vidjet, "Best video types for brands in DIY, Art & Crafts, and Electronics": https://www.vidjet.com/video-shopping-examples-for-diy-and-electronics-brands
- Ecommerce Fastlane, "5 UGC Hooks for Ecommerce Video Ads": https://ecommercefastlane.com/ugc-hooks-for-ecommerce/
- Creative Bloq, sobre el Engraver Pro en TikTok: https://www.creativebloq.com/creative-inspiration/this-tiktok-famous-engraving-pen-turns-wooden-spoons-into-tiny-artworks
