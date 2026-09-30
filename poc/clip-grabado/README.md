# Cliente A · tutorial de grabado en vidrio (primera pasada Frame28)

Vídeo de YouTube de la marca **Cliente A** ("Tutorial de vidrio", 3 min 17 s, inglés),
descargado con `uvx yt-dlp` (sin instalar nada). Brief de marca y storytelling en `brief.md`.

## Qué tiene de distinto

No es un plano de una persona hablando a cámara: es un **tutorial cenital de manos con voz en off**, ya editado
por la marca con sus propios rótulos (títulos arriba, marca de agua arriba a la izquierda, tarjeta final naranja con
"Subscribe"). Frame28 trabaja **encima** de un vídeo producido:

- Sin cara ni gestos: `speaker`/`gestures` no aportan; `behind` no aplica. Los overlays se colocan mirando la hoja
  de contacto y esquivando los gráficos existentes (esquinas superiores) → franja inferior izquierda/derecha para
  cajas (`y` 840), cinéticos arriba al centro-derecha, tarjetas a pantalla completa solo sobre su tarjeta final.
- El audio lleva música: SNR 20 dB. La transcripción salió limpia igual (639 palabras; "(marca mal transcrita)" → Cliente A).
- Marca `cliente-a` creada con `frame28 brand init` a partir del CSS del sitio (ámbar `#fbb04c`, marrón `#2c2523`,
  Poppins) y el logo del sitio con variante marrón para fondo ámbar. Vive en `work/brands/` (logo de terceros, no
  se versiona).

## Qué refuerza el montaje (del brief)

| Objetivo | Overlays |
|---|---|
| Facilidad, promesa | cinético "low speed · right bit · calm pace / beginner friendly" |
| Seguridad (confianza) | cajas "Safety glasses + mask", "Well-ventilated · clean surface" |
| Pasos que se pueden seguir | cajas "Project 1/2/3 · …" y micro-pasos: tape, trace, bits, speed, patina |
| Producto protagonista | `lower_third` "ENGRAVER PRO™ · $69.99 · 30 % off · 30 diamond bits" + foto del producto (`image`) |
| Resultado | cinéticos "That's it!", "the perfect customized gift", "that handmade look" |
| Prueba social | contador 650K+ happy makers · 4.7★ · 15,600+ reviews · 60-day guarantee |
| Cierre | se respeta la tarjeta final de la marca; subtítulos en inglés todo el vídeo |

Ficheros: `brief.md`, `storyboard.json` (26 overlays). `work/` y `out/` no se versionan.

## Lo que este caso pide al plugin (pendiente)

- Detectar los gráficos ya presentes en el vídeo (OCR o detección de texto por fotograma) para proponer zonas libres.
- Un modo "vídeo producido" en `frame28-director` que salte speaker/gestures/behind y sugiera cajas y pizarras.
- `frame28 fetch <url>` con `yt-dlp` como paso opcional del pipeline.
