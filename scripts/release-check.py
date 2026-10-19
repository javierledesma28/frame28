# -*- coding: utf-8 -*-
"""Checklist de release de Frame28 (solo biblioteca estándar): la versión en los cuatro sitios, el árbol limpio,
el tag libre, la rama `release`, la cuenta activa de `gh`, el CLI instalado, el manifiesto del plugin, las versiones
exactas de las librerías (extra `probado`), la suite de pruebas en verde con ellas y la confidencialidad (términos que
no pueden aparecer en nada público).

    python scripts/release-check.py            # comprueba; sale con 1 si algo bloquea
    python scripts/release-check.py --notes    # además lista los commits desde el último tag (punto de partida de las notas)

Nace de la 0.3.0: el bump de ficheros se olvidó de `__init__.py` y `frame28 --version` siguió diciendo 0.2.0.
La fila de confidencialidad nace de la 0.4.0: el nombre de un cliente se limpió del árbol y del historial, pero
seguía en las notas de una release y en una carpeta sin ignorar. Los términos viven en `_private/confidencial.txt`
(no versionado): uno por línea, texto o expresión regular, sin distinguir mayúsculas; `#` comenta.
Las filas de `release` y de las versiones exactas nacen de F28-91: el instalador, el plugin y `uv tool upgrade` instalan
de la rama `release`, que cada release adelanta a su tag, con las versiones con las que pasaron las pruebas.
La de la cota de yt-dlp nace de F28-358: `frame28 fetch` usa yt-dlp >= YTDLP_MIN y cada release la sube a la última
estable, porque las plataformas cambian y un yt-dlp viejo falla con errores que no dicen que es viejo.
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
RELEASE_BRANCH = "release"         # la rama de la última release publicada: de ella instalan los clientes (F28-91)
CONF_FILE = ROOT / "_private" / "confidencial.txt"   # no versionado: los términos no pueden estar en el repo

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


def git(*args: str) -> tuple[int, str]:
    """git sin shell: los formatos con `%` y las salidas grandes no pasan por cmd.exe."""
    try:
        r = subprocess.run(["git", "-c", "core.quotepath=false", *args], cwd=str(ROOT), capture_output=True, text=True, encoding="utf-8", errors="replace")
        return r.returncode, r.stdout
    except FileNotFoundError:
        return 127, ""


def load_patterns(path: Path) -> re.Pattern | None:
    """Términos confidenciales (nombre de un cliente, de su producto, de su gente) como una sola expresión."""
    if not path.is_file():
        return None
    terms = [ln.strip() for ln in path.read_text(encoding="utf-8").splitlines()]
    terms = [t for t in terms if t and not t.startswith("#")]
    return re.compile("|".join(f"(?:{t})" for t in terms), re.I) if terms else None


def find_hits(rx: re.Pattern, files: dict[str, str], log: str, tags: dict[str, str], releases: dict[str, str]) -> dict[str, list[str]]:
    """Dónde aparece algún término. Devuelve sitios (ruta, commit, tag, release), nunca el término: la salida se pega en público."""
    hits: dict[str, list[str]] = {}

    def hit(kind: str, where: str):
        where = rx.sub("***", where)
        if where not in hits.setdefault(kind, []):
            hits[kind].append(where)

    for rel, text in files.items():
        if rx.search(rel) or rx.search(text):
            hit("ficheros", rel)
    commit = "?"
    for ln in log.splitlines():
        if ln.startswith("@@commit "):
            commit = ln[9:].strip()
        elif rx.search(ln):
            hit("commits", commit)
    for name, text in tags.items():
        if rx.search(name) or rx.search(text):
            hit("tags", name)
    for name, text in releases.items():
        if rx.search(name) or rx.search(text):
            hit("releases", name)
    return hits


def _json_stream(raw: str) -> list:
    """`gh api --paginate` concatena un documento JSON por página."""
    dec, i, out = json.JSONDecoder(), 0, []
    while i < len(raw):
        if raw[i].isspace():
            i += 1
            continue
        doc, i = dec.raw_decode(raw, i)
        out.extend(doc if isinstance(doc, list) else [doc])
    return out


def confidential_hits(rx: re.Pattern) -> tuple[dict[str, list[str]], list[str]]:
    """Reúne lo público o a un `git add` de serlo: ficheros versionados y sin ignorar, historia de todos los refs
    (mensajes y diffs), tags, y títulos y notas de las releases y descripción del repo en GitHub."""
    skipped: list[str] = []
    files: dict[str, str] = {}
    _, listing = git("ls-files", "--cached", "--others", "--exclude-standard")
    for rel in listing.splitlines():
        p = ROOT / rel
        try:
            files[rel] = p.read_bytes().decode("utf-8", errors="ignore") if p.is_file() else ""
        except OSError:
            files[rel] = ""
    code, log = git("log", "--exclude=refs/stash", "--all", "-p", "--format=@@commit %h%n%B")
    if code != 0:
        skipped.append("historia")
    tags: dict[str, str] = {}
    for name in git("tag", "-l")[1].split():
        tags[name] = git("tag", "-l", "--format=%(contents)", name)[1]
    releases: dict[str, str] = {}
    try:
        code, raw = sh("gh", "api", f"repos/{REPO}/releases", "--paginate")
        for r in _json_stream(raw) if code == 0 else []:
            releases[str(r.get("tag_name"))] = f"{r.get('name') or ''}\n{r.get('body') or ''}"
        code2, raw = sh("gh", "api", f"repos/{REPO}")
        if code2 == 0:
            r = _json_stream(raw)[0]
            releases["descripción del repo"] = f"{r.get('description') or ''}\n{r.get('homepage') or ''}\n{' '.join(r.get('topics') or [])}"
        if code != 0 or code2 != 0:
            skipped.append("GitHub")
    except (ValueError, IndexError, AttributeError):
        skipped.append("GitHub")
    return find_hits(rx, files, log, tags, releases), skipped


def date_version(v: str | None) -> tuple[int, ...]:
    return tuple(int(x) for x in re.findall(r"\d+", v or "")[:4])


def ytdlp_floor(fetch_py: str, latest: str | None) -> tuple[bool | None, str]:
    """(¿al día?, detalle) de YTDLP_MIN en fetch.py frente a la última estable de PyPI; None si no se pudo consultar."""
    m = re.search(r'^YTDLP_MIN = "([^"]+)"', fetch_py, re.M)
    if not m:
        return False, "no encuentro YTDLP_MIN en plugin/cli/frame28/fetch.py"
    cur = m.group(1)
    if not latest:
        return None, f"{cur}; no se pudo consultar PyPI"
    if date_version(cur) >= date_version(latest):
        return True, f"{cur} (la última estable)"
    return False, (f"{cur} y la última estable es {latest}: sube YTDLP_MIN en plugin/cli/frame28/fetch.py y prueba "
                   "`frame28 fetch` con un vídeo de dominio público")


def pypi_latest(package: str, timeout: float = 10) -> str | None:
    """Última versión estable en PyPI (`info.version` no cuenta prerreleases); None sin red."""
    import urllib.request
    try:
        with urllib.request.urlopen(f"https://pypi.org/pypi/{package}/json", timeout=timeout) as r:
            return json.load(r)["info"]["version"]
    except Exception:  # noqa: BLE001
        return None


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
    bump = "ya existe: sube __version__ en plugin/cli/frame28/__init__.py (y plugin.json, marketplace.json, README) antes de etiquetar"
    _, local_tags = sh("git", "tag", "-l", tag)
    add(not local_tags, f"tag local {tag}", "libre" if not local_tags else bump)
    code, remote = sh("git", "ls-remote", "--tags", "origin", tag)
    add(code == 0 and not remote, f"tag remoto {tag}", "libre" if (code == 0 and not remote) else (bump if remote else "no se pudo consultar"))
    code, ahead = sh("git", "rev-list", "--count", "origin/main..HEAD")
    add(True, "commits sin push", ahead if code == 0 else "?", blocking=False)
    adelantar = f"tras el tag: git push origin {tag}^{{}}:refs/heads/{RELEASE_BRANCH}"
    code, remote_rel = git("ls-remote", "--heads", "origin", RELEASE_BRANCH)
    rel_sha = remote_rel.split()[0] if code == 0 and remote_rel.strip() else ""
    if code != 0:
        add(False, f"rama {RELEASE_BRANCH}", "no se pudo consultar origin", blocking=False)
    elif not rel_sha:
        add(True, f"rama {RELEASE_BRANCH}", f"no existe todavía: la crea esta release ({adelantar})", blocking=False)
    else:
        known = git("cat-file", "-e", rel_sha)[0] == 0
        ff = known and git("merge-base", "--is-ancestor", rel_sha, "HEAD")[0] == 0
        add(ff, f"rama {RELEASE_BRANCH}", (f"{rel_sha[:7]}, se adelanta sin reescribir ({adelantar})" if ff else
            f"{rel_sha[:7]} no es antepasado de HEAD: " + ("haz git fetch origin" if not known else "no se puede adelantar sin reescribir; revisa qué pasó")))

    code, login = sh("gh", "api", "user", "--jq", ".login")
    add(login == OWNER, "cuenta activa de gh", login or "sin sesión", blocking=False)
    code, rel = sh("gh", "release", "view", tag, "--repo", REPO, "--json", "tagName", "--jq", ".tagName")
    add(code != 0, f"release {tag} en GitHub", "libre" if code != 0 else "ya publicada: esta versión está cerrada; el siguiente paso es subir la versión")

    code, cliv = sh("frame28", "--version")
    m = re.search(r"(\d+\.\d+\.\d+)", cliv or "")
    add(bool(m) and m.group(1) == ref, "frame28 instalado", (m.group(1) if m else cliv[:60] or "no encontrado") + (" (reinstala el editable con --reinstall)" if m and m.group(1) != ref else ""), blocking=False)
    code, val = sh("claude", "plugin", "validate", str(ROOT / "plugin"))
    add(code == 0 and "passed" in val.lower(), "claude plugin validate", "ok" if code == 0 else val.splitlines()[-1][:80])
    code, pins = sh(sys.executable, str(ROOT / "scripts" / "fijar-dependencias.py"))
    add(code == 0, "versiones exactas (extra probado)", (pins.splitlines() or ["sin salida"])[-1][:100])
    ok, detail = ytdlp_floor((ROOT / "plugin/cli/frame28/fetch.py").read_text(encoding="utf-8"), pypi_latest("yt-dlp"))
    add(bool(ok), "cota de yt-dlp (fetch)", detail, blocking=ok is not None)
    # con las versiones exactas que reciben los clientes; el pyproject ya lleva -q en addopts (otro -q quitaría "N passed")
    code, tests = sh("uv", "run", "--extra", "probado", "--group", "dev", "pytest", "--no-header", "-p", "no:cacheprovider",
                     cwd=ROOT / "plugin/cli")
    summary = next((ln for ln in reversed(tests.splitlines()) if "passed" in ln or "failed" in ln or "error" in ln.lower()), tests[-80:])
    add(code == 0, "pytest (plugin/cli/tests)", summary.strip()[:80] or "sin salida")

    rx = load_patterns(CONF_FILE)
    if rx is None:
        add(False, "confidencialidad", f"sin términos en {CONF_FILE.relative_to(ROOT).as_posix()}: no se comprueba", blocking=False)
    else:
        hits, skipped = confidential_hits(rx)
        detail = "; ".join(f"{k}: {', '.join(v[:4])}{' …' if len(v) > 4 else ''}" for k, v in hits.items())
        detail = detail or "sin rastro en ficheros, historia, tags y releases"
        add(not hits, "confidencialidad", detail + (f" (sin consultar: {', '.join(skipped)})" if skipped else ""))

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
    print(f"Después: git tag -a {tag} -m … && git push origin {tag} && git push origin {tag}^{{}}:refs/heads/{RELEASE_BRANCH}"
          " (sin la rama, los clientes siguen en la release anterior).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
