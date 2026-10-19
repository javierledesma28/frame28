"""motion: tokens de movimiento de la marca y anclas a la voz (F28-339)."""
from __future__ import annotations

import pytest

from frame28 import motion
from conftest import write_json

WORDS = [
    {"text": "Vamos", "start": 2.86, "end": 3.16}, {"text": "a", "start": 3.16, "end": 3.40},
    {"text": "ver", "start": 3.40, "end": 3.90}, {"text": "los", "start": 3.90, "end": 4.26},
    {"text": "distintos", "start": 4.26, "end": 4.58}, {"text": "componentes,", "start": 4.58, "end": 5.08},
    {"text": "por", "start": 6.76, "end": 7.30}, {"text": "aquí", "start": 7.30, "end": 7.46},
    {"text": "por", "start": 8.20, "end": 8.62}, {"text": "aquí", "start": 8.62, "end": 8.90},
]


def _behind(**kw):
    return {"type": "behind", "id": "bh", "start": 2.7, "end": 7.5, "text": "DISTINTOS COMPONENTES", "matte": "a.webm", **kw}


def test_tokens_default_without_motion():
    t = motion.motion_tokens({})
    assert (t["enter"], t["exit"], t["blur"], t["ease_in"], t["ease_out"]) == (0.2, 1.2, 28, "power1.out", "sine.inOut")
    assert (t["exit_stagger"], t["kicker"], t["word_stagger"]) == (0.3, 0.5, 0.3)


def test_tokens_derive_from_brand_kit_and_explicit_wins():
    t = motion.motion_tokens({"motion": {"standard_ms": 240, "slow_ms": 400}})
    assert (t["enter"], t["kicker"]) == (0.24, 0.4)
    t = motion.motion_tokens({"motion": {"standard_ms": 240, "enter_ms": 150, "exit_ms": 900, "ease_out": "expo.out"}})
    assert (t["enter"], t["exit"], t["ease_out"]) == (0.15, 0.9, "expo.out")


@pytest.mark.parametrize("bad,frag", [
    ({"ease_in": 'power1.out"); alert(1); ("'}, "ease_in: curva de GSAP no válida"),
    ({"exit_ms": 10}, "exit_ms: número entre"),
    ({"enter_ms": "200"}, "enter_ms: número entre"),
    ({"blur": 3}, "token desconocido"),
    ({"mode": "promocional"}, "token desconocido"),
    ({"style": "frenético"}, "style: sober, editorial, promotional"),
    ({"avoid": ["humo"]}, "avoid: lista de efectos"),
])
def test_motion_errors(bad, frag):
    assert any(frag in e for e in motion.motion_errors(bad))


def test_motion_errors_accepts_real_curves():
    assert motion.motion_errors({"ease_in": "back.out(1.7)", "ease_out": "none", "style": "promotional", "fast_ms": 120,
                                 "avoid": ["behind", "camera"]}) == []
    assert motion.motion_tokens({"motion": {"style": "sober", "avoid": ["camera"]}})["avoid"] == ["camera"]
    assert motion.motion_errors(None) == []
    assert motion.motion_errors([1]) and "objeto" in motion.motion_errors([1])[0]


def test_norm_and_phrase_tokens():
    assert motion.norm("¿Componentes?") == "componentes" and motion.norm("AQUÍ") == "aqui"
    assert motion.phrase_tokens("3 CLAVES|PARA  VENDER") == ["3", "CLAVES", "PARA", "VENDER"]


def test_word_anchor_resolves_with_lead_and_end_of_word():
    sb = {"overlays": [{"type": "box", "id": "b", "start": "word:distintos", "end": "word:componentes", "at": "word:componentes",
                        "x": 0, "y": 0, "text": "t"}]}
    out, errs = motion.resolve_anchors(sb, WORDS)
    o = out["overlays"][0]
    assert errs == []
    assert (o["start"], o["end"], o["at"]) == (4.22, 5.08, 4.54)
    assert sb["overlays"][0]["start"] == "word:distintos"     # no toca el original


def test_word_anchor_sequence_and_occurrence():
    out, errs = motion.resolve_anchors({"overlays": [{"id": "a", "start": "word:por aquí#2", "end": 9.5}]}, WORDS)
    assert errs == [] and out["overlays"][0]["start"] == 8.16


def test_ambiguous_word_uses_overlay_window_or_errors():
    ok, errs = motion.resolve_anchors({"overlays": [{"id": "a", "start": 8.4, "end": 9.5, "at": "word:aquí"}]}, WORDS)
    assert errs == [] and ok["overlays"][0]["at"] == 8.58
    _, errs = motion.resolve_anchors({"overlays": [{"id": "a", "start": 6.0, "end": 9.5, "at": "word:aquí"}]}, WORDS)
    assert len(errs) == 1 and "se dice 2 veces" in errs[0] and "word:aqui#n" in errs[0]


def test_missing_word_is_an_error_with_suggestions_never_a_time():
    out, errs = motion.resolve_anchors({"overlays": [{"id": "a", "start": "word:componente", "end": 6}]}, WORDS)
    assert out["overlays"][0]["start"] == "word:componente"
    assert "no se dice" in errs[0] and "componentes" in errs[0]
    _, errs = motion.resolve_anchors({"overlays": [{"id": "a", "start": "word:por#3", "end": 9}]}, WORDS)
    assert "#3 no existe" in errs[0]


def test_words_at_auto_finds_the_phrase_in_the_window():
    out, errs = motion.resolve_anchors({"overlays": [_behind(words_at="auto", kicker={"text": "LOS"})]}, WORDS)
    o = out["overlays"][0]
    assert errs == []
    assert o["words_at"] == [4.22, 4.54]
    assert o["kicker"]["at"] == 3.72                           # «auto»: medio segundo antes de la primera palabra


def test_words_at_auto_with_explicit_anchors_and_kicker_anchor():
    sb = {"overlays": [_behind(words_at=["word:distintos", 4.6], kicker={"text": "Vamos a ver", "at": "word:vamos"})]}
    out, errs = motion.resolve_anchors(sb, WORDS)
    assert errs == [] and out["overlays"][0]["words_at"] == [4.22, 4.6] and out["overlays"][0]["kicker"]["at"] == 2.82


def test_words_at_auto_missing_word_says_what_is_heard():
    _, errs = motion.resolve_anchors({"overlays": [_behind(text="3 COMPONENTES", words_at="auto")]}, WORDS)
    assert len(errs) == 1 and "no encuentra «3»" in errs[0] and "se oye" in errs[0] and "distintos" in errs[0]


def test_anchors_without_words_file(tmp_path):
    sb = {"overlays": [_behind(words_at="auto")]}
    assert motion.has_anchors(sb) and not motion.has_anchors({"overlays": [_behind(words_at=[4.2, 4.5])]})
    _, errs = motion.resolve_storyboard(sb, tmp_path)
    assert errs and "no hay words.json" in errs[0]
    write_json(tmp_path / "w.json", WORDS)
    out, errs = motion.resolve_storyboard({**sb, "words": "w.json"}, tmp_path)
    assert errs == [] and out["overlays"][0]["words_at"] == [4.22, 4.54]


def test_words_path_order(tmp_path):
    assert motion.words_path({"words": "a.json", "caption_style": {"words": "b.json"}}, tmp_path).name == "a.json"
    assert motion.words_path({"caption_style": {"words": "b.json"}}, tmp_path).name == "b.json"
    assert motion.words_path({}, tmp_path).name == "words.json"


def test_spread_keeps_the_original_instants():
    assert motion.spread([4.2, 4.5], 1) == [4.2]
    assert motion.spread([4.2, 4.5], 3) == [4.2, 4.2, 4.5] or motion.spread([4.2, 4.5], 3) == [4.2, 4.5, 4.5]
    assert motion.spread([4.2], 2) == [4.2, 4.2] and motion.spread([], 2) == []
