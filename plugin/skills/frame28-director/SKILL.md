---
name: frame28-director
description: 'Convierte un clip de una persona hablando a cámara en un video de presentación con rótulos, títulos cinéticos, texto detrás del hablante, callouts donde señala, pizarras y subtítulos sincronizados con la voz. Usar cuando el usuario entregue un video (o audio + video) y quiera "el video montado", "un explainer", "un launch video", "estilo founder video", o pida overlays/gráficas/subtítulos sincronizados. Orquesta las demás skills frame28-*.'
---

# Frame28 · Director

El método de esta tarea no viaja en el plugin: lo sirve tu cuenta de Frame28 desde el servidor MCP `frame28`
(`https://frame28.app/mcp`), siempre al día y según tu plan.

1. Llama a la herramienta `frame28_start` del servidor `frame28` con `tarea: "director"`. Es la tarea que orquesta el montaje
   completo: desde ella el método te irá pidiendo las demás.
2. Si la herramienta no aparece o pide autenticación, para y dile al usuario que entre con su cuenta de Frame28: en
   Claude Code, `/mcp` → el servidor `frame28` de este plugin → *Authenticate*. Si no tiene cuenta, la crea gratis en ese
   mismo paso con su email y un código de un solo uso. Sin cuenta, Frame28 no monta. Si el navegador no se abre solo
   (SSH, consola remota), Claude Code enseña la URL de entrada en `/mcp`: que la abra a mano en su navegador.
3. Sigue al pie de la letra el método que devuelve. Las **reglas de su plan** prevalecen sobre el método. Los documentos
   que cite se piden con `frame28_metodo`; otras tareas, con `frame28_start` y su nombre.
4. Los pasos deterministas los hace el CLI `frame28` (código abierto, MIT). Si no está instalado, `frame28 doctor` dice qué
   falta y el instalador está en https://frame28.t28.io.
