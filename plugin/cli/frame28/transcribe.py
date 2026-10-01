"""Transcripción con tiempos por palabra (faster-whisper) y exportación en los tres formatos que usamos."""
from __future__ import annotations

import json
from pathlib import Path


def _ts(sec: float) -> str:
    h = int(sec // 3600); m = int(sec % 3600 // 60); s = sec % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}".replace(".", ",")


def pick_device(device: str = "auto", compute: str = "auto", ready: tuple[bool, str] | None = None) -> tuple[str, str, str]:
    """(device, compute, motivo). `auto` usa la GPU si `env.cuda_ready()` dice que se puede (float16) y, si no, CPU
    (int8). Un `device` explícito se respeta; `compute` explícito también."""
    if device == "auto":
        if ready is None:
            from .env import cuda_ready
            ready = cuda_ready()
        device = "cuda" if ready[0] else "cpu"
        why = ready[1]
    else:
        why = "elegido a mano"
        if device == "cuda":
            from .env import enable_cuda_dlls
            enable_cuda_dlls()
    if compute == "auto":
        compute = "float16" if device == "cuda" else "int8"
    return device, compute, why


def _run_whisper(audio: str | Path, model: str, device: str, compute: str, kw: dict) -> tuple[list[dict], list[dict], object]:
    from faster_whisper import WhisperModel

    m = WhisperModel(model, device=device, compute_type=compute)
    segs, info = m.transcribe(str(audio), **kw)
    words, segments = [], []
    for s in segs:   # la transcripción ocurre al recorrer el generador: un fallo de GPU salta aquí
        segments.append({"start": round(s.start, 3), "end": round(s.end, 3), "text": s.text.strip()})
        for w in (s.words or []):
            words.append({"text": w.word.strip(), "start": round(w.start, 3), "end": round(w.end, 3),
                          "prob": round(w.probability, 3)})
    return words, segments, info


def transcribe(audio: str | Path, out_dir: str | Path, lang: str = "es", model: str = "medium",
               device: str = "auto", compute: str = "auto", script: str | None = None) -> dict:
    """Devuelve dict con words, phrases y rutas escritas. `script` (guion) se acepta como initial_prompt para
    sesgar el vocabulario (nombres propios); el alineado forzado real queda para stable-ts/WhisperX.
    Con `device="auto"` usa la GPU NVIDIA si está lista; si la GPU falla a mitad, repite en CPU."""
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    auto = device == "auto"
    dev, comp, why = pick_device(device, compute)
    kw = {"word_timestamps": True, "language": lang, "vad_filter": True}
    if script:
        kw["initial_prompt"] = script[:800]
    note = None
    try:
        words, segments, info = _run_whisper(audio, model, dev, comp, kw)
    except Exception as e:  # noqa: BLE001
        if not (auto and dev == "cuda"):
            raise
        note = f"la GPU falló ({type(e).__name__}: {str(e)[:120]}); transcrito en CPU"
        dev, comp = "cpu", "int8" if compute == "auto" else compute
        words, segments, info = _run_whisper(audio, model, dev, comp, kw)
    # captions.json por frase completa (partida por comas y conjunciones si no cabe en dos líneas), no por los
    # segmentos de Whisper: cortan cada ~4,5 s a mitad de frase y rompen subtítulos, tramos de shorts y traducción
    from .captions import phrase_captions
    phrases = phrase_captions(words, lang=lang) if words else segments
    # 1) words.json (Frame28)
    (out / "words.json").write_text(json.dumps(words, indent=1, ensure_ascii=False), encoding="utf-8")
    # 2) captions.json: frases para subtítulos
    (out / "captions.json").write_text(json.dumps(phrases, indent=1, ensure_ascii=False), encoding="utf-8")
    # 3) words.srt: una palabra por cue, finales de línea LF (HyperFrames lo importa con --preserve-cues)
    with open(out / "words.srt", "w", encoding="utf-8", newline="\n") as f:
        for i, w in enumerate(words, 1):
            f.write(f"{i}\n{_ts(w['start'])} --> {_ts(w['end'])}\n{w['text']}\n\n")
    # 4) transcript.json en el formato de HyperFrames
    hf = [{"text": w["text"], "start": w["start"], "end": w["end"], "id": f"w{i}"} for i, w in enumerate(words)]
    (out / "transcript.json").write_text(json.dumps(hf, indent=1, ensure_ascii=False), encoding="utf-8")
    text = " ".join(w["text"] for w in words)
    (out / "transcript.txt").write_text(text, encoding="utf-8")
    return {"language": info.language, "words": len(words), "phrases": len(phrases), "text": text, "dir": str(out),
            "device": dev, "compute": comp, "device_note": note or why}
