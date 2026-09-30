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


def hooks_for(clip: dict, lang: str, brand: str | None = None) -> list[dict]:
    """Tres ganchos de tipos distintos a partir de los momentos del tramo (plantillas; el agente los afina)."""
    res = next((m for m in clip["moments"] if m["kind"] == "result"), None)
    obj = next((m for m in clip["moments"] if m["kind"] == "objection"), None)
    pro = next((m for m in clip["moments"] if m["kind"] == "promise"), None)
    num = next((m for m in clip["moments"] if m["kind"] == "number"), None)
    es = lang == "es"
    hooks = []
    if obj:
        q = obj["text"].rstrip(".!")
        hooks.append({"type": "objection", "lines": [q[:40], ("Pues no." if es else "Not anymore.")]})
    if pro:
        hooks.append({"type": "promise", "lines": [("Lo único que necesitas" if es else "The only thing you need"), pro["match"].capitalize() if len(pro["match"]) < 22 else ("para empezar hoy" if es else "to start today")]})
    if res:
        hooks.append({"type": "transformation", "lines": [("De cero a esto" if es else "From zero to this"), ("sin práctica" if es else "with zero practice")]})
    if num:
        hooks.append({"type": "number", "lines": [num["match"], (num["text"][:36])]})
    if len(hooks) < 3:
        hooks.append({"type": "curiosity", "lines": [("¿Se puede hacer esto" if es else "Can you actually do this"), ("con tus manos?" if es else "with your own hands?")]})
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
        sb["brand"] = brand
    if cta:
        c = {"type": "cta", "id": "cta", "start": round(max(dur - 5.0, 3.5), 2), "end": dur, "at": round(max(dur - 4.9, 3.6), 2), **cta}
        sb["overlays"].append(c)
    sb["duration"] = dur
    p = d / "storyboard.json"
    p.write_text(json.dumps(sb, indent=1, ensure_ascii=False), encoding="utf-8")
    return {"storyboard": str(p), "duration": dur, "hook": hook}
