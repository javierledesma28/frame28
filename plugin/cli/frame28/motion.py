"""Movimiento con criterio: tokens de la marca y anclas a la voz (F28-339).

Dos piezas que usa el generador:

- **Tokens de movimiento** (`motion_tokens`): duraciones y curvas de las entradas y salidas salen de la marca
  (`"motion"` en `brands/*.json`), no de números sueltos en `build.py`. Regla de la serie de movimiento: entradas
  rápidas (0,1–0,4 s) ancladas a la palabra y salidas lentas (0,7–1,4 s) con desenfoque o fundido. Una marca sin
  `"motion"` usa `MOTION_DEFAULTS`; los tokens antiguos del brand kit (`standard_ms`, `slow_ms`) dan la entrada y el
  antetítulo si la marca no trae los nuevos.
- **Anclas a la voz** (`resolve_storyboard`): en cualquier `start`, `end`, `at`, `matte_start`, `matte_end` y en
  `words_at` se puede escribir `"word:<palabra>"` (o `"word:<palabra>#n"`, la enésima vez que se dice) y el tiempo sale
  de `words.json`; `behind.words_at: "auto"` busca la frase entera en la voz. Se resuelven antes de validar, con
  `ANCHOR_LEAD_S` de adelanto en las entradas. Una palabra que no se dice o que se dice varias veces sin `#n` es un
  error con los candidatos: nunca un tiempo inventado. Si el storyboard trae `source.audio`, los inicios de palabra se
  pegan antes al arranque real de la voz (`snap_to_voice`): Whisper no deja huecos entre palabras y, tras una pausa, pone
  el inicio de la siguiente dentro de la pausa (la palabra entraría antes de decirse) o unas décimas tarde.
"""
from __future__ import annotations

import copy
import difflib
import re
import unicodedata
import wave
from pathlib import Path

ANCHOR_LEAD_S = 0.04     # la entrada empieza un poco antes de la palabra: el ojo la recibe a la vez que el oído
KICKER_LEAD_S = 0.5      # antetítulo con "at": "auto": medio segundo antes de la primera palabra grande
AUTO_WINDOW_S = 1.0      # words_at "auto" busca la frase desde 1 s antes del start del overlay hasta su end
HOLD_MIN_S = 1.5         # behind: la frase completa tiene que quedarse quieta al menos esto antes de salir
BEHIND_MIN_GAP_S = 20.0  # método: un behind cada ~20 s como mucho
VOICE_DB = -36.0         # voz frente a silencio en voice.wav (prep la deja a -14 LUFS; las pausas quedan por debajo de -40)
ONSET_PAUSE_S = 0.2      # un silencio así separa palabras; los más cortos son el cierre de una consonante (la t, la p)
ONSET_BACK_S = 0.3       # lo más que se adelanta un inicio que Whisper puso dentro de la voz
# Los mismos nombres que la Memoria y la campaña de frame28.app (memoria.py, F28-347): el director copia ahí lo que
# diga el brief en «## Movimiento».
STYLES = ("sober", "editorial", "promotional")
EFFECTS = ("behind", "cards_3d", "camera", "transitions", "live_photos", "brand_open")

MOTION_DEFAULTS = {
    "enter_ms": 200,          # entrada de cada palabra
    "exit_ms": 1200,          # salida (desenfoque o fundido)
    "exit_blur_px": 28,       # desenfoque al final de la salida
    "ease_in": "power1.out",  # curva de las entradas
    "ease_out": "sine.inOut", # curva de las salidas
    "exit_stagger_ms": 300,   # el antetítulo sale esto antes que la frase
    "kicker_ms": 500,         # fundido de entrada del antetítulo
    "word_stagger_ms": 300,   # palabras sin ancla: una cada esto desde `at`
    "char_stagger_ms": 20,    # entrada por letras (chars)
}
DERIVED = {"enter_ms": "standard_ms", "kicker_ms": "slow_ms"}   # tokens del brand kit que ya existían
RANGES_MS = {"enter_ms": (40, 800), "exit_ms": (150, 3000), "exit_blur_px": (0, 120), "exit_stagger_ms": (0, 1500),
             "kicker_ms": (40, 2000), "word_stagger_ms": (0, 2000), "char_stagger_ms": (0, 200),
             "standard_ms": (0, 3000), "fast_ms": (0, 3000), "slow_ms": (0, 3000)}
# las curvas acaban dentro del JS generado: solo nombres de GSAP con su parámetro numérico
EASE_RE = re.compile(r"^(none|linear|(power[0-4]|sine|expo|circ|back|elastic|bounce)(\.(in|out|inOut))?(\(\s*[\d.]+(\s*,\s*[\d.]+)?\s*\))?)$")
TIME_KEYS = ("start", "end", "at", "matte_start", "matte_end")
ANCHOR_RE = re.compile(r"^word:\s*(.+?)\s*(?:#(\d+))?$")


# ── tokens ────────────────────────────────────────────────────────────────────────────────────────────────────────────
def motion_errors(motion) -> list[str]:
    """Formato de `marca.motion`: números en su rango y curvas de GSAP (van al JS generado)."""
    if motion is None:
        return []
    if not isinstance(motion, dict):
        return ["marca.motion: tiene que ser un objeto {enter_ms, exit_ms, exit_blur_px, ease_in, ease_out…}"]
    errs = []
    for k, v in motion.items():
        if k in RANGES_MS:
            lo, hi = RANGES_MS[k]
            if not (isinstance(v, (int, float)) and not isinstance(v, bool) and lo <= v <= hi):
                errs.append(f"marca.motion.{k}: número entre {lo} y {hi}")
        elif k in ("ease_in", "ease_out"):
            if not (isinstance(v, str) and EASE_RE.match(v.strip())):
                errs.append(f"marca.motion.{k}: curva de GSAP no válida '{v}' (power1.out, sine.inOut, expo.out, back.out(1.7)…)")
        elif k not in ("style", "avoid"):
            errs.append(f"marca.motion.{k}: token desconocido (válidos: {', '.join(sorted(set(RANGES_MS) | {'ease_in', 'ease_out', 'style', 'avoid'}))})")
    if motion.get("style") not in (None, *STYLES):
        errs.append(f"marca.motion.style: {', '.join(STYLES)} (los mismos de la Memoria)")
    av = motion.get("avoid")
    if av is not None and not (isinstance(av, list) and all(e in EFFECTS for e in av)):
        errs.append(f"marca.motion.avoid: lista de efectos de la Memoria ({', '.join(EFFECTS)})")
    return errs


# Estilo promotional: entradas más rápidas y salidas más lentas, salvo que la marca fije enter_ms/exit_ms
PROMOTIONAL = {"enter_ms": ("fast_ms", 120), "exit_ms": (None, 1400)}


def motion_tokens(brand: dict | None) -> dict:
    """Tokens efectivos en segundos (y px para el desenfoque): los de la marca, los derivados del brand kit o los de serie."""
    m = (brand or {}).get("motion") or {}
    style = m.get("style", "editorial")
    ms = {}
    for k, default in MOTION_DEFAULTS.items():
        if k in m:
            ms[k] = m[k]
        elif style == "promotional" and k in PROMOTIONAL:
            src, d = PROMOTIONAL[k]
            ms[k] = m.get(src, d) if src else d
        elif k in DERIVED and DERIVED[k] in m:
            ms[k] = m[DERIVED[k]]
        else:
            ms[k] = default
    return {"enter": ms["enter_ms"] / 1000, "exit": ms["exit_ms"] / 1000, "blur": ms["exit_blur_px"],
            "ease_in": ms["ease_in"], "ease_out": ms["ease_out"], "exit_stagger": ms["exit_stagger_ms"] / 1000,
            "kicker": ms["kicker_ms"] / 1000, "word_stagger": ms["word_stagger_ms"] / 1000,
            "char_stagger": ms["char_stagger_ms"] / 1000, "style": style,
            "avoid": list(m.get("avoid") or [])}


# ── anclas a la voz ───────────────────────────────────────────────────────────────────────────────────────────────────
def norm(word: str) -> str:
    """Comparación de palabras: minúsculas, sin tildes ni signos («¿Componentes?» = «componentes»)."""
    s = unicodedata.normalize("NFD", str(word).lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"[^\w]+", "", s)


def phrase_tokens(text: str) -> list[str]:
    """Palabras de una frase en pantalla ('|' parte línea y no cuenta como palabra)."""
    return [w for w in re.split(r"[\s|]+", str(text)) if w.strip()]


def is_anchor(v) -> bool:
    return isinstance(v, str) and (v.strip() == "auto" or bool(ANCHOR_RE.match(v.strip())))


def has_anchors(sb: dict) -> bool:
    def walk(o) -> bool:
        if isinstance(o, dict):
            return any(((k in TIME_KEYS or k == "words_at") and (is_anchor(v) or (isinstance(v, list) and any(is_anchor(x) for x in v))))
                       or walk(v) for k, v in o.items())
        if isinstance(o, list):
            return any(walk(x) for x in o)
        return False
    return walk(sb.get("overlays", []))


def words_path(sb: dict, base: Path) -> Path:
    """words.json de las anclas: clave raíz `words`, si no `caption_style.words`, si no `words.json` junto al storyboard."""
    rel = sb.get("words") or (sb.get("caption_style") or {}).get("words") or "words.json"
    return Path(base) / rel


def _fmt_times(ws: list[dict]) -> str:
    return ", ".join(f"{w['start']:.2f}" for w in ws[:6]) + ("…" if len(ws) > 6 else "")


class _Resolver:
    def __init__(self, words: list[dict] | None):
        self.words = [{**w, "n": norm(w["text"])} for w in (words or [])]
        self.errors: list[str] = []

    def _missing_words(self, where: str) -> None:
        self.errors.append(f"{where}: hay anclas a la voz (word:… o auto) pero no hay words.json; pon la clave raíz \"words\" "
                           "con la ruta del words.json (relativa al storyboard) o escribe los tiempos en segundos")

    def find(self, spec: str, where: str, window: tuple[float, float] | None) -> dict | None:
        """La palabra (o secuencia) de `word:<x>[#n]`; con varias apariciones y sin #n, la única que caiga en la ventana."""
        m = ANCHOR_RE.match(spec.strip())
        toks = [norm(t) for t in phrase_tokens(m.group(1))]
        toks = [t for t in toks if t]
        if not self.words:
            self._missing_words(where); return None
        if not toks:
            self.errors.append(f"{where}: ancla vacía '{spec}'"); return None
        ns = [w["n"] for w in self.words]
        hits = [i for i in range(len(ns) - len(toks) + 1) if ns[i:i + len(toks)] == toks]
        label = " ".join(toks)
        if not hits:
            near = difflib.get_close_matches(toks[0], sorted(set(ns)), n=4, cutoff=0.6)
            self.errors.append(f"{where}: «{label}» no se dice en words.json" + (f" (parecidas: {', '.join(near)})" if near else "")
                               + "; corrige la palabra tal como se oye o pon el tiempo en segundos")
            return None
        if m.group(2):
            n = int(m.group(2))
            if not 1 <= n <= len(hits):
                self.errors.append(f"{where}: «{label}» se dice {len(hits)} vez/veces; #{n} no existe")
                return None
            i = hits[n - 1]
        elif len(hits) == 1:
            i = hits[0]
        else:
            inside = [i for i in hits if window and window[0] - 1e-6 <= self.words[i]["start"] <= window[1] + 1e-6]
            if len(inside) != 1:
                self.errors.append(f"{where}: «{label}» se dice {len(hits)} veces ({_fmt_times([self.words[i] for i in hits])} s); "
                                   f"elige una con word:{label.split()[0]}#n (1–{len(hits)})")
                return None
            i = inside[0]
        return {"start": self.words[i]["start"], "end": self.words[i + len(toks) - 1]["end"]}

    def time(self, key: str, v, where: str, window=None):
        """Valor de una clave de tiempo: números tal cual; anclas word: a segundos (entradas con adelanto, end al final)."""
        if not (isinstance(v, str) and ANCHOR_RE.match(v.strip())):
            return v
        hit = self.find(v, where, window)
        if hit is None:
            return v
        if key in ("end", "matte_end"):
            return round(hit["end"], 3)
        return round(max(0.0, hit["start"] - ANCHOR_LEAD_S), 3)

    def phrase(self, text: str, where: str, window: tuple[float, float]) -> list[float] | None:
        """words_at "auto": cada palabra de la frase en la voz, en orden, dentro de la ventana (seguidas o con palabras
        en medio). Los números escritos con cifras no casan con los dichos con letras: entonces, words_at explícito."""
        toks = [norm(t) for t in phrase_tokens(text)]
        if not self.words:
            self._missing_words(where); return None
        lo, hi = window
        cand = [w for w in self.words if lo - 1e-6 <= w["start"] <= hi + 1e-6]
        out, k = [], 0
        for t in toks:
            if not t:   # un signo suelto («—», «+»): entra con la palabra anterior
                out.append(out[-1] if out else None); continue
            j = next((j for j in range(k, len(cand)) if cand[j]["n"] == t), None)
            if j is None:
                heard = " ".join(w["text"] for w in cand) or "nada"
                self.errors.append(f"{where}: words_at auto no encuentra «{t}» entre {lo:.2f} y {hi:.2f} s (se oye: «{heard[:160]}»); "
                                   "ajusta start/end, escribe la palabra como se dice o usa words_at [\"word:…\", …]")
                return None
            out.append(round(max(0.0, cand[j]["start"] - ANCHOR_LEAD_S), 3)); k = j + 1
        first = next((x for x in out if x is not None), None)
        return [x if x is not None else first for x in out]


def voice_activity(audio: Path | str):
    """(máscara de voz por ventana de 10 ms, duración de la ventana) de un WAV, o None si no se puede leer."""
    from .cut import audio_silence_mask
    try:
        silent, hop = audio_silence_mask(audio, frame_ms=10, threshold_db=VOICE_DB)
    except (OSError, EOFError, KeyError, ValueError, wave.Error):
        return None
    return ~silent, hop


def snap_to_voice(words: list[dict], voiced, hop: float) -> list[dict]:
    """Inicios de palabra pegados al arranque real de la voz; solo cambia `start` y solo en dos casos sin ambigüedad:

    - el inicio cae en un silencio de `ONSET_PAUSE_S` o más: pasa a la primera voz (30 ms seguidos) antes del final de
      la palabra. Es el caso típico tras una pausa: «primero… escucha» con «escucha» empezando en mitad del silencio;
    - el inicio cae dentro de una voz que arrancó tras una pausa así, como mucho `ONSET_BACK_S` antes, y la palabra
      anterior empezó antes de esa pausa (Whisper la estiró sobre el silencio): pasa a ese arranque.

    El habla seguida, sin pausas, se queda como está: ahí Whisper acierta y los huecos cortos son consonantes."""
    n = len(voiced)

    def v(i: int) -> bool:
        return 0 <= i < n and bool(voiced[i])

    out = []
    for k, w in enumerate(words):
        s, e = float(w["start"]), float(w["end"])
        i = int(s / hop + 1e-6)
        new = s
        if i < n and not v(i):
            p = i
            while p > 0 and not v(p - 1):
                p -= 1
            j = i
            while j < n and j * hop < e and not (v(j) and v(j + 1) and v(j + 2)):
                j += 1
            if j < n and j * hop < e and (j - p) * hop >= ONSET_PAUSE_S - 1e-6:
                new = j * hop
        elif i < n:
            j = i
            while j > 0 and v(j - 1):
                j -= 1
            p = j
            while p > 0 and not v(p - 1):
                p -= 1
            prev_start = float(out[-1]["start"]) if out else -1.0
            if (j * hop < s and s - j * hop <= ONSET_BACK_S + 1e-6 and (j - p) * hop >= ONSET_PAUSE_S - 1e-6
                    and prev_start < p * hop):
                new = j * hop
        out.append({**w, "start": round(new, 3)} if abs(new - s) > 1e-9 else w)
    return out


def resolve_anchors(sb: dict, words: list[dict] | None) -> tuple[dict, list[str]]:
    """Copia del storyboard con todas las anclas convertidas a segundos, y la lista de errores (vacía si todo casa)."""
    sb = copy.deepcopy(sb)
    r = _Resolver(words)
    for n, o in enumerate(sb.get("overlays", []) or []):
        if not isinstance(o, dict):
            continue
        where = f"overlays[{n}] ({o.get('id', '?')})"
        for k in ("start", "end"):               # primero el tramo: da la ventana para desambiguar el resto
            if k in o:
                o[k] = r.time(k, o[k], f"{where}.{k}")
        win = (o["start"] - AUTO_WINDOW_S, o["end"]) if all(isinstance(o.get(k), (int, float)) for k in ("start", "end")) else None

        def walk(node, path):
            if isinstance(node, dict):
                for k, v in list(node.items()):
                    if node is o and k in ("start", "end"):
                        continue
                    if k in TIME_KEYS and isinstance(v, str) and v.strip() != "auto":
                        node[k] = r.time(k, v, f"{path}.{k}", win)
                    elif k == "words_at" and isinstance(v, list):
                        node[k] = [r.time("at", x, f"{path}.words_at[{j}]", win) for j, x in enumerate(v)]
                    elif isinstance(v, (dict, list)):
                        walk(v, f"{path}.{k}")
            elif isinstance(node, list):
                for j, v in enumerate(node):
                    walk(v, f"{path}[{j}]")
        walk(o, where)
        if o.get("words_at") == "auto":
            if win is None:
                r.errors.append(f"{where}.words_at: auto necesita start y end en segundos (o anclados a palabras que existan)")
            else:
                ats = r.phrase(o.get("text", ""), f"{where}.words_at", win)
                if ats is not None:
                    o["words_at"] = ats
        k = o.get("kicker")
        if isinstance(k, dict) and k.get("at", "auto") == "auto" and o.get("type") == "behind":
            ats = o.get("words_at") if isinstance(o.get("words_at"), list) else None
            first = min((x for x in ats if isinstance(x, (int, float))), default=None) if ats else o.get("at", o.get("start"))
            if isinstance(first, (int, float)) and isinstance(o.get("start"), (int, float)):
                k["at"] = round(max(o["start"], first - KICKER_LEAD_S), 3)
        if isinstance(o.get("at"), str) and o["at"].strip() == "auto" and isinstance(o.get("words_at"), list) and o["words_at"]:
            o["at"] = o["words_at"][0]
    return sb, r.errors


def resolve_storyboard(sb: dict, base: Path | str) -> tuple[dict, list[str]]:
    """Resuelve las anclas de un storyboard leído de `base` (su carpeta). Sin anclas lo devuelve tal cual."""
    if not has_anchors(sb):
        return sb, []
    from .captions import TranscriptFormatError, load_words
    p = words_path(sb, Path(base))
    words = None
    if p.exists():
        try:
            words = load_words(p)
        except TranscriptFormatError as e:
            return sb, [f"words.json de las anclas ({p.name}): {e}"]
    audio = (sb.get("source") or {}).get("audio")
    if words and isinstance(audio, str) and (Path(base) / audio).is_file():
        va = voice_activity(Path(base) / audio)
        if va is not None:
            words = snap_to_voice(words, *va)
    return resolve_anchors(sb, words)


def spread(ats: list[float], n: int) -> list[float]:
    """Reparte `n` palabras sobre los tiempos de otras (una traducción con más o menos palabras que el original)."""
    if not ats or n <= 0:
        return []
    if n == 1 or len(ats) == 1:
        return [ats[0]] * n if len(ats) == 1 else [ats[0]]
    return [ats[round(k * (len(ats) - 1) / (n - 1))] for k in range(n)]
