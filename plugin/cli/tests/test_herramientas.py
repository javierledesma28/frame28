"""F28-94: ffmpeg de WinGet por versión (no por texto) y buscado una vez, mensaje de instalación por plataforma y
filtros largos de cut apply por fichero (en línea, con ~280 tramos, Windows da WinError 206)."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from frame28 import cut as K
from frame28 import env as E

WINDOWS_MAX = 32767   # caracteres de una orden en Windows (CreateProcess)


@pytest.fixture
def winget(monkeypatch):
    calls = []

    def set_candidates(paths):
        def cands(exe):
            calls.append(exe)
            return list(paths)
        monkeypatch.setattr(E, "_winget_candidates", cands)
        E._winget_best.cache_clear()
        return calls

    yield set_candidates
    E._winget_best.cache_clear()


def test_winget_picks_the_highest_version_not_the_last_by_text(winget):
    base = "C:/Users/u/AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe"
    winget([f"{base}/ffmpeg-9.0.2-full_build/bin/ffmpeg.exe", f"{base}/ffmpeg-10.0-full_build/bin/ffmpeg.exe",
            f"{base}/ffmpeg-8.1.1-full_build/bin/ffmpeg.exe"])
    assert "ffmpeg-10.0-full_build" in E._winget_best("ffmpeg")      # como texto ganaba la 9.0.2


def test_winget_is_scanned_once_per_process(winget):
    calls = winget(["C:/x/ffmpeg-9.0.2-full_build/bin/ffmpeg.exe"])
    for _ in range(3):
        E._winget_best("ffmpeg")
    assert calls == ["ffmpeg"]                                      # antes, un glob recursivo en cada ffmpeg()
    E._winget_best("ffprobe")
    assert calls == ["ffmpeg", "ffprobe"]                           # una búsqueda por ejecutable


@pytest.mark.parametrize("platform, hint", [("win32", "winget install --id Gyan.FFmpeg -e"), ("darwin", "brew install ffmpeg"),
                                            ("linux", "sudo apt install ffmpeg")])
def test_missing_ffmpeg_says_how_to_install_it_on_this_platform(monkeypatch, platform, hint):
    monkeypatch.setattr(E.sys, "platform", platform)
    monkeypatch.setattr(E, "find_tool", lambda name, env_var=None: None)
    with pytest.raises(SystemExit) as e:
        E.ffmpeg()
    assert hint in str(e.value)
    assert platform == "win32" or "winget" not in str(e.value)       # antes, winget también en Mac y Linux


def _fake_run(monkeypatch, fails=lambda cmd: None):
    """run simulado: guarda cada orden con el contenido del fichero de filtros (que se borra al terminar)."""
    seen = []

    def run(cmd, **kw):
        cmd = [str(c) for c in cmd]
        script = None
        for flag in ("-/filter_complex", "-filter_complex_script"):
            if flag in cmd:
                script = Path(cmd[cmd.index(flag) + 1])
        seen.append({"cmd": cmd, "script": script, "fc": script.read_text(encoding="utf-8") if script else None})
        err = fails(cmd)
        return subprocess.CompletedProcess(cmd, 8 if err else 0, "", err or "")

    monkeypatch.setattr(E, "run", run)
    monkeypatch.setattr(E, "ffmpeg", lambda: "ffmpeg")
    monkeypatch.setattr(K, "ffmpeg", lambda: "ffmpeg")
    return seen


def test_run_filter_complex_passes_the_graph_in_a_file(monkeypatch):
    seen = _fake_run(monkeypatch)
    fc = "[0:v]null[v]"
    E.run_filter_complex(["-i", "in.mp4"], fc, ["-map", "[v]", "out.mp4"], "prueba")
    (call,) = seen
    assert call["cmd"][:4] == ["ffmpeg", "-i", "in.mp4", "-/filter_complex"] and fc not in call["cmd"]
    assert call["fc"] == fc and not call["script"].exists()          # el fichero temporal se borra


def test_run_filter_complex_falls_back_on_ffmpeg_older_than_7(monkeypatch):
    old = "Unrecognized option '/filter_complex'.\nError splitting the argument list: Option not found"
    seen = _fake_run(monkeypatch, lambda cmd: old if "-/filter_complex" in cmd else None)
    E.run_filter_complex(["-i", "in.mp4"], "[0:v]null[v]", ["out.mp4"], "prueba")
    assert [("-filter_complex_script" in c["cmd"]) for c in seen] == [False, True]
    assert seen[1]["fc"] == "[0:v]null[v]"


def test_run_filter_complex_stops_with_the_step(monkeypatch):
    _fake_run(monkeypatch, lambda cmd: "Invalid argument")
    with pytest.raises(SystemExit) as e:
        E.run_filter_complex(["-i", "in.mp4"], "[0:v]null[v]", ["out.mp4"], "cut apply: montar el vídeo con los tramos")
    assert str(e.value).startswith("cut apply: montar el vídeo con los tramos: ffmpeg salió con el código 8")


def test_cut_apply_with_500_segments_fits_in_a_windows_command(monkeypatch, tmp_path):
    keep = [{"start": round(0.1 * i, 3), "end": round(0.1 * i + 0.06, 3)} for i in range(500)]
    plan = tmp_path / "cuts.json"
    plan.write_text(json.dumps({"keep": keep, "removed": [], "result_duration": 30.0}), encoding="utf-8")
    seen = _fake_run(monkeypatch)
    K.apply(tmp_path / "clip.mp4", tmp_path / "voice.wav", plan, tmp_path / "cut")
    graphs = [c for c in seen if c["fc"]]
    assert len(graphs) == 2 and "concat=n=500:v=1" in graphs[0]["fc"] and "concat=n=500:v=0:a=1" in graphs[1]["fc"]
    assert max(len(c["fc"]) for c in graphs) > WINDOWS_MAX                # en línea no cabría (WinError 206)
    assert all(len(subprocess.list2cmdline(c["cmd"])) < 2000 for c in seen)
