"""build: validación del storyboard (los casos versionados de poc/ y errores típicos), avisos de plataforma y build sin render."""
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


def test_narrow_class_on_vertical_canvas(tmp_path, tutorial_short):
    sb = dict(tutorial_short); sb["brand"] = "think28"
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


def test_hook_line_that_will_wrap_is_reported(tmp_path, tutorial_short):
    # día 6: una línea de 21 caracteres a 96 px se partía en un lienzo de 1080 y dejaba una palabra huérfana
    sb = json.loads(json.dumps(tutorial_short)); sb["brand"] = "think28"
    hook = next(o for o in sb["overlays"] if o["type"] == "hook")
    hook.pop("text", None); hook.pop("size", None)
    hook["lines"] = ["Light the wick.", "Every jar fills the room."]
    r = build.build_project(write_json(tmp_path / "storyboard.json", sb), tmp_path / "p")
    w = [x for x in r["warnings"] if x.startswith("hook ")]
    assert len(w) == 1 and "Every jar fills the room." in w[0] and "size <=" in w[0]
    hook["size"] = 74
    r = build.build_project(write_json(tmp_path / "storyboard.json", sb), tmp_path / "p2")
    assert not [x for x in r["warnings"] if x.startswith("hook ")]


def test_highlighted_titles_get_taller_lines_for_accented_capitals(tmp_path, tutorial_short):
    # día 6: en una portada con una mayúscula acentuada en la segunda línea, la caja de la primera le tapaba la tilde
    assert build.highlight_line_height(["AROMÁTICAS", "en una tarde"], 1.12) == 1.12       # en la primera línea no molesta
    assert build.highlight_line_height(["Velas", "AROMÁTICAS"], 1.12) == 1.34
    assert build.highlight_line_height(["Jetzt", "ÜBEN"], 1.15) == 1.37
    assert build.highlight_line_height(["Velas", "aromáticas"], 1.15) == 1.15               # las minúsculas caben
    sb = json.loads(json.dumps(tutorial_short)); sb["brand"] = "think28"
    hook = next(o for o in sb["overlays"] if o["type"] == "hook")
    hook.pop("text", None); hook["lines"] = ["Velas", "AROMÁTICAS"]
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


def test_bar_chart_in_portrait_is_legible(tmp_path):
    # F28-165: en 1080x1920 las barras salían en una franja estrecha con letra de 20-46 px
    chart = {"type": "chart", "id": "ch", "kind": "bar", "bg": "black", "start": 0, "end": 4, "title": "Tiempo", "unit": " min", "decimals": 0,
             "series": [{"label": "A mano", "value": 12}, {"label": "Con la máquina", "value": 3}]}
    sb = _sb(canvas={"width": 1080, "height": 1920, "fps": 30}, overlays=[chart])
    build.build_project(write_json(tmp_path / "v.json", sb), tmp_path / "pv", copy_assets=False)
    html = (tmp_path / "pv" / "index.html").read_text(encoding="utf-8")
    assert 'class="clip card chart portrait black"' in html
    assert ".chart.portrait .ch-title { font-size: 84px;" in html and ".chart.portrait .lbl { width: 100%;" in html
    widths = [int(w) for w in re.findall(r'class="fill" id="ch-f\d" style="width:(\d+)px"', html)]
    assert max(widths) > 700                                   # la barra más larga usa el ancho del lienzo
    track = int(re.search(r'class="track" style="width:(\d+)px"', html).group(1))
    assert track <= 1080 - 128
    # apaisado y panel, sin cambios
    build.build_project(write_json(tmp_path / "h.json", _sb(overlays=[chart])), tmp_path / "ph", copy_assets=False)
    assert "portrait" not in (tmp_path / "ph" / "index.html").read_text(encoding="utf-8").split("<body")[1]
    panel = {**chart, "panel": {"x": 40, "y": 300, "w": 1000}}
    panel.pop("bg")
    build.build_project(write_json(tmp_path / "p.json", _sb(canvas={"width": 1080, "height": 1920, "fps": 30}, overlays=[panel])), tmp_path / "pp", copy_assets=False)
    assert "chart portrait" not in (tmp_path / "pp" / "index.html").read_text(encoding="utf-8")


def _video(path, bottom_value, w=108, h=192, n=10):
    import cv2
    import numpy as np
    vw = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), 10, (w, h))
    for _ in range(n):
        f = np.full((h, w, 3), 40, np.uint8)
        f[h * 2 // 3:] = bottom_value                          # el tercio de abajo, donde van los subtítulos
        vw.write(f)
    vw.release()
    return path


def test_word_captions_get_a_backdrop_when_the_bottom_band_is_light(tmp_path):
    # F28-166: subtítulos blancos sobre la franja casi blanca de un vertical con blur no se leían
    from conftest import words_from
    write_json(tmp_path / "words.json", words_from("hola mundo cruel adios", start=0.5))
    def build_with(video_bottom, backdrop=None, name="p"):
        _video(tmp_path / "clip.mp4", video_bottom)
        cs = {"preset": "pages", "words": "words.json"}
        if backdrop:
            cs["backdrop"] = backdrop
        sb = _sb(canvas={"width": 1080, "height": 1920, "fps": 30}, caption_style=cs)
        r = build.build_project(write_json(tmp_path / f"{name}.json", sb), tmp_path / name, copy_assets=False)
        return (tmp_path / name / "index.html").read_text(encoding="utf-8"), r["warnings"]
    html, warns = build_with(245, name="claro")
    assert 'class="clip pages mode-pages upper bd-box"' in html and any("franja de abajo es clara" in w for w in warns)
    html, _ = build_with(30, name="oscuro")
    assert "bd-box" not in html.split("<body")[1]
    html, _ = build_with(245, "stroke", name="contorno")
    assert "bd-stroke" in html.split("<body")[1] and "bd-box" not in html.split("<body")[1]
    html, _ = build_with(245, "none", name="nada")
    assert "bd-" not in html.split("<body")[1]


# ── behind v2: frase palabra a palabra anclada a la voz, con salida por desenfoque (F28-339) ──────────────────────────
JAVIER_WORDS = [{"text": "vamos", "start": 2.86, "end": 3.16}, {"text": "a", "start": 3.16, "end": 3.40},
                {"text": "ver", "start": 3.40, "end": 3.90}, {"text": "los", "start": 3.90, "end": 4.26},
                {"text": "distintos", "start": 4.26, "end": 4.58}, {"text": "componentes", "start": 4.58, "end": 5.08}]


def _bh2(**kw):
    o = {"type": "behind", "id": "bh2", "start": 2.7, "end": 7.5, "text": "DISTINTOS COMPONENTES", "words_at": "auto",
         "kicker": {"text": "Vamos a ver", "at": "word:vamos"}, "matte": "a.webm", "matte_start": 2.7, "matte_end": 7.6}
    o.update(kw)
    return o


def _build_bh(tmp_path, name="p", brand=None, words=JAVIER_WORDS, **kw):
    write_json(tmp_path / "words.json", words)
    sb = _sb(overlays=[_bh2(**kw)], words="words.json", **({"brand": brand} if brand else {}))
    r = build.build_project(write_json(tmp_path / f"{name}.json", sb), tmp_path / name, copy_assets=False)
    return (tmp_path / name / "index.html").read_text(encoding="utf-8"), r


def test_behind_v2_each_word_enters_on_its_spoken_word_and_leaves_with_blur(tmp_path):
    html, r = _build_bh(tmp_path)
    tl = html.split("gsap.timeline", 1)[1]
    # cada palabra en su instante de words.json, 0,04 s antes; el antetítulo anclado a «vamos»
    assert re.search(r'tl\.fromTo\("#bh2-w0", \{ opacity: 0 \}, \{ opacity: 1, duration: 0\.2, ease: "power1\.out" \}, 4\.22\)', tl)
    assert re.search(r'tl\.fromTo\("#bh2-w1", .*\}, 4\.54\)', tl)
    assert re.search(r'tl\.fromTo\("#bh2-k", \{ opacity: 0 \}, \{ opacity: 1, duration: 0\.5,.*\}, 2\.82\)', tl)
    # salida lenta por desenfoque: termina en end; el antetítulo empieza a irse 0,3 s antes
    assert 'tl.fromTo("#bh2-b .bh-l", { filter: "blur(0px)", opacity: 1 }, { filter: "blur(28px)", opacity: 0, duration: 1.2, ' \
           'ease: "sine.inOut", immediateRender: false }, 6.3);' in tl
    assert re.search(r'tl\.fromTo\("#bh2-k", \{ filter: "blur\(0px\)".*immediateRender: false \}, 6\.0\);', tl)
    # capas: texto en la 2, el hablante con alfa en la 3 durante su tramo; ajuste al ancho en el navegador
    assert 'id="bh2" class="clip"' in html and 'style="z-index:2;"' in html
    assert '<video id="bh2-fg" class="clip cover" data-start="2.7" data-duration="4.9"' in html and "z-index:3" in html
    assert 'data-fit="0.85"' in html and "function f28fit()" in html and "document.fonts.ready.then(f28fit)" in html
    assert not re.search(r"\.(to|from|fromTo)\([^)]*\{[^}]*\b(left|top|width)\s*:", tl), "HyperFrames rechaza tweens de left/top/width"
    assert r["warnings"] == [] or all("asset" in w for w in r["warnings"])


def test_behind_v2_takes_motion_from_the_brand(tmp_path):
    html, _ = _build_bh(tmp_path, brand={"accent": "#F5C500", "motion": {"enter_ms": 120, "exit_ms": 900, "exit_blur_px": 40,
                                                                          "ease_out": "expo.inOut", "exit_stagger_ms": 200}})
    assert 'duration: 0.12, ease: "power1.out" }, 4.22)' in html
    assert '{ filter: "blur(40px)", opacity: 0, duration: 0.9, ease: "expo.inOut", immediateRender: false }, 6.6);' in html
    assert 'immediateRender: false }, 6.4);' in html                                       # antetítulo 0,2 s antes
    with pytest.raises(SystemExit, match="ease_in: curva de GSAP no válida"):
        _build_bh(tmp_path, name="mala", brand={"motion": {"ease_in": "x\"); alert(1); (\""}})


def test_behind_v2_variants_fade_rise_chars_and_no_kicker(tmp_path):
    html, _ = _build_bh(tmp_path, name="fade", out="fade", enter="rise", kicker=None, words_at=[4.3, 4.6], color="ink", fit=0.6)
    tl = html.split("gsap.timeline", 1)[1]
    assert "blur(" not in tl and 'tl.fromTo("#bh2-b .bh-l", { opacity: 1 }, { opacity: 0, duration: 1.2' in tl
    assert 'tl.set("#bh2-w0", { opacity: 1 }, 4.3); tl.fromTo("#bh2-w0 .wi", { yPercent: 110 }' in tl
    assert "bh2-k" not in html and "color:var(--ink)" in html and 'data-fit="0.6"' in html
    html, _ = _build_bh(tmp_path, name="chars", enter="chars", size=300)
    assert "SplitText.create(\"#bh2-w0 .wi\"" in html and "SplitText.min.js" in html
    assert "font-size:300px" in html and "data-fit" not in html                              # tamaño fijo: sin ajuste


def test_behind_v2_lines_and_kicker_auto(tmp_path):
    html, _ = _build_bh(tmp_path, name="lineas", text="DISTINTOS|COMPONENTES", kicker="los")
    assert html.count('class="bh-l"') == 2
    assert 'tl.fromTo("#bh2-k", { opacity: 0 }, { opacity: 1, duration: 0.5, ease: "power1.out" }, 3.72);' in html


def test_behind_v2_warns_short_hold_uncovered_matte_and_density(tmp_path):
    _, r = _build_bh(tmp_path, name="corto", end=6.4, matte_start=3.5, matte_end=6.0)
    w = "\n".join(r["warnings"])
    assert "se queda quieta 0.46 s" in w and "alarga end hasta 7.44" in w
    assert "la máscara del hablante (3.5–6.0 s) no cubre lo que se ve (2.82–6.4 s" in w
    write_json(tmp_path / "words.json", JAVIER_WORDS)
    sb = _sb(overlays=[_bh2(), _bh2(id="otro", start=8.0, end=9.9, words_at=[8.2, 8.5], kicker=None, matte_start=8.0, matte_end=9.9)],
             words="words.json")
    r = build.build_project(write_json(tmp_path / "dos.json", sb), tmp_path / "dos", copy_assets=False)
    assert any("behind bh2 y otro: 5.3 s entre uno y otro" in x and "~20 s" in x for x in r["warnings"])


def test_behind_v2_unknown_word_stops_the_build_with_what_is_heard(tmp_path):
    with pytest.raises(SystemExit, match="words_at auto no encuentra «3»"):
        _build_bh(tmp_path, name="cifra", text="3 COMPONENTES")
    with pytest.raises(SystemExit, match="«componente» no se dice"):
        _build_bh(tmp_path, name="palabra", kicker={"text": "x", "at": "word:componente"})


def test_behind_v2_validation():
    errs = "\n".join(build.validate(_sb(overlays=[_bh2(words_at=[4.2], x=560, fit=1.5, kicker={"size": 20}, out_dur=9, enter="zoom",
                                                         text="UNA DOS TRES CUATRO CINCO")])))
    for frag in ("5 palabras", "words_at tiene 1 tiempos y el texto 5", "x es una fracción", "fit es la fracción",
                 "kicker es un texto", "out_dur 9 no cabe", "enter: valor no válido 'zoom'"):
        assert frag in errs, frag
    # sin resolver todavía (validate a pelo, como la prueba de los storyboards versionados): las anclas no son error
    assert build.validate(_sb(overlays=[_bh2()])) == []
    assert "tiene que ser un número (o un ancla" in "\n".join(build.validate(_sb(overlays=[_bh2(start="pronto")])))


def test_behind_v2_poc_resolves_against_the_real_transcript(tmp_path):
    # poc/clip-javier/storyboard-behind2.json con su words.json de verdad: «vamos» 2,86, «distintos» 4,26, «componentes» 4,58
    src = Path(__file__).resolve().parents[3] / "poc" / "clip-javier" / "storyboard-behind2.json"
    out = tmp_path / "p"
    r = build.build_project(src, out, copy_assets=False)
    tl = (out / "index.html").read_text(encoding="utf-8").split("gsap.timeline", 1)[1]
    assert re.search(r'tl\.fromTo\("#bh2-k", \{ opacity: 0 \}.*\}, 2\.82\);', tl)
    assert re.search(r'tl\.fromTo\("#bh2-w0", .*\}, 4\.22\);', tl) and re.search(r'tl\.fromTo\("#bh2-w1", .*\}, 4\.54\);', tl)
    assert "blur(28px)" in tl and "}, 6.3);" in tl
    assert not [w for w in r["warnings"] if "behind" in w]


def test_behind_warns_when_the_brand_avoids_it(tmp_path):
    # la Memoria o la campaña dicen «No uses: texto detrás del hablante» (motion.avoid, F28-347)
    _, r = _build_bh(tmp_path, brand={"accent": "#F5C500", "motion": {"style": "sober", "avoid": ["behind"]}})
    assert any("la marca pide no usar texto detrás del hablante" in w for w in r["warnings"])


def test_behind_missing_matte_says_how_to_make_it(tmp_path):
    # sin la máscara el texto queda delante de la persona: el aviso da la orden con el tramo de la escena
    write_json(tmp_path / "words.json", JAVIER_WORDS)
    sb = _sb(overlays=[_bh2()], words="words.json")
    r = build.build_project(write_json(tmp_path / "sb.json", sb), tmp_path / "p")
    w = next(w for w in r["warnings"] if "a.webm" in w)
    assert "máscara del behind bh2" in w and "frame28 matte <clip> --start 2.7 --end 7.6 -o a.webm" in w


def test_legacy_behind_is_untouched(tmp_path, javier_storyboard):
    bh = next(o for o in javier_storyboard["overlays"] if o["type"] == "behind")
    assert not build.is_behind_v2(bh)
    r = build.build_project(write_json(tmp_path / "sb.json", javier_storyboard), tmp_path / "p", copy_assets=False)
    html = (tmp_path / "p" / "index.html").read_text(encoding="utf-8")
    assert f'tl.fromTo("#{bh["id"]}-w", {{ opacity: 0, scale: 1.15 }}' in html or "SplitText" in html
    assert "f28fit" not in html and "bhv2" not in html.split("<body")[1]
    assert not any("behind" in w for w in r["warnings"])


def test_brand_display_tokens_are_validated():
    assert any("display_tracking" in e for e in build.brand_errors({"display_tracking": "1em; } body { color: red"}))
    assert any("display_weight" in e for e in build.brand_errors({"display_weight": "bold"}))
    assert build.brand_errors({"display_weight": 800, "display_tracking": "-0.035em", "motion": {"standard_ms": 240}}) == []
