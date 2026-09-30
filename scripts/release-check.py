# -*- coding: utf-8 -*-
"""Checklist de release de Frame28 (solo biblioteca estándar): la versión en los cuatro sitios, el árbol limpio,
el tag libre, la cuenta activa de `gh`, el CLI instalado y el manifiesto del plugin.

    python scripts/release-check.py            # comprueba; sale con 1 si algo bloquea
    python scripts/release-check.py --notes    # además lista los commits desde el último tag (punto de partida de las notas)

Nace de la 0.3.0: el bump de ficheros se olvidó de `__init__.py` y `frame28 --version` siguió diciendo 0.2.0.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OWNER = "javierledesma28"          # cuenta dueña del repo; con la corporativa activa el push da 403
REPO = f"{OWNER}/frame28"

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        pass


def sh(*cmd: str, cwd: Path = ROOT) -> tuple[int, str]:
    try:
        r = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, encoding="utf-8", errors="replace", shell=(sys.platform == "win32"))
        return r.returncode, (r.stdout + r.stderr).strip()
    except FileNotFoundError:
        return 127, f"{cmd[0]} no encontrado"


def versions() -> dict[str, str | None]:
    init = (ROOT / "plugin/cli/frame28/__init__.py").read_text(encoding="utf-8")
    m = re.search(r'^__version__\s*=\s*"([^"]+)"', init, re.M)
    v = {"plugin/cli/frame28/__init__.py": m.group(1) if m else None}
    py = (ROOT / "plugin/cli/pyproject.toml").read_text(encoding="utf-8")
    static = re.search(r'^version\s*=\s*"([^"]+)"', py, re.M)
    v["plugin/cli/pyproject.toml"] = static.group(1) if static else ("dinámica desde __init__.py" if 'dynamic = ["version"]' in py else None)
    v["plugin/.claude-plugin/plugin.json"] = json.loads((ROOT / "plugin/.claude-plugin/plugin.json").read_text(encoding="utf-8")).get("version")
    mk = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text(encoding="utf-8"))
    v[".claude-plugin/marketplace.json"] = (mk.get("plugins") or [{}])[0].get("version")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    found = sorted(set(re.findall(r"\bv(\d+\.\d+\.\d+)\b", readme)))
    v["README.md"] = ", ".join(found) if found else None
    return v


def main() -> int:
    notes = "--notes" in sys.argv
    rows: list[tuple[bool, bool, str, str]] = []  # (ok, blocking, name, detail)

    def add(ok: bool, name: str, detail: str, blocking: bool = True):
        rows.append((ok, blocking, name, detail))

    v = versions()
    ref = v["plugin/cli/frame28/__init__.py"]
    for path, val in v.items():
        if path == "plugin/cli/pyproject.toml":
            add(val == "dinámica desde __init__.py", path, val or "sin versión", blocking=True)
        else:
            add(bool(ref) and val == ref, path, val or "sin versión")
    tag = f"v{ref}"

    code, st = sh("git", "status", "--porcelain")
    add(code == 0 and not st, "árbol de trabajo", "limpio" if not st else f"{len(st.splitlines())} cambio(s) sin commitear")
    code, br = sh("git", "rev-parse", "--abbrev-ref", "HEAD")
    add(br == "main", "rama", br)
    _, local_tags = sh("git", "tag", "-l", tag)
    add(not local_tags, f"tag local {tag}", "libre" if not local_tags else "ya existe")
    code, remote = sh("git", "ls-remote", "--tags", "origin", tag)
    add(code == 0 and not remote, f"tag remoto {tag}", "libre" if (code == 0 and not remote) else (remote or "no se pudo consultar"))
    code, ahead = sh("git", "rev-list", "--count", "origin/main..HEAD")
    add(True, "commits sin push", ahead if code == 0 else "?", blocking=False)

    code, login = sh("gh", "api", "user", "--jq", ".login")
    add(login == OWNER, "cuenta activa de gh", login or "sin sesión", blocking=False)
    code, rel = sh("gh", "release", "view", tag, "--repo", REPO, "--json", "tagName", "--jq", ".tagName")
    add(code != 0, f"release {tag} en GitHub", "libre" if code != 0 else "ya publicada")

    code, cliv = sh("frame28", "--version")
    m = re.search(r"(\d+\.\d+\.\d+)", cliv or "")
    add(bool(m) and m.group(1) == ref, "frame28 instalado", (m.group(1) if m else cliv[:60] or "no encontrado") + (" (reinstala el editable con --reinstall)" if m and m.group(1) != ref else ""), blocking=False)
    code, val = sh("claude", "plugin", "validate", str(ROOT / "plugin"))
    add(code == 0 and "passed" in val.lower(), "claude plugin validate", "ok" if code == 0 else val.splitlines()[-1][:80])

    width = max(len(n) for _, _, n, _ in rows) + 2
    for ok, blocking, name, detail in rows:
        mark = "✓" if ok else ("✗" if blocking else "!")
        print(f"  {mark} {name:<{width}} {detail}")
    bad = [r for r in rows if not r[0] and r[1]]
    warn = [r for r in rows if not r[0] and not r[1]]
    print()
    if notes:
        _, last = sh("git", "describe", "--tags", "--abbrev=0")
        rng = f"{last}..HEAD" if last and not last.startswith("fatal") else "HEAD"
        _, logs = sh("git", "log", rng, "--format=- %s")
        print(f"Commits desde {last or 'el inicio'} (borrador de notas):\n{logs}\n")
    if bad:
        print(f"Faltan {len(bad)} comprobación(es) antes de etiquetar {tag}.")
        return 1
    print(f"Listo para etiquetar {tag}." + (f" Avisos: {', '.join(r[2] for r in warn)}." if warn else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
