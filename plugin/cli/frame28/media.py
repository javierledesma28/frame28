"""probe, prep, sheet: operaciones ffmpeg sobre el clip de entrada."""
from __future__ import annotations

import json
import math
import re
from pathlib import Path

from .env import encoder_args, ffmpeg, ffprobe, run


def probe(video: str | Path) -> dict:
    r = run([ffprobe(), "-v", "error", "-show_entries",
            "format=duration,bit_rate:stream=codec_type,codec_name,width,height,r_frame_rate,pix_fmt,sample_rate,channels",
            "-of", "json", str(video)])
    if r.returncode != 0:
        raise SystemExit(r.stderr)
    info = json.loads(r.stdout)
    out: dict = {"path": str(video), "duration": float(info["format"].get("duration", 0)),
                 "bit_rate": int(info["format"].get("bit_rate", 0) or 0), "video": None, "audio": None}
    for s in info.get("streams", []):
        if s["codec_type"] == "video" and out["video"] is None:
            num, den = s["r_frame_rate"].split("/")
            out["video"] = {"codec": s["codec_name"], "width": s["width"], "height": s["height"],
                            "fps": round(int(num) / int(den), 3), "pix_fmt": s.get("pix_fmt")}
        elif s["codec_type"] == "audio" and out["audio"] is None:
            out["audio"] = {"codec": s["codec_name"], "sample_rate": int(s["sample_rate"]), "channels": s["channels"]}
    if out["audio"]:
        v = run([ffmpeg(), "-i", str(video), "-af", "volumedetect", "-f", "null", "-"])
        m = re.search(r"mean_volume: ([-\d.]+) dB", v.stderr)
        x = re.search(r"max_volume: ([-\d.]+) dB", v.stderr)
        out["audio"]["mean_db"] = float(m.group(1)) if m else None
        out["audio"]["max_db"] = float(x.group(1)) if x else None
    return out


def scale_filter(info: dict, size: int | None) -> str:
    """`--width` es el lado largo: un apaisado queda a ese ancho y un vertical a esa altura (antes un vertical de
    1080×1920 con --width 1920 subía a 1920×3413). Sin dimensiones conocidas, se escala por ancho como antes."""
    if not size:
        return ""
    w, h = int(info.get("width") or 0), int(info.get("height") or 0)
    return f",scale=-2:{size}" if h > w > 0 else f",scale={size}:-2"


# Decodificar en la GPU (NVDEC) solo compensa con estos códecs. Medido el 2026-10-03 en una RTX 4060 + 16 núcleos, prep
# completo (fps=30 + NVENC): H.264 de 83 s 14,8 → 11,0 s con la CPU libre y 28,6 → 18,8 s con la CPU ocupada; AV1 de 160 s
# 21,5 → 20,5 s libre y 27,1 → 66,4 s ocupada (dav1d en CPU gana). Solo con el camino entero en GPU (sin bajar fotogramas a
# la memoria: -hwaccel_output_format cuda); bajándolos, H.264 no ganaba y AV1 pasaba de 21,5 a 37 s.
NVDEC_CODECS = ("h264", "hevc")


def scaled_size(info: dict, size: int | None) -> tuple[int, int] | None:
    """Ancho y alto pares tras escalar el lado largo a `size` (lo mismo que scale_filter, en números para scale_cuda)."""
    w, h = int(info.get("width") or 0), int(info.get("height") or 0)
    if not size or not w or not h:
        return None
    if h > w:
        nw, nh = w * size / h, size
    else:
        nw, nh = size, h * size / w
    return int(round(nw / 2)) * 2, int(round(nh / 2)) * 2


def gpu_decode_args(info: dict, fps: int, size: int | None) -> tuple[list[str], str] | None:
    """(argumentos antes de -i, filtro de vídeo) para decodificar, cambiar fps, escalar y pasar a NVENC sin salir de la
    GPU; None si no toca (otro códec, sin NVENC o sin NVDEC) y se hace como siempre."""
    from .env import nvdec_ready, use_gpu_encoder
    v = info.get("video") or {}
    if v.get("codec") not in NVDEC_CODECS or not use_gpu_encoder() or not nvdec_ready():
        return None
    sz = scaled_size(v, size)
    scale = f"scale_cuda=w={sz[0]}:h={sz[1]}:format=yuv420p" if sz else "scale_cuda=format=yuv420p"
    return ["-hwaccel", "cuda", "-hwaccel_output_format", "cuda"], f"fps={fps},{scale}"


def prep(video: str | Path, out_dir: str | Path, fps: int = 30, width: int | None = None, normalize: bool = True) -> dict:
    """Copia de trabajo: vídeo a `fps` sin audio, voz normalizada a -16 LUFS (48k estéreo) y mono 16k para ASR."""
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    info = probe(video)
    vf = f"fps={fps}" + scale_filter(info.get("video") or {}, width)
    clip = out / "clip.mp4"
    gop = ["-g", str(fps), "-keyint_min", str(fps)]  # un fotograma clave por segundo: HyperFrames avisa de saltos si van espaciados
    decoder, r = "cpu", None
    gpu = gpu_decode_args(info, fps, width)
    if gpu:
        pre, gvf = gpu
        r = run([ffmpeg(), "-v", "error", "-y", *pre, "-i", str(video), "-vf", gvf, "-an", *encoder_args(16), *gop, str(clip)])
        decoder = "nvdec" if r.returncode == 0 else "cpu (nvdec falló)"
    if r is None or r.returncode != 0:  # el camino de siempre (y la caída si la GPU no pudo con este vídeo)
        r = run([ffmpeg(), "-v", "error", "-y", "-i", str(video), "-vf", vf, "-an", *encoder_args(16), *gop, "-pix_fmt", "yuv420p", str(clip)])
    if r.returncode != 0:
        raise SystemExit(r.stderr)
    result = {"clip": str(clip), "probe": info, "fps": fps, "decoder": decoder}
    if info["audio"]:
        af = ["-af", "loudnorm=I=-16:TP=-1.5:LRA=11"] if normalize else []
        voice = out / "voice.wav"; a16 = out / "audio16k.wav"
        run([ffmpeg(), "-v", "error", "-y", "-i", str(video), "-vn", "-ac", "2", "-ar", "48000", *af, str(voice)])
        run([ffmpeg(), "-v", "error", "-y", "-i", str(video), "-vn", "-ac", "1", "-ar", "16000", *af, str(a16)])
        result.update({"voice": str(voice), "audio16k": str(a16)})
    (out / "probe.json").write_text(json.dumps(result, indent=1, ensure_ascii=False), encoding="utf-8")
    return result


def sheet_plan(duration: float, max_frames: int = 48) -> tuple[float, int, int]:
    """(every, cols, rows) para que la hoja de contacto cubra el vídeo entero: un fotograma por segundo en clips de
    hasta 20 s (4×5) y, en los largos, entre 20 y `max_frames` repartidos por toda la duración (uno cada ~3 s).
    Con el paso fijo de 1 s, la hoja de un vídeo de 160 s enseñaba solo los primeros 20."""
    if duration <= 20.0:
        return 1.0, 4, 5
    cols = 6
    rows = math.ceil(min(max_frames, max(20, math.ceil(duration / 3.0))) / cols)
    return round(duration / (cols * rows), 3), cols, rows


def sheet(video: str | Path, out_png: str | Path, every: float = 1.0, cols: int = 4, rows: int = 5, width: int = 480) -> Path:
    """Hoja de contacto: un fotograma cada `every` segundos, en rejilla cols×rows."""
    r = run([ffmpeg(), "-v", "error", "-y", "-i", str(video), "-vf",
             f"fps=1/{every},scale={width}:-1,tile={cols}x{rows}", "-frames:v", "1", str(out_png)])
    if r.returncode != 0:
        raise SystemExit(r.stderr)
    return Path(out_png)


def frame_at(video: str | Path, t: float, out_png: str | Path, width: int | None = None) -> Path:
    vf = ["-vf", f"scale={width}:-1"] if width else []
    r = run([ffmpeg(), "-v", "error", "-y", "-ss", str(t), "-i", str(video), "-frames:v", "1", *vf, str(out_png)])
    if r.returncode != 0:
        raise SystemExit(r.stderr)
    return Path(out_png)


def cut(video: str | Path, start: float, end: float, out_mp4: str | Path) -> Path:
    r = run([ffmpeg(), "-v", "error", "-y", "-ss", str(start), "-t", str(end - start), "-i", str(video), "-an",
             *encoder_args(16), "-pix_fmt", "yuv420p", str(out_mp4)])
    if r.returncode != 0:
        raise SystemExit(r.stderr)
    return Path(out_mp4)


def fetch_url(url: str, out_mp4: str | Path, max_height: int = 1080) -> dict:
    """Descarga un vídeo de YouTube/Vimeo/etc. como MP4 (vídeo <= max_height + audio) con yt-dlp. Si yt-dlp no está
    instalado, lo ejecuta con `uvx` (entorno efímero: no instala nada). Devuelve título, duración y ruta."""
    import json as _json
    from .env import find_tool, run
    out = Path(out_mp4); out.parent.mkdir(parents=True, exist_ok=True)
    ytdlp = find_tool("yt-dlp")
    base = [ytdlp] if ytdlp else ([find_tool("uv") or "uv", "tool", "run", "--python", "3.12", "yt-dlp"])
    node = find_tool("node")
    common = ["--no-playlist"] + (["--js-runtimes", "node"] if node else [])
    info = run(base + common + ["--print", "%(title)s\t%(duration)s\t%(uploader)s\t%(upload_date)s", url])
    if info.returncode != 0:
        raise SystemExit("yt-dlp falló:\n" + (info.stderr or info.stdout)[-800:])
    title, dur, up, date = (info.stdout.strip().splitlines()[-1].split("\t") + ["", "", "", ""])[:4]
    fmt = f"bv*[height<={max_height}][ext=mp4]+ba[ext=m4a]/b[ext=mp4]/b"
    r = run(base + common + ["-f", fmt, "--merge-output-format", "mp4", "-o", str(out), url])
    if r.returncode != 0 or not out.exists():
        raise SystemExit("yt-dlp falló:\n" + (r.stderr or r.stdout)[-800:])
    side = {"url": url, "title": title, "duration": float(dur) if dur.replace(".", "").isdigit() else None, "uploader": up, "upload_date": date, "file": str(out)}
    out.with_suffix(".source.json").write_text(_json.dumps(side, indent=1, ensure_ascii=False), encoding="utf-8")
    return side
