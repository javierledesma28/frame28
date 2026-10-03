"""B-roll por palabra clave: sugerir búsquedas desde la transcripción, buscar en Pexels/Pixabay, descargar con la
licencia registrada y recortar el tramo que se va a usar.

Claves: variables de entorno `PEXELS_API_KEY` y `PIXABAY_API_KEY` (o `~/.config/frame28/keys.json` con esas mismas
claves). Sin clave no se busca en ese proveedor; los ficheros propios del usuario funcionan igual como `broll`.
Licencias: Pexels License y Pixabay Content License permiten uso comercial sin atribución; aun así se guarda un
sidecar `.json` con autor, página y licencia junto a cada descarga.
"""
from __future__ import annotations

import json
import os
import re
import urllib.parse
import urllib.request
from pathlib import Path

from .env import ffmpeg, run
from .captions import load_captions

KEYS_FILE = Path.home() / ".config" / "frame28" / "keys.json"
UA = "Frame28/0.2 (+https://frame28.t28.io)"

STOP = {
    "es": set("""a al algo alguna algunas alguno algunos ante antes aquel aquella aquellas aquello aquellos aquí así aun aunque bien
    cada casi como con contra cosa cosas cual cuales cuando cuanto de del desde donde dos e el ella ellas ello ellos en entre era
    erais eran eras eres es esa esas ese eso esos esta estaba estamos estan están estar estas este esto estos estoy fue fueron fui
    fuimos ha hace hacen hacer hacia han has hasta hay he hoy la las le les lo los luego mas más me mi mis mismo mucho muy nada ni
    no nos nosotros nuestra nuestro o os otra otras otro otros para pero poco por porque que qué quien quienes se sea ser si sí sido
    siempre sin sobre solo sólo somos son soy su sus tal también tan tanto te tener tengo ti tiene tienen todo todos tu tus un una
    unas uno unos usted vamos vez ya yo va van voy vas bueno pues eh decir quiero digo veces vez minuto minutos primero segundo
    tercero ejemplo presento presente enseño muestro tarda podemos tenerlo""".split()),
    "en": set("""a about above after again against all am an and any are as at be because been before being below between both but
    by can did do does doing down during each few for from further had has have having he her here hers him his how i if in into
    is it its just me more most my no nor not of off on once only or other our out over own same she so some such than that the
    their them then there these they this those through to too under until up very was we were what when where which while who
    whom why will with you your yeah actually here's really like just thing things""".split()),
}


def _keys() -> dict:
    k = {}
    if KEYS_FILE.exists():
        try:
            k.update(json.loads(KEYS_FILE.read_text(encoding="utf-8-sig")))
        except Exception:
            pass
    for name in ("PEXELS_API_KEY", "PIXABAY_API_KEY"):
        if os.environ.get(name):
            k[name] = os.environ[name]
    return k


def providers_available() -> dict:
    k = _keys()
    return {"pexels": bool(k.get("PEXELS_API_KEY")), "pixabay": bool(k.get("PIXABAY_API_KEY"))}


# ---------- sugerencias desde la transcripción ----------

def suggest(captions_path: str | Path, lang: str = "es", per_phrase: int = 2, min_len: float = 2.0) -> list[dict]:
    """Por cada frase de captions.json: 1–3 palabras de contenido como consulta de stock. El agente afina la consulta
    (traduce al inglés, que es lo que mejor indexan los bancos) y decide en qué frases va B-roll."""
    caps = load_captions(captions_path)
    stop = STOP.get(lang, set())
    out = []
    for c in caps:
        if c["end"] - c["start"] < min_len:
            continue
        toks = [re.sub(r"[^\wáéíóúñü]", "", t.lower()) for t in c["text"].split()]
        content = [t for t in toks if len(t) > 3 and t not in stop and not t.isdigit()]
        seen: list[str] = []
        for t in content:
            if t not in seen:
                seen.append(t)
        if seen:
            out.append({"start": c["start"], "end": c["end"], "text": c["text"], "keywords": seen[:per_phrase + 1],
                        "query": " ".join(seen[:per_phrase])})
    return out


# ---------- búsqueda ----------

def _get_json(url: str, headers: dict | None = None) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def search(query: str, kind: str = "video", provider: str = "auto", orientation: str = "landscape",
           per_page: int = 8, min_duration: float = 3.0) -> list[dict]:
    """Devuelve candidatos normalizados: id, provider, kind, url (descarga), page, thumb, width, height, duration,
    author, license. `provider` auto = todos los que tengan clave."""
    keys = _keys()
    provs = ["pexels", "pixabay"] if provider == "auto" else [provider]
    out: list[dict] = []
    if "pexels" in provs and keys.get("PEXELS_API_KEY"):
        h = {"Authorization": keys["PEXELS_API_KEY"]}
        q = urllib.parse.quote(query)
        if kind == "video":
            d = _get_json(f"https://api.pexels.com/videos/search?query={q}&orientation={orientation}&size=medium&per_page={per_page}", h)
            for v in d.get("videos", []):
                if v.get("duration", 0) < min_duration:
                    continue
                files = sorted((f for f in v.get("video_files", []) if f.get("width")), key=lambda f: abs((f.get("width") or 0) - 1920))
                if not files:
                    continue
                out.append({"id": f"pexels-{v['id']}", "provider": "pexels", "kind": "video", "url": files[0]["link"],
                            "page": v.get("url"), "thumb": v.get("image"), "width": files[0].get("width"), "height": files[0].get("height"),
                            "duration": v.get("duration"), "author": (v.get("user") or {}).get("name"),
                            "license": "Pexels License (uso comercial, sin atribución obligatoria)"})
        else:
            d = _get_json(f"https://api.pexels.com/v1/search?query={q}&orientation={orientation}&size=large&per_page={per_page}", h)
            for p in d.get("photos", []):
                out.append({"id": f"pexels-{p['id']}", "provider": "pexels", "kind": "photo", "url": p["src"].get("large2x") or p["src"].get("original"),
                            "page": p.get("url"), "thumb": p["src"].get("medium"), "width": p.get("width"), "height": p.get("height"),
                            "duration": None, "author": p.get("photographer"), "license": "Pexels License (uso comercial, sin atribución obligatoria)"})
    if "pixabay" in provs and keys.get("PIXABAY_API_KEY"):
        k = keys["PIXABAY_API_KEY"]; q = urllib.parse.quote(query)
        orient = "horizontal" if orientation == "landscape" else "vertical" if orientation == "portrait" else "all"
        if kind == "video":
            d = _get_json(f"https://pixabay.com/api/videos/?key={k}&q={q}&per_page={max(3, per_page)}&safesearch=true")
            for v in d.get("hits", []):
                if v.get("duration", 0) < min_duration:
                    continue
                vs = v.get("videos", {}); f = vs.get("large") or vs.get("medium") or vs.get("small")
                if not f:
                    continue
                out.append({"id": f"pixabay-{v['id']}", "provider": "pixabay", "kind": "video", "url": f["url"], "page": v.get("pageURL"),
                            "thumb": (f.get("thumbnail") or ""), "width": f.get("width"), "height": f.get("height"),
                            "duration": v.get("duration"), "author": v.get("user"),
                            "license": "Pixabay Content License (uso comercial, sin atribución obligatoria)"})
        else:
            d = _get_json(f"https://pixabay.com/api/?key={k}&q={q}&orientation={orient}&per_page={max(3, per_page)}&safesearch=true&image_type=photo")
            for p in d.get("hits", []):
                out.append({"id": f"pixabay-{p['id']}", "provider": "pixabay", "kind": "photo", "url": p.get("largeImageURL"), "page": p.get("pageURL"),
                            "thumb": p.get("previewURL"), "width": p.get("imageWidth"), "height": p.get("imageHeight"), "duration": None,
                            "author": p.get("user"), "license": "Pixabay Content License (uso comercial, sin atribución obligatoria)"})
    return out


# ---------- descarga, sidecar de licencia y recorte ----------

def fetch(item: dict, out_dir: str | Path, trim_in: float = 0.0, duration: float | None = None, width: int | None = None) -> dict:
    """Descarga el candidato a `out_dir/<id>.<ext>`, guarda `<id>.json` (licencia, autor, página) y, si `duration` o
    `trim_in`, deja además `<id>_cut.mp4` recortado y sin audio (listo para el overlay `broll`)."""
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    ext = ".mp4" if item["kind"] == "video" else ".jpg"
    dst = out / f"{item['id']}{ext}"
    if not dst.exists():   # atómico y con todos los bytes: un corte ya no deja un vídeo truncado que parezca bueno
        from .env import fetch_atomic
        fetch_atomic(item["url"], dst, timeout=120, headers={"User-Agent": UA})
    side = {k: item.get(k) for k in ("id", "provider", "kind", "page", "author", "license", "width", "height", "duration")}
    side["file"] = dst.name
    (out / f"{item['id']}.json").write_text(json.dumps(side, indent=1, ensure_ascii=False), encoding="utf-8")
    res = {"file": str(dst), "sidecar": str(out / f"{item['id']}.json"), **side}
    if item["kind"] == "video" and (trim_in or duration):
        cut = out / f"{item['id']}_cut.mp4"
        vf = f"scale={width}:-2" if width else "scale='min(1920,iw)':-2"
        cmd = [ffmpeg(), "-y", "-loglevel", "error", "-ss", str(trim_in), "-i", str(dst)]
        if duration:
            cmd += ["-t", str(duration)]
        cmd += ["-an", "-vf", vf, "-r", "30", "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(cut)]
        run(cmd, check=True)
        res["cut"] = str(cut)
    return res


def sheet(items: list[dict], out_png: str | Path, cols: int = 4, tile: int = 480) -> Path:
    """Hoja de contacto de candidatos (miniaturas con id, autor y duración) para elegir de un vistazo."""
    import cv2
    import numpy as np

    from .imgio import imwrite

    tiles = []
    for it in items:
        img = None
        try:
            req = urllib.request.Request(it["thumb"], headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=30) as r:
                buf = np.frombuffer(r.read(), dtype=np.uint8)
            img = cv2.imdecode(buf, cv2.IMREAD_COLOR)
        except Exception:
            img = None
        if img is None:
            img = np.zeros((tile * 9 // 16, tile, 3), dtype=np.uint8)
        h = tile * 9 // 16
        img = cv2.resize(img, (tile, h))
        label = f"{it['id']}  {it.get('duration') or ''}{'s' if it.get('duration') else ''}  {it.get('author') or ''}"
        cv2.rectangle(img, (0, h - 30), (tile, h), (0, 0, 0), -1)
        cv2.putText(img, label[:60], (8, h - 9), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
        tiles.append(img)
    if not tiles:
        raise SystemExit("sin candidatos")
    while len(tiles) % cols:
        tiles.append(np.zeros_like(tiles[0]))
    rows = [np.hstack(tiles[i:i + cols]) for i in range(0, len(tiles), cols)]
    out = Path(out_png); out.parent.mkdir(parents=True, exist_ok=True)
    imwrite(str(out), np.vstack(rows))
    return out
