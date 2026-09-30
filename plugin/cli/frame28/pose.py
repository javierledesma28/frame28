"""Detección de gestos de señalar con MediaPipe Pose: cuándo, con qué mano y hacia dónde apunta el hablante.

Salida pensada para el storyboard: eventos de "señalar" con la punta del dedo en coordenadas 1080p, la palabra
que se está diciendo en ese instante y una propuesta de `pointer` (dot + box) que no tapa la cara ni la mano.
"""
from __future__ import annotations

import json
import math
import urllib.request
from pathlib import Path

import cv2
import numpy as np

from .env import CACHE_DIR

POSE_MODEL_URL = "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task"
POSE_MODEL_PATH = CACHE_DIR / "pose_landmarker_lite.task"

# índices de landmarks de MediaPipe Pose
NOSE, L_SHOULDER, R_SHOULDER, L_ELBOW, R_ELBOW, L_WRIST, R_WRIST, L_INDEX, R_INDEX = 0, 11, 12, 13, 14, 15, 16, 19, 20
POINT_WORDS = {"aquí", "acá", "ahí", "allí", "allá", "esto", "esta", "este", "eso", "esa", "ese", "aquel", "aquella",
               "here", "there", "this", "that", "these", "those"}


def ensure_pose_model() -> Path:
    if not POSE_MODEL_PATH.exists():
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        print(f"Descargando modelo de pose (5 MB) a {POSE_MODEL_PATH} ...")
        urllib.request.urlretrieve(POSE_MODEL_URL, POSE_MODEL_PATH)
    return POSE_MODEL_PATH


def _landmarker():
    import mediapipe as mp
    from mediapipe.tasks import python as mp_python
    from mediapipe.tasks.python import vision
    opts = vision.PoseLandmarkerOptions(
        base_options=mp_python.BaseOptions(model_asset_path=str(ensure_pose_model())),
        running_mode=vision.RunningMode.VIDEO, num_poses=1,
        min_pose_detection_confidence=0.5, min_tracking_confidence=0.5)
    return vision.PoseLandmarker.create_from_options(opts), mp


def track(video: str | Path, sample_fps: float = 10.0) -> dict:
    """Landmarks clave por fotograma muestreado, en píxeles del vídeo original."""
    lm, mp = _landmarker()
    cap = cv2.VideoCapture(str(video))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    w, h = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    step = max(1, int(round(fps / sample_fps)))
    frames = []
    n = 0
    while True:
        ok, bgr = cap.read()
        if not ok:
            break
        if n % step == 0:
            rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
            img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            res = lm.detect_for_video(img, int(n / fps * 1000))
            t = round(n / fps, 3)
            if res.pose_landmarks:
                pts = res.pose_landmarks[0]
                def P(k):
                    return [round(pts[k].x * w, 1), round(pts[k].y * h, 1), round(pts[k].visibility, 2)]
                frames.append({"t": t, "nose": P(NOSE), "l_sh": P(L_SHOULDER), "r_sh": P(R_SHOULDER),
                               "l_el": P(L_ELBOW), "r_el": P(R_ELBOW), "l_wr": P(L_WRIST), "r_wr": P(R_WRIST),
                               "l_ix": P(L_INDEX), "r_ix": P(R_INDEX)})
            else:
                frames.append({"t": t})
        n += 1
    lm.close()
    return {"video": str(video), "width": w, "height": h, "fps": fps, "sample_fps": fps / step, "frames": frames}


def _hand_out(f: dict, ix: str, sh_key: str, other_sh: str, w: int, h: int) -> bool:
    """La mano está "fuera": dedo visible, dentro del encuadre, a un lado del torso y no colgando por debajo."""
    if ix not in f or f[ix][2] < 0.3 or f[sh_key][2] < 0.5:
        return False
    tip = f[ix]; sh = f[sh_key]; osh = f[other_sh]
    if not (0 <= tip[0] <= w and 0 <= tip[1] <= h * 0.97):
        return False
    shoulder_w = max(1.0, abs(sh[0] - osh[0]))
    torso_l = min(sh[0], osh[0]) - 0.08 * shoulder_w
    torso_r = max(sh[0], osh[0]) + 0.08 * shoulder_w
    outside = tip[0] < torso_l or tip[0] > torso_r
    not_hanging = tip[1] < max(sh[1], osh[1]) + 0.55 * shoulder_w
    return outside and not_hanging


def detect_pointing(tr: dict, min_hold: float = 0.25, canvas: tuple[int, int] | None = None) -> list[dict]:
    """Gesto = una mano fuera del torso, visible y dentro del encuadre, mantenida >= `min_hold` s.
    Si las dos manos están fuera a la vez es énfasis (`kind: both_hands`), no señalar. Punta en coordenadas del lienzo."""
    from .captions import default_canvas
    w, h = tr["width"], tr["height"]
    cw, ch = canvas or default_canvas(w, h)
    sx, sy = cw / w, ch / h
    hands = (("left", "l_ix", "l_sh", "r_sh"), ("right", "r_ix", "r_sh", "l_sh"))
    events = []
    for hand, ix, sh_key, other_sh in hands:
        other_ix = "r_ix" if hand == "left" else "l_ix"
        run: list[dict] = []

        def flush():
            if run and (run[-1]["t"] - run[0]["t"]) >= min_hold:
                cx = float(np.median([f["tip"][0] for f in run])); cy = float(np.median([f["tip"][1] for f in run]))
                nose_x = float(np.median([f["nose"][0] for f in run]))
                both = sum(1 for f in run if f["both"]) > len(run) / 2
                events.append({"kind": "both_hands" if both else "point", "hand": hand,
                               "start": run[0]["t"], "end": run[-1]["t"],
                               "tip": [round(cx * sx), round(cy * sy)], "tip_1080p": [round(cx * sx), round(cy * sy)],
                               "direction": "right" if cx > nose_x + 0.05 * w else "left" if cx < nose_x - 0.05 * w else "center",
                               "frames": len(run)})
            run.clear()

        for f in tr["frames"]:
            if "nose" in f and _hand_out(f, ix, sh_key, other_sh, w, h):
                run.append({"t": f["t"], "tip": f[ix], "nose": f["nose"],
                            "both": _hand_out(f, other_ix, other_sh, sh_key, w, h)})
            else:
                flush()
        flush()
    # fusionar eventos both_hands duplicados (uno por mano) en uno solo
    merged: list[dict] = []
    for e in sorted(events, key=lambda e: e["start"]):
        if e["kind"] == "both_hands" and merged and merged[-1]["kind"] == "both_hands" and e["start"] <= merged[-1]["end"] + 0.15:
            merged[-1]["end"] = max(merged[-1]["end"], e["end"]); merged[-1]["hand"] = "both"
            continue
        merged.append(e)
    return merged


def face_box(tr: dict, canvas: tuple[int, int] | None = None) -> list[int] | None:
    """Caja aproximada de la cara (nariz ± ancho de hombros × 0.45) en coordenadas del lienzo, mediana de todo el clip."""
    from .captions import default_canvas
    fr = [f for f in tr["frames"] if "nose" in f]
    if not fr:
        return None
    w, h = tr["width"], tr["height"]
    cw, ch = canvas or default_canvas(w, h)
    sx, sy = cw / w, ch / h
    nx = float(np.median([f["nose"][0] for f in fr])); ny = float(np.median([f["nose"][1] for f in fr]))
    sw = float(np.median([abs(f["l_sh"][0] - f["r_sh"][0]) for f in fr]))
    half = 0.45 * sw
    return [round((nx - half) * sx), round((ny - 1.3 * half) * sy), round((nx + half) * sx), round((ny + 0.9 * half) * sy)]


face_box_1080p = face_box  # alias antiguo


def suggest_pointers(events: list[dict], words: list[dict] | None, face: list[int] | None, canvas: tuple[int, int] = (1920, 1080)) -> list[dict]:
    """Para cada gesto: palabra que se dice en ese momento (prioridad a deícticos como 'aquí'), texto sugerido
    y una posición de caja en la dirección del gesto, alejada de la mano y fuera de la cara."""
    out = []
    both = [e for e in events if e["kind"] == "both_hands"]
    candidates = [e for e in events if e["kind"] == "point"
                  and not any(e["start"] <= b["end"] and e["end"] >= b["start"] for b in both)]
    for k, e in enumerate(candidates):
        at = e["start"]; text = ""; confidence = "low"
        if words:
            win = [w for w in words if w["start"] <= e["end"] + 0.3 and w["end"] >= e["start"] - 0.4]
            deictic = [w for w in win if w["text"].strip(".,;:!?¿¡").lower() in POINT_WORDS]
            anchor = deictic[0] if deictic else (win[0] if win else None)
            confidence = "high" if deictic else "low"
            if anchor:
                at = anchor["start"]
                # texto: las 2-3 palabras de contenido que siguen al deíctico (p. ej. "hay una cosa")
                after = [w for w in words if w["start"] >= anchor["start"]][1:5]
                content = [w["text"].strip(".,;:!?¿¡") for w in after if w["text"].strip(".,;:!?¿¡").lower() not in POINT_WORDS]
                text = " ".join(content[:3])
        tx, ty = e["tip"]
        cw, ch = canvas
        dx = 90 if e["direction"] == "right" else -90 if e["direction"] == "left" else 0
        bx = tx + dx + (0 if dx >= 0 else -320); by = ty - 210
        bx = max(60, min(bx, cw - 420)); by = max(80, min(by, ch - 200))
        if face and face[0] - 40 < bx < face[2] + 40 and face[1] - 40 < by < face[3] + 40:
            by = face[3] + 60 if by < face[3] else face[1] - 140
        out.append({"id": f"p{k + 1}", "type": "pointer", "start": round(max(0, at - 0.05), 2), "end": round(e["end"] + 0.6, 2),
                    "at": round(at, 2), "dot": [tx, ty], "box": [round(bx), round(by)], "text": text or "aquí",
                    "hand": e["hand"], "direction": e["direction"], "confidence": confidence})
    return out


def analyze(video: str | Path, words_path: str | Path | None = None, sample_fps: float = 10.0, annotate: str | Path | None = None,
            canvas: tuple[int, int] | None = None) -> dict:
    from .captions import default_canvas, load_words
    tr = track(video, sample_fps)
    canvas = canvas or default_canvas(tr["width"], tr["height"])
    events = detect_pointing(tr, canvas=canvas)
    words = load_words(words_path) if words_path else None
    face = face_box(tr, canvas)
    sugg = suggest_pointers(events, words, face, canvas)
    result = {"video": str(video), "frames_analyzed": len(tr["frames"]), "sample_fps": tr["sample_fps"], "canvas": list(canvas),
              "face_box": face, "face_box_1080p": face, "events": events, "pointer_suggestions": sugg}
    if annotate:
        _annotate(video, tr, events, sugg, annotate, canvas)
        result["annotated"] = str(annotate)
    return result


def _annotate(video, tr, events, sugg, out_png, canvas=(1920, 1080)):
    """Hoja con un fotograma por gesto: punta del dedo (círculo) y caja propuesta (rectángulo)."""
    cap = cv2.VideoCapture(str(video)); fps = tr["fps"]
    cw, ch = canvas
    tiles = []
    for s in sugg:
        t = (s["at"] + s["end"] - 0.6) / 2
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(t * fps)); ok, fr = cap.read()
        if not ok:
            continue
        fr = cv2.resize(fr, (cw, ch))
        color = (0, 197, 245) if s["confidence"] == "high" else (140, 140, 140)
        cv2.circle(fr, tuple(s["dot"]), 18, color, 4)
        bx, by = s["box"]; cv2.rectangle(fr, (bx, by), (bx + 300, by + 80), color, 3)
        cv2.putText(fr, f"{s['id']} {s['hand']} -> {s['direction']}  at={s['at']:.2f}s  '{s['text']}'  [{s['confidence']}]",
                    (40, 60), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 3)
        tiles.append(cv2.resize(fr, (cw // 2, ch // 2)))
    if tiles:
        rows = [np.hstack(tiles[i:i + 2]) if i + 1 < len(tiles) else np.hstack([tiles[i], np.zeros_like(tiles[i])]) for i in range(0, len(tiles), 2)]
        cv2.imwrite(str(out_png), np.vstack(rows))
