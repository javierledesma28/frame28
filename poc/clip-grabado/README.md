# Cliente A · tutorial de grabado en vidrio (primera pasada Frame28)

Vídeo de YouTube de una marca de kits de grabado (nombre en clave **Cliente A**; tutorial de vidrio, 3 min 17 s,
inglés), descargado con `uvx yt-dlp` (sin instalar nada). Brief de marca y storytelling en `brief.md` (anonimizado:
el brief real y la marca viven en `work/`, que no se versiona).

## Qué tiene de distinto

No es un plano de una persona hablando a cámara: es un **tutorial cenital de manos con voz en off**, ya editado
por la marca con sus propios rótulos (títulos arriba, marca de agua arriba a la izquierda, tarjeta final de color
con "Subscribe"). Frame28 trabaja **encima** de un vídeo producido:

- Sin cara ni gestos: `speaker`/`gestures` no aportan; `behind` no aplica. Los overlays se colocan mirando la hoja
  de contacto y esquivando los gráficos existentes (esquinas superiores) → franja inferior izquierda/derecha para
  cajas (`y` 840), cinéticos arriba al centro-derecha, tarjetas a pantalla completa solo sobre su tarjeta final.
- El audio lleva música: SNR 20 dB. La transcripción salió limpia igual (639 palabras; el nombre de la marca salió
  mal transcrito una vez y se corrigió a mano).
- Marca `cliente-a` creada con `frame28 brand from-site` a partir del CSS del sitio (acento cálido, tinta oscura,
  fuente de la marca) y el logo del sitio con variante oscura para fondo de acento. Vive en `work/brands/` (logo de
  terceros, no se versiona).

## Qué refuerza el montaje (del brief)

| Objetivo | Overlays |
|---|---|
| Facilidad, promesa | cinético "low speed · right bit · calm pace / beginner friendly" |
| Seguridad (confianza) | cajas "Safety glasses + mask", "Well-ventilated · clean surface" |
| Pasos que se pueden seguir | cajas "Project 1/2/3 · …" y micro-pasos: tape, trace, bits, speed, patina |
| Producto protagonista | `lower_third` "ENGRAVER PRO™ · precio · 30 % off · 30 diamond bits" + foto del producto (`image`) |
| Resultado | cinéticos "That's it!", "the perfect customized gift", "that handmade look" |
| Prueba social | contador de makers · estrellas · reseñas · garantía de 60 días (cifras de la web del día) |
| Cierre | se respeta la tarjeta final de la marca; subtítulos en inglés todo el vídeo |

Ficheros: `brief.md`, `storyboard.json` (26 overlays; nombres, precios y cifras difuminados), `clips.json` y
`storyboard-short-s4.json` + `strings-short-s4.es.json` (short vertical y su versión en español; fixtures de la suite
de pruebas). `work/` y `out/` no se versionan.

## Lo que este caso pidió al plugin (hecho)

- `frame28 graphics`: OCR por muestras (RapidOCR, CPU) → texto en pantalla con caja y tramo, tarjetas de color
  plano, ocupación 3×3 con ventanas libres; `frame28 build --graphics` avisa de colisiones. Probado aquí:
  marca de agua arriba a la izquierda (89 % del tiempo), rótulos del editor, tarjeta final; cero falsos positivos
  en el clip de hablante a cámara.
- Modo "vídeo producido" en `frame28-director` (sin speaker/gestures/behind; brief de marca; `kinetic.color`).
- `frame28 fetch <url>` con `yt-dlp` vía `uvx`.
- `frame28 brand from-site <url>`: la marca desde la web del cliente.
