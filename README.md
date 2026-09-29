<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="docs/brand/think28-logo-reversed-white.svg">
    <img src="docs/brand/think28-logo-primary-dark.svg" alt="Think28" width="160">
  </picture>
</p>

<h1 align="center">Frame28</h1>

<p align="center"><strong>Graba hablando a cámara. Frame28 monta el resto.</strong></p>

<p align="center">
  Rótulos, títulos que aparecen al ritmo de tu voz, texto gigante que pasa por detrás de ti,<br>
  callouts donde señalas, pizarras y subtítulos. Sin editor de video. Sin plantillas que rellenar.
</p>

<p align="center">
  <a href="#instalación">Instalar</a> ·
  <a href="#cómo-funciona">Cómo funciona</a> ·
  <a href="docs/guia-plugin.md">Guía del plugin</a> ·
  <a href="https://t28.io">t28.io</a>
</p>

<p align="center"><sub>A Think28 product · <a href="https://t28.io">t28.io</a> · v0.1.0 · MIT</sub></p>

---

## Qué hace

Le das un clip de 30 segundos, 5 minutos o lo que sea, de una persona hablando a cámara. Frame28 escucha lo que
dice, entiende cuándo dice cada palabra, decide qué merece aparecer en pantalla y lo renderiza.

| Lo que dices | Lo que aparece |
|---|---|
| "Soy Javier, de Think28" | Tarjeta de identidad que se escribe sola |
| "y esto cambia **todo**" | La palabra clave, gigante, pasando por detrás de tu cabeza |
| "por aquí tenemos la consola…" | Un callout con línea justo donde apunta tu dedo |
| "tres cosas: rápido, barato, fiable" | Una lista donde el foco salta al decir cada una |
| "somos veinte veces más rápidos" | Una cifra que cuenta hasta 20× o una gráfica de barras con tu fila destacada |
| "así se ve el producto" | La captura entrando en pantalla |
| todo el rato | Subtítulos limpios, frase a frase |

El estilo es el de los *launch videos* de los laboratorios de IA: tres fondos, dos tipografías, esquinas de
encuadre, animaciones de un cuarto de segundo. Un evento visual cada dos a cuatro segundos, nunca más de ocho sin
nada. Lo estudiamos plano a plano antes de escribir una línea ([qué sacamos de ahí](research/01-analisis-video-referencia.md)).

## Para quién

- **Fundadores y equipos de producto** que anuncian algo y no tienen editor.
- **Formadores y consultores** que graban explicaciones y quieren que se vean cuidadas.
- **Equipos técnicos** que prefieren un JSON a una línea de tiempo con doscientas capas.

## Cómo funciona

Frame28 es un plugin de [Claude Code](https://claude.com/claude-code) más un CLI. El agente dirige; el CLI ejecuta.

```
tu clip ──▶ prep ──▶ transcribe (tiempos por palabra) ──▶ speaker (dónde estás) ──▶ gestures (dónde señalas) ──▶ matte
                                                                     │
                                       el agente escribe ──▶ storyboard.json ◀── reglas de dirección
                                                                     │
                                          build ──▶ composición HyperFrames ──▶ check ──▶ render ──▶ MP4
```

El **storyboard** es un JSON legible: qué overlay, con qué texto, en qué segundo, en qué zona. Lo escribe el
agente a partir de tu voz; tú lo corriges si quieres y se vuelve a renderizar. Nada de tocar HTML.

Debajo: [HyperFrames](https://github.com/heygen-com/hyperframes) para componer y renderizar,
[faster-whisper](https://github.com/SYSTRAN/faster-whisper) para los tiempos por palabra y
[RobustVideoMatting](https://github.com/PeterL1n/RobustVideoMatting) para recortarte del fondo y
[MediaPipe](https://github.com/google-ai-edge/mediapipe) para saber cuándo y hacia dónde señalas. Todo corre en tu
máquina; tu video no sale de ella.

## Instalación

Necesitas Python 3.11+, [uv](https://docs.astral.sh/uv/), Node.js 22+ y ffmpeg.

```bash
# El plugin (skills para Claude Code)
claude plugin marketplace add javierledesma28/frame28
claude plugin install frame28@think28

# El CLI
uv tool install git+https://github.com/javierledesma28/frame28#subdirectory=plugin/cli
frame28 doctor
```

`frame28 doctor` te dice qué falta y cómo instalarlo. Desde un clon local: `uv tool install --editable ./plugin/cli`.

## Uso

En Claude Code, con el plugin instalado:

> Aquí está mi clip `charla.mp4`. Móntamelo.

Eso dispara `frame28-director`, que hace todo el flujo, te enseña una hoja de contacto del resultado y te entrega
el MP4. Si quieres tocar algo ("el título de los 12 segundos, más pequeño y a la derecha"), lo cambia en el
storyboard y vuelve a renderizar.

Las piezas también van sueltas: `frame28-transcribe`, `frame28-cutout`, `frame28-storyboard`, `frame28-compose`.
Y el CLI a mano, para quien prefiera la terminal:

```bash
frame28 prep charla.mp4 -o work
frame28 transcribe work/audio16k.wav -o work --lang es
frame28 speaker work/clip.mp4
frame28 build work/storyboard.json -o work/project && frame28 render work/project -o out/charla.mp4
```

## Cómo grabar para que salga bien

Cámara fija, fondo fijo, luz de frente, aire a un lado para los textos, frases cortas, gestos lentos. Diez consejos
concretos en [la guía de grabación](plugin/skills/frame28-storyboard/references/grabacion.md).

## Estado y roadmap

v0.1.0 funciona de punta a punta en clips reales (probado en Windows con GPU de portátil). Lo siguiente:

- Gráficas: dispersión y tabla con scroll (barras con fila ganadora y contadores ya están).
- Alineado con guion para nombres propios y karaoke exacto.
- Brand kit por usuario: tus colores, tu tipografía, tu logo en el rótulo.
- Instalador de un comando y una interfaz sobre el storyboard, para quien no quiere ver una terminal.

## Estructura del repositorio

| Ruta | Qué es |
|---|---|
| `plugin/` | el plugin: manifiesto, cinco skills y el CLI `frame28`. Es lo único que se instala |
| `.claude-plugin/marketplace.json` | este repo es su propio marketplace |
| `docs/guia-plugin.md` | el ciclo completo del plugin: crear, probar, publicar, consumir, securizar |
| `docs/brand/` | logos de Think28 (del [press kit](https://t28.io/press-kit.html)) |
| `research/` | análisis del video de referencia, evaluación de repos, prueba HyperFrames vs Remotion |
| `poc/` | pruebas de concepto (los medios y renders no se versionan) |

## Licencias

Frame28 es MIT, © 2026 Think28. HyperFrames es Apache-2.0; faster-whisper, MIT; RobustVideoMatting, GPL-3.0
(se ejecuta como proceso separado y su modelo se descarga en tiempo de uso; no se redistribuye ni se enlaza).

<p align="center"><sub>Hecho por <a href="https://t28.io">Think28</a> · Barcelona · Buenos Aires · Ciudad de México</sub></p>
