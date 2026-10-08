---
name: frame28-cutout
description: 'Recorta al hablante del fondo (máscara alfa por fotograma con RobustVideoMatting) para poner texto o gráficas detrás de la persona, hacer PiP limpio o cambiar el fondo. Usar cuando el storyboard tenga overlays `behind` o el usuario pida "texto detrás de mí", "recortarme", "quitar el fondo", "efecto de que el título pasa por detrás".'
---

# Frame28 · Recorte del hablante

El método de esta tarea no viaja en el plugin: lo sirve tu cuenta de Frame28 desde el servidor MCP `frame28`
(`https://frame28.app/mcp`), siempre al día y según tu plan.

1. Llama a la herramienta `frame28_start` del servidor `frame28` con `tarea: "cutout"`.
2. Si la herramienta no aparece o pide autenticación, el usuario tiene que entrar con su cuenta de Frame28 (una vez; si
   no tiene cuenta, se crea gratis en ese paso con su email y un código de un solo uso; sin cuenta, Frame28 no monta):
   - ofrécele abrirle tú la página de entrada y, si acepta, ejecuta con hasta 5 minutos de espera
     `"$CLAUDE_CODE_EXECPATH" mcp login plugin:frame28:frame28` (en PowerShell, `& $env:CLAUDE_CODE_EXECPATH mcp login
     plugin:frame28:frame28`; si la variable no existe, `claude mcp login plugin:frame28:frame28`). Se abre su navegador y él escribe su
     email y el código;
   - o que lo haga él en una terminal: `claude mcp login plugin:frame28:frame28` (si no conoce `login`, antes `claude update`;
     o `claude` → `/mcp` → `frame28` → *Authenticate*). Sin escritorio (SSH), con `--no-browser`, y pega la dirección de
     vuelta que le pide;
   - después, **que abra una sesión nueva** (en la app de escritorio o en la terminal) y repita su petición: las
     herramientas de Frame28 solo aparecen en las sesiones que empiezan después de entrar.
   No lances `mcp login` para comprobar si ya entró: borra la sesión guardada en cuanto empieza. `claude mcp list` lo dice
   sin tocar nada («Connected» o «Needs authentication»).
3. Sigue al pie de la letra el método que devuelve. Las **reglas de su plan** prevalecen sobre el método. Los documentos
   que cite se piden con `frame28_metodo`; otras tareas, con `frame28_start` y su nombre.
4. Los pasos deterministas los hace el CLI `frame28` (código abierto, MIT). Si no está instalado, `frame28 doctor` dice qué
   falta y el instalador está en https://frame28.t28.io.
