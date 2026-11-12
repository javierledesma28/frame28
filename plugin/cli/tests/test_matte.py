"""F28-92: matte sale a los fps del tramo de origen (no a 30 fijos) y no deja la carpeta temporal si algo falla.
F28-331: fotogramas crudos a ffmpeg, sin PNG intermedios. F28-340: tramos de máscara de un storyboard, su caché y su color."""
from __future__ import annotations

import json
import subprocess
import sys

import numpy as np
import pytest

from frame28 import matte as M


def _probe_out(monkeypatch, stdout: str) -> None:
    monkeypatch.setattr(M, "ffprobe", lambda: "ffprobe")
    monkeypatch.setattr(M, "run", lambda cmd, **k: subprocess.CompletedProcess(cmd, 0, stdout, ""))


@pytest.mark.parametrize("stdout, rate", [
    ("avg_frame_rate=25/1\nr_frame_rate=25/1\n", "25/1"),
    ("avg_frame_rate=30000/1001\nr_frame_rate=30000/1001\n", "30000/1001"),
    ("avg_frame_rate=2997/50\nr_frame_rate=90000/1\n", "2997/50"),      # móvil de frecuencia variable: la media, no la nominal
    ("avg_frame_rate=0/0\nr_frame_rate=60/1\n", "60/1"),
    ("", "30/1"),
])
def test_frame_rate_reads_the_source(monkeypatch, stdout, rate):
    _probe_out(monkeypatch, stdout)
    assert M.frame_rate("x.mp4") == rate


def _fake_pipeline(monkeypatch, tmp_path, fail: bool = False):
    work = tmp_path / "frame28_matte_x"
    monkeypatch.setattr(M.tempfile, "mkdtemp", lambda prefix="": (work.mkdir(), str(work))[1])
    monkeypatch.setattr(M, "cut", lambda video, s, e, out: (out.write_bytes(b"seg"), out)[1])
    monkeypatch.setattr(M, "frame_rate", lambda video: "25/1")
    monkeypatch.setattr(M, "color_tags", lambda video: seen.setdefault("color_of", video) and ["-colorspace", "bt709"])
    seen = {}

    class Sink:
        def __init__(self, out, rate, keep_png=None, color=()):
            seen["rate"] = rate; seen["keep_png"] = keep_png; seen["color"] = color

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return None

    def frames(src, sink, ratio, gpu=None):
        (work / "seg.part").write_bytes(b"x" * 1024)
        if fail:
            raise RuntimeError("onnxruntime se quedó sin memoria")
        seen["src"] = src
        return {"frames": 50, "fps": 12.5}

    monkeypatch.setattr(M, "matte_frames", frames)
    monkeypatch.setattr(M, "WebmSink", Sink)
    return work, seen


def test_matte_uses_the_rate_of_the_cut_segment(monkeypatch, tmp_path):
    work, seen = _fake_pipeline(monkeypatch, tmp_path)
    stats = M.matte("orig.mp4", tmp_path / "a.webm", start=1.0, end=3.0)
    assert seen["rate"] == "25/1" and stats["frame_rate"] == "25/1"
    assert seen["src"].name == "seg.mp4"                       # los fps se leen del tramo, no se suponen
    assert stats["fps"] == 12.5                                  # «fps» sigue siendo la velocidad de RVM, como antes
    assert seen["color_of"] == "orig.mp4" and seen["color"] == ["-colorspace", "bt709"]    # el color, del clip y no del tramo recortado
    assert not work.exists()


def test_matte_fps_option_still_forces_the_rate(monkeypatch, tmp_path):
    _, seen = _fake_pipeline(monkeypatch, tmp_path)
    assert M.matte("orig.mp4", tmp_path / "a.webm", fps=60)["frame_rate"] == "60" and seen["rate"] == 60


def test_matte_removes_the_temp_folder_when_it_fails(monkeypatch, tmp_path):
    work, _ = _fake_pipeline(monkeypatch, tmp_path, fail=True)
    with pytest.raises(RuntimeError):
        M.matte("orig.mp4", tmp_path / "a.webm", start=1.0, end=3.0)
    assert not work.exists()                                     # antes quedaban los PNG RGBA (gigas) en %TEMP%


# ---------- F28-331: fotogramas por tubería ----------
def _fake_ffmpeg(tmp_path, code: int = 0):
    """Un «ffmpeg» de verdad para Popen: copia la entrada estándar a un fichero y sale con `code`."""
    script = tmp_path / "ffmpeg_falso.py"
    script.write_text(f"import shutil, sys\nshutil.copyfileobj(sys.stdin.buffer, open(r'{tmp_path / 'raw.bin'}', 'wb'))\n"
                      f"sys.stderr.write('fallo de libvpx')\nsys.exit({code})\n", encoding="utf-8")
    return script


def test_webm_args_are_fast_vp9_with_alpha_from_raw_frames(monkeypatch):
    monkeypatch.setattr(M, "ffmpeg", lambda: "ffmpeg")      # la CI no tiene ffmpeg: la orden se arma sin buscarlo
    a = M.webm_args("a.webm", 1920, 1080, "25/1")
    assert a[a.index("-f") + 1] == "rawvideo" and a[a.index("-pix_fmt") + 1] == "yuva420p" and a[a.index("-s") + 1] == "1920x1080"
    assert a[a.index("-framerate") + 1] == "25/1" and a[a.index("-i") + 1] == "-"
    assert "yuva420p" in a and a[a.index("-deadline") + 1] == "realtime" and a[a.index("-row-mt") + 1] == "1"


@pytest.mark.parametrize("stdout, tags", [
    ("color_space=bt709\ncolor_primaries=bt709\ncolor_transfer=bt709\n", ["-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709"]),
    ("color_space=bt470bg\ncolor_primaries=unknown\ncolor_transfer=unknown\n", ["-colorspace", "bt470bg"]),
    ("color_space=unknown\ncolor_primaries=unknown\ncolor_transfer=unknown\n", []),      # sin etiquetar, los dos se leen igual
    ("color_space=gbr\ncolor_primaries=bt709\ncolor_transfer=unknown\n", ["-color_primaries", "bt709"]),   # los planos de la máscara son YUV
    ("", []),
])
def test_the_mask_takes_the_color_tags_of_the_clip(monkeypatch, stdout, tags):
    # sin ellas, el compositor lee el VP9 con BT.601 y en un clip bt709 la piel saltaba 4-7 niveles al entrar la máscara (F28-340)
    _probe_out(monkeypatch, stdout)
    assert M.color_tags("x.mp4") == tags


def test_webm_args_put_the_color_tags_on_the_input(monkeypatch):
    # después de -i, ffmpeg 9 no etiqueta sino que convierte los planos y el salto de color seguía ahí con la etiqueta correcta
    monkeypatch.setattr(M, "ffmpeg", lambda: "ffmpeg")
    a = M.webm_args("a.webm", 1920, 1080, "25/1", color=["-colorspace", "bt709", "-color_trc", "bt709"])
    assert a.index("-f") < a.index("-colorspace") < a.index("-color_trc") < a.index("-i") and a[a.index("-colorspace") + 1] == "bt709"
    assert a.count("-colorspace") == 1


def test_sink_sends_yuva_planes_and_only_writes_pngs_when_asked(monkeypatch, tmp_path):
    script = _fake_ffmpeg(tmp_path)
    seen = {}
    monkeypatch.setattr(M, "webm_args", lambda *a, **k: seen.update(a=a) or [sys.executable, str(script)])
    frame = np.full((4, 6, 4), 200, dtype=np.uint8)
    frame[:, :, 3] = 77
    with M.WebmSink(tmp_path / "a.webm", "30/1", color=["-colorspace", "bt709"]) as sink:
        sink(frame); sink(frame)
    raw = (tmp_path / "raw.bin").read_bytes()
    y, c, a = 4 * 6, 2 * 3, 4 * 6                                   # luma, cada croma a media resolución, alfa entero
    assert len(raw) == 2 * (y + 2 * c + a) and raw[y + 2 * c:y + 2 * c + a] == bytes([77]) * a
    assert seen["a"][1:4] == (6, 4, "30/1") and seen["a"][-1] == ["-colorspace", "bt709"]
    assert not list(tmp_path.glob("*.png"))
    with M.WebmSink(tmp_path / "b.webm", "30/1", keep_png=tmp_path / "png") as sink:
        sink(frame)
    assert (tmp_path / "png" / "f_0000.png").exists()


def test_sink_trims_odd_sides(monkeypatch, tmp_path):
    script = _fake_ffmpeg(tmp_path)
    monkeypatch.setattr(M, "webm_args", lambda *a, **k: [sys.executable, str(script)])
    with M.WebmSink(tmp_path / "a.webm", "30/1") as sink:
        sink(np.zeros((5, 7, 4), dtype=np.uint8))
    assert len((tmp_path / "raw.bin").read_bytes()) == 4 * 6 + 2 * 2 * 3 + 4 * 6


def test_sink_turns_an_ffmpeg_failure_into_its_message(monkeypatch, tmp_path):
    script = _fake_ffmpeg(tmp_path, code=3)
    monkeypatch.setattr(M, "webm_args", lambda *a, **k: [sys.executable, str(script)])
    with pytest.raises(SystemExit, match="fallo de libvpx"):
        with M.WebmSink(tmp_path / "a.webm", "30/1") as sink:
            sink(np.zeros((4, 4, 4), dtype=np.uint8))


def test_sink_without_frames_is_an_error_not_an_empty_mask(tmp_path):
    with pytest.raises(SystemExit, match="ningún fotograma"):
        with M.WebmSink(tmp_path / "a.webm", "30/1"):
            pass


# ---------- F28-340: tramos de máscara ----------
def _sb(*overlays, duration=30.0, fps=30, **root):
    return {"version": 1, "source": {"video": "clip.mp4", "duration": duration}, "canvas": {"width": 1920, "height": 1080, "fps": fps},
            "overlays": list(overlays), **root}


def _el(i, start, end, **k):
    return {"type": "image", "id": i, "start": start, "end": end, "src": "a.png", "x": 0, "y": 0, "w": 400, "layer": "behind", **k}


def test_two_overlapping_elements_make_one_segment():
    segs = M.matte_segments(_sb(_el("a", 2.0, 5.0), _el("b", 4.0, 7.0)))
    assert segs == [{"start": 1.8, "end": 7.2, "ids": ["a", "b"]}]


def test_elements_more_than_a_second_apart_make_two_segments():
    segs = M.matte_segments(_sb(_el("a", 2.0, 4.0), _el("b", 6.0, 8.0)))
    assert [(x["start"], x["end"]) for x in segs] == [(1.8, 4.2), (5.8, 8.2)]


def test_a_gap_under_a_second_stays_in_one_segment():
    segs = M.matte_segments(_sb(_el("a", 2.0, 4.0), _el("b", 5.2, 8.0)))       # hueco de 0,8 s contando los márgenes
    assert len(segs) == 1 and segs[0]["ids"] == ["a", "b"]


def test_segments_cover_every_window_with_margin_and_stay_in_the_clip():
    segs = M.matte_segments(_sb(_el("a", 0.05, 1.0), _el("z", 9.0, 9.9), duration=10.0))
    assert segs[0]["start"] == 0.0                                              # sin tiempos negativos
    assert segs[-1]["end"] == 10.0                                              # ni más allá del clip
    one = M.matte_segments(_sb(_el("a", 2.03, 3.97)))[0]
    assert one["start"] <= 2.03 - M.SEGMENT_MARGIN_S and one["end"] >= 3.97 + M.SEGMENT_MARGIN_S


def test_nothing_to_cut_after_the_clip():
    assert M.matte_segments(_sb(_el("cierre", 12.0, 14.0), duration=10.0)) == []


@pytest.mark.parametrize("fps, step", [(30, 0.1), (25, 0.04), (24, 0.125), (60, 0.05)])
def test_segment_bounds_are_whole_frames_with_exact_decimals(fps, step):
    # con 2,467 en vez de 74/30, data-start cae entre dos fotogramas y la máscara va uno por detrás del fondo (F28-340)
    assert M.segment_step(fps) == pytest.approx(step)
    x = M.matte_segments(_sb(_el("a", 2.33, 5.71), fps=fps))[0]
    for t in (x["start"], x["end"]):
        assert t * fps == pytest.approx(round(t * fps), abs=1e-6) and t == round(t, 3)


def test_explicit_matte_stays_out_of_the_segments():
    sb = _sb(_el("a", 2.0, 4.0, matte="mia.webm"), {"type": "behind", "id": "b", "start": 8.0, "end": 9.0, "text": "X", "matte": "b.webm"},
             {"type": "behind", "id": "c", "start": 20.0, "end": 22.0, "text": "AUTO"}, {"type": "box", "id": "d", "start": 25, "end": 26, "x": 0, "y": 0, "text": "delante"})
    assert [x["ids"] for x in M.matte_segments(sb)] == [["c"]]


# ---------- F28-340: caché ----------
def _project(tmp_path, *overlays, **root):
    (tmp_path / "clip.mp4").write_bytes(b"contenido del clip")
    return _sb(*overlays, **root)


def test_alpha_lut_clears_the_ghosts_and_keeps_a_ramp_for_the_hair():
    lut = M.alpha_lut()
    low, high = M.ALPHA_LEVELS
    assert lut[0] == 0 and lut[low] == 0 and lut[high] == 255 and lut[255] == 255
    assert lut[(low + high) // 2] in (127, 128)
    assert (np.diff(lut.astype(int)) >= 0).all() and len(set(lut.tolist())) > 150     # recta, no un umbral duro que hiciera parpadear


def test_every_frame_goes_out_with_the_refined_alpha(monkeypatch, tmp_path):
    # el fantasma medido junto a la oreja rondaba 5-70 de alfa y se veía sobre la tarjeta (F28-340)
    class Sess:
        def run(self, _, feed):
            h, w = feed["src"].shape[2:]
            pha = np.full((1, 1, h, w), 40 / 255, dtype=np.float32)
            pha[:, :, :, w // 2:] = 1.0
            return [np.full((1, 3, h, w), 0.5, dtype=np.float32), pha, *[np.zeros([1, 1, 1, 1], dtype=np.float32)] * 4]

    class Cap:
        left = 2

        def __init__(self, _):
            pass

        def get(self, prop):
            return {M.cv2.CAP_PROP_FRAME_WIDTH: 8, M.cv2.CAP_PROP_FRAME_HEIGHT: 4}[prop]

        def read(self):
            self.left -= 1
            return (True, np.zeros((4, 8, 3), np.uint8)) if self.left >= 0 else (False, None)

        def release(self):
            pass

    monkeypatch.setattr(M, "_session", lambda gpu: (Sess(), "CPUExecutionProvider"))
    monkeypatch.setattr(M.cv2, "VideoCapture", Cap)
    seen = []
    stats = M.matte_frames("x.mp4", seen.append)
    assert stats["frames"] == 2 and len(seen) == 2
    assert seen[0].shape == (4, 8, 4) and (seen[0][:, :4, 3] == 0).all() and (seen[0][:, 4:, 3] == 255).all()


def _fake_rvm(monkeypatch, fail_after: int | None = None):
    calls = []

    def fake(video, out, start, end, ratio=None, gpu=None):
        if fail_after is not None and len(calls) >= fail_after:
            out.write_bytes(b"a medias")
            raise RuntimeError("sin memoria")
        calls.append((start, end, ratio, gpu))
        out.write_bytes(b"webm")
        return {"seconds": 12.0, "provider": "CUDAExecutionProvider"}

    monkeypatch.setattr(M, "matte", fake)
    monkeypatch.setattr(M, "matte_speed", lambda: ("gpu", 2.0))
    return calls


def test_second_build_reuses_the_mask_without_calling_rvm(monkeypatch, tmp_path):
    calls = _fake_rvm(monkeypatch)
    sb = _project(tmp_path, _el("a", 2.0, 4.0))
    first = M.ensure_segments(sb, tmp_path)
    assert len(calls) == 1 and first["segments"][0]["cached"] and first["segments"][0]["computed_seconds"] == 12.0
    again = M.ensure_segments(sb, tmp_path)
    assert len(calls) == 1 and again["segments"][0]["cached"] and "computed_seconds" not in again["segments"][0]
    assert again["segments"][0]["file"] == first["segments"][0]["file"] and ".frame28" in again["segments"][0]["file"]


def test_cut_lands_on_the_first_frame_of_the_segment(monkeypatch, tmp_path):
    # -ss se queda con el primer fotograma >= el corte: medio fotograma antes para no perder ni arrastrar uno por redondeo
    calls = _fake_rvm(monkeypatch)
    M.ensure_segments(_project(tmp_path, _el("a", 2.0, 4.0)), tmp_path)
    start, end, *_ = calls[0]
    assert start == pytest.approx(1.8 - 0.5 / 30) and end == pytest.approx(4.2 - 0.5 / 30)


@pytest.mark.parametrize("change", ["clip", "window", "ratio"])
def test_the_cache_key_follows_clip_window_and_ratio(monkeypatch, tmp_path, change):
    calls = _fake_rvm(monkeypatch)
    sb = _project(tmp_path, _el("a", 2.0, 4.0))
    M.ensure_segments(sb, tmp_path)
    if change == "clip":
        (tmp_path / "clip.mp4").write_bytes(b"otro corte con el mismo nombre")
    elif change == "window":
        sb = _sb(_el("a", 2.0, 5.0))
    else:
        sb = {**sb, "matte_ratio": 0.5}
    M.ensure_segments(sb, tmp_path)
    assert len(calls) == 2


def test_the_key_also_depends_on_the_model_and_the_format(monkeypatch):
    a = M.segment_key("c", 1.0, 2.0)
    monkeypatch.setattr(M, "RVM_MODEL_SHA256", "otro modelo")
    b = M.segment_key("c", 1.0, 2.0)
    monkeypatch.setattr(M, "MATTE_FORMAT", M.MATTE_FORMAT + 1)
    assert len({a, b, M.segment_key("c", 1.0, 2.0)}) == 3


def test_a_failed_mask_leaves_nothing_in_the_cache(monkeypatch, tmp_path):
    _fake_rvm(monkeypatch, fail_after=0)
    sb = _project(tmp_path, _el("a", 2.0, 4.0))
    with pytest.raises(RuntimeError):
        M.ensure_segments(sb, tmp_path)
    assert not list((tmp_path / ".frame28" / "matte").glob("*"))
    assert not M.segment_plan(sb, tmp_path)["segments"][0]["cached"]


def test_plan_says_cached_pending_and_cost(monkeypatch, tmp_path):
    _fake_rvm(monkeypatch)
    sb = _project(tmp_path, _el("a", 2.0, 4.0), _el("b", 10.0, 12.0))
    M.ensure_segments(_sb(_el("a", 2.0, 4.0)), tmp_path)
    plan = M.segment_plan(sb, tmp_path)
    assert [x["cached"] for x in plan["segments"]] == [True, False]
    assert plan["total_seconds"] == 4.8 and plan["pending_seconds"] == 2.4
    assert plan["segments"][1]["frames"] == 72 and plan["device"] == "gpu"
    assert plan["estimated_minutes"] == round(72 / 2.0 / 60, 1) and plan["warnings"] == []


def test_plan_warns_over_a_minute_of_mask_with_gpu_and_cpu_time(monkeypatch, tmp_path):
    _fake_rvm(monkeypatch)
    plan = M.segment_plan(_project(tmp_path, _el("a", 2.0, 70.0), duration=100.0), tmp_path)
    assert plan["total_seconds"] > M.MATTE_WARN_S
    assert len(plan["warnings"]) == 1 and "min en GPU" in plan["warnings"][0] and "min en CPU" in plan["warnings"][0]


def test_plan_says_when_the_clip_is_missing(monkeypatch, tmp_path):
    _fake_rvm(monkeypatch)
    plan = M.segment_plan(_sb(_el("a", 2.0, 4.0)), tmp_path)
    assert not plan["segments"][0]["cached"] and "no existe el clip" in plan["warnings"][0]
    assert M.ensure_segments(_sb(_el("a", 2.0, 4.0)), tmp_path)["segments"][0]["key"] is None    # y no se intenta calcular


def test_cli_matte_plan_lists_segments_without_computing(monkeypatch, tmp_path):
    from click.testing import CliRunner
    from frame28.cli import main
    calls = _fake_rvm(monkeypatch)
    path = tmp_path / "sb.json"
    path.write_text(json.dumps(_project(tmp_path, _el("a", 2.0, 4.0))), encoding="utf-8")
    r = CliRunner().invoke(main, ["matte", "--plan", str(path)])
    assert r.exit_code == 0, r.output
    assert json.loads(r.output)["segments"][0]["start"] == 1.8 and not calls


def test_cli_matte_without_video_explains_what_it_needs():
    from click.testing import CliRunner
    from frame28.cli import main
    r = CliRunner().invoke(main, ["matte"])
    assert r.exit_code != 0 and "--plan" in r.output


def test_cli_matte_fps_defaults_to_the_source():
    from click.testing import CliRunner
    from frame28.cli import main
    r = CliRunner().invoke(main, ["matte", "--help"])
    assert r.exit_code == 0 and "vídeo de origen" in r.output and "default: 30" not in r.output
