"""Portada / miniatura: un fotograma del vídeo (o una imagen) + título con resaltado, insignia, logo de marca y un aro
opcional sobre el producto. Se construye como composición HyperFrames de un fotograma y se captura con
`hyperframes snapshot`, así usa las mismas fuentes y colores que el vídeo.

Tamaños: 1280×720 (miniatura de YouTube), 1080×1920 (portada de Shorts/Reels/TikTok), 1080×1080 (ficha de producto).
"""
from __future__ import annotations

import html
import json
import shutil
from pathlib import Path

from . import GSAP_VERSION, HYPERFRAMES_VERSION
from .build import DEFAULT_BRAND, highlight_line_height, resolve_brand
from .env import env_with_ffmpeg, npx, run


def _esc(s: str) -> str:
    return html.escape(str(s), quote=True)


def _layout(W: int, H: int, size: int | None) -> dict:
    """Zona del título y tamaño de fuente según el formato."""
    if H > W:      # vertical: título en el tercio superior, fuera de la interfaz del móvil
        return {"x": 60, "y": 200, "w": W - 120, "size": size or 104, "align": "center", "logo": "bottom"}
    if W == H:     # cuadrado: título abajo
        return {"x": 60, "y": H - 420, "w": W - 120, "size": size or 96, "align": "left", "logo": "top"}
    return {"x": 60, "y": 110, "w": int(W * 0.62), "size": size or 92, "align": "left", "logo": "bottom"}


def build_cover(image: str | Path, out_dir: str | Path, title: str, subtitle: str | None = None, badge: str | None = None,
                size: tuple[int, int] = (1280, 720), brand: str | dict | None = None, bg: str = "accent", darken: float = 0.35,
                ring: tuple[int, int, int] | None = None, focus: tuple[float, float] | None = None, zoom: float = 1.0,
                font_size: int | None = None, lines: list[str] | None = None) -> Path:
    """Escribe el proyecto HyperFrames de la portada en out_dir y devuelve su index.html."""
    W, H = size
    out = Path(out_dir); (out / "assets").mkdir(parents=True, exist_ok=True)
    img = Path(image)
    shutil.copy2(img, out / "assets" / img.name)
    b = dict(DEFAULT_BRAND); meta: dict = {}; brand_dir: Path | None = None
    if brand:
        if isinstance(brand, str):
            bp = resolve_brand(brand, out); meta = json.loads(bp.read_text(encoding="utf-8-sig")); brand_dir = bp.parent
        else:
            meta = brand
        b.update({k: v for k, v in meta.items() if k in b})
    logo_html = ""
    files = meta.get("logo_files") or {}
    variant = files.get("on_dark") or files.get("isotipo")
    if variant and brand_dir and (brand_dir / variant).exists():
        src = brand_dir / variant
        shutil.copy2(src, out / "assets" / src.name)
        logo_html = f'<img class="logo" src="assets/{src.name}" alt="">'
    lay = _layout(W, H, font_size)
    lines = lines or [title]
    # cada línea por encima de la siguiente: los descendentes (g, y, p) se pintan sobre la caja de abajo, no debajo
    title_html = "".join(f'<div style="position:relative; z-index:{100 - k}"><span class="hl">{_esc(t)}</span></div>' for k, t in enumerate(lines))
    sub_html = f'<div class="sub">{_esc(subtitle)}</div>' if subtitle else ""
    badge_html = f'<div class="badge">{_esc(badge)}</div>' if badge else ""
    ring_html = f'<div class="ring" style="left:{ring[0] - ring[2]}px; top:{ring[1] - ring[2]}px; width:{2 * ring[2]}px; height:{2 * ring[2]}px"></div>' if ring else ""
    fx, fy = focus or (0.5, 0.5)
    fl = meta.get("font_link") or ""
    font_link = f'<link rel="stylesheet" href="{fl}">' if fl else ""
    logo_pos = "right: 48px; bottom: 44px;" if lay["logo"] == "bottom" else "right: 48px; top: 44px;"
    css = f"""
      * {{ margin:0; padding:0; box-sizing:border-box; }}
      html, body {{ width:{W}px; height:{H}px; overflow:hidden; background:#000; }}
      :root {{ --accent:{b['accent']}; --ink:{b['ink']}; --paper:{b['paper']}; --sans:{b['sans']}; --mono:{b['mono']}; }}
      #root {{ position:relative; width:{W}px; height:{H}px; font-family:var(--sans); color:#fff; overflow:hidden; }}
      .bg {{ position:absolute; inset:0; width:100%; height:100%; object-fit:cover; object-position:{fx * 100:.1f}% {fy * 100:.1f}%; transform:scale({zoom}); transform-origin:{fx * 100:.1f}% {fy * 100:.1f}%; }}
      .shade {{ position:absolute; inset:0; background:linear-gradient({"180deg" if H > W else "90deg"}, rgba(0,0,0,{darken + 0.25}) 0%, rgba(0,0,0,{darken}) 45%, rgba(0,0,0,0) 80%); }}
      .title {{ position:absolute; left:{lay['x']}px; top:{lay['y']}px; width:{lay['w']}px; font-size:{lay['size']}px; font-weight:800; line-height:{highlight_line_height(lines, 1.12)}; letter-spacing:-0.035em; text-align:{lay['align']}; }}
      .title .hl {{ display:inline; padding:0.04em 0.28em 0.08em; box-decoration-break:clone; -webkit-box-decoration-break:clone; border-radius:0.16em; }}
      .title.accent .hl {{ background:var(--accent); color:var(--ink); }}
      .title.black .hl {{ background:rgba(10,10,10,.88); color:#fff; }}
      .title.white .hl {{ background:var(--paper); color:var(--ink); }}
      .title.none .hl {{ padding:0; color:#fff; text-shadow:0 6px 30px rgba(0,0,0,.8), 0 0 2px #000; }}
      .sub {{ margin-top:0.35em; font-size:0.42em; font-weight:600; letter-spacing:-0.02em; color:#fff; text-shadow:0 4px 18px rgba(0,0,0,.8); }}
      .badge {{ position:absolute; left:{lay['x']}px; top:{max(40, lay['y'] - 90)}px; font-family:var(--mono); font-size:{round(lay['size'] * 0.3)}px; letter-spacing:0.14em; text-transform:uppercase; padding:10px 18px; border-radius:999px; background:#fff; color:var(--ink); }}
      .logo {{ position:absolute; {logo_pos} height:{round(H * 0.06)}px; width:auto; filter:drop-shadow(0 4px 14px rgba(0,0,0,.6)); }}
      .ring {{ position:absolute; border:8px solid var(--accent); border-radius:50%; box-shadow:0 0 0 6px rgba(0,0,0,.35), inset 0 0 0 6px rgba(0,0,0,.25); }}
    """
    doc = f"""<!doctype html>
<html lang="es" data-resolution="{'portrait' if H > W else 'landscape'}">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width={W}, height={H}" />
    <script src="https://cdn.jsdelivr.net/npm/gsap@{GSAP_VERSION}/dist/gsap.min.js"></script>
    {font_link}
    <style>{css}</style>
  </head>
  <body>
    <!-- Portada generada por Frame28 (frame28 cover). -->
    <div id="root" data-composition-id="main" data-start="0" data-duration="1" data-width="{W}" data-height="{H}">
      <img class="bg" src="assets/{img.name}" alt="">
      <div class="shade"></div>
      {ring_html}
      {badge_html}
      <div class="title {bg}">{title_html}{sub_html}</div>
      {logo_html}
    </div>
    <script>
      const tl = gsap.timeline({{ paused: true }});
      window.__timelines = window.__timelines || {{}};
      window.__timelines["main"] = tl;
      tl.seek(0);
    </script>
  </body>
</html>
"""
    (out / "index.html").write_text(doc, encoding="utf-8")
    (out / "hyperframes.json").write_text(json.dumps({
        "$schema": "https://hyperframes.heygen.com/schema/hyperframes.json",
        "registry": "https://raw.githubusercontent.com/heygen-com/hyperframes/main/registry",
        "paths": {"blocks": "compositions", "components": "compositions/components", "assets": "assets"}}, indent=2), encoding="utf-8")
    (out / "package.json").write_text(json.dumps({"name": out.name, "private": True, "type": "module"}, indent=2), encoding="utf-8")
    return out / "index.html"


def snapshot(project: str | Path, out_png: str | Path) -> Path:
    """Captura el fotograma 0 del proyecto con `hyperframes snapshot` y lo deja en out_png."""
    project = Path(project).resolve(); out = Path(out_png).resolve(); out.parent.mkdir(parents=True, exist_ok=True)
    snaps = project / "snapshots"
    if snaps.exists():
        shutil.rmtree(snaps)
    r = run([npx(), "--yes", f"hyperframes@{HYPERFRAMES_VERSION}", "snapshot", "--at", "0", "--no-end", "--describe", "false",
             "--no-browser-gpu", "-o", str(snaps), str(project)], cwd=str(project), env=env_with_ffmpeg(), timeout=300)
    pngs = sorted(snaps.glob("*.png")) if snaps.exists() else []
    if r.returncode != 0 or not pngs:
        raise SystemExit("hyperframes snapshot falló:\n" + (r.stdout + r.stderr)[-1200:])
    shutil.copy2(pngs[0], out)
    return out


def make_cover(video: str | Path | None, out_png: str | Path, title: str, at: float | None = None, image: str | Path | None = None,
               work_dir: str | Path | None = None, **kw) -> dict:
    """Extrae el fotograma (`at`) o usa `image`, construye la portada y la captura. Devuelve rutas."""
    out = Path(out_png)
    work = Path(work_dir) if work_dir else out.with_suffix("").with_name(out.stem + "_cover")
    work.mkdir(parents=True, exist_ok=True)
    if image is None:
        if video is None or at is None:
            raise SystemExit("Hace falta --at (segundo del vídeo) o --image")
        from .media import frame_at
        image = frame_at(video, float(at), work / "frame.png")
    index = build_cover(image, work, title, **kw)
    png = snapshot(work, out)
    return {"cover": str(png), "project": str(work), "frame": str(image), "index": str(index)}
