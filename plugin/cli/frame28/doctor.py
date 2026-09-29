"""Comprobación del entorno: qué hay, qué falta y cómo instalarlo."""
from __future__ import annotations

import importlib
import shutil
import subprocess

from .env import RVM_MODEL_PATH, find_tool


def doctor() -> list[dict]:
    rows = []

    def add(name, ok, detail, fix=""):
        rows.append({"name": name, "ok": ok, "detail": detail, "fix": fix})

    ff = find_tool("ffmpeg", "FRAME28_FFMPEG")
    add("ffmpeg", bool(ff), ff or "no encontrado", "winget install --id Gyan.FFmpeg -e  (o brew/apt) y reabrir la terminal")
    fp = find_tool("ffprobe", "FRAME28_FFPROBE")
    add("ffprobe", bool(fp), fp or "no encontrado", "viene con ffmpeg")
    node = shutil.which("node")
    ver = subprocess.run([node, "--version"], capture_output=True, text=True).stdout.strip() if node else ""
    add("node", bool(node), ver or "no encontrado", "Node.js 22+ desde https://nodejs.org (HyperFrames lo necesita)")
    add("npx", bool(shutil.which("npx") or shutil.which("npx.cmd")), "ok" if shutil.which("npx") or shutil.which("npx.cmd") else "no encontrado", "viene con Node.js")
    for mod, fix in [("faster_whisper", "uv pip install faster-whisper"), ("onnxruntime", "uv pip install onnxruntime"), ("cv2", "uv pip install opencv-python-headless")]:
        try:
            m = importlib.import_module(mod)
            add(mod, True, getattr(m, "__version__", "ok"))
        except Exception as e:  # noqa: BLE001
            add(mod, False, str(e)[:80], fix)
    try:
        import onnxruntime as ort
        provs = ort.get_available_providers()
        add("gpu (onnxruntime)", "CUDAExecutionProvider" in provs, ", ".join(provs), "opcional: uv pip install onnxruntime-gpu + CUDA 12 para matting rápido")
    except Exception:  # noqa: BLE001
        pass
    add("modelo RVM", RVM_MODEL_PATH.exists(), str(RVM_MODEL_PATH), "se descarga solo (15 MB) la primera vez que se use `frame28 matte`")
    return rows
