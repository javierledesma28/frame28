"""Prueba de `frame28 brand from-site` sobre una lista de webs (F28-299).

    python scripts/prueba-from-site.py <lista.txt> <carpeta de salida>

`lista.txt`: un dominio o URL por línea (la lista de marcas candidatas es privada: vive fuera del repo). Cada descarga se
guarda en `<salida>/cache/` una sola vez, así el código se puede iterar sin volver a bajar nada ni molestar a las webs.
Imprime una tabla numerada (sin dominios) con la confianza, el acento o «a confirmar», sus fuentes, la fuente tipográfica
y el logo, y al final los totales. Los JSON completos quedan en `<salida>/pNN.result.json`.

Línea base del 2026-10-07 (motor v0.5.1, 20 webs DTC): alta 5 · media 14 · baja 1; acento solo de widgets de reseñas en 5;
fuente «var» en 6. Tras F28-299: 0 acentos de widgets, 0 «var», fuente resuelta en 18, alta 6 y 14 «a confirmar» con candidatos.
"""
import hashlib
import json
import pathlib
import sys
import time

from frame28 import brandsite as S

if len(sys.argv) < 3:
    raise SystemExit(__doc__)
lista, out = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
cache = out / "cache"
cache.mkdir(parents=True, exist_ok=True)
real_get = S._get


def cached_get(url, binary=False, timeout=30, max_bytes=S.MAX_PAGE, public_only=True):
    key = hashlib.sha1(url.encode()).hexdigest()
    f = cache / (key + (".bin" if binary else ".txt"))
    e = cache / (key + ".err")
    if f.exists():
        return f.read_bytes() if binary else f.read_text(encoding="utf-8")
    if e.exists():
        raise OSError(e.read_text(encoding="utf-8"))
    try:
        data = real_get(url, binary, timeout, max_bytes, public_only)
    except Exception as ex:  # noqa: BLE001
        e.write_text(f"{type(ex).__name__}: {ex}", encoding="utf-8")
        raise
    if binary:
        f.write_bytes(data)
    else:
        f.write_text(data, encoding="utf-8")
    return data


S._get = cached_get
sites = [ln.strip() for ln in lista.read_text(encoding="utf-8").splitlines() if ln.strip() and not ln.startswith("#")]
rows = []
for i, site in enumerate(sites, 1):
    url = site if site.startswith("http") else f"https://{site}/"
    t = time.time()
    try:
        r = S.from_site(url, f"p{i:02d}", out)
    except Exception as ex:  # noqa: BLE001
        r = {"error": f"{type(ex).__name__}: {ex}"}
    r["seconds"] = round(time.time() - t, 1)
    (out / f"p{i:02d}.result.json").write_text(json.dumps(r, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
    if "error" in r:
        rows.append((f"{i:02d}", "ERROR", r["error"][:60], "", "", "", "", ""))
        continue
    lg = r.get("logo") or {}
    rows.append((f"{i:02d}", r["confidence"], str(r["accent"]), r["accent_status"],
                 " / ".join(s[:22] for s in r["accent_sources"][:3]), str(r["font"]),
                 f"{lg.get('kind')}/{len(lg.get('files') or {})}", ",".join(r.get("logo_colors", [])[:3])))

hdr = ("#", "conf", "acento", "estado", "fuentes del acento", "fuente", "logo", "colores logo")
w = [max(len(str(x[k])) for x in rows + [hdr]) for k in range(len(hdr))]
for row in [hdr] + rows:
    print("  ".join(str(c).ljust(w[k]) for k, c in enumerate(row)))
conf = [r[1] for r in rows]
print(f"\nalta {conf.count('alta')} / media {conf.count('media')} / baja {conf.count('baja')} / error {conf.count('ERROR')}")
print("acento desde el logo:", sum(1 for r in rows if "logo" in r[4]), "/ fuente resuelta:",
      sum(1 for r in rows if r[5] not in ("None", "var", "")), "/ a confirmar:", sum(1 for r in rows if r[3] == "a confirmar"))
