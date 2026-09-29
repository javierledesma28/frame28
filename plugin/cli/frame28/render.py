"""check + render de un proyecto HyperFrames, con ffmpeg garantizado en PATH y hoja de contacto de revisión."""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

from . import HYPERFRAMES_VERSION
from .env import env_with_ffmpeg, npx
from .media import sheet


def _hf(args: list[str], cwd: Path, timeout: int = 1800) -> subprocess.CompletedProcess:
    return subprocess.run([npx(), "--yes", f"hyperframes@{HYPERFRAMES_VERSION}", *args], cwd=str(cwd), env=env_with_ffmpeg(),
                          text=True, capture_output=True, encoding="utf-8", errors="replace", timeout=timeout, stdin=subprocess.DEVNULL)


def check(project: str | Path) -> dict:
    r = _hf(["check"], Path(project), timeout=600)
    out = r.stdout + r.stderr
    marks = [l.strip() for l in out.splitlines() if "✗" in l]
    # el falso positivo conocido: texto detrás del hablante marcado como ocluido
    occluded = [e for e in marks if "text_occluded" in e]
    # contraste: HyperFrames lo reporta como aviso; lo separamos para que el agente decida (sombra, caja, otro color)
    contrast = [e for e in marks if "(need " in e]
    real = [e for e in marks if e not in occluded and e not in contrast]
    passed = "Check passed" in out or (not real)
    return {"passed": passed, "errors": real, "contrast_warnings": contrast, "known_false_positives": occluded, "raw": out[-3000:]}


def render(project: str | Path, output: str | Path, quality: str = "high", crf: int = 18, fps: int | None = None, make_sheet: bool = True) -> dict:
    project = Path(project); output = Path(output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    args = ["render", "-o", str(output), "-q", quality, "--crf", str(crf)]
    if fps:
        args += ["-f", str(fps)]
    r = _hf(args, project)
    out = r.stdout + r.stderr
    ok = output.exists() and "Render complete" in out
    m = re.search(r"rendered in ([\dm\s.]+s)", out)
    res = {"ok": ok, "output": str(output), "time": m.group(1).strip() if m else None, "log_tail": out[-1500:]}
    if ok and make_sheet:
        res["sheet"] = str(sheet(output, output.with_name(output.stem + "_sheet.png")))
    return res
