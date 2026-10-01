"""Marca a partir de una web: colores, fuente y logo del sitio del cliente → brand.json listo para el storyboard.

Lo que hacía a mano el director con el primer caso de marca: bajar la portada, contar los colores hexadecimales más usados,
leer las variables CSS de botones (Shopify y similares las exponen), la fuente más repetida, el logo (`<img>` con
"logo" en la ruta o el `og:image` como respaldo), y generar variantes del logo para fondo oscuro y de acento.
Es una propuesta: el agente la revisa con el usuario (`frame28 brand show`) antes de usarla.
"""
from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path

UA = "Mozilla/5.0 (Frame28 brand research; +https://frame28.t28.io)"
NEUTRAL_MAX_SAT = 0.12   # por debajo de esto un color es gris/blanco/negro


def _get(url: str, binary: bool = False, timeout: int = 30):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = r.read()
    return data if binary else data.decode("utf-8", errors="replace")


def _hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _sat_lum(rgb: tuple[int, int, int]) -> tuple[float, float]:
    r, g, b = (c / 255 for c in rgb)
    mx, mn = max(r, g, b), min(r, g, b)
    lum = (mx + mn) / 2
    sat = 0.0 if mx == mn else (mx - mn) / (1 - abs(2 * lum - 1))
    return sat, lum


def analyze_html(html: str, base_url: str) -> dict:
    """Colores (frecuencia), variables CSS de color, fuentes y candidatos a logo, sin descargar nada más."""
    hexes = [h.lower() for h in re.findall(r"#([0-9a-fA-F]{6})\b", html)]
    hexes = ["#" + h for h in hexes if h.lower() not in ("000000", "ffffff")]
    counts = Counter(hexes)
    # variables CSS tipo "--color-button: 251,176,76" (Shopify) o "--primary: #hex"
    css_vars = {}
    for name, val in re.findall(r"--([a-z0-9-]*(?:button|primary|accent|brand|highlight)[a-z0-9-]*)\s*:\s*([^;}]{3,40})", html, re.I):
        v = val.strip()
        m = re.match(r"^(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})$", v)
        if m:
            v = "#%02x%02x%02x" % tuple(int(x) for x in m.groups())
        if re.match(r"^#[0-9a-fA-F]{6}$", v):
            css_vars.setdefault(name.lower(), v.lower())
    fonts = Counter(f.strip().strip("'\"") for f in re.findall(r"font-family\s*:\s*['\"]?([A-Za-z0-9 ]{3,30})['\"]?", html)
                    if f.strip().lower() not in ("inherit", "sans-serif", "serif", "monospace", "system-ui", "initial"))
    logos = []
    for m in re.findall(r"""(?:src|href|content)=["']([^"']*logo[^"']*\.(?:svg|png|webp|jpg)[^"']*)["']""", html, re.I):
        logos.append(urllib.parse.urljoin(base_url, m.replace("&amp;", "&")))
    og = re.search(r'property=["\']og:image["\']\s+content=["\']([^"\']+)', html)
    og_image = urllib.parse.urljoin(base_url, og.group(1)) if og else None
    title = re.search(r"<title>([^<]{1,120})</title>", html, re.I)
    desc = re.search(r'name=["\']description["\']\s+content=["\']([^"\']{1,300})', html, re.I)
    return {"colors": counts.most_common(20), "css_vars": css_vars, "fonts": fonts.most_common(5),
            "logos": list(dict.fromkeys(logos))[:5], "og_image": og_image,
            "title": title.group(1).strip() if title else "", "description": desc.group(1).strip() if desc else ""}


def propose(analysis: dict) -> dict:
    """Acento = variable CSS de botón si existe; si no, el color saturado más frecuente. Tinta = el oscuro más frecuente."""
    accent = None
    for key in ("color-button", "color-primary", "primary", "accent", "brand", "color-accent", "color-brand"):
        for name, v in analysis["css_vars"].items():
            if key in name and "text" not in name:
                accent = v; break
        if accent:
            break
    darks, saturated = [], []
    for h, n in analysis["colors"]:
        sat, lum = _sat_lum(_hex_to_rgb(h))
        if lum < 0.22:
            darks.append((h, n))
        elif sat > NEUTRAL_MAX_SAT and 0.25 < lum < 0.8:
            saturated.append((h, n))
    if not accent and saturated:
        accent = saturated[0][0]
    ink = darks[0][0] if darks else "#111111"
    font = analysis["fonts"][0][0] if analysis["fonts"] else None
    return {"accent": accent or "#EA77A1", "ink": ink, "font": font,
            "secondary": [h for h, _ in saturated[:4] if h != accent], "logo": (analysis["logos"] or [analysis["og_image"]])[0] if (analysis["logos"] or analysis["og_image"]) else None}


def logo_variants(png_path: Path, out_dir: Path, ink: str) -> dict:
    """Del logo original genera on_dark (claro si el logo es oscuro), on_accent (tinta) y on_light (original)."""
    import cv2
    import numpy as np

    im = cv2.imread(str(png_path), cv2.IMREAD_UNCHANGED)
    out_dir.mkdir(parents=True, exist_ok=True)
    files = {}
    if im is None:
        return files
    if im.ndim == 2:
        im = cv2.cvtColor(im, cv2.COLOR_GRAY2BGRA)
    elif im.shape[2] == 3:
        im = cv2.cvtColor(im, cv2.COLOR_BGR2BGRA)
    op = im[:, :, 3] > 128
    if op.sum() == 0:
        return files
    mean = im[:, :, :3][op].mean(axis=0)  # BGR
    lum = (0.114 * mean[0] + 0.587 * mean[1] + 0.299 * mean[2]) / 255
    r, g, b = _hex_to_rgb(ink)
    cv2.imwrite(str(out_dir / "on_light.png"), im); files["on_light"] = out_dir.name + "/on_light.png"
    cv2.imwrite(str(out_dir / "isotipo.png"), im); files["isotipo"] = out_dir.name + "/isotipo.png"
    dark = im.copy(); dark[:, :, :3][op] = (b, g, r)
    cv2.imwrite(str(out_dir / "on_accent.png"), dark); files["on_accent"] = out_dir.name + "/on_accent.png"
    if lum < 0.45:  # logo oscuro: en fondo oscuro, en blanco
        white = im.copy(); white[:, :, :3][op] = 255
        cv2.imwrite(str(out_dir / "on_dark.png"), white); files["on_dark"] = out_dir.name + "/on_dark.png"
    else:
        cv2.imwrite(str(out_dir / "on_dark.png"), im); files["on_dark"] = out_dir.name + "/on_dark.png"
    return files


def from_site(url: str, name: str, out_dir: str | Path = "brands", logo_url: str | None = None, tagline: str | None = None) -> dict:
    """Descarga la portada, propone la marca y escribe <out_dir>/<name>.json (+ logos en <out_dir>/<name>/)."""
    from .build import BUNDLED_BRANDS

    html = _get(url)
    an = analyze_html(html, url)
    prop = propose(an)
    base = json.loads((BUNDLED_BRANDS / "think28.json").read_text(encoding="utf-8"))
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    host = urllib.parse.urlparse(url).netloc.replace("www.", "")
    brand = {**base, "name": name, "site": host, "tagline": tagline or "", "endorsement": host, "source": url,
             "accent": prop["accent"], "ink": prop["ink"], "paper": "#FFFFFF", "grey": "#666666", "border": prop["ink"],
             "logo_files": {}}
    if prop["font"]:
        fam = prop["font"]
        brand["sans"] = f'{fam}, Inter, "Segoe UI", Arial, sans-serif'
        brand["font_link"] = f"https://fonts.googleapis.com/css2?family={urllib.parse.quote(fam)}:wght@400;600;800&family=Space+Mono:wght@400;700&display=swap"
    logo_src = logo_url or prop["logo"]
    logo_info = {"url": logo_src, "files": {}}
    if logo_src:
        try:
            data = _get(logo_src, binary=True, timeout=60)
            ext = ".svg" if logo_src.lower().split("?")[0].endswith(".svg") else ".png"
            ldir = out / name; ldir.mkdir(parents=True, exist_ok=True)
            raw = ldir / f"original{ext}"
            raw.write_bytes(data)
            if ext == ".svg":
                files = {k: f"{name}/original.svg" for k in ("isotipo", "on_dark", "on_light", "on_accent")}
            else:
                files = logo_variants(raw, ldir, prop["ink"])
            brand["logo_files"] = files; logo_info["files"] = files
        except Exception as e:  # el logo es opcional
            logo_info["error"] = str(e)
    path = out / f"{name}.json"
    path.write_text(json.dumps(brand, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"brand": str(path), "accent": brand["accent"], "ink": brand["ink"], "font": prop["font"],
            "secondary": prop["secondary"], "logo": logo_info, "title": an["title"], "description": an["description"],
            "top_colors": an["colors"][:8], "css_vars": an["css_vars"], "fonts": an["fonts"]}
