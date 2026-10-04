"""CLI de Frame28. Todas las órdenes devuelven JSON con --json para que un agente las consuma sin parsear texto."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import click

from . import __version__
from .captions import TranscriptFormatError

# Windows abre la consola en cp1252; forzamos UTF-8 para que ✓ ✗ → y acentos no rompan la salida.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        pass


def out(data, as_json: bool):
    if as_json:
        click.echo(json.dumps(data, indent=1, ensure_ascii=False))
    else:
        if isinstance(data, dict):
            for k, v in data.items():
                click.echo(f"{k}: {v}")
        else:
            click.echo(data)


from .log import TimedGroup


@click.group(cls=TimedGroup)
@click.version_option(__version__, prog_name="frame28")
def main():
    """Frame28: de un clip hablando a cámara a un video con overlays sincronizados."""


@main.group(invoke_without_command=True)
@click.option("--log", "log_file", type=click.Path(), default=None, help="fichero de registro (por defecto .frame28/log.jsonl del directorio actual o FRAME28_LOG)")
@click.option("--rate", type=float, default=None, help="coste por hora (en tu moneda) para estimar el coste del vídeo")
@click.option("--json", "as_json", is_flag=True)
@click.pass_context
def report(ctx, log_file, rate, as_json):
    """Tiempo y coste por vídeo: cada orden del CLI se cronometra sola; `report note` añade lo que el CLI no ve (tokens, minutos de persona, stock)."""
    ctx.obj = {"log": Path(log_file) if log_file else None}
    if ctx.invoked_subcommand is None:
        from .log import format_report, report as _report
        r = _report(ctx.obj["log"], rate)
        out(r, True) if as_json else click.echo(format_report(r))


@report.command("note")
@click.argument("text")
@click.option("--tokens", type=int, default=None, help="tokens consumidos por el director (Claude) en este montaje")
@click.option("--cost", type=float, default=None, help="coste directo (stock, API) en tu moneda")
@click.option("--minutes", type=float, default=None, help="minutos de persona (dirección, revisión)")
@click.pass_context
def report_note(ctx, text, tokens, cost, minutes):
    """Añade una nota al registro: lo que el CLI no puede medir."""
    from .log import add_note
    out(add_note(text, tokens, cost, minutes, (ctx.obj or {}).get("log")), True)


@main.command()
@click.argument("url")
@click.option("-o", "--out", "out_mp4", default="input.mp4", show_default=True, type=click.Path())
@click.option("--max-height", default=1080, show_default=True)
@click.option("--json", "as_json", is_flag=True)
def fetch(url, out_mp4, max_height, as_json):
    """Descarga un vídeo de YouTube/Vimeo/etc. (yt-dlp; vía uvx si no está instalado) y deja <out>.source.json con título y origen."""
    from .media import fetch_url
    out(fetch_url(url, out_mp4, max_height), as_json or True)


@main.command()
@click.option("--json", "as_json", is_flag=True)
def doctor(as_json):
    """Comprueba ffmpeg, Node, dependencias Python, modelos, que el código y la instalación coincidan, y red para GSAP."""
    from .doctor import doctor as _doctor
    rows = _doctor()
    if as_json:
        out(rows, True); return
    for r in rows:
        mark = "✓" if r["ok"] else "✗"
        tag = "  (opcional)" if not r["ok"] and r.get("optional") else ""
        click.echo(f"  {mark} {r['name']:<20} {r['detail']}{tag}" + ("" if r["ok"] else f"\n      → {r['fix']}"))
    missing = [r for r in rows if not r["ok"] and not r.get("optional")]
    click.echo("\n" + ("Todo listo." if not missing else f"Faltan {len(missing)} requisitos."))


@main.command()
@click.argument("video", type=click.Path(exists=True))
@click.option("--json", "as_json", is_flag=True)
def probe(video, as_json):
    """Metadatos del clip: duración, resolución, fps, audio y nivel."""
    from .media import probe as _probe
    out(_probe(video), as_json or True)


@main.command()
@click.argument("video", type=click.Path(exists=True))
@click.option("-o", "--out", "out_dir", required=True, type=click.Path())
@click.option("--fps", default=30, show_default=True)
@click.option("--width", default=None, type=int, help="Reescalar el lado largo a esta medida (p. ej. 1920: un vertical queda a 1080×1920)")
@click.option("--denoise", default="afftdn", show_default=True, type=click.Choice(["none", "afftdn", "rnnoise", "deepfilter"]), help="limpieza de la voz")
@click.option("--lufs", default=-14.0, show_default=True)
@click.option("--gpu/--cpu", default=None, help="NVENC o libx264; sin indicarlo, la GPU si la máquina la tiene (FRAME28_ENCODER=auto|nvenc|cpu)")
@click.option("--json", "as_json", is_flag=True)
def prep(video, out_dir, fps, width, denoise, lufs, gpu, as_json):
    """Copia de trabajo: clip.mp4 a 30 fps sin audio + voice.wav limpia y normalizada + audio16k.wav para ASR."""
    from .media import prep as _prep
    if gpu is not None:
        from .env import use_gpu_encoder; use_gpu_encoder(gpu)
    r = _prep(video, out_dir, fps, width, normalize=(denoise == "none"))
    if r.get("voice") and denoise != "none":
        from .audio import clean
        from .env import ffmpeg, run as _run
        raw = Path(r["voice"]).with_name("voice_raw.wav"); Path(r["voice"]).replace(raw)
        c = clean(raw, r["voice"], denoise, 12, lufs)
        _run([ffmpeg(), "-v", "error", "-y", "-i", r["voice"], "-ac", "1", "-ar", "16000", r["audio16k"]])
        r["audio"] = {"denoise": denoise, "before": c["before"], "after": c["after"], "raw": str(raw)}
    out(r, as_json or True)


@main.command()
@click.argument("audio", type=click.Path(exists=True))
@click.option("-o", "--out", "out_dir", required=True, type=click.Path())
@click.option("--lang", default="es", show_default=True)
@click.option("--model", default="medium", show_default=True, help="tiny/base/small/medium/large-v3")
@click.option("--device", default="auto", show_default=True, help="auto (GPU NVIDIA si está lista, si no CPU), cuda o cpu")
@click.option("--compute", default="auto", show_default=True, help="auto: float16 en GPU, int8 en CPU")
@click.option("--script", type=click.Path(exists=True), default=None, help="Guion en texto para sesgar nombres propios")
@click.option("--json", "as_json", is_flag=True)
def transcribe(audio, out_dir, lang, model, device, compute, script, as_json):
    """Transcribe con tiempos por palabra → words.json, captions.json, words.srt (LF), transcript.json (HyperFrames)."""
    from .transcribe import transcribe as _tr
    txt = Path(script).read_text(encoding="utf-8") if script else None
    out(_tr(audio, out_dir, lang, model, device, compute, txt), as_json or True)


@main.command()
@click.argument("video", type=click.Path(exists=True))
@click.option("-o", "--out", "out_webm", required=True, type=click.Path())
@click.option("--start", type=float, default=None)
@click.option("--end", type=float, default=None)
@click.option("--ratio", type=float, default=None, help="downsample_ratio de RVM (auto por resolución)")
@click.option("--fps", default=30, show_default=True)
@click.option("--keep-png", type=click.Path(), default=None, help="Conservar la secuencia PNG RGBA aquí")
@click.option("--json", "as_json", is_flag=True)
def matte(video, out_webm, start, end, ratio, fps, keep_png, as_json):
    """Máscara alfa del hablante (RobustVideoMatting) como WebM VP9 con alfa. Usa --start/--end para solo un tramo."""
    from .matte import matte as _matte
    out(_matte(video, out_webm, start, end, ratio, fps, keep_png), as_json or True)


@main.command()
@click.argument("video", type=click.Path(exists=True))
@click.option("--samples", default=6, show_default=True)
@click.option("--canvas", default="auto", show_default=True, help="lienzo del storyboard, p. ej. 1920x1080 o 1080x1920 (auto: según el formato del clip)")
@click.option("--json", "as_json", is_flag=True)
def speaker(video, samples, canvas, as_json):
    """Dónde está el hablante (bbox en coordenadas del lienzo) y qué lado queda libre para overlays."""
    from .matte import speaker_layout
    from .media import probe
    from .captions import parse_canvas
    v = probe(video, loudness=False).get("video") or {}
    out(speaker_layout(video, samples, canvas=parse_canvas(canvas, v.get("width", 0), v.get("height", 0))), as_json or True)


@main.command()
@click.argument("video", type=click.Path(exists=True))
@click.option("-o", "--out", "out_png", required=True, type=click.Path())
@click.option("--every", default=1.0, show_default=True, help="segundos entre fotogramas")
@click.option("--cols", default=4, show_default=True)
@click.option("--rows", default=5, show_default=True)
def sheet(video, out_png, every, cols, rows):
    """Hoja de contacto para revisar un video de un vistazo."""
    from .media import sheet as _sheet
    click.echo(str(_sheet(video, out_png, every, cols, rows)))


@main.command()
@click.argument("video", type=click.Path(exists=True))
@click.option("-t", "--time", "times", multiple=True, type=float, required=True, help="instante(s) en segundos")
@click.option("-o", "--out", "out_dir", required=True, type=click.Path())
@click.option("--width", default=960, show_default=True)
def frames(video, times, out_dir, width):
    """Extrae fotogramas en instantes concretos (para leer gestos y decidir dónde va cada callout)."""
    from .media import frame_at
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    for t in times:
        click.echo(str(frame_at(video, t, Path(out_dir) / f"f_{t:05.2f}.png", width)))


@main.command()
@click.argument("video", type=click.Path(exists=True))
@click.option("--words", type=click.Path(exists=True), default=None, help="words.json para cruzar gestos con palabras")
@click.option("--sample-fps", default=10.0, show_default=True)
@click.option("--annotate", type=click.Path(), default=None, help="PNG con un fotograma por gesto para revisar")
@click.option("--canvas", default="auto", show_default=True, help="lienzo del storyboard, p. ej. 1920x1080 o 1080x1920 (auto: según el formato del clip)")
@click.option("-o", "--out", "out_json", type=click.Path(), default=None, help="guardar el resultado en JSON")
@click.option("--json", "as_json", is_flag=True)
def gestures(video, words, sample_fps, annotate, canvas, out_json, as_json):
    """Detecta cuándo el hablante señala (MediaPipe Pose) y propone los overlays `pointer` ya colocados (coordenadas del lienzo)."""
    from .pose import analyze
    from .media import probe
    from .captions import parse_canvas
    v = probe(video, loudness=False).get("video") or {}
    r = analyze(video, words, sample_fps, annotate, canvas=parse_canvas(canvas, v.get("width", 0), v.get("height", 0)))
    if out_json:
        Path(out_json).write_text(json.dumps(r, indent=1, ensure_ascii=False), encoding="utf-8")
        r["saved"] = out_json
    out(r, as_json or True)


@main.command()
@click.argument("video", type=click.Path(exists=True), required=False)
@click.option("-o", "--out", "out_png", required=True, type=click.Path(), help="PNG de salida")
@click.option("--title", required=True, help="título; usa | para partir líneas: 'Engrave GLASS|the easy way'")
@click.option("--subtitle", default=None)
@click.option("--badge", default=None, help="insignia arriba a la izquierda: TUTORIAL, 30% OFF, NEW…")
@click.option("--at", "at_s", type=float, default=None, help="segundo del vídeo para el fotograma de fondo")
@click.option("--image", type=click.Path(exists=True), default=None, help="imagen de fondo en vez de un fotograma")
@click.option("--size", default="1280x720", show_default=True, help="1280x720 (YouTube), 1080x1920 (Shorts/Reels), 1080x1080 (ficha)")
@click.option("--brand", default=None, help="marca (think28, nombre en ./brands o ruta a brand.json): color, fuente y logo")
@click.option("--bg", type=click.Choice(["accent", "black", "white", "none"]), default="accent", show_default=True, help="resaltado del título")
@click.option("--darken", default=0.35, show_default=True, help="oscurecido del fondo bajo el título (0–0.8)")
@click.option("--ring", default=None, help="aro de acento sobre el producto: x,y,r en píxeles de la portada")
@click.option("--focus", default=None, help="punto de interés del fondo en fracciones: 0.6,0.5 (recorte y zoom se centran ahí)")
@click.option("--zoom", default=1.0, show_default=True, help="acercar el fondo (1.2 = 20 %)")
@click.option("--font-size", type=int, default=None)
@click.option("--json", "as_json", is_flag=True)
def cover(video, out_png, title, subtitle, badge, at_s, image, size, brand, bg, darken, ring, focus, zoom, font_size, as_json):
    """Portada o miniatura: fotograma + título con resaltado, insignia, logo y aro opcional; captura con HyperFrames (mismas fuentes que el vídeo)."""
    from .cover import make_cover
    w, h = (int(v) for v in size.lower().replace("×", "x").split("x"))
    lines = [t.strip() for t in title.split("|") if t.strip()]
    ring_t = tuple(int(v) for v in ring.split(",")) if ring else None
    focus_t = tuple(float(v) for v in focus.split(",")) if focus else None
    r = make_cover(video, out_png, lines[0], at_s, image, None, subtitle=subtitle, badge=badge, size=(w, h), brand=brand, bg=bg,
                   darken=darken, ring=ring_t, focus=focus_t, zoom=zoom, font_size=font_size, lines=lines)
    out(r, as_json or True)


@main.command()
@click.argument("video", type=click.Path(exists=True))
@click.option("-o", "--out", "out_mp4", required=True, type=click.Path())
@click.option("--mode", type=click.Choice(["crop", "blur"]), default="crop", show_default=True, help="crop: ventana 9:16 que sigue al hablante; blur: 16:9 entero sobre fondo desenfocado")
@click.option("--size", default="1080x1920", show_default=True, help="salida, p. ej. 1080x1920 o 1080x1080")
@click.option("--deadzone", default=0.10, show_default=True, help="zona muerta (fracción del ancho de la ventana) antes de mover la cámara")
@click.option("--smooth", default=0.8, show_default=True, help="constante de tiempo del suavizado (s); más = más lento y suave")
@click.option("--max-speed", default=0.5, show_default=True, help="velocidad máxima (anchos de ventana por segundo)")
@click.option("--path", "path_json", type=click.Path(), default=None, help="dónde guardar reframe.json (camino de la cámara y franjas libres); por defecto junto a la salida")
@click.option("--gpu/--cpu", default=None, help="NVENC o libx264; sin indicarlo, la GPU si la máquina la tiene (FRAME28_ENCODER=auto|nvenc|cpu)")
@click.option("--json", "as_json", is_flag=True)
def reframe(video, out_mp4, mode, size, deadzone, smooth, max_speed, path_json, gpu, as_json):
    """Reencuadra un clip apaisado a vertical (9:16) siguiendo al hablante (MediaPipe) o con fondo desenfocado."""
    from .reframe import reframe as _reframe
    if gpu is not None:
        from .env import use_gpu_encoder; use_gpu_encoder(gpu)
    w, h = (int(v) for v in size.lower().replace("×", "x").split("x"))
    r = _reframe(video, out_mp4, mode, (w, h), deadzone, smooth, max_speed, path_json)
    if as_json:
        out(r, True); return
    click.echo(f"  {r['output']}  modo {r['mode']}  {r['source'][0]}x{r['source'][1]} → {r['out'][0]}x{r['out'][1]}")
    if mode == "crop":
        click.echo(f"  ventana {r['crop'][0]}x{r['crop'][1]} (escala x{r['scale']}), {r['frames']} fotogramas, sujeto detectado en {r['detected_samples']}/{r['samples']} muestras, cámara en movimiento en {r['moving_samples']}")
    else:
        fg = r["foreground"]; click.echo(f"  vídeo en y {fg['y']}–{fg['y'] + fg['h']}; franjas libres {r['free_bands']}")
    click.echo(f"  reframe.json: {r['path_json']}")


@main.command("reframe-map")
@click.argument("reframe_json", type=click.Path(exists=True))
@click.option("--gestures", "gestures_json", type=click.Path(exists=True), default=None, help="gestures.json del clip apaisado: devuelve los pointers en el lienzo vertical")
@click.option("--point", "points", multiple=True, help="punto del lienzo apaisado 'x,y,t' (repetible), p. ej. --point 1400,600,4.2")
@click.option("--canvas", default="1920x1080", show_default=True, help="lienzo apaisado en el que están las coordenadas de entrada")
@click.option("-o", "--out", "out_json", type=click.Path(), default=None, help="guardar el resultado en JSON")
@click.option("--json", "as_json", is_flag=True)
def reframe_map(reframe_json, gestures_json, points, canvas, out_json, as_json):
    """Convierte coordenadas del apaisado (gestos, callouts, puntos) al lienzo vertical de `frame28 reframe --path`, sin repetir la detección."""
    from .reframe import map_canvas_point, map_gestures, point_visible
    res = json.loads(Path(reframe_json).read_text(encoding="utf-8-sig"))
    cw, ch = (int(v) for v in canvas.lower().replace("×", "x").split("x"))
    r: dict = {"mode": res.get("mode"), "canvas": res.get("out")}
    if gestures_json:
        r = map_gestures(res, json.loads(Path(gestures_json).read_text(encoding="utf-8-sig")))
    if points:
        W, H = res["source"]
        r["points"] = []
        for spec in points:
            x, y, t = (float(v) for v in spec.split(","))
            r["points"].append({"in": [x, y, t], "out": map_canvas_point(res, x, y, t, (cw, ch)),
                                "visible": point_visible(res, x * W / cw, y * H / ch, t)})
    if not gestures_json and not points:
        raise click.UsageError("indica --gestures gestures.json o al menos un --point x,y,t")
    if out_json:
        Path(out_json).write_text(json.dumps(r, indent=1, ensure_ascii=False), encoding="utf-8")
        r["saved"] = out_json
    if as_json:
        out(r, True); return
    for p in r.get("points", []):
        click.echo(f"  ({p['in'][0]:.0f},{p['in'][1]:.0f}) @ {p['in'][2]}s → ({p['out'][0]},{p['out'][1]})" + ("" if p["visible"] else "  fuera del encuadre"))
    for p in r.get("pointer_suggestions", []):
        click.echo(f"  {p['id']} at={p['at']}s dot={p['dot']} box={p['box']} '{p['text']}'" + ("" if p["visible"] else "  fuera del encuadre"))
    for w in r.get("warnings", []):
        click.echo(f"  ! {w}")
    if out_json:
        click.echo(f"  guardado: {out_json}")


@main.command()
@click.argument("video", type=click.Path(exists=True))
@click.option("--sample-fps", default=1.0, show_default=True, help="muestras por segundo (0.5 = doble de rápido)")
@click.option("--canvas", default="auto", show_default=True, help="lienzo del storyboard, p. ej. 1920x1080")
@click.option("--annotate", type=click.Path(), default=None, help="PNG con el mapa de zonas ocupadas y la lista de gráficos")
@click.option("-o", "--out", "out_json", type=click.Path(), default=None, help="guardar graphics.json")
@click.option("--json", "as_json", is_flag=True)
def graphics(video, sample_fps, canvas, annotate, out_json, as_json):
    """Gráficos ya presentes en el vídeo (rótulos, marca de agua, subtítulos quemados, texto en objetos, tarjetas) y zonas libres. OCR en CPU, ~1 s por muestra."""
    from .graphics import scan, annotate as _annotate
    from .media import probe
    from .captions import parse_canvas
    v = probe(video, loudness=False).get("video") or {}
    r = scan(video, sample_fps, canvas=parse_canvas(canvas, v.get("width", 0), v.get("height", 0)))
    if out_json:
        Path(out_json).write_text(json.dumps(r, indent=1, ensure_ascii=False), encoding="utf-8"); r["saved"] = out_json
    if annotate:
        _annotate(r, annotate, video); r["annotated"] = str(annotate)
    if as_json:
        out(r, True); return
    click.echo(f"  {r['samples']} muestras · {len(r['events'])} textos · {len(r['cards'])} tarjetas · subtítulos quemados: {'sí' if r['burned_subtitles'] else 'no'}")
    for e in r["events"]:
        if e["kind"] != "scene_text":
            click.echo(f"  {e['start']:6.1f}–{e['end']:6.1f}  {e['kind']:<10} {e['bbox']}  {e['text'][:50]!r}")
    for c in r["cards"]:
        click.echo(f"  {c['start']:6.1f}–{c['end']:6.1f}  card       {c['color']}")
    click.echo("  zonas (ocupación % del tiempo): " + "  ".join(f"{z} {r['zones'][z]['busy_pct']}" for z in r["zones"]))
    if out_json:
        click.echo(f"  guardado: {out_json}")
    if annotate:
        click.echo(f"  mapa: {annotate}")


@main.group()
def audio():
    """Medir y limpiar la voz: graves, ruido y sonoridad normalizada (EBU R128)."""


@audio.command("measure")
@click.argument("path", type=click.Path(exists=True))
@click.option("--json", "as_json", is_flag=True)
def audio_measure(path, as_json):
    """LUFS integrado, rango, pico real, suelo de ruido y relación señal/ruido."""
    from .audio import measure
    out(measure(path), as_json or True)


@audio.command("clean")
@click.argument("path", type=click.Path(exists=True))
@click.option("-o", "--out", "dst", required=True, type=click.Path())
@click.option("--denoise", default="afftdn", show_default=True, type=click.Choice(["none", "afftdn", "rnnoise", "deepfilter"]))
@click.option("--strength", default=12, show_default=True, help="dB de reducción para afftdn (6–30)")
@click.option("--lufs", default=-14.0, show_default=True, help="sonoridad objetivo (-14 YouTube, -16 podcast/vertical)")
@click.option("--tp", default=-1.5, show_default=True, help="pico real máximo (dBTP)")
@click.option("--highpass", default=80, show_default=True, help="Hz del filtro de graves (0 = desactivar)")
@click.option("--deess", is_flag=True, help="suavizar eses silbantes")
@click.option("--json", "as_json", is_flag=True)
def audio_clean(path, dst, denoise, strength, lufs, tp, highpass, deess, as_json):
    """Limpia y normaliza la voz en dos pasadas → WAV 48 kHz estéreo listo para el montaje y la transcripción."""
    from .audio import clean
    r = clean(path, dst, denoise, strength, lufs, tp, 11.0, highpass, deess)
    if as_json:
        out(r, True); return
    b, a = r["before"], r["after"]
    click.echo(f"salida: {r['output']}   (motor de ruido: {r['denoise']})")
    click.echo(f"  sonoridad   {b['integrated_lufs']:>7} → {a['integrated_lufs']:>7} LUFS   (objetivo {lufs})")
    click.echo(f"  pico real   {b['true_peak_dbtp']:>7} → {a['true_peak_dbtp']:>7} dBTP")
    click.echo(f"  suelo ruido {b['noise_floor_dbfs']:>7} → {a['noise_floor_dbfs']:>7} dBFS")
    click.echo(f"  señal/ruido {b['snr_db']:>7} → {a['snr_db']:>7} dB   ({'+' if r['noise_reduction_db'] >= 0 else ''}{r['noise_reduction_db']} dB)")


@audio.command("compare")
@click.argument("paths", nargs=-1, type=click.Path(exists=True))
@click.option("-o", "--out", "out_png", required=True, type=click.Path())
def audio_compare(paths, out_png):
    """Espectrogramas apilados de varios ficheros (antes / después) en un PNG."""
    from .audio import spectrogram
    click.echo(str(spectrogram(list(paths), out_png)))


@main.group()
def cut():
    """Jump cuts por transcripción: quitar silencios, muletillas y repeticiones."""


@cut.command("plan")
@click.argument("words", type=click.Path(exists=True))
@click.option("--audio", type=click.Path(exists=True), default=None, help="voice.wav para confirmar los silencios")
@click.option("--min-gap", default=0.6, show_default=True, help="pausa mínima (s) para cortar")
@click.option("--pad", default=0.12, show_default=True, help="aire que se deja a cada lado del corte (s)")
@click.option("--lang", default="es", show_default=True)
@click.option("--no-fillers", is_flag=True, help="no cortar muletillas")
@click.option("--no-retakes", is_flag=True, help="no detectar repeticiones")
@click.option("--duration", type=float, default=None, help="duración del clip si no se pasa audio")
@click.option("-o", "--out", "out_json", required=True, type=click.Path())
def cut_plan(words, audio, min_gap, pad, lang, no_fillers, no_retakes, duration, out_json):
    """Propone los cortes → cuts.json (tramos a conservar y motivo de cada eliminación)."""
    from .cut import plan as _plan
    r = _plan(words, audio, min_gap, pad, lang, not no_fillers, not no_retakes, duration)
    Path(out_json).write_text(json.dumps(r, indent=1, ensure_ascii=False), encoding="utf-8")
    click.echo(f"duración: {r['source_duration']} s → {r['result_duration']} s  (se quitan {r['removed_seconds']} s en {len(r['removed'])} tramos)")
    for x in r["removed"]:
        click.echo(f"  - {x['start']:6.2f}–{x['end']:6.2f}  {x['reason']}")
    click.echo(f"guardado: {out_json}")


@cut.command("apply")
@click.argument("video", type=click.Path(exists=True))
@click.argument("cuts", type=click.Path(exists=True))
@click.option("--audio", type=click.Path(exists=True), default=None)
@click.option("--words", type=click.Path(exists=True), default=None)
@click.option("--captions", type=click.Path(exists=True), default=None)
@click.option("--storyboard", type=click.Path(exists=True), default=None)
@click.option("-o", "--out", "out_dir", required=True, type=click.Path())
@click.option("--gpu/--cpu", default=None, help="NVENC o libx264; sin indicarlo, la GPU si la máquina la tiene (FRAME28_ENCODER=auto|nvenc|cpu)")
@click.option("--json", "as_json", is_flag=True)
def cut_apply(video, cuts, audio, words, captions, storyboard, out_dir, gpu, as_json):
    """Aplica cuts.json: clip.mp4 y voice.wav cortados (fundidos de 30 ms) + words/captions/storyboard remapeados."""
    if gpu is not None:
        from .env import use_gpu_encoder; use_gpu_encoder(gpu)
    from .cut import apply as _apply
    out(_apply(video, audio, cuts, out_dir, words, captions, storyboard), as_json or True)


@main.group()
def broll():
    """B-roll de stock (Pexels/Pixabay) con licencia registrada: sugerir, buscar, elegir y descargar."""


@broll.command("providers")
def broll_providers():
    """Qué proveedores tienen clave (PEXELS_API_KEY, PIXABAY_API_KEY o ~/.config/frame28/keys.json)."""
    from .broll import providers_available, KEYS_FILE
    p = providers_available()
    for k, v in p.items():
        click.echo(f"  {k:<8} {'clave OK' if v else 'sin clave'}")
    if not any(p.values()):
        click.echo(f"  Consigue claves gratuitas en https://www.pexels.com/api/ y https://pixabay.com/api/docs/ y guárdalas en\n  {KEYS_FILE}  como {{\"PEXELS_API_KEY\": \"...\", \"PIXABAY_API_KEY\": \"...\"}}  o como variables de entorno.")


@broll.command("suggest")
@click.argument("captions", type=click.Path(exists=True))
@click.option("--lang", default="es", show_default=True)
@click.option("--json", "as_json", is_flag=True)
def broll_suggest(captions, lang, as_json):
    """Palabras clave por frase (de captions.json) como punto de partida para las búsquedas."""
    from .broll import suggest
    s = suggest(captions, lang)
    if as_json:
        out(s, True)
    else:
        for x in s:
            click.echo(f"{x['start']:7.2f}–{x['end']:6.2f}  {x['query']:<28}  {x['text'][:70]}")


@broll.command("search")
@click.argument("query")
@click.option("--kind", type=click.Choice(["video", "photo"]), default="video", show_default=True)
@click.option("--provider", type=click.Choice(["auto", "pexels", "pixabay"]), default="auto", show_default=True)
@click.option("--orientation", type=click.Choice(["landscape", "portrait", "square"]), default="landscape", show_default=True)
@click.option("--per-page", default=8, show_default=True)
@click.option("--sheet", "sheet_png", type=click.Path(), default=None, help="hoja de contacto PNG de los candidatos")
@click.option("-o", "--out", "out_json", type=click.Path(), default=None, help="guardar candidatos en JSON (para fetch)")
@click.option("--json", "as_json", is_flag=True)
def broll_search(query, kind, provider, orientation, per_page, sheet_png, out_json, as_json):
    """Busca vídeos o fotos de stock. Usa consultas en inglés y concretas ("city traffic night", no "ciudad")."""
    from .broll import search, sheet, providers_available
    if not any(providers_available().values()):
        raise SystemExit("Sin claves de Pexels/Pixabay: ejecuta `frame28 broll providers`.")
    items = search(query, kind, provider, orientation, per_page)
    if out_json:
        Path(out_json).write_text(json.dumps(items, indent=1, ensure_ascii=False), encoding="utf-8")
    if sheet_png and items:
        sheet(items, sheet_png)
    if as_json:
        out(items, True)
    else:
        for it in items:
            click.echo(f"  {it['id']:<18} {it['kind']:<5} {str(it.get('duration') or ''):>4}s {it.get('width')}x{it.get('height')}  {it.get('author') or ''}  {it.get('page')}")
        if sheet_png:
            click.echo(f"  hoja: {sheet_png}")
        if out_json:
            click.echo(f"  candidatos: {out_json}")


@broll.command("fetch")
@click.argument("candidates", type=click.Path(exists=True))
@click.argument("item_id")
@click.option("-o", "--out", "out_dir", default="work/broll", show_default=True, type=click.Path())
@click.option("--in", "trim_in", default=0.0, show_default=True, help="segundo del clip de stock por el que empezar")
@click.option("--duration", default=None, type=float, help="segundos a conservar (recorta a *_cut.mp4, sin audio, 30 fps)")
@click.option("--width", default=None, type=int, help="reescalar el recorte a este ancho")
@click.option("--json", "as_json", is_flag=True)
def broll_fetch(candidates, item_id, out_dir, trim_in, duration, width, as_json):
    """Descarga un candidato (id de `search -o`) con su sidecar de licencia; opcionalmente recortado."""
    from .broll import fetch
    items = json.loads(Path(candidates).read_text(encoding="utf-8-sig"))
    it = next((x for x in items if x["id"] == item_id), None)
    if not it:
        raise SystemExit(f"id {item_id} no está en {candidates}")
    out(fetch(it, out_dir, trim_in, duration, width), as_json or True)


@main.group()
def clips():
    """Fábrica de shorts: tramos con más momentos de venta, ganchos, recorte y storyboard de partida."""


@clips.command("plan")
@click.argument("captions", type=click.Path(exists=True))
@click.option("--target", default=30.0, show_default=True, help="duración deseada (s)")
@click.option("--count", default=5, show_default=True, help="cuántos tramos proponer")
@click.option("--lang", default="en", show_default=True)
@click.option("--min-len", default=15.0, show_default=True)
@click.option("--max-len", default=45.0, show_default=True)
@click.option("--keyword", "keywords", multiple=True, help="nombre del producto o marca (puntúa las frases que lo nombran); repetible")
@click.option("--words", "words_path", type=click.Path(exists=True), default=None, help="words.json: frases completas con tiempos exactos (transcripciones antiguas, cortadas a mitad de frase)")
@click.option("-o", "--out", "out_json", type=click.Path(), default=None, help="guardar clips.json")
@click.option("--json", "as_json", is_flag=True)
def clips_plan(captions, target, count, lang, min_len, max_len, keywords, words_path, out_json, as_json):
    """Propone los tramos de 15–45 s con más momentos (resultado, promesa, objeción, cifras, producto) y tres ganchos por tramo."""
    from .clips import plan
    r = plan(captions, target, count, lang, min_len, max_len, list(keywords), words_path=words_path)
    if out_json:
        Path(out_json).write_text(json.dumps(r, indent=1, ensure_ascii=False), encoding="utf-8")
    if as_json:
        out(r, True); return
    click.echo(f"  {r['moments']} momentos en la transcripción · {len(r['clips'])} tramos propuestos")
    if r.get("note"):
        click.echo(f"  aviso: {r['note']}")
    for c in r["clips"]:
        kinds = ", ".join(sorted({m["kind"] for m in c["moments"]}))
        click.echo(f"  {c['id']}  {c['start']:6.1f}–{c['end']:6.1f}  {c['duration']:4.1f}s  puntos {c['score']:5.1f}  [{kinds}]")
        click.echo(f"      «{c['phrases'][0][:70]}…»")
        for h in c["hooks"]:
            click.echo(f"      gancho {h['type']:<14} {' / '.join(h['lines'])}")
    if out_json:
        click.echo(f"  guardado: {out_json}")


@clips.command("markers")
@click.argument("captions", type=click.Path(exists=True))
@click.option("--lang", default="en", show_default=True)
@click.option("--words", "words_path", type=click.Path(exists=True), default=None, help="words.json: `at` exactos de cada palabra del cinético")
@click.option("--canvas", default="1920x1080", show_default=True, help="lienzo del storyboard (1080x1920 en vertical)")
@click.option("--side", default="right", show_default=True, type=click.Choice(["right", "left"]), help="lado libre del hablante (free_side de `frame28 speaker`); en vertical se ignora")
@click.option("--lead", default=8.0, show_default=True, help="segundos antes de la frase de resultado para el fotograma 'antes'")
@click.option("--settle", default=1.0, show_default=True, help="segundos tras la frase para el 'después' y la entrada del antes/después")
@click.option("-o", "--out", "out_json", type=click.Path(), default=None, help="guardar markers.json")
@click.option("--json", "as_json", is_flag=True)
def clips_markers(captions, lang, words_path, canvas, side, lead, settle, out_json, as_json):
    """Marcadores de resultado: en cada frase de resultado propone before_after (dos instantes del clip), draw check y kinetic; en cada promesa, kinetic."""
    from .clips import markers
    w, h = (int(v) for v in canvas.lower().replace("×", "x").split("x"))
    r = markers(captions, lang, words_path, (w, h), side, lead, settle)
    if out_json:
        Path(out_json).write_text(json.dumps(r, indent=1, ensure_ascii=False), encoding="utf-8")
    if as_json:
        out(r, True); return
    click.echo(f"  {r['results']} momentos de resultado · {r['promises']} promesas · lienzo {w}x{h} · {r['duration']:.1f} s")
    for m in r["markers"]:
        kinds = " + ".join(o["type"] for o in m["overlays"])
        ba = next((o for o in m["overlays"] if o["type"] == "before_after"), None)
        extra = f"  (antes {ba['before_t']:.1f} s, después {ba['after_t']:.1f} s)" if ba else ""
        click.echo(f"  {m['id']:<6} {m['t']:6.1f}–{m['end']:6.1f}  {m['kind']:<8} «{m['phrase'][:60]}»")
        click.echo(f"         → {kinds}{extra}")
    click.echo("  " + r["note"])
    if out_json:
        click.echo(f"  guardado: {out_json}")


@clips.command("cut")
@click.argument("clips_json", type=click.Path(exists=True))
@click.argument("clip_id")
@click.argument("video", type=click.Path(exists=True))
@click.option("--audio", type=click.Path(exists=True), default=None, help="voice.wav")
@click.option("--words", type=click.Path(exists=True), default=None)
@click.option("--captions", type=click.Path(exists=True), default=None)
@click.option("-o", "--out", "out_dir", type=click.Path(), default=None, help="carpeta del short (por defecto work/clips/<id>)")
@click.option("--json", "as_json", is_flag=True)
def clips_cut(clips_json, clip_id, video, audio, words, captions, out_dir, as_json):
    """Recorta el tramo elegido: clip.mp4, voice.wav, words.json y captions.json remapeados (fundidos de 30 ms)."""
    from .clips import extract
    plan_ = json.loads(Path(clips_json).read_text(encoding="utf-8-sig"))
    clip = next((c for c in plan_["clips"] if c["id"] == clip_id), None)
    if not clip:
        raise SystemExit(f"{clip_id} no está en {clips_json}")
    out(extract(clip, video, audio, words, captions, out_dir or f"work/clips/{clip_id}"), as_json or True)


@clips.command("scaffold")
@click.argument("clips_json", type=click.Path(exists=True))
@click.argument("clip_id")
@click.option("--dir", "clip_dir", type=click.Path(exists=True), default=None, help="carpeta del short (por defecto work/clips/<id>)")
@click.option("--canvas", default="1080x1920", show_default=True)
@click.option("--platform", default="tiktok", show_default=True)
@click.option("--brand", default=None, help="nombre de marca (think28, o una de ./brands)")
@click.option("--cta", "cta_json", type=click.Path(exists=True), default=None, help="JSON con los campos del overlay cta (price, code, url…)")
@click.option("--hook", "hook_index", default=0, show_default=True, help="cuál de los tres ganchos usar (0, 1, 2)")
@click.option("--video", "video_name", default="clip.mp4", show_default=True, help="vídeo dentro de la carpeta (vertical.mp4 tras reframe)")
@click.option("--json", "as_json", is_flag=True)
def clips_scaffold(clips_json, clip_id, clip_dir, canvas, platform, brand, cta_json, hook_index, video_name, as_json):
    """Escribe el storyboard de partida del short (gancho, subtítulos por palabras, CTA) que ya construye con `frame28 build`."""
    from .clips import scaffold
    plan_ = json.loads(Path(clips_json).read_text(encoding="utf-8-sig"))
    clip = next((c for c in plan_["clips"] if c["id"] == clip_id), None)
    if not clip:
        raise SystemExit(f"{clip_id} no está en {clips_json}")
    w, h = (int(v) for v in canvas.lower().replace("×", "x").split("x"))
    cta = json.loads(Path(cta_json).read_text(encoding="utf-8-sig")) if cta_json else None
    out(scaffold(clip, clip_dir or f"work/clips/{clip_id}", (w, h), platform, brand, cta, hook_index, video_name), as_json or True)


@clips.command("batch")
@click.argument("clips_json", type=click.Path(exists=True))
@click.argument("clip_ids", nargs=-1)
@click.option("--clips-dir", type=click.Path(), default="work/clips", show_default=True, help="carpeta con <id>/ de `clips cut`")
@click.option("-o", "--out", "out_dir", type=click.Path(), default="out/shorts", show_default=True, help="MP4 de salida: <id>-hook<N>.mp4")
@click.option("--hooks", default="all", show_default=True, help="'all' o índices separados por coma: 0,2")
@click.option("--canvas", default="1080x1920", show_default=True)
@click.option("--platform", default="tiktok", show_default=True)
@click.option("--brand", default=None, help="nombre de marca o ruta a .json")
@click.option("--cta", "cta_json", type=click.Path(exists=True), default=None, help="JSON con los campos del overlay cta")
@click.option("--video", "video_name", default="clip.mp4", show_default=True, help="vídeo dentro de la carpeta del short (vertical.mp4 tras reframe)")
@click.option("--no-render", is_flag=True, help="solo storyboards y proyectos construidos (sin check ni render)")
@click.option("--keep", is_flag=True, help="no regenerar los storyboard-hook<N>.json que ya existan (afinados a mano): solo construir y renderizar")
@click.option("--quality", default="high", show_default=True, type=click.Choice(["draft", "standard", "high"]))
@click.option("--workers", default=None, type=click.IntRange(1, 32), help="trabajadores de captura del render (como `frame28 render`)")
@click.option("--gpu/--cpu", default=None, help="codificar los MP4 con NVENC o libx264; sin indicarlo, la GPU si la máquina la tiene")
@click.option("--json", "as_json", is_flag=True)
def clips_batch(clips_json, clip_ids, clips_dir, out_dir, hooks, canvas, platform, brand, cta_json, video_name, no_render, keep, quality, workers, gpu, as_json):
    """Variantes de gancho en lote: por cada short y cada gancho, storyboard + build (+ check + render) → <id>-hook<N>.mp4 y batch.json."""
    from .clips import batch
    w, h = (int(v) for v in canvas.lower().replace("×", "x").split("x"))
    cta = json.loads(Path(cta_json).read_text(encoding="utf-8-sig")) if cta_json else None
    hook_idx = None if hooks == "all" else [int(x) for x in hooks.split(",") if x.strip()]
    r = batch(clips_json, list(clip_ids) or None, clips_dir, out_dir, hook_idx, (w, h), platform, brand, cta, video_name, not no_render, quality, keep,
              workers=workers, gpu=gpu)
    if as_json:
        out(r, True); return
    for v in r["variants"]:
        mark = "✓" if v["ok"] else "✗"
        click.echo(f"  {mark} {v['name']:<14} {v.get('output') or v['storyboard']}" + ("  (storyboard conservado)" if v.get("kept") else "")
                   + (f"  {v['error']}" if v.get("error") else ""))
    click.echo(f"  {r['ok']} de {len(r['variants'])} variantes · manifiesto: {r['manifest']}")
    if r["skipped"]:
        click.echo("  sin carpeta (haz `clips cut` antes): " + ", ".join(r["skipped"]))


@main.group()
def i18n():
    """Versión en otro idioma: extraer los textos del storyboard, traducirlos (lo hace el agente) y aplicarlos con los mismos tiempos."""


@i18n.command("extract")
@click.argument("storyboard", type=click.Path(exists=True))
@click.option("--captions", "captions_path", type=click.Path(exists=True), default=None, help="captions.json del clip (para regenerar los subtítulos por palabras)")
@click.option("-o", "--out", "out_json", type=click.Path(), default=None, help="strings.json (por defecto <storyboard>.strings.json)")
def i18n_extract(storyboard, captions_path, out_json):
    """Saca todos los textos visibles (overlays y subtítulos) a un JSON plano con clave, tipo, instante y límite orientativo."""
    from .i18n import extract_with_captions
    sbp = Path(storyboard); sb = json.loads(sbp.read_text(encoding="utf-8-sig"))
    cp = captions_path or (sbp.parent / "captions.json" if (sbp.parent / "captions.json").exists() else None)
    r = extract_with_captions(sb, cp)
    outp = Path(out_json) if out_json else sbp.with_name(sbp.stem + ".strings.json")
    outp.write_text(json.dumps(r, indent=1, ensure_ascii=False), encoding="utf-8")
    click.echo(f"  {r['count']} textos ({r['lang'] or 'idioma sin declarar'}) → {outp}")
    click.echo("  Traduce los valores 'text' (mismas claves) y aplica con: frame28 i18n apply <storyboard> <strings traducido> --lang <xx>")


@i18n.command("apply")
@click.argument("storyboard", type=click.Path(exists=True))
@click.argument("strings", type=click.Path(exists=True))
@click.option("--lang", required=True, help="código del idioma destino: en, es, fr, de, pt…")
@click.option("-o", "--out", "out_path", type=click.Path(), default=None, help="storyboard traducido (por defecto <storyboard>.<lang>.json)")
@click.option("--words", "words_path", type=click.Path(exists=True), default=None, help="words.json original (subtítulos por palabras)")
@click.option("--captions", "captions_path", type=click.Path(exists=True), default=None, help="captions.json original")
@click.option("--json", "as_json", is_flag=True)
def i18n_apply(storyboard, strings, lang, out_path, words_path, captions_path, as_json):
    """Escribe el storyboard en el otro idioma con los mismos tiempos; con subtítulos por palabras genera words.<lang>.json."""
    from .i18n import translate_project
    r = translate_project(storyboard, strings, lang, out_path, words_path, captions_path)
    if as_json:
        out(r, True); return
    click.echo(f"  {r['translated']} textos aplicados → {r['storyboard']}" + (f"  · palabras: {r['words']} ({r['words_count']})" if r.get("words") else ""))
    for w in r["warnings"]:
        click.echo(f"  ! {w}")
    click.echo("  Ahora: frame28 build <storyboard traducido> -o <proyecto> && frame28 check && frame28 render")
    click.echo("  Si algo reescribe el storyboard traducido después de esto: frame28 i18n check <storyboard traducido>")


@i18n.command("check")
@click.argument("storyboard", type=click.Path(exists=True))
@click.option("--json", "as_json", is_flag=True)
def i18n_check(storyboard, as_json):
    """Antes de renderizar una versión traducida: avisa de los textos visibles que siguen igual que en el original
    (salvo cifras, marcas, nombres y lo marcado en meta.i18n.keep). Sale con código 1 si queda alguno."""
    from .i18n import leftovers
    sb = json.loads(Path(storyboard).read_text(encoding="utf-8-sig"))
    info = (sb.get("meta") or {}).get("i18n")
    left = leftovers(sb)
    if as_json:
        out({"storyboard": storyboard, "fingerprint": bool(info), "leftovers": left}, True)
    elif not info:
        click.echo("  ! este storyboard no tiene la huella de i18n apply (meta.i18n): vuelve a aplicar la traducción para poder comprobarlo")
    elif not left:
        click.echo(f"  ✓ ningún texto visible sigue en el idioma original ({sb.get('meta', {}).get('lang', '?')})")
    else:
        for w in left:
            click.echo(f"  ✗ {w}")
    if left:
        raise SystemExit(1)


@main.group()
def captions():
    """Subtítulos: exportar SRT/VTT legibles a partir de words.json."""


@captions.command("export")
@click.argument("words", type=click.Path(exists=True))
@click.option("-o", "--out", "out_path", required=True, type=click.Path(), help="fichero .srt o .vtt")
@click.option("--max-chars", default=42, show_default=True, help="caracteres por línea")
@click.option("--max-lines", default=2, show_default=True)
@click.option("--max-dur", default=7.0, show_default=True, help="segundos por cue")
@click.option("--max-gap", default=0.7, show_default=True, help="pausa (s) que fuerza un cue nuevo")
@click.option("--max-cps", default=17.0, show_default=True, help="caracteres por segundo tolerados (aviso si se supera)")
@click.option("--json", "as_json", is_flag=True)
def captions_export(words, out_path, max_chars, max_lines, max_dur, max_gap, max_cps, as_json):
    """words.json → .srt/.vtt con cortes en puntuación y pausas, ≤ 42 caracteres por línea, 1–7 s por cue. WORDS puede
    ser también un storyboard (p. ej. storyboard.es.json): exporta sus subtítulos por frase con los mismos tiempos."""
    from .captions import export
    out(export(words, out_path, max_chars=max_chars, max_lines=max_lines, max_dur=max_dur, max_gap=max_gap, max_cps=max_cps), as_json or True)


@captions.command("pages")
@click.argument("words", type=click.Path(exists=True))
@click.option("--max-words", default=4, show_default=True)
@click.option("--max-chars", default=22, show_default=True)
@click.option("--json", "as_json", is_flag=True)
def captions_pages(words, max_words, max_chars, as_json):
    """Muestra cómo quedarían las páginas de los presets `pages`/`karaoke` (para revisar antes de renderizar)."""
    from .captions import load_words, pages
    pgs = pages(load_words(words), max_words=max_words, max_chars=max_chars)
    if as_json:
        out(pgs, True)
    else:
        for p in pgs:
            click.echo(f"{p['start']:7.2f}–{p['end']:6.2f}  {p['text']}")


@main.group()
def storyboard():
    """Validar y construir a partir del storyboard JSON."""


@storyboard.command("validate")
@click.argument("path", type=click.Path(exists=True))
def sb_validate(path):
    from .build import validate
    errs = validate(json.loads(Path(path).read_text(encoding="utf-8-sig")))
    if errs:
        click.echo("Storyboard inválido:\n  - " + "\n  - ".join(errs)); raise SystemExit(1)
    click.echo("Storyboard válido.")
    from .brandcheck import check, load
    sb, rules, brand = load(Path(path))
    if not rules.empty():
        r = check(sb, rules, brand)
        click.echo(f"Nota de marca: {r['score']}/100 · {r['errors']} error(es), {len(r['issues']) - r['errors']} aviso(s)"
                   + ("  (detalle: frame28 storyboard brandcheck)" if r["issues"] else ""))


@storyboard.command("brandcheck")
@click.argument("path", type=click.Path(exists=True))
@click.option("--brief", type=click.Path(exists=True), default=None, help="brief de la Memoria y la campaña (por defecto busca brief.md junto al storyboard o más arriba)")
@click.option("--memoria", type=click.Path(exists=True), default=None, help="Memoria de marca en JSON (Context Pack v1), además del brief")
@click.option("--lang", default=None, help="idioma del storyboard para el glosario (por defecto meta.lang)")
@click.option("--min", "min_score", default=90, show_default=True, help="nota mínima: por debajo, sale con código 1")
@click.option("--json", "as_json", is_flag=True)
def sb_brandcheck(path, brief, memoria, lang, min_score, as_json):
    """Nota de marca del storyboard antes del render: claims legales, palabras prohibidas, ganchos prohibidos, glosario,
    largo de frase, lo que la campaña tiene que decir, contraste y zonas seguras. Sale con 1 si hay errores o la nota no llega."""
    from .brandcheck import check, load
    sb, rules, brand = load(Path(path), Path(brief) if brief else None, Path(memoria) if memoria else None)
    r = check(sb, rules, brand, lang)
    if as_json:
        click.echo(json.dumps(r, ensure_ascii=False, indent=2))
    else:
        src = ", ".join(rules.sources) or "sin reglas de marca (ni voice en la marca ni brief.md)"
        click.echo(f"Nota de marca: {r['score']}/100  ·  reglas: {src}" + (f"  ·  idioma {r['lang']}" if r["lang"] else ""))
        for i in r["issues"]:
            mark = "✗" if i["severity"] == "error" else "!"
            text = f" «{i['text'][:60]}»" if i["text"] else ""
            click.echo(f"  {mark} {i['rule']:<16} {i['id']} ({i['type']}){text}: {i['message']}\n      → {i['fix']}")
        if not r["issues"]:
            click.echo("  Sin fallos." if not rules.empty() else "  Nada que comprobar: pide la Memoria con frame28_memoria y guarda el brief en work/brief.md.")
    if r["errors"] or r["score"] < min_score:
        raise SystemExit(1)


@storyboard.command("schema")
def sb_schema():
    """Imprime la referencia del formato de storyboard (tipos de overlay y campos)."""
    ref = Path(__file__).with_name("STORYBOARD.md")
    click.echo(ref.read_text(encoding="utf-8"))


@main.group()
def brand():
    """Marcas: colores, fuentes y logos que usan los overlays (`"brand": "nombre"` en el storyboard)."""


@brand.command("list")
def brand_list():
    from .build import list_brands
    for name, path in sorted(list_brands().items()):
        click.echo(f"  {name:<16} {path}")


@brand.command("show")
@click.argument("name")
def brand_show(name):
    from .build import resolve_brand
    click.echo(Path(resolve_brand(name)).read_text(encoding="utf-8"))


@brand.command("from-site")
@click.argument("url")
@click.option("--name", required=True, help="nombre de la marca (fichero brands/<name>.json)")
@click.option("--out", "out_dir", default="brands", show_default=True, type=click.Path())
@click.option("--logo-url", default=None, help="URL del logo si el detector no acierta")
@click.option("--tagline", default=None)
@click.option("--json", "as_json", is_flag=True)
def brand_from_site(url, name, out_dir, logo_url, tagline, as_json):
    """Propone una marca a partir de la web del cliente: colores del CSS, fuente, logo con variantes para fondo oscuro y de acento."""
    from .brandsite import from_site
    r = from_site(url, name, out_dir, logo_url, tagline)
    if as_json:
        out(r, True); return
    click.echo(f"  marca: {r['brand']}  ·  confianza {r['confidence']}")
    click.echo(f"  acento {r['accent']} ({', '.join(r['accent_sources']) or 'provisional'})  tinta {r['ink']}  fuente {r['font'] or '(no detectada)'}"
               f"  secundarios {', '.join(r['secondary']) or '-'}")
    click.echo(f"  colores más usados (portada + {r['stylesheets']} hoja(s) CSS): " + ", ".join(f"{h} x{n}" for h, n in r["top_colors"]))
    lg = r["logo"]
    click.echo(f"  logo: {lg.get('url') or '(no encontrado)'}" + (f" [{lg['kind']}]" if lg.get("kind") else "")
               + (f"  → {', '.join(lg['files'].keys())}" if lg.get("files") else "") + (f"  colores {', '.join(r['logo_colors'])}" if r["logo_colors"] else ""))
    for w in r["warnings"]:
        click.echo(f"  ! {w}")
    click.echo(f"  sitio: {r['title']}\n  {r['description'][:160]}")
    click.echo("  Revisa y ajusta con un editor (tagline, endorsement, colores) y úsala con \"brand\": \"" + name + "\" en el storyboard.")


@brand.command("init")
@click.argument("name")
@click.option("--from", "base", default="think28", show_default=True, help="marca de la que partir")
@click.option("--user", "to_user", is_flag=True, help="guardar en ~/.config/frame28/brands en vez de ./brands")
@click.option("--accent", default=None, help="color de acento, p. ej. #0D4F87")
@click.option("--logo", type=click.Path(exists=True), default=None, help="SVG o PNG del isotipo/logo")
def brand_init(name, base, to_user, accent, logo):
    """Crea una marca nueva a partir de otra (por defecto think28) y te dice qué editar."""
    import shutil
    from .build import USER_BRANDS, resolve_brand
    src = resolve_brand(base)
    d = json.loads(src.read_text(encoding="utf-8-sig"))
    d.update({"name": name, "tagline": "", "site": "", "endorsement": "", "source": ""})
    d.pop("logos", None); d.pop("logo_rules", None); d.pop("voice", None)
    if accent:
        d["accent"] = accent
    target_dir = USER_BRANDS if to_user else Path.cwd() / "brands"
    (target_dir / name).mkdir(parents=True, exist_ok=True)
    if logo:
        dst = target_dir / name / ("isotipo" + Path(logo).suffix.lower()); shutil.copy2(logo, dst)
        d["logo_files"] = {"isotipo": f"{name}/{dst.name}", "on_dark": f"{name}/{dst.name}", "on_light": f"{name}/{dst.name}", "on_accent": f"{name}/{dst.name}"}
    else:
        d["logo_files"] = {}
    out = target_dir / f"{name}.json"
    out.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    click.echo(f"Marca creada: {out}")
    click.echo("Edita accent/ink/paper/grey, sans/mono, tagline y endorsement. Logos: pon SVG/PNG en "
               f"{target_dir / name}/ y referéncialos en logo_files (isotipo, on_dark, on_light, on_accent).")
    click.echo(f'Úsala en el storyboard con "brand": "{name}".')


@main.command()
@click.argument("storyboard", type=click.Path(exists=True))
@click.option("-o", "--out", "out_dir", required=True, type=click.Path())
@click.option("--graphics", "graphics_json", type=click.Path(exists=True), default=None, help="graphics.json de `frame28 graphics`: avisa de overlays que pisan gráficos del vídeo")
@click.option("--json", "as_json", is_flag=True)
def build(storyboard, out_dir, graphics_json, as_json):
    """storyboard.json → proyecto HyperFrames (index.html + assets copiados). Con --graphics avisa de overlays que pisan gráficos del vídeo."""
    from .build import build_project
    r = build_project(storyboard, out_dir)
    if graphics_json:
        from .graphics import collisions
        sb = json.loads(Path(storyboard).read_text(encoding="utf-8-sig"))
        gfx = json.loads(Path(graphics_json).read_text(encoding="utf-8-sig"))
        r["graphics_collisions"] = collisions(sb, gfx)
    out(r, as_json or True)


@main.command()
@click.argument("project", type=click.Path(exists=True))
@click.option("--json", "as_json", is_flag=True)
def check(project, as_json):
    """hyperframes check (lint + runtime + layout + contraste) filtrando el falso positivo del texto detrás."""
    from .render import check as _check
    r = _check(project)
    if as_json:
        out(r, True)
    else:
        click.echo(("✓ check pasó" if r["passed"] else "✗ check falló"))
        for e in r["errors"]:
            click.echo("  " + e)
        for w in r["contrast_warnings"]:
            click.echo("  aviso de contraste: " + w)
        if r["known_false_positives"]:
            click.echo(f"  ({len(r['known_false_positives'])} aviso(s) text_occluded ignorados: es el texto detrás del hablante)")
    if not r["passed"]:   # `frame28 check … && frame28 render` ya no deja pasar un render con errores
        raise SystemExit(1)


@main.command()
@click.argument("project", type=click.Path(exists=True))
@click.option("-o", "--out", "output", required=True, type=click.Path())
@click.option("--quality", default="high", show_default=True, type=click.Choice(["draft", "standard", "high"]))
@click.option("--crf", default=18, show_default=True)
@click.option("--fps", default=None, type=int)
@click.option("--no-sheet", is_flag=True)
@click.option("--workers", default=None, type=click.IntRange(1, 32), help="trabajadores de captura (por defecto los elige HyperFrames, ~6). Con 16 núcleos y 32 GB, 10 rinde más; 14 ya empeora")
@click.option("--gpu/--cpu", default=None, help="codificar el MP4 final con NVENC o con libx264; sin indicarlo, la GPU si la máquina la tiene (fichero ~50 %% mayor con NVENC)")
@click.option("--json", "as_json", is_flag=True)
def render(project, output, quality, crf, fps, no_sheet, workers, gpu, as_json):
    """Renderiza el proyecto a MP4 y genera una hoja de contacto para revisar."""
    from .render import render as _render
    r = _render(project, output, quality, crf, fps, not no_sheet, workers, gpu)
    out(r if as_json else {k: v for k, v in r.items() if k != "log_tail"}, as_json)
    if not r["ok"]:
        click.echo(r["log_tail"]); raise SystemExit(1)


def friendly_error(e: BaseException) -> tuple[str, int] | None:
    """Mensaje corto y código de salida para los errores habituales (F28-86); None si no es uno de ellos."""
    import subprocess
    import urllib.error
    if isinstance(e, TranscriptFormatError):
        return str(e), 2
    if isinstance(e, urllib.error.HTTPError):
        hint = (" La web bloquea las descargas automáticas (anti-bots): baja el fichero a mano o pasa --logo-url."
                if e.code in (401, 403, 429) else "")
        return f"la descarga de {e.url} respondió {e.code} {e.reason}.{hint}", 3
    if isinstance(e, urllib.error.URLError):
        return f"sin conexión o dirección inaccesible ({e.reason}). Comprueba la red y repite.", 3
    if isinstance(e, json.JSONDecodeError):
        return (f"JSON no válido (línea {e.lineno}, columna {e.colno}): {e.msg}. Ábrelo y corrígelo; "
                "si lo guardó PowerShell, guárdalo en UTF-8."), 2
    if isinstance(e, subprocess.TimeoutExpired):
        cmd = e.cmd[0] if isinstance(e.cmd, (list, tuple)) and e.cmd else e.cmd
        return f"{Path(str(cmd)).name} no terminó en {int(e.timeout)} s. Repite; si se repite, prueba con un clip más corto.", 4
    if isinstance(e, FileNotFoundError):
        return f"no se encontró {e.filename or e}. `frame28 doctor` dice qué falta y cómo instalarlo.", 2
    if isinstance(e, PermissionError):
        return f"sin permiso para {e.filename or 'un fichero'}: ¿está abierto en otro programa?", 2
    return None


def run():
    """Punto de entrada del ejecutable: los errores habituales salen como mensaje corto con pista, sin traza de Python
    (red, JSON roto, tiempo agotado, programa que falta). FRAME28_DEBUG=1 enseña la traza completa."""
    try:
        main()
    except KeyboardInterrupt:
        click.echo("Interrumpido.", err=True)
        sys.exit(130)
    except Exception as e:  # noqa: BLE001
        if os.environ.get("FRAME28_DEBUG"):
            raise
        known = friendly_error(e)
        if known:
            click.echo(f"Error: {known[0]}", err=True)
            sys.exit(known[1])
        click.echo(f"Error inesperado ({type(e).__name__}): {e}\n  Repite con FRAME28_DEBUG=1 para ver la traza y avísanos.", err=True)
        sys.exit(1)


if __name__ == "__main__":
    run()
