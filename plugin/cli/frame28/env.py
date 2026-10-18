"""Localización de binarios externos (ffmpeg, npx) y rutas de caché. Windows-friendly."""
from __future__ import annotations

import functools
import glob
import os
import re
import shutil
import subprocess
import sys
import tempfile
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


def _version_key(path: str) -> tuple:
    """Orden por versión, no por texto: ffmpeg-10.0 va después de ffmpeg-9.0.2 (como texto iba antes, F28-94)."""
    return tuple(tuple(int(x) for x in v.split(".")) for v in re.findall(r"\d+(?:\.\d+)+", path)), path


@functools.lru_cache(maxsize=None)
def _winget_best(exe: str) -> str | None:
    """El ejecutable de mayor versión entre los paquetes de WinGet. Se busca una vez por proceso: el glob recursivo
    sobre Packages tarda y antes se repetía en cada ffmpeg() (F28-94)."""
    cands = _winget_candidates(exe)
    return max(cands, key=_version_key) if cands else None


def find_tool(name: str, env_var: str | None = None) -> str | None:
    """Busca un ejecutable: variable de entorno explícita, PATH, y en Windows los paquetes de WinGet."""
    if env_var and os.environ.get(env_var):
        return os.environ[env_var]
    found = shutil.which(name)
    if found:
        return found
    if os.name == "nt":
        return _winget_best(name)
    return None


def ffmpeg_install_hint() -> str:
    """Cómo instalar ffmpeg en esta plataforma (antes el error decía winget también en Mac y Linux, F28-94)."""
    if sys.platform == "win32":
        return "winget install --id Gyan.FFmpeg -e"
    if sys.platform == "darwin":
        return "brew install ffmpeg"
    return "sudo apt install ffmpeg (o el gestor de paquetes de tu distribución)"


def ffmpeg() -> str:
    p = find_tool("ffmpeg", "FRAME28_FFMPEG")
    if not p:
        raise SystemExit(f"ffmpeg no encontrado. Instálalo con: {ffmpeg_install_hint()} y abre una terminal nueva "
                         "(o define FRAME28_FFMPEG)")
    return p


def ffprobe() -> str:
    p = find_tool("ffprobe", "FRAME28_FFPROBE")
    if not p:
        # mismo directorio que ffmpeg
        cand = Path(ffmpeg()).with_name("ffprobe.exe" if os.name == "nt" else "ffprobe")
        if cand.exists():
            return str(cand)
        raise SystemExit(f"ffprobe no encontrado: viene con ffmpeg. Instálalo con: {ffmpeg_install_hint()} "
                         "(o define FRAME28_FFPROBE)")
    return p


def npx() -> str:
    p = shutil.which("npx") or shutil.which("npx.cmd")
    if not p:
        raise SystemExit("npx no encontrado: instala Node.js 22+ (https://nodejs.org)")
    return p


def npx_cmd(found: str | None = None) -> list[str]:
    """La orden para lanzar npx sin pasar por cmd.exe. En Windows npx es un .cmd y Python lo ejecuta con cmd.exe, que no
    escapa sus metacaracteres: una ruta con & (C:\\Clientes\\R&D\\) se partía y el resto se ejecutaba como otra orden
    (comprobado el 2026-10-03, F28-87). El .cmd solo hace `node npx-cli.js`: se llama a node directamente. Fuera de
    Windows, o si no aparece npx-cli.js junto al .cmd, npx tal cual."""
    raw = found or npx()
    p = Path(raw)
    if p.suffix.lower() in (".cmd", ".bat") or (os.name == "nt" and p.suffix == ""):
        cli = p.parent / "node_modules" / "npm" / "bin" / "npx-cli.js"
        node = p.parent / "node.exe"
        if not node.exists():
            node = Path(shutil.which("node") or "node")
        if cli.exists():
            return [str(node), str(cli)]
    return [raw]


def run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    """subprocess.run con salida en texto y sin lanzar excepción por defecto."""
    kw.setdefault("text", True)
    kw.setdefault("capture_output", True)
    kw.setdefault("encoding", "utf-8")
    kw.setdefault("errors", "replace")
    return subprocess.run(cmd, **kw)


def _ok(r: subprocess.CompletedProcess, what: str) -> subprocess.CompletedProcess:
    if r.returncode != 0:
        tail = (r.stderr or r.stdout or "").strip()[-800:]
        raise SystemExit(f"{what}: {Path(r.args[0]).stem} salió con el código {r.returncode}" + (f"\n{tail}" if tail else ""))
    return r


def run_ok(cmd: list[str], what: str, **kw) -> subprocess.CompletedProcess:
    """`run` para los pasos de los que depende el siguiente: si la orden falla, para diciendo qué paso era y el final
    de su error. Antes prep, cut apply y audio seguían como si nada y dejaban el trabajo a medias (F28-93)."""
    return _ok(run(cmd, **kw), what)


def run_filter_complex(before: list[str], fc: str, after: list[str], what: str) -> subprocess.CompletedProcess:
    """ffmpeg con un -filter_complex que puede ser muy largo (cut apply con cientos de tramos). Va en un fichero: en
    línea, con ~280 tramos pasa del límite de 32 767 caracteres de una orden de Windows y Python lanza WinError 206
    (F28-94). `-/filter_complex fichero` es la forma de ffmpeg 7 o posterior (la 9 ya no tiene -filter_complex_script);
    con uno anterior se repite con la antigua. Para como `run_ok` si falla."""
    with tempfile.TemporaryDirectory(prefix="frame28_fc_") as tmp:
        script = Path(tmp) / "filter_complex.txt"
        script.write_text(fc, encoding="utf-8")
        r = run([ffmpeg(), *before, "-/filter_complex", str(script), *after])
        if r.returncode != 0 and "Unrecognized option" in (r.stderr or "") and "filter_complex" in r.stderr:
            r = run([ffmpeg(), *before, "-filter_complex_script", str(script), *after])
    return _ok(r, what)


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


ONNX_ENV = "FRAME28_ONNX"   # auto (por defecto: CUDA si onnxruntime-gpu la trae; el OCR, CPU) · gpu · cpu
GPU_EXCLUDES = "excluir-gpu.txt"
# De dónde se instala el motor y con qué versiones (F28-91). PINNED_EXTRA es el extra de pyproject con las versiones
# exactas con las que pasaron las pruebas; RELEASE_REF, la rama de la que sale el código: main hasta la primera release
# fijada, después `release` (apunta siempre a la última release publicada, y `uv tool upgrade` la sigue).
GIT_REPO = "https://github.com/javierledesma28/frame28"
RELEASE_REF = ""
PINNED_EXTRA = "probado"
GIT_SPEC = f"git+{GIT_REPO}{'@' + RELEASE_REF if RELEASE_REF else ''}#subdirectory=plugin/cli"
GPU_EXCLUDES_URL = f"https://raw.githubusercontent.com/javierledesma28/frame28/{RELEASE_REF or 'main'}/plugin/cli/{GPU_EXCLUDES}"
INSTALLER = {"win32": "irm https://frame28.t28.io/install.ps1 | iex"}
INSTALLER_UNIX = "curl -fsSL https://frame28.t28.io/install.sh | bash"


def install_spec(gpu: bool = False) -> str:
    """Lo que se instala con uv: el CLI con las versiones probadas (y el extra gpu si se pide)."""
    return f"frame28[{'gpu,' if gpu else ''}{PINNED_EXTRA}] @ {GIT_SPEC}"


def installer_cmd() -> str:
    """La línea del instalador de esta plataforma: también actualiza y deja el motor con las versiones probadas."""
    return INSTALLER.get(sys.platform, INSTALLER_UNIX)


def onnx_mode() -> str:
    """auto, gpu o cpu según FRAME28_ONNX (cuda = gpu; vacío o desconocido = auto)."""
    v = os.environ.get(ONNX_ENV, "").strip().lower()
    return "gpu" if v in ("gpu", "cuda") else "cpu" if v == "cpu" else "auto"


def onnx_providers(gpu: bool | None = None, available: list[str] | None = None) -> list[str]:
    """Proveedores de onnxruntime para matte (RVM) y OCR: CUDA delante si onnxruntime-gpu la trae (extra `gpu`) y nadie
    pidió CPU (`--cpu`, FRAME28_ONNX=cpu); la CPU siempre detrás, como caída. `gpu=True` (o FRAME28_ONNX=gpu) sin CUDA es
    un error con el arreglo, no un paso a CPU callado."""
    if available is None:
        import onnxruntime as ort
        available = ort.get_available_providers()
    want = onnx_mode() if gpu is None else ("gpu" if gpu else "cpu")
    if want != "cpu" and "CUDAExecutionProvider" in available:
        enable_cuda_dlls()   # cuBLAS y cuDNN del extra, las mismas que usa faster-whisper
        return ["CUDAExecutionProvider", "CPUExecutionProvider"]
    if want == "gpu":
        raise SystemExit("onnxruntime no trae CUDA: instala el extra gpu (frame28 doctor da la orden) o quita --gpu / FRAME28_ONNX=gpu")
    return ["CPUExecutionProvider"]


def gpu_install_cmd(editable_dir: str | None = None) -> str:
    """Orden para instalar el CLI con el extra `gpu`. El extra trae onnxruntime-gpu, que ocupa el mismo módulo que
    onnxruntime (lo pide faster-whisper): sin `--excludes` uv instala los dos y el que gane al copiar ficheros decide si
    hay CUDA. uv guarda el `--excludes` en la instalación, así que `uv tool upgrade` lo respeta."""
    if editable_dir:
        d = editable_dir.rstrip("/\\")
        return f'uv tool install --editable "{d}[gpu,{PINNED_EXTRA}]" --python 3.12 --excludes "{d}/{GPU_EXCLUDES}" --reinstall'
    return f'uv tool install "{install_spec(gpu=True)}" --python 3.12 --excludes {GPU_EXCLUDES_URL} --reinstall'


def onnxruntime_dists() -> list[str]:
    """Paquetes instalados que dan el módulo onnxruntime (onnxruntime, onnxruntime-gpu, -directml…). Más de uno = roto:
    comparten carpeta y cada uno pisa los ficheros del otro."""
    import importlib.metadata as md
    names = set()
    for d in md.distributions():
        if any(str(f).replace("\\", "/") == "onnxruntime/__init__.py" for f in (d.files or [])):
            names.add((d.metadata.get("Name") or "").lower().replace("_", "-"))
    return sorted(names)


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


NOTICES_URL = "https://github.com/javierledesma28/frame28/blob/main/THIRD-PARTY-NOTICES.md"


def download(url: str, dest: Path, label: str, sha256: str | None = None, license: str | None = None) -> Path:
    """Asegura un modelo en la caché: si está y su SHA-256 cuadra, se usa; si falta o está corrupto (una descarga cortada
    dejaba un .onnx truncado y matte/speaker fallaban para siempre con un error de protobuf), se baja de nuevo, atómico.
    Al descargarlo dice de dónde viene y con qué licencia (F28-198): el modelo no va con Frame28, lo baja el usuario."""
    if model_ok(dest, sha256):
        return dest
    if dest.exists():
        note(f"{label} en {dest} está incompleto o corrupto: se descarga de nuevo")
    note(f"Descargando {label} a {dest} ...")
    if license:
        note(f"  Licencia: {license}. Origen: {url.split('/')[2]}. Detalle: {NOTICES_URL}")
    fetch_atomic(url, dest, sha256)
    _VERIFIED.add(str(dest))
    return dest


def ensure_rvm_model() -> Path:
    return download(RVM_MODEL_URL, RVM_MODEL_PATH, "modelo RVM (15 MB)", RVM_MODEL_SHA256,
                    license="GPL-3.0 (RobustVideoMatting; se descarga de su repositorio y no se redistribuye con Frame28)")
