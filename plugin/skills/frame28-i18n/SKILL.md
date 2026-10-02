---
name: frame28-i18n
description: 'Saca la versión de un montaje de Frame28 en otro idioma con los mismos tiempos: extrae los textos del storyboard (rótulos, cinéticos, cajas, gancho, CTA, subtítulos), los traduce con criterio de subtitulado (corto, natural, nombres y cifras intactos), los vuelve a aplicar y regenera los subtítulos por palabras sobre el ritmo original. Usar cuando pidan "la versión en inglés", "tradúcelo", "subtítulos en francés", "el mismo vídeo para el mercado alemán" o una segunda lengua de un vídeo ya montado.'
---

# Frame28 · Versión en otro idioma

El método de esta tarea no viaja en el plugin: lo sirve tu cuenta de Frame28 desde el servidor MCP `frame28`
(`https://frame28.app/mcp`), siempre al día y según tu plan.

1. Llama a la herramienta `frame28_start` del servidor `frame28` con `tarea: "i18n"`.
2. Si la herramienta no aparece o pide autenticación, para y dile al usuario que entre con su cuenta de Frame28: en
   Claude Code, `/mcp` → el servidor `frame28` de este plugin → *Authenticate*. Si no tiene cuenta, la crea gratis en ese
   mismo paso con su email y un código de un solo uso. Sin cuenta, Frame28 no monta. Si el navegador no se abre solo
   (SSH, consola remota), Claude Code enseña la URL de entrada en `/mcp`: que la abra a mano en su navegador.
3. Sigue al pie de la letra el método que devuelve. Las **reglas de su plan** prevalecen sobre el método. Los documentos
   que cite se piden con `frame28_metodo`; otras tareas, con `frame28_start` y su nombre.
4. Los pasos deterministas los hace el CLI `frame28` (código abierto, MIT). Si no está instalado, `frame28 doctor` dice qué
   falta y el instalador está en https://frame28.t28.io.
