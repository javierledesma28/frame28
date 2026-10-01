"""Registro de tiempo por orden y resumen de coste por vídeo.

Cada `frame28 <orden>` apunta una línea JSON en `.frame28/log.jsonl` del directorio de trabajo (o en `FRAME28_LOG`;
`FRAME28_LOG=0` lo desactiva): orden, argumentos, segundos y si acabó bien. `frame28 report` agrupa por orden y da
el tiempo total; `frame28 report note` deja constancia de lo que el CLI no puede medir (tokens del director,
minutos de revisión, coste de stock). Nace del día 5 del plan: saber lo que cuesta producir un vídeo para fijar
precio y ver dónde se va el tiempo.
"""
from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import click

LOG_ENV = "FRAME28_LOG"
DEFAULT_REL = Path(".frame28") / "log.jsonl"
UNLOGGED = {"report", "doctor", "storyboard schema", "brand list", "brand show", "broll providers"}


def log_path() -> Path | None:
    v = os.environ.get(LOG_ENV)
    if v is not None and v.strip() in ("0", "", "off", "no"):
        return None
    return Path(v) if v else Path.cwd() / DEFAULT_REL


def _append(path: Path, entry: dict) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError:
        pass  # el registro nunca rompe una orden


def record(cmd: str, argv: list[str], seconds: float, ok: bool, error: str | None = None, path: Path | None = None) -> None:
    p = path or log_path()
    if p is None or not cmd:
        return
    entry = {"ts": datetime.now(timezone.utc).isoformat(timespec="seconds"), "cmd": cmd,
             "args": [a for a in argv if len(a) < 200][:24], "s": round(seconds, 2), "ok": ok}
    if error:
        entry["error"] = error[:200]
    _append(p, entry)


def add_note(text: str, tokens: int | None = None, cost: float | None = None, minutes: float | None = None, path: Path | None = None) -> dict:
    p = path or log_path() or Path.cwd() / DEFAULT_REL
    entry = {"ts": datetime.now(timezone.utc).isoformat(timespec="seconds"), "note": text}
    if tokens is not None:
        entry["tokens"] = int(tokens)
    if cost is not None:
        entry["cost"] = float(cost)
    if minutes is not None:
        entry["minutes"] = float(minutes)
    _append(p, entry)
    return entry


def command_path(group: click.Group, argv: list[str]) -> str:
    """'cut plan' a partir de argv, siguiendo los grupos de click; '' si no hay orden (p. ej. --help)."""
    names: list[str] = []
    grp: click.Command = group
    for tok in argv:
        if tok.startswith("-"):
            continue
        if isinstance(grp, click.Group) and tok in grp.commands:
            names.append(tok); grp = grp.commands[tok]
            if not isinstance(grp, click.Group):
                break
        elif names:
            break
    return " ".join(names)


class TimedGroup(click.Group):
    """Grupo raíz del CLI: cronometra cada orden y la apunta en el registro, sin tocar las órdenes."""

    def invoke(self, ctx: click.Context):
        argv = list(sys.argv[1:])
        cmd = command_path(self, argv)
        if not cmd or cmd in UNLOGGED or cmd.split()[0] in UNLOGGED or "--help" in argv or "-h" in argv:
            return super().invoke(ctx)
        t0 = time.perf_counter(); ok = False; err = None
        try:
            r = super().invoke(ctx)
            ok = True
            return r
        except click.exceptions.Exit as e:  # ctx.exit(): salida limpia (p. ej. --help de un subgrupo)
            ok = e.exit_code == 0; err = None if ok else str(e.exit_code)
            raise
        except SystemExit as e:  # raise SystemExit(msg) en las órdenes = error con mensaje; code 0/None = bien
            ok = e.code in (0, None); err = None if ok else str(e.code)
            raise
        except BaseException as e:  # noqa: BLE001
            err = f"{type(e).__name__}: {e}"
            raise
        finally:
            record(cmd, argv, time.perf_counter() - t0, ok, err)


def report(path: Path | None = None, rate: float | None = None) -> dict:
    """Resumen del registro: por orden (veces, segundos), total, notas y, con `rate` (coste por hora), una estimación."""
    p = path or log_path() or Path.cwd() / DEFAULT_REL
    if not p.exists():
        return {"log": str(p), "entries": 0, "commands": {}, "total_seconds": 0.0, "notes": [], "tokens": 0, "cost_notes": 0.0}
    cmds: dict[str, dict] = {}; notes = []; total = 0.0; tokens = 0; cost_notes = 0.0; minutes = 0.0; n = 0; first = last = None
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue
        n += 1
        first = first or e.get("ts"); last = e.get("ts") or last
        if "note" in e:
            notes.append(e); tokens += int(e.get("tokens", 0)); cost_notes += float(e.get("cost", 0.0)); minutes += float(e.get("minutes", 0.0))
            continue
        c = cmds.setdefault(e["cmd"], {"runs": 0, "seconds": 0.0, "failed": 0})
        c["runs"] += 1; c["seconds"] = round(c["seconds"] + float(e.get("s", 0.0)), 2); c["failed"] += 0 if e.get("ok") else 1
        total += float(e.get("s", 0.0))
    ordered = dict(sorted(cmds.items(), key=lambda kv: -kv[1]["seconds"]))
    res = {"log": str(p), "entries": n, "first": first, "last": last, "commands": ordered, "total_seconds": round(total, 2),
           "notes": notes, "tokens": tokens, "cost_notes": round(cost_notes, 2), "review_minutes": round(minutes, 1)}
    if rate:
        res["rate_per_hour"] = rate
        res["machine_cost"] = round(total / 3600.0 * rate, 2)
        res["estimated_cost"] = round(res["machine_cost"] + cost_notes + minutes / 60.0 * rate, 2)
    return res


def format_report(r: dict) -> str:
    lines = [f"  registro: {r['log']}  ({r['entries']} entradas" + (f", {r['first'][:16]} → {r['last'][:16]}" if r.get("first") else "") + ")"]
    if not r["commands"]:
        lines.append("  sin órdenes registradas todavía")
    else:
        w = max(len(c) for c in r["commands"]) + 2
        for c, v in r["commands"].items():
            lines.append(f"  {c:<{w}} {v['runs']:>3}×  {v['seconds']:>8.1f} s" + (f"  ({v['failed']} con error)" if v["failed"] else ""))
        lines.append(f"  {'total':<{w}}      {r['total_seconds']:>8.1f} s  = {r['total_seconds'] / 60:.1f} min de máquina")
    for nt in r["notes"]:
        extra = " · ".join(f"{k} {nt[k]}" for k in ("tokens", "cost", "minutes") if k in nt)
        lines.append(f"  nota: {nt['note']}" + (f"  [{extra}]" if extra else ""))
    if r.get("tokens"):
        lines.append(f"  tokens anotados: {r['tokens']:,}".replace(",", "."))
    if r.get("review_minutes"):
        lines.append(f"  minutos de persona anotados: {r['review_minutes']}")
    if "estimated_cost" in r:
        lines.append(f"  coste estimado a {r['rate_per_hour']}/h: máquina {r['machine_cost']} + notas {r['cost_notes']} + persona = {r['estimated_cost']}")
    return "\n".join(lines)
