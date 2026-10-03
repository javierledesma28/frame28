"""check + render de un proyecto HyperFrames, con ffmpeg garantizado en PATH y hoja de contacto de revisión."""
from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

from . import HYPERFRAMES_VERSION
from .env import env_with_ffmpeg, npx_cmd
from .media import probe, sheet, sheet_plan


def _hf(args: list[str], cwd: Path, timeout: int = 1800, extra_env: dict | None = None) -> subprocess.CompletedProcess:
    env = env_with_ffmpeg(); env.update(extra_env or {})
    return subprocess.run([*npx_cmd(), "--yes", f"hyperframes@{HYPERFRAMES_VERSION}", *args], cwd=str(cwd), env=env,
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


def parse_check(returncode: int, out: str) -> dict:
    """Lee la salida de `hyperframes check`. Antes bastaba con no ver líneas ✗ para aprobar: si npx fallaba (sin red la
    primera vez, Node viejo, error de npm) no había ✗ y salía «check pasó» (F28-81). Ahora solo aprueba si HyperFrames se
    ejecutó de verdad (su resumen «N error(s)» o «Check passed/failed») y no hay errores reales; el texto detrás del
    hablante (text_occluded) y los avisos de contraste se separan para que el agente decida."""
    marks = [l.strip() for l in out.splitlines() if "✗" in l]
    occluded = [e for e in marks if "text_occluded" in e]          # el falso positivo conocido: texto detrás del hablante
    contrast = [e for e in marks if "(need " in e]                  # HyperFrames lo da como aviso: sombra, caja u otro color
    real = [e for e in marks if e not in occluded and e not in contrast]
    totals = [int(n) for n in re.findall(r"(\d+) error\(s\)", out)]
    ran = bool(re.search(r"Check (passed|failed)", out) or totals)
    if not ran:
        tail = " · ".join(l.strip() for l in out.strip().splitlines()[-4:] if l.strip())[:400]
        real = [f"HyperFrames no llegó a ejecutarse (código {returncode}): {tail or 'sin salida'}. Mira `frame28 doctor` "
                "(node, npx y la red: la primera vez npx descarga HyperFrames)"]
    unexplained = sum(totals) > len(occluded) + len(contrast) and "Check passed" not in out
    if ran and not real and unexplained:                            # cuenta errores que no sabemos leer: no aprobar a ciegas
        real = [f"HyperFrames cuenta {sum(totals)} error(es) que no se pudieron leer de su salida: revisa «raw»"]
    return {"passed": ran and not real, "ran": ran, "errors": real, "contrast_warnings": contrast,
            "known_false_positives": occluded, "returncode": returncode, "raw": out[-3000:]}


def check(project: str | Path) -> dict:
    try:
        r = _hf(["check"], Path(project), timeout=600)
    except FileNotFoundError:
        return parse_check(127, "npx no encontrado: instala Node.js 22 o superior")
    except subprocess.TimeoutExpired:
        return parse_check(124, "hyperframes check no terminó en 10 minutos")
    return parse_check(r.returncode, r.stdout + r.stderr)


def render_timeout(project: Path) -> int:
    """Segundos que se deja al render: FRAME28_RENDER_TIMEOUT si está; si no, 60 s por segundo de vídeo (unos 2 s por
    fotograma: un portátil modesto) con un mínimo de una hora. Antes era una hora fija y un vídeo largo reventaba."""
    env = os.environ.get("FRAME28_RENDER_TIMEOUT", "").strip()
    if env.isdigit():
        return int(env)
    try:
        durs = [float(x) for x in re.findall(r'data-duration="([\d.]+)"', (project / "index.html").read_text(encoding="utf-8"))]
    except OSError:
        durs = []
    return max(3600, int(60 * max(durs, default=0)))


def render(project: str | Path, output: str | Path, quality: str = "high", crf: int = 18, fps: int | None = None, make_sheet: bool = True,
           workers: int | None = None, gpu: bool | None = None) -> dict:
    """`gpu=None`: NVENC si la máquina lo tiene (env.use_gpu_encoder), si no libx264."""
    if gpu is None:
        from .env import use_gpu_encoder
        gpu = use_gpu_encoder()
    project = Path(project); output = Path(output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    args, env = render_args(output, quality, crf, fps, workers, gpu, os.environ.get("NODE_OPTIONS", ""))
    limit = render_timeout(project)
    try:
        r = _hf(args, project, timeout=limit, extra_env=env)
    except subprocess.TimeoutExpired:
        return {"ok": False, "output": str(output), "time": None,
                "log_tail": f"el render no terminó en {limit} s: sube FRAME28_RENDER_TIMEOUT, usa --quality draft o más --workers"}
    except FileNotFoundError:
        return {"ok": False, "output": str(output), "time": None, "log_tail": "npx no encontrado: instala Node.js 22 o superior"}
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
