# Demo del plugin · guion `docs/guion-demo.md` grabado (clip-demo)

Clip de 83 s (webcam 1080p a 24 fps, español) siguiendo el guion de demo: presentación, "Frame28" detrás,
dos "aquí" señalados, tres objetos enseñados, lista de tres, cifras 90 → 4 minutos y 22×, "eh… bueno…" con
pausa larga a propósito, cierre con marca. Resultado: `out/demo.mp4`, 70 s (66,5 s de clip + tarjeta).

Qué demuestra y qué destapó:
- **Cortes**: 82,7 → 66,5 s en 19 tramos. El "eh… bueno…" no lo cazaba el planificador: Whisper no transcribe
  el "eh" y estira "bueno" hasta tapar la pausa. Se añadieron dos reglas a `cut.py`: silencio de audio *dentro* de
  una palabra larga (≥ 0,7 s) y muletillas condicionadas (`bueno`, `pues`, `vale`, `o sea`, `a ver`…) solo si les
  sigue una pausa de audio. "este"/"nada" quedan fuera por ambiguos ("este muñeco", "de este a oeste").
- **Gestos**: cinco `pointer` (dos "aquí", auriculares, muñeco) de `frame28 gestures` con `confidence: high` o
  revisados en `gestos.png`; la taza no la detectó (mano fuera del encuadre) y se colocó mirando `frames`.
- **Texto detrás**: "FRAME28" con máscara solo del tramo 5,9–8,3 s del clip cortado (37 s de cálculo).
- **Lista sin tapar al hablante**: tres `box` apilados a la derecha en vez de `list_focus` a pantalla completa,
  para que se vean los dedos contando.
- **Gráfica**: `chart bar` a pantalla completa con `stagger` 3,6 s para que "Con Frame28" entre cuando lo dice, y
  `counter` 22×. Nombres propios corregidos en `words.json` antes de cortar (Ledesma, Think28, Frame28).

Ficheros: `storyboard.json` (sobre el clip cortado), `cuts.json`. `work/` y `out/` (medios, caras) no se versionan.

## Versión vertical (9:16) con `frame28 reframe`

`storyboard-vertical.json` monta la misma demo sobre `work/cut/vertical.mp4`, el clip apaisado reencuadrado con
`frame28 reframe --mode crop` (ventana 608×1080 que sigue la cara, escalada ×1,78). Los gestos hacia los lados
("aquí… o aquí") quedan fuera del recorte, así que en vertical se resuelven con un cinético en la franja superior
en vez de `pointer`; las cajas y cinéticos van arriba (`y` 90–340) y los subtítulos por palabras (`pages`) abajo.
Salida: `out/demo_vertical.mp4`.

