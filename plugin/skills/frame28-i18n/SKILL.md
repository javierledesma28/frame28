---
name: frame28-i18n
description: 'Saca la versión de un montaje de Frame28 en otro idioma con los mismos tiempos: extrae los textos del storyboard (rótulos, cinéticos, cajas, gancho, CTA, subtítulos), los traduce con criterio de subtitulado (corto, natural, nombres y cifras intactos), los vuelve a aplicar y regenera los subtítulos por palabras sobre el ritmo original. Usar cuando pidan "la versión en inglés", "tradúcelo", "subtítulos en francés", "el mismo vídeo para el mercado alemán" o una segunda lengua de un vídeo ya montado.'
---

# Frame28 · Versión en otro idioma

El vídeo ya está montado y aprobado en un idioma. La segunda lengua no se remonta: **mismos tiempos, mismos
overlays, textos traducidos**. La voz sigue siendo la original (el doblaje es otro paso, pendiente); lo que cambia
es todo lo que se lee, que en redes es el 70 % del mensaje.

## Flujo

```bash
frame28 i18n extract work/storyboard.json --captions work/captions.json -o work/strings.json
# → traduces los valores "text" del JSON (mismas claves) y lo guardas como work/strings.en.json
frame28 i18n apply work/storyboard.json work/strings.en.json --lang en
# → work/storyboard.en.json (+ work/words.en.json si los subtítulos son por palabras)
frame28 build work/storyboard.en.json -o work/project-en && frame28 check work/project-en && frame28 render work/project-en -o out/video-en.mp4
frame28 captions export work/words.en.json -o out/video-en.srt      # subtítulos aparte para la plataforma
```

`extract` da, por cada texto, la clave, el tipo de overlay, el instante y un **límite orientativo de caracteres**
(`max_chars`): una caja de 26 caracteres en inglés no admite 40 en alemán. `apply` avisa si te pasas un 35 %.

## Cómo traducir (criterio de subtitulador, no de traductor)

- **Corto y hablado**: el espectador lee en el tiempo que dura la frase. Si el original dice "I think I just made
  the perfect customized gift ever", en español cabe "Creo que acabo de hacer el regalo personalizado perfecto",
  no una paráfrasis más larga.
- **Nombres, marcas, cifras y códigos intactos**: Engraver Pro™, Cliente A, 69,99 $, GLASS30. Adapta el formato de
  precio al mercado solo si el usuario lo pide (€ con coma decimal, etc.).
- **Gancho y CTA con las mismas reglas del original**: ≤ 5 palabras por línea, verbo primero, sin cifras nuevas.
- **Subtítulos por palabras** (`pages`/`karaoke`): traduce la **frase** de `captions.N.text`; `apply` reparte las
  palabras traducidas sobre los inicios de las palabras originales, así las pausas caen donde caían. Mantén el
  orden de ideas dentro de la frase para que "ahora" salga cuando el hablante dice "now".
- **Puntuación**: conserva puntos y comas al final de frase; el paginado corta ahí.
- **Tratamiento**: tú/usted según la marca (en su web); en duda, tú para DIY y consumo.
- No traduzcas lo que esté quemado en el vídeo original (rótulos del editor): no puedes cambiarlo, y duplicarlo
  traducido encima confunde; si molesta, tápalo con un `box` en el nuevo idioma.

## Comprueba antes de renderizar

`frame28 build` avisa de cajas que se salen del lienzo (los textos crecen al traducir); `check` avisa de solapes.
Mira la hoja de contacto: un cinético de dos líneas en inglés puede necesitar tres en alemán → baja `size`.

## Portada

`frame28 cover … --title "<gancho traducido>"`: una portada por idioma, mismo fotograma.
