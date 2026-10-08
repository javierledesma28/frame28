"""F28-238: todos los sitios que explican cómo entrar con la cuenta de Frame28 dan el mismo camino, que sirve también en la
app de escritorio (allí `/mcp` no existe): `claude mcp login plugin:frame28:frame28` y una sesión nueva. Y ninguno manda
lanzar `mcp login` para comprobar: borra la sesión guardada en cuanto empieza."""
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
LOGIN = "mcp login plugin:frame28:frame28"
SKILLS = sorted((REPO / "plugin" / "skills").glob("*/SKILL.md"))


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def test_hay_nueve_skills():
    assert len(SKILLS) == 9 and (REPO / "plugin" / "skills" / "frame28" / "SKILL.md") in SKILLS


@pytest.mark.parametrize("skill", SKILLS, ids=lambda p: p.parent.name)
def test_skill_explica_la_entrada(skill):
    t = read(skill)
    assert t.startswith("---\nname: ") and "\ndescription: '" in t                  # descripción entre comillas simples
    assert f'"$CLAUDE_CODE_EXECPATH" {LOGIN}' in t and f"claude {LOGIN}" in t       # el agente en la app y el usuario
    assert "sesión nueva" in t and "No lances `mcp login` para comprobar" in t and "claude mcp list" in t
    assert "en la configuración del plugin" not in t                                 # la ruta de la app sin verificar


@pytest.mark.parametrize("rel, n", [("docs/instalar/index.html", 4), ("docs/instalar/en/index.html", 4), ("docs/instalar.md", 1),
                                    ("docs/install.ps1", 1), ("docs/install.sh", 1), ("README.md", 1)])
def test_docs_e_instaladores_dan_el_mismo_camino(rel, n):
    t = read(REPO / rel)
    assert t.count(f"claude {LOGIN}") == n
    assert "nueva" in t or "new" in t


def test_asistente_no_manda_solo_a_mcp():
    for rel in ("docs/instalar/index.html", "docs/instalar/en/index.html"):
        t = read(REPO / rel)
        assert "escribe <code>/mcp</code>, elige" not in t and "type <code>/mcp</code>, choose" not in t


def test_install_ps1_solo_ascii():
    """Windows PowerShell 5.1 lee la web en Latin-1: un carácter no ASCII rompe el instalador (CLAUDE.md)."""
    bad = sorted({c for c in read(REPO / "docs" / "install.ps1") if ord(c) > 127})
    assert not bad
