"""Máscara alfa del hablante con RobustVideoMatting (ONNX) y detección de dónde está el hablante en el encuadre."""
from __future__ import annotations

import json
import shutil
import tempfile
import time
from pathlib import Path

import cv2
import numpy as np

from .env import ensure_rvm_model, ffmpeg, run
from .media import cut, frame_at
from .imgio import imwrite


def auto_ratio(width: int, height: int) -> float:
    """Tabla del paper para retrato: <=512 → 1, 720p → 0.375, 1080p → 0.25, 4K → 0.125."""
    m = max(width, height)
    if m <= 512:
        return 1.0
    if m <= 1280:
        return 0.375
    if m <= 1920:
        return 0.25
    return 0.125


def _session():
    import onnxruntime as ort
    providers = ["CUDAExecutionProvider", "CPUExecutionProvider"] if "CUDAExecutionProvider" in ort.get_available_providers() else ["CPUExecutionProvider"]
    return ort.InferenceSession(str(ensure_rvm_model()), providers=providers), providers[0]


def matte_frames(video: str | Path, png_dir: str | Path, ratio: float | None = None) -> dict:
    """Genera PNG RGBA por fotograma (RGB = foreground predicho, A = alfa)."""
    sess, provider = _session()
    out = Path(png_dir); out.mkdir(parents=True, exist_ok=True)
    cap = cv2.VideoCapture(str(video))
    w, h = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    ratio = ratio or auto_ratio(w, h)
    rec = [np.zeros([1, 1, 1, 1], dtype=np.float32)] * 4
    ds = np.array([ratio], dtype=np.float32)
    n, t0 = 0, time.time()
    while True:
        ok, bgr = cap.read()
        if not ok:
            break
        x = np.transpose(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0, (2, 0, 1))[None]
        fgr, pha, *rec = sess.run([], {"src": x, "r1i": rec[0], "r2i": rec[1], "r3i": rec[2], "r4i": rec[3], "downsample_ratio": ds})
        fg = (np.transpose(fgr[0], (1, 2, 0)) * 255).clip(0, 255).astype(np.uint8)
        a = (pha[0, 0] * 255).clip(0, 255).astype(np.uint8)
        imwrite(str(out / f"f_{n:04d}.png"), np.dstack([cv2.cvtColor(fg, cv2.COLOR_RGB2BGR), a]))
        n += 1
    dt = time.time() - t0
    return {"frames": n, "seconds": round(dt, 1), "fps": round(n / dt, 2) if dt else None, "ratio": ratio, "provider": provider, "width": w, "height": h}


def png_to_webm(png_dir: str | Path, out_webm: str | Path, fps: int = 30, crf: int = 20) -> Path:
    r = run([ffmpeg(), "-v", "error", "-y", "-framerate", str(fps), "-i", str(Path(png_dir) / "f_%04d.png"),
             "-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p", "-b:v", "0", "-crf", str(crf), "-auto-alt-ref", "0", str(out_webm)])
    if r.returncode != 0:
        raise SystemExit(r.stderr)
    return Path(out_webm)


def matte(video: str | Path, out_webm: str | Path, start: float | None = None, end: float | None = None,
          ratio: float | None = None, fps: int = 30, keep_png: str | Path | None = None) -> dict:
    """Máscara alfa como WebM VP9 con alfa. Con start/end recorta primero (solo el tramo que necesita texto detrás)."""
    tmp = Path(tempfile.mkdtemp(prefix="frame28_matte_"))
    src = Path(video)
    if start is not None and end is not None:
        src = cut(video, start, end, tmp / "seg.mp4")
    png_dir = Path(keep_png) if keep_png else tmp / "png"
    stats = matte_frames(src, png_dir, ratio)
    png_to_webm(png_dir, out_webm, fps)
    stats.update({"webm": str(out_webm), "start": start, "end": end})
    shutil.rmtree(tmp, ignore_errors=True)
    return stats


def speaker_layout(video: str | Path, samples: int = 6, duration: float | None = None, canvas: tuple[int, int] | None = None) -> dict:
    """Dónde está el hablante: bbox unión de `samples` fotogramas (alfa > 0.5) y lado libre para overlays.
    Coordenadas en el lienzo del storyboard (`canvas`; por defecto según el formato del clip: 1920×1080, 1080×1920 o 1080×1080)."""
    from .captions import default_canvas
    sess, _ = _session()
    cap = cv2.VideoCapture(str(video))
    n_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)); fps = cap.get(cv2.CAP_PROP_FPS) or 30
    w, h = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    ds = np.array([auto_ratio(w, h)], dtype=np.float32)
    union = np.zeros((h, w), dtype=bool)
    idxs = np.linspace(0, max(n_frames - 1, 0), samples).astype(int)
    for i in idxs:
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(i))
        ok, bgr = cap.read()
        if not ok:
            continue
        rec = [np.zeros([1, 1, 1, 1], dtype=np.float32)] * 4
        x = np.transpose(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0, (2, 0, 1))[None]
        _, pha, *_ = sess.run([], {"src": x, "r1i": rec[0], "r2i": rec[1], "r3i": rec[2], "r4i": rec[3], "downsample_ratio": ds})
        union |= pha[0, 0] > 0.5
    ys, xs = np.where(union)
    if len(xs) == 0:
        return {"found": False}
    x0, x1, y0, y1 = int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max())
    cx = (x0 + x1) / 2 / w
    side = "left" if cx < 0.4 else "right" if cx > 0.6 else "center"
    free = "right" if side == "left" else "left" if side == "right" else "sides"
    # escala al lienzo del storyboard (el clip se ajusta con object-fit: cover, así que el eje de menor recorte manda)
    cw, ch = canvas or default_canvas(w, h)
    sx, sy = cw / w, ch / h
    bbox_c = [round(x0 * sx), round(y0 * sy), round(x1 * sx), round(y1 * sy)]
    return {"found": True, "frame": [w, h], "canvas": [cw, ch], "bbox": [x0, y0, x1, y1],
            "bbox_canvas": bbox_c, "bbox_1080p": bbox_c,  # bbox_1080p: alias antiguo, mismas coordenadas
            "center_x": round(cx, 3), "side": side, "free_side": free,
            "head_top": bbox_c[1], "head_top_1080p": bbox_c[1], "samples": int(len(idxs))}
