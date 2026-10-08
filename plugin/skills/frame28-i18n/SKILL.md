---
name: frame28-i18n
description: 'Saca la versión de un montaje de Frame28 en otro idioma con los mismos tiempos: extrae los textos del storyboard (rótulos, cinéticos, cajas, gancho, CTA, subtítulos), los traduce con criterio de subtitulado (corto, natural, nombres y cifras intactos), los vuelve a aplicar y regenera los subtítulos por palabras sobre el ritmo original. Usar cuando pidan "la versión en inglés", "tradúcelo", "subtítulos en francés", "el mismo vídeo para el mercado alemán" o una segunda lengua de un vídeo ya montado.'
---

# Frame28 · Versión en otro idioma

El método de esta tarea no viaja en el plugin: lo sirve tu cuenta de Frame28 desde el servidor MCP `frame28`
(`https://frame28.app/mcp`), siempre al día y según tu plan.

1. Llama a la herramienta `frame28_start` del servidor `frame28` con `tarea: "i18n"`.
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
