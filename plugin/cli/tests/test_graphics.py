"""graphics: cajas de los overlays (las mismas que pinta build), colisiones con el texto del vídeo, marca de agua y zonas
libres. Sin OCR ni vídeo (F28-95: era el único módulo sin pruebas)."""
from __future__ import annotations

import json
import re

import pytest

from frame28 import build
from frame28 import graphics as G
from conftest import write_json


def _cta_in_html(sb: dict, tmp_path, name: str) -> tuple[int, int]:
    r = build.build_project(write_json(tmp_path / f"{name}.json", sb), tmp_path / name)
    html = open(r["index"], encoding="utf-8").read()
    cid = next(o["id"] for o in sb["overlays"] if o["type"] == "cta")
    tag = re.search(rf'<div id="{cid}"[^>]*>', html).group(0)
    m = re.search(r"left:(\d+)px; top:(\d+)px", tag)
    return int(m.group(1)), int(m.group(2))


@pytest.mark.parametrize("variant", ["caption_style", "sin subtítulos", "subtítulos sin estilo"])
def test_cta_box_is_where_build_puts_it(tmp_path, tutorial_short, variant):
    # F28-95: overlay_bbox suponía subtítulos con su propia cuenta; en vertical sin subtítulos build ponía el CTA en
    # y=1376 y los avisos de plataforma y de marca de agua lo buscaban en y=938
    sb = json.loads(json.dumps(tutorial_short)); sb["brand"] = "think28"
    if variant != "caption_style":
        sb.pop("caption_style", None)
    if variant == "subtítulos sin estilo":
        sb["captions"] = [{"start": 0.5, "end": 2.0, "text": "hola"}]
    W, H = sb["canvas"]["width"], sb["canvas"]["height"]
    cta = next(o for o in sb["overlays"] if o["type"] == "cta")
    cta.pop("x", None); cta.pop("y", None)
    x, y = _cta_in_html(sb, tmp_path, "p")
    bb = G.overlay_bbox(cta, W, H, sb)
    assert bb[:2] == [x, y]
    if variant == "sin subtítulos":
        assert y == H - 80 - build.CTA_H - 24


def test_full_screen_overlays_have_no_box():
    assert G.overlay_bbox({"type": "card", "id": "c"}, 1920, 1080) is None
    assert G.overlay_bbox({"type": "box", "id": "b", "x": 100, "y": 200, "text": "abcd"}, 1920, 1080) == [100, 200, 260, 280]


def _sb(*overlays, **kw):
    return {"canvas": {"width": 1920, "height": 1080}, "overlays": list(overlays), **kw}


def test_collisions_report_text_and_cards_under_overlays():
    box = {"id": "b1", "type": "box", "x": 100, "y": 900, "text": "Paso uno", "start": 1.0, "end": 4.0}
    card = {"id": "k1", "type": "card", "start": 10.0, "end": 12.0}
    gfx = {"events": [{"kind": "editor_text", "text": "SPEED 1", "bbox": [120, 890, 400, 960], "start": 2.0, "end": 6.0},
                      {"kind": "scene_text", "text": "etiqueta", "bbox": [120, 890, 400, 960], "start": 1.0, "end": 2.5},
                      {"kind": "editor_text", "text": "lejos", "bbox": [1500, 50, 1800, 120], "start": 1.0, "end": 4.0}],
           "cards": [{"color": "#f0a020", "start": 11.0, "end": 13.0}], "burned_subtitles": True}
    out = G.collisions(_sb(box, card, captions=[{"start": 0, "end": 1, "text": "x"}]), gfx)
    assert any(x.startswith("b1 (box) pisa el texto 'SPEED 1'") and "2.0–4.0" in x for x in out)
    assert not any("etiqueta" in x for x in out)                  # texto de escena de menos de 2 s: no cuenta
    assert not any("lejos" in x for x in out)
    assert any(x.startswith("k1 (card) tapa la tarjeta del propio vídeo") for x in out)
    assert any("subtítulos quemados" in x for x in out)


def test_watermark_pass_joins_the_pieces_the_ocr_loses():
    ev = [{"kind": "editor_text", "text": "MARCA", "bbox": [1700, 40, 1880, 90], "start": 0.0, "end": 30.0, "frames": 30},
          {"kind": "editor_text", "text": "MAR", "bbox": [1702, 41, 1878, 91], "start": 35.0, "end": 60.0, "frames": 25},
          {"kind": "editor_text", "text": "Paso 1", "bbox": [100, 900, 400, 960], "start": 5.0, "end": 8.0, "frames": 3}]
    out = G.watermark_pass(ev, dur=60.0, cw=1920)
    summary = [e for e in out if e.get("summary")]
    assert len(summary) == 1 and summary[0]["text"] == "MARCA" and summary[0]["start"] == 0.0 and summary[0]["end"] == 60.0
    assert [e["kind"] for e in out[:3]] == ["watermark", "watermark", "editor_text"]


def test_merge_split_rejoins_a_watermark_cut_in_pieces():
    ev = [{"text": "MARCA", "bbox": [1700, 40, 1880, 90], "start": 0.0, "end": 4.0, "frames": 4, "boxes": [1], "angles": [0]},
          {"text": "MARCA:", "bbox": [1701, 40, 1881, 90], "start": 6.0, "end": 9.0, "frames": 3, "boxes": [2], "angles": [0]},
          {"text": "MARCA", "bbox": [1700, 40, 1880, 90], "start": 20.0, "end": 22.0, "frames": 2, "boxes": [3], "angles": [0]}]
    out = G._merge_split(ev)
    assert [(e["start"], e["end"], e["text"]) for e in out] == [(0.0, 9.0, "MARCA:"), (20.0, 22.0, "MARCA")]


def test_zone_report_counts_busy_time_and_free_windows():
    res = {"canvas": [1920, 1080], "duration": 10.0, "sample_fps": 1.0, "cards": [],
           "events": [{"bbox": [50, 50, 300, 120], "start": 0.0, "end": 5.0}]}
    rep = G.zone_report(res)
    assert rep["top-left"] == {"busy_pct": 50, "free_windows": [[5.0, 10.0]]}
    assert rep["center"] == {"busy_pct": 0, "free_windows": [[0.0, 10.0]]}
