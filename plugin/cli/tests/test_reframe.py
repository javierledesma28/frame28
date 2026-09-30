"""reframe: camino de cámara (zona muerta, límites) y mapeo de coordenadas del apaisado al vertical. Sin vídeo."""
from __future__ import annotations

import pytest

from frame28 import reframe as R

SUBJ = {"width": 1920, "height": 1080, "fps": 30, "sample_fps": 10.0}
CROP_W = 608  # 1080 * 1080 / 1920 → ventana 9:16 de altura completa


def _subject(xs, dt=0.1):
    return {**SUBJ, "t": [round(i * dt, 3) for i in range(len(xs))], "x": xs}


def test_camera_stays_inside_deadzone_and_frame():
    static = _subject([960 + (5 if i % 2 else -5) for i in range(40)])
    cams = [c for _, c in R.camera_path(static, CROP_W)]
    assert max(cams) - min(cams) < 1.0  # el temblor de ±5 px queda dentro de la zona muerta: la cámara no se mueve
    edge = _subject([50] * 40)
    assert all(c == pytest.approx(CROP_W / 2, abs=0.5) for _, c in R.camera_path(edge, CROP_W))


def test_camera_follows_a_jump_smoothly_and_within_speed():
    xs = [960] * 10 + [1700] * 60
    path = R.camera_path(_subject(xs), CROP_W, smooth=0.3)
    cams = [c for _, c in path]
    assert cams[0] == pytest.approx(960, abs=1)
    assert cams[-1] > 1500  # llega cerca del sujeto (zona muerta de 10 %)
    assert cams[-1] <= 1920 - CROP_W / 2 + 0.5
    steps = [b - a for a, b in zip(cams, cams[1:])]
    assert all(s >= -0.5 for s in steps), "no retrocede"
    assert max(steps) <= 0.5 * CROP_W * 0.1 + 1  # velocidad máxima: 0,5 anchos de ventana por segundo


CROP_RES = {"mode": "crop", "source": [1920, 1080], "out": [1080, 1920], "crop": [CROP_W, 1080],
            "path": [[0.0, 960.0], [5.0, 960.0], [6.0, 1300.0]]}
BLUR_RES = {"mode": "blur", "source": [1920, 1080], "out": [1080, 1920], "foreground": {"x": 0, "y": 656, "w": 1080, "h": 608}}


def test_map_point_crop_center_and_offscreen():
    assert R.map_point(CROP_RES, 960, 540, 1.0) == [540, 960]
    assert R.point_visible(CROP_RES, 960, 540, 1.0)
    assert not R.point_visible(CROP_RES, 100, 540, 1.0)
    # la cámara se ha movido a 1300 en t=6: el centro del original queda a la izquierda
    x, _ = R.map_point(CROP_RES, 960, 540, 6.0)
    assert x < 540 and R.point_visible(CROP_RES, 1300, 540, 6.0)


def test_map_point_blur_keeps_everything():
    assert R.map_point(BLUR_RES, 960, 540, 0.0) == [540, 960]
    assert R.map_point(BLUR_RES, 0, 0, 0.0) == [0, 656]
    assert R.point_visible(BLUR_RES, 0, 0, 0.0)


def test_map_canvas_point_scales_from_storyboard_canvas():
    small = {**BLUR_RES, "source": [1280, 720]}
    assert R.map_canvas_point(small, 960, 540, 0.0, (1920, 1080)) == [540, 960]  # centro del lienzo → centro del vertical


def test_map_gestures_marks_hidden_pointers_and_keeps_boxes_inside():
    g = {"canvas": [1920, 1080], "face_box": [860, 200, 1060, 480],
         "events": [{"kind": "point", "start": 1.0, "end": 1.5, "tip": [1000, 600], "hand": "right", "direction": "right"}],
         "pointer_suggestions": [
             {"id": "p1", "type": "pointer", "start": 0.95, "end": 2.1, "at": 1.0, "dot": [1000, 600], "box": [1090, 390], "text": "aquí", "confidence": "high"},
             {"id": "p2", "type": "pointer", "start": 3.0, "end": 4.0, "at": 3.0, "dot": [120, 600], "box": [60, 390], "text": "allí", "confidence": "low"}]}
    r = R.map_gestures(CROP_RES, g)
    assert r["canvas"] == [1080, 1920] and r["hidden"] == 1 and len(r["warnings"]) == 1
    p1, p2 = r["pointer_suggestions"]
    assert p1["visible"] and not p2["visible"]
    assert p1["dot"] == [round((1000 - 656) * 1080 / CROP_W), round(600 * 1920 / 1080)]
    for p in (p1, p2):
        assert 0 <= p["box"][0] <= 1080 - 320 and 0 <= p["box"][1] <= 1920 - 90
        assert 0 <= p["dot"][0] <= 1080 and 0 <= p["dot"][1] <= 1920
    assert r["events"][0]["tip"] == p1["dot"]
    assert r["face_box"] and r["face_box"][0] < r["face_box"][2]
    assert R.map_gestures(BLUR_RES, g)["hidden"] == 0
