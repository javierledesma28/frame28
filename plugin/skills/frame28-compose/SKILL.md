---
name: frame28-compose
description: 'Construye la composición HyperFrames a partir de un storyboard JSON de Frame28, la valida y la renderiza a MP4 con hoja de contacto de revisión. Usar cuando exista un storyboard (o haya que ajustar uno) y se quiera el video final; también para re-renderizar tras cambiar textos, tiempos o posiciones.'
---

# Frame28 · Componer y renderizar

El método de esta tarea no viaja en el plugin: lo sirve tu cuenta de Frame28 desde el servidor MCP `frame28`
(`https://frame28.app/mcp`), siempre al día y según tu plan.

1. Llama a la herramienta `frame28_start` del servidor `frame28` con `tarea: "compose"`.
2. Si la herramienta no aparece o pide autenticación, para y dile al usuario que entre con su cuenta de Frame28: en
   Claude Code, `/mcp` → el servidor `frame28` de este plugin → *Authenticate*. Si no tiene cuenta, la crea gratis en ese
   mismo paso con su email y un código de un solo uso. Sin cuenta, Frame28 no monta. Si el navegador no se abre solo
   (SSH, consola remota), Claude Code enseña la URL de entrada en `/mcp`: que la abra a mano en su navegador.
3. Sigue al pie de la letra el método que devuelve. Las **reglas de su plan** prevalecen sobre el método. Los documentos
   que cite se piden con `frame28_metodo`; otras tareas, con `frame28_start` y su nombre.
4. Los pasos deterministas los hace el CLI `frame28` (código abierto, MIT). Si no está instalado, `frame28 doctor` dice qué
   falta y el instalador está en https://frame28.t28.io.
