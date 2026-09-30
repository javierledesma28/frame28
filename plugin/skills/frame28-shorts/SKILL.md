---
name: frame28-shorts
description: 'Convierte un vídeo largo (tutorial, demo, charla) en varios shorts verticales de 15–45 s que venden: elige los tramos con más momentos (resultado, promesa, objeción, cifras, producto), pone un gancho de 3 s, subtítulos por palabras y una llamada a la acción con precio, código o QR, y genera variantes de gancho para rotar. Usar cuando pidan "sácame shorts", "reels", "TikToks", "clips para redes", "trocea este vídeo" o una versión corta vertical de un vídeo largo.'
---

# Frame28 · Shorts que venden

Un vídeo largo tiene 3–6 tramos que funcionan solos. Este flujo los encuentra, los recorta y los deja montados
con la estructura que convierte (gancho → demostración → resultado → acción). Los datos y plantillas están en
`../frame28-storyboard/references/ganchos.md` y `research/05-video-venta-diy.md`.

## Flujo

```bash
frame28 clips plan work/captions.json --lang en --keyword Engraver Pro --keyword Cliente A -o work/clips.json --target 30 --count 5
```
Propone tramos que empiezan y terminan en frase, puntuados por momentos: **resultado** ("that's it", "turned out"),
**promesa** ("beginner", "easy"), **objeción** ("isn't it", "what if"), **cifras** y **producto** (los `--keyword`).
Cada tramo trae tres ganchos de tipos distintos. Léelos con el usuario: la puntuación ordena, no decide.

Por cada tramo elegido:
```bash
frame28 clips cut work/clips.json s4 work/clip.mp4 --audio work/voice.wav --words work/words.json --captions work/captions.json
frame28 reframe work/clips/s4/clip.mp4 -o work/clips/s4/vertical.mp4 --mode crop     # hablante a cámara
frame28 reframe work/clips/s4/clip.mp4 -o work/clips/s4/vertical.mp4 --mode blur     # manos, producto, vídeo producido
frame28 clips scaffold work/clips.json s4 --brand <marca> --cta work/cta.json --hook 0 --video vertical.mp4
frame28 build work/clips/s4/storyboard.json -o work/clips/s4/project && frame28 check work/clips/s4/project
frame28 render work/clips/s4/project -o out/shorts/s4-hook0.mp4
```
`cut` deja `clip.mp4`, `voice.wav`, `words.json` y `captions.json` con los tiempos del short. `scaffold` escribe un
storyboard que **ya construye**: `platform: tiktok`, gancho (uno de los tres), subtítulos por palabras (`pages`,
a 18 % del borde inferior) y `cta` en los últimos 4–5 s. `work/cta.json` son los campos del overlay `cta`
(`title`, `price`, `old_price`, `discount`, `code`, `line`, `url`).

## Afinar el storyboard del short (lo que hace la diferencia)

1. **Gancho**: reescribe las líneas de la plantilla con las palabras del hablante o de la marca (≤ 5 palabras por
   línea, 2 líneas). Sin cifras inventadas.
2. **Demostración**: si el tramo tiene pasos, añade `steps` (`items` con `at` de cada paso) y una o dos `box`
   con el dato que se dice (velocidad, broca, material). En vertical, todo arriba (`y` 400–700 con `blur`, franja
   superior con `crop`).
3. **Resultado**: `before_after` con `before_t`/`after_t` del propio short (el primer plano del objeto y el final)
   justo después de la frase de resultado; o `draw` check + `kinetic`.
4. **Prueba social** en 2 s si cabe (`counter` 650K+).
5. **CTA**: precio y descuento reales del sitio; `url` para el QR si el vídeo se verá en pantalla grande o en
   YouTube; "Link in bio" si es TikTok/Reels. Nunca antes de haber enseñado el resultado.
6. **Variantes**: renderiza el mismo short con `--hook 0`, `--hook 1`, `--hook 2` → `s4-hook0.mp4`,
   `s4-hook1.mp4`, `s4-hook2.mp4`. Las plataformas queman un creativo en 7–14 días; se rota el gancho, no el cuerpo.

## Qué no hacer

- Shorts de más de 45 s ni de menos de 15 (salvo un "first time here" de 20–35 s a propósito).
- Empezar por el logo o el saludo: el gancho es lo primero.
- Poner texto bajo los iconos de la derecha o la descripción de abajo (`build` avisa con `platform`).
- Repetir el CTA en cada short con la misma frase: cambia el ángulo (precio, garantía, "everything included").
