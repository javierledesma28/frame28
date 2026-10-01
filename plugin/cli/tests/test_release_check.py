"""Fila de confidencialidad de `scripts/release-check.py`: términos de un fichero privado, sitios sin el término.

Regresión de la 0.4.0: el nombre de un cliente se limpió del árbol y del historial, pero seguía en las notas de una
release publicada y en una carpeta sin ignorar dentro del repo.
"""
from __future__ import annotations

import importlib.util

import pytest


@pytest.fixture(scope="module")
def rc(repo):
    spec = importlib.util.spec_from_file_location("release_check", repo / "scripts" / "release-check.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_patterns_file(rc, tmp_path):
    assert rc.load_patterns(tmp_path / "no-existe.txt") is None
    p = tmp_path / "confidencial.txt"
    p.write_text("# comentario\n\n", encoding="utf-8")
    assert rc.load_patterns(p) is None
    p.write_text("# cliente\nAcme Corp\n\\bzed\\b\n", encoding="utf-8")
    rx = rc.load_patterns(p)
    assert rx.search("vídeo de ACME corp") and rx.search("hola Zed.")
    assert not rx.search("zedillo") and not rx.search("Cliente A")


def test_find_hits_reports_places_not_terms(rc, tmp_path):
    p = tmp_path / "confidencial.txt"
    p.write_text("acme\n", encoding="utf-8")
    rx = rc.load_patterns(p)
    hits = rc.find_hits(
        rx,
        files={"README.md": "nada", "docs/caso.md": "probado con Acme", "bajado/propuesta-acme.md": "privado"},
        log="@@commit aaa1111\nmensaje limpio\n+linea limpia\n@@commit bbb2222\nBorrador para ACME\n-acme otra vez\n",
        tags={"v0.1.0": "Frame28 v0.1.0", "v0.2.0": "caso Acme"},
        releases={"v0.3.0": "Frame28 v0.3.0\nProbado con una marca (Acme, 3 min)", "v0.4.0": "limpia"},
    )
    assert hits == {
        "ficheros": ["docs/caso.md", "bajado/propuesta-***.md"],
        "commits": ["bbb2222"],
        "tags": ["v0.2.0"],
        "releases": ["v0.3.0"],
    }
    assert "acme" not in repr(hits).lower()


def test_find_hits_clean(rc, tmp_path):
    p = tmp_path / "confidencial.txt"
    p.write_text("acme\n", encoding="utf-8")
    assert rc.find_hits(rc.load_patterns(p), {"a.md": "Cliente A"}, "@@commit abc\nlimpio\n", {"v1": "ok"}, {"v1": "ok"}) == {}


def test_json_stream_concatenated_pages(rc):
    assert rc._json_stream('[{"a": 1}]\n[{"a": 2}]') == [{"a": 1}, {"a": 2}]
    assert rc._json_stream('{"description": "x"}') == [{"description": "x"}]
