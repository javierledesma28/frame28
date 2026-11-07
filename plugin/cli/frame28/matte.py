"""Máscara alfa del hablante con RobustVideoMatting (ONNX), tramos de máscara de un storyboard con su caché, y detección
de dónde está el hablante en el encuadre."""
from __future__ import annotations

import hashlib
import json
import math
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

import cv2
import numpy as np

from .env import RVM_MODEL_SHA256, ensure_rvm_model, ffmpeg, ffprobe, note, onnx_providers, run
from .media import cut, frame_at
from .imgio import imwrite
from .motion import auto_matte

SEGMENT_MARGIN_S = 0.2        # la máscara empieza antes y acaba después que el elemento: RVM necesita unos fotogramas para asentarse
SEGMENT_MERGE_GAP_S = 1.0     # con un hueco menor no compensa abrir otro vídeo: el tramo sigue de corrido
MATTE_WARN_S = 60.0           # a partir de aquí la máscara ya cuesta minutos de verdad y se avisa
MATTE_FORMAT = 1              # súbelo si cambia cómo se escribe la máscara: las de la caché dejan de valer
MATTE_FPS_GPU = 3.0           # fotogramas por segundo del proceso entero a 1080p, medidos en F28-331: 180 en 59 s con la
MATTE_FPS_CPU = 2.1           # GPU a medias con otro programa, 180 en 86 s en CPU (16 núcleos)
ALPHA_LEVELS = (64, 240)      # el alfa de RVM por debajo y por encima de esto se lleva a 0 y a 255; entre medias, recta (F28-340)


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


def _session(gpu: bool | None = None):
    """Sesión de RVM y el proveedor que de verdad usa: si CUDA no llega a cargar, onnxruntime sigue en CPU sin error."""
    import onnxruntime as ort
    sess = ort.InferenceSession(str(ensure_rvm_model()), providers=onnx_providers(gpu))
    return sess, sess.get_providers()[0]


def alpha_lut(levels: tuple[int, int] = ALPHA_LEVELS) -> np.ndarray:
    """Tabla de 256 valores del alfa refinado. El alfa bajo de RVM no es persona: es un fantasma de lo que tiene detrás (un
    llavero de la pared, una estela junto a la oreja) y el filete del color de la pared alrededor de una mano rápida, y solo se
    ve al poner algo detrás del hablante. Medido sobre fondo oscuro y claro: hasta 32 el fantasma sigue, con 64 se va sin
    perder los mechones de pelo y con 96 asoman escalones en los dedos. Dilatar, que era el plan, ensanchaba el halo."""
    low, high = levels
    return np.clip((np.arange(256, dtype=np.float32) - low) * 255.0 / (high - low), 0, 255).astype(np.uint8)


def matte_frames(video: str | Path, sink, ratio: float | None = None, gpu: bool | None = None) -> dict:
    """Pasa cada fotograma por RVM y lo entrega a `sink(bgra)` (RGB = foreground predicho, A = alfa con `alpha_lut`). `gpu`:
    None = CUDA si la hay. Las conversiones van por OpenCV (SIMD y varios hilos): con NumPy se comían ~200 ms por fotograma a
    1080p (F28-331)."""
    lut = alpha_lut()
    sess, provider = _session(gpu)
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
        x = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB).astype(np.float32).transpose(2, 0, 1)[None] / 255.0
        fgr, pha, *rec = sess.run([], {"src": x, "r1i": rec[0], "r2i": rec[1], "r3i": rec[2], "r4i": rec[3], "downsample_ratio": ds})
        r, g, b = (cv2.convertScaleAbs(fgr[0, c], alpha=255.0) for c in range(3))
        sink(cv2.merge((b, g, r, cv2.LUT(cv2.convertScaleAbs(pha[0, 0], alpha=255.0), lut))))
        n += 1
    cap.release()
    dt = time.time() - t0
    return {"frames": n, "seconds": round(dt, 1), "fps": round(n / dt, 2) if dt else None, "ratio": ratio, "provider": provider, "width": w, "height": h}


def frame_rate(video: str | Path) -> str:
    """Fotogramas por segundo del vídeo como fracción exacta de ffprobe ("30000/1001", "25/1"). Primero la media
    (avg_frame_rate: en un vídeo de móvil de frecuencia variable da la duración real con los fotogramas que hay) y, si
    no la trae, la nominal (r_frame_rate). Sin dato fiable, "30/1"."""
    r = run([ffprobe(), "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=avg_frame_rate,r_frame_rate",
             "-of", "default=noprint_wrappers=1", str(video)])
    rates = dict(line.split("=", 1) for line in (r.stdout or "").splitlines() if "=" in line)
    for key in ("avg_frame_rate", "r_frame_rate"):
        num, _, den = rates.get(key, "").partition("/")
        try:
            if float(num) > 0 and float(den or 1) > 0:
                return f"{num}/{den or 1}"
        except ValueError:
            continue
    return "30/1"


def color_tags(video: str | Path) -> list[str]:
    """Etiquetas de color del clip como opciones de ffmpeg. OpenCV lee siempre con la matriz BT.601, traiga el clip la que
    traiga, y `WebmSink` convierte de vuelta con la misma: los planos de la máscara son los del clip y solo le falta decir
    cómo se leen. Sin etiqueta, el compositor lee un VP9 con BT.601 y en un clip bt709 (casi todos) la piel saltaba 4-7 niveles
    en el fotograma en que entraba (F28-340). `gbr` no se copia: los planos de la máscara son siempre YUV."""
    r = run([ffprobe(), "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=color_space,color_primaries,color_transfer",
             "-of", "default=noprint_wrappers=1", str(video)])
    found = dict(line.split("=", 1) for line in (r.stdout or "").splitlines() if "=" in line)
    tags = (("-colorspace", "color_space"), ("-color_primaries", "color_primaries"), ("-color_trc", "color_transfer"))
    return [v for flag, key in tags if found.get(key, "unknown") not in ("unknown", "reserved", "gbr", "") for v in (flag, found[key])]


def webm_args(out_webm: str | Path, width: int, height: int, fps: int | float | str, crf: int = 20, color: list[str] | tuple = ()) -> list[str]:
    """ffmpeg que lee fotogramas YUVA crudos por la entrada estándar y escribe VP9 con alfa. Sin PNG intermedios (270-329 ms
    por fotograma, ~3 GB por 30 s) y con VP9 en tiempo real y varios hilos: su coste estaba en 2-3 min por 285 fotogramas (F28-331).
    Las etiquetas `color` van antes de `-i` porque describen esos planos. Después de `-i` ffmpeg 9 no etiqueta: convierte de
    BT.601 a la matriz pedida, y en la piel de un clip bt709 cambiaba Y -4,6 y U +2,2 con la etiqueta ya correcta (F28-340)."""
    return [ffmpeg(), "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "yuva420p", "-s", f"{width}x{height}", "-framerate", str(fps), *color, "-i", "-",
            "-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p", "-b:v", "0", "-crf", str(crf), "-auto-alt-ref", "0",
            "-deadline", "realtime", "-cpu-used", "4", "-row-mt", "1", str(out_webm)]


class WebmSink:
    """Recibe fotogramas BGRA y los manda a ffmpeg como YUVA. El primer fotograma da el tamaño; `keep_png` guarda además la
    secuencia. La conversión es de OpenCV y no de ffmpeg: con BGRA de entrada y `-colorspace` de salida, según la versión de
    ffmpeg cambiaba la matriz con la que convertía. Se usa con `with`: al salir cierra la tubería y un fallo de ffmpeg se
    convierte en un error con su mensaje."""

    def __init__(self, out_webm: str | Path, fps: int | float | str, keep_png: str | Path | None = None, crf: int = 20, color: list[str] | tuple = ()):
        self.out, self.fps, self.crf, self.color = out_webm, fps, crf, color
        self.png = Path(keep_png) if keep_png else None
        self.proc: subprocess.Popen | None = None
        self.err = tempfile.TemporaryFile()     # un fichero y no una tubería: si nadie la lee, ffmpeg se quedaría esperando
        self.n = 0

    def __enter__(self) -> "WebmSink":
        if self.png:
            self.png.mkdir(parents=True, exist_ok=True)
        return self

    def __call__(self, bgra: np.ndarray) -> None:
        h, w = bgra.shape[0] & ~1, bgra.shape[1] & ~1     # 4:2:0 no admite lados impares
        bgra = bgra[:h, :w]
        if self.proc is None:
            self.proc = subprocess.Popen(webm_args(self.out, w, h, self.fps, self.crf, self.color), stdin=subprocess.PIPE, stderr=self.err)
        if self.png:
            imwrite(str(self.png / f"f_{self.n:04d}.png"), bgra)
        self.n += 1
        try:
            self.proc.stdin.write(cv2.cvtColor(bgra, cv2.COLOR_BGRA2YUV_I420).tobytes())
            self.proc.stdin.write(bgra[:, :, 3].tobytes())
        except OSError as e:                    # ffmpeg murió a mitad: el mensaje útil es el suyo y sale al cerrar
            self.proc.wait()
            raise SystemExit(self._fail()) from e

    def _fail(self) -> str:
        self.err.seek(0)
        return "ffmpeg no pudo escribir la máscara: " + (self.err.read().decode("utf-8", "replace").strip()[-800:] or f"código {self.proc.returncode}")

    def __exit__(self, exc_type, exc, tb) -> None:
        if self.proc is not None:
            try:
                self.proc.stdin.close()
            except OSError:
                pass
            if self.proc.wait() != 0 and exc_type is None:
                raise SystemExit(self._fail())
        elif exc_type is None:
            raise SystemExit("el vídeo no dio ningún fotograma: no hay máscara que escribir")
        self.err.close()


def matte(video: str | Path, out_webm: str | Path, start: float | None = None, end: float | None = None,
          ratio: float | None = None, fps: int | float | str | None = None, keep_png: str | Path | None = None,
          gpu: bool | None = None) -> dict:
    """Máscara alfa como WebM VP9 con alfa. Con start/end recorta primero (solo el tramo que necesita algo detrás).
    Sale a los fps del tramo de origen (`fps` los fuerza): con 30 fijos, un original a 25 o 60 sin pasar por prep daba un
    alfa a otra velocidad, desincronizado de lo que hay detrás (F28-92). La carpeta temporal se borra también si algo
    falla a medias."""
    tmp = Path(tempfile.mkdtemp(prefix="frame28_matte_"))
    try:
        src = Path(video)
        if start is not None and end is not None:
            src = cut(video, start, end, tmp / "seg.mp4")
        rate = fps or frame_rate(src)
        with WebmSink(out_webm, rate, keep_png, color=color_tags(video)) as sink:
            stats = matte_frames(src, sink, ratio, gpu)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    stats.update({"webm": str(out_webm), "start": start, "end": end, "frame_rate": str(rate)})
    return stats


# ---------- tramos de máscara de un storyboard ----------
def segment_step(fps: int) -> float:
    """Rejilla de los tramos: el múltiplo de fotograma más corto que se escribe exacto con tres decimales (0,1 s a 30 fps;
    0,04 s a 25). Con 2,467 en vez de 74/30, `data-start` cae entre dos fotogramas y la máscara va uno por detrás del fondo."""
    return math.ceil(fps / math.gcd(fps, 1000)) / fps


def matte_segments(sb: dict) -> list[dict]:
    """Une las ventanas de lo que va detrás en tramos de máscara: margen de SEGMENT_MARGIN_S por lado, fusión de huecos
    menores que SEGMENT_MERGE_GAP_S, recortados al clip (en una tarjeta de cierre no hay hablante que recortar)."""
    step = segment_step(int((sb.get("canvas") or {}).get("fps", 30)))
    clip = float(sb["source"]["duration"])
    wins = sorted((float(o["start"]), float(o["end"]), o["id"]) for o in sb.get("overlays", []) if auto_matte(o))
    segs: list[dict] = []
    for s0, e0, oid in wins:
        if s0 >= clip:
            continue
        a = math.floor(max(0.0, s0 - SEGMENT_MARGIN_S) / step + 1e-6) * step
        b = min(clip, math.ceil((e0 + SEGMENT_MARGIN_S) / step - 1e-6) * step)
        if segs and a - segs[-1]["end"] < SEGMENT_MERGE_GAP_S:
            segs[-1]["end"] = max(segs[-1]["end"], b); segs[-1]["ids"].append(oid)
        else:
            segs.append({"start": a, "end": b, "ids": [oid]})
    return [{**x, "start": round(x["start"], 3), "end": round(x["end"], 3)} for x in segs]


def file_digest(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(1 << 20):
            h.update(chunk)
    return h.hexdigest()


def segment_key(clip_digest: str, start: float, end: float, ratio: float | None = None) -> str:
    """Identifica una máscara: el contenido del clip (no su nombre ni su fecha), el tramo, el modelo, el ratio y cómo se escribe."""
    data = json.dumps({"clip": clip_digest, "start": start, "end": end, "model": RVM_MODEL_SHA256, "ratio": ratio, "format": MATTE_FORMAT}, sort_keys=True)
    return hashlib.sha256(data.encode()).hexdigest()[:20]


def matte_speed() -> tuple[str, float]:
    """Dónde va a correr RVM y a cuántos fotogramas por segundo va el proceso entero a 1080p (medido en F28-340)."""
    try:
        gpu = onnx_providers()[0].startswith("CUDA")
    except (ImportError, SystemExit):
        gpu = False
    return ("gpu", MATTE_FPS_GPU) if gpu else ("cpu", MATTE_FPS_CPU)


def segment_plan(sb: dict, base_dir: str | Path) -> dict:
    """Qué máscaras pide un storyboard, cuáles ya están en la caché y cuánto costarán las que faltan. No calcula nada."""
    base = Path(base_dir); video = base / sb["source"]["video"]
    fps = int((sb.get("canvas") or {}).get("fps", 30)); ratio = sb.get("matte_ratio")
    digest = file_digest(video) if video.exists() else None
    segs = []
    for x in matte_segments(sb):
        key = segment_key(digest, x["start"], x["end"], ratio) if digest else None
        path = base / ".frame28" / "matte" / f"{key}.webm" if key else None
        segs.append({**x, "seconds": round(x["end"] - x["start"], 3), "frames": round((x["end"] - x["start"]) * fps),
                     "key": key, "file": str(path) if path else None, "cached": bool(path and path.exists())})
    total = round(sum(x["seconds"] for x in segs), 3)
    pending = [x for x in segs if not x["cached"]]
    device, speed = matte_speed()
    minutes = lambda v: round(sum(x["frames"] for x in pending) / v / 60, 1)  # noqa: E731
    plan = {"segments": segs, "total_seconds": total, "pending_seconds": round(sum(x["seconds"] for x in pending), 3), "device": device,
            "estimated_minutes": minutes(speed), "estimated_minutes_gpu": minutes(MATTE_FPS_GPU), "estimated_minutes_cpu": minutes(MATTE_FPS_CPU),
            "warnings": []}
    if not video.exists():
        plan["warnings"].append(f"no existe el clip {video}: sin él no hay máscara y lo que va detrás quedará delante del hablante")
    if total > MATTE_WARN_S:
        plan["warnings"].append(
            f"{total} s de máscara: {plan['estimated_minutes_gpu']} min en GPU, {plan['estimated_minutes_cpu']} min en CPU "
            f"(por calcular, en {device}: {plan['estimated_minutes']} min). Acorta lo que va detrás si no compensa")
    return plan


def ensure_segments(sb: dict, base_dir: str | Path, gpu: bool | None = None) -> dict:
    """Calcula las máscaras que falten y deja cada una en la caché de la carpeta del storyboard. Se escriben con otro
    nombre y se renombran al terminar: un build interrumpido no deja en la caché una máscara a medias."""
    plan = segment_plan(sb, base_dir)
    pending = [x for x in plan["segments"] if not x["cached"] and x["key"]]
    if pending:
        note(f"Máscara del hablante: {len(pending)} tramo(s), {plan['pending_seconds']} s, unos {plan['estimated_minutes']} min en {plan['device']}…")
    video = Path(base_dir) / sb["source"]["video"]
    half = 0.5 / int((sb.get("canvas") or {}).get("fps", 30))   # -ss se queda con el primer fotograma >= el corte: medio fotograma antes es ese
    for x in pending:
        dst = Path(x["file"]); dst.parent.mkdir(parents=True, exist_ok=True)
        tmp = dst.with_name(dst.stem + ".parcial.webm")
        try:
            stats = matte(video, tmp, max(0.0, x["start"] - half), x["end"] - half, ratio=sb.get("matte_ratio"), gpu=gpu)
            os.replace(tmp, dst)
        finally:
            tmp.unlink(missing_ok=True)
        x.update({"cached": True, "computed_seconds": stats.get("seconds"), "provider": stats.get("provider")})
    return plan


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
