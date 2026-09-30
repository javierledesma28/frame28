# Marca del cliente y vídeo promocional · qué investigar y qué reforzar

Aprendido montando un tutorial promocional de Cliente A (kits de grabado; vídeo ya producido con voz en off).
Vale para cualquier vídeo que venda un producto: el montaje no decora, **refuerza el argumento de venta**.

## 1. Investiga la marca antes de decidir nada (15 minutos)

Del sitio del cliente, en este orden. Guarda el resultado en `work/brief.md` y compártelo con el usuario.

| Qué | Dónde | Para qué en el montaje |
|---|---|---|
| Qué venden y a quién | portada, "About us", colección | tono de los textos; qué producto es el protagonista |
| Promesas literales ("Everything included", "Easy to use") | portada, página de producto | frases-lema de `kinetic`/`card`: usa **sus** palabras, no las tuyas |
| Precio, descuento, qué incluye | página de producto | rótulo de producto (`lower_third`) + foto (`image`) |
| Prueba social (clientes, estrellas, reseñas, garantía) | portada, producto | `counter` o `card` antes del cierre |
| Historia y misión | "About us" | el cierre emocional, si el vídeo lo pide |
| Colores, fuente, logo | CSS de la portada | `frame28 brand from-site <url> --name <marca>` lo propone solo |

`frame28 brand from-site` baja la portada, cuenta los colores más usados, lee las variables CSS de botones
(Shopify las expone como `--color-button: r,g,b`), la fuente más repetida y el logo, y genera variantes del logo
para fondo oscuro y de acento. Revisa `brands/<marca>.json` con el usuario: el acento suele acertar (es el color de
los botones), la tinta y el tagline hay que confirmarlos. Los logos son del cliente: **no se versionan** en repos
públicos.

## 2. Qué reforzar en un promocional (checklist de storytelling)

1. **La promesa** en cuanto se dice, con sus palabras ("beginner friendly", "no guesswork"): `kinetic` corto.
2. **El producto protagonista**: nombre, precio y descuento cuando lo nombra o lo enseña; una sola vez, bien.
3. **Pasos que se pueden seguir**: "Project 1 · …", "Tape the stencil", "Speed 1 · low": cajas breves que un
   espectador podría pausar y copiar. Es lo que convierte un tutorial en "yo también puedo".
4. **El resultado**: la frase de satisfacción ("That's it!", "the perfect gift") como cinético + `draw` check.
5. **Prueba social** justo antes del cierre: "650K+ happy makers · 4.7★ · 60-day guarantee".
6. **Cierre**: si el vídeo ya trae tarjeta final de la marca, respétala; si no, `brand_card`.

Lo que **no**: repetir en un overlay lo que ya está escrito en pantalla, poner precio en cada plano, más de un
overlay grande a la vez, texto sobre el producto cuando lo están enseñando.

## 3. Vídeo ya producido (voz en off, manos, gráficos propios)

Frame28 está pensado para un plano de alguien hablando a cámara, pero trabaja igual encima de un vídeo editado:

- Sáltate `speaker`, `gestures` y `behind` (no hay cara ni gestos; el fondo cambia de plano).
- `frame28 graphics work/clip.mp4 -o work/graphics.json --annotate work/graphics.png` localiza **dónde y cuándo**
  hay texto en pantalla (marca de agua, títulos del editor, subtítulos quemados, texto impreso en objetos) y las
  tarjetas de color plano, y da la ocupación de una rejilla 3×3 con ventanas libres. Complétalo mirando la hoja de
  contacto entera (`frame28 sheet --every 4 --cols 6 --rows 9`). Tus overlays van a otra zona y a otro momento;
  `frame28 build --graphics work/graphics.json` avisa si alguno pisa un gráfico existente.
- Zonas que suelen quedar libres: franja inferior izquierda y derecha (encima de los subtítulos), centro superior.
- El fondo es claro casi siempre (mesas, telas): `kinetic` con `color` oscuro (la tinta de la marca), nunca blanco
  ni acento claro. `box` lleva fondo oscuro semitransparente y funciona en todas partes.
- Sobre la tarjeta final del cliente (fondo de su color de acento): texto en tinta, no en acento.
- Descarga el original a 1080p con `frame28 fetch <url>`; guarda el `.source.json` con el origen.

## 4. Legibilidad (reglas que salieron de los renders)

- Texto blanco solo sobre fondos oscuros o con sombra fuerte; sobre fondos claros, tinta.
- Acento sobre acento no existe: ni texto ámbar sobre tarjeta ámbar ni logo ámbar sobre fondo ámbar (usa la
  variante `on_accent` del logo, en tinta).
- Cajas en la columna derecha: hasta ~26 caracteres a 54 px desde `x` 1150; `frame28 build` avisa si una caja
  probablemente se sale del lienzo.
- Un `image` grande (producto) y un `lower_third` no pueden compartir zona: uno a cada lado.
- Los subtítulos por frase envuelven a dos líneas: deja libres los 140 px inferiores.
