"""Smoke del CLI (click.testing): las órdenes puras responden, --json es JSON y los errores de formato son cortos."""
from __future__ import annotations

import json

from click.testing import CliRunner

from frame28 import __version__
from frame28.captions import TranscriptFormatError
from frame28.cli import main
from conftest import POC, words_from, write_json


def run(*args):
    return CliRunner().invoke(main, [str(a) for a in args], catch_exceptions=False)


def test_version():
    r = run("--version")
    assert r.exit_code == 0 and __version__ in r.output


def test_storyboard_validate_and_schema():
    r = run("storyboard", "validate", POC / "clip-javier" / "storyboard-gsap.json")
    assert r.exit_code == 0 and "Storyboard válido" in r.output
    r = run("storyboard", "schema")
    assert r.exit_code == 0 and "pointer" in r.output


def test_storyboard_validate_fails_with_list(tmp_path):
    p = write_json(tmp_path / "sb.json", {"version": 1, "source": {"video": "v", "duration": 1}, "overlays": [{"type": "box", "id": "b", "start": 0, "end": 2}]})
    r = CliRunner().invoke(main, ["storyboard", "validate", str(p)])
    assert r.exit_code == 1 and "supera la duración" in r.output


def test_captions_pages_and_export(tmp_path, javier_words):
    r = run("captions", "pages", javier_words, "--json")
    pages = json.loads(r.output)
    assert r.exit_code == 0 and pages and all(len(p["words"]) <= 4 for p in pages)
    r = run("captions", "export", javier_words, "-o", tmp_path / "s.srt", "--json")
    assert r.exit_code == 0 and json.loads(r.output)["cues"] >= 1 and (tmp_path / "s.srt").exists()


def test_cut_plan_writes_json_and_short_error_on_bad_input(tmp_path, javier_words):
    r = run("cut", "plan", javier_words, "-o", tmp_path / "cuts.json")
    assert r.exit_code == 0
    cuts = json.loads((tmp_path / "cuts.json").read_text(encoding="utf-8"))
    assert cuts["keep"] and cuts["result_duration"] <= cuts["source_duration"]
    bad = write_json(tmp_path / "bad.json", [{"text": "x"}])
    r = CliRunner().invoke(main, ["cut", "plan", str(bad), "-o", str(tmp_path / "c.json")])
    assert r.exit_code != 0
    # el punto de entrada `cli:run` lo convierte en "Error: …" y exit 2, sin traza
    assert isinstance(r.exception, TranscriptFormatError) and "start/end" in str(r.exception)


def test_clips_plan_and_scaffold(tmp_path):
    cp = write_json(tmp_path / "captions.json", [{"start": 0, "end": 8, "text": "Isn't glass too slippery? Not at all."},
                                                    {"start": 8, "end": 16, "text": "Set the speed to 3 and go slowly."},
                                                    {"start": 16, "end": 24, "text": "And that's it, look at that, beautiful."}])
    r = run("clips", "plan", cp, "--lang", "en", "-o", tmp_path / "clips.json", "--json")
    assert r.exit_code == 0
    plan = json.loads((tmp_path / "clips.json").read_text(encoding="utf-8"))
    assert plan["clips"] and plan["clips"][0]["id"] == "s1"
    d = tmp_path / "clips" / "s1"; d.mkdir(parents=True)
    write_json(d / "words.json", words_from("look at that", start=16.0))
    r = run("clips", "scaffold", tmp_path / "clips.json", "s1", "--dir", d, "--brand", "think28", "--json")
    assert r.exit_code == 0, r.output
    assert (d / "storyboard.json").exists()


def test_reframe_map_points_and_gestures(tmp_path):
    res = write_json(tmp_path / "reframe.json", {"mode": "crop", "source": [1920, 1080], "out": [1080, 1920], "crop": [608, 1080], "path": [[0.0, 960.0]]})
    r = run("reframe-map", res, "--point", "960,540,0.5", "--point", "100,540,0.5", "--json")
    assert r.exit_code == 0
    pts = json.loads(r.output)["points"]
    assert pts[0]["out"] == [540, 960] and pts[0]["visible"] and not pts[1]["visible"]
    g = write_json(tmp_path / "gestures.json", {"canvas": [1920, 1080], "events": [], "pointer_suggestions": [
        {"id": "p1", "type": "pointer", "start": 0.4, "end": 1.6, "at": 0.5, "dot": [960, 540], "box": [1050, 330], "text": "aquí", "confidence": "high"}]})
    r = run("reframe-map", res, "--gestures", g, "-o", tmp_path / "vertical.json")
    assert r.exit_code == 0 and "p1" in r.output and "fuera del encuadre" not in r.output
    assert json.loads((tmp_path / "vertical.json").read_text(encoding="utf-8"))["pointer_suggestions"][0]["visible"]
    r = CliRunner().invoke(main, ["reframe-map", str(res)])
    assert r.exit_code == 2 and "--gestures" in r.output


def test_i18n_extract_and_apply(tmp_path, grabado_short):
    sbp = write_json(tmp_path / "storyboard.json", {**grabado_short, "brand": "think28"})
    r = run("i18n", "extract", sbp, "-o", tmp_path / "strings.json")
    assert r.exit_code == 0, r.output
    data = json.loads((tmp_path / "strings.json").read_text(encoding="utf-8"))
    assert "hook.lines.0" in data["strings"]
    data["strings"]["hook.lines.0"]["text"] = "De cero a esto"
    write_json(tmp_path / "strings.es.json", data)
    r = run("i18n", "apply", sbp, tmp_path / "strings.es.json", "--lang", "es", "--json")
    assert r.exit_code == 0, r.output
    out = json.loads((tmp_path / "storyboard.es.json").read_text(encoding="utf-8"))
    assert out["meta"]["lang"] == "es" and out["overlays"][0]["lines"][0] == "De cero a esto"


def test_brand_list_and_broll_providers():
    r = run("brand", "list")
    assert r.exit_code == 0 and "think28" in r.output
    r = run("broll", "providers")
    assert r.exit_code == 0 and "pexels" in r.output.lower()
