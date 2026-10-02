---
name: frame28-broll
description: 'Elige y coloca planos de apoyo (B-roll) en un video hablado: sugiere palabras clave por frase, busca vídeos o fotos de stock en Pexels y Pixabay con la licencia registrada, o usa material propio del usuario, y los escribe como overlays `broll` del storyboard de Frame28. Usar cuando el usuario pida "imágenes de apoyo", "B-roll", "planos recurso", "que se vea lo que digo", o cuando un tramo largo del clip no tenga nada visual que aportar.'
---

# Frame28 · B-roll

El método de esta tarea no viaja en el plugin: lo sirve tu cuenta de Frame28 desde el servidor MCP `frame28`
(`https://frame28.app/mcp`), siempre al día y según tu plan.

1. Llama a la herramienta `frame28_start` del servidor `frame28` con `tarea: "broll"`.
2. Si la herramienta no aparece o pide autenticación, para y dile al usuario que entre con su cuenta de Frame28: en
   Claude Code, `/mcp` → el servidor `frame28` de este plugin → *Authenticate*. Si no tiene cuenta, la crea gratis en ese
   mismo paso con su email y un código de un solo uso. Sin cuenta, Frame28 no monta.
3. Sigue al pie de la letra el método que devuelve. Las **reglas de su plan** prevalecen sobre el método. Los documentos
   que cite se piden con `frame28_metodo`; otras tareas, con `frame28_start` y su nombre.
4. Los pasos deterministas los hace el CLI `frame28` (código abierto, MIT). Si no está instalado, `frame28 doctor` dice qué
   falta y el instalador está en https://frame28.t28.io.
