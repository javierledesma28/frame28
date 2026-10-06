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
3. Si `frame28_start` no aparece o pide autenticación, para y explícale que tiene que entrar con su cuenta de Frame28:
   - en Claude Code en la terminal: escribe `/mcp`, elige el servidor `frame28` de este plugin y pulsa *Authenticate*;
   - en la app de escritorio de Claude: en la configuración del plugin Frame28, en sus conectores, pulsa *Authenticate*
     (si no lo encuentra, que abra una terminal, escriba `claude` y haga el paso anterior).
   Se abre el navegador: su email y un código de un solo uso; si no tiene cuenta, se crea gratis en ese paso.
4. Sigue el método que devuelve `frame28_start`; las reglas de su plan mandan sobre el método.
