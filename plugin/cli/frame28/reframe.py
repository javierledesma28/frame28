"""Reencuadre automático a vertical (9:16) o cuadrado desde un clip apaisado.

Modo `crop` (por defecto): la mayor ventana con la proporción de salida recorre el clip siguiendo al hablante (nariz y
hombros de MediaPipe Pose, el mismo tracker de `gestures`) con comportamiento de operador de cámara: zona muerta (no se
mueve mientras el sujeto esté cerca del centro), suavizado exponencial, velocidad máxima y media móvil final. Nada de
temblores por fotograma. Si el origen es más ancho que la salida (apaisado → 9:16), la ventana ocupa toda la altura y se
mueve en horizontal; si es más alto (un vertical de móvil → 1:1 o 4:5), ocupa todo el ancho y se mueve en vertical con
la cara en el tercio superior (antes la ventana salía más ancha que el vídeo y la imagen se aplastaba, F28-89). El camino
se guarda en `reframe.json` (`crop`, `axis`, `path`) para mapear coordenadas del clip original.
Modo `blur`: el 16:9 entero centrado sobre su propio fondo desenfocado; no pierde gestos ni bordes, deja franjas
arriba y abajo para overlays y subtítulos.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import cv2
import numpy as np

from .env import encoder_args, ffmpeg, run


def subject_path(video: str | Path, sample_fps: float = 10.0) -> dict:
    """Centro horizontal del sujeto por muestra (px del original): 0,6·nariz + 0,4·centro de hombros."""
    from .pose import track
    tr = track(video, sample_fps)
    xs, ys, ts = [], [], []
    last = None
    for f in tr["frames"]:
        if "nose" in f:
            sh = (f["l_sh"][0] + f["r_sh"][0]) / 2
            last = (0.6 * f["nose"][0] + 0.4 * sh, f["nose"][1])
        if last is not None:
            ts.append(f["t"]); xs.append(last[0]); ys.append(last[1])
    if not xs:  # sin detección: centro fijo (la cara, a un tercio de la altura)
        ts, xs, ys = [0.0], [tr["width"] / 2], [tr["height"] / 3]
    return {"width": tr["width"], "height": tr["height"], "fps": tr["fps"], "sample_fps": tr["sample_fps"],
            "t": ts, "x": xs, "y": ys, "detected": sum(1 for f in tr["frames"] if "nose" in f), "samples": len(tr["frames"])}


FACE_AT = 0.4   # en la ventana vertical, la nariz queda al 40 % de la altura (cabeza en el tercio superior)


def crop_window(W: int, H: int, ow: int, oh: int) -> tuple[str, int, int]:
    """(eje, ancho, alto) de la mayor ventana con la proporción ow:oh que cabe en W×H. Eje «x» si el origen es más
    ancho que la salida (la ventana ocupa toda la altura y se mueve en horizontal), «y» si es más alto."""
    if W * oh >= H * ow:
        cw = min(W, int(round(H * ow / oh)))
        return "x", cw - cw % 2, H
    ch = min(H, int(round(W * oh / ow)))
    return "y", W, ch - ch % 2


def window_origin(axis: str, center: float, W: int, H: int, cw: int, ch: int) -> tuple[int, int]:
    """Esquina superior izquierda de la ventana centrada en `center` sobre su eje, sin salirse del clip."""
    if axis == "y":
        return 0, int(round(max(0, min(H - ch, center - ch / 2))))
    return int(round(max(0, min(W - cw, center - cw / 2)))), 0


def camera_path(subj: dict, crop_w: int, deadzone: float = 0.10, smooth: float = 0.8, max_speed: float = 0.5,
                settle: float = 0.4, axis: str = "x") -> list[list[float]]:
    """Centro de la ventana por muestra sobre su eje. `crop_w` es el tamaño de la ventana en ese eje; `deadzone` y
    `max_speed` en fracción de ese tamaño (por segundo); `smooth` es la constante de tiempo (s) del suavizado; `settle`
    la ventana (s) de la media móvil final. En el eje «y» la ventana busca dejar la nariz al 40 % de su altura."""
    ts = subj["t"]
    if axis == "y":
        W = subj["height"]
        xs = [y + (0.5 - FACE_AT) * crop_w for y in (subj.get("y") or [subj["height"] / 3] * len(ts))]
    else:
        W = subj["width"]; xs = subj["x"]
    half = crop_w / 2
    lo, hi = half, W - half
    dead = deadzone * crop_w
    cam = float(np.clip(xs[0], lo, hi))
    out = []
    for i, (t, x) in enumerate(zip(ts, xs)):
        dt = (t - ts[i - 1]) if i else 0.1
        target = cam
        if x - cam > dead:
            target = x - dead
        elif cam - x > dead:
            target = x + dead
        target = float(np.clip(target, lo, hi))
        alpha = 1 - np.exp(-dt / max(smooth, 1e-3))
        step = (target - cam) * alpha
        vmax = max_speed * crop_w * dt
        step = float(np.clip(step, -vmax, vmax))
        cam += step
        out.append([t, cam])
    # media móvil final para limar el arranque de cada movimiento
    n = max(1, int(round(settle * subj["sample_fps"])))
    arr = np.array([c for _, c in out])
    if len(arr) > n:
        kern = np.ones(n) / n
        pad = np.pad(arr, (n // 2, n - 1 - n // 2), mode="edge")
        arr = np.convolve(pad, kern, mode="valid")
    return [[round(t, 3), round(float(c), 1)] for (t, _), c in zip(out, arr)]


def _interp(path: list[list[float]], t: float) -> float:
    ts = [p[0] for p in path]; cs = [p[1] for p in path]
    return float(np.interp(t, ts, cs))


def reframe(video: str | Path, out_mp4: str | Path, mode: str = "crop", out_size: tuple[int, int] = (1080, 1920),
            deadzone: float = 0.10, smooth: float = 0.8, max_speed: float = 0.5, path_json: str | Path | None = None,
            crf: int = 18) -> dict:
    video = Path(video); out = Path(out_mp4); out.parent.mkdir(parents=True, exist_ok=True)
    ow, oh = out_size
    cap = cv2.VideoCapture(str(video))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    W, H = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    res = {"video": str(video), "output": str(out), "mode": mode, "source": [W, H], "out": [ow, oh], "fps": fps}
    if mode == "blur":
        cap.release()
        # fondo: el mismo clip escalado a cubrir y desenfocado; delante: el clip entero a lo ancho
        vf = (f"split[bg][fg];[bg]scale={ow}:{oh}:force_original_aspect_ratio=increase,crop={ow}:{oh},"
              f"gblur=sigma=40,eq=brightness=-0.08[bgb];[fg]scale={ow}:-2[fgs];[bgb][fgs]overlay=(W-w)/2:(H-h)/2")
        r = run([ffmpeg(), "-y", "-loglevel", "error", "-i", str(video), "-filter_complex", vf, "-an", *encoder_args(crf), "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(out)])
        if r.returncode != 0:
            raise SystemExit(r.stderr[-800:])
        fg_h = round(ow * H / W / 2) * 2
        res.update({"foreground": {"x": 0, "y": (oh - fg_h) // 2, "w": ow, "h": fg_h},
                    "free_bands": [[0, (oh - fg_h) // 2], [(oh + fg_h) // 2, oh]]})
        if path_json:
            Path(path_json).write_text(json.dumps(res, indent=1), encoding="utf-8")
        return res
    # ---- crop: la mayor ventana con la proporción de salida, que se mueve en el eje que sobra ----
    axis, crop_w, crop_h = crop_window(W, H, ow, oh)
    subj = subject_path(video)
    path = camera_path(subj, crop_w if axis == "x" else crop_h, deadzone, smooth, max_speed, axis=axis)
    cmd = [ffmpeg(), "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{ow}x{oh}", "-r", f"{fps:.6f}",
           "-i", "-", "-an", *encoder_args(crf), "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(out)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    i = 0
    try:
        while True:
            ok, fr = cap.read()
            if not ok:
                break
            t = i / fps
            x0, y0 = window_origin(axis, _interp(path, t), W, H, crop_w, crop_h)
            crop = fr[y0:y0 + crop_h, x0:x0 + crop_w]
            up = cv2.resize(crop, (ow, oh), interpolation=cv2.INTER_CUBIC if ow > crop_w else cv2.INTER_AREA)
            proc.stdin.write(up.tobytes())
            i += 1
    finally:
        cap.release()
        proc.stdin.close()
        err = proc.stderr.read().decode("utf-8", "replace"); proc.wait()
    if proc.returncode != 0 or not out.exists():
        raise SystemExit("ffmpeg falló: " + err[-800:])
    moves = sum(1 for a, b in zip(path, path[1:]) if abs(b[1] - a[1]) > 0.5)
    res.update({"crop": [crop_w, crop_h], "axis": axis, "scale": round(ow / crop_w, 3), "frames": i, "detected_samples": subj["detected"],
                "samples": subj["samples"], "path": path, "moving_samples": moves,
                "params": {"deadzone": deadzone, "smooth": smooth, "max_speed": max_speed}})
    if path_json:
        Path(path_json).write_text(json.dumps(res, indent=1), encoding="utf-8")
    return res


def map_point(res: dict, x: float, y: float, t: float) -> list[int]:
    """Punto del clip original (px) → píxeles del clip reencuadrado en el instante t (modo crop o blur).
    En modo crop el punto puede quedar fuera de la ventana: `point_visible` lo dice."""
    if res.get("mode") == "blur":
        fg = res["foreground"]; W, H = res["source"]
        return [round(fg["x"] + x * fg["w"] / W), round(fg["y"] + y * fg["h"] / H)]
    crop_w, crop_h = res["crop"]; ow, oh = res["out"]; W, H = res["source"]
    axis = res.get("axis", "x")   # los reframe.json anteriores a F28-89 siempre recortaban en horizontal
    c = _interp(res["path"], t)
    if axis == "y":
        x0, y0 = 0.0, max(0.0, min(H - crop_h, c - crop_h / 2))
    else:
        x0, y0 = max(0.0, min(W - crop_w, c - crop_w / 2)), 0.0
    return [round((x - x0) * ow / crop_w), round((y - y0) * oh / crop_h)]


def point_visible(res: dict, x: float, y: float, t: float) -> bool:
    """¿El punto del original (px) queda dentro del encuadre vertical en el instante t? (blur: siempre)."""
    if res.get("mode") == "blur":
        return True
    px, py = map_point(res, x, y, t)
    ow, oh = res["out"]
    return 0 <= px <= ow and 0 <= py <= oh


def map_canvas_point(res: dict, x: float, y: float, t: float, canvas: tuple[int, int]) -> list[int]:
    """Punto en el lienzo apaisado del storyboard (p. ej. 1920×1080, donde `gestures` y `speaker` dan sus coordenadas)
    → píxeles del lienzo vertical. Convierte primero al tamaño real del clip original."""
    W, H = res["source"]; cw, ch = canvas
    return map_point(res, x * W / cw, y * H / ch, t)


def map_gestures(res: dict, gestures: dict, box_w: int = 320, box_h: int = 90, margin: int = 40) -> dict:
    """`gestures.json` del clip apaisado → mismos gestos y `pointer` propuestos en el lienzo vertical del reencuadre,
    sin repetir la detección. Cada pointer lleva `visible` (el punto señalado cae dentro del encuadre en modo crop) y
    la caja se recoloca dentro del lienzo. Los que no se ven se devuelven igualmente para que el agente decida."""
    canvas = tuple(gestures.get("canvas") or (1920, 1080))
    W, H = res["source"]; ow, oh = res["out"]
    events = []
    for e in gestures.get("events", []):
        ne = dict(e)
        if "tip" in e:
            ne["tip"] = map_canvas_point(res, e["tip"][0], e["tip"][1], e.get("start", 0.0), canvas)
        events.append(ne)
    pointers = []
    hidden = 0
    for p in gestures.get("pointer_suggestions", []):
        t = p.get("at", p.get("start", 0.0))
        dot = map_canvas_point(res, p["dot"][0], p["dot"][1], t, canvas)
        vis = point_visible(res, p["dot"][0] * W / canvas[0], p["dot"][1] * H / canvas[1], t)
        bx, by = map_canvas_point(res, p["box"][0], p["box"][1], t, canvas)
        # la caja dentro del lienzo y sin pisar el punto: por encima del dedo si cabe, si no debajo
        bx = max(margin, min(bx, ow - box_w - margin))
        if by + box_h > dot[1] - 20 and by < dot[1] + 20:
            by = dot[1] - box_h - 60
        by = max(margin, min(by, oh - box_h - margin))
        np_ = {**p, "dot": [int(max(0, min(dot[0], ow))), int(max(0, min(dot[1], oh)))], "box": [int(bx), int(by)], "visible": vis}
        if not vis:
            hidden += 1
        pointers.append(np_)
    face = gestures.get("face_box")
    if face:
        t0 = 0.0
        a = map_canvas_point(res, face[0], face[1], t0, canvas); b = map_canvas_point(res, face[2], face[3], t0, canvas)
        face = [max(0, a[0]), max(0, a[1]), min(ow, b[0]), min(oh, b[1])]
    return {"mode": res.get("mode"), "canvas": [ow, oh], "source_canvas": list(canvas), "face_box": face,
            "events": events, "pointer_suggestions": pointers, "hidden": hidden,
            "warnings": ([f"{hidden} pointer(s) señalan fuera del encuadre vertical (modo crop): usa --mode blur o quítalos"] if hidden else [])}
