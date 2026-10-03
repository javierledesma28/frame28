"""Limpieza de audio: filtro de graves, reducción de ruido y normalización de sonoridad (EBU R128) en dos pasadas.

Motores de ruido, de menos a más agresivo/costoso:
- `afftdn`   (ffmpeg, sin descargas): denoiser FFT; bueno para ruido constante (ventilador, ambiente).
- `rnnoise`  (ffmpeg `arnndn` + modelo RNNoise BSD-3 descargado a la caché): red neuronal para voz.
- `deepfilter` (binario externo `deep-filter` si está en PATH): DeepFilterNet, el más limpio.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
import wave
from pathlib import Path

import numpy as np

from .env import CACHE_DIR, ffmpeg, run

# fijado a un commit (antes la rama master, que puede cambiar) y con su SHA-256
RNNOISE_MODEL_URL = ("https://raw.githubusercontent.com/GregorR/rnnoise-models/3eee541a283fd3b8f81b85b1748e3b9ccbefa04d/"
                     "somnolent-hogwash-2018-09-01/sh.rnnn")
RNNOISE_MODEL_SHA256 = "70bb6685eb0c2a1d18e2918dca3fbfbd39317010b1802eb1b6ea73a92f3fdec0"
RNNOISE_MODEL_PATH = CACHE_DIR / "rnnoise-sh.rnnn"


def measure(path: str | Path) -> dict:
    """Sonoridad integrada (LUFS), rango (LU), pico real (dBTP) y suelo de ruido (dBFS, RMS del 10 % más silencioso)."""
    r = run([ffmpeg(), "-hide_banner", "-i", str(path), "-af", "ebur128=peak=true", "-f", "null", "-"])
    txt = r.stderr
    def grab(pat):
        m = re.findall(pat, txt)
        return float(m[-1]) if m else None
    out = {"integrated_lufs": grab(r"I:\s+([-\d.]+) LUFS"), "lra_lu": grab(r"LRA:\s+([-\d.]+) LU"),
           "true_peak_dbtp": grab(r"Peak:\s+([-\d.]+) dBFS")}
    # suelo de ruido: RMS por ventanas de 50 ms sobre un WAV temporal mono 16 kHz
    tmp = Path(tempfile.mkdtemp(prefix="frame28_audio_")) / "m.wav"
    run([ffmpeg(), "-v", "error", "-y", "-i", str(path), "-ac", "1", "-ar", "16000", "-sample_fmt", "s16", str(tmp)])
    try:
        with wave.open(str(tmp), "rb") as w:
            x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
            rate = w.getframerate()
        win = int(rate * 0.05); n = len(x) // win
        rms = np.sqrt((x[: n * win].reshape(n, win) ** 2).mean(axis=1) + 1e-12)
        db = np.sort(20 * np.log10(rms + 1e-9))
        k = max(1, int(len(db) * 0.10))
        out["noise_floor_dbfs"] = round(float(db[:k].mean()), 1)
        out["speech_level_dbfs"] = round(float(db[-k:].mean()), 1)
        out["snr_db"] = round(out["speech_level_dbfs"] - out["noise_floor_dbfs"], 1)
        out["duration"] = round(len(x) / rate, 2)
    finally:
        shutil.rmtree(tmp.parent, ignore_errors=True)
    return out


def _denoise_filter(engine: str, strength: int) -> str | None:
    if engine == "none":
        return None
    if engine == "afftdn":
        # nr en dB (6–30); nf = suelo de ruido estimado; tn = seguimiento del ruido
        return f"afftdn=nr={strength}:nf=-45:tn=1"
    if engine == "rnnoise":
        from .env import download
        download(RNNOISE_MODEL_URL, RNNOISE_MODEL_PATH, "modelo RNNoise", RNNOISE_MODEL_SHA256)
        # la ruta del modelo se pasa relativa: ffmpeg se ejecuta con cwd=CACHE_DIR (los dos puntos de "C:" rompen el filtergraph)
        return f"arnndn=m={RNNOISE_MODEL_PATH.name}:mix=0.9"
    raise SystemExit(f"motor de ruido desconocido: {engine} (none, afftdn, rnnoise, deepfilter)")


def _deepfilter(src: Path, dst: Path) -> None:
    exe = shutil.which("deep-filter")
    if not exe:
        raise SystemExit("deep-filter no está en PATH. Descárgalo de https://github.com/Rikorose/DeepFilterNet/releases o usa --denoise rnnoise")
    outdir = dst.parent / "_df"; outdir.mkdir(exist_ok=True)
    r = subprocess.run([exe, "-o", str(outdir), str(src)], capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(r.stderr)
    produced = next(outdir.glob("*.wav"))
    shutil.move(str(produced), str(dst)); shutil.rmtree(outdir, ignore_errors=True)


def clean(src: str | Path, dst: str | Path, denoise: str = "afftdn", strength: int = 12, lufs: float = -14.0,
          tp: float = -1.5, lra: float = 11.0, highpass: int = 80, deess: bool = False) -> dict:
    """Devuelve medidas antes/después y la cadena de filtros usada."""
    src, dst = Path(src).resolve(), Path(dst).resolve(); dst.parent.mkdir(parents=True, exist_ok=True)
    before = measure(src)
    work = src
    cwd = str(CACHE_DIR) if denoise == "rnnoise" else None
    tmpdir = Path(tempfile.mkdtemp(prefix="frame28_clean_"))
    if denoise == "deepfilter":
        work = tmpdir / "df.wav"
        run([ffmpeg(), "-v", "error", "-y", "-i", str(src), "-ac", "1", "-ar", "48000", str(tmpdir / "in.wav")])
        _deepfilter(tmpdir / "in.wav", work)
        pre = []
    else:
        f = _denoise_filter(denoise, strength)
        pre = [f] if f else []
    chain = ([f"highpass=f={highpass}"] if highpass else []) + pre + (["deesser"] if deess else [])
    # pasada 1: medir con loudnorm
    f1 = ",".join(chain + [f"loudnorm=I={lufs}:TP={tp}:LRA={lra}:print_format=json"])
    r = run([ffmpeg(), "-hide_banner", "-i", str(work), "-af", f1, "-f", "null", "-"], cwd=cwd)
    m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", r.stderr, re.S)
    if not m:
        raise SystemExit("loudnorm no devolvió medidas:\n" + r.stderr[-800:])
    meas = json.loads(m.group(0))
    # pasada 2: aplicar con las medidas (modo lineal, sin bombeo)
    ln = (f"loudnorm=I={lufs}:TP={tp}:LRA={lra}:measured_I={meas['input_i']}:measured_TP={meas['input_tp']}:"
          f"measured_LRA={meas['input_lra']}:measured_thresh={meas['input_thresh']}:offset={meas['target_offset']}:linear=true")
    f2 = ",".join(chain + [ln])
    r = run([ffmpeg(), "-v", "error", "-y", "-i", str(work), "-af", f2, "-ar", "48000", "-ac", "2", str(dst)], cwd=cwd)
    if r.returncode != 0:
        raise SystemExit(r.stderr)
    shutil.rmtree(tmpdir, ignore_errors=True)
    after = measure(dst)
    return {"output": str(dst), "denoise": denoise, "filters": f2, "before": before, "after": after,
            "noise_reduction_db": round((after["snr_db"] or 0) - (before["snr_db"] or 0), 1)}


def spectrogram(paths: list[str | Path], out_png: str | Path, width: int = 1200, height: int = 300) -> Path:
    """Espectrogramas apilados (uno por fichero) para comparar antes/después de un vistazo."""
    inputs = []; fc = []
    for i, p in enumerate(paths):
        inputs += ["-i", str(p)]
        fc.append(f"[{i}:a]aformat=channel_layouts=mono,showspectrumpic=s={width}x{height}:legend=0:scale=log:color=fiery[s{i}]")
    fc = ";".join(fc) + ";" + "".join(f"[s{i}]" for i in range(len(paths))) + f"vstack=inputs={len(paths)}[v]"
    r = run([ffmpeg(), "-v", "error", "-y", *inputs, "-filter_complex", fc, "-map", "[v]", "-frames:v", "1", str(out_png)])
    if r.returncode != 0:
        raise SystemExit(r.stderr)
    return Path(out_png)
