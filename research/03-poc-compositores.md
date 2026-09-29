# Prueba de concepto: HyperFrames vs Remotion

**Fecha:** 2026-09-24. **Código y renders:** `poc/` (ver `poc/README.md`).
**Objetivo:** elegir compositor con evidencia, montando las tres técnicas más exigentes del video de referencia en ambos frameworks con el mismo diseño, mismo material y misma máquina (RTX 4060 Laptop, Node 24, Chrome local).

## Las tres escenas (13,4 s en total)

| Escena | Técnica del análisis | Material |
|---|---|---|
| A (0–2,8 s) | **T3 texto detrás del hablante**: fondo = plano completo, palabra gigante, hablante recortado encima | Clip frontal del video de referencia + máscara alfa generada con RobustVideoMatting (ONNX, CPU, 3,5 fps) empaquetada como WebM VP9 con alfa y como secuencia PNG |
| B (2,8–8,8 s) | **T10c bar chart agrupado que se construye** con fila ganadora destacada en caja blanca con esquinas de encuadre | Datos de la tabla "Structured output error rate" del video |
| C (8,8–13,4 s) | **T2 tipografía cinética sincronizada con la voz** | Audio del video (frase "The answer was obviously not…") + tiempos por palabra de faster-whisper |

## Resultado

**Los dos frameworks producen el mismo video, indistinguible a ojo** (misma tipografía, mismo timing, misma sincronía: la voz arranca a los 8,80 s en ambos). Ver `poc/out/comparativa_remotion_vs_hyperframes.png` (Remotion izquierda, HyperFrames derecha).

| Métrica | Remotion 4.0.528 | HyperFrames 0.8.72 |
|---|---|---|
| Andamiaje | `package.json` a mano + `npm install` (254 paquetes, 43 s) | `npx hyperframes init --example blank --non-interactive` (sin `node_modules` propio; usa `npx` pineado) |
| Autoría | React/TSX: 3 componentes, `useCurrentFrame` + `spring`/`interpolate`, `Sequence` | HTML+CSS+GSAP: un `index.html`, timeline GSAP pausada con posiciones absolutas en segundos |
| Líneas escritas | ~190 (TSX) + tokens | ~150 (HTML) |
| Render 1.ª vez (frío) | 2 min 28 s (bundle + extracción PNG del WebM con alfa) | 1 min 16 s (6 workers, GPU) |
| Render siguientes (caché) | 36–39 s | 59 s render / 1 min 13 s pared |
| Tamaño salida (CRF 18) | 2,8 MB | 2,1 MB |
| Vídeo con alfa (WebM VP9) | ✅ `<OffthreadVideo transparent>` | ✅ `<video>` nativo de Chrome |
| Secuencia PNG con alfa | ✅ `<Img>` por frame | (no probado; no hizo falta) |
| Audio sincronizado | ✅ `<Audio>` | ✅ `<audio data-start>` |
| Validación automática | Ninguna | `check`: lint + runtime + layout + motion + contraste. Detectó 2 errores reales (media sin `id`, que habría dejado el vídeo congelado) y una advertencia de contraste legítima |
| Falso positivo | — | El comprobador de layout marca como **error** el texto detrás del hablante ("text_occluded"), porque no sabe que la capa superior tiene alfa. Habrá que silenciarlo para esta técnica |
| Trampa encontrada | **Apilamiento implícito no fiable**: con `AbsoluteFill` (flex) y capas hijas sin `position`/`zIndex`, la capa del hablante quedó debajo del texto en los frames 60–83 y en los *stills*. Con `zIndex` explícito en las tres capas, correcto en los 84 frames | Ninguna en el render. El lint pide `id` en cada elemento con `data-start` y recomienda sub-composiciones para escenas anidadas (solo aviso) |
| Extras relevantes | Ecosistema: `@remotion/captions`, Player, Studio, Lambda | CLI trae `transcribe` (tiempos por palabra), `remove-background`, `capture` (web), `tts`, skills de Claude Code (`/talking-head-recut`) |
| Licencia | Gratis ≤3 personas; Company License si se usa en Semicrol | Apache-2.0 |

## Lo que la PoC demuestra

1. **El efecto "texto detrás del hablante" es viable con software libre y CPU**: RobustVideoMatting recortó pelo y hombros limpiamente sin trimap y ambos compositores aceptan el WebM con alfa. Coste: ~0,3 s por fotograma en CPU a 1000×562; en GPU sería en tiempo real.
2. **La sincronía por palabra funciona con el JSON de tiempos tal cual**: cada palabra entra en su `startMs`. La calidad depende del alineador (ver lecciones en `01-analisis-video-referencia.md`, §6), no del compositor.
3. **Un LLM puede escribir ambas cosas de una pasada**: las tres escenas salieron bien al primer render en los dos frameworks; los dos fallos de diseño (palabra demasiado ancha, caja blanca detrás del fondo por `z-index:-1`) fueron míos e idénticos en ambos.
4. **La diferencia no está en el resultado sino en el proceso**: HyperFrames trae verificación automática y utilidades de pipeline; Remotion trae mejor semántica de tiempo (todo es función del frame) y ecosistema, pero exige más cuidado con CSS y tiene licencia de empresa.

## Decisión

**Compositor por defecto: HyperFrames.** Razones: licencia Apache (no condiciona un posible uso en Semicrol), `check` como *quality gate* automático para lo que genere el agente, y CLI con transcripción y recorte de fondo integrados que cubren dos de nuestras skills previstas. **Remotion queda como segundo backend** para quien tenga licencia o necesite su ecosistema (Player interactivo, Lambda).

**Regla de arquitectura que se deriva:** el storyboard (JSON de escenas tipadas) debe ser **independiente del compositor**, y cada técnica (T1–T16) se implementa como una plantilla HTML/GSAP con las capas y `z-index` explícitos. Así el compositor es intercambiable y el agente no rehace el diseño en cada video.

## Pendientes tras la PoC

- Probar `hyperframes transcribe` y `remove-background` sobre el clip para ver si sustituyen a faster-whisper y a RVM (calidad de tiempos y de bordes).
- Probar `/talking-head-recut` sobre un clip real de 60 s para ver cuánto del estilo de referencia consigue solo.
- Matting en GPU (onnxruntime-gpu o TensorRT) para clips largos.
- Grabar un clip propio del usuario (fondo fijo, buena luz) como material de pruebas en lugar del video de referencia.

---

## Prueba end-to-end (2026-09-29): un clip de 20 s → video "recut" automático

**Objetivo:** ver funcionando la cadena completa sobre un clip real, como la haría la skill: transcripción con tiempos por palabra → decisión de overlays → composición HyperFrames → render. Código y salidas en `_private/poc/e2e/` (no se publica: deriva del video de referencia).

**Entrada:** 20 s del video de referencia (41,3–61,3 s), audio normalizado.

**Qué hace el resultado, todo sincronizado con `transcript.json`:**
- Tarjeta de identidad monoespaciada que se escribe carácter a carácter (T1) mediante una máscara de anchura animada.
- Callouts en caja con esquinas ("2 years", "building in stealth", "side by side") que aparecen al decirse la palabra (T6/T7).
- Títulos cinéticos palabra a palabra ("New type of foundation model", "The improvements are clear") (T2).
- "AUTOMATION" detrás del hablante con máscara alfa de RobustVideoMatting solo en el tramo necesario (T3).
- Tres pizarras a pantalla completa: "System One / Models", lista con foco móvil (Architecture → Sampler → Training algorithm) y "Reinforcement Learning for Calibrated Decisions" con iniciales en rosa (T5).
- Subtítulos por frase (T15).

Render: 1 min 09 s para 20 s a 1080p. `check` pasó sin errores (solo avisos de contraste en texto blanco sobre madera clara: un aviso legítimo a tener en cuenta en el diseño).

**Utilidades integradas de HyperFrames, probadas:**

| Utilidad | Resultado |
|---|---|
| `hyperframes transcribe` (whisper) | **No disponible**: exige `whisper-cpp` compilado con cmake; `doctor` lo confirma. Alternativa que funcionó: importar un SRT con una palabra por cue (`transcribe fichero.srt --preserve-cues`) generado con faster-whisper. Trampa: el SRT debe llevar finales de línea LF; con CRLF el parser devolvió 1 palabra |
| `hyperframes remove-background` (u2net_human_seg) | Funciona en CPU: 600 frames en 5 min 46 s (577 ms/frame). Bordes correctos en pelo y hombros, algo más duros que RVM. RVM en CPU: 300–400 ms/frame y mejor coherencia temporal. Ambos válidos; RVM sigue siendo preferible para el efecto detrás del hablante |
| `hyperframes preview` (Studio) | Abre en `http://127.0.0.1:3002`: línea de tiempo por pistas, previsualización con scrubbing, Inspector para editar elementos, "Describe a change to the agent". Aviso: en la previsualización la capa alfa del hablante siguió visible fuera de su rango de tiempo; el render fue correcto. Tratar el Studio como herramienta de revisión, no como verdad |
| `hyperframes doctor` | Útil para empaquetar requisitos: detecta ffmpeg, Chrome, whisper-cpp, TTS (Kokoro), Docker |

**Lecciones para las skills:**
1. La transcripción debe ser una skill propia (faster-whisper/WhisperX) que **exporte SRT palabra a palabra con LF** e importe en HyperFrames; no depender de su whisper.
2. El material de prueba tiene que ser un clip **sin edición previa**: el video de referencia ya lleva sus propios cortes y textos quemados, y en el segundo 8 el corte a negro del original coincidió con nuestro efecto detrás del hablante.
3. Las posiciones de los overlays hay que darlas inline (el `.clip` con `inset:0` del framework pisa el CSS de clase).
4. El comprobador de contraste avisa con razón: texto blanco sobre fondo de madera necesita sombra o caja.
