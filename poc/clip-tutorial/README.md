# Tutorial producido · velas de soja (caso inventado)

**Todo en esta carpeta es inventado**: la marca (*Example Candle Co.*, en el dominio reservado `example.com`), el
producto (*Pour Kit™*), los precios, las cifras de prueba social y la transcripción. Reproduce la forma de un caso real
de Frame28 (un tutorial ya producido de una marca DTC, en inglés, con voz en off sobre un plano cenital de manos), pero
no sale de ningún vídeo ni de ninguna marca existente. Sirve de ejemplo del modo «vídeo producido» y de fixture de la
suite de pruebas. No hay vídeo: el storyboard se valida y se construye, pero para renderizar hace falta un `clip.mp4`
propio.

## Qué tiene de distinto un vídeo producido

No es un plano de una persona hablando a cámara: la marca ya lo editó con sus rótulos, su marca de agua y su tarjeta
final. Frame28 trabaja **encima**:

- Sin cara ni gestos: `speaker`/`gestures` no aportan y `behind` no aplica. Los overlays se colocan mirando la hoja
  de contacto y esquivando los gráficos que ya trae (`frame28 graphics` los detecta): cajas en la franja inferior
  (`y` 840), cinéticos arriba, tarjetas a pantalla completa solo sobre su propia tarjeta final.
- Fondos claros (mesa, cera, tela): los cinéticos van en la tinta de la marca (`kinetic.color`), no en blanco.
- La marca se propone con `frame28 brand from-site <url>`; aquí es `brands/velas-ejemplo.json`, inventada y sin logo.

## Qué refuerza el montaje (del brief)

| Objetivo | Overlays |
|---|---|
| Facilidad, promesa | cinético «thermometer · steady pour · patience / beginner friendly» |
| Seguridad (confianza) | cajas «Double boiler, never the burner», «Never leave melting wax alone» |
| Pasos que se pueden seguir | cajas «Project 1/2/3 · …» y micro-pasos: temperatura, mecha, fragancia, vertido, curado |
| Producto protagonista | `lower_third` «POUR KIT™» al principio y con precio y descuento cuando se nombra |
| Resultado | cinéticos «That's it!» con su `draw` check, «smooth, creamy top», «perfectly straight», «it lights up» |
| Prueba social | contador de velas hechas, estrellas, reseñas y devolución en 30 días |
| Cierre | se respeta la tarjeta final de la marca; subtítulos en inglés todo el vídeo |

## Ficheros

- `captions.json`: la transcripción inventada (44 frases, 212 s).
- `clips.json`: `frame28 clips plan captions.json --lang en --keyword "Pour Kit" -o clips.json` (cinco tramos con sus
  ganchos; lo genera el código, no se retoca a mano).
- `storyboard.json`: el montaje apaisado (23 overlays y subtítulos por frase).
- `storyboard-short-s5.json` + `strings-short-s5.es.json`: el short vertical del tramo s5 y su versión en español.
- `brief.md` y `brands/velas-ejemplo.json`: el brief de marca y la marca, inventados.
