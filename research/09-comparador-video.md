# Research: comparador de vídeo "antes / después" con barra deslizante

> **Para quien lee esto (prompt / agente del producto):** este documento recoge el research hecho para elegir cómo montar en la web una comparación interactiva entre el vídeo original y el vídeo procesado por el producto. Úsalo para decidir la implementación. La sección 7 tiene una recomendación, pero puedes descartarla si el contexto del producto pide otra cosa.

---

## 1. Objetivo

- Publicar un vídeo en un sitio web.
- Sobre el vídeo hay una **línea vertical que el usuario puede arrastrar** a izquierda o derecha.
- **Izquierda de la línea:** vídeo original. **Derecha:** el mismo vídeo con el producto aplicado.
- El usuario puede **reproducir, pausar y mover la línea en cualquier momento mientras el vídeo corre** y comparar en tiempo real.
- Es el mismo formato que usan las demos de GPUs, como las comparativas de NVIDIA DLSS (nativo frente a DLSS).
- **Objetivo principal:** que la diferencia entre original y procesado se vea con claridad y sea creíble.

## 2. Requisitos derivados

| # | Requisito | Prioridad | Motivo |
|---|---|---|---|
| R1 | **Sincronía exacta a nivel de frame** entre los dos lados | Crítica | Si un lado va 2–3 frames desfasado, la comparación pierde credibilidad |
| R2 | Barra arrastrable con ratón **y táctil** (móvil y tablet) | Alta | Los clientes ven demos en el móvil |
| R3 | Controles: play/pausa, seek, sonido, pantalla completa, loop | Alta | Es una demo de producto, no un GIF |
| R4 | Calidad visual alta (poca compresión) | Alta | La compresión puede tapar justo la diferencia que se quiere enseñar |
| R5 | Página estática, sin backend | Media | Se puede alojar en cualquier hosting estático o CDN |
| R6 | Sin dependencias poco mantenidas | Media | Menos riesgo y menos mantenimiento |
| R7 | Accesible (teclado, aria) y responsive | Media | Calidad de producto |
| R8 | Fácil de reutilizar con otros pares de vídeos | Media | Habrá más demos |

## 3. Las dos arquitecturas posibles

### A. Dos elementos `<video>` superpuestos

- Se reproducen dos vídeos independientes, uno encima del otro. El de arriba se recorta con `clip-path` o `width` según la posición de la barra.
- **Pros:** simple. Cada vídeo se puede cambiar por separado y no hace falta preprocesarlos.
- **Contras:** **los dos vídeos se desincronizan** por buffering, seek, pestaña en segundo plano o decodificación desigual. Hay que resincronizar por JS (comparar `currentTime` y corregir), y aun así puede haber deriva de 1–3 frames. Además se descargan dos archivos y se decodifican dos streams.
- **No cumple bien R1.**

### B. Un único vídeo "side-by-side" (SBS) y render en canvas o CSS ✅

- Se preprocesa: original y procesado se unen en **un solo MP4** colocados uno al lado del otro (doble de ancho).
- En el navegador hay un solo `<video>` oculto. Un `<canvas>` pinta la parte izquierda del frame original hasta la barra y, desde la barra, la parte equivalente del frame procesado.
- **Pros:** **sincronía perfecta por construcción**, porque es un único stream. Un solo archivo, un solo decodificador y un solo control de reproducción. Es la técnica que usan las demos serias.
- **Contras:** requiere un paso de preprocesado con ffmpeg. El archivo tiene el doble de ancho (por ejemplo 3840×1080 para dos clips 1080p), así que pesa más. Los dos clips deben tener la misma resolución, fps y duración.
- **Cumple R1 a R8.**

Comando de preprocesado, ya probado:

```bash
ffmpeg -i original.mp4 -i procesado.mp4 \
  -filter_complex "[0:v][1:v]hstack=inputs=2,format=yuv420p[v]" \
  -map "[v]" -map 1:a \
  -c:v libx264 -crf 21 -preset slow -profile:v high -level 5.1 \
  -movflags +faststart -c:a aac -b:a 128k comparativa_sbs.mp4
```

- `-map 1:a`: usa el audio del vídeo procesado. Cámbialo a `0:a` si el audio bueno es el del original. Si ninguno tiene audio, quita esa opción.
- `-crf 18–21`: calidad alta. Un valor más bajo da más calidad y más peso.
- `+faststart`: el vídeo empieza a reproducirse antes de descargarse entero.
- Alternativa `vstack` (uno encima de otro, 1920×2160): sirve si algún navegador o dispositivo tiene problemas con 3840 px de ancho.

## 4. Opciones de librería y código evaluadas

**No existe un ranking oficial para este tipo de componente.** El "reconocimiento" se mide por adopción (estrellas en GitHub, descargas en npm), mantenimiento activo y aparición en comparativas.

### 4.1 Librería más reconocida de la categoría (orientada a imágenes)

| Opción | Tipo | Vídeo | Sincronía | Mantenimiento | Comentario |
|---|---|---|---|---|---|
| [sneas/img-comparison-slider](https://github.com/sneas/img-comparison-slider) | Web component con wrappers para React, Vue y Angular | Sí, con un `<video>` en cada slot | ❌ La resuelves tú (arquitectura A) | Activo, la más adoptada | Aparece en comparativas 2026 ([croct.com](https://blog.croct.com/post/best-react-before-after-image-comparison-slider-libraries)). Buena UX de barra, pero no está pensada para vídeo |

### 4.2 Específicas para vídeo (proyectos pequeños)

| Opción | Qué es | Comentario |
|---|---|---|
| [kriskbx/video-comparison.js](https://github.com/kriskbx/video-comparison.js/) | Librería JS de slider para vídeo HTML5 | La "clásica" de vídeo, pero antigua y con poco mantenimiento |
| [bluememory14/web-video-comparison](https://github.com/bluememory14/web-video-comparison) | Herramienta HTML con reproducción sincronizada y zoom | Interesante para revisar calidad internamente; menos pensada como widget de marketing |
| [chenyuntc/video-comparison-slider](https://github.com/chenyuntc/video-comparison-slider) | HTML de ejemplo | Muy simple, sirve de referencia |
| [LiangrunDa/video-compare](https://github.com/LiangrunDa/video-compare) | Proyecto pequeño de comparación de vídeo | Referencia |

### 4.3 Ejemplos y tutoriales (para entender la técnica, no para producción)

- [CodePen: HTML5 Video Before-and-After Comparison Slider](https://codepen.io/njr-amorim/pen/PZrdrM)
- [The New Code: Interactive Before/After Video Comparison in HTML5 Canvas](https://thenewcode.com/364/Interactive-Before-After-Video-Comparison-in-HTML5-Canvas). Explica la técnica de canvas (arquitectura B).
- [CSS Script: Mobile-Friendly Video Comparison Slider](https://www.cssscript.com/video-comparison-slider/)

### 4.4 Referencias del formato "estilo DLSS"

- [DLSS 5 Video Player (demo)](https://2600th.github.io/dlss5-video-player/) y [ficha del proyecto](https://www.2600th.com/work/dlss5-video-player/). Proyecto personal open source, muy vistoso, sirve como referencia visual.
- [tekkusai/dlss5-comparison](https://github.com/tekkusai/dlss5-comparison). Slider entre Native, Lighting Only y DLSS 5. Útil como idea si en el futuro se quieren **más de dos estados**.

## 5. Matriz de decisión

Puntuación de 1 a 5 frente a los requisitos de la sección 2.

| Criterio | Peso | Propia (B: SBS + canvas) | img-comparison-slider + 2 vídeos (A) | Librerías vídeo pequeñas | Ejemplos CodePen/blog |
|---|---|---|---|---|---|
| R1 Sincronía | ×3 | **5** | 2–3 (con script de resync) | 2–4 según proyecto | 2 |
| R2 Táctil | ×2 | 5 | 5 | 2–3 | 2–3 |
| R3 Controles | ×2 | 5 (hechos a medida) | 3 (hay que añadirlos) | 2–3 | 1–2 |
| R4 Calidad | ×2 | 5 (un stream, CRF controlado) | 4 | 4 | 4 |
| R5 Estático | ×1 | 5 | 5 | 5 | 5 |
| R6 Dependencias | ×1 | 5 (cero) | 4 | 1–2 | 5 (pero hay que reescribirlos) |
| R7 Accesibilidad | ×1 | 4 | 5 | 1–2 | 1 |
| R8 Reutilizable | ×1 | 4 (requiere ffmpeg por par) | 5 | 3 | 2 |

## 6. Implementación ya construida (POC)

Ya existe un POC funcional con la **arquitectura B**:

- **Vídeos de entrada:** `clip.mp4` (original, 1920×1080, 30 fps, 10 s, sin audio) y `javier_recut.mp4` (procesado, mismo formato, con audio AAC). Se comprobó que van alineados frame a frame.
- **Salida:** `comparador-web/index.html` y `comparador-web/comparativa_sbs.mp4` (3840×1080, unos 14,5 MB, CRF 21).
- **Funcionalidad:** barra arrastrable (pointer events, ratón y táctil), flechas ← → para mover la barra, espacio para play/pausa, seek, sonido (arranca en silencio por las políticas de autoplay y se activa al pulsar play), loop, pantalla completa, etiquetas "Original" y "Con producto" que se ocultan cuando la barra llega al borde, y tema claro/oscuro.
- **Render:** un `<video>` oculto y un `<canvas>` que se repinta en cada frame con `requestVideoFrameCallback` (con `requestAnimationFrame` si el navegador no lo soporta). Para cada frame se hacen dos `drawImage`: la mitad izquierda del SBS hasta `split` y la mitad derecha desde `split`.
- **Pendiente:**
  - Probarlo en navegadores reales (Chrome, Edge, Safari iOS).
  - Poner el nombre del producto en la etiqueta derecha.
  - Añadir un poster o miniatura.
  - Valorar varias resoluciones si los vídeos son largos.

Lógica clave del render:

```js
const hw = v.videoWidth / 2, vh = v.videoHeight;
const x = Math.round(W * split), sx = hw * split;
ctx.drawImage(v, 0,       0, sx,      vh, 0, 0, x,     H); // original
ctx.drawImage(v, hw + sx, 0, hw - sx, vh, x, 0, W - x, H); // procesado
```

## 7. Recomendación

**Usar la arquitectura B con código propio, como en el POC.**

1. Es la única opción que garantiza el requisito crítico (R1, sincronía exacta), y lo garantiza por diseño, sin depender de parches.
2. Son unas 80–100 líneas de JS sin dependencias, con control total del diseño y la marca.
3. Las librerías de vídeo que existen son pequeñas y están poco mantenidas. La librería más reconocida (img-comparison-slider) está pensada para imágenes y obliga a usar la arquitectura A.

**Cuándo elegir otra opción:**

- **img-comparison-slider con dos `<video>`:** si el producto ya usa React, Vue o Angular y prima la integración rápida frente a la sincronía perfecta, o si los vídeos llegan por separado y no se puede preprocesar con ffmpeg. En ese caso hay que añadir un script de resincronización (comparar `currentTime` cada X ms y corregir si la deriva pasa de ~1 frame).
- **Variante con más de dos estados** (por ejemplo original, intermedio y final): seguir la arquitectura B con `hstack=inputs=3` y un selector, tomando como referencia tekkusai/dlss5-comparison.

## 8. Despliegue y operación

- **Hosting:** cualquier hosting estático, por ejemplo Azure Static Web Apps o Azure Storage con sitio web estático. Si hay tráfico o vídeos pesados, poner **Azure Front Door o CDN** delante.
- **Servir el MP4** con `Content-Type: video/mp4` y soporte de **HTTP Range requests**. Storage y CDN lo hacen por defecto; sin Range, el seek no funciona bien.
- **CORS:** si el vídeo se sirve desde otro dominio, el canvas necesita `crossorigin="anonymous"` en el `<video>` y CORS habilitado en el origen. Si no, el canvas queda "tainted". No afecta al dibujado, pero sí a una posible exportación del frame.
- **Peso:** con clips largos, valorar CRF 23–24, una versión 720p para móvil o HLS/DASH. Para demos de 10–30 s, un MP4 con `faststart` es suficiente.
- **Autoplay:** los navegadores solo permiten autoplay si el vídeo está en silencio. El sonido se activa con la interacción del usuario.
- **Compatibilidad:** H.264 High a 3840 px de ancho (nivel 5.1) se reproduce en navegadores actuales de escritorio y móvil. Si algún dispositivo antiguo falla, usar la alternativa `vstack` (1920×2160) o bajar cada lado a 1280×720.

## 9. Fuentes

- https://codepen.io/njr-amorim/pen/PZrdrM
- https://thenewcode.com/364/Interactive-Before-After-Video-Comparison-in-HTML5-Canvas
- https://www.cssscript.com/video-comparison-slider/
- https://github.com/sneas/img-comparison-slider
- https://blog.croct.com/post/best-react-before-after-image-comparison-slider-libraries
- https://github.com/kriskbx/video-comparison.js/
- https://github.com/bluememory14/web-video-comparison
- https://github.com/chenyuntc/video-comparison-slider
- https://github.com/LiangrunDa/video-compare
- https://2600th.github.io/dlss5-video-player/
- https://www.2600th.com/work/dlss5-video-player/
- https://github.com/tekkusai/dlss5-comparison
