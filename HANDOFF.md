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
Primer cliente objetivo: **Cliente A** (the-brand.com, kits de grabado, EE. UU.), que hoy solo sabe que existimos;
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
6. **Giro a producto** tras un brainstorming con t28.io y the-brand.com leídas: `research/07` con definición de
   producto, capas Open/Launch/Studio/Team/Cloud con precios early adopter propuestos, programa Fundadores,
   garantía, lo que Cliente A compraría, base de conocimiento y mini curso, arquitectura del sitio frame28.app en
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

## Qué quedó a medias o sin hacer

Decisiones conscientes:

1. **Precios y capas de `research/07` sin validar por el usuario.** Los commits ya están en `origin/main` (repo
   público): si Javier corrige los números, se edita `research/07` §2 y la landing será la fuente pública.
2. **Landing frame28.app**: no existe todavía la carpeta `site/`; el dominio está en Cloudflare; la arquitectura y
   las rutas están en `research/07` §5. Es el día 2 del plan.
3. **Propuesta a Cliente A**: borrador en inglés en `research/07` anexo; no enviada. El caso (largo, shorts,
   portada, ES) existe en `poc/clip-grabado/out` pero no hay permiso para publicarlo.
4. **Base de conocimiento y mini curso**: solo planificados (`research/07` §4); las fuentes ya existen en
   `plugin/skills/frame28-storyboard/references/` (`grabacion.md`, `ganchos.md`, `marca-y-promocional.md`,
   `tecnicas.md`) y en `plugin/cli/frame28/STORYBOARD.md`.
5. **Tarjeta de Frame28 en el ecosistema de t28.io**: pendiente (la web de Think28 no está en este repo).

Deuda técnica, por orden:

6. **Suite de pruebas: hecha** (82, ver §Estado). Fuera de ella: render, `matte`, `gestures`, `graphics` (OCR), `reframe`
   con vídeo real, `broll` contra la API. Regla: cada bug nuevo entra con su prueba en `plugin/cli/tests/`.
7. **B-roll sin probar contra la API real**: faltan claves de Pexels/Pixabay (`~/.config/frame28/keys.json` o
   `PEXELS_API_KEY`/`PIXABAY_API_KEY`); `plugin/cli/frame28/broll.py::search`.
8. **Pendientes pequeños**: `reframe-map` hecho pero sin probar con un `gestures.json` real (solo sintético en tests);
   `clips.py:176 hooks_for` da plantilla de curiosidad en tramos sin momentos; `chart bar` en vertical con más de
   tres filas; `reframe --mode crop` sin probar con hablante en movimiento; cuadrado 1:1 sin caso documentado
   (`research/05` #7); marcadores de resultado (`research/05` #8); `docs/install.sh` sin Mac real.
9. **Deuda menor**: GSAP por CDN sin copia local ni SRI (`build.py` líneas 785–801, `cover.py:89`; el render
   necesita red); HyperFrames 0.8.72 pineado con 0.8.98 publicada; OpenCV instalado por triplicado (arrastrado por
   mediapipe y rapidocr; cv2 5.0.0 con pin `>=4.9`); `poc/remotion/package-lock.json` versionado aunque Remotion está
   descartado.

## Bloqueos y dudas

| Bloqueo o duda | Dueño | Qué lo desbloquea |
|---|---|---|
| Validar precios, capas, garantía y programa Fundadores (`research/07` §2) | Javier | Su OK o sus correcciones; entonces push y landing |
| Acceso a Cloudflare (Pages, Access, Email Service) para frame28.app | Javier | Autorizar cada paso o desplegar él; Claude prepara `site/` y la configuración |
| Permiso de Cliente A para publicar el caso | Javier con Cliente A | Hasta entonces la página del caso es privada |
| Claves de Pexels y Pixabay | Javier | Crearlas en pexels.com/api y pixabay.com/api/docs |
| Términos de la suscripción de Claude para uso profesional del servicio | Javier | Revisar los términos vigentes; para Cloud, API |
| Horas disponibles para operar el piloto en una semana | Javier | Fija si Launch se entrega en cinco días laborables |
| Cuenta de `gh`: la activa es la corporativa | Claude al pushear | `gh auth switch --user javierledesma28`, push, y volver |
| Seis decisiones de `research/06` §8 | Javier | Tres ya respondidas el 2026-09-30: marca Frame28.app, segmento DTC con puerta corporativa abierta, piloto pagado a precio early adopter; quedan quién opera, umbrales para Cloud y qué sigue abierto (propuesto: todo) |

## Próximos pasos, por prioridad

Plan de siete días de `research/07` §6, con lo necesario para ejecutarlo:

1. **Día 1 — validar y escribir.** Javier valida `research/07` §2. Claude: textos de la landing en ES y EN
   (promesa "Envías un vídeo. Recibes la campaña." / "Send the video. Get the campaign."), contrato base y
   derechos (material del cliente, stock con licencia por vídeo, entregables del cliente). Push de los commits
   pendientes: `gh auth switch --user javierledesma28 && git push origin main && gh auth switch --user javierledesmasmc`.
2. **Día 2 — landing.** Carpeta `site/` con `/`, `/fundadores`, `/casos/cliente-a` (privada hasta el permiso),
   `/contacto` (Pages Functions + Email Service), redirecciones `/roadmap` y `/plugin`. Cloudflare Pages con raíz
   `site/` y dominio frame28.app (skills `cloudflare`, `wrangler`, `cloudflare-email-service` disponibles).
   Tarjeta en t28.io.
3. **Día 3 — propuesta y caso.** One-pager en inglés desde el anexo de `research/07`, enlaces a las muestras de
   `poc/clip-grabado/out` (subirlas a un sitio privado o al artefacto), página del caso.
4. **Día 4 — base de conocimiento y lección 1.** Ocho artículos desde las referencias del plugin en `site/kb/`
   tras Cloudflare Access (código por email); guion del curso; Javier graba la lección 1 y se monta con Frame28.
5. **Día 5 — v0.4.0 mínima para el servicio.** Suite de pruebas hecha (adelantada); quedan claves de B-roll y prueba
   real, registro de coste y tiempo por vídeo, variantes de gancho en lote (`clips scaffold --hook N` para cada
   gancho y render en cadena).
6. **Día 6 — muestra de acrílico.** `frame28 fetch` del tutorial de acrílico de Cliente A, flujo de vídeo producido
   (`graphics`, marca `cliente-a` regenerada con `brand from-site`), largo, shorts, portada, ES y DE.
7. **Día 7 — enviar.** Propuesta a [[buzon-partners-cliente]] y a [[fundador]] (fundador) por LinkedIn; abrir Fundadores.

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
