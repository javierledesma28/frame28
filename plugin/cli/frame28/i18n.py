"""Versión en otro idioma del mismo montaje: mismos tiempos, textos traducidos.

`extract` saca todos los textos traducibles del storyboard (overlays y subtítulos) a un JSON plano con claves
estables ("k1.lines.0.1.text", "captions.3.text") y contexto (tipo, instante, límite de longitud orientativo).
El agente traduce los valores. `apply` los vuelve a meter en una copia del storyboard, cambia `meta.lang` y, si
los subtítulos son por palabras (`caption_style`), genera `words.<lang>.json` repartiendo las palabras traducidas
de cada frase sobre el ritmo de las palabras originales (misma pausa donde la había).

`apply` guarda además en `meta.i18n` la huella de los textos de origen; `leftovers` (lo usan `build` y `i18n check`)
avisa de cualquier texto visible que siga igual que en el original: un script que reescribe el storyboard traducido
después de `apply` dejaba rótulos en el idioma de origen y nada lo veía antes del render (F28-129).
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from .captions import load_captions, load_words

# campos con texto visible, por tipo de overlay (el resto: ids, tiempos, rutas, colores)
TEXT_FIELDS = {"title", "subtitle", "text", "label", "caption", "credit", "line", "discount", "code_label",
               "endorsement", "label_before", "label_after"}
LIST_FIELDS = {"lines", "items", "series"}
LIMITS = {"box": 26, "hook": 24, "lower_third": 30, "pointer": 22, "steps": 24, "kinetic": 28, "cta": 40}


def _walk(obj, prefix: str, out: dict, ctx: dict) -> None:
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in TEXT_FIELDS and isinstance(v, str) and v.strip():
                out[f"{prefix}.{k}"] = {"text": v, **ctx}
            elif k in TEXT_FIELDS and isinstance(v, dict) and isinstance(v.get("text"), str):  # card.title = {text, at}
                out[f"{prefix}.{k}.text"] = {"text": v["text"], **ctx}
            elif k in LIST_FIELDS and isinstance(v, list):
                _walk(v, f"{prefix}.{k}", out, ctx)
    elif isinstance(obj, list):
        for i, it in enumerate(obj):
            if isinstance(it, str):  # hook.lines = ["línea 1", "línea 2"]
                if it.strip():
                    out[f"{prefix}.{i}"] = {"text": it, **ctx}
            else:
                _walk(it, f"{prefix}.{i}", out, ctx)


def extract(sb: dict) -> dict:
    """{'lang': ..., 'strings': {clave: {text, type, id, at, max_chars?}}}"""
    strings: dict = {}
    for o in sb.get("overlays", []):
        ctx = {"type": o["type"], "id": o["id"], "at": o.get("at", o.get("start"))}
        if o["type"] in LIMITS:
            ctx["max_chars"] = LIMITS[o["type"]]
        _walk(o, o["id"], strings, ctx)
    for i, c in enumerate(sb.get("captions", [])):
        strings[f"captions.{i}.text"] = {"text": c["text"], "type": "caption", "id": f"captions.{i}", "at": c["start"]}
    return {"lang": sb.get("meta", {}).get("lang", ""), "count": len(strings), "strings": strings}


def _set_path(root, path: list[str], value: str) -> None:
    cur = root
    for k in path[:-1]:
        cur = cur[int(k)] if isinstance(cur, list) else cur[k]
    last = path[-1]
    if isinstance(cur, list):
        cur[int(last)] = value
    elif isinstance(cur.get(last), dict) and "text" in cur[last]:
        cur[last]["text"] = value
    else:
        cur[last] = value


def apply(sb: dict, translations: dict, lang: str) -> tuple[dict, list[str]]:
    """Devuelve (storyboard traducido, avisos). `translations` = {clave: texto} o el JSON de extract con textos cambiados."""
    tr = translations.get("strings", translations)
    tr = {k: (v["text"] if isinstance(v, dict) else v) for k, v in tr.items()}
    out = json.loads(json.dumps(sb))
    by_id = {o["id"]: o for o in out.get("overlays", [])}
    warns: list[str] = []
    for key, val in tr.items():
        if not isinstance(val, str):
            continue
        parts = key.split(".")
        try:
            if parts[0] == "captions":
                if not out.get("captions"):
                    continue  # subtítulos por palabras: estas frases se usan en retime_words, no van al storyboard
                out["captions"][int(parts[1])]["text"] = val
            else:
                o = by_id[parts[0]]
                _set_path(o, parts[1:], val)
                lim = LIMITS.get(o["type"])
                if lim and len(val) > lim * 1.35:
                    warns.append(f"{key}: {len(val)} caracteres, orientativo {lim} para {o['type']} ('{val[:30]}…')")
        except (KeyError, IndexError, ValueError, TypeError):
            warns.append(f"{key}: no existe en el storyboard, ignorada")
    src_strings = {k: v["text"] for k, v in extract(sb)["strings"].items()}
    keep = sorted(k for k, v in tr.items() if isinstance(v, str) and k in src_strings and _norm(v) == _norm(src_strings[k]))
    meta = out.setdefault("meta", {})
    meta["i18n"] = {"from": sb.get("meta", {}).get("lang", ""), "source": src_strings, "keep": keep}
    meta["lang"] = lang
    return out, warns


def _norm(text: str) -> str:
    return " ".join(str(text).split()).casefold()


WORD_RE = re.compile(r"[^\W\d_]{3,}")


def _needs_translation(text: str) -> bool:
    """Lo que no hace falta traducir: cifras y símbolos, y nombres propios o marcas cortas (todas las palabras con
    mayúscula inicial, hasta tres, sin estar entero en mayúsculas: «Frame28», «Sailrite Ultrafeed»)."""
    words = WORD_RE.findall(text)
    if not words:
        return False
    if text.isupper():
        return True
    return not (len(words) <= 3 and all(w[0].isupper() for w in words))


def leftovers(sb: dict, show: int = 8) -> list[str]:
    """Avisos de textos visibles que siguen en el idioma de origen en un storyboard traducido con `i18n apply`.
    No avisa de lo que el traductor dejó igual a propósito (`meta.i18n.keep`) ni de cifras, marcas y nombres."""
    info = (sb.get("meta") or {}).get("i18n")
    if not isinstance(info, dict) or not isinstance(info.get("source"), dict):
        return []
    src, keep = info["source"], set(info.get("keep") or [])
    same = [(k, v["text"]) for k, v in extract(sb)["strings"].items()
            if k not in keep and k in src and _norm(v["text"]) == _norm(src[k]) and _needs_translation(v["text"])]
    lang = (sb.get("meta") or {}).get("lang", "")
    out = [f"{k}: sigue en el idioma original ('{txt[:40]}'); tradúcelo a '{lang}' o, si va así a propósito, añade la clave a meta.i18n.keep"
           for k, txt in same[:show]]
    if len(same) > show:
        out.append(f"y {len(same) - show} textos más sin traducir")
    return out


def _tokens(text: str) -> list[str]:
    return [t for t in re.split(r"\s+", text.strip()) if t]


MIN_WORD_S = 0.12  # menos de esto no se lee: si la frase traducida no cabe, se recorta y se avisa


def retime_words(words: list[dict], captions_src: list[dict], captions_tr: list[str], warns: list[str] | None = None) -> list[dict]:
    """Palabras traducidas con tiempos: para cada frase original [start, end] con sus palabras, la frase traducida
    se reparte sobre los inicios de las palabras originales (misma cadencia, mismas pausas)."""
    out: list[dict] = []
    for i, (c, tr_text) in enumerate(zip(captions_src, captions_tr)):
        s, e = float(c["start"]), float(c["end"])
        orig = [w for w in words if s - 0.05 <= float(w["start"]) < e + 0.05]
        toks = _tokens(tr_text)
        if not toks:
            continue
        cap = max(1, int((e - s) / MIN_WORD_S))
        if len(toks) > cap:
            if warns is not None:
                warns.append(f"captions.{i}: {len(toks)} palabras en {e - s:.2f} s (caben {cap}); frase residual del corte o traducción larga: se recorta a '{' '.join(toks[:cap])}'")
            toks = toks[:cap]
        if not orig:
            step = (e - s) / len(toks)
            for j, t in enumerate(toks):
                out.append({"text": t, "start": round(s + j * step, 3), "end": round(s + (j + 1) * step, 3), "prob": 1.0})
            continue
        n, m = len(orig), len(toks)
        starts = []
        for j in range(m):
            idx = min(n - 1, int(j * n / m))
            base = float(orig[idx]["start"])
            # varias palabras traducidas sobre la misma original: repartir dentro de su duración
            same = [jj for jj in range(m) if min(n - 1, int(jj * n / m)) == idx]
            k = same.index(j); span = float(orig[idx]["end"]) - base
            starts.append(base + span * k / max(1, len(same)))
        for j, t in enumerate(toks):
            st = starts[j]; en = starts[j + 1] if j + 1 < m else max(float(orig[-1]["end"]), st + 0.15)
            out.append({"text": t, "start": round(st, 3), "end": round(max(en, st + 0.08), 3), "prob": 1.0})
    return out


def translate_project(storyboard_path: str | Path, strings_path: str | Path, lang: str, out_path: str | Path | None = None,
                      words_path: str | Path | None = None, captions_src_path: str | Path | None = None) -> dict:
    """Aplica las traducciones y, con caption_style por palabras, genera words.<lang>.json junto al storyboard."""
    sbp = Path(storyboard_path); sb = json.loads(sbp.read_text(encoding="utf-8-sig"))
    tr = json.loads(Path(strings_path).read_text(encoding="utf-8-sig"))
    new, warns = apply(sb, tr, lang)
    out = Path(out_path) if out_path else sbp.with_name(f"{sbp.stem}.{lang}.json")
    res = {"storyboard": str(out), "lang": lang, "translated": len(tr.get("strings", tr)), "warnings": warns}
    cs = new.get("caption_style")
    if cs and cs.get("preset") in ("pages", "karaoke"):
        wp = Path(words_path) if words_path else sbp.parent / cs.get("words", "words.json")
        cp = Path(captions_src_path) if captions_src_path else sbp.parent / "captions.json"
        if not wp.exists() or not cp.exists():
            warns.append(f"subtítulos por palabras: faltan {wp.name} o {cp.name}; deja caption_style.words apuntando al original")
        else:
            words = load_words(wp, merge_symbols=False); caps = load_captions(cp)
            strings = tr.get("strings", tr)
            caps_tr = []
            for i, c in enumerate(caps):
                v = strings.get(f"captions.{i}.text")
                caps_tr.append(v["text"] if isinstance(v, dict) else (v if isinstance(v, str) else c["text"]))
            if not any(f"captions.{i}.text" in strings for i in range(len(caps))):
                warns.append("no hay traducciones 'captions.N.text' para regenerar las palabras: extrae con --captions")
            nw = retime_words(words, caps, caps_tr, warns)
            wout = sbp.parent / f"{wp.stem}.{lang}.json"
            wout.write_text(json.dumps(nw, indent=1, ensure_ascii=False), encoding="utf-8")
            new["caption_style"]["words"] = wout.name
            res["words"] = str(wout); res["words_count"] = len(nw)
    warns.extend(density_warnings(sb.get("captions") or [], new.get("captions") or []))
    out.write_text(json.dumps(new, indent=1, ensure_ascii=False), encoding="utf-8")
    return res


DENSE_CPS = 21.0     # por encima no da tiempo a leer; la referencia de subtitulado es 17


def density_warnings(src: list[dict], tr: list[dict], limit: float = DENSE_CPS, show: int = 6) -> list[str]:
    """Subtítulos por frase traducidos que no da tiempo a leer: la traducción suele ser más larga que el original y la
    frase dura lo mismo. Avisa de las que pasan de `limit` caracteres por segundo, con la densidad del original."""
    def cps(c):
        d = float(c["end"]) - float(c["start"])
        return len(c["text"].replace(" ", "")) / d if d > 0 else 0.0

    dense = [(i, cps(t), cps(src[i]) if i < len(src) else 0.0) for i, t in enumerate(tr) if t.get("text") and cps(t) > limit]
    out = [f"captions.{i}: {c:.0f} caracteres/s (original {o:.0f}); condensa la frase, dura {float(tr[i]['end']) - float(tr[i]['start']):.1f} s"
           for i, c, o in dense[:show]]
    if len(dense) > show:
        out.append(f"y {len(dense) - show} subtítulos más por encima de {limit:.0f} caracteres/s")
    return out


def extract_with_captions(sb: dict, captions_path: str | Path | None) -> dict:
    """Como extract, y si el storyboard usa subtítulos por palabras añade las frases de captions.json para traducirlas."""
    r = extract(sb)
    cs = sb.get("caption_style")
    if cs and cs.get("preset") in ("pages", "karaoke") and captions_path and Path(captions_path).exists():
        caps = load_captions(captions_path)
        wp = Path(captions_path).parent / cs.get("words", "words.json")
        words = load_words(wp) if wp.exists() else []
        for i, c in enumerate(caps):
            s, e = float(c["start"]), float(c["end"])
            inside = [w["text"] for w in words if s - 0.05 <= float(w["start"]) < e + 0.05]
            entry = {"text": c["text"], "type": "caption", "id": f"captions.{i}", "at": s, "duration": round(e - s, 2),
                     "max_words": max(1, int((e - s) / MIN_WORD_S))}
            if words and not inside:
                entry["note"] = "frase residual del corte: no se oye ninguna palabra; déjala vacía"
                entry["visible"] = ""
            elif inside and len(inside) < len(_tokens(c["text"])) * 0.6:
                entry["note"] = f"frase residual del corte: solo se oye '{' '.join(inside)}'; traduce solo eso"
                entry["visible"] = " ".join(inside)
            r["strings"][f"captions.{i}.text"] = entry
        r["count"] = len(r["strings"])
    return r
