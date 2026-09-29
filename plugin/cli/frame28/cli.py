"""CLI de Frame28. Todas las órdenes devuelven JSON con --json para que un agente las consuma sin parsear texto."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import click

from . import __version__

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


@click.group()
@click.version_option(__version__, prog_name="frame28")
def main():
    """Frame28: de un clip hablando a cámara a un video con overlays sincronizados."""


@main.command()
@click.option("--json", "as_json", is_flag=True)
def doctor(as_json):
    """Comprueba ffmpeg, Node, dependencias Python y modelos."""
    from .doctor import doctor as _doctor
    rows = _doctor()
    if as_json:
        out(rows, True); return
    for r in rows:
        mark = "✓" if r["ok"] else "✗"
        click.echo(f"  {mark} {r['name']:<20} {r['detail']}" + ("" if r["ok"] else f"\n      → {r['fix']}"))
    missing = [r for r in rows if not r["ok"] and r["name"] not in ("gpu (onnxruntime)", "modelo RVM")]
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
@click.option("--width", default=None, type=int, help="Reescalar a este ancho (p. ej. 1920)")
@click.option("--json", "as_json", is_flag=True)
def prep(video, out_dir, fps, width, as_json):
    """Copia de trabajo: clip.mp4 a 30 fps sin audio + voice.wav normalizada + audio16k.wav para ASR."""
    from .media import prep as _prep
    out(_prep(video, out_dir, fps, width), as_json or True)


@main.command()
@click.argument("audio", type=click.Path(exists=True))
@click.option("-o", "--out", "out_dir", required=True, type=click.Path())
@click.option("--lang", default="es", show_default=True)
@click.option("--model", default="medium", show_default=True, help="tiny/base/small/medium/large-v3")
@click.option("--device", default="cpu", show_default=True)
@click.option("--compute", default="int8", show_default=True)
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
@click.option("--json", "as_json", is_flag=True)
def speaker(video, samples, as_json):
    """Dónde está el hablante (bbox en coordenadas 1080p) y qué lado queda libre para overlays."""
    from .matte import speaker_layout
    out(speaker_layout(video, samples), as_json or True)


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


@main.group()
def storyboard():
    """Validar y construir a partir del storyboard JSON."""


@storyboard.command("validate")
@click.argument("path", type=click.Path(exists=True))
def sb_validate(path):
    from .build import validate
    errs = validate(json.loads(Path(path).read_text(encoding="utf-8")))
    if errs:
        click.echo("Storyboard inválido:\n  - " + "\n  - ".join(errs)); raise SystemExit(1)
    click.echo("Storyboard válido.")


@storyboard.command("schema")
def sb_schema():
    """Imprime la referencia del formato de storyboard (tipos de overlay y campos)."""
    ref = Path(__file__).with_name("STORYBOARD.md")
    click.echo(ref.read_text(encoding="utf-8"))


@main.command()
@click.argument("storyboard", type=click.Path(exists=True))
@click.option("-o", "--out", "out_dir", required=True, type=click.Path())
@click.option("--json", "as_json", is_flag=True)
def build(storyboard, out_dir, as_json):
    """storyboard.json → proyecto HyperFrames (index.html + assets copiados)."""
    from .build import build_project
    out(build_project(storyboard, out_dir), as_json or True)


@main.command()
@click.argument("project", type=click.Path(exists=True))
@click.option("--json", "as_json", is_flag=True)
def check(project, as_json):
    """hyperframes check (lint + runtime + layout + contraste) filtrando el falso positivo del texto detrás."""
    from .render import check as _check
    r = _check(project)
    if as_json:
        out(r, True); return
    click.echo(("✓ check pasó" if r["passed"] else "✗ check falló"))
    for e in r["errors"]:
        click.echo("  " + e)
    if r["known_false_positives"]:
        click.echo(f"  ({len(r['known_false_positives'])} aviso(s) text_occluded ignorados: es el texto detrás del hablante)")


@main.command()
@click.argument("project", type=click.Path(exists=True))
@click.option("-o", "--out", "output", required=True, type=click.Path())
@click.option("--quality", default="high", show_default=True, type=click.Choice(["draft", "standard", "high"]))
@click.option("--crf", default=18, show_default=True)
@click.option("--fps", default=None, type=int)
@click.option("--no-sheet", is_flag=True)
@click.option("--json", "as_json", is_flag=True)
def render(project, output, quality, crf, fps, no_sheet, as_json):
    """Renderiza el proyecto a MP4 y genera una hoja de contacto para revisar."""
    from .render import render as _render
    r = _render(project, output, quality, crf, fps, not no_sheet)
    out(r if as_json else {k: v for k, v in r.items() if k != "log_tail"}, as_json)
    if not r["ok"]:
        click.echo(r["log_tail"]); raise SystemExit(1)


if __name__ == "__main__":
    main()
