"""F28-238: todos los sitios que explican cómo entrar con la cuenta de Frame28 dan el mismo camino, que sirve también en la
app de escritorio (allí `/mcp` no existe): `claude mcp login plugin:frame28:frame28` y una sesión nueva. Y ninguno manda
lanzar `mcp login` para comprobar: borra la sesión guardada en cuanto empieza."""
import os
import shutil
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
LOGIN = "mcp login plugin:frame28:frame28"
SKILLS = sorted((REPO / "plugin" / "skills").glob("*/SKILL.md"))


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def test_hay_diez_skills():
    nombres = {p.parent.name for p in SKILLS}
    assert len(SKILLS) == 10 and {"frame28", "frame28-memoria"} <= nombres


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


def test_instalar_desde_la_app_de_escritorio():
    """F28-451: en la app de escritorio no hay terminal. Se usa su claude.exe en vez de instalar la CLI, el PATH se recarga
    del registro tras winget, el plan B no manda a /plugin (en la pestaña Code no existe) y el cierre pide cerrar la app."""
    ps1, md = read(REPO / "docs" / "install.ps1"), read(REPO / "docs" / "instalar.md")
    assert "$env:CLAUDE_CODE_EXECPATH" in ps1 and r"Claude\claude-code" in ps1 and "[version]" in ps1
    assert "if ((Has claude) -or $App)" in ps1 and "& $Claude plugin install" in ps1
    assert "/plugin marketplace add" not in ps1 and "/plugin install" not in ps1
    assert "if ($App) {" in ps1 and "Cierra la app de Claude del todo" in ps1
    assert "CLAUDE_CODE_EXECPATH" in md and r"%APPDATA%\Claude\claude-code" in md and "no por fecha" in md
    assert "GetEnvironmentVariable('Path','Machine')" in md and r"%USERPROFILE%\.local\bin\frame28.exe" in md
    assert "FRAME28_YES=1" in md and "cerrar la app del todo" in md


def _funcion_ps(nombre: str) -> str:
    t = read(REPO / "docs" / "install.ps1")
    i = t.index(f"function {nombre} {{")
    fin = t.index("\n}\n", i) + 3
    return t[i:fin]


@pytest.mark.skipif(os.name != "nt" or not shutil.which("pwsh"), reason="install.ps1 es de Windows")
def test_app_claude_elige_la_version_mas_alta(tmp_path):
    """La carpeta de la app guarda varias versiones: gana la más alta por número (2.1.10 > 2.1.9), no por orden alfabético
    ni por fecha; una CLAUDE_CODE_EXECPATH rota no cuenta."""
    for v in ("2.1.9", "2.1.10", "basura"):
        exe = tmp_path / "Claude" / "claude-code" / v / "abc" / "claude.exe"
        exe.parent.mkdir(parents=True)
        exe.write_text("")
    script = _funcion_ps("App-Claude") + "\nApp-Claude\n"
    env = {**os.environ, "APPDATA": str(tmp_path), "CLAUDE_CODE_EXECPATH": str(tmp_path / "no-existe.exe")}
    r = subprocess.run(["pwsh", "-NoProfile", "-Command", script], capture_output=True, text=True, env=env, timeout=60)
    assert r.returncode == 0, r.stderr
    assert Path(r.stdout.strip()).parent.parent.name == "2.1.10"
