"""F28-93: prep, cut apply y audio paran con un mensaje claro si falla un paso de ffmpeg, prep no pierde voice.wav y
`--denoise none` normaliza al `--lufs` pedido (antes, -16 en una pasada)."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
from click.testing import CliRunner

from frame28 import audio as A
from frame28 import cut as K
from frame28 import env as E
from frame28 import media as M

LOUDNORM = '{\n "input_i" : "-30.0", "input_tp" : "-9.0", "input_lra" : "4.0", "input_thresh" : "-40.0", "target_offset" : "0.1"\n}'


def _fake_run(monkeypatch, fails=lambda cmd: False, stderr="", *modules):
    """`run` simulado en env (lo usa run_ok) y en los módulos dados; `fails(cmd)` decide qué orden sale con código 1."""
    seen: list[list[str]] = []

    def run(cmd, **kw):
        seen.append([str(c) for c in cmd])
        if fails(seen[-1]):
            return subprocess.CompletedProcess(cmd, 1, "", "Error opening input: Invalid data found when processing input")
        return subprocess.CompletedProcess(cmd, 0, "", stderr)

    for mod in (E, *modules):
        monkeypatch.setattr(mod, "run", run)
    for mod in (M, K, A):
        monkeypatch.setattr(mod, "ffmpeg", lambda: "ffmpeg")
    monkeypatch.setattr(E, "ffmpeg", lambda: "ffmpeg")
    return seen


def test_run_ok_says_which_step_failed_and_how(monkeypatch):
    _fake_run(monkeypatch, fails=lambda cmd: True)
    with pytest.raises(SystemExit) as e:
        E.run_ok(["ffmpeg", "-i", "x.mp4"], "prep: extraer la voz de x.mp4")
    msg = str(e.value)
    assert msg.startswith("prep: extraer la voz de x.mp4: ffmpeg salió con el código 1")
    assert "Invalid data found" in msg


def test_prep_stops_when_the_voice_cannot_be_extracted(monkeypatch, tmp_path):
    monkeypatch.setattr(M, "probe", lambda v: {"video": {"width": 1920, "height": 1080}, "audio": {"codec": "aac"}})
    monkeypatch.setattr(M, "gpu_decode_args", lambda info, fps, width: None)
    _fake_run(monkeypatch, lambda cmd: "48000" in cmd, "", M)
    with pytest.raises(SystemExit) as e:
        M.prep(tmp_path / "in.mp4", tmp_path / "work")
    assert "prep: extraer la voz de in.mp4" in str(e.value)             # antes seguía y transcribe fallaba sin audio


def test_prep_extracts_the_voice_as_is(monkeypatch, tmp_path):
    monkeypatch.setattr(M, "probe", lambda v: {"video": {"width": 1920, "height": 1080}, "audio": {"codec": "aac"}})
    monkeypatch.setattr(M, "gpu_decode_args", lambda info, fps, width: None)
    seen = _fake_run(monkeypatch, lambda cmd: False, "", M)
    M.prep(tmp_path / "in.mp4", tmp_path / "work")
    assert not any("loudnorm" in " ".join(c) for c in seen)             # la sonoridad la pone audio.clean, al --lufs pedido


def _cli_prep(monkeypatch, tmp_path, args, clean_fails=False):
    work = tmp_path / "work"

    def prep(video, out_dir, fps, width):
        work.mkdir(parents=True, exist_ok=True)
        (work / "voice.wav").write_bytes(b"voz original"); (work / "audio16k.wav").write_bytes(b"16k")
        return {"clip": str(work / "clip.mp4"), "voice": str(work / "voice.wav"), "audio16k": str(work / "audio16k.wav")}

    calls = {}

    def clean(src, dst, denoise, strength, lufs, highpass=80):
        calls.update(src=str(src), denoise=denoise, lufs=lufs, highpass=highpass)
        Path(dst).write_bytes(b"voz a medias")
        if clean_fails:
            raise SystemExit("audio: limpiar y normalizar voice.wav: ffmpeg salió con el código 1")
        return {"before": {"integrated_lufs": -31.0}, "after": {"integrated_lufs": lufs}}

    monkeypatch.setattr(M, "prep", prep)
    monkeypatch.setattr(A, "clean", clean)
    seen = _fake_run(monkeypatch)
    video = tmp_path / "in.mp4"; video.write_bytes(b"x")
    from frame28.cli import main
    r = CliRunner().invoke(main, ["prep", str(video), "-o", str(work), *args])
    return r, work, calls, seen


def test_cli_prep_keeps_voice_wav_when_cleaning_fails(monkeypatch, tmp_path):
    r, work, _, _ = _cli_prep(monkeypatch, tmp_path, [], clean_fails=True)
    assert r.exit_code != 0 and "audio: limpiar y normalizar" in str(r.exception or r.output)
    assert (work / "voice.wav").read_bytes() == b"voz original"           # antes se renombraba a voice_raw.wav y desaparecía
    assert not (work / "voice_raw.wav").exists() and not (work / "voice.clean.wav").exists()


def test_cli_prep_denoise_none_normalizes_to_the_requested_lufs(monkeypatch, tmp_path):
    r, work, calls, seen = _cli_prep(monkeypatch, tmp_path, ["--denoise", "none", "--lufs", "-14"])
    assert r.exit_code == 0, r.output
    assert calls == {"src": str(work / "voice.wav"), "denoise": "none", "lufs": -14.0, "highpass": 0}
    assert json.loads(r.output)["audio"]["lufs"] == -14.0
    assert (work / "voice_raw.wav").read_bytes() == b"voz original" and (work / "voice.wav").read_bytes() == b"voz a medias"
    assert any("16000" in c and str(work / "voice.wav") in c for c in seen)  # el audio de 16 kHz sale de la voz ya limpia


def test_cli_prep_default_cleans_with_highpass(monkeypatch, tmp_path):
    r, _, calls, _ = _cli_prep(monkeypatch, tmp_path, [])
    assert r.exit_code == 0, r.output
    assert calls["denoise"] == "afftdn" and calls["lufs"] == -14.0 and calls["highpass"] == 80


def test_cut_apply_refuses_an_empty_plan(tmp_path):
    plan = tmp_path / "cuts.json"
    plan.write_text(json.dumps({"keep": [], "removed": [], "result_duration": 0}), encoding="utf-8")
    with pytest.raises(SystemExit) as e:
        K.apply(tmp_path / "clip.mp4", None, plan, tmp_path / "cut")
    assert "no conserva ningún tramo" in str(e.value)                    # antes, concat=n=0 y un error de filtros


def test_cut_apply_stops_when_the_16k_audio_fails(monkeypatch, tmp_path):
    plan = tmp_path / "cuts.json"
    plan.write_text(json.dumps({"keep": [{"start": 0.0, "end": 1.0}], "removed": [], "result_duration": 1.0}), encoding="utf-8")
    _fake_run(monkeypatch, lambda cmd: "16000" in cmd, "", K)
    with pytest.raises(SystemExit) as e:
        K.apply(tmp_path / "clip.mp4", tmp_path / "voice.wav", plan, tmp_path / "cut")
    assert "cut apply: audio de 16 kHz" in str(e.value)


def test_measure_stops_and_cleans_up_when_the_wav_fails(monkeypatch, tmp_path):
    tmp = tmp_path / "frame28_audio_x"
    monkeypatch.setattr(A.tempfile, "mkdtemp", lambda prefix="": (tmp.mkdir(), str(tmp))[1])
    _fake_run(monkeypatch, lambda cmd: "s16" in cmd, "I: -20.0 LUFS\nLRA: 5.0 LU\nPeak: -1.0 dBFS", A)
    with pytest.raises(SystemExit) as e:
        A.measure(tmp_path / "voz.wav")
    assert "audio: pasar voz.wav a WAV mono" in str(e.value)            # antes, un wave.Error sin contexto
    assert not tmp.exists()


def test_clean_removes_its_temp_folder_when_it_fails(monkeypatch, tmp_path):
    tmp = tmp_path / "frame28_clean_x"
    monkeypatch.setattr(A.tempfile, "mkdtemp", lambda prefix="": (tmp.mkdir(), str(tmp))[1])
    monkeypatch.setattr(A, "measure", lambda p: {"integrated_lufs": -30.0, "snr_db": 20.0})
    _fake_run(monkeypatch, lambda cmd: "linear=true" in " ".join(cmd), LOUDNORM, A)
    with pytest.raises(SystemExit) as e:
        A.clean(tmp_path / "voz.wav", tmp_path / "limpia.wav", "afftdn")
    assert "audio: limpiar y normalizar voz.wav" in str(e.value)
    assert not tmp.exists()
