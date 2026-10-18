"""F28-91, de punta a punta: una instalación limpia baja la release fijada (la rama `release`), no main, con las
versiones exactas del extra `probado`; y `uv tool upgrade` la sigue cuando la rama avanza a la release siguiente.

Instala de verdad (unos cientos de MB; con la caché de uv, segundos), así que solo corre si se pide:
    FRAME28_PRUEBA_INSTALACION=1 uv run --extra probado --group dev pytest tests/test_instalacion.py
Usa un repo git local con la forma del público (plugin/cli) y un directorio de herramientas de uv temporal: no toca
la instalación de la máquina."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from frame28 import __version__, env

CLI = Path(__file__).resolve().parents[1]
REPO = CLI.parents[1]

pytestmark = pytest.mark.skipif(os.environ.get("FRAME28_PRUEBA_INSTALACION") != "1" or not shutil.which("uv")
                                or not shutil.which("git"), reason="instala de verdad: FRAME28_PRUEBA_INSTALACION=1")

DUMP = """
import importlib.metadata as md, json
from frame28 import __version__, doctor as D
from frame28.env import PINNED_EXTRA
pins = D.pinned_versions(md.requires("frame28"), PINNED_EXTRA)
installed = {D._canon(d.metadata["Name"] or ""): d.version for d in md.distributions()}
print(json.dumps({"version": __version__, "row": D.pinned_row(pins, installed, None), "pins": len(pins)}))
"""


def _run(cmd, cwd=None, env_=None, timeout=900):
    r = subprocess.run(cmd, cwd=cwd, env=env_, capture_output=True, text=True, encoding="utf-8", errors="replace",
                       timeout=timeout)
    assert r.returncode == 0, f"{cmd}\n{(r.stderr or r.stdout)[-2000:]}"
    return r.stdout


def _git(repo: Path, *args: str) -> str:
    return _run(["git", "-c", "user.name=prueba", "-c", "user.email=prueba@example.invalid", "-c", "commit.gpgsign=false",
                 *args], cwd=repo)


def _repo_publico(dst: Path) -> None:
    """Un repo con plugin/cli tal como está en el árbol de trabajo (versionado y nuevo sin ignorar) y dos commits: la
    release (rama `release`) y main, que va por delante con otra versión."""
    files = _run(["git", "ls-files", "--cached", "--others", "--exclude-standard", "plugin/cli"], cwd=REPO).splitlines()
    for rel in files:
        src = REPO / rel
        if src.is_file():
            (dst / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst / rel)
    _git(dst, "init", "-q", "-b", "main")
    _git(dst, "add", "-A")
    _git(dst, "commit", "-q", "-m", "release")
    _git(dst, "branch", "release")
    init = dst / "plugin" / "cli" / "frame28" / "__init__.py"
    t = init.read_text(encoding="utf-8")
    assert f'__version__ = "{__version__}"' in t
    init.write_text(t.replace(f'__version__ = "{__version__}"', '__version__ = "9.9.9"'), encoding="utf-8")
    _git(dst, "commit", "-q", "-am", "main por delante")


def test_instalacion_limpia_baja_la_release_fijada_y_upgrade_la_sigue(tmp_path):
    origen = tmp_path / "frame28"
    origen.mkdir()
    _repo_publico(origen)
    e = {k: v for k, v in os.environ.items() if k not in ("VIRTUAL_ENV", "UV_PROJECT_ENVIRONMENT", "PYTHONPATH")}
    e.update(UV_TOOL_DIR=str(tmp_path / "tools"), UV_TOOL_BIN_DIR=str(tmp_path / "bin"), PYTHONIOENCODING="utf-8")
    url = "git+" + origen.as_uri()
    spec = f"frame28[{env.PINNED_EXTRA}] @ {url}@release#subdirectory=plugin/cli"

    _run(["uv", "tool", "install", "--python", "3.12", spec], env_=e)
    receipt = (tmp_path / "tools" / "frame28" / "uv-receipt.toml").read_text(encoding="utf-8")
    assert '"probado"' in receipt and "rev=release" in receipt
    py = tmp_path / "tools" / "frame28" / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
    got = json.loads(_run([str(py), "-I", "-c", DUMP], env_=e).strip().splitlines()[-1])
    assert got["version"] == __version__                       # la release, no main (9.9.9)
    assert got["pins"] > 20 and got["row"]["ok"], got["row"]   # y exactamente las versiones probadas

    _git(origen, "branch", "-f", "release", "main")            # la release siguiente adelanta la rama
    _run(["uv", "tool", "upgrade", "frame28"], env_=e)
    got = json.loads(_run([str(py), "-I", "-c", DUMP], env_=e).strip().splitlines()[-1])
    assert got["version"] == "9.9.9" and got["row"]["ok"], got
