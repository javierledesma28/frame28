"""F28-92: matte sale a los fps del tramo de origen (no a 30 fijos) y no deja la carpeta temporal si algo falla."""
from __future__ import annotations

import subprocess

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
    seen = {}

    def frames(src, png_dir, ratio):
        png_dir.mkdir(parents=True, exist_ok=True)
        (png_dir / "f_0000.png").write_bytes(b"x" * 1024)
        if fail:
            raise RuntimeError("onnxruntime se quedó sin memoria")
        seen["src"] = src
        return {"frames": 50, "fps": 12.5}

    monkeypatch.setattr(M, "matte_frames", frames)
    monkeypatch.setattr(M, "png_to_webm", lambda png_dir, out, fps: seen.setdefault("rate", fps))
    return work, seen


def test_matte_uses_the_rate_of_the_cut_segment(monkeypatch, tmp_path):
    work, seen = _fake_pipeline(monkeypatch, tmp_path)
    stats = M.matte("orig.mp4", tmp_path / "a.webm", start=1.0, end=3.0)
    assert seen["rate"] == "25/1" and stats["frame_rate"] == "25/1"
    assert seen["src"].name == "seg.mp4"                       # los fps se leen del tramo, no se suponen
    assert stats["fps"] == 12.5                                  # «fps» sigue siendo la velocidad de RVM, como antes
    assert not work.exists()


def test_matte_fps_option_still_forces_the_rate(monkeypatch, tmp_path):
    _, seen = _fake_pipeline(monkeypatch, tmp_path)
    assert M.matte("orig.mp4", tmp_path / "a.webm", fps=60)["frame_rate"] == "60" and seen["rate"] == 60


def test_matte_removes_the_temp_folder_when_it_fails(monkeypatch, tmp_path):
    work, _ = _fake_pipeline(monkeypatch, tmp_path, fail=True)
    with pytest.raises(RuntimeError):
        M.matte("orig.mp4", tmp_path / "a.webm", start=1.0, end=3.0)
    assert not work.exists()                                     # antes quedaban los PNG RGBA (gigas) en %TEMP%


def test_cli_matte_fps_defaults_to_the_source():
    from click.testing import CliRunner
    from frame28.cli import main
    r = CliRunner().invoke(main, ["matte", "--help"])
    assert r.exit_code == 0 and "vídeo de origen" in r.output and "default: 30" not in r.output
