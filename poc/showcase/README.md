# Showcase del motor

Campaña de demo de 38 s (más 3,5 s de tarjeta de marca) que enseña los efectos de movimiento sobre un vídeo nuestro: el
tramo de `poc/clip-demo` que empieza en «Frame28 hace tres cosas» (de 28,4 a 66,48 s del corte). Cada efecto de la serie
de movimiento (R1–R5) añade aquí su escena al terminar, y Marketing y Diseño la usan para la demo real del motor en la
web (F28-292).

| Tramo | Escena | Serie | Estado |
|---|---|---|---|
| 1,9–12,4 s | Frase detrás del hablante palabra a palabra: antetítulo «TRES COSAS» y ESCUCHA / ENTIENDE / MONTA, cada palabra cuando la dice (mientras cuenta con los dedos), la cabeza delante de la última línea y salida lenta con desenfoque | R1 (F28-339) | hecha |
| — | Las escenas de R2 a R5 | F28-340 a F28-343 | pendientes |
| 16,5–41,6 s | Barras «a mano / con Frame28», contador 22×, dos cinéticos y tarjeta de marca, los de `poc/clip-demo` desplazados | — | de partida |

## Cómo se reproduce

Los medios no se versionan (`work/` está ignorado). Salen del corte de clip-demo (`poc/clip-demo/work/cut/`, ver su
README) con el tramo de `keep.json`:

```bash
cd poc/showcase
frame28 cut apply ../clip-demo/work/cut/clip.mp4 keep.json --audio ../clip-demo/work/cut/voice.wav \
  --words ../clip-demo/work/cut/words.json --captions ../clip-demo/work/cut/captions.json -o work
cd work
frame28 matte clip.mp4 --start 2.0 --end 12.5 -o alpha_2.0.webm     # unos 7 min en CPU; --gpu con el extra gpu
cp ../storyboard.json . && frame28 build storyboard.json -o project && frame28 check project
frame28 render project -o out/showcase.mp4 --workers 10
```

El storyboard ancla las palabras a la voz (`"words": "words.json"` en la raíz y `words_at: "auto"`): si cambias el tramo,
`build` vuelve a poner cada palabra en su sitio sin tocar segundos. Al añadir una escena, respeta el ritmo del modo
promocional (un evento cada 1–3 s solo en los primeros 20–30 s) y que haya una frase detrás del hablante cada ~20 s como
mucho.

## Medidas (2026-10-19)

- **Whisper no acierta el inicio de la palabra que sigue a una pausa.** Contra la onda de `voice.wav`, en este tramo:
  «tres» +0,25 s, «escucha» +0,40 s (la palabra entraba antes de decirse), «monta» −0,14 s. En el storyboard de
  clip-demo, el cinético «se queda en» entraba 0,78 s antes de la voz y «y listo» 0,80 s antes. Desde F28-339, `build`
  pega las anclas al arranque real de la voz (`motion.snap_to_voice`, con `source.audio`); aquí los cinéticos `k2` y
  `k3` van anclados (`"at": "word:…"`) para que lo enseñen.
- **±1 fotograma contra la voz**, comprobado con los fotogramas t−1, t y t+1 de cada entrada (70–72 para el antetítulo,
  143–145 ESCUCHA, 195–197 ENTIENDE y 277–279 MONTA): en t−1 la palabra apenas asoma y en t ya está entrando.
- **Composición**: tinta (`ink`) sobre la pared lisa, entre la viga y la estantería (`x` 0.383, `y` 0.235, `fit` 0.31);
  el pelo tapa el pie de «TA» de MONTA (la máscara funciona) y la frase completa se queda 2 s antes de irse.
- **Tiempos**: máscara de 10,5 s a 1080p, 6 min 40 s en CPU; render de 41,6 s con `--workers 10 --gpu`, 3 min 30 s.
  `check` solo avisa del contraste de la tarjeta de marca a mitad de su animación por letras (el mismo de clip-demo).
