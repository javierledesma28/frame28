"""Jump cuts por transcripción: silencios, muletillas y repeticiones (retakes).

`plan` decide qué tramos quitar a partir de words.json y confirma los silencios contra el audio real.
`apply` corta vídeo y voz con fundidos de 30 ms y reajusta los tiempos de palabras, subtítulos y storyboard
para que el resto del pipeline trabaje sobre el clip ya cortado sin volver a transcribir.
"""
from __future__ import annotations

import json
import wave
from pathlib import Path

import numpy as np

from .captions import load_captions, load_words
from .env import ffmpeg, run

FILLERS = {
    "es": {"eh", "ehh", "ehm", "em", "emm", "mm", "mmm", "hmm", "uhm", "um", "uh", "ah", "aha", "ajá", "aja", "este...", "o sea..."},
    "en": {"uh", "um", "uhm", "hmm", "mm", "mmm", "erm", "er", "ah", "like..."},
}
# muletillas condicionadas: solo se cortan si el audio las aísla con una pausa (antes o después). "bueno" o "este"
# también son palabras normales; sueltas entre silencios son relleno.
SOFT_FILLERS = {
    "es": {"bueno", "pues", "digamos", "vale", "eh", "ehh", "em", "a ver", "o sea"},  # "este"/"nada" fuera: demasiado ambiguos
    "en": {"well", "so", "like", "right", "okay", "ok", "you know", "i mean"},
}


def _norm(w: str) -> str:
    return w.strip().strip(".,;:!?¿¡\"'«»()").lower()


def audio_silence_mask(audio: str | Path, frame_ms: int = 20, threshold_db: float = -42.0) -> tuple[np.ndarray, float]:
    """Devuelve (máscara booleana de silencio por ventana, duración de ventana en s) leyendo un WAV PCM."""
    with wave.open(str(audio), "rb") as w:
        rate, ch, sw, n = w.getframerate(), w.getnchannels(), w.getsampwidth(), w.getnframes()
        raw = w.readframes(n)
    dtype = {1: np.int8, 2: np.int16, 4: np.int32}[sw]
    x = np.frombuffer(raw, dtype=dtype).astype(np.float32)
    if ch > 1:
        x = x.reshape(-1, ch).mean(axis=1)
    x /= float(np.iinfo(dtype).max)
    win = int(rate * frame_ms / 1000)
    n_win = len(x) // win
    rms = np.sqrt((x[: n_win * win].reshape(n_win, win) ** 2).mean(axis=1) + 1e-12)
    db = 20 * np.log10(rms + 1e-9)
    return db < threshold_db, win / rate


def _silent_core(mask: np.ndarray, hop: float, a: float, b: float) -> tuple[float, float] | None:
    """Mayor tramo continuo de silencio de audio dentro de [a, b]; None si no hay ninguno."""
    i0, i1 = int(a / hop), min(int(b / hop), len(mask))
    best, cur_start, best_len = None, None, 0
    for i in range(i0, i1 + 1):
        s = i < i1 and mask[i]
        if s and cur_start is None:
            cur_start = i
        if (not s) and cur_start is not None:
            if i - cur_start > best_len:
                best_len, best = i - cur_start, (cur_start * hop, i * hop)
            cur_start = None
    return best


def plan(words_path: str | Path, audio: str | Path | None = None, min_gap: float = 0.6, pad: float = 0.12,
         lang: str = "es", fillers: bool = True, retakes: bool = True, duration: float | None = None) -> dict:
    words = load_words(words_path)
    removed: list[dict] = []
    mask, hop = (audio_silence_mask(audio) if audio else (None, 0.0))
    total = float(duration or (mask is not None and len(mask) * hop) or (words[-1]["end"] if words else 0))

    # 1) silencios: huecos entre palabras > min_gap (confirmados con el audio si lo hay)
    gaps = []
    if words:
        gaps.append((0.0, words[0]["start"], "inicio"))
        for a, b in zip(words, words[1:]):
            gaps.append((a["end"], b["start"], "pausa"))
        gaps.append((words[-1]["end"], total, "final"))
    for g0, g1, kind in gaps:
        if g1 - g0 < (min_gap if kind == "pausa" else 0.35):
            continue
        c0, c1 = g0, g1
        if mask is not None:
            core = _silent_core(mask, hop, g0, g1)
            if core is None:
                continue
            c0, c1 = core
        # dejar aire a cada lado; el inicio y el final se cortan casi a ras
        keep_pad = pad if kind == "pausa" else 0.05
        c0, c1 = c0 + keep_pad, c1 - keep_pad
        if c1 - c0 >= 0.15:
            removed.append({"start": round(max(0.0, c0), 3), "end": round(min(total, c1), 3), "reason": "silencio " + kind})

    # 1b) silencios *dentro* de una palabra: Whisper estira la palabra anterior a una pausa ("bueno" de 2 s).
    #     Se recorta el silencio de audio interior si dura >= 0.5 s, dejando aire al final de la palabra.
    if mask is not None:
        for w in words:
            if (w["end"] - w["start"]) < 0.9:
                continue
            core = _silent_core(mask, hop, w["start"] + 0.15, w["end"])
            if core and (core[1] - core[0]) >= max(0.7, min_gap + 0.1):
                c0, c1 = core[0] + pad, core[1] - 0.05
                if c1 - c0 >= 0.15:
                    removed.append({"start": round(c0, 3), "end": round(c1, 3), "reason": f"silencio dentro de '{w['text'].strip()}'"})

    # 2) muletillas: palabras sueltas de la lista, cortadas con su silencio adyacente
    if fillers:
        fl = FILLERS.get(lang, set())
        for w in words:
            if _norm(w["text"]) in fl and (w["end"] - w["start"]) <= 1.2:
                removed.append({"start": round(max(0.0, w["start"] - 0.03), 3), "end": round(w["end"] + 0.03, 3),
                                "reason": f"muletilla '{w['text'].strip()}'"})

    # 2b) muletillas condicionadas: 'bueno', 'pues', 'este'... solo si va seguida de una pausa de audio (>= 0.2 s
    #     pegada a su final). "este muñeco" no se toca; "este... [pausa]" sí. Se cortan con su silencio.
    if fillers and mask is not None:
        sf = SOFT_FILLERS.get(lang, set())

        def silent_near(t: float, span: float = 0.35) -> bool:
            core = _silent_core(mask, hop, max(0.0, t - span), t + span)
            return bool(core and (core[1] - core[0]) >= 0.2)

        for k, w in enumerate(words):
            if _norm(w["text"]) not in sf:
                continue
            voiced = w["end"] - w["start"]
            if voiced > 2.5:
                continue
            if silent_near(w["end"]) and not (k + 1 < len(words) and words[k + 1]["start"] - w["end"] < 0.05 and not silent_near(w["end"], 0.2)):
                removed.append({"start": round(max(0.0, w["start"] - 0.03), 3), "end": round(w["end"] + 0.03, 3),
                                "reason": f"muletilla '{w['text'].strip()}' (aislada por pausa)"})

    # 3) retakes (falsos arranques): el hablante repite la misma secuencia de >= 3 palabras
    #    y la primera vez se quedó a medias: la repetición empieza justo después (como mucho una palabra
    #    en medio) y suele haber una pausa antes de volver a empezar. "por aquí hay X, por aquí hay Y"
    #    NO es un retake: entre ambas hay contenido.
    if retakes and len(words) >= 6:
        toks = [_norm(w["text"]) for w in words]
        n = len(toks); i = 0
        while i < n - 5:
            found = False
            for L in range(min(8, (n - i) // 2), 2, -1):
                seq = toks[i:i + L]
                for j in (i + L, i + L + 1):
                    if j + L <= n and toks[j:j + L] == seq:
                        between = j - (i + L)
                        pause = words[j]["start"] - words[j - 1]["end"]
                        if between == 0 or pause >= 0.25:
                            removed.append({"start": round(words[i]["start"] - 0.03, 3), "end": round(words[j]["start"] - 0.03, 3),
                                            "reason": "falso arranque: '" + " ".join(w["text"].strip() for w in words[i:i + L]) + "'"})
                            i = j; found = True; break
                if found:
                    break
            if not found:
                i += 1

    # fusionar y convertir en tramos a conservar
    removed.sort(key=lambda r: r["start"])
    merged: list[dict] = []
    for r in removed:
        if merged and r["start"] <= merged[-1]["end"] + 0.02:
            merged[-1]["end"] = max(merged[-1]["end"], r["end"]); merged[-1]["reason"] += " + " + r["reason"]
        else:
            merged.append(dict(r))
    keep, t = [], 0.0
    for r in merged:
        if r["start"] - t >= 0.2:
            keep.append({"start": round(t, 3), "end": round(r["start"], 3)})
        t = r["end"]
    if total - t >= 0.2:
        keep.append({"start": round(t, 3), "end": round(total, 3)})
    new_total = sum(k["end"] - k["start"] for k in keep)
    return {"source_duration": round(total, 3), "result_duration": round(new_total, 3),
            "removed_seconds": round(total - new_total, 3), "min_gap": min_gap, "pad": pad,
            "keep": keep, "removed": merged}


# ---------- remapeo de tiempos ----------
def _mapper(keep: list[dict]):
    """Devuelve f(t) → tiempo en el clip cortado, o None si t cae en un tramo eliminado."""
    offsets = []
    acc = 0.0
    for k in keep:
        offsets.append((k["start"], k["end"], acc)); acc += k["end"] - k["start"]

    def f(t: float, clamp: bool = True):
        for a, b, off in offsets:
            if a <= t <= b:
                return round(t - a + off, 3)
        if clamp:  # cae en un hueco: al borde más cercano
            best = None
            for a, b, off in offsets:
                for edge, val in ((a, off), (b, off + b - a)):
                    d = abs(t - edge)
                    if best is None or d < best[0]:
                        best = (d, val)
            return round(best[1], 3) if best else None
        return None
    return f


def remap_words(words: list[dict], keep: list[dict]) -> list[dict]:
    f = _mapper(keep); out = []
    for w in words:
        s = f(w["start"], clamp=False); e = f(w["end"], clamp=False)
        if s is None and e is None:
            continue  # palabra eliminada (muletilla / retake)
        s = s if s is not None else f(w["start"]); e = e if e is not None else f(w["end"])
        if e > s:
            out.append({**w, "start": s, "end": e})
    return out


def remap_storyboard(sb: dict, keep: list[dict]) -> tuple[dict, list[str]]:
    f = _mapper(keep); warnings = []
    new_total = round(sum(k["end"] - k["start"] for k in keep), 3)
    sb = json.loads(json.dumps(sb))
    old_src = float(sb["source"]["duration"])
    sb["source"]["duration"] = new_total
    if "duration" in sb:
        sb["duration"] = round(new_total + max(0.0, float(sb["duration"]) - old_src), 3)
    for c in sb.get("captions", []):
        c["start"], c["end"] = f(c["start"]), f(c["end"])
    for o in sb.get("overlays", []):
        # la máscara alfa se compara con los cortes en tiempos ORIGINALES (antes de remapear el overlay)
        m0, m1 = o.get("matte_start", o.get("start")), o.get("matte_end", o.get("end"))
        for k in ("start", "end", "at", "matte_start", "matte_end"):
            if k in o and o[k] <= old_src + 0.01:
                o[k] = f(o[k])
            elif k in o:  # tarjetas de cierre más allá del clip: desplazar en bloque
                o[k] = round(o[k] - (old_src - new_total), 3)
        if o.get("type") == "behind" and m0 is not None and m1 is not None:
            gaps = [r for r in sb.get("_removed", []) if r["start"] < m1 and r["end"] > m0]
            if gaps:
                warnings.append(f"overlay {o['id']} (behind): un corte cae dentro de su máscara alfa; regenera la máscara con `frame28 matte` sobre el clip cortado")
        for line in o.get("lines", []) or []:
            for w in line:
                if "at" in w:
                    w["at"] = f(w["at"])
        for it in o.get("items", []) or []:
            if "at" in it:
                it["at"] = f(it["at"])
        for key in ("title", "subtitle"):
            if isinstance(o.get(key), dict) and "at" in o[key]:
                o[key]["at"] = f(o[key]["at"])
        if "end" in o and "start" in o and o["end"] <= o["start"]:
            o["end"] = round(o["start"] + 0.5, 3); warnings.append(f"overlay {o['id']}: duración colapsada por un corte; ajustada a 0,5 s")
    sb.pop("_removed", None)
    return sb, warnings


# ---------- aplicar cortes ----------
def apply(video: str | Path, audio: str | Path | None, cuts_path: str | Path, out_dir: str | Path,
          words_path: str | Path | None = None, captions_path: str | Path | None = None, storyboard_path: str | Path | None = None,
          fade: float = 0.03) -> dict:
    cuts = json.loads(Path(cuts_path).read_text(encoding="utf-8")); keep = cuts["keep"]
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    res: dict = {"segments": len(keep), "result_duration": cuts["result_duration"]}
    # vídeo: trim + concat (re-encode; los tramos no caen en keyframes)
    parts = []; labels = []
    for i, k in enumerate(keep):
        parts.append(f"[0:v]trim=start={k['start']}:end={k['end']},setpts=PTS-STARTPTS[v{i}]"); labels.append(f"[v{i}]")
    fc = ";".join(parts) + ";" + "".join(labels) + f"concat=n={len(keep)}:v=1:a=0[v]"
    vout = out / "clip.mp4"
    r = run([ffmpeg(), "-v", "error", "-y", "-i", str(video), "-filter_complex", fc, "-map", "[v]", "-c:v", "libx264", "-crf", "16",
             "-pix_fmt", "yuv420p", "-r", "30", str(vout)])
    if r.returncode != 0:
        raise SystemExit(r.stderr)
    res["clip"] = str(vout)
    # audio: atrim + fundidos de 30 ms en cada borde + concat
    if audio:
        parts = []; labels = []
        for i, k in enumerate(keep):
            d = k["end"] - k["start"]
            parts.append(f"[0:a]atrim=start={k['start']}:end={k['end']},asetpts=PTS-STARTPTS,afade=t=in:st=0:d={fade},afade=t=out:st={max(0.0, d - fade):.3f}:d={fade}[a{i}]")
            labels.append(f"[a{i}]")
        fc = ";".join(parts) + ";" + "".join(labels) + f"concat=n={len(keep)}:v=0:a=1[a]"
        aout = out / "voice.wav"
        r = run([ffmpeg(), "-v", "error", "-y", "-i", str(audio), "-filter_complex", fc, "-map", "[a]", "-ar", "48000", "-ac", "2", str(aout)])
        if r.returncode != 0:
            raise SystemExit(r.stderr)
        res["voice"] = str(aout)
        a16 = out / "audio16k.wav"
        run([ffmpeg(), "-v", "error", "-y", "-i", str(aout), "-ac", "1", "-ar", "16000", str(a16)]); res["audio16k"] = str(a16)
    # tiempos
    if words_path:
        words = load_words(words_path, merge_symbols=False)
        nw = remap_words(words, keep)
        (out / "words.json").write_text(json.dumps(nw, indent=1, ensure_ascii=False), encoding="utf-8")
        res["words"] = str(out / "words.json"); res["words_dropped"] = len(words) - len(nw)
    if captions_path:
        caps = load_captions(captions_path)
        f = _mapper(keep)
        nc = [{**c, "start": f(c["start"]), "end": f(c["end"])} for c in caps]
        nc = [c for c in nc if c["end"] > c["start"]]
        (out / "captions.json").write_text(json.dumps(nc, indent=1, ensure_ascii=False), encoding="utf-8"); res["captions"] = str(out / "captions.json")
    if storyboard_path:
        sb = json.loads(Path(storyboard_path).read_text(encoding="utf-8")); sb["_removed"] = cuts["removed"]
        nsb, warns = remap_storyboard(sb, keep)
        nsb["source"]["video"] = "clip.mp4"
        if nsb["source"].get("audio"):
            nsb["source"]["audio"] = "voice.wav"
        (out / "storyboard.json").write_text(json.dumps(nsb, indent=1, ensure_ascii=False), encoding="utf-8")
        res["storyboard"] = str(out / "storyboard.json"); res["warnings"] = warns
    return res
