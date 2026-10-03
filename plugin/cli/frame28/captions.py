"""Subtítulos: paginado por palabras (estilo TikTok/karaoke) y exportación SRT/VTT con reglas de legibilidad.

Trabaja siempre sobre `words.json` (tiempos por palabra). Las reglas son las habituales de subtitulado:
≤ 42 caracteres por línea, 1–7 s por cue, ≤ 17 caracteres por segundo, sin solapes, corte en signos de
puntuación o en pausas largas. `pages()` es lo que usa `frame28 build` para los presets `pages` y `karaoke`.
"""
from __future__ import annotations

import json
from pathlib import Path

END_PUNCT = ".!?…"
SOFT_PUNCT = ",;:"


def default_canvas(width: int, height: int) -> tuple[int, int]:
    """Lienzo por defecto según el formato del clip: vertical → 1080×1920, cuadrado → 1080×1080, resto → 1920×1080."""
    if width <= 0 or height <= 0:
        return (1920, 1080)
    r = width / height
    if r < 0.85:
        return (1080, 1920)
    if r < 1.2:
        return (1080, 1080)
    return (1920, 1080)


def parse_canvas(spec: str | None, width: int, height: int) -> tuple[int, int]:
    """'1080x1920' → (1080, 1920); None o 'auto' → por formato del clip."""
    if not spec or spec.lower() == "auto":
        return default_canvas(width, height)
    w, h = spec.lower().replace("×", "x").split("x")
    return (int(w), int(h))


class TranscriptFormatError(ValueError):
    """words.json o captions.json en un formato que Frame28 no entiende (el CLI lo muestra como error corto, sin traza)."""


def _seconds(d: dict, key: str) -> float | None:
    """Tiempo en segundos: `start`/`end` (s) o `startMs`/`endMs` (ms, formato de transcript de HyperFrames)."""
    if d.get(key) is not None:
        return float(d[key])
    ms = d.get(key + "Ms")
    return float(ms) / 1000.0 if ms is not None else None


def _read_json(path: str | Path):
    p = Path(path)
    try:
        return json.loads(p.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as ex:
        raise TranscriptFormatError(f"{p}: JSON inválido ({ex.msg}, línea {ex.lineno})") from ex


def normalize_words(data, merge_symbols: bool = True, source: str = "words.json") -> list[dict]:
    """Único cargador de palabras del CLI. Devuelve `text`, `start`, `end` en segundos (más las claves extra, p. ej. `prob`),
    sin entradas vacías. Acepta: lista de palabras; dict con `words` o con `segments[].words` (faster-whisper, WhisperX);
    texto en `text` o `word`; tiempos en segundos (`start`/`end`) o en milisegundos (`startMs`/`endMs`, HyperFrames).
    Con `merge_symbols`, "30" + "%" (o "€", "$") se pegan en una sola palabra, como los separa el ASR."""
    ws = data
    if isinstance(data, dict):
        if isinstance(data.get("words"), list):
            ws = data["words"]
        elif isinstance(data.get("segments"), list):
            ws = [w for s in data["segments"] for w in (s.get("words") or [])]
        else:
            raise TranscriptFormatError(f"{source}: no es una lista de palabras ni tiene 'words' o 'segments'")
    if not isinstance(ws, list):
        raise TranscriptFormatError(f"{source}: se esperaba una lista de palabras")
    out: list[dict] = []
    for i, w in enumerate(ws):
        if not isinstance(w, dict):
            raise TranscriptFormatError(f"{source}: la entrada {i} no es un objeto con text/start/end")
        t = (w.get("text") or w.get("word") or "").strip()
        if not t:
            continue
        s, e = _seconds(w, "start"), _seconds(w, "end")
        if s is None or e is None:
            raise TranscriptFormatError(f"{source}: la palabra {i} ({t!r}) no tiene tiempos start/end ni startMs/endMs; regenera con `frame28 transcribe`")
        if merge_symbols and out and t[0] in "%€$" and len(t) <= 2:
            out[-1]["text"] += t; out[-1]["end"] = e; continue
        nw = {k: v for k, v in w.items() if k not in ("word", "startMs", "endMs")}
        nw.update({"text": t, "start": s, "end": e})
        out.append(nw)
    return out


def load_words(path: str | Path, merge_symbols: bool = True) -> list[dict]:
    """words.json normalizado (ver `normalize_words`). Todo el CLI lee las palabras por aquí, nunca con json.loads a pelo."""
    return normalize_words(_read_json(path), merge_symbols, source=Path(path).name)


def load_captions(path: str | Path) -> list[dict]:
    """captions.json normalizado: frases con `text`, `start`, `end` en segundos (acepta dict con `captions` o `segments`,
    y tiempos en milisegundos). Sin frases vacías."""
    p = Path(path); d = _read_json(p)
    caps = d
    if isinstance(d, dict):
        caps = d.get("captions") if isinstance(d.get("captions"), list) else d.get("segments")
        if not isinstance(caps, list):
            raise TranscriptFormatError(f"{p.name}: no es una lista de frases ni tiene 'captions' o 'segments'")
    out: list[dict] = []
    for i, c in enumerate(caps):
        if not isinstance(c, dict):
            raise TranscriptFormatError(f"{p.name}: la entrada {i} no es un objeto con text/start/end")
        t = (c.get("text") or "").strip()
        if not t:
            continue
        s, e = _seconds(c, "start"), _seconds(c, "end")
        if s is None or e is None:
            raise TranscriptFormatError(f"{p.name}: la frase {i} ({t[:30]!r}) no tiene tiempos start/end; regenera con `frame28 transcribe`")
        nc = {k: v for k, v in c.items() if k not in ("startMs", "endMs")}
        nc.update({"text": t, "start": s, "end": e})
        out.append(nc)
    return out


def pages(words: list[dict], max_words: int = 4, max_gap: float = 0.6, hold: float = 0.8, max_chars: int = 22) -> list[dict]:
    """Agrupa palabras en páginas cortas: corta en puntuación final, en pausas > `max_gap` s, al llegar a
    `max_words` o a `max_chars`. Cada página dura desde su primera palabra hasta la siguiente página (máx. `hold` s
    tras la última palabra)."""
    out: list[dict] = []
    cur: list[dict] = []

    def flush():
        if cur:
            out.append({"start": cur[0]["start"], "end": cur[-1]["end"], "words": list(cur)})
            cur.clear()

    for w in words:
        if cur:
            gap = w["start"] - cur[-1]["end"]
            chars = sum(len(x["text"]) for x in cur) + len(cur) - 1 + 1 + len(w["text"])
            if gap > max_gap or len(cur) >= max_words or chars > max_chars or cur[-1]["text"][-1:] in END_PUNCT:
                flush()
        cur.append(w)
    flush()
    for k, p in enumerate(out):
        nxt = out[k + 1]["start"] if k + 1 < len(out) else p["end"] + hold
        p["end"] = round(min(p["end"] + hold, nxt), 3)
        p["start"] = round(p["start"], 3)
        p["text"] = " ".join(w["text"] for w in p["words"])
    return out


def cues(words: list[dict], max_chars: int = 42, max_lines: int = 2, max_dur: float = 7.0, min_dur: float = 1.0,
         max_gap: float = 0.7, max_cps: float = 17.0) -> list[dict]:
    """Cues de subtítulo legibles a partir de palabras: hasta `max_lines` líneas de `max_chars`, 1–7 s, corte en
    puntuación o pausa. Devuelve [{start, end, lines: [..], text, cps}]."""
    out: list[dict] = []
    cur: list[dict] = []
    limit = max_chars * max_lines

    def text_of(ws):
        return " ".join(w["text"] for w in ws)

    def flush():
        if not cur:
            return
        t = text_of(cur)
        out.append({"start": cur[0]["start"], "end": cur[-1]["end"], "text": t})
        cur.clear()

    for w in words:
        if cur:
            gap = w["start"] - cur[-1]["end"]
            too_long = len(text_of(cur + [w])) > limit
            too_slow = (w["end"] - cur[0]["start"]) > max_dur
            ends = cur[-1]["text"][-1:] in END_PUNCT and len(text_of(cur)) >= max_chars * 0.5
            if gap > max_gap or too_long or too_slow or ends:
                flush()
        cur.append(w)
    flush()
    # duración mínima y sin solapes; luego repartir en líneas equilibradas
    for k, c in enumerate(out):
        nxt = out[k + 1]["start"] if k + 1 < len(out) else None
        end = max(c["end"], c["start"] + min_dur)
        if nxt is not None:
            end = min(end, nxt - 0.04)
        c["end"] = round(max(end, c["start"] + 0.3), 3); c["start"] = round(c["start"], 3)
        c["lines"] = _split_lines(c["text"], max_chars, max_lines)
        dur = c["end"] - c["start"]
        c["cps"] = round(len(c["text"].replace(" ", "")) / dur, 1) if dur > 0 else 0.0
        c["warnings"] = ([f"cps {c['cps']} > {max_cps}"] if c["cps"] > max_cps else []) + \
                        ([f"línea de {max(map(len, c['lines']))} > {max_chars}"] if max(map(len, c["lines"])) > max_chars else [])
    return out


# Palabras por las que se puede partir una frase larga sin romper una idea (la parte nueva empieza por ellas).
JOINTS = {
    "en": {"and", "so", "because", "where", "that", "once", "when", "until", "as", "to", "with", "into", "but", "or", "which", "while", "if", "anything"},
    "es": {"y", "e", "pero", "porque", "que", "cuando", "donde", "para", "aunque", "mientras", "hasta", "como", "si", "o", "ni", "así", "con"},
}


def _text(ws: list[dict]) -> str:
    return " ".join(w["text"].strip() for w in ws)


def sentences(words: list[dict], max_gap: float = 1.5) -> list[list[dict]]:
    """Palabras agrupadas por frase completa: corte en `. ! ? …` o en una pausa de más de `max_gap` s (transcripciones
    sin puntuación). Es la unidad con la que se eligen tramos y se buscan momentos; los subtítulos la parten después."""
    out: list[list[dict]] = []
    cur: list[dict] = []
    for w in words:
        if cur and w["start"] - cur[-1]["end"] > max_gap:
            out.append(cur); cur = []
        cur.append(w)
        if w["text"].strip()[-1:] in END_PUNCT:
            out.append(cur); cur = []
    if cur:
        out.append(cur)
    return out


def _split_clause(ws: list[dict], max_chars: int, joints: set[str]) -> list[list[dict]]:
    """Parte una frase larga por la coma o la conjunción más cercana al centro; nunca deja trozos de una o dos palabras."""
    text = _text(ws)
    if len(text) <= max_chars or len(ws) < 6:
        return [ws]
    best = None
    for i in range(3, len(ws) - 2):
        comma = ws[i - 1]["text"].strip()[-1:] in SOFT_PUNCT
        if not comma and ws[i]["text"].strip(" .,;:!?¿¡").lower() not in joints:
            continue
        a = len(_text(ws[:i]))
        score = abs(a - (len(text) - a - 1)) - (12 if comma else 0)
        if best is None or score < best[0]:
            best = (score, i)
    i = best[1] if best else len(ws) // 2
    return _split_clause(ws[:i], max_chars, joints) + _split_clause(ws[i:], max_chars, joints)


def phrase_captions(words: list[dict], max_chars: int = 84, lang: str = "en", min_dur: float = 1.0) -> list[dict]:
    """Subtítulos por frase a partir de las palabras: una entrada por frase completa y, si no cabe en dos líneas
    (`max_chars`), partida por comas y conjunciones. Cada entrada lleva `sent` (índice de su frase) para que
    `clips plan` y `clips markers` trabajen con frases enteras. Los segmentos de Whisper cortan cada ~4,5 s, a mitad
    de frase cuando la transcripción trae pocas comas: no sirven ni para subtitular ni para traducir."""
    joints = JOINTS.get(lang, set()) | (JOINTS["en"] if lang != "en" else set())
    out: list[dict] = []
    for n, sent in enumerate(sentences(words)):
        for part in _split_clause(sent, max_chars, joints):
            out.append({"start": round(part[0]["start"], 3), "end": round(part[-1]["end"], 3), "text": _text(part), "sent": n})
    for k, c in enumerate(out):     # duración mínima cuando hay sitio, y sin solapes
        nxt = out[k + 1]["start"] if k + 1 < len(out) else None
        end = max(c["end"], c["start"] + min_dur)
        c["end"] = round(min(end, nxt - 0.04) if nxt is not None else end, 3)
        c["end"] = max(c["end"], round(c["start"] + 0.3, 3))
    return out


def group_sentences(caps: list[dict]) -> list[dict]:
    """Frases completas a partir de entradas de captions.json: junta las que comparten `sent` y, si no lo traen
    (transcripciones antiguas o segmentos de Whisper), las consecutivas hasta la puntuación final."""
    out: list[dict] = []
    cur: dict | None = None
    for c in caps:
        same = cur is not None and (c.get("sent") == cur.get("sent") if "sent" in c and "sent" in cur
                                    else cur["text"].strip()[-1:] not in END_PUNCT)
        if same:
            cur["end"] = c["end"]; cur["text"] = cur["text"].rstrip() + " " + c["text"].strip()
        else:
            if cur is not None:
                out.append(cur)
            cur = {**c, "text": c["text"].strip()}
    if cur is not None:
        out.append(cur)
    return out


def caption_cues(caps: list[dict], max_chars: int = 42, max_lines: int = 2, max_cps: float = 17.0) -> list[dict]:
    """Cues SRT/VTT a partir de subtítulos por frase ya decididos (los `captions` de un storyboard, traducido o no):
    mismos tiempos, líneas equilibradas y los avisos de legibilidad de `cues()`."""
    out = []
    for c in caps:
        text = (c.get("text") or "").strip()
        if not text:
            continue
        lines = _split_lines(text, max_chars, max_lines)
        dur = float(c["end"]) - float(c["start"])
        cps = round(len(text.replace(" ", "")) / dur, 1) if dur > 0 else 0.0
        warns = ([f"cps {cps} > {max_cps}"] if cps > max_cps else []) + \
                ([f"línea de {max(map(len, lines))} > {max_chars}"] if max(map(len, lines)) > max_chars else [])
        out.append({"start": round(float(c["start"]), 3), "end": round(float(c["end"]), 3), "text": text, "lines": lines,
                    "cps": cps, "warnings": warns})
    return out


def _split_lines(text: str, max_chars: int, max_lines: int) -> list[str]:
    if len(text) <= max_chars:
        return [text]
    words = text.split()
    # dos líneas: buscar el corte más equilibrado, preferiblemente tras una coma
    best = None
    for i in range(1, len(words)):
        a, b = " ".join(words[:i]), " ".join(words[i:])
        if len(a) > max_chars or len(b) > max_chars * (max_lines - 1):
            continue
        score = abs(len(a) - len(b)) - (12 if a[-1:] in SOFT_PUNCT + END_PUNCT else 0)
        if best is None or score < best[0]:
            best = (score, a, b)
    if best is None:
        return [text]
    return [best[1]] + (_split_lines(best[2], max_chars, max_lines - 1) if max_lines > 2 else [best[2]])


def _ts(sec: float, sep: str = ",") -> str:
    h = int(sec // 3600); m = int(sec % 3600 // 60); s = sec % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}".replace(".", sep)


def write_srt(cs: list[dict], path: str | Path) -> Path:
    p = Path(path)
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        for i, c in enumerate(cs, 1):
            f.write(f"{i}\n{_ts(c['start'])} --> {_ts(c['end'])}\n" + "\n".join(c["lines"]) + "\n\n")
    return p


def write_vtt(cs: list[dict], path: str | Path) -> Path:
    p = Path(path)
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write("WEBVTT\n\n")
        for i, c in enumerate(cs, 1):
            f.write(f"{i}\n{_ts(c['start'], '.')} --> {_ts(c['end'], '.')}\n" + "\n".join(c["lines"]) + "\n\n")
    return p


def export(words_path: str | Path, out_path: str | Path, **rules) -> dict:
    """`frame28 captions export`: words.json → .srt o .vtt (por la extensión) con las reglas dadas. También acepta un
    storyboard: exporta sus subtítulos por frase tal cual (es la única fuente en una versión traducida, que no tiene
    words.json propio) o, si son por palabras, sigue `caption_style.words`."""
    src = Path(words_path)
    data = _read_json(src)
    ws: list[dict] = []
    source = "words"
    if isinstance(data, dict) and "overlays" in data:
        style = data.get("caption_style") or {}
        if style.get("words"):
            ws = load_words(src.parent / style["words"])
            cs = cues(ws, **rules)
        else:
            source = "storyboard"
            cs = caption_cues(data.get("captions") or [], **{k: v for k, v in rules.items() if k in ("max_chars", "max_lines", "max_cps")})
    else:
        ws = normalize_words(data, source=src.name)
        cs = cues(ws, **rules)
    out = Path(out_path)
    (write_vtt if out.suffix.lower() == ".vtt" else write_srt)(cs, out)
    warns = [f"cue {k + 1} ({c['start']}s): {'; '.join(c['warnings'])}" for k, c in enumerate(cs) if c["warnings"]]
    cps = [c["cps"] for c in cs]
    return {"output": str(out), "cues": len(cs), "words": len(ws), "source": source,
            "max_cps": max(cps, default=0.0), "mean_cps": round(sum(cps) / len(cps), 1) if cps else 0.0, "warnings": warns}
