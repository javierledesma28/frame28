"""cut: plan de jump cuts (silencios, muletillas, falsos arranques) y remapeo de tiempos. Sin ffmpeg."""
from __future__ import annotations

import pytest

from frame28 import cut
from conftest import words_from, write_json, write_wav


def _plan(tmp_path, words, **kw):
    return cut.plan(write_json(tmp_path / "words.json", words), **kw)


def test_plan_real_fixture_keeps_less_than_source(javier_words, tmp_path):
    r = cut.plan(javier_words)
    assert r["source_duration"] > 0
    assert 0 < r["result_duration"] <= r["source_duration"]
    assert r["removed_seconds"] == pytest.approx(r["source_duration"] - r["result_duration"], abs=0.01)
    for k in r["keep"]:
        assert k["end"] > k["start"]
    for a, b in zip(r["keep"], r["keep"][1:]):
        assert a["end"] <= b["start"]


def test_plan_gap_without_audio(tmp_path):
    ws = words_from("hola mundo|3.0 sigo")
    r = _plan(tmp_path, ws, duration=4.0)
    reasons = [x["reason"] for x in r["removed"]]
    assert any("silencio pausa" in s for s in reasons)
    assert any("silencio final" in s for s in reasons)
    assert not any("inicio" in s for s in reasons)  # 0,0 s de aire al inicio: nada que cortar
    assert r["result_duration"] < r["source_duration"]


def test_plan_gap_confirmed_against_audio(tmp_path):
    # voz 0-1 s, silencio 1-3 s, voz 3-4 s; la transcripción deja hueco 0.9-3.05
    wav = write_wav(tmp_path / "voice.wav", [(0.0, 1.0, True), (1.0, 3.0, False), (3.0, 4.0, True)])
    ws = words_from("hola mundo", start=0.0, dur=0.4, gap=0.1) + [{"text": "sigo", "start": 3.05, "end": 3.9}]
    r = _plan(tmp_path, ws, audio=wav)
    gap = [x for x in r["removed"] if "silencio pausa" in x["reason"]]
    assert len(gap) == 1
    assert 1.0 <= gap[0]["start"] <= 1.2 and 2.8 <= gap[0]["end"] <= 3.0  # el núcleo silencioso, con aire a cada lado
    assert r["source_duration"] == pytest.approx(4.0, abs=0.05)


def test_plan_silence_inside_stretched_word(tmp_path):
    # Whisper estira "bueno" hasta cubrir una pausa de 1,5 s
    wav = write_wav(tmp_path / "voice.wav", [(0.0, 0.5, True), (0.5, 2.0, False), (2.0, 3.0, True)])
    ws = [{"text": "bueno", "start": 0.0, "end": 2.0}, {"text": "sigo", "start": 2.0, "end": 2.9}]
    r = _plan(tmp_path, ws, audio=wav, fillers=False)
    assert any("silencio dentro de 'bueno'" in x["reason"] for x in r["removed"])


def test_plan_fillers_and_soft_fillers(tmp_path):
    ws = words_from("hola eh mundo")
    r = _plan(tmp_path, ws, duration=1.2)
    assert any("muletilla 'eh'" in x["reason"] for x in r["removed"])
    sin = _plan(tmp_path, ws, duration=1.2, fillers=False)
    assert all("muletilla" not in x["reason"] for x in sin["removed"])
    # "este" nunca se corta aunque vaya seguido de pausa (ambiguo: "este muñeco")
    wav = write_wav(tmp_path / "v.wav", [(0.0, 0.4, True), (0.4, 1.2, False), (1.2, 2.0, True)])
    ws = [{"text": "este", "start": 0.0, "end": 0.4}, {"text": "muñeco", "start": 1.2, "end": 1.9}]
    r = _plan(tmp_path, ws, audio=wav)
    assert not any("muletilla" in x["reason"] for x in r["removed"])
    # "bueno" aislado por una pausa sí
    ws = [{"text": "bueno", "start": 0.0, "end": 0.4}, {"text": "sigo", "start": 1.2, "end": 1.9}]
    r = _plan(tmp_path, ws, audio=wav)
    assert any("muletilla 'bueno' (aislada por pausa)" in x["reason"] for x in r["removed"])


def test_plan_retake_detected_but_not_parallel_structure(tmp_path):
    ws = words_from("esta es una frase|0.0 esta|1.6 es una frase completa ya")
    r = _plan(tmp_path, ws)
    fa = [x for x in r["removed"] if "falso arranque" in x["reason"]]
    assert len(fa) == 1 and "esta es una frase" in fa[0]["reason"]
    assert fa[0]["end"] == pytest.approx(1.6 - 0.03, abs=1e-3)
    # "por aquí hay X, por aquí hay Y" sin pausa: estructura paralela, no se toca
    ws = words_from("por aquí hay luz por aquí hay sombra", gap=0.02)
    assert not any("falso arranque" in x["reason"] for x in _plan(tmp_path, ws)["removed"])


def test_plan_merges_adjacent_removals(tmp_path):
    ws = words_from("hola eh|1.0 eh mundo|4.0", gap=0.05)
    r = _plan(tmp_path, ws, duration=4.5)
    starts = [x["start"] for x in r["removed"]]
    assert starts == sorted(starts)
    for a, b in zip(r["removed"], r["removed"][1:]):
        assert b["start"] > a["end"] + 0.02


# ---------- remapeo ----------
KEEP = [{"start": 0.0, "end": 2.0}, {"start": 3.0, "end": 5.0}]


def test_mapper_inside_gap_and_clamp():
    f = cut._mapper(KEEP)
    assert f(1.0) == 1.0
    assert f(3.5) == 2.5
    assert f(2.5, clamp=False) is None
    assert f(2.5) == 2.0  # borde más cercano


def test_remap_words_drops_removed_and_clamps_partial():
    ws = [{"text": "a", "start": 0.5, "end": 1.0}, {"text": "eh", "start": 2.2, "end": 2.6}, {"text": "b", "start": 1.8, "end": 2.4},
          {"text": "c", "start": 3.2, "end": 3.6}]
    out = cut.remap_words(ws, KEEP)
    assert [w["text"] for w in out] == ["a", "b", "c"]
    assert out[1] == {"text": "b", "start": 1.8, "end": 2.0}
    assert out[2] == {"text": "c", "start": 2.2, "end": 2.6}


def test_remap_storyboard_shifts_overlays(javier_storyboard):
    sb = dict(javier_storyboard); sb["_removed"] = [{"start": 2.0, "end": 3.0}]
    keep = [{"start": 0.0, "end": 2.0}, {"start": 3.0, "end": 10.0}]
    new, warns = cut.remap_storyboard(sb, keep)
    assert new["source"]["duration"] == 9.0
    assert new["duration"] == pytest.approx(javier_storyboard["duration"] - 1.0)
    assert "_removed" not in new
    old = {o["id"]: o for o in javier_storyboard["overlays"]}
    for o in new["overlays"]:
        if old[o["id"]]["start"] >= 3.0 and old[o["id"]]["start"] <= 10.0:
            assert o["start"] == pytest.approx(old[o["id"]]["start"] - 1.0, abs=1e-3)
        assert o["end"] > o["start"]
    assert not [w for w in warns if "behind" in w], "el corte (2–3 s) queda fuera de la máscara alfa (4,3–6,8 s)"


def test_remap_storyboard_warns_when_a_cut_falls_inside_the_matte(javier_storyboard):
    # la máscara del behind va de 4,3 a 6,8 s; un corte al final de la máscara (6,5–6,9) debe avisar.
    # Regresión: se comparaba con los tiempos ya remapeados del overlay y este caso pasaba en silencio.
    sb = dict(javier_storyboard); sb["_removed"] = [{"start": 6.5, "end": 6.9}]
    keep = [{"start": 0.0, "end": 6.5}, {"start": 6.9, "end": 10.0}]
    _, warns = cut.remap_storyboard(sb, keep)
    assert any("bh (behind)" in w and "frame28 matte" in w for w in warns)


def test_remap_storyboard_collapsed_overlay_gets_half_second():
    sb = {"version": 1, "source": {"video": "x", "duration": 5.0}, "duration": 5.0,
          "overlays": [{"type": "box", "id": "b", "x": 0, "y": 0, "text": "t", "start": 2.1, "end": 2.9}]}
    new, warns = cut.remap_storyboard(sb, [{"start": 0.0, "end": 2.0}, {"start": 3.0, "end": 5.0}])
    o = new["overlays"][0]
    assert o["start"] == 2.0 and o["end"] == 2.5
    assert any("colapsada" in w for w in warns)
