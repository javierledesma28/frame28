# Traspaso — estado del proyecto a 2026-09-30

Para retomar Frame28 desde otra cuenta de Claude Code **sin historial de conversación**, sobre este mismo
repositorio local. Lee primero [CLAUDE.md](CLAUDE.md) (qué es, estructura, cómo se ejecuta, convenciones,
trampas). Este fichero es el estado verificado, lo hecho por sesiones, lo que quedó a medias, los bloqueos y los
próximos pasos. `main` está sincronizado con `origin/main` (los commits con precios propuestos ya subieron con la
mudanza a la nube); la sesión en la nube del 2026-09-30 (noche, 2) trabaja en la rama `main-ky21ae` (ver §Sesiones).

## Qué es esto y por qué

**Frame28** es un producto de **Think28** (empresa de Javier Ledesma, `https://t28.io`; consultora B2B de cloud e
IA con un ecosistema de productos propios: Hub28, T28 AI, Synapse 28, Augusta y ahora Frame28). Convierte un vídeo
de una persona hablando a cámara, o un vídeo ya producido, en el paquete que hace falta para vender: el largo
montado con la marca, shorts verticales con ganchos distintos, portada y ficha de producto, subtítulos y
versiones en otros idiomas con los mismos tiempos. Dos piezas: un **plugin de Claude Code** (ocho skills; Claude
dirige y escribe el storyboard JSON) y un **CLI Python `frame28`** (los pasos deterministas). El compositor es
**HyperFrames** (HTML + GSAP), todo en local y en CPU. El plugin y el CLI son MIT y públicos.

**Giro del 2026-09-30 (noche):** Frame28 deja de ser "un plugin sin monetizar" y pasa a ser un **producto
monetizable** con dominio **frame28.app** (comprado en Cloudflare; el plugin abierto sigue en frame28.t28.io).
Primer cliente objetivo: **Cliente A** (nombre en clave; marca de kits de grabado, EE. UU.), que hoy solo sabe que existimos;
objetivo: piloto en **una semana** desde el 2026-09-30. La oferta se vende como servicio operado por Think28
(Launch, Studio), implantación en el cliente (Team) y, solo con demanda demostrada, plataforma (Cloud). Todo en
[research/07-producto-frame28-app.md](research/07-producto-frame28-app.md); el análisis previo de caminos en
[research/06-monetizacion.md](research/06-monetizacion.md). **Regla de trabajo explícita del usuario:** todo lo que se
aprende con un caso, un vídeo o un diagnóstico se capitaliza en el plugin (CLI, `doctor`, validaciones, skills y
referencias), no se queda en un README ni en este fichero.

## Estado: qué funciona hoy (verificado el 2026-09-30, noche)

| Qué | Evidencia |
|---|---|
| Versión publicada | **v0.3.0**: tag sobre `f178d0c`, release https://github.com/javierledesma28/frame28/releases/tag/v0.3.0 marcada Latest; v0.1.0 y v0.2.0 anteriores |
| Versión en ficheros | 0.3.0 en `plugin/cli/frame28/__init__.py` (fuente; pyproject la lee con hatch), `plugin/.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` y README; `python scripts/release-check.py` da versiones coincidentes y marca tag y release de la 0.3.0 como ya existentes (correcto: hay que subir `__version__` antes de la próxima etiqueta) y avisa de la cuenta `gh` |
| CLI instalado | `frame28 --version` 0.3.0, editable desde `plugin/cli`; `frame28 doctor` "Todo listo" (ffmpeg 9.0.2, Node 24.13.1, faster-whisper 1.2.1, onnxruntime 1.30.0 CPU, cv2 5.0.0, RVM en caché, red al CDN de GSAP); 38 órdenes en 20 módulos |
| Instalación limpia desde el tag | `uvx --from "git+https://github.com/javierledesma28/frame28@v0.3.0#subdirectory=plugin/cli" frame28 --version` construye y responde 0.3.0 en 21 s |
| Plugin | `claude plugin validate ./plugin` pasa; instalado 0.3.0 a nivel usuario desde el marketplace local; caché idéntica al repo |
| Storyboards | 11 de 11 versionados válidos (`frame28 storyboard validate`) |
| Regresión | `poc/clip-javier/storyboard-gsap.json`: build 1 s, check pasa en 88 s, render 111 s (10 s a 1080p en CPU), portada con `frame28 cover` correcta |
| Smoke de módulos | `cut plan` (fixture nuevo, formato antiguo en ms y fichero roto con error corto), `cut apply`, `gestures`, `captions pages/export`, `clips plan`, `broll suggest`, `i18n extract`: funcionan |
| Pruebas automatizadas | **82 en verde en 0,3 s** (`cd plugin/cli && uv run --group dev pytest`): captions, cut, clips, i18n, build (validate, platform_warnings, build_project sobre los 11 storyboards versionados), reframe (camera_path, map_*), smoke del CLI; `scripts/release-check.py` las ejecuta como fila bloqueante |
| Web | https://frame28.t28.io/ `/presentacion/` `/instalar/` `/roadmap/` responden 200; portada, diapositiva de cierre y README enlazan el roadmap |
| Roadmap visual | `docs/roadmap/index.html`: 6 versiones, 56 ítems (24 hechos, 2 a medias, 30 pendientes), filtro por estado; artefacto privado https://claude.ai/artifact/CxhtKMffGhQRsKUhAqwUS8 (versión 2) |
| Git | `main` = `origin/main` (`9a086c6`); la sesión en la nube empuja a `main-ky21ae` (rama de trabajo; fusionar en `main` es decisión de Javier). En el PC la cuenta activa de `gh` quedó en `javierledesma28` |
| Casos reales | `poc/clip-javier`, `clip-auriculares`, `clip-whatsapp`, `clip-demo`, `clip-grabado` (largo, 3 shorts, portada, versión ES en `poc/clip-grabado/out`, no versionados) |

## Qué se ha hecho, por sesiones

### Sesiones 2026-09-24 a 2026-09-29 — research, plugin base, v0.1.0 y v0.2.0
Análisis del vídeo de referencia, repos, PoC HyperFrames vs Remotion, roadmap de 18 features (`research/01`–`04`);
plugin con 5 skills y CLI base; brand kit, gráficas, gestos, jump cuts, limpieza de audio, GSAP con plugins; repo
público limpio, GitHub Pages con dominio, deck de guía, instaladores; releases v0.1.0 y v0.2.0.

### Sesión 2026-09-30 (madrugada) — instalación y subtítulos
Anuncio de auriculares; guion de demo; instaladores interactivos y asistente web; lienzo vertical y cuadrado;
subtítulos por palabras (`pages`/`karaoke`) y SRT/VTT; demo del plugin montada; `cut plan` más fino; B-roll
(overlay, CLI, skill; sin claves).

### Sesión 2026-09-30 (mañana) — caso Cliente A y vídeos producidos
`fetch`, brief de marca, `brand from-site`, dos pasadas del montaje, rótulo sin recortes, `kinetic.color`, avisos de
cajas fuera del lienzo, referencia marca-y-promocional; `graphics` (OCR, zonas libres, colisiones); `reframe`.

### Sesión 2026-09-30 (tarde) — vídeo que vende
`research/05`; overlays hook/cta/steps/before_after; zonas seguras; fábrica de shorts (`clips`) y skill; referencia
de ganchos; tres variantes de short; `cover`; `i18n` y skill; ganchos con la frase real; bump a 0.3.0 en ficheros.

### Sesión 2026-09-30 (noche) — relevamiento, higiene y release 0.3.0, roadmap, monetización, giro a producto
1. **Relevamiento completo** sin tocar nada (46 commits, 142 ficheros, todo verificado ejecutando). Hallazgos:
   bump incompleto (`__init__.py` en 0.2.0), fixture de clip-javier en milisegundos que hacía reventar `cut plan`,
   dominio `think28.app` muerto en manifiestos, docs desfasadas, cero tests, render dependiente del CDN de GSAP.
2. **Higiene 0.3.0** (commit `ad8682a`): versión única en `__init__.py` con pyproject dinámico; cargador único y
   tolerante `captions.normalize_words/load_words/load_captions` usado en cut, clips, i18n, pose, broll y build, con
   `TranscriptFormatError` y punto de entrada `cli:run` que lo muestra sin traza; `doctor` con deriva de versión,
   HyperFrames pineado, red al CDN y filas opcionales; `GSAP_VERSION`; `scripts/release-check.py`; fixture
   normalizado; `t28.io` en pyproject y marketplace; CLAUDE.md, guía del plugin y asistente al día.
3. **Tag y release v0.3.0** publicados con el OK del usuario; plugin local reinstalado; instalación limpia desde el
   tag verificada.
4. **Roadmap visual** `docs/roadmap/index.html` (Think28, datos inline, filtro), publicado en frame28.t28.io/roadmap/
   y como artefacto; enlazado desde la portada, la diapositiva de cierre de la guía (deck reconstruido) y el README.
5. **Monetización**: `research/06` (tres caminos dimensionados, recomendación híbrida por fases, plan de 90 días),
   versionado por decisión del usuario aunque el repo sea público.
6. **Giro a producto** tras un brainstorming con t28.io y la web del Cliente A leídas: `research/07` con definición de
   producto, capas Open/Launch/Studio/Team/Cloud con precios early adopter propuestos, programa Fundadores,
   garantía, lo que el Cliente A compraría, base de conocimiento y mini curso, arquitectura del sitio frame28.app en
   Cloudflare Pages, plan de siete días y borrador de propuesta en inglés. Roadmap actualizado con los ítems de
   producto (v0.4.0), Frame28 Team (v0.5.0) y Frame28 Cloud (v1.0.0).
7. Memoria persistente de Claude actualizada (producto frame28.app, regla de capitalizar en el plugin).

### Sesión 2026-09-30 (noche, 2; en la nube, rama `main-ky21ae`) — suite de pruebas y `reframe-map`
Sin validación de precios todavía, se adelantó lo del día 5 que no depende de Javier:
1. **Suite de pruebas** `plugin/cli/tests/` (pytest en el grupo `dev` del pyproject; 82 pruebas, 0,3 s, sin ffmpeg ni
   modelos): cargadores y subtítulos, `cut.plan` con WAV sintético (silencios, muletillas, falsos arranques, estructuras
   paralelas), remapeo, shorts y ganchos con `poc/clip-grabado/clips.json`, i18n de extremo a extremo, validación de
   los 11 storyboards versionados y errores típicos, avisos de plataforma, `build_project` de clip-javier (ids, plugins
   GSAP, sin tweens de left/top), reencuadre y smoke del CLI con `CliRunner`. `release-check` la ejecuta.
2. **Dos bugs que salieron al escribirlas, arreglados con su regresión**: `cut.remap_storyboard` comparaba los cortes
   con los tiempos ya remapeados del `behind` (un corte al final de la máscara alfa no avisaba); `i18n extract` no
   marcaba como residual una frase sin ninguna palabra oída (ahora `note` + `visible: ""`).
3. **`frame28 reframe-map`** (ítem "Callouts del original al vertical" del roadmap): `reframe.json` (de `reframe --path`)
   + `gestures.json` del apaisado → los mismos `pointer` en el lienzo vertical, con `visible: false` en los que señalan
   fuera del encuadre en modo crop; también `--point x,y,t` sueltos. Documentado en las skills director y shorts.
4. Roadmap: "Suite mínima de pruebas" y "Callouts del original al vertical" en hecho; el siguiente es B-roll real.
   CLAUDE.md, README y README del CLI al día. El artefacto del roadmap en claude.ai no se republicó desde aquí.

### Sesión 2026-10-01 (nube) — precios validados, landing, contrato y sitio
Javier validó precios y capas y pidió fusionar en `main`. Después: textos de la landing ES/EN (`site/content/`),
contrato base ES/EN (`site/content/condiciones.es.md`, `terms.en.md`) y el sitio completo en `site/` (día 2):
`build.py` con plantilla común y CONFIG, ocho páginas, formulario con Pages Function y binding `send_email`,
redirecciones, cabeceras de seguridad, `wrangler.toml` y README de despliegue. Verificado con Chromium (Playwright)
a 1280 y 390 px: sin desbordes ni errores de JS propios. Pendiente de Javier: desplegar en Cloudflare Pages.

### Sesión 2026-10-01 (nube, continuación) — confidencialidad, propuesta, base de conocimiento y curso
Anonimización del cliente en árbol e historial (ver §Confidencialidad); propuesta entregada fuera del repo; día 4:
base de conocimiento (8×2) y curso online (6×2) en `site/`, incluidos en todas las capas de pago, con el
generador extendido (`render_section`: índices, páginas, anterior/siguiente, bloque de vídeo, noindex).
Día 5 (nube): `log.py` + `frame28 report`, `clips batch`, ganchos `statement`, fila de B-roll en `doctor`, 90 pruebas.

## Confidencialidad del primer cliente (regla de Javier, 2026-10-01)

El cliente objetivo **no se nombra en ningún fichero del repo ni del sitio** (el repo es público y la captación va
en paralelo). Nombre en clave: **Cliente A**; producto: **Engraver Pro™**; web: `the-brand.com`; carpeta del caso:
`poc/clip-grabado`; marca local `cliente-a` (en `work/`, no versionada). Cifras y títulos de vídeo del cliente van
difuminados o parafraseados. La propuesta comercial (email, one-pager, seguimiento) vive **fuera del repo**, en
los ficheros de Javier. El sitio publica el caso anónimo hasta tener permiso escrito (`site/build.py`
`CONFIG["case_public"]` + `case_brand`). El árbol de trabajo se limpió el 2026-10-01 (script de anonimizado con
comprobación final) y **el historial de git se reescribió el mismo día con `git filter-repo`** (rutas, contenidos y
mensajes de los 62 commits; tags v0.1.0–v0.3.0 recreados; push forzado de `main` y `main-ky21ae`): cero coincidencias
en todos los objetos. Los hashes cambiaron: **el clon del PC de Javier debe resincronizarse** (`git fetch origin &&
git checkout main && git reset --hard origin/main`; los tags los trae `mover-tags.sh` desde el bundle). Los tags
v0.2.0 y v0.3.0 remotos los mueve Javier con ese script (ver §Bloqueos). Copia previa del repo en un bundle fuera del repo.

## Qué quedó a medias o sin hacer

Decisiones conscientes:

1. **Precios y capas de `research/07` §2: validados por Javier el 2026-10-01** ("están bien"). Son la base de la
   landing, que será la fuente pública cuando exista; cualquier cambio futuro se hace primero en `research/07` §2.
2. **Landing frame28.app**: HTML listo en `site/` (8 páginas ES/EN generadas por `site/build.py`, formulario con
   `functions/api/contact.js`, `_redirects`, `_headers`, `wrangler.toml`); verificado en Chromium a 1280 y 390 px
   (sin desbordes, HTML equilibrado). **Falta desplegar**: proyecto en Cloudflare Pages (root `site`), dominio
   frame28.app, remitente `hola@frame28.app` verificado y binding `SEND_EMAIL` (pasos en `site/README.md`; el
   API de envío de Email Service no se pudo verificar desde la nube: docs de Cloudflare bloqueadas por el proxy).
   También falta `site/assets/og.png` (1200×630) y la página del caso (`CONFIG["case_public"]`).
3. **Propuesta al Cliente A**: escrita el 2026-10-01 y entregada a Javier fuera del repo (no se versiona: nombra al
   cliente). El caso (largo, shorts, portada, ES) existe en `poc/clip-grabado/out` pero no hay permiso para publicarlo.
4. **Base de conocimiento y curso online**: escritos y generados en `site/` (día 4): 8 artículos ES/EN en
   `site/content/kb/` y 6 lecciones ES/EN en `site/content/curso/` (lección 1 con guion completo de 8 min; 2–6 con
   esquema, frases clave, qué pone el montaje en pantalla y tarea). Incluidos en **todas** las capas de pago (Launch 12
   meses, Studio y Team activos): landing, condiciones y `research/07` §2/§4 actualizados. Faltan: grabar los vídeos
   (campo `video:` de cada lección; Javier graba la 1 y se monta con Frame28) y activar Cloudflare Access sobre las
   cuatro rutas (pasos en `site/README.md`); hasta entonces las páginas son públicas aunque lleven noindex.
5. **Tarjeta de Frame28 en el ecosistema de t28.io**: pendiente (la web de Think28 no está en este repo).

Deuda técnica, por orden:

6. **Suite de pruebas: hecha** (82, ver §Estado). Fuera de ella: render, `matte`, `gestures`, `graphics` (OCR), `reframe`
   con vídeo real, `broll` contra la API. Regla: cada bug nuevo entra con su prueba en `plugin/cli/tests/`.
7. **B-roll sin probar contra la API real**: faltan claves de Pexels/Pixabay (`~/.config/frame28/keys.json` o
   `PEXELS_API_KEY`/`PIXABAY_API_KEY`); `plugin/cli/frame28/broll.py::search`. `frame28 doctor` ya avisa (fila opcional).
   **`clips batch` con render sin probar en real** (solo `--no-render` en la suite): primera prueba sobre `poc/clip-demo`.
   **Tokens del director**: el CLI no los ve; el director los anota con `frame28 report note --tokens` (skill, paso 8).
8. **Pendientes pequeños**: `reframe-map` hecho pero sin probar con un `gestures.json` real (solo sintético en tests);
   `chart bar` en vertical con más de
   tres filas; `reframe --mode crop` sin probar con hablante en movimiento; cuadrado 1:1 sin caso documentado
   (`research/05` #7); marcadores de resultado (`research/05` #8); `docs/install.sh` sin Mac real.
9. **Deuda menor**: GSAP por CDN sin copia local ni SRI (`build.py` líneas 785–801, `cover.py:89`; el render
   necesita red); HyperFrames 0.8.72 pineado con 0.8.98 publicada; OpenCV instalado por triplicado (arrastrado por
   mediapipe y rapidocr; cv2 5.0.0 con pin `>=4.9`); `poc/remotion/package-lock.json` versionado aunque Remotion está
   descartado.

## Bloqueos y dudas

| Bloqueo o duda | Dueño | Qué lo desbloquea |
|---|---|---|
| ~~Validar precios, capas, garantía y programa Fundadores (`research/07` §2)~~ | Javier | **Validados el 2026-10-01**: desbloquea landing, contrato y propuesta |
| Acceso a Cloudflare (Pages, Access, Email Service) para frame28.app | Javier | Autorizar cada paso o desplegar él; Claude prepara `site/` y la configuración |
| **Tags v0.2.0 y v0.3.0 en GitHub apuntan todavía a la historia antigua** (el proxy de la nube no permite mover ni borrar tags: 403 por git y por API). Mientras tanto la historia vieja sigue alcanzable | Javier, desde su PC | Claude le entregó `tags-reescritos.bundle` (los dos tags reescritos, con autor y fecha originales) y `mover-tags.sh`: resincroniza `main`, importa los tags del bundle, `gh auth switch --user javierledesma28`, `git push --force origin refs/tags/v0.2.0 refs/tags/v0.3.0`, y verifica con un clon limpio (62 commits, 0 coincidencias). Los commits destino (`a38672b`, `264777d`) ya están en `origin/main`. La release v0.3.0 queda enganchada al tag nuevo |
| Commits antiguos cacheados en GitHub tras la reescritura (accesibles por hash hasta su recolección) | Javier | Pedir a soporte de GitHub la purga del repo, si se quiere cerrar del todo |
| Permiso del Cliente A para publicar el caso | Javier con el cliente | Hasta entonces la página del caso es privada |
| Claves de Pexels y Pixabay | Javier | Crearlas en pexels.com/api y pixabay.com/api/docs |
| Términos de la suscripción de Claude para uso profesional del servicio | Javier | Revisar los términos vigentes; para Cloud, API |
| Horas disponibles para operar el piloto en una semana | Javier | Fija si Launch se entrega en cinco días laborables |
| Cuenta de `gh`: la activa es la corporativa | Claude al pushear | `gh auth switch --user javierledesma28`, push, y volver |
| Seis decisiones de `research/06` §8 | Javier | Tres ya respondidas el 2026-09-30: marca Frame28.app, segmento DTC con puerta corporativa abierta, piloto pagado a precio early adopter; quedan quién opera, umbrales para Cloud y qué sigue abierto (propuesto: todo) |

## Próximos pasos, por prioridad

Plan de siete días de `research/07` §6, con lo necesario para ejecutarlo:

1. **Día 1 — validar y escribir.** Precios validados (2026-10-01). Textos de la landing en ES y EN escritos en
   `site/content/landing.es.md` y `landing.en.md` (hero, para quién, tres pasos, entregables, precios con las cifras
   de `research/07` §2, Fundadores, caso en dos versiones (con permiso / anónima), cómo lo hacemos, roadmap, FAQ,
   contacto con microcopy del formulario, pie, páginas /fundadores y /contacto, textos cortos). Huecos `[[…]]`:
   plazas de Fundadores, enlaces a las muestras, buzón `hola@frame28.app` por confirmar. **Contrato base** escrito
   en `site/content/condiciones.es.md` y `terms.en.md` (18 cláusulas con la misma numeración en ES y EN: capas y
   precios, proceso con aprobación tácita a 10 días laborables, garantías del cliente sobre su material, rondas de
   cambios, stock y herramientas (incluye el uso de Claude con transcripción y fotogramas), pago, garantía de Launch,
   propiedad intelectual (cesión al pago; Think28 conserva software, storyboards y know-how), confidencialidad,
   RGPD con encargo y subencargados, responsabilidad limitada, Fundadores, ley española; anexos: hoja de pedido,
   lista de comprobación de derechos, encargo del tratamiento). **Pendiente de revisión por un asesor legal** y de
   las decisiones marcadas `[[…]]`: datos fiscales, ciudad del fuero, idioma que prevalece, música como complemento,
   arrastre de vídeos en Studio, medio de pago, tratamiento fiscal fuera de la UE, términos vigentes de Anthropic.
   La landing enlaza `/condiciones` y `/terms` y ya no dice "tu vídeo no sale de nuestras máquinas" a secas: dice
   que se procesa en nuestros equipos y que la dirección usa modelos de lenguaje con transcripción y fotogramas.
2. **Día 2 — landing.** Hecho el sitio (`site/`: `/`, `/en/`, `/fundadores`, `/contacto`, `/condiciones` y sus
   equivalentes EN; `/casos/*` redirige al contacto hasta el permiso; `/roadmap` y `/plugin` redirigen a
   frame28.t28.io). Queda el despliegue en Cloudflare Pages con raíz `site` y dominio frame28.app, el remitente
   y el binding de email (pasos en `site/README.md`; lo hace Javier o se autoriza paso a paso), `og.png` y la
   tarjeta en t28.io.
3. **Día 3 — propuesta y caso.** One-pager en inglés desde el anexo de `research/07`, enlaces a las muestras de
   `poc/clip-grabado/out` (subirlas a un sitio privado o al artefacto), página del caso.
4. **Día 4 — base de conocimiento y lección 1.** Hecho lo escrito (artículos, guiones, páginas); queda que Javier
   grabe la lección 1 (guion en `site/content/curso/es/01-que-es-frame28.md`), montarla con Frame28 y poner la URL
   en `video:`; y activar Access.
5. **Día 5 — v0.4.0 mínima para el servicio.** Hecho en la nube: suite (90 pruebas), registro de tiempo por orden y
   `frame28 report` (+ `report note` para tokens y minutos de persona; `--rate` estima el coste), `frame28 clips
   batch` (variantes de gancho en lote con manifiesto), ganchos `statement` para tramos sin momentos, fila de claves
   de B-roll en `doctor`. Queda lo que exige el PC de Javier: crear las claves de Pexels/Pixabay y probar `broll
   search`/`fetch` reales, y pasar `clips batch` con render sobre `poc/clip-demo` (en la nube no hay HyperFrames ni red al CDN).
6. **Día 6 — muestra de acrílico.** `frame28 fetch` del segundo tutorial del Cliente A, flujo de vídeo producido
   (`graphics`, marca `cliente-a` regenerada con `brand from-site`), largo, shorts, portada, ES y DE.
7. **Día 7 — enviar.** Propuesta al Cliente A (buzón de partners y fundador por LinkedIn; datos fuera del repo); abrir Fundadores.

Después de la semana: resto de la v0.4.0 (doblaje/TTS, marcadores de resultado, `hooks_for`) y
mantener el roadmap cambiando el estado de cada ítem en el array `ROADMAP` de `docs/roadmap/index.html`, regenerar
la variante de artefacto (marcadores `artifact:head`/`artifact:body`) y republicarla pasando su URL.

## Para retomar sin sorpresas

```bash
frame28 doctor                                   # fila frame28: 0.3.0 en código y 0.3.0 instalada (editable); "Todo listo."
claude plugin validate ./plugin                  # Validation passed
python scripts/release-check.py --notes          # versiones 0.3.0 coincidentes; tag local, tag remoto y release v0.3.0 "ya existe/ya publicada" (normal hasta subir __version__); pytest en verde; aviso de cuenta gh
(cd plugin/cli && uv run --group dev pytest)     # 82 passed en < 1 s
cd poc/clip-javier && frame28 cut plan words.json --audio voice.wav -o work/cuts.json     # 9.94 s -> 9.49 s, 1 tramo
cd poc/clip-javier && frame28 build storyboard-gsap.json -o work/f28-gsap && frame28 check work/f28-gsap && frame28 render work/f28-gsap -o out/test.mp4   # 13 overlays, check pasa, ~2 min
curl -sI https://frame28.t28.io/roadmap/ | head -1     # HTTP/2 200
git status -sb                                    # ## main...origin/main (o main-ky21ae si se retoma la rama de la nube)
```

Si ffmpeg o uv no están en el PATH de la shell, el CLI los encuentra solo; para la shell, la línea `export PATH`
de las Trampas de `CLAUDE.md`. Si `frame28 --version` no dice 0.3.0: `uv tool install --editable ./plugin/cli
--python 3.12 --reinstall`. Si las skills `frame28:*` no aparecen en una sesión nueva: `claude plugin uninstall
frame28@think28 && claude plugin install frame28@think28 --scope user`.
