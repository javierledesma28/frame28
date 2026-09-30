# Vídeo que vende productos "hazlo tú mismo" · qué funciona y qué debe hacer Frame28 (investigación 2026-09-30)

Caso de referencia: **Cliente A** (nombre en clave; marca DTC de kits de manualidades; tienda propia; venta apoyada en
TikTok, creadores y YouTube). Su promesa en todos los productos es la misma: *cualquiera puede hacerlo con sus manos,
hoy, y queda bien a la primera*. El vídeo tiene que demostrarlo. El detalle de su canal (títulos, duraciones y vistas)
está en `_private/`: con él se encuentra la marca en una búsqueda.

## 1. Qué publica el Cliente A y qué le funciona (YouTube, canal pequeño)

Vídeos largos, por formato y por vistas relativas:

| Formato | Duración típica | Vistas, frente al tutorial más visto |
|---|---|---|
| Tutorial paso a paso de un proyecto, con un título que promete facilidad | 2:30–4:00 | 1× (los tres o cuatro primeros del canal) |
| Bienvenida para quien llega al canal: empieza hoy | < 1 min | ~0,3× |
| Qué es el hobby / qué elegir para empezar | 1:30–4:00 | ~0,03× |
| Ideas de regalo por ocasión (aniversario, cumpleaños) | 3:30–4:00 | ~0,01× |
| Directos y talleres | 30–36 min | ~0,02× |

Shorts, los más vistos, por patrón de gancho:

| Patrón | Vistas, frente al tutorial más visto |
|---|---|
| Transformación: de algo sin valor a algo que quieres conservar | ~4× |
| Riesgo: hacerlo con cero práctica (¿error?) | ~2× |
| Curiosidad: un objeto inesperado, "esto pasó" | ~1,5× |
| Beneficio práctico: además protege tus cosas | ~1,3× |
| Exclusividad: un regalo que nadie más tiene | ~1× |
| Primera persona y alguien querido: "le hice a mi madre…" | ~0,3× |

Lo que se lee en los números:

1. **El tutorial paso a paso gana de calle**: 10× las vistas de las listas de regalos. El título promete facilidad
   y exclusividad (el único que necesitas, el camino más fácil, sin miedo a estropearlo, paso a paso). Es el formato
   que reduce la duda "¿sabré hacerlo?".
2. **Los shorts multiplican por 5–10 el alcance del largo** y los que funcionan tienen un gancho de
   transformación o de riesgo: de algo sin valor a algo que quieres conservar, del caos a algo bonito, hacerlo sin
   práctica (¿error?), ¿vale algo o nada?, este hobby me cambió las tardes. Persona, primera persona, resultado
   visible.
3. **El vídeo de bienvenida de menos de un minuto** es el segundo más visto: corto, orientado a "empieza hoy".
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

## 3. Traducción a la promesa del Cliente A

El vídeo que vende un kit tiene que hacer sentir tres cosas, en este orden:

| Sensación | Cómo se enseña | Overlay de Frame28 |
|---|---|---|
| "Esto es para mí" (gancho) | 3 s con transformación, riesgo o dolor: *De basura a…*, *sin práctica*, *¿lo estropearé?* | `hook` (texto grande, zona segura, 1–3 s) |
| "Yo puedo" (demostración) | pasos numerados, material corto, el ajuste y la herramienta dichos, primer plano de manos | `steps` (progreso 1/3), `box`, `pointer`, `list_focus` |
| "Sale bien" (resultado) | antes/después, "That's it!", el objeto terminado en manos | `before_after`, `draw` check, `kinetic` |
| "Otros lo hicieron" (prueba) | {N}K makers, {nota}★, reseña en texto | `counter`, `card` |
| "Ahora" (acción) | precio con descuento, código, "link in bio", QR, garantía de devolución | `cta` (precio + código + QR) |

## 4. Qué debe hacer Frame28 para una empresa así (prioridad por impacto/esfuerzo)

| # | Mejora | Por qué | Esfuerzo |
|---|---|---|---|
| 1 | **Overlays de venta**: `hook`, `cta` (precio, código, QR, "link in bio"), `steps` (progreso), `before_after` (dos instantes del mismo vídeo con barrido) | Son los cuatro momentos de la estructura que convierte y hoy se improvisan con `box`/`kinetic` | S–M |
| 2 | **Fábrica de shorts**: de un tutorial largo, N clips verticales de 15–45 s con gancho, subtítulos por palabras y cierre de CTA; variantes de gancho para rotar cada 7–14 días | Es donde está el alcance (shorts 5–10× el largo) y la cura de la fatiga de creativos | M |
| 3 | **Zonas seguras de plataforma** (TikTok/Reels/Shorts: iconos a la derecha, descripción abajo, barra superior): el generador avisa y la skill coloca | El 70 % se ve sin sonido y en el móvil; un texto bajo los iconos no existe | S |
| 4 | **Biblioteca de ganchos** en la skill de storyboard: los 10 tipos con plantillas en ES/EN y las frases del propio cliente que funcionaron | Que el agente escriba ganchos que ya han demostrado tirar | S |
| 5 | **Portada/miniatura** a partir de un fotograma + título + marca (YouTube 1280×720, Shorts vertical) | La miniatura decide el clic; hoy no la hacemos | M |
| 6 | **Versión en otro idioma** del mismo montaje: subtítulos y textos traducidos por el agente, mismos tiempos | Venden en varios mercados; el coste marginal es casi cero | S (flujo) |
| 7 | **Cuadrado 1:1 para ficha de producto** con el mismo storyboard (ya soportado por `canvas`) | El vídeo en PDP es el que más convierte | S (docs) |
| 8 | **Marcadores de resultado**: detectar en la transcripción las frases de resultado ("that's it", "turned out", "look at this") y proponer ahí el `before_after` y el check | Automatiza el momento "sale bien" | S |

Pendiente que no depende de Frame28: testimonios reales (necesitan clientes grabando), unboxing (material propio).

## Fuentes

- Canal de YouTube del Cliente A (listado con yt-dlp, 2026-09-30); el detalle, en `_private/`.
- Segwise, "Best DTC Ad Creative Hooks for 2026: Types, Examples, and Benchmarks": https://segwise.ai/blog/dtc-ad-creative-hooks
- Motion, "Best DTC Meta ad hooks 2025" y "How to write UGC ad scripts": https://motionapp.com/blog/best-dtc-meta-ad-hooks-2025 · https://motionapp.com/blog/how-to-write-ugc-ad-scripts
- Videowise, "8 Types of UGC Videos to Scale Ecommerce Revenue and CVR": https://videowise.com/live-commerce/8-types-of-ugc-videos-to-scale-ecommerce-revenue-and-cvr
- Vidjet, "Best video types for brands in DIY, Art & Crafts, and Electronics": https://www.vidjet.com/video-shopping-examples-for-diy-and-electronics-brands
- Ecommerce Fastlane, "5 UGC Hooks for Ecommerce Video Ads": https://ecommercefastlane.com/ugc-hooks-for-ecommerce/
