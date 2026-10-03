"""Nota de marca del storyboard antes del render (F28-24): comprueba los textos en pantalla contra las reglas de la marca y
devuelve una nota de 0 a 100 con la lista de fallos, cada uno con su arreglo, para que el director los corrija solo.

La «claridad» del estudio de frame28.app puntúa el prompt; esto puntúa el resultado. Las reglas salen de lo que el
montaje ya tiene en disco, sin red: el JSON de marca del CLI (`voice.avoid`, `voice.max_words_per_sentence`), el brief
que el método guarda en `work/brief.md` (Memoria + campaña: «Nunca digas», reglas legales, ganchos prohibidos, glosario,
lo que la campaña tiene que decir y lo que no) y, si se pasa, la Memoria entera en JSON (Context Pack v1).

Qué mira: claims legales y palabras prohibidas en pantalla (errores), ganchos prohibidos, términos del glosario sin su
forma en el idioma del storyboard, frases más largas que el máximo de la voz, cajas con demasiadas palabras, lo que la
campaña tiene que decir y no sale, contraste de texto sobre fondo de color conocido y zonas seguras del móvil. Los
subtítulos son la voz (no se cambian en el storyboard): de ellos solo se avisa si dicen un claim legal."""
from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

PENALTY = {"legal": 25, "avoid": 10, "banned_hook": 15, "accent_on_accent": 10, "voice_claim": 10,
           "glossary": 5, "safe_zone": 5, "must_say": 5, "contrast": 5, "long_sentence": 3, "density": 3}
ERRORS = {"legal", "avoid", "banned_hook", "accent_on_accent"}
DENSITY = {"box": 6, "pointer": 6, "lower_third": 8, "hook": 12, "steps": 8}   # palabras como mucho por overlay


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"\s+", " ", s).strip()


def _pattern(term: str) -> re.Pattern | None:
    t = norm(term)
    if not t:
        return None
    if " " not in t and len(t) >= 6:     # una palabra larga: también sus variantes («garantizado» → «garantizada», «-s»)
        return re.compile(rf"(?<![a-z0-9]){re.escape(t[:-1])}[a-z]{{0,3}}(?![a-z0-9])")
    return re.compile(rf"(?<![a-z0-9]){re.escape(t)}(?![a-z0-9])")


def found(term: str, text: str) -> bool:
    p = _pattern(term)
    return bool(p and p.search(norm(text)))


@dataclass
class Rules:
    avoid: list[str] = field(default_factory=list)
    claims: list[str] = field(default_factory=list)
    banned_hooks: list[str] = field(default_factory=list)
    glossary: dict[str, dict[str, str]] = field(default_factory=dict)
    must_say: list[str] = field(default_factory=list)
    max_words: int | None = None
    sources: list[str] = field(default_factory=list)

    def empty(self) -> bool:
        return not (self.avoid or self.claims or self.banned_hooks or self.glossary or self.must_say or self.max_words)

    def add(self, other: "Rules") -> None:
        for k in ("avoid", "claims", "banned_hooks", "must_say", "sources"):
            cur = getattr(self, k)
            cur.extend(x for x in getattr(other, k) if x and x not in cur)
        for lang, terms in other.glossary.items():
            self.glossary.setdefault(lang, {}).update(terms)
        self.max_words = self.max_words or other.max_words


def rules_from_brand(brand: dict, source: str = "marca") -> Rules:
    v = brand.get("voice") if isinstance(brand.get("voice"), dict) else {}
    r = Rules(avoid=[str(x) for x in v.get("avoid", [])], max_words=v.get("max_words_per_sentence") or None)
    r.sources = [source] if not r.empty() else []
    return r


def rules_from_memoria(m: dict, source: str = "memoria") -> Rules:
    voice, legal, hooks = m.get("voice") or {}, m.get("legal") or {}, m.get("hooks") or {}
    r = Rules(avoid=list(voice.get("avoid", [])), claims=list(legal.get("claims_not_allowed", [])),
              banned_hooks=list(hooks.get("banned", [])), glossary={k: dict(v) for k, v in (m.get("glossary") or {}).items()},
              max_words=voice.get("max_words_per_sentence") or None)
    r.sources = [source] if not r.empty() else []
    return r


def _items(line: str) -> list[str]:
    return [x.strip().strip("«»\"'`") for x in line.split(",") if x.strip()]


def rules_from_brief(text: str, source: str = "brief") -> Rules:
    """Lee el brief en Markdown que sirve el MCP (`frame28_memoria` + `frame28_campana`, guardado en work/brief.md)."""
    r = Rules()
    section = ""
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("## "):
            section = norm(line[3:])
            continue
        if not line.startswith("- "):
            continue
        item = line[2:].strip()
        low = norm(item)
        if section.startswith("voz"):
            if low.startswith("nunca digas:"):
                r.avoid += _items(item.split(":", 1)[1])
            m = re.match(r"frases de (\d+) palabras", low)
            if m:
                r.max_words = int(m.group(1))
        elif section.startswith("reglas legales") and low.startswith("no afirmar:"):
            r.claims += _items(item.split(":", 1)[1])
        elif section.startswith("ganchos prohibidos"):
            r.banned_hooks.append(item)
        elif section.startswith("glosario"):
            if ":" in item:
                lang, terms = item.split(":", 1)
                for pair in terms.split(";"):
                    if "→" in pair:
                        a, b = (x.strip() for x in pair.split("→", 1))
                        if a and b:
                            r.glossary.setdefault(lang.strip(), {})[a] = b
        elif section.startswith("esta campana no dice"):
            r.avoid.append(item)
        elif section.startswith("tiene que decirse"):
            r.must_say.append(item)
    r.sources = [source] if not r.empty() else []
    return r


def screen_texts(sb: dict) -> list[tuple[dict, str, str]]:
    """(overlay, campo, texto) de todo lo que sale escrito en pantalla."""
    out: list[tuple[dict, str, str]] = []

    def add(o, where, t):
        if isinstance(t, str) and t.strip():
            out.append((o, where, t.strip()))

    for o in sb.get("overlays", []):
        t = o.get("type")
        for k in ("title", "subtitle", "text", "label", "caption", "line", "code_label", "discount", "endorsement",
                  "label_before", "label_after", "prefix", "suffix"):
            v = o.get(k)
            add(o, k, v.get("text") if isinstance(v, dict) else v)
        if t in ("kinetic", "card_words"):
            for n, line in enumerate(o.get("lines", [])):
                add(o, f"lines[{n}]", " ".join(w.get("text", "") for w in line if isinstance(w, dict)))
        if t == "hook" and isinstance(o.get("lines"), list):
            add(o, "lines", " ".join(x if isinstance(x, str) else x.get("text", "") for x in o["lines"]))
        for n, it in enumerate(o.get("items", []) or []):
            if isinstance(it, dict):
                add(o, f"items[{n}]", it.get("text") or it.get("label"))
        for n, s in enumerate(o.get("series", []) or []):
            if isinstance(s, dict):
                add(o, f"series[{n}]", s.get("label"))
    return out


def _sentences(text: str) -> list[str]:
    return [s for s in re.split(r"[.!?¡¿…]+", text) if s.strip()]


def _hex_rgb(c: str) -> tuple[float, float, float] | None:
    m = re.fullmatch(r"#?([0-9a-fA-F]{6})", (c or "").strip())
    if not m:
        return None
    v = m.group(1)
    return tuple(int(v[i:i + 2], 16) / 255 for i in (0, 2, 4))  # type: ignore[return-value]


def contrast(a: str, b: str) -> float | None:
    """Contraste WCAG entre dos colores #RRGGBB (1 a 21); None si alguno no es un color fijo."""
    def lum(c):
        rgb = _hex_rgb(c)
        if rgb is None:
            return None
        lin = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in rgb]
        return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]
    la, lb = lum(a), lum(b)
    if la is None or lb is None:
        return None
    hi, lo = max(la, lb), min(la, lb)
    return round((hi + 0.05) / (lo + 0.05), 2)


def check(sb: dict, rules: Rules, brand: dict | None = None, lang: str | None = None) -> dict:
    brand = brand or {}
    lang = (lang or (sb.get("meta") or {}).get("lang") or "").lower() or None
    issues: list[dict] = []

    def issue(rule, o, where, text, msg, fix, oid="captions", otype="caption"):
        issues.append({"rule": rule, "severity": "error" if rule in ERRORS else "aviso", "id": (o or {}).get("id", oid),
                       "type": (o or {}).get("type", otype), "where": where, "text": text, "message": msg, "fix": fix})

    texts = screen_texts(sb)
    for o, where, text in texts:
        for c in rules.claims:
            if found(c, text):
                issue("legal", o, where, text, f"afirma «{c}», que la marca no puede decir (regla legal)",
                      "quita la afirmación o reformúlala sin prometer; las reglas legales mandan sobre todo")
        for w in rules.avoid:
            if found(w, text):
                issue("avoid", o, where, text, f"usa «{w}», que la voz de la marca nunca dice", "cámbialo por una palabra de los pilares de la voz")
        if o.get("type") == "hook":
            for h in rules.banned_hooks:
                if norm(h) and (norm(h) in norm(text) or norm(text) in norm(h)):
                    issue("banned_hook", o, where, text, f"es un gancho prohibido («{h}»)", "usa uno de los ganchos aprobados o de la campaña")
        if lang and lang in rules.glossary:
            for term, said in rules.glossary[lang].items():
                if norm(term) != norm(said) and found(term, text) and not found(said, text):
                    issue("glossary", o, where, text, f"«{term}» en {lang} se dice «{said}» (glosario)", f"escribe «{said}»")
        if rules.max_words:
            for s in _sentences(text):
                n = len(s.split())
                if n > rules.max_words:
                    issue("long_sentence", o, where, text, f"frase de {n} palabras; la voz pide {rules.max_words} como mucho", "pártela o recórtala")
        lim = DENSITY.get(o.get("type", ""))
        if lim and where in ("text", "title", "lines") and len(text.split()) > lim:
            issue("density", o, where, text, f"{len(text.split())} palabras en un {o['type']}; se lee mal por encima de {lim}",
                  "deja una sola idea en pocas palabras")

    for n, c in enumerate(sb.get("captions", []) or []):
        for cl in rules.claims:
            if found(cl, c.get("text", "")):
                issue("voice_claim", None, f"captions[{n}]", c.get("text", ""), f"la voz dice «{cl}», que la marca no puede afirmar",
                      "corta ese tramo (frame28 cut) o díselo al usuario: no se arregla en el storyboard")

    if rules.must_say:
        everything = " ".join(t for _, _, t in texts) + " " + " ".join(c.get("text", "") for c in sb.get("captions", []) or [])
        for m in rules.must_say:
            if norm(m) and norm(m) not in norm(everything):
                issue("must_say", None, "campaña", m, "la campaña pide decir esto y no sale en pantalla ni en la voz",
                      "añádelo en un overlay (cta, box o card) con sus palabras", oid="campaña", otype="campaña")

    accent, ink, paper = brand.get("accent"), brand.get("ink", "#0A0A0A"), brand.get("paper", "#FFFFFF")
    bgs = {"accent": accent, "black": "#000000", "white": "#FFFFFF"}
    for o in sb.get("overlays", []):
        bg, color = bgs.get(o.get("bg", "")), o.get("color")
        if not bg or not color:
            continue
        col = accent if color == "accent" else color
        if accent and o.get("bg") == "accent" and norm(col) == norm(accent):
            issue("accent_on_accent", o, "color", color, "texto en el color de acento sobre fondo de acento: no se lee",
                  f"usa la tinta ({ink}) o el papel ({paper}) de la marca")
            continue
        ratio = contrast(col, bg)
        if ratio is not None and ratio < 4.5:
            issue("contrast", o, "color", color, f"contraste {ratio}:1 sobre {o['bg']} (mínimo 4,5:1)", f"usa la tinta ({ink}) o el papel ({paper})")

    try:
        from .build import platform_warnings
        for w in platform_warnings(sb):
            oid = w.split(" ", 1)[0]
            o = next((x for x in sb.get("overlays", []) if x.get("id") == oid), None)
            issue("safe_zone", o, "posición", "", w, "muévelo hacia el centro del lienzo")
    except Exception:  # noqa: BLE001  (sin lienzo o sin overlays con caja: no hay zonas que mirar)
        pass

    score = max(0, 100 - sum(PENALTY[i["rule"]] for i in issues))
    return {"score": score, "errors": sum(i["severity"] == "error" for i in issues), "issues": issues,
            "rules": {"sources": rules.sources, "avoid": len(rules.avoid), "claims": len(rules.claims), "banned_hooks": len(rules.banned_hooks),
                      "glossary": {k: len(v) for k, v in rules.glossary.items()}, "must_say": len(rules.must_say), "max_words": rules.max_words},
            "lang": lang, "texts": len(texts)}


def find_brief(sb_path: Path) -> Path | None:
    """work/brief.md junto al storyboard o en las carpetas que lo contienen (como resolve_brand con las marcas)."""
    for d in [sb_path.parent, *sb_path.parent.parents][:6]:
        if (d / "brief.md").exists():
            return d / "brief.md"
    return None


def load(sb_path: Path, brief: Path | None = None, memoria: Path | None = None) -> tuple[dict, Rules, dict]:
    """(storyboard, reglas reunidas, marca) desde disco."""
    sb = json.loads(sb_path.read_text(encoding="utf-8-sig"))
    brand: dict = {}
    b = sb.get("brand")
    if isinstance(b, dict):
        brand = b
    elif isinstance(b, str) and b:
        from .build import resolve_brand
        try:
            brand = json.loads(resolve_brand(b, near=sb_path.parent).read_text(encoding="utf-8-sig"))
        except SystemExit:
            brand = {}
    rules = rules_from_brand(brand, f"marca {b}" if isinstance(b, str) else "marca")
    brief = brief or find_brief(sb_path)
    if brief and brief.exists():
        rules.add(rules_from_brief(brief.read_text(encoding="utf-8"), str(brief)))
    if memoria:
        rules.add(rules_from_memoria(json.loads(Path(memoria).read_text(encoding="utf-8-sig")), str(memoria)))
    return sb, rules, brand
