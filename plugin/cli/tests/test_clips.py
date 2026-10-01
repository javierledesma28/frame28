"""clips: tramos por momentos de venta, ganchos con la frase real y storyboard de partida del short."""
from __future__ import annotations

import json

from frame28 import clips
from frame28.build import validate
from conftest import words_from, write_json

CAPS_EN = [
    (0.0, 4.0, "Hi everyone, welcome to another tutorial where we break engraving down into simple steps."),
    (4.0, 9.0, "People always ask me things like, isn't glass too slippery, what if it cracks?"),
    (9.0, 14.0, "Today we are engraving a wine glass with the Engraver."),
    (14.0, 19.0, "Set the speed to 3 and use the diamond tip."),
    (19.0, 24.0, "Follow the outline slowly, no pressure at all."),
    (24.0, 29.0, "And that's it, look at that, beautiful."),
    (29.0, 34.0, "Anyone can do this in 20 minutes."),
    (34.0, 40.0, "Thanks for watching and see you next time."),
]


def _caps(tmp_path, rows=CAPS_EN):
    return write_json(tmp_path / "captions.json", [{"text": t, "start": s, "end": e} for s, e, t in rows])


def test_plan_finds_moments_and_non_overlapping_clips(tmp_path):
    r = clips.plan(_caps(tmp_path), target=30, count=3, lang="en", keywords=["Engraver"])
    assert r["moments"] >= 5
    kinds = {m["kind"] for c in r["clips"] for m in c["moments"]}
    assert {"objection", "result", "promise", "product"} <= kinds
    assert r["clips"], "debe elegir al menos un tramo"
    for c in r["clips"]:
        assert 15.0 <= c["duration"] <= 45.0
        assert c["id"].startswith("s") and len(c["hooks"]) == 3
        # empieza y termina en frase
        assert any(abs(c["start"] - s) < 1e-6 for s, _, _ in CAPS_EN)
        assert any(abs(c["end"] - e) < 1e-6 for _, e, _ in CAPS_EN)
    for a, b in zip(r["clips"], r["clips"][1:]):
        assert b["start"] >= a["end"] - 3


def test_hooks_use_real_words_and_fit_two_lines(grabado_clips):
    for c in grabado_clips["clips"]:
        hooks = clips.hooks_for(c, "en")
        assert 1 <= len(hooks) <= 3
        assert len({h["type"] for h in hooks}) == len(hooks)
        for h in hooks:
            assert 1 <= len(h["lines"]) <= 2
            for line in h["lines"]:
                assert len(line.split()) <= clips.MAX_LINE_WORDS
                assert len(line) <= clips.MAX_LINE_CHARS
            if h["type"] != "curiosity":
                assert h["quote"] and h["t"] >= c["start"] - 0.5


def test_hooks_objection_ends_with_question_and_answer(tmp_path):
    r = clips.plan(_caps(tmp_path), target=30, count=1, lang="en")
    h = next(h for h in r["clips"][0]["hooks"] if h["type"] == "objection")
    assert h["lines"][0].endswith("?")
    assert h["lines"][0].lower().startswith("isn't glass")
    assert len(h["lines"]) == 2


def test_clean_removes_leading_fillers_and_hedges():
    assert clips._clean("and i think just this is great", "en") == "This is great"
    assert clips._clean("bueno, pues queda precioso", "es") == "Queda precioso"
    assert clips._clean("it's really pretty easy", "en") == "It's easy"


def test_two_lines_limits_and_natural_break():
    lines = clips._two_lines("Set the speed to three and use the diamond tip today")
    assert len(lines) == 2
    for line in lines:
        assert len(line.split()) <= clips.MAX_LINE_WORDS and len(line) <= clips.MAX_LINE_CHARS
    assert clips._two_lines("Short one") == ["Short one"]
    # sin corte válido: recorta a palabras enteras
    lines = clips._two_lines("abcdef ghijkl mnopqr stuvwx yzabcd efghij klmnop qrstuv")
    assert len(lines) == 2 and all(len(line) <= clips.MAX_LINE_CHARS for line in lines)


def test_trim_trailing_stopwords():
    assert clips._trim_trailing("engrave it with the", "en") == "engrave it"
    assert clips._trim_trailing("queda precioso en tu", "es") == "queda precioso"


def test_hooks_without_moments_use_the_strongest_phrase():
    clip = {"id": "s9", "start": 10.0, "end": 40.0, "moments": [], "phrases": [
        "so today we are going to talk about the general setup of the workshop and the tools that we use every single day",
        "Have you ever wondered why your lines come out crooked?",
        "we clean the table.",
    ]}
    hooks = clips.hooks_for(clip, "en")
    assert hooks[0]["type"] == "statement"
    assert hooks[0]["lines"][0].lower().startswith("have you ever wondered")
    assert hooks[0]["quote"].startswith("Have you ever") and hooks[0]["t"] == 10.0
    assert all(len(line) <= clips.MAX_LINE_CHARS for line in hooks[0]["lines"])
    assert hooks[-1]["type"] == "curiosity"  # la plantilla sigue de relleno hasta tres
    assert clips.strongest_phrase({"phrases": []}, "en") is None
    assert clips.hooks_for({"id": "x", "start": 0, "moments": [], "phrases": []}, "es")[0]["type"] == "curiosity"


def test_batch_builds_a_project_per_hook_without_rendering(tmp_path, grabado_clips):
    clip = grabado_clips["clips"][0]
    cdir = tmp_path / "clips"; d = cdir / clip["id"]; d.mkdir(parents=True)
    (d / "clip.mp4").write_bytes(b"")  # basta con que exista: sin render no se abre
    write_json(d / "words.json", words_from("look at that", start=1.0))
    plan = write_json(tmp_path / "clips.json", {"clips": [clip, {**clip, "id": "s2"}]})
    r = clips.batch(plan, None, cdir, tmp_path / "out", None, brand="think28", render=False)
    assert r["skipped"] == ["s2"] and not r["rendered"]
    assert len(r["variants"]) == len(clip["hooks"]) and r["ok"] == len(clip["hooks"])
    for k, v in enumerate(r["variants"]):
        assert v["name"] == f"{clip['id']}-hook{k}" and v["hook"] == clip["hooks"][k]["lines"]
        sb = json.loads((d / f"storyboard-hook{k}.json").read_text(encoding="utf-8"))
        assert validate(sb) == [] and sb["overlays"][0]["lines"] == clip["hooks"][k]["lines"]
        assert (d / f"project-hook{k}" / "index.html").exists()
    manifest = json.loads((cdir / "batch.json").read_text(encoding="utf-8"))
    assert manifest["ok"] == r["ok"]
    only = clips.batch(plan, [clip["id"]], cdir, tmp_path / "out", [1], brand="think28", render=False)
    assert [v["hook_index"] for v in only["variants"]] == [1]


def test_scaffold_writes_a_storyboard_that_validates(tmp_path, grabado_clips):
    clip = grabado_clips["clips"][0]
    d = tmp_path / "s1"; d.mkdir()
    write_json(d / "words.json", words_from("hola mundo cruel", start=0.5))
    (tmp_path / "brands").mkdir()
    brand = write_json(tmp_path / "brands" / "acme.json", {"name": "acme"})
    r = clips.scaffold(clip, d, brand=str(brand), cta={"title": "Buy", "url": "https://acme.test"}, hook_index=1, video_name="vertical.mp4")
    sb = json.loads((d / "storyboard.json").read_text(encoding="utf-8"))
    assert validate(sb) == []
    assert sb["source"]["video"] == "vertical.mp4" and sb["platform"] == "tiktok"
    assert sb["canvas"] == {"width": 1080, "height": 1920, "fps": 30}
    assert sb["overlays"][0]["type"] == "hook" and sb["overlays"][0]["lines"] == clip["hooks"][1]["lines"]
    assert sb["overlays"][-1]["type"] == "cta" and sb["overlays"][-1]["end"] == sb["duration"]
    assert sb["brand"] == "../brands/acme.json"  # relativa al storyboard del short
    assert r["duration"] == sb["duration"] >= clip["end"] - clip["start"]
