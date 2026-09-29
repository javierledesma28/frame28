# Catálogo de técnicas (del análisis de un *founder launch video* de referencia)

Sistema de diseño que las une: tres fondos (acento, blanco hueso, negro), dos tipografías (grotesca para lo grande,
monoespaciada para "lo que parece software"), esquinas de encuadre en casi todas las cajas, conectores con codo y
punto, animaciones de 0,15–0,5 s con *ease-out*. Ritmo: un evento visual cada 2–4 s; ~40 % hablante con overlays,
~60 % pizarras a pantalla completa; el hablante nunca pasa de 8 s sin evento.

| # | Técnica | `type` en Frame28 | Cómo se logra | Cuándo usarla |
|---|---|---|---|---|
| T1 | Tarjeta de identidad monoespaciada que se escribe | `lower_third` | máscara de anchura animada + cursor de acento | presentación, primeros 4 s |
| T2 | Tipografía cinética sincronizada con la voz | `kinetic`, `card_words` (+ `reveal`: fade / rise / chars) | cada palabra entra en su `start`; `rise` = máscara por palabra, `chars` = letras escalonadas (SplitText) | afirmaciones, lemas |
| T3 | Texto detrás del hablante | `behind` | fondo → texto → vídeo con alfa del hablante encima | una palabra clave, fondo fijo |
| T4 | Transición de mosaico de píxeles | (pendiente) | rejilla de celdas con retardo aleatorio | cambio de capítulo |
| T5 | Pizarras minimalistas a pantalla completa | `card`, `list_focus`, `card_words` | fondo plano + texto + diagrama mínimo | cuando el hablante no aporta |
| T6 | Callout con conector (punto + línea) | `pointer` | línea que crece del punto a la caja | señalar algo en el encuadre |
| T7 | Esquinas de encuadre | (automático en cajas) | cuatro `<i>` con bordes | firma visual |
| T7b | Iconos y trazos que se dibujan | `draw` | DrawSVG sobre paths de Lucide o propios | marcar, subrayar, señalar |
| T8 | Mockups de UI (ventana, terminal) | `image` (por ahora) | HTML/CSS renderizado | mostrar producto |
| T9 | Carrera de terminales lado a lado | (pendiente) | dos velocidades de tipeo | comparar rendimiento |
| T10a | Rejilla de puntos secuencial vs paralela | (pendiente) | celdas que se encienden | explicar un proceso |
| T10b | Barras 3D isométricas | (pendiente) | proyección isométrica | datos con dos dimensiones |
| T10c | Bar chart horizontal agrupado con fila ganadora | `chart` kind `bar` (+ `hero`) | barras con ease-out + caja blanca | comparativa con ganador |
| T10d | Tabla con scroll hasta la fila clave | (pendiente) | desplazamiento vertical | listas largas con un ganador |
| T10e | Scatter log con punto destacado | (pendiente) | puntos escalonados + etiqueta | "off the charts" |
| T10f | Cifras animadas (contador, anillo) | `chart` kind `counter` | interpolación numérica | un número fuerte |
| T11 | PiP del hablante dentro de una tarjeta de datos | (pendiente) | vídeo escalado con marco | dato + reacción |
| T12 | Rueda giratoria de textos en arco | (pendiente) | rotación de grupo, activo en blanco | enumeración de 3 males |
| T13 | Karaoke de párrafo | (pendiente) | palabras que se iluminan | disclaimer, cita larga |
| T14 | Texturas de fondo (dithering, grid, suelo 3D) | (pendiente) | patrón SVG/PNG | profundidad barata |
| T15 | Subtítulos quemados | `captions` | caja negra centrada abajo | siempre |
| T16 | Fondo fijo + cambios de vestuario por capítulo | dirección de rodaje | — | ver `grabacion.md` |

Regla de oro: cada gráfica dura 3–6 s, tiene un solo mensaje y un solo elemento destacado, que entra el último.
