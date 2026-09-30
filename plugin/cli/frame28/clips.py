"""Fábrica de shorts: de un vídeo largo, los tramos de 15–45 s con más "momentos" de venta, tres ganchos por tramo,
y el recorte listo (clip, voz, palabras y subtítulos remapeados) con un storyboard de partida que ya construye.

Momentos que puntúan (ES/EN): resultado ("that's it", "turned out", "queda", "mira"), promesa ("beginner",
"easy", "cualquiera", "fácil"), objeción ("isn't it", "what if", "¿y si"), cifras y menciones del producto.
Un tramo empieza y termina en frase (captions.json), no a mitad de palabra.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

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
    caps = json.loads(Path(captions_path).read_text(encoding="utf-8"))
    caps = [c for c in caps if c.get("text", "").strip()]
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


def _two_lines(text: str) -> list[str]:
    """Parte en dos líneas de <= 5 palabras / 26 caracteres en el punto más natural; recorta si no cabe."""
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


def hooks_for(clip: dict, lang: str, brand: str | None = None) -> list[dict]:
    """Tres ganchos de tipos distintos con las **palabras reales** del hablante: la cláusula donde ocurre el momento
    (resultado, objeción, promesa, cifra), sin relleno inicial, en dos líneas. Cada gancho lleva `quote` y `t`."""
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
             brand: str | dict | None = None, cta: dict | None = None, hook_index: int = 0, video_name: str = "clip.mp4") -> dict:
    """Storyboard de partida para el short: gancho, subtítulos por palabras, CTA al final. Construye tal cual."""
    d = Path(clip_dir)
    words = json.loads((d / "words.json").read_text(encoding="utf-8")) if (d / "words.json").exists() else []
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
    p = d / "storyboard.json"
    p.write_text(json.dumps(sb, indent=1, ensure_ascii=False), encoding="utf-8")
    return {"storyboard": str(p), "duration": dur, "hook": hook}
