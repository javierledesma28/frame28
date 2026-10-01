# Cómo se monetiza Frame28 · análisis y recomendación (2026-09-30)

Pregunta del usuario: "¿es mejor mantenerlo como plugin, montarlo como producto dentro de una plataforma, o ya me
dirás tú?". Este documento dimensiona los tres caminos con lo que existe hoy, recomienda uno y deja las decisiones
que solo puede tomar Javier. Las cifras de mercado y de coste son órdenes de magnitud a verificar antes de fijar
precios; las de esfuerzo salen del ritmo real del proyecto (tres versiones en dos días con un solo desarrollador
asistido por Claude Code).

## 1. Qué hay hoy (activos y dependencias)

| Activo | Estado | Peso en la decisión |
|---|---|---|
| Plugin MIT público con ocho skills y CLI de 38 órdenes | v0.3.0 publicada, probado en cinco casos reales | Lo abierto ya no se cierra: retirar la licencia no retira lo publicado |
| Conocimiento de dirección (qué poner en pantalla, ganchos, marca, zonas seguras) | Vive en las skills y sus referencias | Es lo difícil de copiar; HeyGen, video-use y OpenMontage cubren la mecánica, no el criterio |
| Pipeline local en CPU: 2–14 min por vídeo, sin coste de nube | Funciona en Windows; macOS sin probar en máquina real | Un servicio puede operarse desde un portátil; una plataforma exige servidores |
| Caso Cliente A: vídeo largo, tres shorts, portada, versión en español | Entregable listo para enseñar | Es el material de venta para marcas DTC |
| Marca Think28, web, instaladores para no técnicos | Publicado en frame28.t28.io | La adopción del plugin ya tiene canal |
| Dependencia de Claude Code | El "director" es Claude con las skills; cada usuario del plugin necesita su propia cuenta | Para un servicio basta la cuenta de Think28; para una plataforma el director pasa a la API |
| Tiempo disponible | Proyecto personal de alguien con un puesto a jornada completa | Es la restricción real: descarta lo que exija operar infraestructura a diario |

## 2. A quién le sirve y qué compra cada uno

| Segmento | Qué quiere | Qué compra | Encaje |
|---|---|---|---|
| Marcas DTC y pymes con producto (tipo Cliente A) | Vídeos que vendan, cada semana, sin aprender nada | El vídeo terminado: largo, shorts, portada, idiomas | Servicio, y a medio plazo plataforma |
| Fundadores y equipos técnicos que ya usan Claude Code | Montar sus propios clips sin editor | El plugin (gratis) y, quizá, marca y plantillas premium | Plugin abierto |
| Agencias y freelances de vídeo | Producir más en menos horas | Herramienta con licencia de uso comercial y soporte | Plugin más formación o licencia de equipo |
| Equipos de marketing con alguien técnico | Volumen de variantes para anuncios | Servicio o plataforma con cuentas | Plataforma, cuando exista |

El segmento que paga más rápido y con menos fricción es el primero: no quiere una herramienta, quiere el vídeo.
Es el que ya tenemos demostrado con el Cliente A.

## 3. Los tres caminos, dimensionados

### A. Plugin abierto y valor alrededor

El plugin y el CLI siguen MIT. Se cobra por lo que rodea al plugin: paquetes de marca y plantillas por sector,
bibliotecas de ganchos, formación para agencias, consultoría de montaje.

| | |
|---|---|
| Tiempo hasta el primer ingreso | Semanas (un paquete de marca o una formación se venden en cuanto hay demanda) |
| Inversión | Casi nula: cero infraestructura; el trabajo es contenido y difusión |
| Ingreso potencial | Bajo y discontinuo: el plugin no factura por sí mismo; los complementos son de decenas a pocos cientos de euros |
| Riesgo | Que HeyGen (skills oficiales de HyperFrames) o herramientas similares hagan lo mismo gratis; que el público técnico sea pequeño |
| Qué aprende | Adopción y qué técnicas se usan, si se instrumenta |
| Dependencia de Claude | Cada usuario paga su Claude Code; Think28 no interviene |

Sirve como canal de adopción y credibilidad. No sirve como negocio principal.

### B. Producto en plataforma

Una web donde el cliente sube el clip, revisa una propuesta y recibe el vídeo. Requiere render en servidor
(Chrome headless, ffmpeg, modelos en CPU o GPU), colas, almacenamiento, cuentas, pagos y una interfaz sobre el
storyboard; el director pasa a ser la API de Claude con las skills como prompts.

Dimensionado del mínimo vendible, para una persona a tiempo parcial:

| Bloque | Qué incluye | Esfuerzo estimado |
|---|---|---|
| Entrada y cuentas | Subida del clip, brief de marca, autenticación, pagos con Stripe | 2–3 semanas |
| Render en servidor | Workers con el CLI actual, cola, almacenamiento, límites de tiempo, reintentos | 2–3 semanas |
| Director por API | Las skills convertidas en prompts y herramientas sobre la API; control de coste por vídeo | 2 semanas |
| Revisión y entrega | Ver la hoja de contacto, pedir cambios sobre el storyboard, descargar; notificaciones | 4 semanas o más |
| Operación | Monitorización, costes de nube, soporte, actualizaciones de modelos y de HyperFrames | Continua |

Total: del orden de tres a cuatro meses a tiempo completo, seis o más a tiempo parcial, antes del primer cliente.
Coste fijo de nube: un worker de CPU siempre encendido ronda el centenar de euros al mes; con GPU, varios cientos.
Coste variable por vídeo: la API de Claude (a medir: hoy el director consume tokens de la suscripción de Claude
Code, no hay cifra) más minutos de cómputo.

Compite con Descript, Opus Clip, Captions, Submagic, Veed y CapCut, que cobran suscripciones de entre diez y
cincuenta dólares al mes por usuario y ya tienen distribución. La diferencia de Frame28 (dirección con criterio,
overlays de venta, marca del cliente, todo desde la voz) hay que demostrarla con clientes antes de construir esto.

### C. Servicio de montaje operado por Think28

Think28 monta los vídeos con Frame28 como herramienta interna y vende el resultado: por vídeo o por cuota mensual
con un número de piezas (largo, shorts, portada, versión en otro idioma). El cliente no instala nada.

| | |
|---|---|
| Tiempo hasta el primer ingreso | Días o semanas: el caso del Cliente A ya es la demo |
| Inversión | Una página de oferta, un formulario y dos o tres vídeos de muestra para marcas objetivo |
| Ingreso potencial | Medio y recurrente: cuotas mensuales por marca; el margen viene de que el montaje está automatizado |
| Riesgo | Es un negocio de servicios: escala con horas de Javier; necesita vender; cada cliente pide algo distinto |
| Qué aprende | Lo que de verdad importa: disposición a pagar, qué piezas se usan, qué falla, cuánto cuesta cada vídeo |
| Dependencia de Claude | Solo la cuenta de Think28; revisar que los términos vigentes permiten el uso profesional que se hace |

Cada vídeo de cliente deja conocimiento que, por regla del proyecto, se incorpora al plugin. El servicio financia
y valida la plataforma en vez de apostar por ella a ciegas.

## 4. Comparación

| Criterio | A. Plugin abierto | B. Plataforma | C. Servicio |
|---|---|---|---|
| Primer ingreso | Semanas | Meses | Días o semanas |
| Inversión inicial | Mínima | Alta | Baja |
| Ingreso a un año | Bajo | Alto si funciona, cero si no | Medio, recurrente |
| Escala | Limitada por el nicho técnico | Alta | Limitada por horas |
| Riesgo de construir lo que nadie compra | Bajo | Alto | Bajo |
| Cabe con un trabajo a jornada completa | Sí | Difícil | Sí, con pocos clientes |
| Lo que enseña sobre el mercado | Poco | Tarde | Mucho y pronto |

## 5. Recomendación: híbrido por fases

1. **Ahora: servicio (C) con el plugin abierto (A) como canal.** El plugin sigue público y es la demo viva; Think28
   vende vídeos montados a dos o tres marcas de referencia, el Cliente A la primera. Todo lo aprendido se capitaliza en
   el plugin, que mejora para ambos canales a la vez.
2. **Con datos: decidir la plataforma (B).** Solo si el servicio muestra demanda recurrente y el cuello de botella
   es la entrega, no la venta. Entonces la v1.0.0 del roadmap (interfaz sobre el storyboard, director por API) deja
   de ser condicional. Si el cuello de botella es la venta, la plataforma no lo arregla.
3. **Lo que no hacer:** cerrar la licencia (no sirve de nada y rompe la confianza) o construir la plataforma antes
   de cobrar el primer vídeo.

### Plan de 90 días

| Semanas | Qué | Resultado que lo cierra |
|---|---|---|
| 1–2 | Definir la oferta (qué piezas, plazo, precio de lanzamiento) y una página en frame28.t28.io con formulario. Montar dos vídeos de muestra para marcas objetivo con material público suyo. Cerrar la v0.4.0 hasta donde afecte al servicio: pruebas, B-roll real, coste por vídeo | Página publicada, dos muestras, coste por vídeo medido |
| 3–8 | Tres clientes piloto a precio de lanzamiento. Cada entrega deja mejoras en el plugin y una cifra de horas y tokens | Tres marcas facturadas, tiempo por vídeo por debajo de un umbral fijado |
| 9–12 | Con los datos, decidir: seguir en servicio y plugin, o diseñar la plataforma mínima. Ajustar precios y roadmap | Decisión escrita con números; roadmap v1.0.0 abierto o aparcado |

## 6. Precios: hipótesis para validar, no tarifas

Órdenes de magnitud del mercado a septiembre de 2026, para situar la oferta (verificar antes de publicar precios):
un editor freelance cobra decenas de euros por short y de cientos a más de mil por un vídeo largo montado; las
herramientas SaaS de subtítulos y clips cobran entre diez y cincuenta dólares al mes por usuario; una agencia de
contenido cobra cuotas mensuales de cuatro cifras.

Hipótesis de oferta para el servicio: paquete mensual por marca con un vídeo largo, tres a cinco shorts con
variantes de gancho, portada y una segunda lengua, en la franja de cientos a pocos miles de euros al mes según
volumen, con un precio de lanzamiento para los pilotos. El coste de producción hoy es tiempo de revisión más
minutos de CPU; el registro de coste por vídeo previsto en la v0.4.0 es lo que permite fijar el precio con margen.

## 7. Licencias y términos que condicionan el uso comercial

| Pieza | Licencia | Servicio | Plataforma |
|---|---|---|---|
| Frame28 (plugin y CLI) | MIT | Sí | Sí |
| HyperFrames | Apache-2.0 | Sí | Sí |
| GSAP 3.13+ y plugins | Gratis, uso comercial incluido | Sí | Sí |
| faster-whisper y pesos de Whisper | MIT | Sí | Sí |
| RobustVideoMatting | GPL-3 | Sí, ejecutado como proceso aparte y sin redistribuir | Sí, mismo criterio; no es AGPL |
| MediaPipe, RapidOCR, segno | Apache y BSD | Sí | Sí |
| Pexels y Pixabay | Licencias propias, comercial sin atribución | Sí, con la licencia guardada por vídeo | Sí, revisar límites de la API |
| Kokoro (TTS previsto) | Apache; espeak-ng GPL como proceso | Sí | Sí |
| Claude Code y API de Claude | Términos de Anthropic vigentes | Revisar que la suscripción cubre el uso profesional | API con coste por token |

Nada de lo anterior bloquea el servicio. Para la plataforma, el único cambio de fondo es pasar el director de la
suscripción a la API.

## 8. Decisiones que solo puede tomar Javier

1. **Segmento inicial:** marcas DTC con producto físico (recomendado, es el caso probado), o fundadores de
   software (pide la demo de pantalla con zoom antes).
2. **Oferta y precio de lanzamiento:** paquete mensual o pago por vídeo; cuánto para los tres pilotos.
3. **Qué sigue abierto:** todo (recomendado) o reservar las referencias de dirección y marca para clientes.
4. **Quién opera:** Think28 con Javier revisando cada vídeo, o un colaborador formado con la guía.
5. **Marca de la oferta:** Frame28 como producto de Think28 (coherente con lo publicado) o servicio bajo Think28
   sin nombrar la herramienta.
6. **Umbrales para la plataforma:** cuántos clientes recurrentes y qué tiempo por vídeo justifican construirla.

## 9. Qué cambia en el roadmap con esta recomendación

- La v0.4.0 se orienta al servicio: pruebas (fiabilidad al entregar a terceros), B-roll real, coste por vídeo,
  variantes de gancho en lote, marcadores de resultado y doblaje para clientes con varios mercados.
- La v0.5.0 mantiene calidad y alcance; la demo de pantalla sube de prioridad solo si el segmento elegido es
  software.
- La v1.0.0 (interfaz, director por API, cuentas y pagos) queda condicionada a los datos del servicio.
- El primer ítem de trabajo es la suite mínima de pruebas: es lo que hace que entregar a un cliente no dependa
  de mirar la hoja de contacto con suerte.

## Fuentes y supuestos

- Estado del proyecto: `HANDOFF.md`, relevamiento del 2026-09-30, `research/04-roadmap-features.md` y
  `research/05-video-venta-diy.md` (con sus fuentes de mercado sobre ganchos, UGC y fatiga de creativos).
- Precios de herramientas y de edición: conocimiento general del mercado a la fecha, sin consulta específica en
  esta sesión; verificar antes de publicar cualquier tarifa.
- Costes de nube: experiencia con Azure del autor; el coste por vídeo en API de Claude no está medido todavía.
