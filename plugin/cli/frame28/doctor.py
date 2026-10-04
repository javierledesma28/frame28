"""Comprobación del entorno: qué hay, qué falta y cómo instalarlo. Las filas `optional` no bloquean ("Todo listo")."""
from __future__ import annotations

import importlib
import json
import os
import shutil
import subprocess
import time
import urllib.request
from pathlib import Path

from . import GSAP_VERSION, HYPERFRAMES_VERSION, __version__
from .env import CACHE_DIR, RVM_MODEL_PATH, find_tool

NODE_MIN = 22   # HyperFrames 0.8 necesita Node 22


def node_major(version: str) -> int:
    """«v22.11.0» → 22; 0 si no se entiende."""
    try:
        return int(version.strip().lstrip("v").split(".")[0])
    except (ValueError, IndexError):
        return 0

GSAP_CDN = f"https://cdn.jsdelivr.net/npm/gsap@{GSAP_VERSION}/dist/gsap.min.js"


def installed_version() -> tuple[str | None, bool]:
    """(versión según la metadata del paquete instalado, ¿instalación editable?). (None, False) si no está instalado como paquete."""
    try:
        import importlib.metadata as md
        dist = md.distribution("frame28")
    except Exception:  # noqa: BLE001
        return None, False
    editable = False
    try:
        du = json.loads(dist.read_text("direct_url.json") or "{}")
        editable = bool((du.get("dir_info") or {}).get("editable"))
    except Exception:  # noqa: BLE001
        pass
    return dist.version, editable


def cdn_reachable(url: str = GSAP_CDN, timeout: float = 5.0) -> bool:
    try:
        req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": f"frame28/{__version__}"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status < 400
    except Exception:  # noqa: BLE001
        return False


RELEASES_API = "https://api.github.com/repos/javierledesma28/frame28/releases/latest"
CLI_UPGRADE = "uv tool upgrade frame28  (o repetir el instalador)"
PLUGIN_UPGRADE = ("claude plugin marketplace update think28 && claude plugin update frame28@think28  "
                  "(y abrir una sesión nueva de Claude Code)")
PLUGIN_INSTALL = "claude plugin marketplace add javierledesma28/frame28 && claude plugin install frame28@think28"
RELEASE_TTL = 12 * 3600       # una respuesta de GitHub vale 12 h: sin token, GitHub da 60 consultas por hora
RELEASE_FAIL_TTL = 3600       # sin red: no volver a esperar el timeout en cada doctor durante una hora


def _vtuple(v: str) -> tuple[int, ...]:
    return tuple(int(x) for x in v.strip().lstrip("v").split(".") if x.isdigit())


def release_newer(current: str | None, latest: str | None) -> bool | None:
    """True si la release publicada es más nueva que la instalada; False si está al día; None si no se sabe."""
    if not latest or not current:
        return None
    a, b = _vtuple(current), _vtuple(latest)
    if not a or not b:        # una etiqueta sin números ("rc") no dice nada
        return None
    return b > a


def _fetch_release(url: str, timeout: float) -> str | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": f"frame28/{__version__}", "Accept": "application/vnd.github+json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8")).get("tag_name")
    except Exception:  # noqa: BLE001
        return None


def latest_release(url: str = RELEASES_API, timeout: float = 5.0, cache: Path | None = None, now: float | None = None) -> str | None:
    """Tag de la última release pública (None si no se sabe), con caché en ~/.cache/frame28/release.json: 12 h si GitHub
    respondió, 1 h si no (sin red, `doctor` no espera el timeout cada vez)."""
    cache = cache or CACHE_DIR / "release.json"
    now = time.time() if now is None else now
    try:
        c = json.loads(cache.read_text(encoding="utf-8-sig"))
        ttl = RELEASE_TTL if c.get("tag") else RELEASE_FAIL_TTL
        if c.get("url") == url and 0 <= now - float(c.get("at", 0)) < ttl:
            return c.get("tag")
    except Exception:  # noqa: BLE001  (sin caché o caché rota: se pregunta)
        pass
    tag = _fetch_release(url, timeout)
    try:
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps({"url": url, "tag": tag, "at": now}), encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    return tag


def claude_plugins_file() -> Path:
    return Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude") / "plugins" / "installed_plugins.json"


def plugin_installed(path: Path | None = None) -> tuple[bool, str | None]:
    """(¿hay Claude Code en este usuario?, versión del plugin frame28 instalado o None). Lee installed_plugins.json de
    Claude Code; admite el formato con `plugins` y el plano, y una entrada o varias (alcances usuario y proyecto)."""
    path = path or claude_plugins_file()
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError:
        return False, None
    except Exception:  # noqa: BLE001  (formato desconocido: hay Claude Code, no sabemos la versión)
        return True, None
    plugins = data.get("plugins", data) if isinstance(data, dict) else {}
    versions = []
    for key, entries in (plugins.items() if isinstance(plugins, dict) else []):
        if str(key).split("@")[0] != "frame28":
            continue
        for e in entries if isinstance(entries, list) else [entries]:
            if isinstance(e, dict) and _vtuple(str(e.get("version") or "")):
                versions.append(str(e["version"]))
    return True, (max(versions, key=_vtuple) if versions else None)


def marketplace_clash(config_dir: Path | None = None) -> str | None:
    """Si `extraKnownMarketplaces` de settings.json declara un marketplace con una fuente distinta de la instalada
    (típico: un `path` añadido a mano junto al `repo`), Claude Code lo ignora y el plugin sale «failed to load» aunque
    /mcp diga Connected (F28-240). Devuelve el aviso con el arreglo, o None si todo cuadra o no hay nada que mirar."""
    base = config_dir or Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude")

    def load(p: Path) -> dict:
        try:
            d = json.loads(p.read_text(encoding="utf-8-sig"))
            return d if isinstance(d, dict) else {}
        except Exception:  # noqa: BLE001
            return {}
    declared = load(base / "settings.json").get("extraKnownMarketplaces")
    installed = load(base / "plugins" / "known_marketplaces.json")
    for name, entry in (declared.items() if isinstance(declared, dict) else []):
        want = entry.get("source") if isinstance(entry, dict) else None
        have = (installed.get(name) or {}).get("source") if isinstance(installed.get(name), dict) else None
        if isinstance(want, dict) and isinstance(have, dict) and want != have:
            return (f"settings.json declara el marketplace «{name}» con una fuente distinta de la instalada ({want} frente a {have}): "
                    "Claude Code lo ignora y el plugin no carga. Deja en `extraKnownMarketplaces." + name + ".source` solo "
                    f"{have} (quita los campos de más, p. ej. `path`) o borra la entrada, y reabre Claude Code")
    return None


def version_rows(cli: str, latest: str | None, plugin: tuple[bool, str | None]) -> list[dict]:
    """Las dos filas de versiones: el CLI y el plugin de Claude Code contra la última release, cada una con su orden (un
    usuario con una instalación vieja no sabía que había versión nueva ni cómo actualizar; `claude plugin update` solo
    actúa si cambia la versión, así que el plugin es lo que más se queda atrás)."""
    rows = []
    newer = release_newer(cli, latest)
    rows.append({"name": "última release (CLI)", "ok": newer is not True, "optional": True, "fix": CLI_UPGRADE if newer else "",
                 "detail": f"{latest} publicada, {cli} instalada" if newer else (f"{cli} al día" if newer is False else f"{cli} · sin respuesta de GitHub")})
    has_claude, pv = plugin
    if not has_claude:
        rows.append({"name": "plugin (Claude Code)", "ok": False, "optional": True, "fix": "instala Claude Code y después: " + PLUGIN_INSTALL,
                     "detail": "no se encontró Claude Code en este usuario"})
    elif pv is None:
        rows.append({"name": "plugin (Claude Code)", "ok": False, "optional": True, "fix": PLUGIN_INSTALL,
                     "detail": "el plugin frame28 no está instalado en Claude Code"})
    else:
        pnew = release_newer(pv, latest)
        rows.append({"name": "plugin (Claude Code)", "ok": pnew is not True, "optional": True, "fix": PLUGIN_UPGRADE if pnew else "",
                     "detail": f"{pv} instalado, {latest} publicada" if pnew else (f"{pv} al día" if pnew is False else f"{pv} instalado")})
    return rows


def doctor() -> list[dict]:
    rows = []

    def add(name, ok, detail, fix="", optional=False):
        rows.append({"name": name, "ok": ok, "detail": detail, "fix": fix, "optional": optional})

    # la propia instalación: el código y la metadata deben decir la misma versión (la instalación editable no relee __version__)
    inst, editable = installed_version()
    if inst is None:
        add("frame28", True, f"{__version__} (sin metadata de instalación)")
    else:
        add("frame28", inst == __version__, f"{__version__} en código, {inst} instalada" + (" (editable)" if editable else ""),
            "el código y la instalación no coinciden: " + ("uv tool install --editable <ruta>/plugin/cli --python 3.12 --reinstall" if editable else "uv tool upgrade frame28"))
    ff = find_tool("ffmpeg", "FRAME28_FFMPEG")
    add("ffmpeg", bool(ff), ff or "no encontrado", "winget install --id Gyan.FFmpeg -e  (o brew/apt) y reabrir la terminal")
    fp = find_tool("ffprobe", "FRAME28_FFPROBE")
    add("ffprobe", bool(fp), fp or "no encontrado", "viene con ffmpeg")
    node = shutil.which("node")
    ver = subprocess.run([node, "--version"], capture_output=True, text=True).stdout.strip() if node else ""
    major = node_major(ver)
    add("node", bool(node) and major >= NODE_MIN, (ver + (f" (hace falta la {NODE_MIN} o superior)" if node and major < NODE_MIN else "")) if ver else "no encontrado",
        f"Node.js {NODE_MIN}+ desde https://nodejs.org (HyperFrames lo necesita); o repite el instalador, que lo actualiza")
    has_npx = bool(shutil.which("npx") or shutil.which("npx.cmd"))
    add("npx", has_npx, "ok" if has_npx else "no encontrado", "viene con Node.js")
    add("hyperframes", True, f"{HYPERFRAMES_VERSION} pineado (npx lo descarga la primera vez que se use)")
    for mod, fix in [("faster_whisper", "uv pip install faster-whisper"), ("onnxruntime", "uv pip install onnxruntime"), ("cv2", "uv pip install opencv-python-headless")]:
        try:
            m = importlib.import_module(mod)
            add(mod, True, getattr(m, "__version__", "ok"))
        except Exception as e:  # noqa: BLE001
            add(mod, False, str(e)[:80], fix)
    try:
        import onnxruntime as ort
        provs = ort.get_available_providers()
        add("gpu (onnxruntime)", "CUDAExecutionProvider" in provs, ", ".join(provs), "opcional: uv pip install onnxruntime-gpu + CUDA 12 para matting rápido", optional=True)
    except Exception:  # noqa: BLE001
        pass
    try:
        from .env import encoder_mode, nvenc_ready
        mode = encoder_mode()
        ok_nv, why_nv = nvenc_ready()
        uses = "NVENC (GPU)" if (mode == "nvenc" or (mode == "auto" and ok_nv)) else "libx264 (CPU)"
        add("codificador", True, f"{uses} · FRAME28_ENCODER={mode} · {why_nv}",
            "" if ok_nv or mode == "cpu" else "opcional: con una GPU NVIDIA y su driver, prep, reframe, cut y render codifican ~5x más rápido sin pedirlo",
            optional=True)
    except Exception:  # noqa: BLE001
        pass
    try:
        from .env import cuda_ready
        ok_gpu, why_gpu = cuda_ready()
        add("gpu (transcripción)", ok_gpu, why_gpu, 'opcional: uv tool install --editable "<ruta>/plugin/cli[gpu]" --python 3.12 --reinstall (librerías CUDA, más de 1 GB); sin ellas `transcribe` va por CPU', optional=True)
    except Exception:  # noqa: BLE001
        pass
    from .audio import RNNOISE_MODEL_PATH, RNNOISE_MODEL_SHA256
    from .env import RVM_MODEL_SHA256, model_ok
    from .pose import POSE_MODEL_PATH, POSE_MODEL_SHA256
    for label, path, sha, when in (("modelo RVM", RVM_MODEL_PATH, RVM_MODEL_SHA256, "la primera vez que se use `frame28 matte` (15 MB)"),
                                   ("modelo de pose", POSE_MODEL_PATH, POSE_MODEL_SHA256, "con `speaker`, `gestures` o `reframe` (5 MB)"),
                                   ("modelo RNNoise", RNNOISE_MODEL_PATH, RNNOISE_MODEL_SHA256, "con `prep --denoise rnnoise`")):
        ok = model_ok(path, sha)
        add(label, ok, str(path) + ("" if ok or not path.exists() else " (incompleto o corrupto)"),
            f"se descarga solo {when}" + (" y sustituye al corrupto" if path.exists() and not ok else ""), optional=True)
    try:
        from .broll import providers_available
        provs = providers_available()
        have = [k for k, v in provs.items() if v]
        add("claves de B-roll", bool(have), ", ".join(have) if have else "sin claves de Pexels ni Pixabay",
            "opcional: PEXELS_API_KEY / PIXABAY_API_KEY en el entorno o en ~/.config/frame28/keys.json (gratis en pexels.com/api y pixabay.com/api/docs); sin ellas `frame28 broll search` no busca", optional=True)
    except Exception as e:  # noqa: BLE001
        add("claves de B-roll", False, str(e)[:80], "revisa ~/.config/frame28/keys.json", optional=True)
    rows.extend(version_rows(__version__, latest_release(), plugin_installed()))
    clash = marketplace_clash()
    add("marketplace del plugin", clash is None, "ok" if clash is None else clash, "" if clash is None else clash, optional=True)
    net = cdn_reachable()
    add("red (GSAP por CDN)", net, f"gsap@{GSAP_VERSION} en cdn.jsdelivr.net" + ("" if net else ": sin acceso"),
        "el render y la portada cargan GSAP por internet: conecta la red antes de `frame28 render` o `frame28 cover`", optional=True)
    return rows
