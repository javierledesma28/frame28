"""Fábrica de shorts: de un vídeo largo, los tramos de 15–45 s con más "momentos" de venta, tres ganchos por tramo,
y el recorte listo (clip, voz, palabras y subtítulos remapeados) con un storyboard de partida que ya construye.

Momentos que puntúan (ES/EN): resultado ("that's it", "turned out", "queda", "mira"), promesa ("beginner",
"easy", "cualquiera", "fácil"), objeción ("isn't it", "what if", "¿y si"), cifras y menciones del producto.
Un tramo empieza y termina en frase (captions.json), no a mitad de palabra.

`markers` usa los mismos momentos para el vídeo entero (o un short ya recortado): en cada frase de resultado
propone el `before_after` con dos instantes del propio clip, el `draw` check y el `kinetic` con la frase real; en
cada promesa, el `kinetic`. Son overlays listos para pegar en el storyboard, con posiciones orientativas.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from .captions import load_captions, load_words

MOMENTS = {
    "result": {
        "es": [r"\bqued[aó]\b", r"\bmira\b", r"\blisto\b", r"\bya está\b", r"\basí de fácil\b", r"\bperfecto\b", r"\bprecioso\b", r"\bterminad[oa]\b"],
        "en": [r"\bthat'?s it\b", r"\bturned out\b", r"\blook at (that|this)\b", r"\bbeautiful\b", r"\bperfect\b", r"\bdone\b", r"\bfinished\b", r"\bhere (it|they) (is|are)\b", r"\bta-?da\b"],
    },
    "promise": {
        "es": [r"\bcualquiera\b", r"\bfácil\b", r"\bsencill[oa]\b", r"\bsin experiencia\b", r"\ben \d+ minutos\b", r"\bprincipiante"],
        "en": [r"\bbeginner", r"\beasy\b", r"\banyone can\b", r"\bsimple\b", r"\bno (skills|experience|guesswork)\b", r"\bin \d+ minutes\b", r"\bfriendly\b"],
    },
    "objection": {
        "es": [r"¿y si\b", r"\bno es (muy|demasiado)\b", r"\bda miedo\b", r"\bparece difícil\b", r"\bmiedo\b"],
        "en": [r"\bisn'?t (it|that|glass|this)\b", r"\bwhat if\b", r"\btoo (hard|slippery|difficult|expensive)\b", r"\bintimidating\b", r"\bafraid\b", r"\bscared\b"],
    },
    "number": {"es": [r"\b\d+\s?%", r"\b\d{2,}\b", r"\bveces\b"], "en": [r"\b\d+\s?%", r"\b\d{2,}\b", r"\btimes\b", r"\bx\d\b"]},
}
WEIGHTS = {"result": 3.0, "promise": 2.0, "objection": 2.5, "number": 1.0, "product": 2.0}


def _moments(caps: list[dict], lang: str, keywords: list[str]) -> list[dict]:
    out = []
    for c in caps:
        text = c["text"]
        for kind, langs in MOMENTS.items():
            for pat in langs.get(lang, []) + (langs.get("en", []) if lang != "en" else []):
                m = re.search(pat, text, re.I)
                if m:
                    out.append({"t": c["start"], "kind": kind, "text": text.strip(), "match": m.group(0)})
                    break
        for kw in keywords:
            if kw and re.search(re.escape(kw), text, re.I):
                out.append({"t": c["start"], "kind": "product", "text": text.strip(), "match": kw})
                break
    return out


def plan(captions_path: str | Path, target: float = 30.0, count: int = 5, lang: str = "en",
         min_len: float = 15.0, max_len: float = 45.0, keywords: list[str] | None = None, brand: str | None = None) -> dict:
    caps = load_captions(captions_path)
    keywords = [k for k in (keywords or []) if k]
    moments = _moments(caps, lang, keywords)
    cands = []
    n = len(caps)
    for i in range(n):
        for j in range(i, n):
            s, e = caps[i]["start"], caps[j]["end"]
            d = e - s
            if d < min_len:
                continue
            if d > max_len:
                break
            inside = [m for m in moments if s <= m["t"] < e]
            score = sum(WEIGHTS[m["kind"]] for m in inside)
            kinds = {m["kind"] for m in inside}
            if any(m["kind"] in ("objection", "promise") and m["t"] - s < 6 for m in inside):
                score += 2.0  # arranca con dolor o promesa: gancho natural
            if any(m["kind"] == "result" and e - m["t"] < 10 for m in inside):
                score += 2.0  # termina con el resultado
            score += len(kinds) * 0.5
            score -= abs(d - target) / target * 2.0
            cands.append({"start": round(s, 2), "end": round(e, 2), "duration": round(d, 2), "score": round(score, 2),
                          "moments": inside, "phrases": [c["text"].strip() for c in caps[i:j + 1]]})
    cands.sort(key=lambda c: -c["score"])
    chosen: list[dict] = []
    for c in cands:
        if all(c["end"] <= x["start"] + 3 or c["start"] >= x["end"] - 3 for x in chosen):
            chosen.append(c)
        if len(chosen) >= count:
            break
    chosen.sort(key=lambda c: c["start"])
    for k, c in enumerate(chosen, 1):
        c["id"] = f"s{k}"
        c["hooks"] = hooks_for(c, lang, brand)
    return {"captions": str(captions_path), "lang": lang, "target": target, "moments": len(moments), "clips": chosen}


FILLERS_START = {
    "en": ["i think", "i mean", "you know", "so", "and", "but", "well", "now", "okay", "ok", "also", "then", "just", "actually", "honestly", "basically"],
    "es": ["creo que", "o sea", "bueno", "pues", "y", "pero", "entonces", "ahora", "vale", "también", "la verdad", "básicamente", "además", "que", "es decir"],
}
TRAILING_STOP = {"en": {"on", "in", "with", "the", "a", "an", "of", "to", "for", "and", "or", "at", "by", "is", "are", "it", "that", "this", "your", "my"},
                 "es": {"en", "con", "de", "del", "la", "el", "los", "las", "un", "una", "y", "o", "a", "para", "por", "que", "es", "son", "tu", "mi", "unos", "unas"}}
WINDOW_WORDS = 8
HEDGES = {"en": [r"\bi think\b", r"\bi guess\b", r"\bkind of\b", r"\bsort of\b", r"\ba little\b", r"\bpretty\b", r"\breally\b"],
          "es": [r"\bcreo que\b", r"\bun poco\b", r"\bbastante\b", r"\brealmente\b", r"\bla verdad\b"]}
MAX_LINE_WORDS = 5
MAX_LINE_CHARS = 26


def _clause(text: str, match: str) -> str:
    """La cláusula (entre signos de puntuación) que contiene el momento."""
    parts = re.split(r"(?<=[.,;:!?…—])\s+|\s+[-–—]\s+", text)
    for part in parts:
        if match.lower() in part.lower():
            return part.strip()
    return text.strip()


def _window(clause: str, match: str, n: int = WINDOW_WORDS) -> str:
    """Si la cláusula es larga, quédate con ~n palabras alrededor del momento (el resto es contexto que no cabe)."""
    words = clause.split()
    if len(words) <= n + 1:
        return clause
    low = [w.lower().strip(".,;:!?\"'") for w in words]
    mw = match.lower().split()
    idx = next((i for i in range(len(low)) if low[i:i + len(mw)] == mw), None)
    if idx is None:
        idx = next((i for i, w in enumerate(low) if mw[0] in w), 0)
    start = max(0, min(idx - 1, len(words) - n))  # lo que importa es lo que sigue al momento
    return " ".join(words[start:start + n])


def _trim_trailing(text: str, lang: str) -> str:
    words = text.split()
    stop = TRAILING_STOP.get(lang, set()) | TRAILING_STOP["en"]
    while len(words) > 2 and words[-1].lower().strip(".,;:!?") in stop:
        words.pop()
    return " ".join(words)


def _clean(clause: str, lang: str) -> str:
    c = clause.strip().strip("\"'“”‘’")
    low = c.lower()
    changed = True
    while changed:  # quita arranques de relleno encadenados: "and i think just ..."
        changed = False
        for f in FILLERS_START.get(lang, []) + (FILLERS_START["en"] if lang != "en" else []):
            if low.startswith(f + " ") or low.startswith(f + ","):
                c = c[len(f):].lstrip(" ,"); low = c.lower(); changed = True
    for h in HEDGES.get(lang, []):
        c = re.sub(h, "", c, flags=re.I)
    c = re.sub(r"\s{2,}", " ", c).strip(" ,;:")
    return c[:1].upper() + c[1:] if c else c


def _two_lines(text: str, max_words: int = MAX_LINE_WORDS, max_chars: int = MAX_LINE_CHARS) -> list[str]:
    """Parte en dos líneas de <= 5 palabras / 26 caracteres en el punto más natural; recorta si no cabe."""
    MAX_LINE_WORDS, MAX_LINE_CHARS = max_words, max_chars  # noqa: N806  límites locales (los ganchos usan los globales)
    words = text.split()
    if len(words) <= MAX_LINE_WORDS and len(text) <= MAX_LINE_CHARS:
        return [text]
    words = words[: 2 * MAX_LINE_WORDS]
    best = None
    for i in range(1, len(words)):
        a, b = " ".join(words[:i]), " ".join(words[i:])
        if len(a) > MAX_LINE_CHARS or len(b) > MAX_LINE_CHARS or i > MAX_LINE_WORDS or len(words) - i > MAX_LINE_WORDS:
            continue
        score = abs(len(a) - len(b)) - (8 if a[-1:] in ",;:" else 0) - (4 if words[i].lower() in ("with", "and", "that", "con", "y", "que", "para", "to", "for", "of") else 0)
        if words[i - 1].lower().strip(".,;:!?") in TRAILING_STOP["en"] | TRAILING_STOP["es"]:
            score += 30  # no partir tras "en tu", "with a"...
        if best is None or score < best[0]:
            best = (score, a, b)
    if best is None:  # no hay corte válido: primera línea de 5 palabras, segunda con las palabras enteras que quepan
        a_words = words[:MAX_LINE_WORDS]
        while len(" ".join(a_words)) > MAX_LINE_CHARS and len(a_words) > 1:
            a_words.pop()
        rest = words[len(a_words):len(a_words) + MAX_LINE_WORDS]
        while rest and len(" ".join(rest)) > MAX_LINE_CHARS:
            rest.pop()
        return [" ".join(a_words)] + ([" ".join(rest)] if rest else [])
    return [best[1], best[2]]


STRONG = {"en": [r"\byou\b", r"\byour\b", r"\bnever\b", r"\balways\b", r"\bonly\b", r"\bsecret\b", r"\bmistake\b", r"\bwrong\b", r"\bbest\b", r"\bfree\b"],
          "es": [r"\btú\b", r"\btu\b", r"\bnunca\b", r"\bsiempre\b", r"\bsolo\b", r"\bsecreto\b", r"\berror\b", r"\bmal\b", r"\bmejor\b", r"\bgratis\b"]}


def strongest_phrase(clip: dict, lang: str) -> dict | None:
    """Para un tramo sin momentos: la frase del propio tramo con más fuerza como gancho. Puntúa preguntas, cifras,
    segunda persona y palabras fuertes; penaliza las largas (no caben en dos líneas) y las de relleno."""
    phrases = [p.strip() for p in clip.get("phrases", []) if p and p.strip()]
    if not phrases:
        return None
    best = None
    for i, ph in enumerate(phrases):
        clause = _clause(ph, ph)
        words = clause.split()
        if len(words) < 3:
            continue
        score = 0.0
        if "?" in clause:
            score += 3
        if re.search(r"\d", clause):
            score += 2
        score += sum(1 for pat in STRONG.get(lang, STRONG["en"]) if re.search(pat, clause, re.I))
        low = clause.lower()
        if any(low.startswith(f + " ") for f in FILLERS_START.get(lang, []) + FILLERS_START["en"]):
            score -= 1
        if 4 <= len(words) <= 10:
            score += 1
        elif len(words) > 16:
            score -= 2
        score -= i * 0.05  # a igualdad, la primera (es el arranque natural del tramo)
        if best is None or score > best[0]:
            best = (score, ph, clause)
    if best is None:
        return None
    return {"text": best[1], "match": best[2], "t": clip.get("start", 0.0)}


def hooks_for(clip: dict, lang: str, brand: str | None = None) -> list[dict]:
    """Tres ganchos de tipos distintos con las **palabras reales** del hablante: la cláusula donde ocurre el momento
    (resultado, objeción, promesa, cifra), sin relleno inicial, en dos líneas. Cada gancho lleva `quote` y `t`.
    Si el tramo no tiene momentos, el gancho sale de la frase más fuerte del propio tramo (`statement`); la plantilla
    de curiosidad queda como último recurso."""
    es = lang == "es"
    hooks: list[dict] = []
    used: set[str] = set()

    def add(kind: str, m: dict, lines: list[str]) -> None:
        lines = [l for l in lines if l][:2]
        key = " ".join(lines).lower()
        if not lines or key in used:
            return
        used.add(key)
        hooks.append({"type": kind, "lines": lines, "quote": m["text"].strip(), "t": m["t"]})

    first = lambda kind: next((m for m in clip["moments"] if m["kind"] == kind), None)
    obj, res, pro, num = first("objection"), first("result"), first("promise"), first("number")
    if obj:
        q = _trim_trailing(_clean(_window(_clause(obj["text"], obj["match"]), obj["match"]), lang).rstrip("."), lang)
        if not q.endswith("?"):
            q += "?"
        lines = _two_lines(q)
        if len(lines) == 1:
            lines.append("Pues no." if es else "Not anymore.")
        add("objection", obj, lines)
    if res:
        add("result", res, _two_lines(_trim_trailing(_clean(_window(_clause(res["text"], res["match"]), res["match"]), lang).rstrip(".!"), lang)))
    if pro:
        add("promise", pro, _two_lines(_trim_trailing(_clean(_window(_clause(pro["text"], pro["match"]), pro["match"]), lang).rstrip(".!"), lang)))
    if num:
        add("number", num, _two_lines(_trim_trailing(_clean(_window(_clause(num["text"], num["match"]), num["match"]), lang).rstrip(".!"), lang)))
    if len(hooks) < 3:
        sp = strongest_phrase(clip, lang)
        if sp:
            q = _trim_trailing(_clean(_window(_clause(sp["text"], sp["match"]), sp["match"]), lang).rstrip(".!"), lang)
            if q and not q.endswith("?") and len(q.split()) <= 10 and "?" in sp["text"]:
                q += "?"
            add("statement", sp, _two_lines(q))
    if len(hooks) < 3:
        hooks.append({"type": "curiosity", "lines": [("¿Se puede hacer esto" if es else "Can you actually do this"), ("con tus manos?" if es else "with your own hands?")],
                      "quote": "", "t": clip["start"]})
    return hooks[:3]


def extract(clip: dict, video: str | Path, audio: str | Path | None, words: str | Path | None, captions: str | Path | None,
            out_dir: str | Path, pad: float = 0.15) -> dict:
    """Recorta el tramo con `cut.apply` (fundidos, palabras y subtítulos remapeados)."""
    from .cut import apply
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    s = max(0.0, clip["start"] - pad); e = clip["end"] + pad
    cuts = {"source_duration": None, "result_duration": round(e - s, 3), "min_gap": 0, "pad": 0,
            "keep": [{"start": round(s, 3), "end": round(e, 3)}], "removed": []}
    cp = out / "cuts.json"
    cp.write_text(json.dumps(cuts, indent=1), encoding="utf-8")
    r = apply(video, audio, cp, out, words, captions, None)
    r["clip"] = clip["id"]; r["start"] = s; r["end"] = e
    return r


def scaffold(clip: dict, clip_dir: str | Path, canvas: tuple[int, int] = (1080, 1920), platform: str = "tiktok",
             brand: str | dict | None = None, cta: dict | None = None, hook_index: int = 0, video_name: str = "clip.mp4",
             name: str = "storyboard.json") -> dict:
    """Storyboard de partida para el short: gancho, subtítulos por palabras, CTA al final. Construye tal cual.
    `name` permite guardar varias variantes en la misma carpeta (storyboard-hook1.json)."""
    d = Path(clip_dir)
    words = load_words(d / "words.json") if (d / "words.json").exists() else []
    dur = round(clip["end"] - clip["start"] + 0.3, 2)
    if words:
        dur = round(max(dur, words[-1]["end"] + 0.3), 2)
    W, H = canvas
    hook = (clip.get("hooks") or [{"lines": ["…"]}])[min(hook_index, len(clip.get("hooks", [])) - 1)]
    sb = {"version": 1, "meta": {"title": f"Short {clip['id']}", "lang": "en"},
          "canvas": {"width": W, "height": H, "fps": 30}, "platform": platform,
          "source": {"video": video_name, "audio": "voice.wav", "duration": dur},
          "speaker": {"side": "center"},
          "caption_style": {"preset": "pages", "words": "words.json", "max_words": 4, "bottom": int(0.18 * H)},
          "overlays": [{"type": "hook", "id": "hook", "start": 0.2, "end": min(3.2, dur - 1), "at": 0.3, "lines": hook["lines"], "bg": "accent"}]}
    if brand:
        bp = Path(brand) if isinstance(brand, str) else None
        if bp is not None and bp.suffix == ".json" and bp.exists():
            import os
            sb["brand"] = os.path.relpath(bp.resolve(), d.resolve()).replace("\\", "/")  # relativa al storyboard del short
        else:
            sb["brand"] = brand
    if cta:
        c = {"type": "cta", "id": "cta", "start": round(max(dur - 5.0, 3.5), 2), "end": dur, "at": round(max(dur - 4.9, 3.6), 2), **cta}
        sb["overlays"].append(c)
    sb["duration"] = dur
    sb["meta"]["title"] = f"Short {clip['id']} · gancho {hook_index + 1}: " + " / ".join(hook["lines"])
    p = d / name
    p.write_text(json.dumps(sb, indent=1, ensure_ascii=False), encoding="utf-8")
    return {"storyboard": str(p), "duration": dur, "hook": hook, "hook_index": hook_index}


def batch(clips_json: str | Path, clip_ids: list[str] | None, clips_dir: str | Path = "work/clips", out_dir: str | Path = "out/shorts",
          hook_indexes: list[int] | None = None, canvas: tuple[int, int] = (1080, 1920), platform: str = "tiktok",
          brand: str | dict | None = None, cta: dict | None = None, video_name: str = "clip.mp4", render: bool = True,
          quality: str = "high") -> dict:
    """Variantes de gancho en lote: para cada short (ya recortado con `clips cut`) y cada gancho, escribe
    `storyboard-hook<N>.json`, construye `project-hook<N>/` y, con `render`, pasa `check` y renderiza a
    `<out>/<id>-hook<N>.mp4` con su hoja de contacto. Deja `batch.json` en la carpeta de clips con el resultado de
    cada variante: lo que falla no detiene al resto. Las plataformas queman un creativo en 7–14 días: se rota el
    gancho, no el cuerpo, y esto deja todas las rotaciones listas de una vez."""
    from .build import build_project
    plan_ = json.loads(Path(clips_json).read_text(encoding="utf-8"))
    cdir = Path(clips_dir); odir = Path(out_dir)
    chosen = [c for c in plan_["clips"] if not clip_ids or c["id"] in clip_ids]
    variants = []; skipped = []
    for c in chosen:
        d = cdir / c["id"]
        if not (d / video_name).exists():
            skipped.append(c["id"]); continue
        idxs = hook_indexes if hook_indexes is not None else list(range(len(c.get("hooks") or [])))
        for k in idxs:
            if k >= len(c.get("hooks") or []):
                continue
            name = f"{c['id']}-hook{k}"
            v: dict = {"clip": c["id"], "hook_index": k, "name": name, "ok": False}
            try:
                s = scaffold(c, d, canvas, platform, brand, cta, k, video_name, name=f"storyboard-hook{k}.json")
                v["storyboard"] = s["storyboard"]; v["hook"] = s["hook"]["lines"]; v["type"] = s["hook"]["type"]
                b = build_project(s["storyboard"], d / f"project-hook{k}")
                v["project"] = b["project"]; v["warnings"] = b["warnings"]
                if render:
                    from .render import check as _check, render as _render
                    ck = _check(b["project"])
                    v["check"] = {"passed": ck["passed"], "errors": ck["errors"], "contrast_warnings": ck["contrast_warnings"]}
                    if not ck["passed"]:
                        raise RuntimeError("check falló: " + "; ".join(ck["errors"])[:200])
                    odir.mkdir(parents=True, exist_ok=True)
                    rr = _render(b["project"], odir / f"{name}.mp4", quality)
                    if not rr["ok"]:
                        raise RuntimeError("render falló: " + rr["log_tail"][-200:])
                    v["output"] = rr["output"]; v["sheet"] = rr.get("sheet"); v["time"] = rr.get("time")
                v["ok"] = True
            except Exception as e:  # noqa: BLE001  una variante rota no para el lote
                v["error"] = f"{type(e).__name__}: {e}"[:300]
            variants.append(v)
    manifest = cdir / "batch.json"
    res = {"clips": [c["id"] for c in chosen], "variants": variants, "ok": sum(1 for v in variants if v["ok"]),
           "skipped": skipped, "rendered": render, "manifest": str(manifest)}
    cdir.mkdir(parents=True, exist_ok=True)
    manifest.write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
    return res


# ---------- marcadores de resultado ----------
RESULT_LEAD = 8.0      # segundos antes de la frase de resultado para el fotograma "antes"
RESULT_SETTLE = 1.0    # segundos tras la frase para el "después" (la cámara ya enseña el resultado)
RESULT_CLUSTER = 6.0   # resultados a menos de esto son la misma racha ("that's it… look at that… perfect")
BA_DURATION = 3.0      # el antes/después dura 2–4 s
WORD_STEP = 0.18       # separación entre palabras cuando no hay words.json


def _norm(w: str) -> str:
    return re.sub(r"[^\w']", "", w.lower().replace("’", "'"))


def _word_times(words: list[dict], tokens: list[str], t0: float, t1: float) -> list[float]:
    """`at` de cada token: la palabra real de words.json dentro de la frase (en orden); si no está, el anterior + paso."""
    cands = [w for w in words if t0 - 0.3 <= w["start"] <= t1 + 0.3]
    out: list[float] = []
    k = 0
    for tok in tokens:
        n = _norm(tok)
        hit = next((j for j in range(k, len(cands)) if _norm(cands[j]["text"]) == n), None)
        if hit is not None:
            out.append(round(cands[hit]["start"], 3)); k = hit + 1
        else:
            out.append(round((out[-1] + WORD_STEP) if out else t0, 3))
    return out


def _kinetic_lines(text: str, match: str, lang: str, words: list[dict], t0: float, t1: float, max_chars: int) -> list[list[dict]]:
    clause = _trim_trailing(_clean(_window(_clause(text, match), match), lang).rstrip(".!"), lang)
    lines = _two_lines(clause, MAX_LINE_WORDS, max_chars)
    tokens = [w for line in lines for w in line.split()]
    ats = _word_times(words, tokens, t0, t1)
    first = _norm(match.split()[0]) if match else ""
    accent_done = False
    out: list[list[dict]] = []
    k = 0
    for line in lines:
        row = []
        for w in line.split():
            item = {"text": w, "at": ats[k]}
            if not accent_done and first and _norm(w) == first:
                item["accent"] = True; accent_done = True
            row.append(item); k += 1
        out.append(row)
    return out


def _zone(canvas: tuple[int, int], side: str) -> dict:
    """Posiciones orientativas: el lado libre del hablante en 16:9, la franja superior en vertical."""
    W, H = canvas
    narrow = W < 1400
    if narrow:
        return {"kin": (80, 160), "size": 76, "chars": 22, "draw": (W - 220, 120), "draw_w": 120, "ba": (60, int(H * 0.22), W - 120)}
    x0 = 90 if side == "left" else 1100
    return {"kin": (x0, 200), "size": 76, "chars": 20, "draw": (x0 + 640, 90), "draw_w": 140, "ba": (x0 - 30 if side == "left" else x0 - 60, 180, 820)}


def markers(captions_path: str | Path, lang: str = "en", words_path: str | Path | None = None,
            canvas: tuple[int, int] = (1920, 1080), side: str = "right", lead: float = RESULT_LEAD,
            settle: float = RESULT_SETTLE) -> dict:
    """Marcadores de resultado y de promesa a partir de captions.json: por cada racha de frases de resultado, un
    `before_after` (dos instantes del propio clip: `lead` s antes y `settle` s después), un `draw` check en la
    palabra que lo dice y un `kinetic` con la frase real; por cada promesa, un `kinetic`. Las posiciones son
    orientativas (`side` = lado libre de `frame28 speaker`, o la franja superior en vertical): el director las
    ajusta y comprueba `before_t` con `frame28 frames` (el "antes" debe ser el objeto sin tocar)."""
    caps = load_captions(captions_path)
    words = load_words(words_path) if words_path else []
    total = round(max(c["end"] for c in caps), 3) if caps else 0.0
    moms = [m for m in _moments(caps, lang, []) if m["kind"] in ("result", "promise")]
    by_t: dict[float, dict] = {c["start"]: c for c in caps}
    z = _zone(canvas, side)
    out: list[dict] = []
    seen_prom: set[str] = set()
    results: list[list[dict]] = []
    for m in sorted(moms, key=lambda m: m["t"]):
        if m["kind"] == "promise":
            if m["text"] in seen_prom:
                continue
            seen_prom.add(m["text"])
            c = by_t[m["t"]]
            k = sum(1 for o in out if o["kind"] == "promise") + 1
            lines = _kinetic_lines(m["text"], m["match"], lang, words, c["start"], c["end"], z["chars"])
            at = lines[0][0]["at"]
            out.append({"id": f"prom{k}", "kind": "promise", "t": round(c["start"], 3), "end": round(c["end"], 3),
                        "phrase": m["text"], "match": m["match"],
                        "overlays": [{"type": "kinetic", "id": f"prom{k}-kin", "start": round(max(0.0, at - 0.05), 3),
                                      "end": round(min(total, c["end"] + 0.6), 3), "x": z["kin"][0], "y": z["kin"][1],
                                      "size": z["size"], "reveal": "rise", "lines": lines}]})
            continue
        if results and m["t"] - results[-1][-1]["t"] <= RESULT_CLUSTER:
            results[-1].append(m)
        else:
            results.append([m])
    for k, grp in enumerate(results, 1):
        first, last = grp[0], grp[-1]
        c0, c1 = by_t[first["t"]], by_t[last["t"]]
        lines = _kinetic_lines(first["text"], first["match"], lang, words, c0["start"], c0["end"], z["chars"])
        at = lines[0][0]["at"]
        hit = next((w["at"] for row in lines for w in row if w.get("accent")), at)
        ba_start = round(min(c1["end"] + settle, max(0.0, total - BA_DURATION)), 3)
        ba_end = round(min(total, ba_start + BA_DURATION), 3)
        before_t = round(max(0.0, first["t"] - lead), 3)
        after_t = round(max(0.0, min(total - 0.05, ba_start - 0.05)), 3)
        kin_end = round(max(at + 1.0, min(c0["end"] + 0.6, ba_start)), 3)  # la frase que lo dice, no toda la racha
        ovs = [
            {"type": "kinetic", "id": f"res{k}-kin", "start": round(max(0.0, at - 0.05), 3), "end": kin_end,
             "x": z["kin"][0], "y": z["kin"][1], "size": z["size"], "reveal": "rise", "lines": lines},
            {"type": "draw", "id": f"res{k}-check", "icon": "check", "start": round(max(0.0, hit - 0.05), 3),
             "end": round(min(total, hit + 1.6), 3), "at": round(hit, 3), "x": z["draw"][0], "y": z["draw"][1],
             "w": z["draw_w"], "color": "#ffffff", "duration": 0.5},
        ]
        if ba_end - ba_start >= 1.5:
            ovs.append({"type": "before_after", "id": f"res{k}-ba", "start": ba_start, "end": ba_end,
                        "before_t": before_t, "after_t": after_t, "x": z["ba"][0], "y": z["ba"][1], "w": z["ba"][2],
                        "label_before": "Antes" if lang == "es" else "Before", "label_after": "Después" if lang == "es" else "After"})
        out.append({"id": f"res{k}", "kind": "result", "t": round(first["t"], 3), "end": round(c1["end"], 3),
                    "phrase": first["text"], "match": first["match"],
                    "phrases": [m["text"] for m in grp] if len(grp) > 1 else [first["text"]], "overlays": ovs})
    out.sort(key=lambda m: m["t"])
    return {"captions": str(captions_path), "lang": lang, "canvas": list(canvas), "side": side, "duration": total,
            "results": len(results), "promises": sum(1 for m in out if m["kind"] == "promise"), "markers": out,
            "note": "posiciones orientativas: mueve cada overlay al lado libre de `frame28 speaker` (o a las free_bands del "
                    "reframe) y comprueba before_t/after_t con `frame28 frames` antes de pegarlos en el storyboard"}
