# Instalar Frame28 · instrucciones para un agente (Claude Code)

Estás ayudando a una persona, probablemente no técnica, a instalar **Frame28** (A Think28 product) en su equipo.
Explica cada paso en una frase antes de hacerlo, pide permiso como haces siempre, y no des nada por instalado
sin comprobarlo. Idioma: el de la persona (por defecto español). Si algo falla, di qué pasó en lenguaje llano y
qué vas a intentar; nunca pidas contraseñas por el chat (las escribe la persona en su propia terminal).

## Qué es Frame28

Convierte un clip de la persona hablando a cámara en un video montado (rótulos, títulos sincronizados con la voz,
texto detrás del hablante, callouts donde señala, gráficas y subtítulos). Piezas: un **CLI** `frame28` (Python,
instalado con `uv`) y un **plugin de Claude Code** (skills) que lo dirige. Renderiza con HyperFrames (Node.js).

## Plan

1. **Detecta el sistema** (Windows, macOS o Linux) y comprueba internet.
2. **Programas de apoyo**, solo los que falten. Comprueba cada uno con `--version`:
   - **ffmpeg** (video), **Node.js 22+** (render), **uv** (instala Frame28 y trae su propio Python) y **Git** (uv lo
     necesita para instalar el motor desde GitHub; un equipo recién instalado no lo trae).
   - Windows: `winget install --id Gyan.FFmpeg -e --accept-source-agreements --accept-package-agreements`,
     `winget install --id OpenJS.NodeJS.LTS -e ...`, `winget install --id astral-sh.uv -e ...`, `winget install --id Git.Git -e ...`, y el runtime
     `winget install --id Microsoft.VCRedist.2015+.x64 -e ...` si falta. Tras instalar, refresca el PATH de la
     sesión o avisa de que hay que abrir una terminal nueva.
   - macOS: si no hay Homebrew, explícale que Homebrew le pedirá su contraseña y puede tardar 5–15 minutos
     descargando las Command Line Tools; lánzalo con
     `/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"` en una
     terminal **de la persona** (es interactivo). Luego `brew install ffmpeg node uv git` y carga `brew shellenv`.
   - Linux (Debian/Ubuntu): `sudo apt-get install -y ffmpeg git`, Node desde nodesource, uv desde `https://astral.sh/uv/install.sh`.
3. **Claude Code** en terminal, si `claude` no existe: `curl -fsSL https://claude.ai/install.sh | bash` (macOS/Linux)
   o `irm https://claude.ai/install.ps1 | iex` (Windows). La persona tendrá que iniciar sesión después con `claude`.
4. **Motor de Frame28**: `uv tool install --python 3.12 --force git+https://github.com/javierledesma28/frame28#subdirectory=plugin/cli`
   y después `uv tool update-shell`. Comprueba `frame28 --version`.
5. **Plugin**: `claude plugin marketplace add javierledesma28/frame28` y `claude plugin install frame28@think28 --scope user`.
   Si falla por no haber iniciado sesión, indícale que lo haga y repite.
6. **Comprobación**: `frame28 doctor`. Explica cada línea. Las aspas en «gpu» y «modelo RVM» son normales.
7. **Cuenta de Frame28** (sin esto el plugin no puede trabajar): tras reiniciar Claude Code, que escriba `/mcp`, elija
   **frame28** y pulse **Authenticate**. Se abre el navegador: email y el código que le llega, sin contraseña. Si no tiene
   cuenta, se crea ahí, gratis, y monta en modo demo (marca de Frame28); con un plan de pago, con su marca. Si el
   navegador no se abre (consola sin escritorio), `/mcp` enseña el enlace para abrirlo a mano. Tú no puedes hacer este
   paso por la persona: es su login.
8. **Cierre**: dile que abra una terminal nueva, que reinicie Claude Code para que cargue el plugin, que entre con su
   cuenta (paso 7) y que el primer uso es grabar un clip de 30 segundos y escribir en Claude Code «Aquí está mi clip. Móntamelo».
   Guía con imágenes: https://frame28.t28.io/presentacion/

## Alternativa de un solo paso

Si la persona prefiere no ir paso a paso, el instalador interactivo hace exactamente esto:
`irm https://frame28.t28.io/install.ps1 | iex` (Windows) o `curl -fsSL https://frame28.t28.io/install.sh | bash` (macOS).
Puedes lanzarlo tú desde su terminal con su permiso; en Mac, Homebrew seguirá pidiéndole la contraseña a la persona.

## Para actualizar

Si Frame28 ya está instalado y la persona quiere la versión nueva, no hace falta repetir la instalación:

1. **CLI**: `uv tool upgrade frame28` (lo reinstala desde GitHub en unos 15 segundos, aunque el número de versión no haya
   cambiado). Comprueba `frame28 --version` contra https://github.com/javierledesma28/frame28/releases/latest.
2. **Plugin**: `claude plugin marketplace update think28` y después `claude plugin update frame28@think28`. Solo actúa si el
   número de versión del plugin cambió; «already at the latest version» significa que no había nada nuevo. Hay que reiniciar
   Claude Code para que cargue las skills nuevas.
3. `frame28 doctor` para confirmar que todo sigue en su sitio.
