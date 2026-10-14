"""F28-298: marca de agua de la prueba gratis. Con `"watermark"` en la raíz del storyboard, build la pinta en todo el vídeo
(de 0 a la duración total, por encima de todo, fuera de la interfaz del móvil); sin el campo, el HTML no cambia. También en
portadas y en los shorts de `clips scaffold/batch`."""
from __future__ import annotations

import json
import re

import pytest

from frame28 import build, clips, cover
from conftest import words_from, write_json


def _sb(**kw):
    return {"version": 1, "source": {"video": "clip.mp4", "duration": 10.0}, "duration": 12.0,
            "captions": [{"start": 0.5, "end": 2.0, "text": "Hola"}], "overlays": [
                {"type": "box", "id": "caja", "x": 120, "y": 140, "text": "Algo", "start": 1, "end": 3},
                {"type": "brand_card", "id": "cierre", "start": 10.0, "end": 12.0}], **kw}


def _html(tmp_path, sb, name="p"):
    r = build.build_project(write_json(tmp_path / f"{name}.json", sb), tmp_path / name, copy_assets=False)
    return (tmp_path / name / "index.html").read_text(encoding="utf-8"), r


def _wm(html):
    m = re.search(r'<div id="wm"[^>]*>[^<]*</div>', html)
    return m.group(0) if m else None


def test_watermark_en_todo_el_rango_y_por_encima_de_todo(tmp_path):
    html, _ = _html(tmp_path, _sb(watermark="Frame28 Studio"))
    wm = _wm(html)
    assert wm and ">Frame28 Studio</div>" in wm
    # de 0 a la duración total (12 s, más que el clip de 10: también sobre la tarjeta de cierre en negro)
    assert 'data-start="0"' in wm and 'data-duration="12.0"' in wm
    # sin animación que la esconda: ninguna orden de la timeline la toca
    assert "#wm" not in html.split("gsap.timeline", 1)[-1]
    z = [int(v) for v in re.findall(r"z-index:\s*(\d+)", html.split("<body>", 1)[-1])]
    assert re.search(r"z-index:20", wm) and max(z) == 20 and z.count(20) == 1
    assert ".wm {" in html and "rgba(10,10,10,.58)" in html      # píldora oscura: se lee sobre blanco y sobre negro


def test_sin_watermark_el_html_no_cambia(tmp_path):
    con, _ = _html(tmp_path, _sb(watermark="Frame28 Studio"), "con")
    sin, _ = _html(tmp_path, _sb(), "sin")
    assert _wm(sin) is None and ".wm {" not in sin and 'id="wm"' not in sin
    quitado = con.replace(_wm(con), "").replace(build.WATERMARK_CSS, "")
    assert re.sub(r"\s+", "", quitado) == re.sub(r"\s+", "", sin)
    assert _wm(_html(tmp_path, _sb(watermark=None), "nulo")[0]) is None                       # null = sin marca de agua


def test_objeto_con_posicion_y_opacidad(tmp_path):
    wm = _wm(_html(tmp_path, _sb(watermark={"text": "Frame28 Studio", "position": "tl", "opacity": 0.6}))[0])
    assert "left:" in wm and "top:" in wm and "opacity:0.6" in wm and "right:" not in wm


def test_texto_escapado(tmp_path):
    wm = _wm(_html(tmp_path, _sb(watermark='<script>alert(1)</script>'))[0])
    assert "<script>" not in wm and "&lt;script&gt;" in wm


@pytest.mark.parametrize("value, msg", [
    ("", "falta el texto"), ("   ", "falta el texto"), (42, "tiene que ser un texto"),
    ("x" * 41, "40 caracteres"), ("Frame28\nStudio", "una sola línea"),
    ({"text": "Frame28 Studio", "position": "centro"}, "position"),
    ({"text": "Frame28 Studio", "opacity": 0.1}, "opacity"), ({"text": "Frame28 Studio", "opacity": "1"}, "opacity"),
    ({"text": "Frame28 Studio", "size": 40}, "claves desconocidas"), ({"position": "br"}, "falta el texto"),
])
def test_validate_rechaza_valores_malos(value, msg):
    errs = build.validate(_sb(watermark=value))
    assert any(msg in e for e in errs), errs


def test_validate_acepta_texto_y_objeto():
    assert build.validate(_sb(watermark="Frame28 Studio")) == []
    assert build.validate(_sb(watermark={"text": "Frame28 Studio", "position": "bl", "opacity": 1})) == []


@pytest.mark.parametrize("platform", ["tiktok", "reels", "shorts", None])
@pytest.mark.parametrize("position", build.WATERMARK_POSITIONS)
def test_vertical_respeta_las_zonas_de_la_interfaz(platform, position):
    W, H = 1080, 1920
    x0, y0, x1, y1 = build.watermark_layout(W, H, position, platform, "Frame28 Studio")["box"]
    zonas = [[W - 150, int(0.35 * H), W, int(0.88 * H)], [0, int(0.84 * H), W, H], [0, 0, W, int(0.08 * H)]]   # platform_warnings
    for zx0, zy0, zx1, zy1 in zonas:
        assert not (x0 < zx1 and x1 > zx0 and y0 < zy1 and y1 > zy0), (position, (x0, y0, x1, y1))
    assert 0 <= x0 < x1 <= W and 0 <= y0 < y1 <= H


def test_short_del_scaffold_sin_avisos_con_la_posicion_por_defecto(tmp_path, grabado_short):
    """El vertical por defecto (br, encima de la columna de iconos) no pisa el gancho, el CTA ni los subtítulos de un short real."""
    sb = {**grabado_short, "brand": "think28", "watermark": "Frame28 Studio"}
    _, r = _html(tmp_path, sb)
    assert not [w for w in r["warnings"] if "marca de agua" in w], r["warnings"]


def test_avisa_de_lo_que_queda_debajo(tmp_path):
    sb = _sb(canvas={"width": 1080, "height": 1920, "fps": 30}, platform="tiktok",
             caption_style={"preset": "pages", "words": "words.json", "bottom": 345},
             watermark={"text": "Frame28 Studio", "position": "tr"},
             overlays=[{"type": "hook", "id": "gancho", "start": 0.2, "end": 3.0, "lines": ["UNA LÍNEA BASTANTE LARGA"]}])
    write_json(tmp_path / "words.json", words_from("hola mundo", start=0.5))
    _, r = _html(tmp_path, sb)
    assert any("gancho (hook) queda debajo" in w for w in r["warnings"]), r["warnings"]
    sb["watermark"] = {"text": "Frame28 Studio", "position": "bl"}
    _, r = _html(tmp_path, sb, "p2")
    assert any("franja de subtítulos" in w for w in r["warnings"]), r["warnings"]


def test_apaisado_por_debajo_de_los_subtitulos():
    lay = build.watermark_layout(1920, 1080, "br", None, "Frame28 Studio")
    assert lay["box"][1] >= 1080 - 56            # la franja de subtítulos por frase empieza a 56 px del borde
    assert not build.watermark_warnings(_sb(), lay, "br")


def test_portada_con_y_sin_marca_de_agua(tmp_path):
    img = tmp_path / "f.png"; img.write_bytes(b"x")
    sin = cover.build_cover(img, tmp_path / "c0", "Hola").read_text(encoding="utf-8")
    assert 'id="wm"' not in sin and ".wm {" not in sin
    con = cover.build_cover(img, tmp_path / "c1", "Hola", watermark="Frame28 Studio").read_text(encoding="utf-8")
    assert ">Frame28 Studio</div>" in con and "left:" in _wm(con)                 # apaisada: abajo a la izquierda, lejos del logo
    sq = cover.build_cover(img, tmp_path / "c2", "Hola", size=(1080, 1080), watermark="Frame28 Studio").read_text(encoding="utf-8")
    assert "right:" in _wm(sq) and "bottom:" in _wm(sq)                          # cuadrada: el logo va arriba a la derecha
    with pytest.raises(SystemExit, match="Marca de agua"):
        cover.build_cover(img, tmp_path / "c3", "Hola", watermark={"text": "x", "position": "medio"})


def test_scaffold_y_batch_la_ponen_en_cada_short(tmp_path, grabado_clips):
    clip = grabado_clips["clips"][0]
    cdir = tmp_path / "clips"; d = cdir / clip["id"]; d.mkdir(parents=True)
    (d / "clip.mp4").write_bytes(b"")
    write_json(d / "words.json", words_from("look at that", start=1.0))
    clips.scaffold(clip, d, brand="think28", watermark="Frame28 Studio")
    sb = json.loads((d / "storyboard.json").read_text(encoding="utf-8"))
    assert sb["watermark"] == "Frame28 Studio" and build.validate(sb) == []
    clips.scaffold(clip, d, brand="think28", name="sin.json")
    assert "watermark" not in json.loads((d / "sin.json").read_text(encoding="utf-8"))     # sin la opción, como antes
    plan = write_json(tmp_path / "clips.json", {"clips": [clip]})
    # primero sin marca de agua (afinados a mano), luego --keep con marca de agua: se añade a los que no la llevan
    clips.batch(plan, None, cdir, tmp_path / "out", [0], brand="think28", render=False)
    sp = d / "storyboard-hook0.json"
    assert "watermark" not in json.loads(sp.read_text(encoding="utf-8"))
    kept = clips.batch(plan, None, cdir, tmp_path / "out", [0], brand="think28", render=False, keep=True, watermark="Frame28 Studio")
    assert kept["variants"][0]["kept"] and kept["variants"][0]["watermark_added"]
    assert json.loads(sp.read_text(encoding="utf-8"))["watermark"] == "Frame28 Studio"
    assert ">Frame28 Studio</div>" in (d / "project-hook0" / "index.html").read_text(encoding="utf-8")
    again = clips.batch(plan, None, cdir, tmp_path / "out", [0], brand="think28", render=False, keep=True, watermark="Frame28 Studio")
    assert not again["variants"][0].get("watermark_added")                       # ya la lleva: no se reescribe
    fresh = clips.batch(plan, None, cdir, tmp_path / "out", [0], brand="think28", render=False, watermark="Frame28 Studio")
    assert fresh["ok"] == 1 and json.loads(sp.read_text(encoding="utf-8"))["watermark"] == "Frame28 Studio"


def test_cli_opciones(tmp_path):
    from click.testing import CliRunner
    from frame28.cli import main
    for cmd in (["cover", "--help"], ["clips", "scaffold", "--help"], ["clips", "batch", "--help"]):
        r = CliRunner().invoke(main, cmd)
        assert r.exit_code == 0 and "--watermark" in r.output, cmd
    r = CliRunner().invoke(main, ["storyboard", "schema"])
    assert '"watermark": "Frame28 Studio"' in r.output and "20 marca de agua" in r.output
