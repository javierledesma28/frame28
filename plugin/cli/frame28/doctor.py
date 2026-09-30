"""Comprobación del entorno: qué hay, qué falta y cómo instalarlo. Las filas `optional` no bloquean ("Todo listo")."""
from __future__ import annotations

import importlib
import json
import shutil
import subprocess
import urllib.request

from . import GSAP_VERSION, HYPERFRAMES_VERSION, __version__
from .env import RVM_MODEL_PATH, find_tool

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
    add("node", bool(node), ver or "no encontrado", "Node.js 22+ desde https://nodejs.org (HyperFrames lo necesita)")
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
    add("modelo RVM", RVM_MODEL_PATH.exists(), str(RVM_MODEL_PATH), "se descarga solo (15 MB) la primera vez que se use `frame28 matte`", optional=True)
    net = cdn_reachable()
    add("red (GSAP por CDN)", net, f"gsap@{GSAP_VERSION} en cdn.jsdelivr.net" + ("" if net else ": sin acceso"),
        "el render y la portada cargan GSAP por internet: conecta la red antes de `frame28 render` o `frame28 cover`", optional=True)
    return rows
