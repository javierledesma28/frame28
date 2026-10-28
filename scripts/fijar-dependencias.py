# -*- coding: utf-8 -*-
"""Versiones exactas del motor (F28-91; solo biblioteca estándar + uv).

El extra `probado` de plugin/cli/pyproject.toml fija cada paquete que instalan las dependencias del CLI, en todas las
plataformas, con la versión con la que pasaron las pruebas. El instalador, `uv tool upgrade` y las órdenes de
`frame28 doctor` instalan "frame28[probado] @ git+…", así que un cliente recibe exactamente esa combinación, y las
pruebas corren con ella (`uv run --extra probado --group dev pytest`). Sin esto, una instalación limpia resolvía lo
último de cada librería: el 2026-10-19 eran 20 paquetes distintos de los probados, varios de versión mayor.

El extra `gpu` hace lo mismo con lo que añade (F28-458): sus rangos, escritos a mano, y debajo la versión exacta de cada
paquete de CUDA y de onnxruntime-gpu; lo que comparte con `probado` (numpy, protobuf…) queda en `probado`. Se instala
siempre con él ("frame28[gpu,probado]"), así que quien acepta la aceleración recibe también la combinación probada.

    python scripts/fijar-dependencias.py               # comprueba los extras; sale con 1 si falta, sobra o choca algo
    python scripts/fijar-dependencias.py --escribir    # los rehace conservando las versiones fijadas (tras tocar dependencies)
    python scripts/fijar-dependencias.py --actualizar  # lo rehace con lo último dentro de los techos

Después de --escribir o --actualizar: `uv run --extra probado --group dev pytest` en plugin/cli y, si pasa, commit.
Salida: 0 bien, 1 el extra no cuadra, 2 no se pudo resolver (sin uv o sin red).
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PYPROJECT = ROOT / "plugin" / "cli" / "pyproject.toml"
EXTRA = "probado"
PYTHON_MIN = "3.11"            # requires-python del CLI: la resolución universal cubre 3.11 en adelante
GPU = "gpu"                    # sus rangos (líneas sin `==`) y, debajo, las versiones exactas de lo que añade a `probado`
PIN = re.compile(r"^(?P<nombre>[A-Za-z0-9][A-Za-z0-9._-]*)==(?P<version>[^\s;]+)(?:\s*;\s*(?P<marca>.+))?$")

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        pass


def canon(nombre: str) -> str:
    return re.sub(r"[-_.]+", "-", nombre).lower()


def dependencias(texto: str) -> list[str]:
    """Las dependencias directas del CLI (`[project] dependencies`)."""
    m = re.search(r"^dependencies = \[\n(.*?)^\]", texto, re.M | re.S)
    if not m:
        raise SystemExit("pyproject.toml sin `dependencies = [`")
    return re.findall(r'^\s*"([^"]+)",?\s*$', m.group(1), re.M)


def bloque(extra: str) -> re.Pattern:
    return re.compile(rf'^(?P<cab>{extra} = \[\n)(?P<cuerpo>.*?)^\]', re.M | re.S)


def fijadas(texto: str, extra: str = EXTRA) -> list[str]:
    """Las líneas de un extra (por defecto `probado`), tal cual."""
    m = bloque(extra).search(texto)
    if not m:
        raise SystemExit(f"pyproject.toml sin el extra `{extra} = [`")
    return re.findall(r'^\s*"([^"]+)",?\s*$', m.group("cuerpo"), re.M)


def rangos_gpu(texto: str) -> list[str]:
    """Las dependencias del extra gpu con su rango (las que se escriben a mano)."""
    return [p for p in fijadas(texto, GPU) if "==" not in p]


def pins_gpu(texto: str) -> list[str]:
    """Las versiones exactas del extra gpu: las de las pruebas de lo que no fija ya `probado` (F28-458)."""
    return [p for p in fijadas(texto, GPU) if "==" in p]


def con_fijadas(texto: str, pins: list[str], extra: str = EXTRA, delante: list[str] | None = None) -> str:
    """El pyproject con un extra sustituido: `delante` tal cual y los pins en orden alfabético, uno por línea."""
    lineas = list(delante or []) + sorted(pins, key=lambda p: (canon(p.split("==")[0]), p))
    cuerpo = "".join(f'  "{p}",\n' for p in lineas)
    return bloque(extra).sub(lambda m: m.group("cab") + cuerpo + "]", texto, count=1)


def nombre_version(pin: str) -> tuple[str, str] | None:
    m = PIN.match(pin.strip())
    return (canon(m.group("nombre")), m.group("version")) if m else None


def problemas(deps: list[str], pins: list[str], resueltas: list[str]) -> list[str]:
    """Qué no cuadra entre el extra y una resolución de las dependencias limitada por él (`resueltas`): líneas mal
    formadas, dependencias directas sin fijar, paquetes que la resolución pide y el extra no fija, y fijados que ya
    nadie pide. Comparar nombre y versión basta: las marcas solo reparten versiones por plataforma o Python."""
    out = [f"línea sin `nombre==versión`: {p}" for p in pins if not nombre_version(p)]
    fij = {nv for p in pins if (nv := nombre_version(p))}
    res = {nv for p in resueltas if (nv := nombre_version(p))}
    nombres = {n for n, _ in fij}
    for d in deps:
        n = canon(re.split(r"[\s<>=!~;\[]", d, maxsplit=1)[0])
        if n not in nombres:
            out.append(f"dependencia directa sin fijar: {n}")
    out += [f"sin fijar: {n}=={v}" for n, v in sorted(res - fij)]
    out += [f"fijado y ya no lo pide nadie (o choca con los rangos): {n}=={v}" for n, v in sorted(fij - res)]
    return out


def resolver(deps: list[str], *, preferir: list[str] | None = None, restringir: list[str] | None = None,
             actualizar: bool = False) -> list[str]:
    """`uv pip compile` universal de las dependencias: con `restringir`, limitada a esas versiones; con `preferir`,
    quedándose con ellas mientras quepan (y añadiendo lo que falte)."""
    uv = shutil.which("uv")
    if not uv:
        print("No encuentro uv en el PATH: lo necesito para resolver las dependencias (https://docs.astral.sh/uv/).", file=sys.stderr)
        sys.exit(2)
    with tempfile.TemporaryDirectory() as d:
        req, out = Path(d) / "deps.in", Path(d) / "probado.txt"
        req.write_text("\n".join(deps) + "\n", encoding="utf-8")
        cmd = [uv, "pip", "compile", str(req), "--universal", "--python-version", PYTHON_MIN, "--no-header",
               "--no-annotate", "--quiet", "-o", str(out)]
        if restringir is not None:
            con = Path(d) / "restricciones.txt"
            con.write_text("\n".join(restringir) + "\n", encoding="utf-8")
            cmd += ["-c", str(con)]
        if preferir:
            out.write_text("\n".join(preferir) + "\n", encoding="utf-8")
        if actualizar:
            cmd.append("--upgrade")
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        if r.returncode != 0:
            print("uv no pudo resolver las dependencias con esas versiones:\n" + (r.stderr or r.stdout)[-1500:], file=sys.stderr)
            sys.exit(2 if restringir is None else 1)
        return [ln.strip() for ln in out.read_text(encoding="utf-8").splitlines() if ln.strip() and not ln.lstrip().startswith("#")]


def solo_gpu(resueltas: list[str], pins: list[str]) -> list[str]:
    """De una resolución con el extra gpu, lo que no fija ya `probado` (CUDA y onnxruntime-gpu): eso fija el extra gpu,
    que siempre se instala junto a `probado` ("frame28[gpu,probado]")."""
    base = {nv for p in pins if (nv := nombre_version(p))}
    return [p for p in resueltas if nombre_version(p) not in base]


def main(argv: list[str]) -> int:
    texto = PYPROJECT.read_text(encoding="utf-8")
    deps, pins = dependencias(texto), fijadas(texto)
    rangos, gpu = rangos_gpu(texto), pins_gpu(texto)
    if "--escribir" in argv or "--actualizar" in argv:
        act = "--actualizar" in argv
        nuevas = resolver(deps, preferir=pins, actualizar=act)
        # el extra gpu, con `probado` ya fijado: sus paquetes comunes (numpy, protobuf…) son los mismos
        nuevas_gpu = solo_gpu(resolver(deps + rangos, preferir=nuevas + gpu, restringir=nuevas, actualizar=act), nuevas)
        texto = con_fijadas(con_fijadas(texto, nuevas), nuevas_gpu, GPU, delante=rangos)
        PYPROJECT.write_bytes(texto.replace("\r\n", "\n").encode("utf-8"))
        for extra, a, b in ((EXTRA, pins, nuevas), (GPU, gpu, nuevas_gpu)):
            antes = {nv for p in a if (nv := nombre_version(p))}
            despues = {nv for p in b if (nv := nombre_version(p))}
            print(f"extra `{extra}`: {len(b)} versiones; {len(despues - antes)} nuevas, {len(antes - despues)} retiradas.")
            for n, v in sorted(despues - antes):
                print(f"  + {n}=={v}")
        print("Ahora: cd plugin/cli && uv run --extra probado --group dev pytest")
        return 0
    malos = problemas(deps, pins, resolver(deps, restringir=pins))
    malos += [f"gpu: {m}" for m in problemas(rangos, gpu, solo_gpu(resolver(deps + rangos, restringir=pins + gpu), pins))]
    for m in malos:
        print("  ✗ " + m)
    if malos:
        print(f"Los extras `{EXTRA}` y `{GPU}` no cuadran con las dependencias: python scripts/fijar-dependencias.py --escribir")
        return 1
    print(f"extras `{EXTRA}` y `{GPU}`: {len(pins)} y {len(gpu)} versiones exactas, completas y dentro de los rangos.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
