# Traspaso — estado del proyecto a 2026-10-01 (PC, con la v0.4.0 publicada)

Para retomar Frame28 desde otra cuenta de Claude Code **sin historial de conversación**, sobre este mismo
repositorio. Lee primero [CLAUDE.md](CLAUDE.md) (qué es, estructura, cómo se ejecuta, convenciones, trampas). Este
fichero es el estado verificado, lo hecho por sesiones, lo que quedó a medias, los bloqueos y lo que toca ahora.
`main` = `origin/main`; el tag `v0.4.0` está en `4e7a6cb`; árbol limpio.

## Qué es esto y por qué

**Frame28** es un producto de **Think28** (empresa de Javier Ledesma, `https://t28.io`; consultora B2B de cloud e
IA con un ecosistema de productos propios: Hub28, T28 AI, Synapse 28, Augusta y ahora Frame28). Convierte un vídeo
de una persona hablando a cámara, o un vídeo ya producido, en el paquete que hace falta para vender: el largo
montado con la marca, shorts verticales con ganchos distintos, portada y ficha de producto, subtítulos y
versiones en otros idiomas con los mismos tiempos. Dos piezas: un **plugin de Claude Code** (ocho skills; Claude
dirige y escribe el storyboard JSON) y un **CLI Python `frame28`** (los pasos deterministas). El compositor es
**HyperFrames** (HTML + GSAP), todo en local y en CPU. El plugin y el CLI son MIT y públicos.

**Giro del 2026-09-30:** Frame28 es un **producto monetizable** con dominio **frame28.app** (en Cloudflare; el
plugin abierto sigue en frame28.t28.io). Se vende como servicio operado por Think28 (Launch 990 USD, Studio
2.490 USD/mes), implantación en el cliente (Team 2.900 + 490 USD/mes) y, solo con demanda, plataforma (Cloud).
Precios y capas **validados por Javier el 2026-10-01** (`research/07` §2); el curso online y la base de conocimiento
van en todas las capas de pago. Primer cliente objetivo: **Cliente A** (nombre en clave, ver §Confidencialidad).
**Regla de trabajo de Javier:** todo lo que se aprende con un caso, un vídeo o un diagnóstico se capitaliza en el
plugin (CLI, `doctor`, validaciones, skills y referencias), no en un README ni en este fichero.

## Estado: qué funciona hoy (verificado el 2026-10-01 en el PC, Windows 11)

| Qué | Evidencia |
|---|---|
| Versión publicada | **v0.4.0** (release https://github.com/javierledesma28/frame28/releases/tag/v0.4.0, tag en `4e7a6cb`) |
| Versión en ficheros | 0.4.0 en `plugin/cli/frame28/__init__.py` (fuente; pyproject la lee con hatch), `plugin/.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` y README. Con la versión ya publicada, `python scripts/release-check.py` marca tag y release "ya existe" hasta subir `__version__` |
| CLI | 42 órdenes en 21 módulos; `frame28 --version` 0.4.0 y `frame28 doctor` "Todo listo" (sin GPU y sin claves de B-roll: filas opcionales) |
| Instalación limpia desde el tag | `uvx --from "git+https://github.com/javierledesma28/frame28@v0.4.0#subdirectory=plugin/cli" frame28 --version` → 0.4.0 en 23 s |
| Plugin | `claude plugin validate ./plugin` pasa; instalado 0.4.0 desde el marketplace local |
| Storyboards | 11 de 11 versionados válidos; los dos de `poc/clip-grabado` validan con la marca local `cliente-a` en `work/brands/` |
| Regresión | `poc/clip-javier/storyboard-gsap.json` con el código 0.4.0: build sin avisos, check pasa, render 89 s; hoja de contacto correcta |
| Pruebas automatizadas | **98 en verde en ~3 s** (`cd plugin/cli && uv run --group dev pytest`): captions, cut (WAV sintético), clips (ganchos, `batch --no-render`, `markers`), i18n, build (validate, platform_warnings, build_project), reframe (camera_path, map_*), log/report, smoke del CLI y la fila de confidencialidad de `release-check`. `release-check` las ejecuta como fila bloqueante |
| Web del plugin | https://frame28.t28.io/ `/presentacion/` `/instalar/` `/roadmap/` (GitHub Pages sobre `docs/`) |
| Roadmap | `docs/roadmap/index.html`: 6 versiones, 56 ítems (29 hechos, 4 a medias, 23 pendientes); 0.4.0 cerrada y marcada "estás aquí"; artefacto privado https://claude.ai/artifact/CxhtKMffGhQRsKUhAqwUS8 (versión 3, republicado el 2026-10-01) |
| Sitio del producto | `site/`: 40 páginas estáticas ES/EN (landing, Fundadores, contacto, condiciones, 8 artículos de base de conocimiento, 6 lecciones del curso), formulario con Pages Function, `og.png`, redirecciones y cabeceras; verificado en Chromium a 1280 y 390 px. **No desplegado** |
| Git | Historial reescrito; `main` = `origin/main`; tags `v0.1.0`–`v0.4.0` dentro de la historia de `main`. Un clon limpio no tiene rastro del cliente en mensajes, contenidos ni rutas. La rama `main-ky21ae` (de la sesión en la nube) quedó por detrás de `main` y se puede borrar. Cuenta activa de `gh` en el PC: la corporativa (`gh auth switch --user javierledesma28` antes de cada push) |
| Casos reales | `poc/clip-javier`, `clip-auriculares`, `clip-whatsapp`, `clip-demo`, `clip-grabado` (largo, 3 shorts, portada, versión ES en `poc/clip-grabado/out` del PC, no versionados; `work/`, `out/` e `input.mp4` movidos allí desde la carpeta con el nombre antiguo) |

## Confidencialidad del primer cliente (regla de Javier, 2026-10-01)

El cliente objetivo **no se nombra en ningún fichero del repo ni del sitio** (el repo es público y la captación va
en paralelo). Nombre en clave: **Cliente A**; producto: **Engraver Pro™**; web: `the-brand.com`; carpeta del caso:
`poc/clip-grabado`; marca local `cliente-a` (en `work/`, no versionada). Cifras y títulos de vídeo del cliente van
difuminados o parafraseados. Todo lo que lo nombra (propuesta, brief y guion de la segunda muestra, paquete de
envío) vive **fuera de lo versionado**: en el PC, en `_private/cliente-a/` (`_private/` está en `.gitignore`). El
sitio publica el caso anónimo hasta tener permiso escrito (`site/build.py` `CONFIG["case_public"]` + `case_brand`).

El árbol se limpió con un script de anonimizado con comprobación final (cero coincidencias, incluidas frases
genéricas que coinciden con títulos del canal) y **el historial se reescribió con `git filter-repo`** (rutas,
contenidos y mensajes; cero coincidencias en todos los objetos; push forzado de `main` y `main-ky21ae`). Los hashes
cambiaron. **Cerrado en el PC el 2026-10-01:** clon resincronizado, tags `v0.2.0` y `v0.3.0` recreados sobre la
historia nueva (`a38672b` y `264777d`, mismo autor, fecha y mensaje) con push forzado, y notas de la release v0.3.0
corregidas (nombraban al cliente; el anonimizado no las miraba). Copia de la historia antigua en un bundle dentro de
`_private/`.

**Control permanente:** `scripts/release-check.py` tiene la fila bloqueante **confidencialidad**. Lee los términos
de `_private/confidencial.txt` (no versionado; uno por línea, texto o expresión regular) y los busca en los ficheros
versionados y en los que están sin ignorar, en los mensajes y diffs de todos los refs, en los tags y en los títulos,
notas de release y descripción del repo en GitHub. Informa del sitio, nunca del término. Sin ese fichero (un clon
nuevo, la nube) la fila avisa de que no se comprueba: hay que recrearlo antes de etiquetar. Lo que se baje de una
sesión en la nube y nombre al cliente va directo a `_private/`, nunca a una carpeta suelta dentro del repo.

## Qué se ha hecho, por sesiones

### 2026-09-24 a 2026-09-29 — research, plugin base, v0.1.0 y v0.2.0
Análisis del vídeo de referencia, repos, PoC HyperFrames vs Remotion, roadmap de 18 features (`research/01`–`04`);
plugin con 5 skills y CLI base; brand kit, gráficas, gestos, jump cuts, limpieza de audio, GSAP con plugins; repo
público, GitHub Pages con dominio, deck de guía, instaladores; releases v0.1.0 y v0.2.0.

### 2026-09-30 (PC) — instalación, subtítulos, caso Cliente A, vídeo que vende, release 0.3.0, roadmap, giro a producto
Instaladores y asistente web; lienzo vertical y cuadrado; subtítulos por palabras y SRT/VTT; B-roll (sin claves);
`fetch`, `brand from-site`, `graphics` (OCR), `reframe`; overlays de venta, fábrica de shorts, ganchos, `cover`,
`i18n`; relevamiento completo e higiene (versión única, cargador tolerante, `doctor`, `release-check`); tag y
release v0.3.0; roadmap visual; `research/06` (monetización) y `research/07` (producto frame28.app, plan de 7 días).

### 2026-09-30 (nube, noche) — suite de pruebas y `reframe-map`
82 pruebas sobre módulos puros; dos regresiones arregladas (`cut.remap_storyboard` comparaba cortes con tiempos
ya remapeados; `i18n extract` no marcaba frases sin palabra oída); `frame28 reframe-map`.

### 2026-10-01 (nube) — plan de siete días, confidencialidad y preparación de la 0.4.0
1. **Precios validados** por Javier; fusión en `main`.
2. **Día 1**: textos de la landing ES/EN (`site/content/landing.*.md`) y **contrato base** ES/EN
   (`site/content/condiciones.es.md`, `terms.en.md`: 18 cláusulas, hoja de pedido, checklist de derechos, encargo
   del tratamiento). La landing dice con exactitud que la dirección usa modelos de lenguaje con transcripción y
   fotogramas de revisión.
3. **Día 2**: sitio completo en `site/` (`build.py` con plantilla común y CONFIG, Pages Function del formulario,
   `_redirects`, `_headers`, `wrangler.toml`, README de despliegue y de Access, `og.png`).
4. **Día 3**: propuesta al cliente (email, one-pager, seguimiento) entregada fuera del repo.
5. **Confidencialidad**: anonimizado del árbol y reescritura del historial (ver sección).
6. **Día 4**: base de conocimiento (8 artículos ES/EN) y curso online (6 lecciones ES/EN; la 1 con guion completo de
   8 min) en `site/`, incluidos en todas las capas de pago (landing, condiciones y `research/07` al día); generador
   con índices, navegación, bloque de vídeo y noindex.
7. **Día 5**: `log.py` + `frame28 report` (+ `report note`), `frame28 clips batch`, ganchos `statement` para tramos
   sin momentos, fila de claves de B-roll en `doctor`; 90 pruebas.
8. **Día 6**: brief diferencial, guion de montaje con disparadores y plantilla de storyboard de la segunda muestra
   (privados); método capitalizado en `references/marca-y-promocional.md` §4.
9. **Día 7**: paquete de envío (privado) y textos públicos de lanzamiento y apertura de Fundadores
   (`site/content/lanzamiento.md`).
10. **Release 0.4.0 preparada**: versión en los cuatro sitios, roadmap cerrado (sus seis pendientes pasan a la 0.5.0),
    README, notas de release entregadas a Javier (`RELEASE-NOTES-v0.4.0.md`, fuera del repo), artefacto del roadmap
    republicado, `release-check` en verde.
11. **Bloque del PC en un script** (`avanza-pc.ps1`, entregado fuera del repo junto al bundle y las notas): el `.sh`
    no sirve en Windows PowerShell 5.1 (no hay `&&` ni WSL). **Marcadores de resultado** (`frame28 clips markers`,
    R5 #8): en cada frase de resultado propone `before_after` con dos instantes del clip, `draw` check y `kinetic`
    con la frase real; en cada promesa, `kinetic`. 94 pruebas. Entra en la 0.4.0 si el tag se crea después de este
    commit (el script etiqueta `origin/main`); las notas entregadas ya lo incluyen.

### 2026-10-01 (PC, tarde) — tags, release 0.4.0 y control de confidencialidad
1. **Retomar en el PC**: de la nube solo llegaron los cinco ficheros privados de los días 6 y 7; el script
   `avanza-pc.ps1`, el bundle de tags y las notas no. Se hizo a mano: los commits equivalentes de los tags se
   localizaron por fecha de autor, asunto y número de commits.
2. **Tags `v0.2.0` y `v0.3.0`** recreados sobre la historia nueva y subidos con push forzado; clon limpio verificado.
   Notas de la **release v0.3.0** corregidas: nombraban al cliente.
3. **Líneas de firma de las condiciones**: los guiones bajos se interpretaban como énfasis y el HTML cambiaba según
   la versión de `markdown` (el build del PC ensuciaba el árbol). Escapados en la fuente.
4. **Release v0.4.0** publicada (tag en `4e7a6cb`): CLI reinstalado, `release-check` en verde, plugin 0.4.0,
   instalación limpia con `uvx`, regresión de render de `clip-javier`.
5. **Fila de confidencialidad en `release-check`** (ver §Confidencialidad) con sus pruebas (98 en total).
6. **Carpetas locales**: `work/`, `out/` e `input.mp4` del caso a `poc/clip-grabado/`; material privado a
   `_private/cliente-a/`; marca local `cliente-a.json` junto a la original.

## Lo que toca ahora (en este orden)

1. **Día 6 en el PC**: `frame28 fetch` del segundo tutorial del Cliente A, transcribir, poner tiempos en la plantilla
   (`_private/cliente-a/storyboard-acrilico.template.json`) siguiendo los `cue`, largo, `clips batch`, ES y DE,
   portadas, `frame28 report note` con los tokens. Muestras a una carpeta privada.
2. **Desplegar frame28.app.** Cloudflare Pages conectado al repo, rama `main`, root `site`, sin build; dominio;
   remitente `hola@frame28.app` y binding `SEND_EMAIL`; probar el formulario; **Cloudflare Access** sobre `/kb`,
   `/curso`, `/en/kb`, `/en/course` con PIN por email (pasos en `site/README.md`). Sin Access, el área de clientes es
   pública.
3. **Condiciones**: rellenar los `[[…]]` (datos fiscales, fuero, buzón, IVA, idioma que prevalece, música, arrastre en
   Studio, medio de pago) y pasarlas por el asesor; regenerar con `uv run --with markdown python site/build.py`.
4. **Grabar la lección 1** del curso con su guion (`site/content/curso/es/01-que-es-frame28.md`), montarla con Frame28 y
   poner la URL en `video:`.
5. **Día 7**: lista previa de once puntos del paquete de envío (`_private/cliente-a/dia7-envio-final.md`), y enviar.
   Publicar `lanzamiento.md` (tarjeta en t28.io, LinkedIn ES/EN, email a contactos) el mismo día que el sitio esté en
   vivo con Access.
6. Claves de Pexels y Pixabay en `~/.config/frame28/keys.json` y una búsqueda real; `clips batch` con render sobre
   `poc/clip-demo`.

## Qué quedó a medias o sin hacer

1. **Sitio frame28.app**: construido y verificado, no desplegado; `og.png` hecha; caso de cliente anónimo hasta permiso.
2. **Área de clientes**: artículos y guiones hechos; faltan los vídeos del curso y activar Access.
3. **Condiciones**: 48 huecos `[[…]]` (los resalta `build.py`) y revisión legal pendientes.
4. **Tarjeta de Frame28 en t28.io**: texto en `site/content/lanzamiento.md`; la web de Think28 no está en este repo.
5. **Sin probar en real**: `broll search/fetch` (sin claves), `clips batch` con render, `reframe-map` con un
   `gestures.json` real, `reframe --mode crop` con hablante en movimiento, `clips markers` sobre un vídeo real
   (sus `before_t` hay que mirarlos con `frame28 frames`: el "antes" debe enseñar el objeto sin tocar). El director anota los tokens con
   `frame28 report note --tokens`; el CLI no puede verlos.
6. **Deuda menor**: GSAP por CDN sin copia local (el render necesita red); HyperFrames 0.8.72 pineado con 0.8.98
   publicada; OpenCV instalado por triplicado; `poc/remotion/package-lock.json` versionado aunque Remotion está
   descartado; cuadrado 1:1 sin caso documentado; `chart bar` en vertical con más de tres filas; `install.sh` sin Mac
   real. Todo en el roadmap, bajo la 0.5.0.

## Bloqueos y dudas

| Bloqueo o duda | Dueño | Qué lo desbloquea |
|---|---|---|
| Commits antiguos cacheados en GitHub tras la reescritura (ya sin ningún ref que los alcance, pero accesibles por hash hasta su recolección) | Javier | Pedir a soporte de GitHub la purga del repo, si se quiere cerrar del todo |
| Acceso a Cloudflare (Pages, Access, Email Service) | Javier | Desplegar él (paso 2) o dar a la sesión un token de API con permisos de Pages, DNS y Email |
| API de envío de Cloudflare Email Service | Javier al desplegar | `functions/api/contact.js::sendMail` usa el binding `send_email` estable; si la beta cambia la forma, es el único sitio que tocar (docs de Cloudflare bloqueadas desde la nube) |
| Permiso del Cliente A para publicar el caso | Javier con el cliente | Hasta entonces, versión anónima |
| Claves de Pexels y Pixabay | Javier | pexels.com/api y pixabay.com/api/docs |
| Términos de la suscripción de Claude para uso profesional | Javier | Revisar los vigentes o pasar la dirección a la API; la cláusula 7 de las condiciones lo asume |
| Horas para operar el piloto | Javier | Fija si Launch se entrega en cinco días laborables |
| Decisiones de `research/06` §8 aún abiertas | Javier | Quién opera, umbrales para Cloud y qué sigue abierto (propuesto: todo) |

## Para retomar sin sorpresas

```bash
git fetch origin && git status -sb                # main...origin/main; si el clon es anterior al 2026-10-01: reset --hard origin/main (historial reescrito)
frame28 doctor                                   # fila frame28: 0.4.0 en código y 0.4.0 instalada tras --reinstall; "Todo listo." (gpu, RVM, B-roll y red son opcionales)
claude plugin validate ./plugin                  # Validation passed
python scripts/release-check.py --notes          # con la 0.4.0 publicada: tag y release "ya existe" hasta subir __version__; fila confidencialidad "sin rastro" (necesita _private/confidencial.txt)
(cd plugin/cli && uv run --group dev pytest)     # 98 passed en ~3 s
uv run --with markdown python site/build.py      # 40 páginas · plazas Fundadores: 5 · caso público: False · huecos en condiciones: 48
cd poc/clip-javier && frame28 build storyboard-gsap.json -o work/f28-gsap && frame28 check work/f28-gsap && frame28 render work/f28-gsap -o out/test.mp4   # 13 overlays, ~2 min (PC)
curl -sI https://frame28.t28.io/roadmap/ | head -1     # HTTP/2 200
```

Si ffmpeg o uv no están en el PATH de la shell, el CLI los encuentra solo; para la shell, la línea `export PATH`
de las Trampas de `CLAUDE.md`. Si `frame28 --version` no dice 0.4.0: `uv tool install --editable ./plugin/cli
--python 3.12 --reinstall`. Si las skills `frame28:*` no aparecen en una sesión nueva: `claude plugin uninstall
frame28@think28 && claude plugin install frame28@think28 --scope user`. En la nube no hay HyperFrames ni red al
CDN: sirve para código, pruebas, sitio y docs; los renders y las muestras se hacen en el PC.
