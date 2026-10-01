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


# ---------- subtítulos por frase completa (día 6: la transcripción venía troceada a mitad de frase) ----------
LONG = ("Today we paint a small wooden box. First you sand every side until it feels smooth "
        "and then you wipe the dust with a dry cloth because paint never sticks to a dusty surface. Done!")


def test_sentences_split_on_final_punctuation_and_long_pauses():
    ws = words_from("One two. Three four five|9.0 six seven")
    assert [C._text(s) for s in C.sentences(ws)] == ["One two.", "Three four", "five six seven"]


def test_phrase_captions_keep_sentences_whole_and_split_long_ones_at_joints():
    caps = C.phrase_captions(words_from(LONG), max_chars=84, lang="en")
    texts = [c["text"] for c in caps]
    assert texts[0] == "Today we paint a small wooden box." and texts[-1] == "Done!"
    assert all(len(t) <= 84 for t in texts)
    middle = [c for c in caps if c["sent"] == 1]
    assert len(middle) >= 2 and " ".join(c["text"] for c in middle).endswith("a dusty surface.")
    assert all(c["text"].split()[0] in C.JOINTS["en"] for c in middle[1:])      # la parte nueva empieza en conjunción
    assert [c["sent"] for c in caps] == sorted(c["sent"] for c in caps)
    assert all(a["end"] <= b["start"] for a, b in zip(caps, caps[1:]))          # sin solapes
    assert all(c["end"] - c["start"] >= 0.3 for c in caps)


def test_phrase_captions_prefer_a_comma_and_know_spanish_joints():
    es = "Primero lijas todas las caras hasta que queden suaves, luego quitas el polvo con un trapo seco porque la pintura no agarra."
    caps = C.phrase_captions(words_from(es), max_chars=70, lang="es")
    assert len(caps) >= 2 and all(len(c["text"]) <= 70 for c in caps)
    assert caps[0]["text"].endswith("suaves,")


def test_group_sentences_from_sent_index_and_from_punctuation():
    caps = C.phrase_captions(words_from(LONG))
    whole = C.group_sentences(caps)
    assert [c["text"] for c in whole][0] == "Today we paint a small wooden box." and len(whole) == 3
    assert whole[1]["start"] == caps[1]["start"] and whole[1]["text"].endswith("a dusty surface.")
    old = [{"start": 0.0, "end": 2.0, "text": "This starts here and"}, {"start": 2.0, "end": 4.0, "text": "ends here. Another"},
           {"start": 4.0, "end": 5.0, "text": "one."}]
    merged = C.group_sentences(old)                                             # segmentos de Whisper, sin `sent`
    assert [c["text"] for c in merged] == ["This starts here and ends here. Another one."]
    assert merged[0]["start"] == 0.0 and merged[0]["end"] == 5.0


def test_export_from_a_translated_storyboard_keeps_its_phrases_and_times(tmp_path):
    sb = {"version": 1, "overlays": [], "captions": [
        {"start": 1.0, "end": 3.0, "text": "Hoy pintamos una caja pequeña de madera."},
        {"start": 3.2, "end": 4.0, "text": "Primero se lijan todas las caras hasta que queden suaves al tacto."}]}
    p = write_json(tmp_path / "storyboard.es.json", sb)
    r = C.export(p, tmp_path / "es.srt")
    assert r["source"] == "storyboard" and r["cues"] == 2 and r["words"] == 0 and r["mean_cps"] > 0
    assert any("cps" in w for w in r["warnings"])                               # la segunda frase no da tiempo a leerla
    srt = (tmp_path / "es.srt").read_text(encoding="utf-8")
    assert "00:00:01,000 --> 00:00:03,000" in srt and "caja pequeña" in srt
    words = write_json(tmp_path / "words.json", words_from("uno dos tres."))
    assert C.export(words, tmp_path / "w.srt")["source"] == "words"            # words.json sigue igual
    per_word = write_json(tmp_path / "short.json", {"version": 1, "overlays": [], "caption_style": {"preset": "pages", "words": "words.json"}})
    assert C.export(per_word, tmp_path / "s.srt")["words"] == 3                 # subtítulos por palabras: sigue caption_style.words
