"""Localización de binarios externos (ffmpeg, npx) y rutas de caché. Windows-friendly."""
from __future__ import annotations

import glob
import os
import shutil
import subprocess
import sys
from pathlib import Path

CACHE_DIR = Path(os.environ.get("FRAME28_CACHE", Path.home() / ".cache" / "frame28"))
RVM_MODEL_URL = "https://github.com/PeterL1n/RobustVideoMatting/releases/download/v1.0.0/rvm_mobilenetv3_fp32.onnx"
RVM_MODEL_PATH = CACHE_DIR / "rvm_mobilenetv3_fp32.onnx"
RVM_MODEL_SHA256 = "88d4531297118f595bf2fd60f6f566aec2e559393802d1f436c380f0cbbd2828"


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


ENCODER_ENV = "FRAME28_ENCODER"   # auto (por defecto: NVENC si funciona) · nvenc · cpu
NVENC_TTL = 7 * 24 * 3600          # la prueba de NVENC vale una semana para el mismo ffmpeg (cambia con drivers o ffmpeg)


def encoder_mode() -> str:
    """auto, nvenc o cpu según FRAME28_ENCODER (gpu = nvenc; x264, libx264 = cpu; vacío o desconocido = auto)."""
    v = os.environ.get(ENCODER_ENV, "").strip().lower()
    return "nvenc" if v in ("nvenc", "gpu", "cuda") else "cpu" if v in ("cpu", "x264", "libx264") else "auto"


def nvenc_ready(cache: Path | None = None, now: float | None = None, probe=None) -> tuple[bool, str]:
    """¿Codifica este ffmpeg con NVENC? Prueba real de 1 s (h264_nvenc a null) con su resultado en
    ~/.cache/frame28/nvenc.json una semana, ligado a la ruta y el tamaño del ffmpeg. (sí/no, motivo en una línea)."""
    import json
    import time
    ff = ffmpeg()
    if not ff:
        return False, "sin ffmpeg"
    try:
        key = f"{ff}|{os.path.getsize(ff)}"
    except OSError:
        key = ff
    cache = cache or CACHE_DIR / "nvenc.json"
    now = time.time() if now is None else now
    try:
        c = json.loads(cache.read_text(encoding="utf-8-sig"))
        if c.get("key") == key and 0 <= now - float(c.get("at", 0)) < NVENC_TTL:
            return bool(c["ok"]), str(c.get("why", ""))
    except Exception:  # noqa: BLE001  (sin caché o rota: se prueba)
        pass
    if probe is None:
        r = run([ff, "-hide_banner", "-v", "error", "-f", "lavfi", "-i", "color=c=black:s=256x256:r=30:d=1",
                 "-c:v", "h264_nvenc", "-f", "null", "-"], timeout=60)
        ok = r.returncode == 0
        why = "h264_nvenc funciona" if ok else ((r.stderr or "").strip().splitlines() or ["h264_nvenc no disponible"])[-1][:120]
    else:
        ok, why = probe(ff)
    try:
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps({"key": key, "ok": ok, "why": why, "at": now}), encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    return ok, why


_NVDEC: bool | None = None


def nvdec_ready() -> bool:
    """¿Tiene este ffmpeg el decodificador por hardware de NVIDIA (`-hwaccels` incluye cuda)? Se pregunta una vez por
    proceso; el uso real lo decide media.gpu_decode_args (solo H.264/HEVC y con NVENC: AV1 en GPU salió más lento)."""
    global _NVDEC
    if _NVDEC is None:
        ff = ffmpeg()
        r = run([ff, "-hide_banner", "-hwaccels"], timeout=30) if ff else None
        _NVDEC = bool(r and r.returncode == 0 and any(l.strip() == "cuda" for l in (r.stdout or "").splitlines()))
    return _NVDEC


def use_gpu_encoder(enable: bool | None = None) -> bool:
    """¿Se codifica con NVENC? Por defecto (auto) sí, si la GPU NVIDIA y el ffmpeg lo permiten (nvenc_ready); si no, CPU
    sin pedir nada. `enable` lo fuerza para el resto del proceso (--gpu / --cpu). Medido en una RTX 4060: 20 s de 1080p
    en 3,2 s frente a 15,4 s con libx264; el fichero sale mayor. Premisa de Javier (2026-10-03): si la GPU puede, la GPU."""
    if enable is not None:
        os.environ[ENCODER_ENV] = "nvenc" if enable else "cpu"
    mode = encoder_mode()
    if mode != "auto":
        return mode == "nvenc"
    return nvenc_ready()[0]


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


def note(msg: str) -> None:
    """Avisos para la persona (descargas, progreso): siempre por stderr. Muchas órdenes devuelven JSON por stdout y el
    director lo lee con json.loads; un aviso por stdout lo rompía justo en la primera ejecución en una máquina nueva."""
    print(msg, file=sys.stderr, flush=True)


def sha256_file(path: Path) -> str:
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


_VERIFIED: set[str] = set()


def model_ok(path: Path, sha256: str | None) -> bool:
    """¿Está el modelo y es el que debe ser? (una vez por proceso: 15 MB se comprueban en milisegundos)."""
    if not path.exists() or path.stat().st_size == 0:
        return False
    if not sha256 or str(path) in _VERIFIED:
        return True
    ok = sha256_file(path) == sha256
    if ok:
        _VERIFIED.add(str(path))
    return ok


def fetch_atomic(url: str, dest: Path, sha256: str | None = None, timeout: int = 120, headers: dict | None = None,
                 attempts: int = 2) -> Path:
    """Descarga a `<dest>.part-<pid>`, comprueba que llegaron todos los bytes (Content-Length) y el SHA-256 si lo hay, y
    solo entonces lo mueve a `dest` de golpe. Una descarga cortada ya no deja un fichero truncado que parezca bueno."""
    import hashlib
    import urllib.request

    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_name(f"{dest.name}.part-{os.getpid()}")
    last: Exception | None = None
    for _ in range(max(1, attempts)):
        try:
            h, got = hashlib.sha256(), 0
            req = urllib.request.Request(url, headers=headers or {"User-Agent": "frame28"})
            with urllib.request.urlopen(req, timeout=timeout) as r, open(part, "wb") as f:
                expected = int(r.headers.get("Content-Length") or 0)
                for chunk in iter(lambda: r.read(1 << 16), b""):
                    f.write(chunk); h.update(chunk); got += len(chunk)
            if expected and got != expected:
                raise IOError(f"descarga incompleta: {got} de {expected} bytes")
            if sha256 and h.hexdigest() != sha256:
                raise IOError(f"el fichero descargado no es el esperado (SHA-256 {h.hexdigest()[:12]}…, se esperaba {sha256[:12]}…)")
            os.replace(part, dest)
            return dest
        except Exception as e:  # noqa: BLE001  (red o fichero malo: se reintenta una vez y luego se cuenta claro)
            last = e
        finally:
            if part.exists():
                part.unlink()
    raise SystemExit(f"No se pudo descargar {url}: {last}. Comprueba la conexión y repite la orden.")


def download(url: str, dest: Path, label: str, sha256: str | None = None) -> Path:
    """Asegura un modelo en la caché: si está y su SHA-256 cuadra, se usa; si falta o está corrupto (una descarga cortada
    dejaba un .onnx truncado y matte/speaker fallaban para siempre con un error de protobuf), se baja de nuevo, atómico."""
    if model_ok(dest, sha256):
        return dest
    if dest.exists():
        note(f"{label} en {dest} está incompleto o corrupto: se descarga de nuevo")
    note(f"Descargando {label} a {dest} ...")
    fetch_atomic(url, dest, sha256)
    _VERIFIED.add(str(dest))
    return dest


def ensure_rvm_model() -> Path:
    return download(RVM_MODEL_URL, RVM_MODEL_PATH, "modelo RVM (15 MB)", RVM_MODEL_SHA256)
