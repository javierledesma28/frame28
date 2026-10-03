"""check + render de un proyecto HyperFrames, con ffmpeg garantizado en PATH y hoja de contacto de revisión."""
from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

from . import HYPERFRAMES_VERSION
from .env import env_with_ffmpeg, npx
from .media import probe, sheet, sheet_plan


def _hf(args: list[str], cwd: Path, timeout: int = 1800, extra_env: dict | None = None) -> subprocess.CompletedProcess:
    env = env_with_ffmpeg(); env.update(extra_env or {})
    return subprocess.run([npx(), "--yes", f"hyperframes@{HYPERFRAMES_VERSION}", *args], cwd=str(cwd), env=env,
                          text=True, capture_output=True, encoding="utf-8", errors="replace", timeout=timeout, stdin=subprocess.DEVNULL)


NODE_HEAP_MB = 8192   # el heap por defecto de Node (~4 GB) aguanta unos 5 trabajadores de captura (lo avisa HyperFrames)


def render_args(output: Path, quality: str = "high", crf: int = 18, fps: int | None = None, workers: int | None = None,
                gpu: bool = False, node_options: str = "") -> tuple[list[str], dict]:
    """Argumentos y entorno de `hyperframes render`. El tiempo se va en capturar cada fotograma con Chrome (que ya usa
    la GPU del navegador por defecto), repartido entre trabajadores: HyperFrames elige ~6; con más núcleos y memoria,
    `workers` lo sube (y el heap de Node con él). `gpu` codifica con la GPU (NVENC): algo más rápido, fichero mayor.
    Medido en 16 núcleos, 32 GB y RTX 4060 con un clip de 10 s: 6 → 81 s; 10 → 68 s; 14 → 76 s; 10 + gpu → 57 s."""
    args = ["render", "-o", str(output), "-q", quality, "--crf", str(crf)]
    env: dict = {}
    if fps:
        args += ["-f", str(fps)]
    if workers:
        args += ["-w", str(int(workers))]
        if int(workers) > 5 and "max-old-space-size" not in node_options:
            env["NODE_OPTIONS"] = (node_options + f" --max-old-space-size={NODE_HEAP_MB}").strip()
    if gpu:
        args.append("--gpu")
    return args, env


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


def render(project: str | Path, output: str | Path, quality: str = "high", crf: int = 18, fps: int | None = None, make_sheet: bool = True,
           workers: int | None = None, gpu: bool | None = None) -> dict:
    """`gpu=None`: NVENC si la máquina lo tiene (env.use_gpu_encoder), si no libx264."""
    if gpu is None:
        from .env import use_gpu_encoder
        gpu = use_gpu_encoder()
    project = Path(project); output = Path(output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    args, env = render_args(output, quality, crf, fps, workers, gpu, os.environ.get("NODE_OPTIONS", ""))
    r = _hf(args, project, timeout=3600, extra_env=env)
    out = r.stdout + r.stderr
    ok = output.exists() and "Render complete" in out
    m = re.search(r"rendered in ([\dm\s.]+s)", out)
    res = {"ok": ok, "output": str(output), "time": m.group(1).strip() if m else None, "log_tail": out[-1500:],
           **({"workers": int(workers)} if workers else {}), **({"gpu": True} if gpu else {})}
    if ok and make_sheet:
        every, cols, rows = sheet_plan(probe(output)["duration"])
        res["sheet"] = str(sheet(output, output.with_name(output.stem + "_sheet.png"), every, cols, rows))
        res["sheet_every"] = every
    return res
