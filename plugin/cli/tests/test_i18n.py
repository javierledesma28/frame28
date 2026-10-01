"""i18n: extracción de textos, aplicación de traducciones y retiming de palabras sobre el ritmo original."""
from __future__ import annotations

import json

import pytest

from frame28 import i18n
from frame28.build import validate
from conftest import words_from, write_json


def test_extract_short_storyboard(grabado_short):
    r = i18n.extract(grabado_short)
    keys = set(r["strings"])
    assert {"hook.lines.0", "hook.lines.1", "cta.title"} <= keys
    assert r["strings"]["hook.lines.0"]["max_chars"] == i18n.LIMITS["hook"]
    assert r["strings"]["hook.lines.0"]["type"] == "hook"
    assert r["count"] == len(keys)
    assert r["lang"] == "en"


def test_extract_card_title_dict_and_captions():
    sb = {"overlays": [{"type": "card", "id": "c", "start": 0, "end": 1, "title": {"text": "Título", "at": 0.2}, "items": ["uno", "dos"]}],
          "captions": [{"start": 0, "end": 1, "text": "Hola."}], "meta": {"lang": "es"}}
    r = i18n.extract(sb)
    assert r["strings"]["c.title.text"]["text"] == "Título"
    assert r["strings"]["c.items.1"]["text"] == "dos"
    assert r["strings"]["captions.0.text"] == {"text": "Hola.", "type": "caption", "id": "captions.0", "at": 0}


def test_apply_replaces_texts_and_warns(grabado_short, grabado_strings):
    new, warns = i18n.apply(grabado_short, grabado_strings, "es")
    assert new["meta"]["lang"] == "es"
    hook = next(o for o in new["overlays"] if o["id"] == "hook")
    assert hook["lines"] == [grabado_strings["strings"]["hook.lines.0"], grabado_strings["strings"]["hook.lines.1"]]
    assert validate(new) == []
    assert grabado_short["meta"]["lang"] == "en", "apply no debe tocar el original"
    # las frases de captions.json no van al storyboard cuando los subtítulos son por palabras
    assert "captions" not in new
    new2, warns2 = i18n.apply(grabado_short, {"hook.lines.0": "x" * 60, "nadie.text": "y"}, "de")
    assert any("60 caracteres" in w for w in warns2)
    assert any("no existe" in w for w in warns2)


def test_retime_words_follows_original_rhythm():
    words = words_from("one two three", start=1.0, dur=0.3, gap=0.2)  # 1.0-1.3, 1.5-1.8, 2.0-2.3
    caps = [{"start": 1.0, "end": 2.3, "text": "one two three"}]
    out = i18n.retime_words(words, caps, ["uno dos tres cuatro"])
    assert [w["text"] for w in out] == ["uno", "dos", "tres", "cuatro"]
    assert out[0]["start"] == 1.0
    assert all(b["start"] >= a["start"] for a, b in zip(out, out[1:]))
    assert all(w["end"] > w["start"] for w in out)
    assert out[-1]["end"] >= 2.3


def test_retime_words_without_original_words_spreads_evenly_and_caps_length():
    warns: list[str] = []
    out = i18n.retime_words([], [{"start": 0.0, "end": 0.5, "text": "x"}], ["una frase demasiado larga para medio segundo"], warns)
    assert len(out) == int(0.5 / i18n.MIN_WORD_S)
    assert warns and "se recorta" in warns[0]
    assert out[0]["start"] == 0.0 and out[-1]["end"] == pytest.approx(0.5, abs=1e-3)


def test_extract_with_captions_marks_residual_phrase(tmp_path):
    words = words_from("hola mundo cruel", start=0.5)
    write_json(tmp_path / "words.json", words)
    cp = write_json(tmp_path / "captions.json", [{"start": 0.0, "end": 0.24, "text": "frase de la que no queda nada"},
                                                    {"start": 0.3, "end": 0.7, "text": "frase anterior larga de la que solo queda hola"},
                                                    {"start": 0.85, "end": 1.6, "text": "mundo cruel"}])
    sb = {"overlays": [], "caption_style": {"preset": "pages", "words": "words.json"}, "meta": {"lang": "es"}}
    r = i18n.extract_with_captions(sb, cp)
    s = r["strings"]
    assert "note" not in s["captions.2.text"]
    assert s["captions.1.text"]["visible"] == "hola" and "solo se oye 'hola'" in s["captions.1.text"]["note"]
    assert s["captions.0.text"]["visible"] == "" and "no se oye" in s["captions.0.text"]["note"]
    assert s["captions.0.text"]["max_words"] == 2


def test_translate_project_end_to_end(tmp_path, grabado_short):
    sb = json.loads(json.dumps(grabado_short)); sb["brand"] = "think28"
    sbp = write_json(tmp_path / "storyboard.json", sb)
    write_json(tmp_path / "words.json", words_from("look at that", start=0.2))
    write_json(tmp_path / "captions.json", [{"start": 0.2, "end": 1.3, "text": "look at that"}])
    strings = {"lang": "es", "strings": {"hook.lines.0": {"text": "Mira esto"}, "captions.0.text": {"text": "mira eso"}}}
    sp = write_json(tmp_path / "strings.es.json", strings)
    r = i18n.translate_project(sbp, sp, "es")
    out = json.loads((tmp_path / "storyboard.es.json").read_text(encoding="utf-8"))
    assert out["meta"]["lang"] == "es" and out["caption_style"]["words"] == "words.es.json"
    ws = json.loads((tmp_path / "words.es.json").read_text(encoding="utf-8"))
    assert [w["text"] for w in ws] == ["mira", "eso"] and r["words_count"] == 2
    assert validate(out) == []


def test_density_warnings_flag_translations_too_dense_to_read():
    src = [{"start": 0.0, "end": 2.0, "text": "A short line."}, {"start": 2.0, "end": 3.0, "text": "Next one."}]
    tr = [{"start": 0.0, "end": 2.0, "text": "Una línea corta."},
          {"start": 2.0, "end": 3.0, "text": "La siguiente frase es bastante más larga que la original."}]
    w = i18n.density_warnings(src, tr)
    assert len(w) == 1 and w[0].startswith("captions.1:") and "condensa" in w[0]
    many = [{"start": float(i), "end": i + 1.0, "text": "x" * 40} for i in range(9)]
    w = i18n.density_warnings(many, many, show=3)
    assert len(w) == 4 and "6 subtítulos más" in w[-1]
    assert i18n.density_warnings(src, src) == []
