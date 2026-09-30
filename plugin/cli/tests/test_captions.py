"""captions: cargador único de words/captions, lienzo por defecto, paginado y cues SRT/VTT."""
from __future__ import annotations

import json

import pytest

from frame28 import captions as C
from conftest import words_from, write_json


# ---------- lienzo ----------
@pytest.mark.parametrize("wh,expected", [((1920, 1080), (1920, 1080)), ((1280, 720), (1920, 1080)), ((1080, 1920), (1080, 1920)),
                                         ((720, 1280), (1080, 1920)), ((1080, 1080), (1080, 1080)), ((0, 0), (1920, 1080))])
def test_default_canvas(wh, expected):
    assert C.default_canvas(*wh) == expected


def test_parse_canvas():
    assert C.parse_canvas("1080×1920", 1920, 1080) == (1080, 1920)
    assert C.parse_canvas("1080x1080", 1920, 1080) == (1080, 1080)
    assert C.parse_canvas(None, 720, 1280) == (1080, 1920)
    assert C.parse_canvas("auto", 1920, 1080) == (1920, 1080)


# ---------- normalize_words ----------
def test_normalize_words_accepts_hyperframes_ms_and_word_key():
    data = [{"word": "hola", "startMs": 500, "endMs": 900}, {"word": "mundo", "startMs": 1000, "endMs": 1400}]
    ws = C.normalize_words(data)
    assert [w["text"] for w in ws] == ["hola", "mundo"]
    assert ws[0]["start"] == 0.5 and ws[0]["end"] == 0.9
    assert "startMs" not in ws[0] and "word" not in ws[0]


def test_normalize_words_accepts_segments_dict_and_keeps_extra_keys():
    data = {"segments": [{"words": [{"text": "a", "start": 0, "end": 0.2, "prob": 0.9}]}, {"words": [{"text": "b", "start": 0.3, "end": 0.5}]}]}
    ws = C.normalize_words(data)
    assert [w["text"] for w in ws] == ["a", "b"]
    assert ws[0]["prob"] == 0.9


def test_normalize_words_merges_symbols_and_skips_empty():
    data = [{"text": "30", "start": 0, "end": 0.3}, {"text": "%", "start": 0.3, "end": 0.4}, {"text": "  ", "start": 0.4, "end": 0.5},
            {"text": "€", "start": 0.5, "end": 0.6}]
    ws = C.normalize_words(data)
    assert [w["text"] for w in ws] == ["30%€"]
    assert ws[0]["end"] == 0.6
    assert [w["text"] for w in C.normalize_words(data, merge_symbols=False)] == ["30", "%", "€"]


@pytest.mark.parametrize("bad", [
    {"foo": []},
    "no soy una lista",
    [{"text": "x"}],
    ["cadena suelta"],
])
def test_normalize_words_short_error(bad):
    with pytest.raises(C.TranscriptFormatError):
        C.normalize_words(bad)


def test_load_words_real_fixture_is_monotonic(javier_words):
    ws = C.load_words(javier_words)
    assert len(ws) > 20
    assert all(w["end"] >= w["start"] for w in ws)
    assert all(b["start"] >= a["start"] for a, b in zip(ws, ws[1:]))


def test_load_words_invalid_json_is_transcript_error(tmp_path):
    p = tmp_path / "words.json"; p.write_text("{no json", encoding="utf-8")
    with pytest.raises(C.TranscriptFormatError, match="JSON inválido"):
        C.load_words(p)


def test_load_captions_accepts_dict_in_ms(tmp_path):
    p = write_json(tmp_path / "captions.json", {"captions": [{"text": "Hola.", "startMs": 0, "endMs": 1200}, {"text": "", "startMs": 1200, "endMs": 1300}]})
    caps = C.load_captions(p)
    assert caps == [{"text": "Hola.", "start": 0.0, "end": 1.2}]
    write_json(p, [{"text": "sin tiempos"}])
    with pytest.raises(C.TranscriptFormatError, match="regenera"):
        C.load_captions(p)


# ---------- pages ----------
def test_pages_respects_max_words_and_punctuation():
    ws = words_from("uno dos tres cuatro cinco seis. siete ocho")
    pg = C.pages(ws, max_words=4)
    assert [p["text"] for p in pg] == ["uno dos tres cuatro", "cinco seis.", "siete ocho"]
    for a, b in zip(pg, pg[1:]):
        assert a["end"] <= b["start"]  # nunca dos páginas a la vez
    assert pg[-1]["end"] == pytest.approx(ws[-1]["end"] + 0.8, abs=1e-3)


def test_pages_breaks_on_long_gap_and_max_chars():
    ws = words_from("hola mundo|3.0 otra")
    assert [p["text"] for p in C.pages(ws)] == ["hola", "mundo otra"]
    ws = words_from("supercalifragilístico espialidoso")
    assert len(C.pages(ws, max_chars=22)) == 2


# ---------- cues ----------
def test_cues_are_readable_and_do_not_overlap():
    text = ("esta es una frase bastante larga que sigue y sigue para probar el corte en dos líneas equilibradas, "
            "y luego otra frase. Y una tercera corta.")
    ws = words_from(text, dur=0.25, gap=0.02)
    cs = C.cues(ws)
    assert len(cs) >= 2
    for c in cs:
        assert 1 <= len(c["lines"]) <= 2
        assert all(len(line) <= 42 for line in c["lines"])
        assert c["end"] - c["start"] >= 0.3
        assert c["end"] - c["start"] <= 7.0 + 1.0
    for a, b in zip(cs, cs[1:]):
        assert a["end"] <= b["start"]


def test_cues_min_duration_and_cps_warning():
    ws = words_from("palabras muy rápidas apretadísimas aquí", dur=0.05, gap=0.0)
    cs = C.cues(ws, min_dur=1.0)
    assert cs[0]["end"] - cs[0]["start"] >= 1.0
    fast = C.cues(words_from("una frase larguísima dicha a toda velocidad sin pausa ninguna", dur=0.02, gap=0.0), min_dur=0.3)
    assert any("cps" in w for c in fast for w in c["warnings"])


def test_export_srt_uses_lf_and_vtt_header(tmp_path):
    wp = write_json(tmp_path / "words.json", words_from("hola mundo. adiós mundo."))
    r = C.export(wp, tmp_path / "subs.srt")
    raw = (tmp_path / "subs.srt").read_bytes()
    assert b"\r\n" not in raw and raw.startswith(b"1\n00:00:00,000 --> ")
    assert r["cues"] >= 1 and r["words"] == 4
    C.export(wp, tmp_path / "subs.vtt")
    assert (tmp_path / "subs.vtt").read_text(encoding="utf-8").startswith("WEBVTT\n\n1\n00:00:00.000 --> ")


def test_ts_format():
    assert C._ts(3661.5) == "01:01:01,500"
    assert C._ts(0.04, ".") == "00:00:00.040"
