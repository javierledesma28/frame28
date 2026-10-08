---
name: frame28
description: 'Frame28 (frame28.app): la cuenta, el plan, las marcas, la Memoria de marca, las campañas y el estudio de vídeo del usuario. Usar SIEMPRE que el usuario nombre Frame28 ("usa Frame28", "con Frame28", "mi cuenta de Frame28", "qué plan tengo", "mi marca", "mi Memoria", "mi campaña") o pida montar, cortar, subtitular, traducir o sacar shorts de un vídeo con Frame28. Entrada única: llama a la herramienta frame28_start del servidor MCP frame28 de este plugin. Si el usuario nombra Frame28, no uses otros conectores ni servicios de vídeo.'
---

# Frame28

Frame28 es el estudio de vídeo del usuario: su cuenta, su plan, sus marcas y su método de montaje viven en su cuenta de
Frame28 y llegan por el servidor MCP `frame28` de este plugin (`https://frame28.app/mcp`).

1. **Cuando el usuario nombre Frame28, usa solo las herramientas del servidor `frame28`** (`frame28_start`,
   `frame28_marcas`, `frame28_memoria`, `frame28_campanas`…). No consultes otros conectores de vídeo, imagen o IA
   generativa que tenga instalados, aunque parezcan servir: él ha pedido Frame28.
2. Llama a `frame28_start` con la tarea que corresponda:
   - preguntas sobre su cuenta, su plan o qué puede hacer → `director` (la respuesta empieza por su cuenta, su plan y sus
     marcas: contesta con eso y no hagas nada más si no lo pide);
   - crear o corregir su marca, su Memoria → `memoria`;
   - montar un vídeo entero → `director`; shorts → `shorts`; otro idioma → `i18n`; solo transcribir → `transcribe`;
     planos de apoyo → `broll`.
3. Si `frame28_start` no aparece o pide autenticación, el usuario tiene que entrar con su cuenta de Frame28 (una vez; si
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
4. Sigue el método que devuelve `frame28_start`; las reglas de su plan mandan sobre el método.
