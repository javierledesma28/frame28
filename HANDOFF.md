# Traspaso — estado del proyecto a 2026-10-01 (cierre de la sesión en la nube)

Para retomar Frame28 desde otra cuenta de Claude Code **sin historial de conversación**, sobre este mismo
repositorio. Lee primero [CLAUDE.md](CLAUDE.md) (qué es, estructura, cómo se ejecuta, convenciones, trampas). Este
fichero es el estado verificado, lo hecho por sesiones, lo que quedó a medias, los bloqueos y lo que toca ahora.
`main` = `origin/main` = `main-ky21ae` (`01aa895`); árbol limpio.

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

## Estado: qué funciona hoy (verificado el 2026-10-01 en la nube; lo marcado "PC" se verificó el 2026-09-30 en Windows)

| Qué | Evidencia |
|---|---|
| Versión publicada | **v0.3.0** (release https://github.com/javierledesma28/frame28/releases/tag/v0.3.0). **v0.4.0 preparada, pendiente de etiquetar** (ver §Lo que toca ahora, paso 2) |
| Versión en ficheros | 0.4.0 en `plugin/cli/frame28/__init__.py` (fuente; pyproject la lee con hatch), `plugin/.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` y README; `python scripts/release-check.py` → "Listo para etiquetar v0.4.0" (todas las filas en verde) |
| CLI | 41 órdenes en 21 módulos; en la nube `frame28 --version` 0.4.0 y `frame28 doctor` "Todo listo" (sin GPU, sin modelo RVM, sin red al CDN: filas opcionales). **PC**: instalado editable 0.3.0, hace falta `--reinstall` |
| Instalación limpia desde el tag | **PC**: `uvx --from "git+https://github.com/javierledesma28/frame28@v0.3.0#subdirectory=plugin/cli" frame28 --version` → 0.3.0 en 21 s; repetir con v0.4.0 tras etiquetar |
| Plugin | `claude plugin validate ./plugin` pasa (nube). **PC**: instalado 0.3.0 desde el marketplace local; reinstalar tras el pull |
| Storyboards | 11 de 11 versionados válidos; además `poc/clip-grabado/storyboard-short-s4.json` construye con marca think28 (suite) |
| Regresión | **PC**: `poc/clip-javier/storyboard-gsap.json`: build 1 s, check 88 s, render 111 s; portada correcta |
| Pruebas automatizadas | **90 en verde en ~1 s** (`cd plugin/cli && uv run --group dev pytest`): captions, cut (WAV sintético), clips (ganchos, `batch --no-render`), i18n, build (validate, platform_warnings, build_project), reframe (camera_path, map_*), log/report, smoke del CLI. `release-check` las ejecuta como fila bloqueante |
| Web del plugin | https://frame28.t28.io/ `/presentacion/` `/instalar/` `/roadmap/` (GitHub Pages sobre `docs/`) |
| Roadmap | `docs/roadmap/index.html`: 6 versiones, 56 ítems (29 hechos, 4 a medias, 23 pendientes); 0.4.0 cerrada y marcada "estás aquí"; artefacto privado https://claude.ai/artifact/CxhtKMffGhQRsKUhAqwUS8 (versión 3, republicado el 2026-10-01) |
| Sitio del producto | `site/`: 40 páginas estáticas ES/EN (landing, Fundadores, contacto, condiciones, 8 artículos de base de conocimiento, 6 lecciones del curso), formulario con Pages Function, `og.png`, redirecciones y cabeceras; verificado en Chromium a 1280 y 390 px. **No desplegado** |
| Git | 71 commits tras la reescritura del historial; `main` = `origin/main` = `main-ky21ae`. **PC**: el clon tiene la historia antigua y debe resincronizarse; cuenta activa de `gh` allí: `javierledesma28` |
| Casos reales | `poc/clip-javier`, `clip-auriculares`, `clip-whatsapp`, `clip-demo`, `clip-grabado` (largo, 3 shorts, portada, versión ES en `poc/clip-grabado/out` del PC, no versionados) |

## Confidencialidad del primer cliente (regla de Javier, 2026-10-01)

El cliente objetivo **no se nombra en ningún fichero del repo ni del sitio** (el repo es público y la captación va
en paralelo). Nombre en clave: **Cliente A**; producto: **Engraver Pro™**; web: `the-brand.com`; carpeta del caso:
`poc/clip-grabado`; marca local `cliente-a` (en `work/`, no versionada). Cifras y títulos de vídeo del cliente van
difuminados o parafraseados. Todo lo que lo nombra (propuesta, brief y guion de la segunda muestra, paquete de
envío) vive **fuera del repo**, en los ficheros de Javier. El sitio publica el caso anónimo hasta tener permiso
escrito (`site/build.py` `CONFIG["case_public"]` + `case_brand`).

El árbol se limpió con un script de anonimizado con comprobación final (cero coincidencias, incluidas frases
genéricas que coinciden con títulos del canal) y **el historial se reescribió con `git filter-repo`** (rutas,
contenidos y mensajes; cero coincidencias en todos los objetos; push forzado de `main` y `main-ky21ae`). Los hashes
cambiaron. **Pendiente en el PC:** resincronizar el clon y mover los tags `v0.2.0` y `v0.3.0` remotos, que siguen
apuntando a la historia antigua (ver §Lo que toca ahora, paso 1). Copia previa del repo en un bundle, fuera del repo.

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

## Lo que toca ahora (Javier, en su PC, en este orden)

1. **Pasos 1 y 2 en una sola orden (Windows PowerShell):**
   `powershell -ExecutionPolicy Bypass -File avanza-pc.ps1 -Bundle "C:\ruta\tags-reescritos.bundle" -Notes "C:\ruta\RELEASE-NOTES-v0.4.0.md"`
   (los tres ficheros los entregó Claude fuera del repo). Hace `fetch` + `reset --hard origin/main`, importa los tags
   reescritos del bundle y comprueba sus hashes, `gh auth switch --user javierledesma28`, `git push --force origin
   refs/tags/v0.2.0 refs/tags/v0.3.0`, verifica con un clon limpio (0 coincidencias del nombre del cliente), reinstala
   el CLI, pasa `release-check`, crea y sube el tag `v0.4.0`, publica la release con las notas, reinstala el plugin,
   prueba la instalación limpia desde el tag con `uvx` y vuelve a la cuenta corporativa. Se detiene en el primer error.
   Hasta entonces la historia antigua con el nombre del cliente sigue alcanzable desde los tags viejos.
2. **A mano, si el script falla a mitad**: `uv tool install --editable ./plugin/cli --python 3.12 --reinstall`,
   `python scripts/release-check.py`, `git tag -a v0.4.0 -m "Frame28 v0.4.0"`, `git push origin v0.4.0`,
   `gh release create v0.4.0 --title "Frame28 v0.4.0" --notes-file RELEASE-NOTES-v0.4.0.md`, volver a la cuenta
   corporativa, reinstalar el plugin (`claude plugin uninstall frame28@think28`; `claude plugin install
   frame28@think28 --scope user`) y comprobar la instalación limpia desde el tag con `uvx`. En PowerShell 5.1 no existe
   `&&`: una orden por línea. El roadmap publicado ya dice que la 0.4.0 está publicada el 1 de octubre.
3. **Desplegar frame28.app.** Cloudflare Pages conectado al repo, rama `main`, root `site`, sin build; dominio;
   remitente `hola@frame28.app` y binding `SEND_EMAIL`; probar el formulario; **Cloudflare Access** sobre `/kb`,
   `/curso`, `/en/kb`, `/en/course` con PIN por email (pasos en `site/README.md`). Sin Access, el área de clientes es
   pública.
4. **Condiciones**: rellenar los `[[…]]` (datos fiscales, fuero, buzón, IVA, idioma que prevalece, música, arrastre en
   Studio, medio de pago) y pasarlas por el asesor; regenerar con `uv run --with markdown python site/build.py`.
5. **Día 6 en el PC**: `frame28 fetch` del segundo tutorial del Cliente A, transcribir, poner tiempos en la plantilla
   siguiendo los `cue`, largo, `clips batch`, ES y DE, portadas, `frame28 report note` con los tokens. Muestras a una
   carpeta privada.
6. **Grabar la lección 1** del curso con su guion (`site/content/curso/es/01-que-es-frame28.md`), montarla con Frame28 y
   poner la URL en `video:`.
7. **Día 7**: lista previa de once puntos del paquete de envío, y enviar. Publicar `lanzamiento.md` (tarjeta en t28.io,
   LinkedIn ES/EN, email a contactos) el mismo día que el sitio esté en vivo con Access.
8. Claves de Pexels y Pixabay en `~/.config/frame28/keys.json` y una búsqueda real; `clips batch` con render sobre
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
| Tags v0.2.0 y v0.3.0 en GitHub apuntan a la historia antigua (el proxy de la nube no permite tocar tags: 403 por git y por API; verificado dos veces) | Javier, PC | `avanza-pc.ps1` con el bundle (paso 1 de arriba) |
| Tag y release v0.4.0 | Javier, PC | el mismo script (paso 1) o el paso 2 a mano |
| Commits antiguos cacheados en GitHub tras la reescritura (accesibles por hash hasta su recolección) | Javier | Pedir a soporte de GitHub la purga del repo, si se quiere cerrar del todo |
| Acceso a Cloudflare (Pages, Access, Email Service) | Javier | Desplegar él (paso 3) o dar a una sesión nueva un token de API con permisos de Pages, DNS y Email y permitir `api.cloudflare.com` en la red del entorno |
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
python scripts/release-check.py --notes          # "Listo para etiquetar v0.4.0" hasta que exista el tag; después, tag y release "ya existe" hasta subir __version__
(cd plugin/cli && uv run --group dev pytest)     # 94 passed en ~1 s
uv run --with markdown python site/build.py      # 40 páginas · plazas Fundadores: 5 · caso público: False · huecos en condiciones: 48
cd poc/clip-javier && frame28 build storyboard-gsap.json -o work/f28-gsap && frame28 check work/f28-gsap && frame28 render work/f28-gsap -o out/test.mp4   # 13 overlays, ~2 min (PC)
curl -sI https://frame28.t28.io/roadmap/ | head -1     # HTTP/2 200
```

Si ffmpeg o uv no están en el PATH de la shell, el CLI los encuentra solo; para la shell, la línea `export PATH`
de las Trampas de `CLAUDE.md`. Si `frame28 --version` no dice 0.4.0: `uv tool install --editable ./plugin/cli
--python 3.12 --reinstall`. Si las skills `frame28:*` no aparecen en una sesión nueva: `claude plugin uninstall
frame28@think28 && claude plugin install frame28@think28 --scope user`. En la nube no hay HyperFrames ni red al
CDN: sirve para código, pruebas, sitio y docs; los renders y las muestras se hacen en el PC.
