"""Fixtures compartidas: rutas del repo (casos reales de `poc/`) y datos sintéticos pequeños.

La suite cubre solo los módulos puros y rápidos (sin ffmpeg, sin modelos, sin render). Se ejecuta desde `plugin/cli`:

    uv run --group dev pytest

`scripts/release-check.py` la lanza antes de etiquetar.
"""
from __future__ import annotations

import json
import struct
import wave
from pathlib import Path

import pytest

CLI_DIR = Path(__file__).resolve().parents[1]
REPO = CLI_DIR.parents[1]
POC = REPO / "poc"


def _storyboards() -> list[Path]:
    return sorted(p for p in POC.glob("*/storyboard*.json") if "work" not in p.parts and "out" not in p.parts)


STORYBOARDS = _storyboards()


@pytest.fixture(scope="session")
def repo() -> Path:
    return REPO


@pytest.fixture(scope="session")
def javier_words() -> Path:
    """words.json real (10 s, en segundos) del clip de regresión."""
    p = POC / "clip-javier" / "words.json"
    assert p.exists(), p
    return p


@pytest.fixture(scope="session")
def javier_storyboard() -> dict:
    return json.loads((POC / "clip-javier" / "storyboard-gsap.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def cliente-a_short() -> dict:
    return json.loads((POC / "clip-grabado" / "storyboard-short-s4.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def cliente-a_strings() -> dict:
    return json.loads((POC / "clip-grabado" / "strings-short-s4.es.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def cliente-a_clips() -> dict:
    return json.loads((POC / "clip-grabado" / "clips.json").read_text(encoding="utf-8"))


def words_from(spec: str, start: float = 0.0, dur: float = 0.3, gap: float = 0.05) -> list[dict]:
    """'hola mundo|2.0 otra' → palabras consecutivas; un token 'texto|t' fija el inicio de esa palabra en t."""
    out, t = [], start
    for tok in spec.split():
        text, _, at = tok.partition("|")
        if at:
            t = float(at)
        out.append({"text": text, "start": round(t, 3), "end": round(t + dur, 3)})
        t = round(t + dur + gap, 3)
    return out


def write_json(path: Path, data) -> Path:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    return path


def write_wav(path: Path, segments: list[tuple[float, float, bool]], rate: int = 16000) -> Path:
    """WAV mono 16 bit: lista de (inicio, fin, con_voz). La voz es una onda de amplitud alta; el silencio, ceros."""
    total = max(e for _, e, _ in segments)
    n = int(total * rate)
    samples = [0] * n
    for s, e, voiced in segments:
        if not voiced:
            continue
        for i in range(int(s * rate), min(n, int(e * rate))):
            samples[i] = 12000 if (i // 40) % 2 == 0 else -12000  # onda cuadrada de 200 Hz
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate)
        w.writeframes(struct.pack(f"<{n}h", *samples))
    return path
