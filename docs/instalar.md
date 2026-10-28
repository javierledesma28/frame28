# Instalar Frame28 · instrucciones para un agente (Claude Code)

Estás ayudando a una persona, probablemente no técnica, a instalar **Frame28** (A Think28 product) en su equipo.
Explica cada paso en una frase antes de hacerlo, pide permiso como haces siempre, y no des nada por instalado
sin comprobarlo. Idioma: el de la persona (por defecto español). Si algo falla, di qué pasó en lenguaje llano y
qué vas a intentar; nunca pidas contraseñas por el chat (las escribe la persona en su propia terminal).

## Qué es Frame28

Convierte un clip de la persona hablando a cámara en un video montado (rótulos, títulos sincronizados con la voz,
texto detrás del hablante, callouts donde señala, gráficas y subtítulos). Piezas: un **CLI** `frame28` (Python,
instalado con `uv`) y un **plugin de Claude Code** (skills) que lo dirige. Renderiza con HyperFrames (Node.js).

## Si estás en la app de escritorio

Mira antes de empezar si corres dentro de la app de escritorio de Claude (pestaña Code): la variable
`CLAUDE_CODE_ENTRYPOINT` vale `claude-desktop` y `CLAUDE_CODE_EXECPATH` apunta a su `claude.exe` (la ve tu herramienta
Bash; en PowerShell puede no estar). Ahí la persona no tiene terminal propia, así que:

- **No instales Claude Code de terminal** (paso 3) si `claude` no está en el PATH: usa el de la app. En Bash,
  `"$CLAUDE_CODE_EXECPATH"`; en PowerShell, el más reciente de
  `%APPDATA%\Claude\claude-code\<versión>\<hash>\claude.exe` (ordena por versión, no por fecha). Donde este documento
  diga `claude …`, usa esa ruta.
- **Las variables no pasan de una orden a la siguiente** y la app no ve el PATH nuevo hasta que se reinicia. En cada
  orden que vaya después de un `winget`, recarga el PATH del registro delante:
  `$env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [Environment]::GetEnvironmentVariable('Path','User')`
  (Bash: `export PATH="$PATH:/c/Program Files/nodejs:$HOME/.local/bin"` o la carpeta que corresponda).
- Llama al motor por su ruta, `%USERPROFILE%\.local\bin\frame28.exe`, hasta que la app se reinicie.
- Si lanzas tú el instalador de un solo paso, ponle `FRAME28_YES=1` (no puede preguntar) y avisa antes de lo que va a
  instalar.
- **Cierre**: la persona tiene que cerrar la app del todo (también el icono junto al reloj) o reiniciar el equipo, y la
  cuenta de Frame28 (paso 7) se hace después, en una sesión nueva de la pestaña Code.

## Plan

1. **Detecta el sistema** (Windows, macOS o Linux) y comprueba internet.
2. **Programas de apoyo**, solo los que falten. Comprueba cada uno con `--version`:
   - **ffmpeg** (video), **Node.js 22+** (render), **uv** (instala Frame28 y trae su propio Python) y **Git** (uv lo
     necesita para instalar el motor desde GitHub; un equipo recién instalado no lo trae).
   - Windows: `winget install --id Gyan.FFmpeg -e --accept-source-agreements --accept-package-agreements`,
     `winget install --id OpenJS.NodeJS.LTS -e ...`, `winget install --id astral-sh.uv -e ...`, `winget install --id Git.Git -e ...`, y el runtime
     `winget install --id Microsoft.VCRedist.2015+.x64 -e ...` si falta. Después de cada `winget`, recarga el PATH del
     registro en la misma orden que use el programa nuevo (ver «Si estás en la app de escritorio»); en una terminal de la
     persona, abrir una nueva también sirve.
   - macOS: si no hay Homebrew, explícale que Homebrew le pedirá su contraseña y puede tardar 5–15 minutos
     descargando las Command Line Tools; lánzalo con
     `/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"` en una
     terminal **de la persona** (es interactivo). Luego `brew install ffmpeg node uv git` y carga `brew shellenv`.
   - Linux (Debian/Ubuntu): `sudo apt-get install -y ffmpeg git`, Node desde nodesource, uv desde `https://astral.sh/uv/install.sh`.
3. **Claude Code** en terminal, si `claude` no existe y no estás en la app de escritorio (allí usa su `claude.exe`): `curl -fsSL https://claude.ai/install.sh | bash` (macOS/Linux)
   o `irm https://claude.ai/install.ps1 | iex` (Windows). La persona tendrá que iniciar sesión después con `claude`.
4. **Motor de Frame28**: `uv tool install --python 3.12 --force "frame28[probado] @ git+https://github.com/javierledesma28/frame28@release#subdirectory=plugin/cli"`
   (`[probado]` trae las versiones exactas de las librerías con las que pasaron las pruebas; no lo quites) y después
   `uv tool update-shell`. Comprueba `frame28 --version`.
   **Con una tarjeta NVIDIA** (Windows o Linux: `nvidia-smi -L` responde), ofrece la aceleración por GPU, que transcribe
   unas 4 veces más rápido. **Pregúntaselo en el chat antes** y espera su respuesta: son unos **3,3 GB** más y sin ella
   todo funciona igual, por CPU. Sin un sí suyo, no la instales. Si lanzas el instalador de un solo paso, `FRAME28_YES=1`
   no la instala; solo con el sí de la persona añade `FRAME28_GPU=1`. Si acepta, instala en su lugar
   `uv tool install "frame28[gpu,probado] @ git+https://github.com/javierledesma28/frame28@release#subdirectory=plugin/cli" --python 3.12 --excludes https://raw.githubusercontent.com/javierledesma28/frame28/release/plugin/cli/excluir-gpu.txt --reinstall`
   (la misma que propone `frame28 doctor` en su fila «gpu»; el `--excludes` no se quita: evita que queden dos onnxruntime que se pisan) y lánzalo en segundo plano: tarda varios
   minutos.
5. **Plugin**: `claude plugin marketplace add javierledesma28/frame28` y `claude plugin install frame28@think28 --scope user`.
   Si falla por no haber iniciado sesión, indícale que lo haga y repite.
6. **Comprobación**: `frame28 doctor`. Explica cada línea. El aspa en «modelo RVM» es normal (se descarga la
   primera vez que hace falta); la de «gpu» también si el equipo no tiene NVIDIA o la persona no quiso la aceleración.
7. **Cuenta de Frame28** (sin esto el plugin no puede trabajar): `claude mcp login plugin:frame28:frame28` en una terminal
   nueva (Claude Code 2.1.186 o posterior: si no conoce `login`, `claude update` y repite; alternativa, `claude` → `/mcp` →
   **frame28** → **Authenticate**). Puedes lanzarlo tú si la persona está delante: se abre su navegador y ella escribe su
   email y el código que le llega, sin contraseña. Si no tiene cuenta, se crea ahí, gratis, y monta en modo demo (marca de
   Frame28); con un plan de pago, con su marca. Sin escritorio (SSH), que lo ejecute ella con `--no-browser` y pegue la
   dirección de vuelta. No lo lances para comprobar si ya entró: `mcp login` borra la sesión guardada en cuanto empieza;
   `claude mcp list` (o la fila «cuenta de Frame28» de `frame28 doctor`) lo dice sin tocar nada. Tú no escribes su email
   ni su código: es su login.
   En la app de escritorio no hay terminal: tras reiniciarla, la persona abre una sesión nueva de la pestaña Code y te
   pide «Entra en mi cuenta de Frame28»; lánzalo entonces con el `claude.exe` de la app, **en segundo plano** o con el
   tiempo de espera máximo (la persona tarda en escribir su email y el código, y tu herramienta corta a los 2 minutos) y
   sin `--no-browser` (sin terminal falla con «stdin isn't a terminal»). Si aun así falla, pídele que abra PowerShell
   desde el menú Inicio solo para ese paso y escriba allí la orden con la ruta del `claude.exe` de la app.
8. **Cierre**: dile que abra una **sesión nueva** de Claude Code, en la terminal o en la app de escritorio (Frame28 aparece
   en las sesiones que empiezan después de entrar; en la app, después de cerrarla del todo o reiniciar), y que el primer uso es grabar un clip de 30 segundos y escribir
   «Aquí está mi clip. Móntamelo».
   Guía con imágenes: https://frame28.t28.io/presentacion/

## Alternativa de un solo paso

Si la persona prefiere no ir paso a paso, el instalador interactivo hace exactamente esto:
`irm https://frame28.t28.io/install.ps1 | iex` (Windows) o `curl -fsSL https://frame28.t28.io/install.sh | bash` (macOS).
Puedes lanzarlo tú desde su terminal con su permiso; en Mac, Homebrew seguirá pidiéndole la contraseña a la persona.

## Para actualizar

Si Frame28 ya está instalado y la persona quiere la versión nueva, no hace falta repetir la instalación:

1. **CLI**: `uv tool upgrade frame28` (lo reinstala desde GitHub en unos 15 segundos, aunque el número de versión no haya
   cambiado). Comprueba `frame28 --version` contra https://github.com/javierledesma28/frame28/releases/latest. Si
   `frame28 doctor` marca la fila «librerías (versiones probadas)», la instalación es anterior a esas versiones y `upgrade`
   no se las da: repite una vez la orden del paso 4.
2. **Plugin**: `claude plugin marketplace update think28` y después `claude plugin update frame28@think28`. Solo actúa si el
   número de versión del plugin cambió; «already at the latest version» significa que no había nada nuevo. Hay que reiniciar
   Claude Code para que cargue las skills nuevas.
3. `frame28 doctor` para confirmar que todo sigue en su sitio.
