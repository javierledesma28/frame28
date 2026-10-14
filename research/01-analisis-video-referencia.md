# Análisis del video de referencia (privado)

El punto de partida de Frame28 fue el análisis plano a plano de un *founder launch video* real: guion con
marcas de tiempo, sistema de diseño (paleta, tipografías, esquinas de encuadre, conectores), ritmo de montaje y un
catálogo de 16 técnicas con cómo se logra cada una.

Ese documento, junto con los fotogramas y la transcripción del video, **no se publica** porque contiene material
de un tercero. Lo derivado y propio está aquí:

- el catálogo de técnicas, las reglas de dirección y la guía de grabación forman parte del método del director. Hasta
  la v0.4 viajaban en las skills de este repo. Desde la v0.5 los sirve el servidor de Frame28 a cada cuenta: son los
  documentos `tecnicas` y `grabacion` de la herramienta `frame28_metodo`, y la tarea `storyboard` de `frame28_start`.
  Hay copia en el historial de git, en la etiqueta `v0.4.0` (`plugin/skills/frame28-storyboard/`);
- lo que el motor hace con ese criterio, en el código de `plugin/cli/frame28/` (`build.py` para los overlays) y en su
  contrato, [`STORYBOARD.md`](../plugin/cli/frame28/STORYBOARD.md);
- la evaluación de repos y la prueba HyperFrames vs Remotion: [`02-repos-github.md`](02-repos-github.md) y
  [`03-poc-compositores.md`](03-poc-compositores.md).

Cifras que resumen lo aprendido: un evento visual cada 2–4 s, cortes cada ~4 s, animaciones de 200–400 ms,
~40 % hablante con overlays y ~60 % pizarras, y cada gráfica con un solo mensaje y el dato ganador entrando el último.
