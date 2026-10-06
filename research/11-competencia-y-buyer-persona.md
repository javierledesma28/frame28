# Competencia y buyer persona de Frame28 (2026-10-03)

Investigación en internet hecha el 2026-10-03 en cuatro frentes, en paralelo:

1. Competidores dentro de los agentes de código: plugins, skills y servidores MCP de vídeo.
2. SaaS de vídeo con IA que resuelven el mismo trabajo.
3. Productos que guardan la marca para la IA, el equivalente de nuestra Memoria de marca.
4. Quién compra y cuánto mercado hay.

**[H]** marca un hecho con fuente (URL al final de cada sección o en la tabla); **[I]** marca una inferencia nuestra. Las
estrellas de GitHub se leyeron ese día con `gh api`. Los precios son los públicos en USD/mes con pago mensual; si la página
oficial no cargó, se dice.

Complementa a `research/08` (plataforma, precios vigentes en §11): **este documento no cambia precios**, propone qué validar.

---

## 0. En diez líneas

1. **Recortar, subtitular, reencuadrar y renderizar ya es gratis o casi gratis.** HyperFrames, video-use y Remotion son
   gratuitos; Reap cobra desde 10 USD y OpusClip desde 15 USD. Eso no se puede cobrar.
2. **El canal tampoco es exclusivo.** OpusClip publica plugin para Claude Code y Codex con cuenta y créditos (nuestro mismo
   modelo de negocio), y Cardboard, Creatify, Descript, Reap, invideo, HeyGen y Runway ya están en Claude por MCP.
3. **La «memoria de marca por MCP» tampoco es un foso por sí sola.** Jasper, Canva, Adobe y proyectos MIT ya la sirven.
4. **Lo que nadie junta es lo nuestro:** montaje de **metraje real** de alguien hablando a cámara, **con criterio de
   marca y de campaña**, que entrega **el paquete completo**:
   - el largo, los shorts con variantes de gancho y la portada;
   - los idiomas con los mismos tiempos y el copy de publicación;
   - todo **en local**, sin subir el vídeo ni usar claves de terceros.
5. **La mayor amenaza es nuestro propio proveedor.** HeyGen ya publica `talking-head-recut` y `embedded-captions`
   (texto detrás del hablante, en local) en el plugin de HyperFrames, con 56.000★.
6. **Lo que falta y en el resto del mercado ya viene de serie:** doblaje de voz, publicación o programación en redes y
   revisión con aprobación por enlace.
7. **Ideas que conviene copiar:** que la Memoria arranque sola desde la web y desde un vídeo, voz aprendida de ejemplos,
   nota de marca sobre el resultado y aprender de los datos reales de las plataformas.
8. **Precio:** Creator (79) cuesta entre 2 y 5 veces lo que un recortador de clips. Brand (199) y Agency (499) son baratos
   frente a un editor o una agencia (2.000–5.000 USD/mes), que es su comparación real.
9. **Foco de los próximos 6 meses: la marca DTC «educativa»**, el perfil del Cliente A. Entra por Studio y se queda en
   Brand. **La agencia pequeña** es el canal en paralelo. El creador individual se aparca.
10. **Hay que verificar pronto** si Frame28 puede usarse desde **Cowork** o desde la app de escritorio de Claude sin
    terminal: es por donde Anthropic mete a los no programadores.

---

## 1. El mapa: cuatro capas de competencia

| Capa | Quién | Qué cobra | Relación con Frame28 |
|---|---|---|---|
| **A. Motores y skills gratis** | HyperFrames (HeyGen), Remotion, video-use, toolkit de Digital Samba, MCP de ffmpeg | Nada; Remotion cobra licencia de empresa a partir de 3 personas | Comoditizan la mecánica de montar. Son la base de nuestra calidad, no nuestro valor |
| **B. SaaS de clips y edición, ya con MCP o plugin** | OpusClip, Descript, Reap, invideo, Cardboard, Creatify, HeyGen, Runway, Submagic, Vizard, Klap, Kapwing, Riverside, Captions, VEED, CapCut/Pippit, Gling, Eddie, Mosaic, Rask, Arcads | 10–250 USD/mes por créditos o minutos | Competencia por el mismo trabajo. Suben el vídeo a su nube |
| **C. Memoria de marca para la IA** | Jasper, Typeface, Writer, Copy.ai, Canva, Adobe GenStudio, Google Pomelli, HubSpot Breeze, Omneky, Holo, brandsystem-mcp | 0 (Pomelli) – enterprise | Validan la categoría y le quitan el estatus de foso. Ninguno está pensado para vídeo a cámara |
| **D. Personas** | Editor freelance (75–200 USD por short), agencia de short-form (1.500–5.000 USD/mes) | Horas | **La comparación real de Brand, Agency y Studio** |

### 1.1 Competidores directos dentro de los agentes de código

| Nombre | Qué hace bien | Qué le falta frente a Frame28 | Licencia / precio | Tracción |
|---|---|---|---|---|
| **HyperFrames (HeyGen), plugin oficial** | 21 skills. `talking-head-recut`: rótulos, datos y citas sincronizados con la transcripción. `embedded-captions`: recorta al sujeto en local y pone texto detrás, sin API key | Por diseño no hace cortes ni reencuadre, y admite un solo hablante. No tiene marca ni shorts con variantes, ni i18n ni copy | Apache-2.0, gratis | **56.127★**, actividad diaria |
| **video-use** (browser-use) | De la carpeta de brutos a `final.mp4` charlando: quita muletillas, corrige color, subtitula. Se autoevalúa (hasta 3 re-renders) y tiene memoria por proyecto | Exige clave de ElevenLabs para transcribir. Sin marca persistente, variantes, portada ni i18n | MIT, gratis + ElevenLabs | **27.930★** en 6 meses |
| **OpusClip AI Producer, Video Tools y MCP** | Plugin MIT para Claude Code, Codex y ChatGPT, más 43 plantillas de lanzamiento. El MCP tiene 27 herramientas: recorte viral, reencuadre, plantillas de marca, **programación en redes** | Nube cerrada. Sin texto detrás del hablante, gestos ni montaje a medida | Plugin gratis + créditos | Repo de 3 semanas, 4★; la marca es conocida |
| **Descript MCP** | Transcribe, quita muletillas, Studio Sound, highlight reels, SRT | No descarga el vídeo sin publicarlo antes. Sin gráficos de marca | Créditos del plan de Descript | Está en el directorio de conectores de Claude |
| **Reap MCP** | Recorte, subtítulos en más de 100 idiomas, **doblaje en más de 80 con alineación labial** | No hace montaje creativo | Gratis 1 h; desde 9,99 USD/mes | n/d |
| **invideo MCP** (2026-09-30) | El agente edita **en vivo** una línea de tiempo multipista; exporta a Premiere, FCP y Resolve | Sin memoria de marca ni método | Editor gratis + créditos | Recién anunciado |
| **HeyGen MCP y skills** | Traducción a más de 175 idiomas con clon de voz y labios | Genera un avatar; no monta tu clip | Créditos de HeyGen | 461★ (skills) |
| **Remotion Agent Skills** | La referencia de vídeo programático (12 skills) | Crea vídeo desde cero; no monta un vídeo a cámara | Licencia de empresa | 4.822★ (skills) |
| **Cardboard** | «Agentic video editor» integrado con Claude Code y Codex; B-roll, motion graphics y clonado de voz | n/d sobre marca e idiomas | 8–250 USD/mes | n/d |
| **Long tail** (adukhan98, nextwork, mehdiagent…) | Ideas: brand kit desde PDF con tablero aprobable; imitar el estilo de un creador midiendo ritmo y zooms | Poco mantenimiento | MIT | 0–6★ |

El marketplace oficial de plugins de Anthropic no lista plugins de vídeo [H]. Se distribuyen por marketplaces propios y
directorios comunitarios.

Fuentes: [hyperframes](https://github.com/heygen-com/hyperframes) ·
[talking heads](https://hyperframes.heygen.com/prompting/captions-and-talking-heads) ·
[video-use](https://github.com/browser-use/video-use) · [remotion skills](https://github.com/remotion-dev/skills) ·
[ai-producer](https://github.com/opus-pro/ai-producer-plugin) · [opus mcp](https://www.opus.pro/mcp) ·
[descript mcp](https://help.descript.com/api-and-mcp/mcp) · [reap mcp](https://reap.video/mcp) ·
[invideo mcp](https://invideo.io/news/introducing-invideo-mcp/) · [heygen skills](https://github.com/heygen-com/skills) ·
[cardboard](https://www.cardboard.ai/) · [toolkit](https://github.com/digitalsamba/claude-code-video-toolkit) ·
[adukhan98](https://github.com/adukhan98/video-edit) · [nextwork](https://github.com/nextwork-projects/ai-video-editor)

### 1.2 SaaS de vídeo con IA (precio público, entrada / equipo)

| Producto | Entrada / equipo (USD/mes) | Marca | Idiomas | Ganchos | Para quién |
|---|---|---|---|---|---|
| OpusClip | 15 / 29 (2–4 usuarios) | Plantillas | Doblaje desde Pro | Virality score | Creadores, podcasts |
| Submagic | 19 / 69 | Plantillas | Subtítulos traducidos | AI hook titles | Creadores, agencias de shorts |
| Descript | 24 / 65 | Brand Studio en Business | 61 subtítulos, 30 doblaje | «viral moments» | Podcasts, formación |
| Vizard | 29 / 39 (terceros) | Brand kit en Business | Subtítulos | No | Equipos sociales |
| Klap | 29 / 189 | Brand kit | Doblaje 29 (terceros) | Sí | Creadores |
| Kapwing | 24 / 64 | Brand kit desde Pro | 60+ | No | Equipos de marketing |
| Riverside | 29 / 39–99 | Solo Business | Solo Business | No | Podcasts, webinars |
| Creatify | 39 / 99 | Brand Spaces | 75+ | No | Anunciantes de rendimiento |
| HeyGen | 29 / 149 + 20 por asiento | Solo Business | 175+ | No | Marketing, formación |
| Rask | 39 / 249 | **Glosario de marca** en Business | 135+, voz en 32 | No | Localización |
| Mosaic | 50 / 150 (página caída; buscador) | — | — | A/B de variantes | Agencias, medios |
| Gling · Eddie | 20 / 100 · créditos 10–350 | — | — | — | YouTubers, productoras |

VEED, CapCut, Pippit, Arcads y Captions tienen precios cambiantes o páginas que no cargaron: ver la investigación
original. Munch ha pivotado a gestión de redes.
Fuentes: [opus](https://www.opus.pro/pricing) · [submagic](https://www.submagic.co/pricing) ·
[descript](https://www.descript.com/pricing) · [kapwing](https://www.kapwing.com/pricing) ·
[creatify](https://creatify.ai/pricing) · [heygen](https://www.heygen.com/pricing) · [rask](https://www.rask.ai/pricing) ·
[riverside](https://riverside.com/pricing) · [gling](https://www.gling.ai/pricing) · [eddie](https://www.heyeddie.ai/pricing)

**Quejas recurrentes [H], que son argumentos para nosotros:**

- **Facturación y bajas.** Cargos después de cancelar y soporte inaccesible (Opus 4,0 en Trustpilot; Submagic; VEED).
- **Créditos opacos que se gastan en fallos.** Pasa con HeyGen, Captions y el cambio de Descript a créditos en 2025. Opus,
  además, cobra por los minutos del vídeo de entrada.
- **Cortes malos.** Clips que cortan el remate o empiezan a mitad de idea (Opus, Magic Clips).
- **Resultados genéricos** sin plantillas propias.
- **Privacidad.** Los términos de CapCut de junio de 2025 dan una licencia perpetua sobre la imagen y la voz. HeyGen
  entrena con los datos de los clientes salvo en Enterprise.

Fuentes: [trustpilot opus](https://www.trustpilot.com/review/opus.pro) ·
[trustpilot submagic](https://www.trustpilot.com/review/submagic.co) ·
[trustpilot captions](https://www.trustpilot.com/review/captions.ai) · [eesel opus](https://www.eesel.ai/blog/opusclip-reviews) ·
[dpreview capcut](https://www.dpreview.com/news/1239418455/capcut-video-editing-app-s-new-terms-spark-rights-concerns-we-asked-a-lawyer-for-guidance/) ·
[sonix descript](https://sonix.ai/resources/descript-pricing/)

### 1.3 Memoria de marca en el mercado

| Producto | Qué guarda | Aprende del rendimiento | API / MCP | Precio |
|---|---|---|---|---|
| Jasper IQ | Voz, Style Guide (sustituye términos), Knowledge, **Audiences**, guías visuales | No | **MCP** desde 2025-09 (Business) | 69/asiento; Business a medida |
| Typeface | **Voz por canal**; tono aprendido de textos; *brand linting* de la propia guía | n/d | n/d | Enterprise |
| Writer | Voz por departamento, vocabulario obligatorio y prohibido, **guardrails legales** | n/d | API en Enterprise | A medida |
| Canva | Brand Kit + Brand Voice (resumen, Do y Don't) | No | **MCP oficial** con Brand Kit | Pro/Teams |
| Adobe GenStudio | Brands, Products, **Personas**; reglas sacadas de un PDF; **nota de cumplimiento** | **Sí**: atributos creativos ligados a conversiones | MCP para Claude y ChatGPT | Enterprise |
| **Google Pomelli** | «Business DNA» **sacado de la web** o de 20 ficheros; genera un **Brand Book**; anima con Veo | No consta | No consta | **Gratis (beta)** |
| HubSpot Breeze | Voz entrenada con blogs y emails; identidad sacada del dominio (sentimiento, competidores) | Datos del CRM | n/d | Professional+ |
| Omneky | «Brand LLM» con lo que ya rindió | **Sí**: Meta y Google | Anuncia MCP | Desde 99 (terceros) |
| brandsystem-mcp (MIT) | Tokens con nivel de confianza, personas, `brand_check_compliance` (0–100) | — | MCP | Gratis |

Fuentes: [jasper mcp](https://www.jasper.ai/mcp) · [typeface](https://www.typeface.ai/product/brand-agent) ·
[writer](https://writer.com/plans) · [canva connector](https://www.canva.com/ai-connector) ·
[adobe insights](https://business.adobe.com/products/genstudio/performance-marketing/insights.html) ·
[pomelli](https://support.google.com/labs/answer/17090488) ·
[hubspot](https://knowledge.hubspot.com/branding/generate-your-brand-identity-context-with-ai) ·
[omneky](https://www.omneky.com/llm) · [brandsystem-mcp](https://github.com/Brandcode-Studio/brandsystem-mcp)

### 1.4 Actualización del 2026-10-06 (mapa R1 de Research)

Segunda pasada, tres días después: 88 repositorios por la API de GitHub, 60 productos de pago en su página de precios,
17 servicios de edición humana y 15 ofertas de empleo de marcas DTC. El detalle, con URL y hora de cada cifra, está en el
informe interno R1 (`frame28-backlog/informes/research/2026-10-06-mapa-competencia.md`). Lo que cambia respecto a lo de
arriba:

**Capa A, gratis y abierto.** Dos grandes que no estaban en el mapa, los dos **AGPL-3.0** (no se pueden integrar en
un motor MIT; sí mirar y, en todo caso, llamar como servicio externo):

| Repo | ★ (06-10) | Qué hace | Qué le falta |
|---|---|---|---|
| [OpenMontage](https://github.com/calesthio/OpenMontage) | 64.649 | Sistema agéntico de producción: 12 pipelines (uno «Talking Head» de metraje real, otro «Localization & Dub», otro «Podcast → clips»), 60+ proveedores, 700+ ficheros de skills; compone con Remotion o HyperFrames | Marca persistente, campañas, variantes de gancho, idiomas con los mismos tiempos; 357 issues abiertas |
| [VoiceStudio](https://github.com/debpalash/VoiceStudio) | 54.199 | «ElevenLabs en local»: clon y diseño de voz, doblaje de vídeo con voz temporizada, MCP | No monta vídeo |
| [hyperframes-student-kit](https://github.com/nateherkai/hyperframes-student-kit) | 1.201 | 15 skills: cortes por transcripción, plan narrativo, short-form 9:16 con subtítulos y B-roll | Marca, cuenta, idiomas; transcripción con ElevenLabs |
| [Orkas VideoStudio](https://github.com/Orkas-AI/Orkas-VideoStudio) | 497 | `plan.json` editable y re-renderizable (el mismo contrato que nuestro storyboard): cortes, silencios, subtítulos, doblaje, highlights; CLI y MCP | Marca y método; un autor |
| [hotclip](https://github.com/xixihhhh/hotclip) | 296 | Largos → shorts 9:16 con highlights por IA, todo en local, MCP (AGPL) | Mercado chino |

**HyperFrames** publicó 25 versiones entre el 3 y el 6 de octubre, casi todas de **Studio** (su editor gráfico) y de la
app de escritorio «para editar por chat»; `media-use` suma voces de HeyGen. Sin skill nueva de cortes ni reencuadre:
HeyGen va hoy a por el usuario sin terminal, no a por el montaje. El plugin de OpusClip y video-use, sin commits desde
el 30-09 y el 02-10.

**Capa B, SaaS.** Entrada de los recortadores 15–29 USD/mes y 12–14,5 pagando el año; 12 de 25 cobran por créditos
ligados a los minutos subidos (solo OpusClip documenta devolverlos si falla); **9 de 24 ya tienen MCP, plugin o skills
para agentes** (eran 5 el 03-10): la ventana de «el primero en Claude Code» se cerró. Trustpilot separa dos mundos: los
recortadores especializados aguantan (Vizard 4,7; Submagic 4,5; Captions 4,4; OpusClip 4,0) y los editores con IA no
(CapCut 1,2; Runway 1,1; Adobe 1,1; InVideo 1,8; Kapwing 1,9; Descript 2,6). Declaran entrenar con el contenido del
cliente HeyGen (planes de pago), Runway, Riverside, Pippit, VEED Free, Captions, Wisecut, Munch y Descript (salvo
opt-out); a confirmar en sus términos antes de usarlo como argumento. **Doblaje**: integrarlo por API cuesta 0,33–2,20
USD por minuto (ElevenLabs, Rask, Vozo, HeyGen) o nada en local con VoiceStudio. **Render por API**: el mercado paga
5–20 céntimos por minuto renderizado (Shotstack, Creatomate, json2video), el ancla para la fase Cloud. InVideo da a su
MCP exportación a Premiere, Final Cut y Resolve: la forma literal de «el editor da el acabado».

**Capa D, personas (la comparación real).** Edición humana por suscripción 899–2.499 USD/mes, es decir, 21–60 USD por
short (80–94 por pieza); freelance 75–300 por vídeo (a confirmar: Upwork y Fiverr no se dejaron leer); agencia DTC
1.500–20.000 al mes solo en creatividad; equipo interno de tres, 26.000–41.000. Una marca con 5–15 k de inversión
mensual en anuncios necesita 12–20 creatividades nuevas al mes y la fatiga creativa llega a las 3–4 semanas. En 13
ofertas de empleo de marcas DTC, **Premiere aparece en las 13 y CapCut en 9**; la IA, como extra (Submagic u OpusClip,
ElevenLabs, HeyGen o Rask). Consecuencia para los precios de §4: Brand (199) es una quinta parte de lo habitual; Studio
(990 / 2.490) cuesta lo mismo que una suscripción de edición humana y tiene que ganar por marca, idiomas y ganchos.

**Capa C.** Sin novedad de fondo: Pomelli publica directo en Instagram y anima con Veo; Canva declara 3,7 M de usuarios
de su MCP; Munch y Eddie añaden «contexto de marca por workspace» (texto libre). La Memoria específica de vídeo sigue sin
competidor directo.

---

## 2. Qué es nuestro y qué no

| Comoditizado (no se cobra) | Diferencial (se cobra) |
|---|---|
| Transcripción, recorte por silencios, subtítulos por palabra, render | **El criterio**: Memoria de marca **específica de vídeo** (ganchos puntuados, glosario y CTA por idioma) + **campañas** servidas por MCP con login y por plan |
| Shorts verticales con reencuadre | **El paquete completo con un solo criterio**: largo + shorts con 2 variantes de gancho + portada + idiomas con los mismos tiempos + copy |
| Texto detrás del hablante (HyperFrames ya lo regala) | **Callouts guiados por gestos** (MediaPipe): no lo encontramos en nadie |
| Brand kit visual (colores, logo, fuentes) | **Local de verdad**: el vídeo no sale del ordenador y no hay claves de terceros ni créditos que se gasten al regenerar |
| «Memoria de marca por MCP» genérica | **Panel para agencias** con varias marcas y control por plan, para agentes |
| Plugin de Claude Code (OpusClip ya lo tiene) | **El estudio de prompting**: claridad del prompt, notas del productor y prompts para completar lo que falta |

**[I]** El mensaje de venta tiene que hablar del resultado y del criterio, no de «edita con Claude».

---

## 3. Qué adoptar, por prioridad

Cada fila dice dónde cae en nuestro producto (CLI y plugin en este repo; estudio, API y MCP en `frame28-app`).

### Ahora: antes de vender Brand en serio (0–6 semanas)

| # | Qué | Por qué | Dónde |
|---|---|---|---|
| 1 | **Memoria que arranca sola**: URL de la web (+ 1 vídeo publicado) → borrador de la Memoria para *revisar*, con cada campo marcado como inferido o confirmado | Pomelli, Holo y HubSpot dan el primer valor en un minuto. `brand from-site` ya existe | CLI `brand from-site` + tarea `memoria` + estudio (botón «Empezar desde mi web») |
| 2 | **Nota de marca sobre el storyboard** antes del render: voz, palabras prohibidas, glosario, legal, contraste, zonas seguras | Adobe y brandsystem puntúan el resultado; nuestra «claridad» solo puntúa el prompt | CLI (`storyboard validate` / `check`) + resultado visible en la campaña |
| 3 | **Argumentos de venta que ya tenemos**: privacidad local, sin créditos que se gasten al fallar, cortes en frases completas (antes/después), baja en un clic con aviso de renovación | Son las quejas recurrentes del mercado | Landing y condiciones (Paddle) |
| 4 | **Probar Frame28 en Cowork y en la app de escritorio sin terminal** | Es la puerta de Anthropic para los no programadores; si no funciona, P1 depende de Studio | Spike del plugin |

### Próximo trimestre

| # | Qué | Por qué | Dónde |
|---|---|---|---|
| 5 | **Doblaje de voz** (clon y, si se puede, labios) **integrando** ElevenLabs, HeyGen o Reap por su MCP, con la Memoria y el glosario mandando | Es el hueco más visible frente al mercado; integrar es más barato que construir | Método `i18n` + documento de referencia + orquestación del director |
| 6 | **Revisión y aprobación por enlace** con comentarios en el tiempo del vídeo | Crítico para Agency y para el cliente de P1; ya está en `research/08` §6 | Estudio: campaña → entregables → revisión |
| 7 | **Publicación y programación** (integrar el MCP de OpusClip, Buffer o Metricool, o las API de las plataformas) | Cierra el «publicar esta semana» | MCP / estudio |
| 8 | **Voz aprendida de ejemplos** (frases que sí y que no) y **voz por plataforma** | Lo hacen Typeface, HubSpot, OwlyWriter y Canva | Memoria v2 (`voice.samples`, `voice.by_platform`) |
| 9 | **Personas de audiencia** con su dolor y sus objeciones | Jasper, Adobe y brandsystem las tienen; mejoran ganchos y callouts | Memoria v2 (`audience.personas`) |

| 9b | **Otros motores de IA** además de Claude (Codex, Gemini CLI y otros agentes que hablen MCP): el método y la Memoria ya viajan por MCP; falta empaquetar el plugin para cada uno y probar el método | Decisión de Javier (2026-10-03): hoy solo Claude, en el roadmap el resto. OpusClip y Cardboard ya están en Codex | Plugin y método |

### Después

| # | Qué | Por qué |
|---|---|---|
| 10 | **Aprendizaje con datos reales**: subir el CSV de retención o conversiones de YouTube, TikTok o Meta → puntuación de ganchos | Adobe y Omneky lo hacen; hoy el nuestro es manual |
| 11 | **Ranking de clips** con un número comparable (gancho, ritmo, cara, tono) | El virality score de Opus es lo que el cliente espera ver |
| 12 | **Exportación a NLE** (XML de Premiere o Resolve) para quien quiera retocar a mano | Gling, Eddie e invideo; choca con «se edita el storyboard» |
| 13 | **Brand Book compartible** generado desde la Memoria | Pomelli: activo que enseñar y que nos difunde |
| 14 | **Imitar una referencia** (ritmo, frecuencia de zoom, estilo de subtítulos medidos de un vídeo) | Convierte `references` en datos útiles |
| 15 | **Bucle de autoevaluación** del render (mirar la hoja de contacto → arreglar → re-render, N vueltas) | Idea de video-use; capitalizable en el método del director |

**No adoptar [I]:** generación sintética de avatares y actores UGC (Creatify, Arcads, HeyGen) y B-roll generativo como
núcleo. Es otro trabajo distinto, con otra economía de créditos, y rompe el «local, tu metraje real». Se puede integrar
por MCP más adelante si lo piden.

---

## 4. Precio frente al mercado (sin cambiar nada todavía)

- **Clippers de entrada** (15–39 USD/mes): Creator a 79 cuesta entre 2 y 5 veces más. La persona sola gasta en IA 30–50
  USD/mes ([Metricool](https://metricool.com/what-to-spend-on-ai-tools-social-media/), 2026-09-15). **[I]** A ella solo
  se le vende Creator como el asistente que le quita horas de edición, no como «otra herramienta más».
- **Planes de equipo** (39–150 USD): Brand a 199 está por encima de casi todos, salvo de Rask Business (249) y Cardboard
  Pro (175–250).
- **Personas**: 20 shorts al mes con un freelance cuestan unos 2.000 USD; una agencia de nivel medio, 1.500–5.000 USD al
  mes ([skapo](https://skapo.io/resources/short-form-video-pricing-agencies-2026),
  [pixflow](https://pixflow.net/blog/freelance-video-editing-rates/)). **[I]** Aquí Brand y Agency son baratos y Studio
  (2.490) está en precio.
- **Coste oculto y ventaja**: el cliente paga además Claude (20–100 USD), pero no paga créditos y no necesita juntar 2–3
  herramientas (p. ej. Opus Pro 29 + Rask 39 + Submagic 39 ≈ 107 USD).

**A validar con Fundadores [I]**:

1. ¿Creator (79) convierte, o el creador individual se queda en OpusClip? Si no convierte, Creator se queda como escalón
   de Brand y no se le hace marketing.
2. Ofrecer «doblaje incluido» en Brand cuando exista el punto 5.
3. Mantener el anual ×10, aunque la competencia rebaja hasta un 50 % en anual. Decidirlo con datos.

Cualquier cambio se hace primero en `research/08` §11 y después en la landing.

---

## 5. Buyer persona

### Lo que sabemos del mercado

- **Claude Code fuera de la programación [H].** Anthropic no publica el número de usuarios. Datos públicos:
  - En la Serie G (2026-02-12) Claude Code superaba los 2.500 M USD de ingresos anualizados, con los usuarios semanales
    duplicados desde enero ([anthropic](https://www.anthropic.com/news/anthropic-raises-30-billion-series-g-funding-380-billion-post-money-valuation)).
  - En su estudio de uso (2026-06-16), los grupos no informáticos más grandes son negocio, artes, diseño y medios, y
    dirección ([anthropic](https://www.anthropic.com/research/claude-code-expertise)).
  - Anthropic usa Claude Code en su propio marketing: anuncios de 30 minutos a 30 segundos
    ([claude.com](https://claude.com/blog/how-anthropic-uses-claude-marketing)).
  - Para los no programadores lanzó **Cowork** (2026-01), que tiene plugins por función, incluido uno de Marketing.
- **Ecosistema de marketers con Claude Code [H]:** MKT1 («Gen Marketers»), Animalz, claudecodeformarketers.com, el repo
  `marketingskills`. Son early adopters, sobre todo B2B y SaaS.
- **Vídeo y empresa [H]:**
  - El 91 % de las empresas usa vídeo (Wistia/Wyzowl vía [shopify](https://www.shopify.com/blog/video-marketing-statistics)).
  - El 54 % ya tiene equipo de vídeo propio, pero casi el 40 % gastó menos de 5.000 USD en producción el año pasado
    ([wistia](https://wistia.com/blog/state-of-video-webinar-recap)).
- **Idiomas [H]:** solo el 43 % de los creadores traduce sus vídeos y solo el 56 % de las webs de marca con vídeo lo
  tiene localizado. El 65 % de la visualización de YouTube es de fuera de EE. UU.
  ([kapwing](https://www.kapwing.com/resources/video-translation-statistics-how-many-creators-localize-their-content-in-2026/)).
- **Referencia de mercado [H]:** OpusClip, con unos 10–20 M USD de ingresos en 2025 según la fuente
  ([sacra](https://sacra.com/c/opusclip/), [getlatka](https://getlatka.com/companies/opus.pro)).

### Las cuatro personas, por prioridad

| | **P1 · Marketing de marca DTC «educativa»** | **P2 · Agencia pequeña** | **P3 · «Gen Marketer» B2B/SaaS** | **P4 · Creador o coach** |
|---|---|---|---|---|
| **Quién** | Head of Content o Growth, o el fundador. Marca de EE. UU. de 2–50 M USD en Shopify o Amazon con producto que se aprende (DIY, herramientas, hobby, cosmética técnica) | Fundador u *ops lead* de una agencia social o UGC de 3–20 personas con 5–15 clientes | Content o PMM de una SaaS de 20–500 personas | Experto independiente con cursos o consultoría |
| **Situación** | Archivo de tutoriales largos; le faltan shorts, anuncios e idiomas | Vive del margen sobre horas de edición | Webinars, demos y vídeos del fundador | Graba mucho, publica poco |
| **Trabajo** | «De cada tutorial, 6–10 shorts y anuncios con la marca en EN/ES/DE con el equipo que ya tengo» | «Más piezas por cliente con el mismo equipo; idiomas como extra» | «Cada webinar convertido en clips para LinkedIn con la marca» | «Publicar con constancia» |
| **Hoy paga** | Freelance (75–200 USD por short) o agencia (1.500–5.000 USD/mes) + Opus o CapCut | Editores en Upwork o Fiverr + Descript u Opus | Opus o Descript (30–65 USD) | 30–50 USD/mes en IA + Fiverr |
| **Objeciones** | «No tenemos Claude Code», instalar en el portátil, «¿respeta la marca?», calidad frente a un humano | Que sus editores lo aprendan, licencia por puestos, verlo como competidor | Precio frente a Descript | Precio |
| **Disparador** | Lanzamiento, mercado nuevo, se va el editor, fatiga creativa | Cliente nuevo, presión sobre el margen | Lanzamiento, programa de vídeos del fundador | — |
| **Canal** | Envío en frío **con muestra hecha con su propio vídeo**, DTC Newsletter, comunidades de Motion y Foreplay, referencias del Cliente A | Comunidades de fundadores de agencia, MKT1, r/agency, **programa de partners** | MKT1, Animalz, X, r/ClaudeAI; tutorial «así lo montamos» | — |
| **Plan** | **Studio 990 → Brand 199** | **Agency 499** | Creator / Brand | Creator |
| **¿Ya usa Claude Code?** | Baja-media | Media-alta | La más alta | Media-baja |
| **Prioridad** | **Foco** | **Canal en paralelo** | Visibilidad y contenido | **Aparcar** |

### Decisión de Javier (2026-10-03)

**El foco es la marca DTC** (P1): marca *direct-to-consumer* que vende su propio producto por su web, Amazon o TikTok
Shop, sin intermediarios, y que vive de los anuncios y del vídeo. Dentro de ella, la «educativa», que ya tiene
tutoriales grabados. Siguiente paso: validarlo con 5–10 marcas candidatas y una muestra hecha con su propio vídeo
(`research/12`). Mientras la relación con el Cliente A esté en curso, **no se prospecta a sus competidores directos**
(grabado y corte láser).

### Quién compra, quién usa y cómo nos presentamos (Javier, 2026-10-03)

En una marca DTC hay dos papeles, y el mensaje tiene que servir a los dos:

| Papel | Quién es | Qué le importa |
|---|---|---|
| **Quien compra** | Fundador, Head of Marketing o Growth de la marca | Más creatividades y más mercados con el mismo presupuesto; que todo salga con su marca |
| **Quien lo usa** | Quien lleva la edición, el diseño o el contenido: editor o diseñador interno, content lead, o el freelance o la agencia que trabaja para la marca | Quitarse el trabajo repetitivo (cortes, subtítulos, versiones, formatos, idiomas) y dedicar el tiempo a lo creativo |

**Reglas de posicionamiento:**

1. **Frame28 potencia a los editores, no los reemplaza.** Ahorra horas de edición, genera más piezas y deja al editor
   el criterio y el acabado. Nunca «sin editores», «0 editores» ni «reemplaza a tu editor». Si el editor lo ve como una
   amenaza, perdemos a quien tiene que usarlo y recomendarlo.
2. **Facilitamos el trabajo con IA.** La Memoria de marca y el estudio de prompting convierten «usar IA» en algo
   ordenado: la marca queda escrita una vez y cualquier persona del equipo obtiene resultados con su voz.
3. **Hoy con Claude; mañana, con más motores.** Hoy Frame28 trabaja con Claude (Claude Code). Adaptarlo a otros
   motores de IA está en el roadmap. El contexto (Memoria y campañas por MCP) ya es un estándar abierto que esos motores
   empiezan a hablar.

**Mensaje para quien compra:** *«Tus tutoriales, convertidos cada semana en shorts, anuncios e idiomas con tu marca.
Tu equipo produce más sin crecer, y el vídeo no sale de tu ordenador.»*

**Mensaje para quien lo usa:** *«Lo repetitivo lo hace Frame28: cortes, subtítulos, versiones, formatos e idiomas. Tú
decides y das el acabado.»*

**Revisar con este criterio** el copy de la landing (repo `frame28-app`, `web/src/content/landing.ts`) y la métrica
«0 editores» de `research/08` §10.

### Recomendación [I]

- **Foco de los próximos 6 meses: P1.** Es el caso validado (Cliente A) y el que más aprovecha lo que solo nosotros
  hacemos: paquete completo, idiomas y marca.
  - Frente a sus 2.000–5.000 USD al mes, 199 es poco, y 990 o 2.490 se venden como servicio.
  - **Studio resuelve la objeción «no tengo Claude Code».** El cliente entra por el servicio con su Memoria hecha, y
    después pasa a Brand.
- **P2 en paralelo, como canal.** Una venta son diez marcas. Necesita revisión por enlace (punto 6) y tarjeta final
  propia.
- **P3 como canal de visibilidad, no como fuente de ingresos.** Es quien adopta antes y difunde, pero su presupuesto de
  vídeo es pequeño. Le sirve el contenido «cómo montamos esto con Claude Code».
- **P4, aparcado.** Muy sensible al precio, compite con Opus a 15–29 USD, pide mucho soporte y se va enseguida.

**Mensaje para P1:** ver «Quién compra, quién usa y cómo nos presentamos», más arriba.

Su vocabulario: *creative volume, hook rate, thumb-stop, creative testing, ad fatigue*.

---

## 6. Riesgos y vigilancia

| Riesgo | Señal que vigilar | Respuesta |
|---|---|---|
| **HeyGen amplía HyperFrames** con cortes y reencuadre: cubriría gran parte de nuestra mecánica gratis | Releases de `heygen-com/hyperframes` (skills `talking-head-*`) | Vender criterio y paquete, no mecánica; mantener las regresiones fijadas y el storyboard como capa propia; poder cambiar de compositor |
| **HeyGen llega al usuario sin terminal** (Studio, app de escritorio, «editar por chat»; 25 releases en tres días, 06-10-2026) | Releases de HyperFrames que toquen Studio y escritorio; adopción | Puerta sin terminal de Frame28 (app de escritorio, Cowork) antes del POC; vender la cuenta y la Memoria, no el editor |
| **OpusClip con plugin y cuenta** (nuestro modelo, su marca) | Novedades de `opus-pro/ai-producer-plugin`, MCP con marca persistente | Memoria específica de vídeo, local, sin créditos; agencias |
| **Google Pomelli monta vídeo a cámara** gratis | Blog de Google Labs (Pomelli + Veo) | P1 y P2 (más allá de la pyme pequeña), calidad de montaje de metraje real, idiomas |
| **Skills gratuitas abaratan «editar con Claude»** | video-use y toolkits | Comunicar el resultado, no la herramienta |
| **Adopción de Claude Code baja en DTC** | Conversión de Fundadores; peticiones de «no tengo Claude Code» | Studio como puerta; spike de Cowork y escritorio (punto 4) |
| **Dependencia de terceros** si integramos doblaje y publicación | Precios y términos de ElevenLabs, HeyGen y Reap | Integraciones intercambiables y la Memoria como fuente de verdad |

---

## 7. Siguientes pasos propuestos

1. Javier decide el foco (P1 + P2) y si el punto 4 (Cowork y escritorio) va antes que el resto.
2. Llevar los puntos 1–4 al roadmap (`docs/roadmap/index.html`) y los 5–9 como siguiente versión.
3. Preparar la «muestra con su propio vídeo» como pieza de captación de P1: un tutorial público de una marca DIY → 6
   shorts + 2 idiomas. Es el flujo que ya hicimos con el Cliente A, anonimizado.
4. Programa de partners para agencias (P2): condiciones y revenue share, en `research/08`.
5. Vigilancia de competencia quincenal a cargo de «[F28] Research» (`informes/research/vigilancia.md`); próxima: 2026-10-20. La revisión a fondo del mapa, trimestral (2027-01).
