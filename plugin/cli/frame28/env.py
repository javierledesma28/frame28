"""Localización de binarios externos (ffmpeg, npx) y rutas de caché. Windows-friendly."""
from __future__ import annotations

import glob
import os
import shutil
import subprocess
from pathlib import Path

CACHE_DIR = Path(os.environ.get("FRAME28_CACHE", Path.home() / ".cache" / "frame28"))
RVM_MODEL_URL = "https://github.com/PeterL1n/RobustVideoMatting/releases/download/v1.0.0/rvm_mobilenetv3_fp32.onnx"
RVM_MODEL_PATH = CACHE_DIR / "rvm_mobilenetv3_fp32.onnx"


def _winget_candidates(exe: str) -> list[str]:
    base = Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WinGet" / "Packages"
    if not base.exists():
        return []
    return glob.glob(str(base / "**" / f"{exe}.exe"), recursive=True)


def find_tool(name: str, env_var: str | None = None) -> str | None:
    """Busca un ejecutable: variable de entorno explícita, PATH, y en Windows los paquetes de WinGet."""
    if env_var and os.environ.get(env_var):
        return os.environ[env_var]
    found = shutil.which(name)
    if found:
        return found
    if os.name == "nt":
        cands = _winget_candidates(name)
        if cands:
            return sorted(cands)[-1]
    return None


def ffmpeg() -> str:
    p = find_tool("ffmpeg", "FRAME28_FFMPEG")
    if not p:
        raise SystemExit("ffmpeg no encontrado. Instala con: winget install --id Gyan.FFmpeg -e  (o define FRAME28_FFMPEG)")
    return p


def ffprobe() -> str:
    p = find_tool("ffprobe", "FRAME28_FFPROBE")
    if not p:
        # mismo directorio que ffmpeg
        cand = Path(ffmpeg()).with_name("ffprobe.exe" if os.name == "nt" else "ffprobe")
        if cand.exists():
            return str(cand)
        raise SystemExit("ffprobe no encontrado")
    return p


def npx() -> str:
    p = shutil.which("npx") or shutil.which("npx.cmd")
    if not p:
        raise SystemExit("npx no encontrado: instala Node.js 22+ (https://nodejs.org)")
    return p


def run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    """subprocess.run con salida en texto y sin lanzar excepción por defecto."""
    kw.setdefault("text", True)
    kw.setdefault("capture_output", True)
    kw.setdefault("encoding", "utf-8")
    kw.setdefault("errors", "replace")
    return subprocess.run(cmd, **kw)


def env_with_ffmpeg() -> dict:
    """Entorno con el directorio de ffmpeg en PATH (HyperFrames lo necesita en PATH)."""
    env = dict(os.environ)
    ffdir = str(Path(ffmpeg()).parent)
    env["PATH"] = ffdir + os.pathsep + env.get("PATH", "")
    return env


def ensure_rvm_model() -> Path:
    if RVM_MODEL_PATH.exists():
        return RVM_MODEL_PATH
    import urllib.request

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Descargando modelo RVM (15 MB) a {RVM_MODEL_PATH} ...")
    urllib.request.urlretrieve(RVM_MODEL_URL, RVM_MODEL_PATH)
    return RVM_MODEL_PATH
