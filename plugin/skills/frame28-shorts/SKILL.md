---
name: frame28-shorts
description: 'Convierte un vídeo largo (tutorial, demo, charla) en varios shorts verticales de 15–45 s que venden: elige los tramos con más momentos (resultado, promesa, objeción, cifras, producto), pone un gancho de 3 s, subtítulos por palabras y una llamada a la acción con precio, código o QR, y genera variantes de gancho para rotar. Usar cuando pidan "sácame shorts", "reels", "TikToks", "clips para redes", "trocea este vídeo" o una versión corta vertical de un vídeo largo.'
---

# Frame28 · Shorts que venden

El método de esta tarea no viaja en el plugin: lo sirve tu cuenta de Frame28 desde el servidor MCP `frame28`
(`https://frame28.app/mcp`), siempre al día y según tu plan.

1. Llama a la herramienta `frame28_start` del servidor `frame28` con `tarea: "shorts"`.
2. Si la herramienta no aparece o pide autenticación, para y dile al usuario que entre con su cuenta de Frame28: en
   Claude Code, `/mcp` → el servidor `frame28` de este plugin → *Authenticate*. Si no tiene cuenta, la crea gratis en ese
   mismo paso con su email y un código de un solo uso. Sin cuenta, Frame28 no monta. Si el navegador no se abre solo
   (SSH, consola remota), Claude Code enseña la URL de entrada en `/mcp`: que la abra a mano en su navegador.
3. Sigue al pie de la letra el método que devuelve. Las **reglas de su plan** prevalecen sobre el método. Los documentos
   que cite se piden con `frame28_metodo`; otras tareas, con `frame28_start` y su nombre.
4. Los pasos deterministas los hace el CLI `frame28` (código abierto, MIT). Si no está instalado, `frame28 doctor` dice qué
   falta y el instalador está en https://frame28.t28.io.
