# Frame28 como plataforma: plugin de pago + frame28.app como panel de control (2026-10-01)

Documento de definición de la nueva etapa. Sustituye a `research/07` en la **oferta** (§2–3 de aquel documento quedan
superados) y lo complementa en lo demás (base de conocimiento, curso, sitio, plan). Nace de la decisión de Javier del
2026-10-01 por la noche: *«El enfoque no es que nos envíen el vídeo y nosotros hacemos el trabajo. El enfoque es que el
cliente trabaja con sus propios vídeos, con un plugin de pago en su Claude Code, y todo lo que ese plugin sabe de su marca,
su producto, su tono y sus campañas lo configura y gestiona desde frame28.app, con el mismo usuario y su membresía.»*

Todo lo técnico que se afirma aquí está comprobado el 2026-10-01: la documentación de plugins y MCP de Claude Code, los
stacks de las webs de referencia (HTML real), y lo que Think28 ya opera en Synapse28 y en el VPS. Lo que es propuesta
(precios, nombres, fases) está marcado como tal.

---

## 0. En diez líneas

1. **Frame28 es un estudio de vídeo que vive dentro del Claude Code del cliente y que conoce su marca.**
2. El cliente se da de alta en **frame28.app**, paga una membresía y rellena su **Memoria de marca**: brand kit, historia,
   voz, catálogo, ganchos, idiomas, plataformas. Frame28 se la redacta a partir de su web y de sus vídeos; él la corrige.
3. Desde frame28.app crea **campañas**: objetivo, producto, formatos, idiomas, fechas, vídeos de origen.
4. En Claude Code, el **plugin** se autentica con ese mismo usuario (OAuth, un clic) y recibe la Memoria y la campaña por
   **MCP**. El director de Frame28 monta: largo, shorts con ganchos, portadas, subtítulos, idiomas, copy de publicación.
5. Los entregables suben a la campaña; el cliente revisa, comenta y aprueba **en la web**, y marca qué funcionó: la
   Memoria aprende (ganchos, promesas, objeciones).
6. El **motor** (CLI + HyperFrames, MIT) es el mismo en el portátil del cliente hoy y en la nube de Frame28 mañana: el
   contrato es el **storyboard JSON** y la **Memoria de marca**.
7. **Modelo**: open core **con control de uso**. El **motor** (CLI) es MIT; el **plugin** es una cáscara que solo funciona
   autenticado contra frame28.app (cuenta gratuita para probar, membresía para todo lo demás): el criterio del director y la
   Memoria se sirven desde el servidor por MCP, nunca dentro del plugin (§7 bis). Think28 mantiene un tier *Studio* operado.
8. **Stack**: Next.js + Tailwind + GSAP + un shader en el hero (web); FastAPI + Postgres + MCP en Python (API; comparte
   el paquete `frame28`); Think28 ID sobre Entra External ID (el CIAM de Synapse28); Paddle (reutilizado); R2 para vídeo;
   Docker + túnel de Cloudflare en t28server (ya desplegado así el sitio actual).
9. **Diseño**: disciplina Linear/Vercel, el producto como héroe al estilo Cursor/Supabase (una composición real de Frame28
   corriendo en HTML+GSAP, que es lo que el motor produce), un momento wow barato tipo Stripe, métricas duras como TypeSafe,
   contención Anthropic en el tono. Negro `#0A0A0A`, un solo acento `#F5C500`, Inter + Space Mono: los mismos tokens que
   los vídeos que Frame28 renderiza.
10. **Plan**: fase 0 (días) posicionamiento en la landing en vivo y lista de acceso anticipado; fase 1 (3–4 semanas) MVP
    cuenta + Memoria + campañas + MCP + plugin conectado; fase 2 equipo, agencia, revisión; fase 3 Frame28 Cloud.

---

## 1. El giro, y qué se conserva

| | Antes (`research/07`, landing en vivo) | Ahora |
|---|---|---|
| Qué vende Think28 | Un servicio: «Envías un vídeo. Recibes la campaña.» Launch, Studio, Team | Un producto: el plugin + la cuenta en frame28.app, con la marca del cliente como contexto; Studio queda como tier operado |
| Quién opera | Think28 con el plugin | El cliente, en su Claude Code (o Think28 en Studio; o la nube de Frame28 después) |
| Dónde vive la marca | En `work/brands/` del operador | En la Memoria de marca de la cuenta, servida al plugin por MCP |
| Dónde viven las campañas | En correos y carpetas | En frame28.app: brief, entregables, revisión, aprendizaje |
| Qué es frame28.app | Landing + condiciones + KB y curso tras Access | **La aplicación**: cuenta, membresía, Memoria, campañas, biblioteca, equipo, y la landing |
| Plugin | Gratis, marca Think28 o marcas locales | **De pago por membresía**; sin cuenta funciona en modo demo |

**Se conserva**: el motor (CLI, HyperFrames, storyboard JSON, 114 pruebas), las ocho skills (ganan contexto), la base de
conocimiento y el curso (ahora parte de la membresía), la infraestructura (t28server, túnel, `deploy/`), la marca Think28 y la
confidencialidad del Cliente A. La segunda muestra ya montada sigue siendo la demostración comercial: el Cliente A puede
ser el primer cliente **Team/Studio** del nuevo modelo.

**Lo que hay que cambiar pronto**: la landing en vivo sigue vendiendo el servicio (fase 0), las condiciones son de un servicio
y no de un SaaS (revisión legal), el roadmap gana épicas (cuenta, Memoria, campañas, MCP, cloud), y `research/07` §2–3.

---

## 2. Para quién y qué compra

| Perfil | Situación | Qué compra | Tier propuesto |
|---|---|---|---|
| **Marca con marketing propio** (DTC, software, formación, salud) que ya graba vídeo | Tiene tutoriales, demos, un fundador que habla a cámara; no tiene editores ni tiempo | Convertir cada vídeo en campaña completa, con su marca, en horas; que el sistema recuerde su marca | Brand |
| **Creador o consultor** con una marca personal | Graba mucho, publica poco | Lo mismo, una sola marca, sin equipo | Creator |
| **Agencia o freelance de contenido** | Varias marcas, plazos, revisiones | Varias Memorias, revisión con el cliente, tarjeta final propia | Agency |
| **Empresa con equipo de ventas o formación** | Quiere que su gente produzca vídeo sin saber editar | Puestos, marca bloqueada, biblioteca de ganchos aprobada | Team (hoy) / Brand con puestos |
| **Marca que no quiere operar nada** | Quiere resultados, no herramientas | Que Think28 lo haga con Frame28, con la misma cuenta como registro | Studio (servicio) |

El trabajo que hacen («job to be done»): *«publicar en todos los formatos y mercados lo que ya grabé, con mi marca, esta
semana, sin ampliar el equipo de edición»* (Frame28 potencia a quien edita, no lo sustituye: `research/11` §5).

---

## 3. Las cuatro piezas

```
┌─────────────────────────────── frame28.app (Next.js) ───────────────────────────────┐
│  Cuenta · Membresía (Paddle) · Memoria de marca · Campañas · Biblioteca · Equipo     │
│  Revisión y aprobación · Aprendizaje de ganchos · KB y curso · Landing               │
└───────────────┬───────────────────────────────────────────────┬──────────────────────┘
                │ API REST (FastAPI)                            │ MCP remoto (OAuth, Think28 ID)
                ▼                                               ▼
   ┌─────────────────────┐                    ┌────────────────────────────────────────┐
   │ Postgres (RLS)      │                    │ Plugin Frame28 en el Claude Code        │
   │ R2 (vídeos, assets) │◄── presigned URLs ─┤ del cliente: 8 skills + .mcp.json       │
   └─────────────────────┘                    │ Claude dirige con la Memoria y el brief │
                                              └──────────────┬─────────────────────────┘
                                                             │ Bash
                                                             ▼
                                              ┌────────────────────────────────────────┐
                                              │ Motor: CLI frame28 (MIT) + HyperFrames  │
                                              │ prep · transcribe · cut · build · render│
                                              │ hoy en el portátil; mañana en la nube   │
                                              └────────────────────────────────────────┘
```

1. **frame28.app**: la aplicación (y la landing). Sistema de registro: quién es el cliente, qué paga, qué marca tiene, qué
   campañas, qué entregables, qué funcionó.
2. **Memoria de marca**: el contexto que hace que el vídeo sea *de esa marca* y no genérico (§5).
3. **Plugin**: lo que el cliente instala en Claude Code. Las skills de siempre, más un servidor MCP remoto que les da la
   Memoria y la campaña, y les permite entregar (§7).
4. **Motor**: el CLI y HyperFrames, deterministas, abiertos. Corren donde haga falta: el portátil del cliente (plugin), el
   de Think28 (Studio) o un worker de Frame28 (Cloud, fase 3). El contrato entre el director y el motor sigue siendo el
   storyboard JSON; el contrato entre la cuenta y el director es la Memoria + el brief de campaña.

---

## 4. Un día con Frame28 (flujo de punta a punta)

1. **Alta** en frame28.app con Think28 ID (email con código, Google o Microsoft). Elige plan, paga con Paddle (tarjeta,
   impuestos y facturas resueltos por Paddle como *merchant of record*).
2. **Onboarding en diez minutos**: pega la URL de su web y enlaza dos o tres vídeos suyos. Frame28 propone la Memoria de
   marca: colores, fuente y logo desde la web (`brand from-site`, ya existe), y desde las transcripciones de sus vídeos la
   voz, las promesas, las objeciones, el vocabulario y los productos que nombra. El cliente corrige y completa el
   cuestionario (§5). Cada campo tiene un «por qué lo pedimos».
3. **Conectar Claude Code**: una página «Conectar» con la línea de instalación (`irm … | iex` / `curl … | sh`) y el aviso de
   que, al primer uso, Claude Code abrirá el navegador para entrar con su cuenta (OAuth, `/mcp`). Para equipos y CI, un
   **token de API** alternativo.
4. **Crear campaña** en la web: objetivo (lanzar, vender, educar, retener), producto del catálogo, plataformas y formatos
   (largo 16:9, shorts 9:16, ficha 1:1), idiomas, fecha, vídeos de origen (sube a R2 o enlaza YouTube), notas. La web
   genera el **brief** y la lista de **entregables esperados**.
5. **En Claude Code**: «Monta la campaña *Lanzamiento acrílico*». El plugin pide por MCP la Memoria y la campaña; el
   director transcribe, decide el montaje con la marca, los ganchos aprobados y las reglas de la voz, construye y renderiza:
   largo, shorts con dos ganchos cada uno, portadas, SRT, versiones en los idiomas pedidos y el **copy de publicación**
   (títulos, descripciones, hashtags por plataforma). Anota tiempo y coste (`frame28 report`).
6. **Entrega**: `frame28 deliver` sube cada pieza con una URL firmada que el MCP le dio; en la web aparece el tablero de la
   campaña con hojas de contacto, vídeos reproducibles y el storyboard de cada pieza.
7. **Revisión en la web** (también desde el móvil): aprobar, pedir cambios con marca de tiempo, descargar. Un cambio vuelve
   al plugin como nota de la campaña; el director regenera solo lo tocado.
8. **Publicar y aprender**: checklist de publicación por plataforma; a los días, el cliente marca qué ganchos y piezas
   rindieron (o lo conecta a sus analíticas, fase 2). La Memoria prioriza esos ganchos y promesas en la siguiente campaña.

---

## 5. La Memoria de marca (Context Pack v1)

Es la pieza que convierte un generador de vídeo en **el estudio de esa marca**. Un documento estructurado por cuenta y marca
(una cuenta puede tener varias marcas: agencias), versionado, con origen por campo (web, vídeo, cliente, campaña).

```jsonc
{
  "brand": {           // lo que ya es brands/<marca>.json del CLI: accent, ink, paper, sans, mono, logos, motion
    "name": "…", "accent": "#…", "ink": "#…", "sans": "…", "mono": "…", "logo_files": {…}, "display_weight": 800
  },
  "voice": {           // ya existe en think28.json: se formaliza y se rellena para cada cliente
    "pillars": ["directo", "cercano", "experto"], "avoid": ["revolucionario", "mágico"], "max_words_per_sentence": 14,
    "person": "tú", "register": "informal-profesional", "emoji": false, "caps_in_hooks": true
  },
  "story": {           // el cuestionario
    "who": "qué es la marca en una frase", "for_whom": ["segmentos"], "promise": "qué cambia para el cliente",
    "proof": ["cifras, clientes, garantías"], "objections": [{"objection": "…", "answer": "…"}],
    "enemies": ["lo que la marca combate: el editor caro, la plantilla genérica…"], "origin": "historia fundacional (opcional)"
  },
  "catalog": [          // productos y ofertas: lo que el director nombra y señala
    {"id": "engraver-pro", "name": "…", "price": "…", "codes": ["…"], "url": "…", "features": ["…"], "images": ["r2://…"]}
  ],
  "audience": {"platforms": ["youtube", "tiktok", "instagram"], "safe_zones": "tiktok", "languages": ["en", "es", "de"]},
  "hooks": {"approved": [{"text": "…", "type": "promise|result|objection|number", "score": 0.0}], "banned": ["…"]},
  "glossary": {"es": {"engraver": "grabador"}, "de": {…}},   // términos fijos por idioma (nombres, cifras, claims)
  "legal": {"claims_not_allowed": ["cura", "garantizado"], "disclaimers": ["…"]},
  "cta": {"default": {"text": "…", "url": "…", "code": "…", "qr": true}},
  "references": ["vídeos que le gustan y por qué"],
  "learning": {"winners": [...], "losers": [...], "updated_at": "…"}   // lo que las campañas enseñan
}
```

**Cómo la consume el plugin**: la skill directora pide `context.get(brand, campaign)` al MCP y recibe dos cosas: el JSON de
marca que el CLI ya entiende (lo escribe en `work/brands/<marca>.json`) y un **brief en Markdown** de dos pantallas (voz,
historia, catálogo, ganchos, glosario, reglas legales, campaña) que es lo que Claude lee antes de decidir el montaje. Es la
formalización de lo que hoy hacemos a mano en `brief.md`, `nombres.txt` y `marca-y-promocional.md` §4 con el Cliente A.

**Cómo se crea sin cansar al cliente**: onboarding asistido. La web lanza (con la API de Claude, en servidor) una primera
redacción desde la web del cliente y las transcripciones de sus vídeos (el mismo `transcribe` del motor, en un worker) y se
la presenta para corregir. Cada campo con ejemplo y «por qué». Objetivo: Memoria utilizable en diez minutos, afinada en la
primera campaña.

---

## 6. Campañas, entregables y aprendizaje

Modelo de datos (nombres provisionales):

- **Account** (tenant) → **Brand**(s) → **Memory** (versionada) · **Member**s (roles: owner, editor, reviewer) · **Subscription** (Paddle).
- **Campaign**: brand, goal, product, platforms, formats, languages, deadline, sources (vídeos en R2 o URL), notes, status
  (`draft → briefed → producing → review → approved → published → measured`).
- **Deliverable**: campaign, kind (`long`, `short`, `cover`, `square`, `srt`, `copy`, `storyboard`), language, hook, asset
  (R2), sheet (hoja de contacto), storyboard JSON, cost (segundos de máquina, tokens, stock), status, comments (con `t`).
- **Review**: comentarios con marca de tiempo y resolución; aprobación por pieza.
- **Learning**: por deliverable, señales (`published`, `views`, `ctr`, `saves`, `conversions` manual o por conector) → puntúa
  `hooks.approved[].score` y `story.promise` en la Memoria.

Lo que el plugin entrega además del vídeo: **copy de publicación** por plataforma (título, descripción, hashtags, primer
comentario con el CTA), la **hoja de contacto** (revisión rápida) y el **storyboard** (reutilizable como plantilla de la marca:
«la próxima campaña, igual que esta pero con el producto nuevo»).

---

## 7. El plugin: qué cambia y qué permite Claude Code (verificado)

Lo que la documentación de Claude Code garantiza hoy (consultada el 2026-10-01):

- Un plugin declara servidores MCP en `.mcp.json` (raíz del plugin) o en `mcpServers` del manifiesto; **remotos** con
  `type: "http"`, `url`, `headers`, `headersHelper` y un bloque **`oauth`** (`clientId`, `callbackPort`, `scopes`,
  `authServerMetadataUrl`). Claude Code hace el descubrimiento OAuth 2.0 (RFC 9728 y 8414), admite **registro dinámico o
  cliente preconfigurado**, guarda los tokens en el llavero del sistema y los renueva; el usuario entra con `/mcp` o
  `claude mcp login <servidor>` (también `--no-browser` para SSH).
- `userConfig` con `sensitive: true` pide un valor al activar el plugin y lo guarda en el almacén seguro; se sustituye como
  `${user_config.KEY}` en la configuración del MCP (`headers`, `env`). Vía válida para un **token de API** (equipos, CI).
- `${CLAUDE_PLUGIN_DATA}` (`~/.claude/plugins/data/<id>/`) persiste entre versiones del plugin: caché de la Memoria y de
  los briefs. `${CLAUDE_PLUGIN_ROOT}` cambia con cada versión: nunca estado ahí.
- `bin/` pone ejecutables en el PATH del Bash, pero **claude.ai y Cowork no instalan plugins con `bin/`**: la parte
  autenticada va por MCP remoto, no por binarios. El CLI sigue instalándose aparte (ya es así).
- `metadata` es libre («catalog or entitlement fields»): sitio para el id de producto y el tier mínimo.
- Las skills pueden incluir `${user_config.KEY}` no sensibles en su texto (p. ej. la marca por defecto).

Cambios en el plugin de Frame28:

1. **`.mcp.json`** con el servidor remoto `frame28` (`https://frame28.app/mcp`, OAuth con Think28 ID; alternativa `headers`
   con `${user_config.api_token}` para el perfil Team/CI). Herramientas: `account.me`, `brands.list`, `context.get(brand,
   campaign)`, `campaigns.list/get`, `campaigns.note`, `deliverables.upload_url(kind, lang, hook)`, `deliverables.submit`,
   `hooks.search`, `report.submit`. El MCP es **el único puente autenticado**; el CLI no necesita credenciales.
2. **Skills mínimas (cáscara)**: cada skill del plugin se reduce a «llama a la herramienta `frame28_start` con lo que pide el
   usuario y sigue al pie de la letra el método que devuelva». El **método del director** (lo que hoy son 863 líneas de
   skills y referencias: técnicas, ganchos, marca y promocional, grabación) se sirve desde el MCP, por sesión, ya fundido
   con la Memoria de la marca y el brief de la campaña, y **según el plan**: la cuenta gratuita recibe el método demo (marca
   Think28, tarjeta final «Hecho con Frame28», tres campañas); la membresía recibe el completo. Sin sesión, `frame28_start`
   devuelve solo «entra en frame28.app». Las skills de storyboard, shorts e i18n leen la voz, el glosario, los ganchos
   aprobados y las reglas legales de la Memoria porque vienen dentro de ese método. Ver §7 bis.
3. **Comandos**: `/frame28:campaña [nombre]` (lista y elige campaña), `/frame28:entregar` (sube lo que haya en `out/`),
   `/frame28:memoria` (muestra lo que el plugin sabe de la marca y dónde cambiarlo).
4. **CLI**: `frame28 deliver <fichero> --to <url firmada>` (PUT a R2 con reintentos y hash), `frame28 context apply
   <brief.json>` (escribe `work/brands/<marca>.json` y `work/brief.md` a partir de lo que dio el MCP), `frame28 publish-copy`
   (plantillas de copy por plataforma desde el storyboard y la Memoria). Todo MIT, como hoy.
5. **Distribución**: el plugin sigue público en el marketplace `think28` (GitHub), pero desde la v0.5 **no lleva nada que
   valga sin cuenta**: ni el método del director ni la Memoria (§7 bis). Lo de pago no es el código: es la cuenta y lo que el
   servidor le sirve. El motor (CLI) es MIT: cualquiera puede renderizar un storyboard con él; nadie obtiene sin membresía el
   criterio actualizado, la Memoria, las campañas, la entrega, el aprendizaje ni la nube.

## 7 bis. Control de uso: solo quien se autentica y tiene membresía puede usar el plugin

Pregunta de Javier (2026-10-01, noche): *«tenemos que tener la certeza de que la persona que instale nuestro plugin no sea
cualquier persona… solo será posible instalarlo o utilizarlo si se autentica con nuestra web, identifica que es un usuario
válido, su membresía y toda su historia»*.

**Lo que Claude Code permite y lo que no (verificado en su documentación):**

- Un plugin son ficheros (Markdown, JSON, scripts) que Claude Code copia al ordenador del usuario. **Todo lo que viaje dentro
  del plugin es legible y copiable.** No hay plugins cifrados ni un marketplace de pago nativo. Un marketplace privado en
  GitHub exigiría dar acceso al repo a cada cliente: inviable para vender a marcas.
- No se puede impedir que alguien **instale** un plugin público ni que use el motor MIT ya publicado (v0.1–v0.4) con sus
  propias marcas. Sí se puede impedir que obtenga **lo que vendemos**. El control vive en el servidor, y el plugin se diseña
  para que **sin servidor no sepa hacer nada**.

**Diseño en cuatro capas, de más a menos fuerte:**

| Capa | Qué hace | Qué impide |
|---|---|---|
| 1. **Cáscara + MCP** | El plugin publicado lleva `.mcp.json` (MCP remoto con OAuth), `hooks.json` y skills de dos líneas. El **método del director** (técnicas, ganchos, marca, reglas de montaje) y la **Memoria** se sirven por MCP, por sesión, solo con token válido y según el plan. El MCP comprueba en cada llamada la membresía (estado de Paddle) y la pertenencia de la marca y la campaña a esa cuenta | Que alguien sin cuenta, o con la suscripción caducada, tenga el criterio y el contexto que hacen el vídeo. Es la capa que de verdad controla: no hay nada que copiar del plugin |
| 2. **Hooks de sesión** | `SessionStart` ejecuta `frame28 whoami` y añade al contexto «Frame28: sin cuenta, solo demo» o «cuenta X, plan Brand, marcas …»; `PreToolUse` sobre Bash bloquea `frame28 build/render` con marca ajena a la cuenta cuando no hay licencia válida (exit 2 con el motivo) | El uso por descuido o por costumbre sin sesión; da la experiencia por defecto gated. Son ficheros editables: refuerzan, no sostienen |
| 3. **Licencia en el motor** | El MCP emite un **token de licencia firmado** (JWT, 72 h, ligado a la cuenta, el plan y las marcas; renovación automática) que la skill entrega al CLI (`frame28 license set`). Sin token válido el CLI renderiza en modo demo: marca Think28, tarjeta final «Hecho con Frame28», sin i18n ni variantes en lote; con token, todo. Límite de dispositivos por puesto | Compartir un render premium sin cuenta y seguir usando funciones de pago tras caducar. El CLI es MIT y alguien puede quitar la comprobación: solo gana la tarjeta final, no el criterio ni la Memoria |
| 4. **El servidor manda en tiempo real** | Webhook de Paddle → estado de la suscripción → el MCP responde `payment_required` y deja de servir método, Memoria y entregas al instante; la licencia caduca en 72 h | Que una baja o un impago sigan produciendo vídeo. Y cada token lleva el `sub` de la cuenta: un token compartido se detecta (dos dispositivos, dos IP, dos marcas ajenas) |

**Opcional, si se quiere apretar más (sin cambiar la arquitectura):** paquete `frame28-pro` cerrado en un índice privado
(`https://pypi.frame28.app/simple/`) que solo se puede instalar y actualizar con token de cuenta; y, llegado el caso,
cambiar la licencia de las versiones nuevas del CLI (las publicadas quedan MIT). Se decide cuando haya datos de uso.

**Consecuencia sobre la decisión 4 (open core):** se mantiene, con este matiz. El **motor** sigue MIT (adopción, confianza,
demo técnica). El **plugin** deja de llevar las skills completas desde la v0.5 y **exige cuenta siempre**: la prueba gratuita
es un **plan Open con cuenta** (tres campañas de prueba, marca Think28, tarjeta final), no un modo anónimo. Así cada persona
que use el plugin está identificada desde el primer render, su historia queda en su cuenta, y el embudo comercial tiene su
email. La landing lo dice así desde la fase 0.

---

## 8. Arquitectura y por qué cada pieza

| Pieza | Decisión | Por qué |
|---|---|---|
| Web (landing + app) | **Next.js** (App Router, TypeScript) + **Tailwind** + **shadcn/ui** (Radix) + **GSAP** (ScrollTrigger, gratis desde 3.13) + MDX para KB y curso | Un solo framework para marketing y aplicación; SSR para SEO; es el stack verificado de Vercel, Cursor, Supabase, Resend, Raycast, Composio y Stripe; el equipo ya trabaja React + Tailwind (t28website); GSAP ya es nuestro (HyperFrames) |
| Hero wow | Fragment shader WebGL ligero (OGL o WebGL a pelo; **no** Three.js salvo que haga falta 3D) + la composición real de Frame28 en HTML+GSAP | El efecto Stripe cuesta poco; el producto es el héroe (Cursor/Supabase) y nuestro producto *ya* genera HTML+GSAP |
| API | **FastAPI** (Python) | Mismo lenguaje que el motor: comparte el paquete `frame28` (esquema del storyboard, marcas, `brand from-site`, `transcribe` en el worker de onboarding); es el stack de Synapse28 |
| MCP | **Servidor MCP en Python** (SDK oficial, transporte Streamable HTTP) montado en la API en `/mcp`, con validación de tokens de Think28 ID | Un proceso menos; el mismo modelo de datos; `claude plugin validate` ya comprueba la URL remota |
| Identidad | **Think28 ID = Microsoft Entra External ID (CIAM)**, el tenant que ya usa Synapse28, con una app registration para Frame28 (API con scope `frame28.access`) y un **cliente público con PKCE** para Claude Code (`oauth.clientId` + `authServerMetadataUrl` en `.mcp.json`) | Login con email, Google y Microsoft ya resuelto; una identidad para todo el ecosistema; Claude Code admite cliente preconfigurado, así que no hace falta registro dinámico. Un día de *spike* para probar el handshake de punta a punta antes de construir encima |
| Cobros | **Paddle** (merchant of record), reutilizando `billing.py`, el webhook con filtrado `custom_data.product` y `scripts/paddle_bootstrap.py` de Synapse28 | Impuestos y facturas globales; código ya escrito y probado (131 tests en Synapse28); el webhook ya ignora productos ajenos |
| Datos | **PostgreSQL 16** con RLS por tenant (patrón Synapse28), cola de trabajos en Postgres (`FOR UPDATE SKIP LOCKED`) | Multi-tenant seguro desde el día 1; sin Redis hasta que haga falta |
| Vídeo y assets | **Cloudflare R2** (S3) con URLs firmadas y dominio `media.frame28.app` | El VPS tiene 16 GB libres y cada largo pesa 145 MB: el vídeo no puede vivir en disco; R2 no cobra salida y el token ya tiene permiso |
| Email | Resend (transaccional) o Cloudflare Email Service; listas con el **listmonk** que ya corre en el VPS | Barato y fiable; la lista de acceso anticipado ya tiene herramienta |
| Analítica y salud | **Plausible** y **uptime-kuma**, ya desplegados en t28server | Cero coste, privacidad |
| Infra | Docker Compose en `/opt/frame28` (web, api+mcp, db, worker) tras el túnel de Cloudflare; Turnstile en alta y contacto; Access solo para `/admin` | Es exactamente el patrón de hoy y el de Synapse28; cabe en la RAM disponible (≈0,7 GB) |
| Render en la nube (fase 3) | Imagen `frame28-engine` (Python + ffmpeg + Node + Chromium) en una **caja aparte** (Hetzner CPX41 u otra) consumiendo la cola | Capturar fotogramas con Chrome no cabe en el VPS compartido (4 CPU, 7,7 GB); la cola y el contrato ya existen |

Lo que **no** se elige y por qué: **Framer + Unicorn Studio** (TypeSafe, Sahara): rapidísimo para una landing, pero es
hosting ajeno, no sirve para la aplicación y rompe el patrón VPS + túnel. **Webflow** (Anthropic, Wispr, Featherless): lo
mismo. **Astro** para la landing + SPA para la app: dos frameworks que mantener. **SvelteKit** (Modal): válido, pero el
ecosistema Think28 es React. **React Three Fiber**: solo si aparece un render 3D de producto real; para el hero basta un
shader. **MinIO**: ocuparía el disco con vídeo. **Cloudflare Pages**: descartado por Javier a favor del VPS; `site/functions`
se conserva por si acaso.

---

## 9. Las referencias, verificadas

Firmas encontradas en el HTML real el 2026-10-01 (Next.js por `/_next/`, Framer por `framerusercontent`, Webflow, Svelte,
Unicorn Studio, Three.js, GSAP, Lenis, Spline, Sanity, Contentful; cabecera `x-vercel-id` = alojado en Vercel). Lo que
en tu documento iba con ⚠️ y aquí cambia está en negrita.

| Sitio | Stack verificado | Nota |
|---|---|---|
| vercel.com | Next.js, Geist, Vercel | ✅ como decías |
| typesafe.ai | **Framer + Unicorn Studio** | ✅ confirmado |
| linear.app | sin verificar | devuelve 95 bytes a un cliente sin JS: protección anti-bot |
| cursor.com | **Next.js en Vercel** | confirmado |
| supabase.com | Next.js, Tailwind, Radix, Vercel | ✅ |
| resend.com | **Next.js, Tailwind, Vercel y Spline** | el 3D sobrio es Spline, no WebGL a medida |
| raycast.com | **Next.js, Tailwind, Geist, Vercel** | confirmado |
| featherless.ai | **Webflow + GSAP** | no era Framer |
| composio.dev | **Next.js en Vercel** | confirmado |
| modal.com | **SvelteKit** | confirmado |
| wisprflow.ai | **Webflow + GSAP** | confirmado |
| anthropic.com | **Webflow + GSAP + Lenis + Sanity** | antes «no verificado» |
| lusion.co | WebGL propio sobre Vite, Netlify | coherente |
| oryzo.ai | sin firma de framework (carga diferida) | tras Cloudflare |
| igloo.inc | sin verificar (1,4 KB de cáscara; Vercel) | la UI se pinta en WebGL |
| activetheory.net | WebGL propio, Fastly | coherente |
| ivress.com | sin verificar (114 bytes) | |
| stripe.com | **Next.js + Contentful** | el shader va encima |
| apple.com/iphone | propio | |
| saharaai.com | **Framer** | antes «no verificado» |
| shopify.com/editions | propio con Lenis + Tailwind | |
| bruno-simon.com | Three.js | ✅ |

Lectura: los «trascendentales» son casi todos **Next.js + Tailwind en Vercel**; los editoriales de marca son **Webflow +
GSAP**; los de wow son **WebGL a medida**. El framework no es lo que los hace buenos: lo es la disciplina del sistema y que
enseñan el producto de verdad. GSAP aparece en Anthropic, Featherless, Wispr y Lusion: ya es nuestro.

---

## 10. Dirección de diseño

**Principios** (de tu síntesis, ajustados a Frame28):

1. **El producto es el héroe.** Nada de mockups: una composición real de Frame28 (un clip hablando a cámara con rótulo,
   cinético, texto detrás, callout, gráfica y subtítulos) **corriendo en el navegador en HTML+GSAP**, que es lo que el
   motor produce. El scroll avanza la línea de tiempo (Apple) y, al lado, el storyboard JSON resalta el overlay que se está
   viendo: «esto es lo que escribe el director». Debajo, la terminal de Claude Code tecleando la orden: Raycast decía «el
   producto se ve como si ya lo usaras».
2. **Un momento wow, barato.** Fondo del hero con un shader de luz refractada en el amarillo de marca sobre negro (Stripe),
   que reacciona al ratón; nada más en 3D.
3. **Disciplina Linear/Vercel.** Rejilla técnica sutil, bento de seis cajas (Memoria de marca · Campañas · Shorts con
   ganchos · Idiomas · Portadas y fichas · Coste por vídeo), tipografía grande con tracking negativo, mono para datos.
4. **Métricas duras como elementos** (TypeSafe), reales y nuestras: «1 vídeo → 3 idiomas · 6 shorts · 4 portadas · 2 h de
   máquina» (sin «0 editores»: potenciamos a los editores, no los reemplazamos; `research/11` §5), «render 1 m 16 s», «114 pruebas», `frame28 v0.4.0` en vivo desde GitHub, un *ticker* con líneas
   del registro (`.frame28/log.jsonl`): detalle retro-computacional con sentido.
5. **Un solo acento**: `#F5C500` sobre `#0A0A0A`, Inter 800 con `-0.035em` y Space Mono: los tokens de `brands/think28.json`.
   Lo que el visitante ve en la web es lo que Frame28 renderiza: coherencia como argumento.
6. **Contención Anthropic en el tono**: frases de menos de quince palabras, sin «innovador/disruptivo/mágico» (la lista de
   `voice.avoid` de la marca), pruebas antes que promesas.

**Secciones de la landing nueva**: hero vivo → «Cómo funciona» en tres pasos (Memoria · Campaña · Claude Code) → «Dentro de
tu Claude Code» (terminal real) → Memoria de marca (qué recuerda) → Campañas y revisión (capturas del panel) → métricas →
precios → acceso anticipado → preguntas → pie.

**Copy propuesto para el hero** (a validar por Javier):

- ES: **«Tu Claude Code, convertido en el estudio de vídeo de tu marca.»** Subtítulo: «Frame28 recuerda tu marca, tu voz y
  tus productos. Tú grabas; él monta el largo, los shorts con gancho, las portadas, los subtítulos y los idiomas. Desde tu
  ordenador, con tu marca, en horas.» Botones: «Pide acceso anticipado» · «Ver una campaña real».
- EN: **"Your Claude Code, turned into your brand's video studio."** "Frame28 remembers your brand, your voice and your
  products. You record; it edits the long cut, the hook-led shorts, the covers, the subtitles and the languages. On your
  machine, in your brand, in hours." Buttons: "Request early access" · "See a real campaign".

---

## 11. Modelo de negocio y precios (decididos el 2026-10-01: Javier pidió una propuesta cerrada e implementarla; se retoca al final si hace falta)

**Open core** (decisión 4): CLI y plugin base **MIT y gratis** (modo demo con marca Think28 y tarjeta final). Lo que se paga
es la **cuenta**: Memoria de marca, campañas, contexto por MCP, biblioteca, aprendizaje, equipo y, después, nube.

| Tier | Incluye | Precio de lanzamiento (USD, sin IVA) |
|---|---|---|
| Open (cuenta gratuita, obligatoria para usar el plugin) | 3 campañas de prueba, marca Think28, tarjeta final «Hecho con Frame28», KB pública; el motor (CLI) es MIT | 0 |
| **Creator** | 1 marca, 1 puesto; Memoria; campañas ilimitadas en el propio ordenador; largo, shorts, portadas, 1:1, subtítulos, idiomas, copy de publicación; KB y curso | **79 /mes** o 790 /año |
| **Brand** (recomendado) | 3 marcas, 3 puestos; todo Creator; campañas con brief, revisión y aprobación en la web; catálogo; biblioteca de ganchos y storyboards; aprendizaje; soporte por email | **199 /mes** o 1.990 /año |
| **Agency** | 10 marcas, 10 puestos; todo Brand por marca; enlaces de revisión para clientes; tarjeta final propia; roles; token de API; soporte prioritario | **499 /mes** o 4.990 /año |
| **Studio** (servicio, Think28 opera sobre la misma cuenta) | Primera campaña: 1 largo, 4 shorts × 2 ganchos, portada, 1:1, SRT, 1 idioma más, 5 días laborables, garantía de devolución a 30 días si no se publica la mitad · Mensual: 4 largos, 12 shorts, 2 idiomas, informe de ganchos | **990** pago único · **2.490 /mes** (los validados en `research/07`) |
| Cloud (fase 3) | minutos de render en la nube, sin Claude Code | lista de espera; por minuto o paquete |

Lógica de las cifras: el anual regala dos meses (×10); Creator queda entre Claude Pro y Claude Max, que el cliente paga
aparte; Brand cuesta menos que un solo vídeo editado por un freelance al mes; Agency se amortiza con el primer cliente de
la agencia. Precios de lanzamiento congelados doce meses para el acceso anticipado; «precio regular» no se anuncia hasta
tener datos. Se retocan al final si hace falta: primero aquí, después en la landing.

**Fundadores** pasa de «cinco marcas con el servicio» a **acceso anticipado de la plataforma**: 25 plazas
(`site/build.py` `CONFIG["seats"]`), precio congelado doce meses, Memoria de marca redactada con nosotros, voto en el
roadmap, logo y canal directo, a cambio de caso publicable, testimonio y dos sesiones de feedback.

**Cliente A** (decisión 6, resuelta): su propuesta en curso sigue tal cual como **Studio**; cuando la plataforma exista se
le ofrece Brand con su Memoria ya hecha. Nada que cambiar ni frenar.

---

## 12. Plan por fases

**Fase 0 — Posicionamiento (días).** Reescribir hero, pasos y bento de la landing en vivo con el enfoque nuevo (sitio
estático actual, `build.py`), quitar la tabla de precios del servicio o convertirla en «acceso anticipado», formulario de
lista de espera (listmonk o el Worker del formulario), condiciones con aviso «versión en revisión». Mantener KB y curso. Es
lo primero porque hoy la web vende lo contrario de lo que se va a construir.

**Fase 1 — MVP de plataforma (3–4 semanas).** Hecho cuando una marca nueva, sin ayuda, se da de alta, paga, rellena su
Memoria asistida, crea una campaña, conecta Claude Code con un clic, monta la campaña con el plugin, la entrega y la revisa
en la web.
1. *Spike* (1 día): Think28 ID + MCP remoto + Claude Code `/mcp` de punta a punta; Paddle en sandbox con `product=frame28`.
2. Repo `frame28-app` (monorepo: `web/` Next.js, `api/` FastAPI + MCP, `db/`, `deploy/`): cuenta, membresía, Memoria v1
   con onboarding asistido, campañas y entregables, R2, revisión básica.
3. Plugin v0.5 (cáscara, §7 bis): `.mcp.json` remoto, `hooks.json` (SessionStart avisa del estado de la cuenta; PreToolUse
   bloquea render con marca ajena sin licencia), skills mínimas que llaman a `frame28_start`; el MCP sirve el método del
   director por plan y la Memoria; CLI: `frame28 deliver`, `frame28 context apply`, `frame28 license set/whoami` (token de
   72 h) y modo demo. Pruebas de las nuevas órdenes.
4. Landing nueva en Next.js con el hero vivo y migración de KB y curso (MDX) tras la membresía.
5. Despliegue en `/opt/frame28` (compose nuevo), Turnstile, Plausible, uptime-kuma; `deploy.sh` evoluciona a imágenes.

**Fase 2 — Equipo y agencia (semanas 5–8).** Puestos y roles, varias marcas, enlaces de revisión externos, comentarios con
marca de tiempo, copy de publicación, aprendizaje de ganchos manual, token de API para Team/CI, remote MCP también desde
claude.ai (sin render: dirección y revisión).

**Fase 3 — Frame28 Cloud (cuando haya demanda).** Worker `frame28-engine` en caja aparte, Claude vía API como director con
las mismas skills, subir vídeo → campaña sin Claude Code; conectores de analíticas.

---

## 13. Riesgos y cómo se cubren

| Riesgo | Cobertura |
|---|---|
| El motor es MIT: alguien quita la tarjeta final o copia el plugin | El valor está en la cuenta (Memoria, campañas, aprendizaje, nube), no en el código; se vigila el uso y se decide licencia de versiones nuevas si hace falta |
| Términos de Anthropic para plugins y MCP comerciales y uso de la suscripción de Claude Code del cliente | Revisar los términos vigentes antes de la fase 1; el cliente usa **su** Claude Code (su licencia); Frame28 vende contexto y servicio, no acceso a Claude. Para la nube (fase 3), API con nuestra clave |
| Dependencia de Entra External ID | Es la misma que Synapse28; el MCP valida JWT estándar: cambiar de IdP es cambiar el emisor. La vía token de API es independiente |
| Capacidad del VPS | La app cabe (≈0,7 GB); el render cloud va a una caja aparte; vídeo en R2, no en disco |
| Privacidad de los vídeos del cliente | R2 con jurisdicción UE si se exige, URLs firmadas y caducas, borrado por campaña, RLS por tenant; contrato con encargo de tratamiento (las condiciones ya lo traen) |
| El onboarding asistido inventa cosas | Cada campo propuesto lleva su origen (URL, segundo del vídeo) y el cliente confirma; nada sale al vídeo sin estar en la Memoria aprobada |
| Dos caminos de auth (OAuth y token) | El token es solo para Team/CI; el producto principal es OAuth. Documentado en la página «Conectar» |
| Legal del SaaS | Nuevas condiciones (suscripción, uso aceptable, datos) con el asesor; hasta entonces la landing dice «en revisión» |

---

## 14. Decisiones que necesita Javier

1. **Posicionamiento y copy del hero** (§10): ¿aplicamos la fase 0 a la landing en vivo esta semana?
2. **Tiers y cifras** (§11): validar estructura y rangos, o pedir una propuesta cerrada.
3. **Think28 ID**: ¿reutilizar el tenant CIAM de Synapse28 (una identidad para todo el ecosistema) o uno nuevo para Frame28?
4. **Open core**: ¿CLI y plugin base siguen MIT (recomendado) o se cierra el código de las versiones nuevas?
5. **Repo**: ¿`frame28-app` aparte (recomendado: ciclo y permisos distintos) o monorepo con el plugin?
6. **Cliente A**: ¿se le presenta ya como primer cliente Brand/Studio del modelo nuevo, con la segunda muestra como prueba?

---

## 15. Fuentes

- Claude Code: referencia del manifiesto de plugins (`code.claude.com/docs/en/plugins-reference`) y MCP
  (`code.claude.com/docs/en/mcp`), consultadas el 2026-10-01: `mcpServers`, `.mcp.json`, `userConfig` sensible,
  `${CLAUDE_PLUGIN_DATA}`, `bin/` y claude.ai, OAuth con cliente preconfigurado, `headersHelper`, `/mcp`.
- Memorias de Synapse28 (mismo PC): arquitectura (FastAPI, Postgres RLS, cola en Postgres), auth (Entra External ID CIAM,
  auditoría), Paddle (código completo, filtrado por producto, bootstrap), despliegue (git archive, túnel).
- Sondeo de los 22 sitios de referencia (HTML y cabeceras) y del VPS t28server (RAM, CPU, contenedores) el 2026-10-01.
- `research/06` (monetización) y `research/07` (producto frame28.app, superado en §2–3 por este documento).
