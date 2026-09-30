# Guía: crear, probar, publicar, consumir y securizar el plugin Frame28

Escrita para la primera vez que se construye un plugin de Claude Code. Cada etapa tiene qué se hace, con qué
comando, cómo se comprueba y qué puede salir mal. Vamos tachando.

## 0. Qué es un plugin (en una frase por pieza)

- **Skill**: carpeta con `SKILL.md` (instrucciones + referencias). Claude la carga cuando la tarea encaja con su
  `description`. Tú ya has hecho skills: un plugin es un **paquete de skills** (más, opcionalmente, comandos,
  agentes, hooks y servidores MCP) con un manifiesto y una forma estándar de instalarse.
- **Manifiesto** `.claude-plugin/plugin.json`: nombre, versión, autor. Con él las skills se instalan como
  `frame28:frame28-director`, etc.
- **Marketplace** `.claude-plugin/marketplace.json`: catálogo de plugins. Un repo puede ser su propio marketplace
  (es nuestro caso: `source: "./"`). Así otra persona hace `marketplace add` y `install` sin nada más.
- **CLI `frame28`**: no forma parte del plugin en sentido estricto (es un paquete Python); las skills lo llaman.
  Se instala aparte con `uv tool install`.

## 1. Crear ✅ (hecho el 2026-09-29)

```
.claude-plugin/marketplace.json     catálogo (este mismo repo, source: ./plugin)
plugin/.claude-plugin/plugin.json   manifiesto
plugin/skills/frame28-*/SKILL.md    siete skills
plugin/cli/                         paquete Python
```
Comprobación: `claude plugin validate .` → `Validation passed`.

## 2. Probar en local ✅ (hecho el 2026-09-29)

Lo que pasó al hacerlo, y que ahora está corregido:

- **El plugin se copia entero al caché** (`~/.claude/plugins/cache/<marketplace>/<plugin>/<versión>/`). Con el
  manifiesto en la raíz del repo se copió todo, incluidos `poc/` con `node_modules` y videos. Solución: el plugin
  vive en `plugin/` y el marketplace apunta a `./plugin`. Ahora el caché pesa 226 KB.
- **Las `description` del frontmatter con `:` rompen el YAML** y la skill carga "con metadatos vacíos" (no se
  dispara nunca). `claude plugin validate ./plugin` lo detecta. Solución: descripciones entre comillas simples.
- **El CLI no está en el PATH de una terminal nueva**: `uv tool install` deja `frame28` en `~/.local/bin`.
  Arreglo de una vez: `uv tool update-shell` (añade esa carpeta al PATH del usuario) y abrir terminal nueva.
- **Al editar skills en local hay que reinstalar**: `claude plugin marketplace update think28` y
  `claude plugin install frame28@think28`; el caché es una copia, no un enlace.

Comandos usados:

```bash
claude plugin marketplace add C:/Workspaces/personal/Skill-Director   # registra el repo local como marketplace "think28"
claude plugin install frame28@think28 --scope user                     # instala para tu usuario
```
Comprobación pendiente en una sesión nueva de Claude Code (los plugins se cargan al arrancar): `/frame28:frame28-director` debe aparecer, y pedir "móntame este clip"
debe disparar la skill. Para quitarlo: `claude plugin uninstall frame28@think28`. Para actualizar tras editar
skills en local: `claude plugin marketplace update think28` o reinstalar.

Qué puede fallar: que Claude Code no encuentre `frame28` en PATH (el CLI vive en `~/.local/bin`; `uv tool
update-shell` lo añade), o que una skill no se dispare (afinar su `description`: es lo que Claude lee para decidir).

## 3. Publicar ✅ (2026-09-29): push, etiqueta `v0.1.0` y release en GitHub

Hecho: repo privado `javierledesma28/frame28`, rama `main`, commit inicial (80 ficheros, 5,9 MB). Lo que hubo
que arreglar antes de subir:

- **Medios y salidas fuera del repo**: el primer `git add` sumaba 77 MB por una secuencia PNG de la PoC.
  Regla: todo lo que se regenera (renders, máscaras, `node_modules`, secuencias) va en `.gitignore`.
- **Finales de línea**: `.gitattributes` con `* text=auto eol=lf` y `core.autocrlf=false`. Importa de verdad:
  el `words.srt` que importa HyperFrames solo funciona con LF, y Windows lo convertiría a CRLF.
- **Repo privado**: instalar desde GitHub exige credenciales git en la máquina que instala (`gh auth login`
  basta). Para compartirlo con cualquiera, hacerlo público cuando esté listo.


1. Repo: `javierledesma28/frame28` en GitHub (público para que cualquiera lo instale; privado funciona con
   credenciales git del que instala).
2. Primer commit y push (el `.gitignore` ya excluye medios y salidas).
3. Etiquetar versiones: `git tag v0.1.0 && git push --tags`. La `version` de `plugin.json` y de `pyproject.toml`
   deben coincidir con la etiqueta; subirlas juntas en cada release.
4. Opcional: publicar el CLI en PyPI (`uv build && uv publish`) para que `uv tool install frame28` funcione sin
   git. Mientras tanto: `uv tool install git+https://github.com/javierledesma28/frame28#subdirectory=plugin/cli`.

## 4. Consumir ✅ probado (2026-09-29)

Probado como lo haría otra persona, sin tocar la instalación local: `uvx --from
"git+https://github.com/javierledesma28/frame28@v0.1.0#subdirectory=plugin/cli" frame28 --version` construye el
paquete desde la etiqueta e imprime la versión en 24 s. Mientras el repo sea privado hace falta tener credenciales
git en la máquina (`gh auth login` las deja configuradas). `uv tool update-shell` dejó `~/.local/bin` en el PATH
del usuario, así que `frame28` funciona en cualquier terminal nueva.


```bash
claude plugin marketplace add javierledesma28/frame28
claude plugin install frame28@think28
uv tool install git+https://github.com/javierledesma28/frame28#subdirectory=plugin/cli
frame28 doctor
```
Para alguien no técnico esto son demasiados pasos, así que existe el **instalador de una línea** (hecho el
2026-09-29), servido desde el dominio de Frame28 vía GitHub Pages:

```powershell
irm https://frame28.t28.io/install.ps1 | iex        # Windows
```
```bash
curl -fsSL https://frame28.t28.io/install.sh | sh    # macOS (Homebrew) y Linux (apt)
```
Instalan solo lo que falta (ffmpeg, Node.js, uv), el CLI desde GitHub con `uv tool install --force`, el plugin si
`claude` está en el PATH, y terminan con `frame28 doctor`. Son idempotentes. Fuente: `docs/install.ps1` y
`docs/install.sh`; cualquier cambio se publica solo al hacer push. Es el mismo patrón `irm | iex` / `curl | sh`
que usan uv, Homebrew o Scoop: el script se lee entero desde HTTPS en tu dominio, y quien desconfíe puede abrir
la URL en el navegador y leerlo antes de ejecutarlo.

## 5. Securizar · limpieza previa a hacerlo público ✅ (2026-09-29)

Antes de plantear el repo público revisamos qué había versionado y encontramos tres cosas que no debían salir:
imágenes con la cara del autor (pruebas del clip propio), fotogramas y transcripciones del video de referencia
(material de un tercero) y el análisis plano a plano que lo cita. Se movieron a `_private/` (ignorado por git),
se dejó un resumen público en `research/01-…md` y se **reescribió el historial** a un único commit limpio con
`git checkout --orphan` + `git push --force`. Regla desde ahora: caras, clips y material de terceros nunca entran
en el repo; `_private/` es su sitio.

Aviso: GitHub conserva un tiempo los objetos de los commits antiguos aunque ya no estén en ninguna rama, y se
pueden abrir por SHA si alguien lo conoce. Para eliminarlos del todo: borrar y recrear el repo antes de hacerlo
público, o pedir a soporte de GitHub que ejecute la recolección.


Qué puede hacer un plugin: sus skills ejecutan comandos con **los permisos del usuario que lo instala**. Por eso:

- **Nada de secretos en el repo** (ni claves de API, ni tokens de HeyGen). El CLI no necesita ninguno; si algún
  día lo necesita, se lee de variable de entorno y se documenta.
- **Versiones fijadas**: HyperFrames va pineado (`0.8.72`) y las dependencias Python con mínimos; así lo que se
  instala hoy es lo que probamos.
- **Sin hooks ni MCP en v0.1**: no hay código que se ejecute solo al arrancar la sesión. Cuando añadamos un MCP,
  irá declarado en `.mcp.json` y revisado.
- **Modelos y binarios de terceros**: RVM se descarga de su release oficial a `~/.cache/frame28/`; Chrome lo
  descarga HyperFrames. Documentado en README y en `frame28 doctor`.
- **Ámbito de instalación**: `--scope user` (para ti), `--scope project` (para un equipo, queda en
  `.claude/settings.json` del repo) o `--scope local` (solo tu máquina, no versionado).
- **Revisión antes de cada release**: `claude plugin validate .`, `frame28 doctor`, un render de prueba del clip
  de ejemplo y `git diff` de las skills (son instrucciones para un agente: lo que diga, se hará).

## 6. Brand kit ✅ (2026-09-29)

Hecho y probado con el clip propio (`poc/clip-javier/storyboard-think28.json`):

- `plugin/cli/frame28/brands/think28.json`: tokens del brand kit oficial (amarillo `#F5C500`, negro `#0A0A0A`,
  Inter, Space Mono, tiempos de animación, endorsement) + logos SVG incluidos (`brands/think28/`).
- El storyboard acepta `"brand": "think28"`, un nombre propio o una ruta a JSON. Orden de búsqueda: `./brands/`
  junto al proyecto → `~/.config/frame28/brands/` → marcas incluidas.
- El `lower_third` lleva el isotipo; las `card` con `bg: accent` usan el color de marca; el overlay nuevo
  `brand_card` (apertura o cierre) pone logo, título, tagline y endorsement, con la variante de logo correcta
  según el fondo (`on_dark`, `on_light`, `on_accent`).
- `frame28 brand init mimarca --accent "#0D4F87" --logo logo.svg` crea una marca nueva; `brand list` y
  `brand show` para consultarlas. Frame28 sale con Think28 por defecto y cada usuario pone la suya.
- Aprendido: los SVG del press kit llevan fondo propio (oscuro, blanco o amarillo), por eso las variantes se nombran
  por el fondo sobre el que van y no por su color.

Diseño original (para referencia):

- `brand.json` por usuario o proyecto: `accent`, `ink`, `paper`, fuentes, logo (SVG/PNG), nombre y tagline.
  El storyboard lo referencia con `"brand": "think28"` o ruta.
- El CLI trae `brands/think28.json` por defecto y un comando `frame28 brand init` que crea el tuyo.
- El `lower_third` incorpora el logo; las `card` usan `accent`; los subtítulos, la fuente de la marca.
- Nunca se mezcla con marcas de terceros por defecto: Frame28 sale con Think28 y cada usuario pone la suya.

## 7. Iterar

Cada mejora sigue el mismo ciclo: cambiar skill o CLI → `claude plugin validate .` → probar con
`poc/clip-javier` → subir versión → tag → push. Las personas que lo tengan instalado actualizan con
`claude plugin marketplace update think28` y `uv tool upgrade frame28`.
