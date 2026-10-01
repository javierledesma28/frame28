---
title: Instalar y operar Frame28 en tu equipo
summary: Para Team. Qué necesita un puesto, cómo se instala en diez minutos, cómo se monta el primer vídeo y qué hacer cuando algo falla.
order: 8
minutes: 6
tier: team
---

Con Team, Frame28 corre en vuestros propios ordenadores: el vídeo no sale de la empresa y el equipo produce sin
depender de nadie. Nosotros instalamos los dos primeros puestos, configuramos vuestra marca y os formamos; este
artículo es la chuleta para después.

## Qué necesita un puesto

- Windows 11 o macOS reciente. Linux también vale.
- 16 GB de memoria; sin tarjeta gráfica dedicada todo funciona, solo más despacio.
- Una cuenta de Claude Code (de Anthropic) para la persona que dirige los montajes. Es quien decide qué va en
  pantalla; el resto lo hace el motor en local.
- Conexión a internet para instalar y para que el render descargue sus scripts. El vídeo no se sube.

## Instalar en diez minutos

Lo más sencillo: abre una terminal y pega el instalador. Pregunta antes de cada paso y comprueba al final.

- Windows (PowerShell): `irm https://frame28.t28.io/install.ps1 | iex`
- macOS (Terminal): `curl -fsSL https://frame28.t28.io/install.sh | bash`

Instala tres programas de apoyo si faltan (ffmpeg para vídeo, Node.js para el render y uv para Python), el motor
`frame28`, y el plugin dentro de Claude Code. En Mac, el primer paso puede pedirte la contraseña del ordenador.

Otra forma, si ya usas Claude Code: pega esto en una sesión y deja que lo haga: *"Instala Frame28 siguiendo
https://frame28.t28.io/instalar.md"*.

Al terminar, en una terminal nueva: `frame28 doctor`. Cada línea con una marca verde es un requisito que está. Las
dos aspas en "gpu" y "modelo RVM" son normales: la primera dice que no hay tarjeta gráfica (va más lento, no peor)
y el modelo se descarga solo la primera vez que hace falta.

## Tu marca

La dejamos configurada en la instalación. Para verla o cambiarla: `frame28 brand list` y `frame28 brand show
<nombre>`. Si cambiáis de identidad, `frame28 brand from-site https://vuestra-web` propone colores, fuente y logo
desde la web y lo revisáis juntos.

## Montar el primer vídeo

1. Carpeta nueva con el clip dentro.
2. Abre Claude Code en esa carpeta y escribe: *"Aquí está mi clip. Móntamelo con la marca {nombre}."*
3. Claude pregunta lo que necesite (destino, duración, idioma), transcribe, corta silencios y muletillas, decide
   los textos y escribe el guion de montaje. Te lo enseña antes de renderizar.
4. Revisa la hoja de contacto (`out/<nombre>_sheet.png`). Pide cambios en lenguaje normal: *"el rótulo del minuto
   1:10 más corto"*, *"quita el contador"*. Cada cambio regenera solo lo necesario.
5. Para shorts: *"Sácame tres shorts verticales con dos ganchos cada uno."* Para otro idioma: *"Versión en inglés."*

Los tiempos en un portátil sin tarjeta gráfica: transcribir un minuto de vídeo, alrededor de un minuto; renderizar
un minuto de vídeo, dos o tres. Se puede dejar en segundo plano.

## Cuando algo falla

| Síntoma | Qué hacer |
|---|---|
| "frame28 no se reconoce" | abre una terminal nueva; si sigue, `uv tool update-shell` y otra terminal nueva |
| El render se queda sin red | el render carga unos scripts de internet la primera vez; conecta y repite |
| Un texto tapa la cara | díselo a Claude: *"mueve el rótulo al otro lado"*; usa el lado libre que detecta `frame28 speaker` |
| Nombres mal transcritos | pasa la lista de nombres y marcas en la petición; se corrigen y se reutilizan |
| Vídeo congelado en el resultado | no edites el HTML generado; pide regenerar desde el guion |
| Algo no cuadra con la instalación | `frame28 doctor` dice qué falta y cómo instalarlo |

Soporte por email con respuesta en dos días laborables mientras la cuota esté activa. Las actualizaciones del
motor llegan con `uv tool upgrade frame28`; las del plugin, desinstalando e instalando desde el marketplace.

## Lo que el equipo aprende en las dos sesiones

Primera: grabar, brief, el primer montaje de principio a fin y cómo leer la hoja de contacto. Segunda: shorts con
ganchos, versiones en otros idiomas, portadas, y cómo pedirle cambios a Claude de forma que salgan a la primera.
