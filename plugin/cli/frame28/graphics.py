"""Gráficos ya presentes en un vídeo producido: texto en pantalla (rótulos, marca de agua, subtítulos quemados,
texto impreso en objetos), tarjetas a pantalla completa y, a partir de eso, las zonas libres para nuestros overlays.

Detector de texto: RapidOCR (PaddleOCR en ONNX, Apache-2.0) sobre onnxruntime en CPU, ~1 s por fotograma 1080p.
Muestreamos el vídeo a `sample_fps` (1 por defecto), agrupamos las cajas en eventos (misma zona y texto parecido en
muestras consecutivas) y clasificamos:
  watermark   presente en más del 60 % del vídeo, siempre en el mismo sitio
  text        texto estable ≥ 1 s, recto y sin moverse: rótulos del editor o texto impreso en objetos quietos
              (el OCR no distingue un rótulo de la caja del producto sobre la mesa; para colocar overlays da igual)
  subtitle    franja inferior, centrado, cambia cada pocos segundos (subtítulos quemados)
  scene_text  texto que se mueve, está girado o dura poco: impreso en objetos que las manos mueven
  card        fotograma casi plano de un solo color (tarjeta final, transición)
Para colocar overlays da igual la clase: **todo texto en pantalla es una zona a respetar**; la clase sirve para
decidir si añadimos subtítulos (no, si ya los hay) o si tapamos con una pizarra (no, sobre su tarjeta final).
"""
from __future__ import annotations

import json
import logging
import math
from difflib import SequenceMatcher
from pathlib import Path

import cv2
import numpy as np

ZONES = ["top-left", "top-center", "top-right", "mid-left", "center", "mid-right", "bottom-left", "bottom-center", "bottom-right"]


def _ocr_engine():
    logging.getLogger("RapidOCR").setLevel(logging.ERROR)
    try:
        from rapidocr import RapidOCR
    except ImportError as e:  # pragma: no cover
        raise SystemExit("Falta rapidocr (pip/uv: rapidocr). Reinstala el CLI: uv tool install --editable ./plugin/cli --python 3.12 --reinstall") from e
    return RapidOCR()


def _iou(a, b) -> float:
    x0, y0 = max(a[0], b[0]), max(a[1], b[1]); x1, y1 = min(a[2], b[2]), min(a[3], b[3])
    inter = max(0, x1 - x0) * max(0, y1 - y0)
    if inter == 0:
        return 0.0
    ua = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / ua if ua else 0.0


def _sim(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def _card_like(frame: np.ndarray) -> tuple[bool, str]:
    """Fotograma casi plano: > 55 % de píxeles a ±14 del color dominante y pocos bordes."""
    small = cv2.resize(frame, (192, 108))
    q = (small // 16).reshape(-1, 3)
    vals, counts = np.unique(q, axis=0, return_counts=True)
    dom = vals[counts.argmax()] * 16 + 8
    close = (np.abs(small.astype(int) - dom).sum(axis=2) < 42).mean()
    edges = cv2.Canny(cv2.cvtColor(small, cv2.COLOR_BGR2GRAY), 80, 160).mean() / 255
    return bool(close > 0.55 and edges < 0.08), "#%02x%02x%02x" % (int(dom[2]), int(dom[1]), int(dom[0]))


def scan(video: str | Path, sample_fps: float = 1.0, canvas: tuple[int, int] | None = None, max_side: int = 1280,
         min_score: float = 0.6) -> dict:
    from .captions import default_canvas

    cap = cv2.VideoCapture(str(video))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)); dur = n / fps
    w, h = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cw, ch = canvas or default_canvas(w, h)
    sx, sy = cw / w, ch / h
    step = 1.0 / sample_fps
    eng = _ocr_engine()
    open_events: list[dict] = []; events: list[dict] = []; cards: list[dict] = []
    card_open: dict | None = None
    samples = 0
    t = 0.0
    while t < dur:
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
        ok, fr = cap.read()
        if not ok:
            break
        samples += 1
        is_card, color = _card_like(fr)
        if is_card:
            if card_open and card_open["color"] == color and t - card_open["end"] <= step * 1.5:
                card_open["end"] = t
            else:
                card_open = {"kind": "card", "color": color, "start": round(t, 2), "end": round(t, 2)}
                cards.append(card_open)
        else:
            card_open = None
        scale = min(1.0, max_side / max(w, h))
        img = cv2.resize(fr, None, fx=scale, fy=scale) if scale < 1 else fr
        r = eng(img)
        boxes = []
        if r is not None and r.boxes is not None and len(r.boxes):
            boxes = list(zip(list(r.boxes), list(r.txts or []), list(r.scores or [])))
        seen = set()
        for pts, txt, sc in boxes:
            if sc < min_score or not txt.strip():
                continue
            xs = [p[0] / scale for p in pts]; ys = [p[1] / scale for p in pts]
            bb = [round(min(xs) * sx), round(min(ys) * sy), round(max(xs) * sx), round(max(ys) * sy)]
            ang = abs(math.degrees(math.atan2(pts[1][1] - pts[0][1], pts[1][0] - pts[0][0])))
            ang = min(ang, abs(180 - ang))
            best = None
            for k, e in enumerate(open_events):
                if k in seen or t - e["end"] > max(2.5, step * 1.5):
                    continue
                score = _iou(e["bbox"], bb) + 0.5 * _sim(e["text"], txt)
                if score > 0.6 and (best is None or score > best[0]):
                    best = (score, k)
            if best:
                e = open_events[best[1]]; seen.add(best[1])
                e["end"] = t; e["frames"] += 1
                e["boxes"].append(bb); e["angles"].append(ang)
                if len(txt) > len(e["text"]):
                    e["text"] = txt
            else:
                ev = {"text": txt, "bbox": bb, "boxes": [bb], "angles": [ang], "start": t, "end": t, "frames": 1}
                open_events.append(ev); events.append(ev)
        # cerrar los que llevan tiempo sin verse
        open_events = [e for e in open_events if t - e["end"] <= max(2.5, step * 1.5)]
        t += step
    cap.release()
    events = _merge_split(events, gap=3.0)
    out_events = []
    for e in events:
        if e["frames"] < 2 and (e["end"] - e["start"]) < step:
            continue  # una sola muestra: ruido
        arr = np.array(e["boxes"]); bb = [int(v) for v in np.median(arr, axis=0)]
        # desviación robusta de la caja (percentil 90 de |caja - mediana|): una lectura torcida no debe convertir
        # una marca de agua quieta en "texto que se mueve"
        jitter = float(np.percentile(np.abs(arr - np.array(bb)), 90)) if len(arr) > 1 else 0.0
        d = e["end"] - e["start"] + step
        height = bb[3] - bb[1]
        cy = (bb[1] + bb[3]) / 2 / ch; cx = (bb[0] + bb[2]) / 2 / cw
        angle = float(np.median(e["angles"])) if e.get("angles") else 0.0
        coverage = e["frames"] * step / max(d, step)  # fracción del tramo en que el OCR lo vio
        if d >= 0.5 * dur and jitter < 0.02 * cw and coverage > 0.5:
            kind = "watermark"
        elif cy > 0.78 and abs(cx - 0.5) < 0.2 and 1.0 <= d <= 8 and jitter < 0.03 * cw:
            kind = "subtitle"
        elif d >= 1.0 and jitter < 0.015 * cw and angle < 5 and height >= 0.03 * ch:
            kind = "text"
        else:
            kind = "scene_text"
        out_events.append({"kind": kind, "text": e["text"], "bbox": bb, "start": round(e["start"], 2), "end": round(e["end"] + step, 2),
                           "frames": e["frames"], "jitter_px": round(jitter), "angle_deg": round(angle, 1)})
    for c in cards:
        c["end"] = round(c["end"] + step, 2)
    cards = [c for c in cards if c["end"] - c["start"] >= 1.0]
    subs = [e for e in out_events if e["kind"] == "subtitle"]
    burned = len(subs) >= 3 and sum(e["end"] - e["start"] for e in subs) > 0.25 * dur
    out_events = watermark_pass(out_events, dur, cw)
    result = {"video": str(video), "duration": round(dur, 2), "canvas": [cw, ch], "sample_fps": sample_fps, "samples": samples,
              "events": sorted(out_events, key=lambda e: e["start"]), "cards": cards, "burned_subtitles": burned}
    result["zones"] = zone_report(result)
    return result


def watermark_pass(events: list[dict], dur: float, cw: int, min_cover: float = 0.5) -> list[dict]:
    """Marca de agua = misma zona (IoU > 0.6, quieta) ocupada en total >= `min_cover` del vídeo, aunque el OCR la
    pierda a ratos o lea 'CLIENTE A', 'CLIENTE A:' o 'RESPAR'. Los trozos pasan a `watermark` y se añade un evento
    resumen que cubre todo el vídeo (es lo que importa para colocar overlays)."""
    groups: list[list[dict]] = []
    for e in sorted(events, key=lambda e: e["start"]):
        if e["kind"] == "subtitle" or e.get("summary"):
            continue
        for g in groups:
            if _iou(g[0]["bbox"], e["bbox"]) > 0.6:
                g.append(e); break
        else:
            groups.append([e])
    out = list(events)
    for g in groups:
        cover = sum(x["end"] - x["start"] for x in g)
        if len(g) >= 2 and cover >= min_cover * dur:
            for x in g:
                x["kind"] = "watermark"
            arr = np.array([x["bbox"] for x in g])
            out.append({"kind": "watermark", "text": max((x["text"] for x in g), key=len), "bbox": [int(v) for v in np.median(arr, axis=0)],
                        "start": 0.0, "end": round(dur, 2), "frames": sum(x["frames"] for x in g), "jitter_px": 0,
                        "angle_deg": 0.0, "coverage": round(cover / dur, 2), "summary": True})
    return out


def _merge_split(events: list[dict], gap: float = 3.0) -> list[dict]:
    """Une eventos de la misma zona (IoU > 0.5) y texto parecido separados por menos de `gap` s: el OCR pierde
    alguna muestra y partiría una marca de agua en veinte trozos."""
    events = sorted(events, key=lambda e: e["start"])
    merged: list[dict] = []
    for e in events:
        target = None
        for m in merged:
            if e["start"] - m["end"] <= gap and _iou(m["bbox"], e["bbox"]) > 0.5 and _sim(m["text"], e["text"]) > 0.5:
                target = m; break
        if target is None:
            merged.append(dict(e)); continue
        target["end"] = max(target["end"], e["end"]); target["frames"] += e["frames"]
        target["boxes"] = target["boxes"] + e["boxes"]; target["angles"] = target.get("angles", []) + e.get("angles", [])
        if len(e["text"]) > len(target["text"]):
            target["text"] = e["text"]
    return merged


def zone_report(res: dict) -> dict:
    """Ocupación de una rejilla 3×3 en % del tiempo (texto o tarjeta) y ventanas libres por zona."""
    cw, ch = res["canvas"]; dur = res["duration"]
    step = 1.0 / res["sample_fps"]; nb = max(1, int(math.ceil(dur / step)))
    occ = {z: np.zeros(nb, dtype=bool) for z in ZONES}
    for e in res["events"]:
        x0, y0, x1, y1 = e["bbox"]
        cols = {min(2, int(3 * x / cw)) for x in (x0, (x0 + x1) / 2, x1)}
        rows = {min(2, int(3 * y / ch)) for y in (y0, (y0 + y1) / 2, y1)}
        i0, i1 = int(e["start"] / step), min(nb, int(math.ceil(e["end"] / step)))
        for r in rows:
            for c in cols:
                occ[ZONES[r * 3 + c]][i0:i1] = True
    for c in res["cards"]:
        i0, i1 = int(c["start"] / step), min(nb, int(math.ceil(c["end"] / step)))
        for z in ZONES:
            occ[z][i0:i1] = True
    report = {}
    for z in ZONES:
        a = occ[z]
        busy = float(a.mean()) if nb else 0.0
        windows = []; start = None
        for i, v in enumerate(list(a) + [True]):
            if not v and start is None:
                start = i
            if v and start is not None:
                if (i - start) * step >= 3.0:
                    windows.append([round(start * step, 1), round(i * step, 1)])
                start = None
        report[z] = {"busy_pct": round(busy * 100), "free_windows": windows[:12]}
    return report


def annotate(res: dict, out_png: str | Path, video: str | Path | None = None) -> Path:
    """Mapa 3×3 de ocupación + lista de eventos sobre un fotograma de fondo (si se da el vídeo)."""
    cw, ch = res["canvas"]
    W, H = 960, round(960 * ch / cw)
    if video:
        cap = cv2.VideoCapture(str(video)); cap.set(cv2.CAP_PROP_POS_FRAMES, 30); ok, fr = cap.read(); cap.release()
        bg = cv2.resize(fr, (W, H)) if ok else np.full((H, W, 3), 40, np.uint8)
        bg = (bg * 0.45).astype(np.uint8)
    else:
        bg = np.full((H, W, 3), 40, np.uint8)
    sx, sy = W / cw, H / ch
    colors = {"watermark": (60, 60, 230), "text": (0, 197, 245), "subtitle": (200, 120, 0)}
    for e in res["events"]:
        if e["kind"] == "scene_text" or (e["end"] - e["start"]) < 2:
            continue
        x0, y0, x1, y1 = e["bbox"]
        c = colors.get(e["kind"], (200, 200, 200))
        cv2.rectangle(bg, (int(x0 * sx), int(y0 * sy)), (int(x1 * sx), int(y1 * sy)), c, 2)
    for i, z in enumerate(ZONES):
        r, c = divmod(i, 3)
        x, y = int(c * W / 3), int(r * H / 3)
        pct = res["zones"][z]["busy_pct"]
        cv2.rectangle(bg, (x, y), (int((c + 1) * W / 3), int((r + 1) * H / 3)), (255, 255, 255), 1)
        cv2.putText(bg, f"{z} {pct}%", (x + 8, y + 24), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)
    # leyenda + lista
    rows = [f"{e['start']:6.1f}-{e['end']:6.1f}  {e['kind']:<10} {e['text'][:38]}" for e in res["events"] if e["kind"] != "scene_text" and (e["end"] - e["start"]) >= 2][:40]
    rows += [f"{c['start']:6.1f}-{c['end']:6.1f}  card       {c['color']}" for c in res["cards"]]
    panel = np.full((max(H, 24 * len(rows) + 40), 640, 3), 24, np.uint8)
    cv2.putText(panel, "rojo=marca de agua  amarillo=texto estable (rotulo u objeto quieto)  naranja=subtitulo  (>= 2 s)", (10, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1, cv2.LINE_AA)
    for i, row in enumerate(rows):
        cv2.putText(panel, row, (10, 50 + 24 * i), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (230, 230, 230), 1, cv2.LINE_AA)
    if panel.shape[0] > H:
        bg = np.vstack([bg, np.full((panel.shape[0] - H, W, 3), 24, np.uint8)])
    out = Path(out_png); out.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out), np.hstack([bg, panel]))
    return out


# ---------- colisiones con un storyboard ----------

def overlay_bbox(o: dict, W: int, H: int) -> list[int] | None:
    """Caja aproximada de un overlay del storyboard (los de pantalla completa devuelven None)."""
    t = o["type"]
    if t == "box":
        return [o["x"], o["y"], o["x"] + round(54 * 0.5 * len(o["text"]) + 52), o["y"] + 80]
    if t == "kinetic":
        size = o.get("size", 124); lines = o["lines"]
        wmax = max(sum(len(w["text"]) + 1 for w in line) for line in lines) * size * 0.5
        return [o["x"], o["y"], o["x"] + round(wmax), o["y"] + round(size * 1.1 * len(lines))]
    if t == "lower_third":
        n = max(len(o["title"]) + 8, len(o.get("subtitle", "")) + 2)
        return [o["x"], o["y"], o["x"] + round(34 * 0.62 * n + 48), o["y"] + (128 if o.get("subtitle") else 68)]
    if t == "pointer":
        bx, by = o["box"]
        return [min(bx, o["dot"][0]), min(by, o["dot"][1]), max(bx + round(30 * 0.55 * len(o["text"]) + 40), o["dot"][0]), max(by + 70, o["dot"][1])]
    if t == "image":
        return [o["x"], o["y"], o["x"] + o["w"], o["y"] + o["w"]]
    if t == "draw":
        return [o["x"], o["y"], o["x"] + o["w"], o["y"] + o.get("h", o["w"])]
    if t == "broll" and o.get("pip"):
        p = o["pip"]; return [p["x"], p["y"], p["x"] + p["w"], p["y"] + p["h"]]
    return None


def collisions(sb: dict, gfx: dict) -> list[str]:
    """Avisos: overlay del storyboard que pisa (tiempo y espacio) texto/gráficos existentes o una tarjeta del vídeo."""
    W = int(sb.get("canvas", {}).get("width", 1920)); H = int(sb.get("canvas", {}).get("height", 1080))
    out = []
    full = {"card", "list_focus", "card_words", "brand_card"}
    for o in sb.get("overlays", []):
        bb = overlay_bbox(o, W, H)
        for e in gfx.get("events", []):
            if e["kind"] == "scene_text" and (e["end"] - e["start"]) < 2:
                continue
            if o["end"] <= e["start"] or o["start"] >= e["end"]:
                continue
            if bb is not None and _iou(bb, e["bbox"]) > 0.02:
                out.append(f"{o['id']} ({o['type']}) pisa el texto '{e['text'][:30]}' ({e['kind']}) en {max(o['start'], e['start']):.1f}–{min(o['end'], e['end']):.1f} s")
        for c in gfx.get("cards", []):
            if o["end"] <= c["start"] or o["start"] >= c["end"]:
                continue
            if o["type"] in full or (o["type"] == "chart" and not o.get("panel")) or (o["type"] == "broll" and not o.get("pip")):
                out.append(f"{o['id']} ({o['type']}) tapa la tarjeta del propio vídeo ({c['color']}) en {max(o['start'], c['start']):.1f}–{min(o['end'], c['end']):.1f} s")
    if gfx.get("burned_subtitles") and sb.get("captions"):
        out.append("el vídeo ya trae subtítulos quemados: quita `captions` o súbelos con `caption_style.bottom`")
    return out
