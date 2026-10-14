---
name: frame28-memoria
description: 'Crea o corrige la Memoria de marca de Frame28, lo que Frame28 recuerda de una marca para que sus vídeos sean suyos: colores, logo y fuente, voz, historia, catálogo con precios y códigos, ganchos que funcionan, glosario, claims prohibidos y llamada a la acción, redactada desde la web de la marca y sus vídeos. También consulta las campañas de la marca y su brief. Usar cuando pidan "crea la Memoria de mi marca", "prepara mi marca para los vídeos con mi web", "cambia el precio o el código de descuento del catálogo", "apunta que este gancho funcionó", "qué campañas tengo" o "qué pide la campaña X", aunque no nombren Frame28. No usar para montar un vídeo, tampoco el de una campaña ni para sacar colores o logo de una web para el vídeo en curso (frame28-director), ni para shorts (frame28-shorts), ni para manuales de identidad, guías de estilo en PDF o kits de marca de Canva u otras herramientas.'
---

# Frame28 · Memoria de marca y campañas

El método de esta tarea no viaja en el plugin: lo sirve tu cuenta de Frame28 desde el servidor MCP `frame28`
(`https://frame28.app/mcp`), siempre al día y según tu plan.

1. Según lo que pida el usuario:
   - **crear o corregir la Memoria** (marca visual, voz, historia, catálogo, ganchos, glosario, reglas legales, llamada a
     la acción, o lo que funcionó en una campaña) → llama a la herramienta `frame28_start` del servidor `frame28` con
     `tarea: "memoria"`. La Memoria se guarda entera en cada cambio: el método dice cómo;
   - **consultar campañas** → `frame28_campanas` con la marca las lista; `frame28_campana` con la marca y la campaña da su
     brief. Si no sabe el nombre corto de su marca, `frame28_marcas`;
   - **crear o editar una campaña** → se escribe en su estudio, https://frame28.app/app/ (estudio → campañas), no desde
     aquí. Díselo y, si lo que quiere es montarla ya, sigue con la tarea `director`;
   - **montar los vídeos de una campaña** → `frame28_start` con `tarea: "director"`: el método lee la Memoria y el brief.
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
