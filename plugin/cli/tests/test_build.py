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


# ── F28-84: lo que no es texto también acaba en el HTML (atributos, estilos, JS, rutas) ─────────────────────────────────
PAYLOAD = '"><script>alert(1)</script>'


def test_validate_rejects_hostile_values():
    sb = _sb(overlays=[
        {"type": "box", "id": "a b", "x": 0, "y": 0, "text": "t", "start": 1, "end": 2},
        {"type": "box", "id": PAYLOAD, "x": 0, "y": 0, "text": "t", "start": 1, "end": 2},
        {"type": "kinetic", "id": "k", "x": 0, "y": 0, "text": "t", "start": 1, "end": 2, "color": "red;}</style><script>"},
        {"type": "box", "id": "b", "x": 0, "y": 0, "text": "t", "start": 1, "end": 2, "bg": 'x" onload="alert(1)'},
        {"type": "image", "id": "i1", "x": 0, "y": 0, "w": 10, "start": 1, "end": 2, "src": "<script>.png"},
        {"type": "image", "id": "i2", "x": 0, "y": 0, "w": 10, "start": 1, "end": 2, "src": "C:/Windows/win.ini"},
        {"type": "image", "id": "i3", "x": 0, "y": 0, "w": 10, "start": 1, "end": 2, "src": "https://evil.example/x.png"},
        {"type": "image", "id": "i4", "x": 0, "y": 0, "w": 10, "start": 1, "end": 2, "src": "assets/../../../x.png"},
        {"type": "draw", "id": "d1", "x": 0, "y": 0, "w": 10, "start": 1, "end": 2, "paths": ['M0 0"/><script>']},
        {"type": "draw", "id": "d2", "x": 0, "y": 0, "w": 10, "start": 1, "end": 2, "viewBox": '0 0 24 24" onload="x'},
        {"type": "box", "id": "c", "x": "0); alert(1); (", "y": 0, "text": "t", "start": 1, "end": 2},
    ], meta={"lang": 'es"><script>'}, brand={"accent": "#fff", "sans": "x;}</style><script>", "font_link": 'https://f.example/" onload="x'})
    errs = "\n".join(build.validate(sb))
    for frag in ("overlays[0].id", "overlays[1].id", "overlays[2].color", "overlays[3].bg", "overlays[4].src", "overlays[5].src",
                 "overlays[6].src", "overlays[7].src", "overlays[8].paths", "overlays[9].viewBox", "overlays[10].x", "meta.lang",
                 "marca.sans", "marca.font_link"):
        assert frag in errs, frag


def test_safe_rel_path():
    for ok in ("clip.mp4", "assets/x.png", "../clip.mp4", "../../work/alpha_4.3.webm", "./a/b.webm"):
        assert build.safe_rel_path(ok), ok
    for bad in ("", "/etc/passwd", r"\\srv\x","C:/x.png", "file:x", "https://a/b", "a/../../b", "..", "../", 'a".png', "a<b>.png"):
        assert not build.safe_rel_path(bad), bad


def _draw_sb(tmp_path, svg: str) -> Path:
    (tmp_path / "icon.svg").write_text(svg, encoding="utf-8")
    return write_json(tmp_path / "sb.json", _sb(overlays=[
        {"type": "draw", "id": "d", "x": 10, "y": 10, "w": 100, "start": 1, "end": 2, "src": "icon.svg"}]))


def test_build_project_rejects_svg_with_scripts(tmp_path):
    sbp = _draw_sb(tmp_path, '<svg viewBox="0 0 24 24"><path d="M0 0L24 24" onmouseover="alert(1)"/></svg>')
    with pytest.raises(SystemExit, match="draw.src"):
        build.build_project(sbp, tmp_path / "p")
    sbp = _draw_sb(tmp_path, '<svg viewBox="0 0 24 24"><path d="M0 0L24 24"/></svg>')
    html = (Path(build.build_project(sbp, tmp_path / "p2")["index"])).read_text(encoding="utf-8")
    assert 'd="M0 0L24 24"' in html


def test_build_project_never_writes_outside_the_project(tmp_path):
    (tmp_path / "clip.mp4").write_bytes(b"x")
    work = tmp_path / "work"; work.mkdir()
    sb = _sb(); sb["source"]["video"] = "../clip.mp4"
    res = build.build_project(write_json(work / "sb.json", sb), work / "project")
    assert not (work / "clip.mp4").exists()                       # antes se copiaba a work/, fuera del proyecto
    assert any("fuera del proyecto" in w for w in res["warnings"])


def test_build_rejects_brand_with_css_injection(tmp_path):
    sb = _sb(brand={"accent": "red;}</style><script>alert(1)</script>"})
    with pytest.raises(SystemExit, match="marca.accent"):
        build.build_project(write_json(tmp_path / "sb.json", sb), tmp_path / "p")


def test_cover_validates_brand_and_escapes_font_link(tmp_path):
    from frame28 import cover
    img = tmp_path / "f.png"; img.write_bytes(b"x")
    with pytest.raises(SystemExit, match="marca.accent"):
        cover.build_cover(img, tmp_path / "c1", "Hola", brand={"accent": "red;}</style><script>"})
    with pytest.raises(SystemExit, match="fondo"):
        cover.build_cover(img, tmp_path / "c2", "Hola", bg='accent"><script>')
    idx = cover.build_cover(img, tmp_path / "c3", PAYLOAD, brand={"font_link": "https://fonts.example/css?family=A&display=swap"})
    html = idx.read_text(encoding="utf-8")
    assert "family=A&amp;display=swap" in html and "<script>alert" not in html


def test_on_accent_picks_ink_or_white_by_contrast():
    # F28-128: con un acento oscuro (azul marino) la tinta casi negra no se lee; con uno claro, sí
    assert build.on_accent_color("#24258E", "#111111") == "#FFFFFF"
    assert build.on_accent_color("#F5C500", "#0A0A0A") == "#0A0A0A"
    assert build.on_accent_color("#EA77A1", "#111111") == "#111111"
    assert build.on_accent_color("rgb(0,0,0)", "#111111") == "#111111"     # no hex: se queda la tinta
    assert round(build.contrast_ratio("#000000", "#FFFFFF"), 1) == 21.0


def test_build_uses_on_accent_for_text_on_accent(tmp_path):
    hook = {"type": "hook", "id": "h", "start": 0, "end": 2, "lines": ["Hola"], "bg": "accent"}
    build.build_project(write_json(tmp_path / "a.json", _sb(brand={"accent": "#24258E", "ink": "#111111"}, overlays=[hook])), tmp_path / "pa")
    html = (tmp_path / "pa" / "index.html").read_text(encoding="utf-8")
    assert "--on-accent: #FFFFFF" in html and ".hook.accent .hl { background: var(--accent); color: var(--on-accent); }" in html
    build.build_project(write_json(tmp_path / "b.json", _sb(brand={"accent": "#F5C500", "ink": "#0A0A0A"}, overlays=[hook])), tmp_path / "pb")
    assert "--on-accent: #0A0A0A" in (tmp_path / "pb" / "index.html").read_text(encoding="utf-8")
    # la marca puede imponerlo, y se valida como color
    build.build_project(write_json(tmp_path / "c.json", _sb(brand={"accent": "#24258E", "on_accent": "#FFEEDD"}, overlays=[hook])), tmp_path / "pc")
    assert "--on-accent: #FFEEDD" in (tmp_path / "pc" / "index.html").read_text(encoding="utf-8")
    with pytest.raises(SystemExit, match="marca.on_accent"):
        build.build_project(write_json(tmp_path / "d.json", _sb(brand={"on_accent": "red;}</style>"})), tmp_path / "pd")


def test_cover_uses_on_accent(tmp_path):
    from frame28 import cover
    img = tmp_path / "f.png"; img.write_bytes(b"x")
    html = cover.build_cover(img, tmp_path / "c", "Hola", brand={"accent": "#24258E", "ink": "#111111"}).read_text(encoding="utf-8")
    assert "--on-accent:#FFFFFF" in html and "color:var(--on-accent)" in html
