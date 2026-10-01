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


ENCODER_ENV = "FRAME28_ENCODER"   # "nvenc" → h264_nvenc en los clips intermedios; cualquier otra cosa → libx264


def use_gpu_encoder(enable: bool | None = None) -> bool:
    """Lee (o fija, con `enable`) si los clips intermedios se codifican con NVENC. Medido en una RTX 4060: 20 s de
    1080p en 3,2 s frente a 15,4 s con libx264; el fichero sale mayor. Los intermedios no se entregan: no importa."""
    if enable is not None:
        os.environ[ENCODER_ENV] = "nvenc" if enable else "x264"
    return os.environ.get(ENCODER_ENV, "").lower() == "nvenc"


def encoder_args(crf: int = 16) -> list[str]:
    """Argumentos de codificación H.264 de los clips intermedios: libx264 con `crf`, o NVENC con el mismo valor como
    `-cq` cuando `use_gpu_encoder()`."""
    if use_gpu_encoder():
        return ["-c:v", "h264_nvenc", "-preset", "p5", "-rc", "vbr", "-cq", str(crf), "-b:v", "0"]
    return ["-c:v", "libx264", "-crf", str(crf)]


def cuda_dll_dirs() -> list[Path]:
    """Carpetas con las librerías de CUDA instaladas como paquetes pip (`nvidia-cublas-cu12`, `nvidia-cudnn-cu12`):
    site-packages/nvidia/<lib>/bin en Windows, .../lib en Linux."""
    try:
        import nvidia
        roots = [Path(p) for p in nvidia.__path__]
    except Exception:  # noqa: BLE001  el extra `gpu` no está instalado
        return []
    out: list[Path] = []
    for r in roots:
        for d in sorted(r.glob("*/bin")) + sorted(r.glob("*/lib")):
            if any(d.glob("*.dll")) or any(d.glob("*.so*")):
                out.append(d)
    return out


def enable_cuda_dlls() -> list[str]:
    """Deja las librerías de CUDA localizables para ctranslate2, que las carga por nombre al usar la GPU."""
    dirs = cuda_dll_dirs()
    for d in dirs:
        if hasattr(os, "add_dll_directory"):
            try:
                os.add_dll_directory(str(d))
            except OSError:
                pass
        if str(d) not in os.environ.get("PATH", ""):
            os.environ["PATH"] = str(d) + os.pathsep + os.environ.get("PATH", "")
    return [str(d) for d in dirs]


def cuda_ready() -> tuple[bool, str]:
    """¿Puede faster-whisper usar la GPU? Hace falta un dispositivo CUDA (driver de NVIDIA) y las librerías cuBLAS y
    cuDNN. Devuelve (sí/no, motivo en una línea)."""
    try:
        import ctranslate2
        n = ctranslate2.get_cuda_device_count()
    except Exception as e:  # noqa: BLE001
        return False, f"ctranslate2 no disponible ({type(e).__name__})"
    if n < 1:
        return False, "sin GPU NVIDIA con driver CUDA"
    dirs = enable_cuda_dlls()
    if os.name == "nt":
        import ctypes
        for lib in ("cublas64_12.dll", "cudnn64_9.dll"):
            try:
                ctypes.WinDLL(lib)
            except OSError:
                return False, f"GPU detectada, falta {lib} (instala el extra: frame28[gpu])"
    elif not dirs:
        return False, "GPU detectada, faltan cuBLAS/cuDNN (instala el extra: frame28[gpu])"
    return True, f"{n} GPU CUDA con cuBLAS y cuDNN"


def ensure_rvm_model() -> Path:
    if RVM_MODEL_PATH.exists():
        return RVM_MODEL_PATH
    import urllib.request

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Descargando modelo RVM (15 MB) a {RVM_MODEL_PATH} ...")
    urllib.request.urlretrieve(RVM_MODEL_URL, RVM_MODEL_PATH)
    return RVM_MODEL_PATH
