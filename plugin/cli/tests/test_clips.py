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


CAPS_RESULT = [
    (0.0, 5.0, "Hi everyone, today we are engraving a wine glass with the Engraver."),
    (5.0, 9.0, "Anyone can do this, it's really easy."),
    (9.0, 14.0, "Set the speed to 3 and use the diamond tip."),
    (14.0, 19.0, "Follow the outline slowly, no pressure at all."),
    (19.0, 24.0, "And that's it, look at that, beautiful."),
    (24.0, 28.0, "Perfect, it turned out great."),
    (28.0, 34.0, "Thanks for watching and see you next time."),
]


def _sb_with(overlays, duration=34.0, canvas=(1920, 1080)):
    return {"version": 1, "source": {"video": "clip.mp4", "duration": duration}, "duration": duration,
            "canvas": {"width": canvas[0], "height": canvas[1], "fps": 30}, "overlays": overlays}


def test_markers_group_a_result_streak_and_propose_the_three_overlays(tmp_path):
    r = clips.markers(_caps(tmp_path, CAPS_RESULT), lang="en")
    assert r["results"] == 1 and r["promises"] == 1 and r["duration"] == 34.0
    res = next(m for m in r["markers"] if m["kind"] == "result")
    assert res["t"] == 19.0 and res["end"] == 28.0 and len(res["phrases"]) == 2  # "that's it" + "perfect" = una racha
    types = [o["type"] for o in res["overlays"]]
    assert types == ["kinetic", "draw", "before_after"]
    kin, chk, ba = res["overlays"]
    assert kin["lines"][0][0]["text"].lower() == "that's" and kin["lines"][0][0]["accent"] is True
    assert kin["start"] == 18.95 and kin["end"] <= ba["start"] and kin["end"] <= 24.6
    assert chk["icon"] == "check" and chk["at"] == 19.0 and chk["end"] == 20.6
    assert ba["before_t"] == 11.0 and ba["after_t"] < ba["start"] and ba["end"] - ba["start"] == 3.0 and ba["end"] <= 34.0
    assert ba["label_before"] == "Before"
    prom = next(m for m in r["markers"] if m["kind"] == "promise")
    assert [o["type"] for o in prom["overlays"]] == ["kinetic"] and prom["overlays"][0]["id"] == "prom1-kin"
    # todo lo propuesto es un storyboard válido tal cual, en 16:9 y en vertical
    all_ov = [o for m in r["markers"] for o in m["overlays"]]
    assert validate(_sb_with(all_ov)) == []
    v = clips.markers(_caps(tmp_path, CAPS_RESULT), lang="en", canvas=(1080, 1920))
    v_ov = [o for m in v["markers"] for o in m["overlays"]]
    assert validate(_sb_with(v_ov, canvas=(1080, 1920))) == []
    assert all(o["x"] + o.get("w", 0) <= 1080 for o in v_ov) and all(o["y"] < 500 for o in v_ov)
    left = clips.markers(_caps(tmp_path, CAPS_RESULT), lang="en", side="left")
    assert left["markers"][0]["overlays"][0]["x"] == 90 and r["markers"][0]["overlays"][0]["x"] == 1100


def test_markers_take_word_times_from_words_json_and_respect_lead(tmp_path):
    words = write_json(tmp_path / "words.json", words_from("and|19.2 that's|19.6 it|20.1 look|20.5 at that beautiful"))
    r = clips.markers(_caps(tmp_path, CAPS_RESULT), lang="en", words_path=words, lead=3.0, settle=0.5)
    res = next(m for m in r["markers"] if m["kind"] == "result")
    kin, chk, ba = res["overlays"]
    assert [w["at"] for w in kin["lines"][0]] == [19.6, 20.1]  # "That's it" con los tiempos reales
    assert chk["at"] == 19.6 and kin["start"] == 19.55
    assert ba["before_t"] == 16.0 and ba["start"] == 28.5 and ba["after_t"] == 28.45


def test_markers_spanish_labels_and_no_results(tmp_path):
    caps = _caps(tmp_path, [(0.0, 4.0, "Hoy grabamos una copa."), (4.0, 8.0, "Y ya está, mira qué precioso queda."), (8.0, 10.0, "Hasta luego.")])
    r = clips.markers(caps, lang="es")
    res = r["markers"][-1]
    assert res["kind"] == "result" and res["overlays"][-1]["label_before"] == "Antes"
    assert res["overlays"][-1]["end"] <= 10.0 and res["overlays"][-1]["end"] - res["overlays"][-1]["start"] >= 1.5
    empty = clips.markers(_caps(tmp_path, [(0.0, 3.0, "Hola."), (3.0, 6.0, "Adiós.")]), lang="es")
    assert empty["markers"] == [] and empty["results"] == 0


# ---------- día 6: frases completas, patrones de resultado, CTA en la franja libre y lote sin regenerar ----------
def test_plan_and_markers_work_on_whole_sentences_even_if_captions_split_mid_sentence(tmp_path):
    # captions.json troceado como los segmentos de Whisper: ninguna entrada empieza ni acaba en frase
    caps = [{"start": 0.0, "end": 5.0, "text": "Welcome to the workshop today we paint"},
            {"start": 5.0, "end": 10.0, "text": "a small box. This part is easy and"},
            {"start": 10.0, "end": 15.0, "text": "anyone can do it. Sand every side"},
            {"start": 15.0, "end": 20.0, "text": "slowly. That is it, look at that"},
            {"start": 20.0, "end": 25.0, "text": "finish. See you next time."}]
    p = write_json(tmp_path / "captions.json", caps)
    old = clips.plan(p, target=20, count=2, lang="en", min_len=10, max_len=30)
    assert old["clips"] and "a mitad de frase" in old["note"]                    # transcripción antigua: como antes, con aviso
    wp = write_json(tmp_path / "words.json", words_from(" ".join(c["text"] for c in caps)))
    plan = clips.plan(p, target=6, count=2, lang="en", min_len=3, max_len=12, words_path=wp)
    assert plan["clips"] and "note" not in plan
    for c in plan["clips"]:
        assert c["phrases"][0][0].isupper() and c["phrases"][-1].rstrip()[-1] in ".!?"
    from frame28.captions import load_words, phrase_captions
    newp = write_json(tmp_path / "captions.new.json", phrase_captions(load_words(wp)))   # lo que escribe `transcribe`
    m = clips.markers(newp, lang="en", words_path=wp)
    assert m["markers"] and all(x["phrase"].rstrip()[-1] in ".!?" for x in m["markers"])
    again = clips.plan(newp, target=6, count=2, lang="en", min_len=3, max_len=12)
    assert "note" not in again and [c["start"] for c in again["clips"]] == [c["start"] for c in plan["clips"]]


def test_result_patterns_skip_future_done_and_perfect_for():
    def kinds(text):
        return {m["kind"] for m in clips._moments([{"start": 0.0, "end": 3.0, "text": text}], "en", [])}

    assert "result" not in kinds("Every stroke shows up when you're done.")
    assert "result" not in kinds("Pine is perfect for this kind of project.")
    assert "result" in kinds("Once the lid is done the box looks great.")
    assert "result" in kinds("That's it, perfect!")


def test_scaffold_puts_the_cta_in_the_free_top_band_of_a_blur_reframe(tmp_path, grabado_clips):
    clip = grabado_clips["clips"][0]
    d = tmp_path / "s1"; d.mkdir()
    write_json(d / "words.json", words_from("hola mundo cruel", start=0.5))
    cta = {"title": "Buy", "price": "$10"}
    clips.scaffold(clip, d, cta=cta, video_name="vertical.mp4")
    assert "y" not in json.loads((d / "storyboard.json").read_text(encoding="utf-8"))["overlays"][-1]   # sin reframe.json: por defecto
    write_json(d / "reframe.json", {"mode": "blur", "out": [1080, 1920], "free_bands": [[0, 656], [1264, 1920]]})
    clips.scaffold(clip, d, cta=cta, video_name="vertical.mp4")
    c = json.loads((d / "storyboard.json").read_text(encoding="utf-8"))["overlays"][-1]
    assert c["type"] == "cta" and int(0.08 * 1920) < c["y"] and c["y"] + clips.CTA_HEIGHT <= 656      # dentro de la franja y bajo la barra
    clips.scaffold(clip, d, cta={**cta, "y": 900}, video_name="vertical.mp4")
    assert json.loads((d / "storyboard.json").read_text(encoding="utf-8"))["overlays"][-1]["y"] == 900  # el del usuario manda
    write_json(d / "reframe.json", {"mode": "crop", "out": [1080, 1920]})
    assert clips._free_band_y(d, 1080, 1920) is None


def test_batch_keep_renders_hand_tuned_storyboards_without_rescaffolding(tmp_path, grabado_clips):
    clip = grabado_clips["clips"][0]
    cdir = tmp_path / "clips"; d = cdir / clip["id"]; d.mkdir(parents=True)
    (d / "clip.mp4").write_bytes(b"")
    write_json(d / "words.json", words_from("look at that", start=1.0))
    plan = write_json(tmp_path / "clips.json", {"clips": [clip]})
    clips.batch(plan, None, cdir, tmp_path / "out", [0], brand="think28", render=False)
    sp = d / "storyboard-hook0.json"
    sb = json.loads(sp.read_text(encoding="utf-8"))
    sb["overlays"].append({"type": "box", "id": "mio", "start": 1.0, "end": 2.0, "x": 90, "y": 470, "text": "Afinado a mano"})
    write_json(sp, sb)
    kept = clips.batch(plan, None, cdir, tmp_path / "out", [0], brand="think28", render=False, keep=True)
    assert kept["variants"][0]["kept"] and kept["variants"][0]["ok"]
    assert any(o["id"] == "mio" for o in json.loads(sp.read_text(encoding="utf-8"))["overlays"])
    assert "Afinado a mano" in (d / "project-hook0" / "index.html").read_text(encoding="utf-8")
    clips.batch(plan, None, cdir, tmp_path / "out", [0], brand="think28", render=False)
    assert not any(o["id"] == "mio" for o in json.loads(sp.read_text(encoding="utf-8"))["overlays"])     # sin keep, se regenera
