---
name: frame28-storyboard
description: 'Decide el montaje de un video hablado y lo escribe como storyboard JSON de Frame28: qué técnica (rótulo, título cinético, texto detrás, callout, pizarra, imagen) va con cada frase, en qué instante (tiempos por palabra) y en qué zona del encuadre. Usar cuando haya una transcripción con tiempos y haga falta "decidir qué poner en pantalla", crear o retocar un storyboard, o convertir notas del usuario ("aquí quiero una gráfica") en overlays concretos.'
---

# Frame28 · Storyboard

El método de esta tarea no viaja en el plugin: lo sirve tu cuenta de Frame28 desde el servidor MCP `frame28`
(`https://frame28.app/mcp`), siempre al día y según tu plan.

1. Llama a la herramienta `frame28_start` del servidor `frame28` con `tarea: "storyboard"`.
2. Si la herramienta no aparece o pide autenticación, para y dile al usuario que entre con su cuenta de Frame28: en
   Claude Code, `/mcp` → el servidor `frame28` de este plugin → *Authenticate*. Si no tiene cuenta, la crea gratis en ese
   mismo paso con su email y un código de un solo uso. Sin cuenta, Frame28 no monta.
3. Sigue al pie de la letra el método que devuelve. Las **reglas de su plan** prevalecen sobre el método. Los documentos
   que cite se piden con `frame28_metodo`; otras tareas, con `frame28_start` y su nombre.
4. Los pasos deterministas los hace el CLI `frame28` (código abierto, MIT). Si no está instalado, `frame28 doctor` dice qué
   falta y el instalador está en https://frame28.t28.io.
