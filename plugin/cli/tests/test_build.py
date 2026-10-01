"""build: validación del storyboard (los 11 casos reales versionados y errores típicos), avisos de plataforma y build sin render."""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from frame28 import build
from conftest import STORYBOARDS, write_json


@pytest.mark.parametrize("path", STORYBOARDS, ids=[str(p.relative_to(p.parents[2])) for p in STORYBOARDS])
def test_versioned_storyboards_are_valid(path: Path):
    sb = json.loads(path.read_text(encoding="utf-8"))
    assert build.validate(sb) == []


def test_at_least_ten_storyboards_in_repo():
    assert len(STORYBOARDS) >= 10


def _sb(**overlays_kw):
    return {"version": 1, "source": {"video": "clip.mp4", "duration": 10.0}, "duration": 12.0, "overlays": [], **overlays_kw}


def test_validate_reports_each_problem():
    sb = _sb(overlays=[
        {"type": "box", "id": "a", "x": 0, "y": 0, "text": "t", "start": 1, "end": 2},
        {"type": "box", "id": "a", "x": 0, "y": 0, "text": "t", "start": 3, "end": 2},
        {"type": "nada", "id": "b", "start": 0, "end": 13},
        {"type": "hook", "id": "h", "start": 0, "end": 1},
        {"type": "chart", "id": "c", "kind": "bar", "start": 0, "end": 1},
        {"type": "chart", "id": "d", "kind": "counter", "start": 0, "end": 1},
        {"type": "kinetic", "id": "k", "start": 0, "end": 1},
    ], captions=[{"start": 0, "text": "sin end"}], caption_style={"preset": "raro"}, canvas={"width": 300, "height": 300}, platform="x")
    errs = "\n".join(build.validate(sb))
    for frag in ("id duplicado 'a'", "end debe ser > start", "tipo desconocido 'nada'", "supera la duración 12.0", "(hook): falta 'text' o 'lines'",
                 "(chart bar): falta 'series'", "(chart counter): falta 'value'", "(kinetic): falta 'x'", "captions[0]: falta 'end'",
                 "caption_style.preset desconocido", "canvas demasiado pequeño", "platform debe ser"):
        assert frag in errs, frag
    assert build.validate({"overlays": []}) == ["version debe ser 1", "source.video es obligatorio", "source.duration es obligatorio"]


def test_validate_allows_overlays_up_to_duration_with_tolerance():
    sb = _sb(overlays=[{"type": "brand_card", "id": "end", "start": 10, "end": 12.005}])
    assert build.validate(sb) == []


def test_platform_warnings_vertical_zones():
    sb = {"version": 1, "canvas": {"width": 1080, "height": 1920}, "platform": "tiktok", "source": {"video": "v", "duration": 5},
          "overlays": [{"type": "box", "id": "right", "x": 900, "y": 1000, "text": "hola", "start": 0, "end": 1},
                       {"type": "box", "id": "safe", "x": 100, "y": 500, "text": "hola", "start": 0, "end": 1}],
          "caption_style": {"preset": "pages", "bottom": 100}}
    w = build.platform_warnings(sb)
    assert any(x.startswith("right (box)") and "columna derecha" in x for x in w)
    assert not any(x.startswith("safe ") for x in w)
    assert any("subtítulos a 100 px" in x and ">= 307" in x for x in w)
    sb["caption_style"]["bottom"] = 345
    assert not any("subtítulos" in x for x in build.platform_warnings(sb))
    sb["platform"] = "youtube"
    assert build.platform_warnings(sb) == []
    sb["platform"] = "reels"; sb["canvas"] = {"width": 1920, "height": 1080}
    assert build.platform_warnings(sb) == []  # apaisado: no hay zonas de móvil


def test_build_project_generates_hyperframes_composition(tmp_path, javier_storyboard, repo):
    sbp = write_json(tmp_path / "storyboard.json", javier_storyboard)
    r = build.build_project(sbp, tmp_path / "project")
    html = (tmp_path / "project" / "index.html").read_text(encoding="utf-8")
    assert r["overlays"] == len(javier_storyboard["overlays"]) and r["canvas"] == [1920, 1080]
    for o in javier_storyboard["overlays"]:
        assert f'id="{o["id"]}"' in html, o["id"]
    assert f"gsap@{build.GSAP_VERSION}" in html
    assert "SplitText" in html and "DrawSVG" in html  # el storyboard usa chars y draw: se cargan los plugins
    assert (tmp_path / "project" / "package.json").exists() and (tmp_path / "project" / "hyperframes.json").exists()
    assert json.loads((tmp_path / "project" / "package.json").read_text())["scripts"]["render"].endswith(f"hyperframes@{build.HYPERFRAMES_VERSION} render")
    # medios ausentes en el tmp: avisa, no revienta
    assert any("asset no encontrado" in w for w in r["warnings"])
    # el <video> y el <audio> llevan id (si no, HyperFrames los congela)
    assert '<video id="bg"' in html and '<audio id="voice"' in html
    # los tweens de posición van por x/y/scale/opacity o clipPath, nunca left/top (gsap_non_transform_motion en el check);
    # la línea del pointer crece con width y el check la acepta (regresión verificada en poc/clip-javier)
    tl = html.split("gsap.timeline", 1)[-1]
    assert not re.search(r"\.(to|from|fromTo)\([^)]*\{[^}]*\b(left|top)\s*:", tl), "HyperFrames rechaza tweens de left/top"


def test_build_project_rejects_invalid_storyboard(tmp_path):
    sbp = write_json(tmp_path / "bad.json", {"version": 2})
    with pytest.raises(SystemExit, match="Storyboard inválido"):
        build.build_project(sbp, tmp_path / "p")


def test_narrow_class_on_vertical_canvas(tmp_path, grabado_short):
    sb = dict(grabado_short); sb["brand"] = "think28"
    sbp = write_json(tmp_path / "storyboard.json", sb)
    build.build_project(sbp, tmp_path / "p")
    html = (tmp_path / "p" / "index.html").read_text(encoding="utf-8")
    assert "narrow" in html


def test_brand_resolution(tmp_path):
    p = build.resolve_brand("think28")
    assert p.name == "think28.json" and p.exists()
    (tmp_path / "brands").mkdir()
    custom = write_json(tmp_path / "brands" / "acme.json", {"name": "acme"})
    assert build.resolve_brand("acme", near=tmp_path) == custom
    assert build.resolve_brand(str(custom)) == custom
    with pytest.raises(SystemExit):
        build.resolve_brand("no-existe")


def test_brand_by_name_is_found_from_a_short_folder(tmp_path):
    # día 6: la marca vive en work/brands/ y el short en work/clips/<id>/project-hook0/
    (tmp_path / "work" / "brands").mkdir(parents=True)
    custom = write_json(tmp_path / "work" / "brands" / "acme.json", {"name": "acme"})
    project = tmp_path / "work" / "clips" / "s1" / "project-hook0"
    project.mkdir(parents=True)
    assert build.resolve_brand("acme", near=project) == custom


def test_hook_line_that_will_wrap_is_reported(tmp_path, grabado_short):
    # día 6: una línea de 21 caracteres a 96 px se partía en un lienzo de 1080 y dejaba una palabra huérfana
    sb = json.loads(json.dumps(grabado_short)); sb["brand"] = "think28"
    hook = next(o for o in sb["overlays"] if o["type"] == "hook")
    hook.pop("text", None); hook.pop("size", None)
    hook["lines"] = ["Turn the light on.", "Every single line glows."]
    r = build.build_project(write_json(tmp_path / "storyboard.json", sb), tmp_path / "p")
    w = [x for x in r["warnings"] if x.startswith("hook ")]
    assert len(w) == 1 and "Every single line glows." in w[0] and "size <=" in w[0]
    hook["size"] = 74
    r = build.build_project(write_json(tmp_path / "storyboard.json", sb), tmp_path / "p2")
    assert not [x for x in r["warnings"] if x.startswith("hook ")]


def test_highlighted_titles_get_taller_lines_for_accented_capitals(tmp_path, grabado_short):
    # día 6: en la portada "Graba / ACRÍLICO" la caja de la primera línea tapaba la tilde de la Í
    assert build.highlight_line_height(["ACRÍLICO", "fácil de grabar"], 1.12) == 1.12      # en la primera línea no molesta
    assert build.highlight_line_height(["Graba", "ACRÍLICO"], 1.12) == 1.34
    assert build.highlight_line_height(["Jetzt", "ÜBEN"], 1.15) == 1.37
    assert build.highlight_line_height(["Graba", "acrílico"], 1.15) == 1.15                 # las minúsculas caben
    sb = json.loads(json.dumps(grabado_short)); sb["brand"] = "think28"
    hook = next(o for o in sb["overlays"] if o["type"] == "hook")
    hook.pop("text", None); hook["lines"] = ["Graba", "ACRÍLICO"]
    build.build_project(write_json(tmp_path / "storyboard.json", sb), tmp_path / "p")
    assert "line-height:1.37;" in (tmp_path / "p" / "index.html").read_text(encoding="utf-8")
