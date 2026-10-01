# Cliente A · brief de marca para el montaje (ejemplo anonimizado)

Nombre en clave de una marca real de kits de grabado (EE. UU.). Los datos identificativos (nombre, fundador,
historia, web, colores exactos, logo) no se versionan: el brief real vive en `work/` (ignorado) y la marca se
regenera con `frame28 brand from-site <url>`. Este fichero conserva la **estructura** del brief y el tipo de dato
que hay que recoger, con valores difuminados, para que sirva de plantilla en el siguiente cliente.

Fuentes del brief real: home, página del producto, "about", FAQ, colección y blog de la web; el vídeo largo
(tutorial de grabado en vidrio, 3 min 17 s, inglés, ya producido con voz en off).

## Qué es la marca

Marca DTC de **kits para crear con las manos**. Empezó en otro producto artesanal, inventó un lápiz grabador
inalámbrico y lo lanzó como producto estrella; hoy vende dos familias: **grabado** (el grabador y sus kits de
proyecto: lámpara, botella, espejo, posavasos, tazas, joyería; brocas, plantillas, set de seguridad) y
**marroquinería** (kits de bolso, cartera, funda).

- **Misión**: devolver la chispa creativa haciendo las manualidades simples y divertidas.
- **Origen emocional**: una persona mayor de la familia del fundador probó el lápiz y "volvió a sentirse niña".
- **Concepto**: proyectos cortos de principio a fin, "sin lío, sin estrés".
- **Promesas**: "todo incluido, sin herramientas extra ni adivinanzas" · "impresionante desde el primer día" ·
  "fácil, perfecto para principiantes" · "una experiencia relajante" · "haz únicos los objetos corrientes".
- **Prueba social**: cientos de miles de clientes, ~4,7★ con más de diez mil reseñas, más de un millón de
  creaciones. Garantía de devolución de 60 días, 1 año de garantía, atención 24/7. (Las cifras exactas se toman
  de la web el día del montaje; nunca se inventan ni se redondean hacia arriba.)
- **Taglines**: una para la home ("elige tu manualidad, hazla tuya") y otra para el producto ("grabar, fácil").

## El producto que vende este vídeo: Engraver Pro™ (nombre en clave)

- Precio ~60 $ (antes ~90 $, **30 % off**). Inalámbrico, ~50 g, ~12 cm, USB-C, ~2 h por carga.
- 3 velocidades, 8 000–21 000 rpm.
- En la caja: fresa de carburo, **30 brocas de diamante** (regalo), lienzos de práctica (acrílico, bambú,
  eco-piel, aluminio), plantillas, guía rápida, ebook.
- Materiales: madera, vidrio, metal, piedra, plástico, piel (dureza < 4 Mohs).
- **Para vidrio**: brocas de diamante; la FAQ recomienda humedecer; el kit de lámpara de botella es el proyecto natural.

## Colores, tipografía y logo (del CSS del sitio)

| Uso | Valor |
|---|---|
| Acento / botones | un ámbar cálido y sus secundarios (naranja, amarillo pálido) |
| Tinta / fondos oscuros | un marrón muy oscuro, casi negro |
| Verde de apoyo | un verde azulado |
| Claros | blanco, gris claro, crema |
| Fuente | una geométrica redondeada (Google Fonts) |
| Logo | wordmark horizontal en el acento sobre transparente; variante oscura para fondo de acento |

`frame28 brand from-site` saca estos valores del CSS y del logo de la web y los deja en `work/brands/cliente-a.json`.

## Qué debe potenciar el montaje

El vídeo es un **tutorial promocional**: enseña a grabar vidrio para demostrar que *cualquiera puede* con el
grabador. El storytelling que hay que reforzar, en este orden:

1. **Facilidad**: "lo único que necesitas" → una lista corta de material (pizarra o `list_focus`), y callouts en
   cada objeto cuando lo muestra.
2. **El producto como protagonista**: rótulo con nombre y precio con descuento cuando aparece el grabador;
   `pointer` a la broca de diamante y a la velocidad cuando las mencione.
3. **Pasos numerados**: cada paso del tutorial con `box` "1 · …", "2 · …" para que el espectador lo siga.
4. **Resultado "impresionante desde el primer día"**: al final, el antes/después y la frase-lema en `card`.
5. **Confianza**: clientes, estrellas y garantía → contadores o tarjeta antes del cierre.
6. **Cierre con marca**: `brand_card` con logo, tagline y web.

Tono: cálido, cercano, sin tecnicismos; el acento cálido sobre fondo oscuro; la fuente de la marca.
