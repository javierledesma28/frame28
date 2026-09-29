---
name: frame28-storyboard
description: 'Decide el montaje de un video hablado y lo escribe como storyboard JSON de Frame28: qué técnica (rótulo, título cinético, texto detrás, callout, pizarra, imagen) va con cada frase, en qué instante (tiempos por palabra) y en qué zona del encuadre. Usar cuando haya una transcripción con tiempos y haga falta "decidir qué poner en pantalla", crear o retocar un storyboard, o convertir notas del usuario ("aquí quiero una gráfica") en overlays concretos.'
---

# Frame28 · Storyboard

Entrada: `work/words.json`, `work/captions.json`, `work/transcript.txt`, salida de `frame28 speaker` y de `frame28 gestures`, hoja de
contacto del clip y, si hay, el brief del usuario. Salida: `work/storyboard.json` válido
(`frame28 storyboard schema` imprime el formato; `references/ejemplo-storyboard.json` es uno real).

## Método (en este orden)

1. **Lee el discurso entero** y márcalo en *beats*: cada frase o grupo de frases con una idea. Para cada beat
   decide su función: presentar (quién habla), afirmar (una idea fuerte), enumerar (lista), señalar (gesto a
   algo), contrastar (A vs B), cifra (número), mostrar (una UI o imagen), cerrar.
2. **Asigna una técnica por función** con esta tabla. No mezcles dos técnicas grandes en el mismo beat.

   | Función | Técnica (type) | Cuándo entra |
   |---|---|---|
   | presentar | `lower_third` | 0,3 s tras la primera palabra, dura 2,5–4 s |
   | afirmar / palabra clave | `kinetic` (2 líneas máx.) o `behind` (una palabra) | cada palabra en su `start` |
   | enumerar | `list_focus` (3–5 ítems) | el foco salta en el `start` de cada ítem |
   | señalar con la mano | `pointer` | copia la sugerencia de `frame28 gestures` (`confidence: high`) |
   | dato corto / matiz | `box` | `at` = primera palabra del dato |
   | comparar / cifra fuerte | `chart` (`bar` con `hero`, `counter`) | 3–6 s; el ganador entra el último |
   | frase-lema, cambio de capítulo | `card` (negro o acento) o `card_words` | tapa al hablante 1,5–3 s |
   | mostrar algo | `image` | `at` = cuando lo nombra |
   | abrir o cerrar con marca | `brand_card` | 2–3 s; al final, con `duration` raíz mayor que el clip |
   | todo el video | `captions` (frase) o `caption_style` (`pages`/`karaoke`, por palabras) | por frase de `captions.json`; por palabras de `words.json` |

3. **Coloca** cada overlay en el lado libre (`free_side` de `frame28 speaker`). En 1920×1080: con hablante a la
   izquierda, `x` entre 1100 y 1750; a la derecha, `x` entre 90 y 800; centrado, usa esquinas y `behind`. Nunca sobre la
   cara (`face_box` de `frame28 gestures` o `bbox_canvas` de `frame28 speaker`; ambos ya vienen en píxeles del lienzo).
   Los `pointer` salen de `frame28 gestures`; si hay que ajustar uno, mira el fotograma con `frame28 frames`.
   **Vertical (1080×1920)**: el hablante ocupa el centro; las zonas libres son la franja superior (`y` 40–260, encima
   del pelo), la inferior (`y` 1150–1650, sobre el torso; los subtítulos van de 1650 abajo) y poco a los lados. Usa
   `box`/`kinetic` arriba, `pointer` con la caja sobre el torso, `card`/`counter` a pantalla completa para tapar
   silencios, y `caption_style` `pages` en vez de `captions` por frase. Nada de `chart bar` con más de 3 filas.
4. **Ritmo**: un evento visual cada 2–4 s; ningún tramo de más de 8 s sin nada; máximo un overlay grande a la
   vez, más subtítulos. Los overlays se solapan solo si están en zonas distintas.
5. **Tiempos**: `start` = 0,05 s antes del `at`; `end` = fin de la frase o inicio del siguiente overlay en la
   misma zona. `at` de cada palabra = su `start` en `words.json`, sin redondear.
6. Escribe el JSON, valida con `frame28 storyboard validate` y haz una pasada de lectura en voz alta: ¿cada
   overlay dice algo que la voz está diciendo en ese instante? Si no, fuera.

## Reglas de estilo (del análisis del video de referencia)

- Cajas: 2–4 palabras. Cinéticos: hasta 5 palabras por línea, 2 líneas. `behind`: una palabra en mayúsculas.
- Una palabra de acento por overlay como mucho (`accent: true`), la que lleva la carga.
- Revelado: `reveal: "rise"` para titulares de impacto (máscara por palabra), `"chars"` para una sola palabra o marca, `fade` para el resto. No mezclar los tres en la misma escena.
- `draw` (icono que se dibuja) solo con propósito: un check al confirmar, un subrayado bajo la palabra clave, una flecha hacia lo señalado. Uno por escena.
- Pizarras: fondo negro para afirmaciones, acento para "producto", blanco para listas.
- El dato ganador entra el último y destacado; nunca una tabla entera de golpe.
- Todo en el idioma del hablante; nombres propios tal como los escribe el usuario.

## Referencias

- `references/tecnicas.md`: las 16 técnicas del video de referencia, cómo se logran y cuándo usarlas.
- `references/grabacion.md`: qué pedirle al usuario para que el material funcione.
- `references/ejemplo-storyboard.json`: storyboard real de un clip de 10 s (webcam, español).
