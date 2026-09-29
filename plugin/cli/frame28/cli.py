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


@main.command()
@click.argument("video", type=click.Path(exists=True))
@click.option("--words", type=click.Path(exists=True), default=None, help="words.json para cruzar gestos con palabras")
@click.option("--sample-fps", default=10.0, show_default=True)
@click.option("--annotate", type=click.Path(), default=None, help="PNG con un fotograma por gesto para revisar")
@click.option("-o", "--out", "out_json", type=click.Path(), default=None, help="guardar el resultado en JSON")
@click.option("--json", "as_json", is_flag=True)
def gestures(video, words, sample_fps, annotate, out_json, as_json):
    """Detecta cuándo el hablante señala (MediaPipe Pose) y propone los overlays `pointer` ya colocados."""
    from .pose import analyze
    r = analyze(video, words, sample_fps, annotate)
    if out_json:
        Path(out_json).write_text(json.dumps(r, indent=1, ensure_ascii=False), encoding="utf-8")
        r["saved"] = out_json
    out(r, as_json or True)


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
@click.option("--json", "as_json", is_flag=True)
def cut_apply(video, cuts, audio, words, captions, storyboard, out_dir, as_json):
    """Aplica cuts.json: clip.mp4 y voice.wav cortados (fundidos de 30 ms) + words/captions/storyboard remapeados."""
    from .cut import apply as _apply
    out(_apply(video, audio, cuts, out_dir, words, captions, storyboard), as_json or True)


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
    d = json.loads(src.read_text(encoding="utf-8"))
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
