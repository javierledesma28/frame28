"""log: cada orden del CLI se cronometra y se apunta; `report` agrupa; `report note` añade lo que el CLI no mide."""
from __future__ import annotations

import json
import sys

import click
from click.testing import CliRunner

from frame28 import log as L
from frame28.cli import main
from conftest import write_json


def test_command_path_follows_groups():
    assert L.command_path(main, ["cut", "plan", "w.json", "-o", "c.json"]) == "cut plan"
    assert L.command_path(main, ["--json", "doctor"]) == "doctor"
    assert L.command_path(main, ["captions", "pages", "w.json"]) == "captions pages"
    assert L.command_path(main, ["--version"]) == ""
    assert L.command_path(main, ["report", "note", "hola"]) == "report note"


def test_record_and_report_roundtrip(tmp_path):
    p = tmp_path / "log.jsonl"
    L.record("cut plan", ["cut", "plan", "w.json"], 1.25, True, path=p)
    L.record("cut plan", ["cut", "plan", "w.json"], 0.75, False, error="boom", path=p)
    L.record("build", ["build", "s.json"], 3.0, True, path=p)
    L.add_note("director: montaje del largo", tokens=12000, minutes=20, path=p)
    r = L.report(p, rate=60.0)
    assert r["entries"] == 4 and r["total_seconds"] == 5.0
    assert r["commands"]["build"] == {"runs": 1, "seconds": 3.0, "failed": 0}
    assert r["commands"]["cut plan"] == {"runs": 2, "seconds": 2.0, "failed": 1}
    assert list(r["commands"]) == ["build", "cut plan"]  # ordenado por tiempo
    assert r["tokens"] == 12000 and r["review_minutes"] == 20
    assert r["machine_cost"] == round(5.0 / 3600 * 60, 2) and r["estimated_cost"] == round(r["machine_cost"] + 20 / 60 * 60, 2)
    txt = L.format_report(r)
    assert "cut plan" in txt and "1 con error" in txt and "tokens anotados: 12.000" in txt


def test_report_without_log(tmp_path):
    r = L.report(tmp_path / "nada.jsonl")
    assert r["entries"] == 0 and r["commands"] == {}
    assert "sin órdenes" in L.format_report(r)


def test_cli_commands_are_logged(tmp_path, javier_words, monkeypatch):
    p = tmp_path / "log.jsonl"
    monkeypatch.setenv(L.LOG_ENV, str(p))
    monkeypatch.setattr(sys, "argv", ["frame28", "captions", "pages", str(javier_words), "--json"])
    r = CliRunner().invoke(main, ["captions", "pages", str(javier_words), "--json"])
    assert r.exit_code == 0
    entries = [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines()]
    assert len(entries) == 1 and entries[0]["cmd"] == "captions pages" and entries[0]["ok"] and entries[0]["s"] >= 0
    # una orden que falla queda apuntada como error
    bad = write_json(tmp_path / "bad.json", [{"text": "x"}])
    monkeypatch.setattr(sys, "argv", ["frame28", "cut", "plan", str(bad), "-o", str(tmp_path / "c.json")])
    CliRunner().invoke(main, ["cut", "plan", str(bad), "-o", str(tmp_path / "c.json")])
    entries = [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines()]
    assert entries[-1]["cmd"] == "cut plan" and not entries[-1]["ok"] and "TranscriptFormatError" in entries[-1]["error"]
    # report no se registra a sí mismo y suma lo anterior
    monkeypatch.setattr(sys, "argv", ["frame28", "report", "--json"])
    r = CliRunner().invoke(main, ["report", "--log", str(p), "--json"])
    assert r.exit_code == 0, r.output
    rep = json.loads(r.output)
    assert rep["entries"] == 2 and set(rep["commands"]) == {"captions pages", "cut plan"}
    r = CliRunner().invoke(main, ["report", "--log", str(p), "note", "tokens del director", "--tokens", "5000"])
    assert r.exit_code == 0, r.output
    assert L.report(p)["tokens"] == 5000


def test_help_and_unlogged_commands_leave_no_trace(tmp_path, monkeypatch):
    p = tmp_path / "log.jsonl"
    monkeypatch.setenv(L.LOG_ENV, str(p))
    for argv in (["clips", "batch", "--help"], ["doctor", "--help"], ["brand", "list"], ["storyboard", "schema"]):
        monkeypatch.setattr(sys, "argv", ["frame28", *argv])
        r = CliRunner().invoke(main, argv)
        assert r.exit_code == 0, (argv, r.output)
    assert not p.exists()


def test_log_disabled_with_env_zero(monkeypatch):
    monkeypatch.setenv(L.LOG_ENV, "0")
    assert L.log_path() is None
    monkeypatch.delenv(L.LOG_ENV)
    assert L.log_path() is not None and L.log_path().name == "log.jsonl"
