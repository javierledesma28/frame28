"""probe, prep, sheet: operaciones ffmpeg sobre el clip de entrada."""
from __future__ import annotations

import json
import re
from pathlib import Path

from .env import ffmpeg, ffprobe, run


def probe(video: str | Path) -> dict:
    r = run([ffprobe(), "-v", "error", "-show_entries",
            "format=duration,bit_rate:stream=codec_type,codec_name,width,height,r_frame_rate,sample_rate,channels",
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
                            "fps": round(int(num) / int(den), 3)}
        elif s["codec_type"] == "audio" and out["audio"] is None:
            out["audio"] = {"codec": s["codec_name"], "sample_rate": int(s["sample_rate"]), "channels": s["channels"]}
    if out["audio"]:
        v = run([ffmpeg(), "-i", str(video), "-af", "volumedetect", "-f", "null", "-"])
        m = re.search(r"mean_volume: ([-\d.]+) dB", v.stderr)
        x = re.search(r"max_volume: ([-\d.]+) dB", v.stderr)
        out["audio"]["mean_db"] = float(m.group(1)) if m else None
        out["audio"]["max_db"] = float(x.group(1)) if x else None
    return out


def prep(video: str | Path, out_dir: str | Path, fps: int = 30, width: int | None = None) -> dict:
    """Copia de trabajo: vídeo a `fps` sin audio, voz normalizada a -16 LUFS (48k estéreo) y mono 16k para ASR."""
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    info = probe(video)
    vf = f"fps={fps}" + (f",scale={width}:-2" if width else "")
    clip = out / "clip.mp4"
    r = run([ffmpeg(), "-v", "error", "-y", "-i", str(video), "-vf", vf, "-an", "-c:v", "libx264", "-crf", "16",
             "-pix_fmt", "yuv420p", str(clip)])
    if r.returncode != 0:
        raise SystemExit(r.stderr)
    result = {"clip": str(clip), "probe": info, "fps": fps}
    if info["audio"]:
        loud = "loudnorm=I=-16:TP=-1.5:LRA=11"
        voice = out / "voice.wav"; a16 = out / "audio16k.wav"
        run([ffmpeg(), "-v", "error", "-y", "-i", str(video), "-vn", "-ac", "2", "-ar", "48000", "-af", loud, str(voice)])
        run([ffmpeg(), "-v", "error", "-y", "-i", str(video), "-vn", "-ac", "1", "-ar", "16000", "-af", loud, str(a16)])
        result.update({"voice": str(voice), "audio16k": str(a16)})
    (out / "probe.json").write_text(json.dumps(result, indent=1, ensure_ascii=False), encoding="utf-8")
    return result


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
             "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", str(out_mp4)])
    if r.returncode != 0:
        raise SystemExit(r.stderr)
    return Path(out_mp4)
