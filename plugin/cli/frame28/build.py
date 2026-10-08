"""Generador: storyboard.json → proyecto HyperFrames (index.html + assets).

El LLM decide el storyboard (qué técnica, qué texto, cuándo y dónde). Este módulo lo convierte de forma
determinista en HTML + CSS + una timeline GSAP, siguiendo las reglas que verificamos en la PoC:
capas con z-index explícito, todo elemento temporizado con id, posiciones inline, fades cortos.
"""
from __future__ import annotations

import html
import re
import json
import math
import shutil
from pathlib import Path

from . import GSAP_VERSION, HYPERFRAMES_VERSION

OVERLAY_TYPES = {"lower_third", "box", "kinetic", "behind", "pointer", "card", "list_focus", "card_words", "image", "brand_card", "chart", "draw", "broll",
                 "hook", "cta", "steps", "before_after"}

DEFAULT_BRAND = {
    "accent": "#EA77A1",
    "ink": "#111111",
    "paper": "#FFFFFC",
    "grey": "#80807D",
    "sans": '"Helvetica Neue", Inter, "Segoe UI", Arial, sans-serif',
    "mono": '"Cascadia Mono", Consolas, "Courier New", monospace',
    "caption_font_size": 40,
}

CSS = """
      * { margin: 0; padding: 0; box-sizing: border-box; }
      html, body { width: {W}px; height: {H}px; overflow: hidden; background: #000; }
      :root { --accent: {accent}; --on-accent: {on_accent}; --ink: {ink}; --paper: {paper}; --grey: {grey}; --sans: {sans}; --mono: {mono}; }
      #root { position: relative; width: {W}px; height: {H}px; font-family: var(--sans); color: #fff; }
      .clip { position: absolute; inset: 0; }
      video.cover { width: 100%; height: 100%; object-fit: cover; }
      .c { position: absolute; width: 18px; height: 18px; border: 0 solid currentColor; }
      .tl { top: -6px; left: -6px; border-top-width: 3px; border-left-width: 3px; }
      .tr { top: -6px; right: -6px; border-top-width: 3px; border-right-width: 3px; }
      .bl { bottom: -6px; left: -6px; border-bottom-width: 3px; border-left-width: 3px; }
      .br { bottom: -6px; right: -6px; border-bottom-width: 3px; border-right-width: 3px; }
      .box { position: absolute; padding: 10px 26px; font-size: 54px; font-weight: 500; letter-spacing: -0.03em; color: #fff; background: rgba(0,0,0,.45); white-space: nowrap; opacity: 0; }
      .lower { position: absolute; font-family: var(--mono); font-size: 34px; color: #fff; opacity: 0; width: max-content; max-width: calc(100% - 40px); }
      .lower .line { overflow: hidden; white-space: nowrap; border: 1.5px solid rgba(255,255,255,.9); padding: 12px 22px; background: rgba(0,0,0,.45); }
      .lower .line + .line { border-top: 0; }
      .lower .mask { display: inline-block; white-space: nowrap; vertical-align: bottom; clip-path: inset(0 100% 0 0); }
      .lower .cur { color: var(--accent); }
      .lower .c { width: 18px; height: 18px; } .lower .tl { top: -9px; left: -9px; } .lower .br { bottom: -9px; right: -9px; }
      .kin { position: absolute; font-weight: 600; line-height: 1.02; letter-spacing: -0.045em; text-shadow: 0 6px 30px rgba(0,0,0,.55); }
      .kin .w { display: inline-block; opacity: 0; margin-right: 0.22em; }
      .kin.onlight { text-shadow: 0 2px 6px rgba(255,255,255,.75), 0 0 24px rgba(255,255,255,.6); }
      .accent { color: var(--accent); }
      .behind { display: flex; align-items: center; justify-content: center; }
      .behind .w { font-weight: 700; letter-spacing: -0.05em; white-space: nowrap; text-shadow: 0 8px 40px rgba(0,0,0,.35); opacity: 0; }
      .conn { position: absolute; height: 3px; background: #fff; transform-origin: left center; width: 0; }
      .dot { position: absolute; width: 18px; height: 18px; border-radius: 50%; background: #fff; box-shadow: 0 0 0 6px rgba(255,255,255,.25); transform: scale(0); }
      .card { display: flex; flex-direction: column; align-items: center; justify-content: center; }
      .card.black { background: #000; color: #fff; }
      .card.white { background: var(--paper); color: var(--ink); }
      .card.accent { background: var(--accent); color: var(--on-accent); }
      .card .big { font-weight: 600; letter-spacing: -0.05em; opacity: 0; text-align: center; }
      .card .small { color: #bdbdb8; letter-spacing: -0.03em; margin-top: 10px; opacity: 0; }
      .card.white .small { color: var(--grey); }
      .list { position: relative; display: grid; row-gap: 26px; letter-spacing: -0.04em; align-items: center; }
      .list .item { color: var(--grey); opacity: 0; }
      .list .lab { grid-column: 1; }
      .list .newlabel { position: absolute; left: 0; top: 0; display: flex; align-items: center; gap: 22px; color: var(--ink); }
      .list .newlabel .icon { border: 2px solid #c9c9c4; border-radius: 22px; display: flex; align-items: center; justify-content: center; }
      .list .newlabel .icon i { width: 22px; height: 22px; border: 4px solid var(--ink); border-radius: 50%; }
      .cw .row { display: flex; gap: 0.28em; font-weight: 600; letter-spacing: -0.045em; justify-content: center; }
      .cw .w { opacity: 0; }
      .cw .w b { color: var(--accent); font-weight: 600; }
      .img { position: absolute; opacity: 0; box-shadow: 0 30px 80px rgba(0,0,0,.45); border-radius: 18px; overflow: hidden; }
      .img img { display: block; width: 100%; height: auto; }
      .lt-logo { height: 30px; width: auto; vertical-align: -6px; margin-right: 4px; }
      .bc .bc-logo { opacity: 0; margin-bottom: 40px; }
      .bc .bc-title { opacity: 0; font-weight: 800; font-size: 120px; letter-spacing: -0.035em; }
      .bc .bc-sub { opacity: 0; font-size: 44px; font-family: var(--mono); letter-spacing: 0.2em; text-transform: uppercase; margin-top: 18px; color: var(--grey); }
      .bc .bc-endorse { opacity: 0; position: absolute; bottom: 64px; font-family: var(--mono); font-size: 26px; letter-spacing: 0.12em; color: var(--grey); }
      .bc.accent .bc-sub, .bc.accent .bc-endorse { color: rgba(10,10,10,.7); }
      /* chart: barras horizontales y contador */
      .chart { display: flex; flex-direction: column; justify-content: center; align-items: flex-start; padding: 90px 140px; }
      .chart.panel { position: absolute; inset: auto; background: rgba(10,10,10,.82); border-radius: 22px; padding: 36px 44px; color: #fff; }
      .chart .ch-title { font-weight: 600; letter-spacing: -0.03em; font-size: 56px; opacity: 0; }
      .chart .ch-sub { font-family: var(--mono); font-size: 24px; margin-top: 8px; opacity: 0.85; }
      .chart .rows { margin-top: 44px; position: relative; width: 100%; }
      .chart .row { display: flex; align-items: center; height: 74px; position: relative; opacity: 0; }
      .chart .row.hero { isolation: isolate; }
      .chart .grp { width: 200px; font-family: var(--mono); font-size: 24px; }
      .chart .grp span { background: var(--ink); color: var(--accent); padding: 2px 8px; }
      .chart.black .grp span, .chart.panel .grp span { background: var(--accent); color: var(--on-accent); }
      .chart .lbl { width: 320px; font-family: var(--mono); font-size: 26px; text-align: right; padding-right: 28px; white-space: nowrap; }
      .chart .track { position: relative; height: 34px; flex: 0 0 auto; }
      .chart .fill { position: absolute; left: 0; top: 0; height: 34px; background: rgba(10,10,10,.55); transform-origin: left center; transform: scaleX(0); }
      .chart.black .fill, .chart.panel .fill { background: rgba(255,255,255,.45); }
      .chart .row.hero .fill { background: var(--ink); }
      .chart.black .row.hero .fill, .chart.panel .row.hero .fill { background: var(--accent); }
      .chart .val { position: absolute; top: 0; line-height: 34px; font-family: var(--mono); font-size: 26px; opacity: 0; white-space: nowrap; }
      .chart .hero-box { position: absolute; left: -24px; right: -24px; top: 4px; bottom: 4px; background: var(--paper); z-index: -1; opacity: 0; color: var(--ink); }
      .chart.black .hero-box, .chart.panel .hero-box { background: rgba(255,255,255,.12); color: #fff; }
      .chart .hero-box .c { border-color: currentColor; }
      .counter { display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; }
      .counter .num { font-weight: 800; letter-spacing: -0.05em; font-size: 300px; line-height: 1; opacity: 0; }
      .counter .num b { color: var(--accent); font-weight: 800; }
      .counter.accent .num b { color: var(--on-accent); opacity: .55; }
      .counter .lab { font-size: 64px; letter-spacing: -0.03em; margin-top: 12px; opacity: 0; }
      .counter .sub { font-family: var(--mono); font-size: 26px; letter-spacing: 0.12em; text-transform: uppercase; margin-top: 26px; opacity: 0.8; }
      .w .wi { display: inline-block; }
      .w.rise { overflow: hidden; vertical-align: bottom; padding-bottom: 0.08em; margin-bottom: -0.08em; }
      .draw { position: absolute; opacity: 0; }
      /* b-roll: a pantalla completa (tapa al hablante) o como ventana (pip) */
      .broll { position: absolute; overflow: hidden; opacity: 0; background: #000; }
      .broll.full { inset: 0; }
      .broll.pip { border-radius: 18px; box-shadow: 0 30px 80px rgba(0,0,0,.45); }
      .broll video, .broll img { display: block; width: 100%; height: 100%; object-fit: cover; transform-origin: center center; }
      .broll .credit { position: absolute; right: 22px; top: 16px; font-family: var(--mono); font-size: 20px; letter-spacing: 0.08em; color: rgba(255,255,255,.75); text-shadow: 0 2px 8px rgba(0,0,0,.8); }
      .broll .cap { position: absolute; left: 0; right: 0; bottom: 0; padding: 18px 28px; font-weight: 600; font-size: 40px; letter-spacing: -0.03em; color: #fff; background: linear-gradient(transparent, rgba(0,0,0,.7)); }
      .draw svg { width: 100%; height: 100%; overflow: visible; }
      .draw svg * { fill: none; stroke: currentColor; stroke-linecap: round; stroke-linejoin: round; }
      /* venta: gancho, CTA, progreso de pasos, antes/después */
      .hook { position: absolute; text-align: center; font-weight: 800; line-height: 1.15; letter-spacing: -0.03em; opacity: 0; }
      .hook .hl { display: inline; padding: 0.04em 0.3em 0.08em; box-decoration-break: clone; -webkit-box-decoration-break: clone; border-radius: 0.18em; }
      .hook.accent .hl { background: var(--accent); color: var(--on-accent); }
      .hook.black .hl { background: rgba(10,10,10,.88); color: #fff; }
      .hook.white .hl { background: var(--paper); color: var(--ink); }
      .hook.none .hl { padding: 0; color: #fff; text-shadow: 0 4px 24px rgba(0,0,0,.7), 0 0 2px #000; }
      .cta { position: absolute; display: flex; align-items: center; gap: 36px; padding: 34px 44px; border-radius: 26px; opacity: 0; }
      .cta.accent { background: var(--accent); color: var(--on-accent); }
      .cta.black { background: rgba(10,10,10,.92); color: #fff; }
      .cta.white { background: var(--paper); color: var(--ink); }
      .cta .col { display: flex; flex-direction: column; gap: 10px; min-width: 0; flex: 1 1 auto; }
      .cta .title { font-weight: 800; font-size: 44px; letter-spacing: -0.03em; line-height: 1.05; }
      .cta .price { font-weight: 800; font-size: 96px; letter-spacing: -0.05em; line-height: 1; }
      .cta .price s { font-weight: 500; font-size: 0.45em; opacity: .6; margin-left: 0.3em; letter-spacing: -0.02em; }
      .cta .pill { display: inline-block; font-family: var(--mono); font-size: 26px; letter-spacing: 0.08em; padding: 8px 16px; border-radius: 999px; background: rgba(0,0,0,.14); width: max-content; }
      .cta.black .pill { background: rgba(255,255,255,.14); }
      .cta .code { font-family: var(--mono); font-size: 34px; letter-spacing: 0.12em; }
      .cta .code b { padding: 6px 14px; border: 2px dashed currentColor; border-radius: 10px; }
      .cta .line { font-size: 32px; opacity: .85; letter-spacing: -0.02em; }
      .cta .qr { flex: 0 0 auto; width: 220px; height: 220px; background: #fff; border-radius: 18px; padding: 12px; }
      .cta .qr svg { width: 100%; height: 100%; display: block; }
      .steps { position: absolute; display: flex; align-items: center; gap: 16px; padding: 12px 22px 12px 14px; border-radius: 999px; background: rgba(10,10,10,.72); color: #fff; font-size: 34px; letter-spacing: -0.02em; opacity: 0; white-space: nowrap; }
      .steps .n { font-family: var(--mono); font-weight: 700; background: var(--accent); color: var(--on-accent); border-radius: 999px; padding: 4px 16px; font-size: 30px; }
      .steps .lab { visibility: hidden; position: absolute; left: 110px; top: 50%; transform: translateY(-50%); }
      .steps .lab.on { visibility: visible; }
      .ba { position: absolute; overflow: hidden; border-radius: 22px; opacity: 0; box-shadow: 0 30px 80px rgba(0,0,0,.45); background: #000; }
      .ba img { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }
      .ba .after { clip-path: inset(0 100% 0 0); }
      .ba .bar { position: absolute; top: 0; bottom: 0; width: 6px; background: #fff; left: 0; box-shadow: 0 0 18px rgba(0,0,0,.6); }
      .ba .lbl { position: absolute; top: 18px; font-family: var(--mono); font-size: 26px; letter-spacing: 0.12em; text-transform: uppercase; padding: 8px 16px; border-radius: 999px; background: rgba(10,10,10,.75); color: #fff; }
      .ba .lbl.b { left: 18px; } .ba .lbl.a { right: 18px; background: var(--accent); color: var(--on-accent); }
      .caps span { visibility: hidden; position: absolute; left: 50%; transform: translateX(-50%); bottom: 0; background: #000; color: #fff; padding: 8px 20px; white-space: normal; text-align: center; line-height: 1.25; max-width: calc(100% - 80px); width: max-content; font-size: {capsize}px; }
      /* subtítulos por palabras (pages: entran al decirse; karaoke: la palabra actual en acento) */
      .pages { position: absolute; left: 0; right: 0; }
      .pages .pg { visibility: hidden; position: absolute; left: 50%; transform: translateX(-50%); bottom: 0; width: calc(100% - 100px); text-align: center; font-weight: 800; line-height: 1.08; letter-spacing: -0.02em; text-shadow: 0 3px 0 rgba(0,0,0,.35), 0 6px 28px rgba(0,0,0,.75), 0 0 2px #000; }
      .pages.upper .pg { text-transform: uppercase; }
      .pages .pw { display: inline-block; margin: 0 0.16em; }
      .pages.mode-pages .pw { opacity: 0; }
      .pages.mode-karaoke .pw { opacity: 1; color: rgba(255,255,255,.92); }
      /* fondo para los subtítulos por palabras (F28-166): caja semitransparente o contorno, para que se lean sobre fondo claro */
      .pages.bd-box .pg { width: max-content; max-width: calc(100% - 100px); background: rgba(0,0,0,.62); border-radius: 16px; padding: 0.1em 0.42em 0.16em; }
      .pages.bd-stroke .pw { -webkit-text-stroke: 0.07em #000; paint-order: stroke fill; }
      /* lienzos estrechos (vertical, cuadrado): tipografías y columnas más compactas */
      .narrow .chart { padding: 60px 48px; }
      .narrow .chart .ch-title { font-size: 46px; }
      .narrow .chart .grp { width: 110px; font-size: 20px; }
      .narrow .chart .lbl { width: 210px; font-size: 22px; padding-right: 18px; }
      .narrow .counter .num { font-size: 220px; }
      .narrow .counter .lab { font-size: 52px; }
      .narrow .bc .bc-title { font-size: 96px; }
      .narrow .bc .bc-sub { font-size: 34px; }
      .narrow .card .big { font-size: 96px; }
      /* barras a pantalla completa en vertical (F28-165): una fila = etiqueta encima y barra a todo el ancho, letra que se
         lee en el móvil y el bloque centrado por encima de la franja de subtítulos */
      .chart.portrait { padding: 140px 64px 24% 64px; }
      .chart.portrait .ch-title { font-size: 84px; line-height: 1.05; }
      .chart.portrait .ch-sub { font-size: 36px; margin-top: 14px; }
      .chart.portrait .rows { margin-top: 70px; }
      .chart.portrait .row { flex-wrap: wrap; height: auto; margin-bottom: 46px; }
      .chart.portrait .grp { width: 100%; font-size: 34px; margin-bottom: 12px; }
      .chart.portrait .grp:empty { display: none; }
      .chart.portrait .lbl { width: 100%; text-align: left; font-size: 46px; padding: 0 0 14px 0; white-space: normal; }
      .chart.portrait .track, .chart.portrait .fill { height: 64px; }
      .chart.portrait .val { line-height: 64px; font-size: 46px; }
      .chart.portrait .hero-box { top: -14px; bottom: -14px; }
"""


TALL_CAPS = re.compile(r"[ÁÉÍÓÚÀÈÌÒÙÂÊÎÔÛÄËÏÖÜÃÕÑÅ]")


def highlight_line_height(lines: list[str], base: float) -> float:
    """Interlineado de un título con resaltado por línea (gancho, portada). Cada línea va por encima de la siguiente
    para no cortar los descendentes (g, y, p); por eso la caja de arriba tapa la tilde o la diéresis de una mayúscula
    de la línea de abajo ("ACRÍLICO" se leía "ACRILICO"). Con más interlineado caben los dos."""
    return round(base + 0.22, 2) if any(TALL_CAPS.search(t) for t in lines[1:]) else base


HOOK_EM = 0.465   # medido en un short real: 20 caracteres a 96 px caben en 960 px; 21 se parten
BUNDLED_BRANDS = Path(__file__).with_name("brands")
USER_BRANDS = Path.home() / ".config" / "frame28" / "brands"


def resolve_brand(name_or_path: str, near: Path | None = None) -> Path:
    """Orden: ruta explícita -> brands/<n>.json junto al proyecto o en las carpetas que lo contienen (un short en
    work/clips/<id>/ encuentra la marca de work/brands/) -> ./brands -> ~/.config/frame28/brands -> incluidas."""
    p = Path(name_or_path)
    if p.suffix == ".json":
        for cand in ([p] + ([near / p, near.parent / p] if near and not p.is_absolute() else [])):
            if cand.exists():
                return cand
    cands = []
    if near:
        cands += [d / "brands" / f"{name_or_path}.json" for d in [near, *near.parents][:6]]
    cands += [Path.cwd() / "brands" / f"{name_or_path}.json", USER_BRANDS / f"{name_or_path}.json", BUNDLED_BRANDS / f"{name_or_path}.json"]
    for c in cands:
        if c.exists():
            return c
    raise SystemExit(f"marca '{name_or_path}' no encontrada. Buscado en: " + ", ".join(str(c) for c in cands))


def load_brand_file(path: Path) -> dict:
    """Lee una marca guardada y se niega si no tiene acento: con el valor por defecto el vídeo saldría con el rosa de
    Think28, un color que no es de la marca (F28-299). `brand from-site` deja `accent_pending` cuando no lo encontró con
    certeza; `frame28 brand set <marca> --accent` guarda el que elija el usuario."""
    brand = json.loads(path.read_text(encoding="utf-8-sig"))
    bad = brand_errors(brand)
    if not brand.get("accent_pending") and not brand.get("accent"):
        bad.append(f"marca.accent: falta en {path.name}; sin él el vídeo saldría con un color que no es de la marca. "
                   f"Guárdalo con: frame28 brand set {path.stem} --accent #RRGGBB")
    if bad:
        raise SystemExit("Marca no válida:\n  - " + "\n  - ".join(bad))
    return brand


def list_brands() -> dict[str, Path]:
    found: dict[str, Path] = {}
    for d in (BUNDLED_BRANDS, USER_BRANDS, Path.cwd() / "brands"):
        if d.exists():
            for f in d.glob("*.json"):
                found[f.stem] = f
    return found


# Iconos de trazo (Lucide, ISC), viewBox 0 0 24 24, para el overlay `draw`
ICONS = {
    "check": ["M20 6 9 17l-5-5"],
    "circle-check": ["M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20z", "m9 12 2 2 4-4"],
    "circle": ["M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20z"],
    "arrow-right": ["M5 12h14", "m12 5 7 7-7 7"],
    "arrow-up-right": ["M7 7h10v10", "M7 17 17 7"],
    "arrow-down": ["M12 5v14", "m19 12-7 7-7-7"],
    "zap": ["M4 14a1 1 0 0 1-.78-1.63l9.9-10.2a.5.5 0 0 1 .86.46l-1.92 6.02A1 1 0 0 0 13 10h7a1 1 0 0 1 .78 1.63l-9.9 10.2a.5.5 0 0 1-.86-.46l1.92-6.02A1 1 0 0 0 11 14z"],
    "star": ["M11.525 2.295a.53.53 0 0 1 .95 0l2.31 4.679a2.123 2.123 0 0 0 1.595 1.16l5.166.756a.53.53 0 0 1 .294.904l-3.736 3.638a2.123 2.123 0 0 0-.611 1.878l.882 5.14a.53.53 0 0 1-.771.56l-4.618-2.428a2.122 2.122 0 0 0-1.973 0L6.396 21.01a.53.53 0 0 1-.77-.56l.881-5.139a2.122 2.122 0 0 0-.611-1.879L2.16 9.795a.53.53 0 0 1 .294-.906l5.165-.755a2.122 2.122 0 0 0 1.597-1.16z"],
    "x": ["M18 6 6 18", "m6 6 12 12"],
    "plus": ["M5 12h14", "M12 5v14"],
    "heart": ["M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"],
    "underline": ["M2 12c4-6 8-6 10 0s6 6 10 0"],
}


def esc(s: str) -> str:
    return html.escape(str(s), quote=True)


class Builder:
    def __init__(self, sb: dict, project_dir: Path):
        self.sb = sb
        self.dir = project_dir
        brand = sb.get("brand", {})
        self.brand_dir: Path | None = None
        if isinstance(brand, str):
            path = resolve_brand(brand, project_dir)
            brand = load_brand_file(path)
            self.brand_dir = path.parent
        bad = brand_errors(brand)
        if bad:
            raise SystemExit("Marca no válida:\n  - " + "\n  - ".join(bad))
        self.brand = {**DEFAULT_BRAND, **{k: v for k, v in brand.items() if k in DEFAULT_BRAND}}
        self.brand["on_accent"] = brand.get("on_accent") or on_accent_color(self.brand["accent"], self.brand["ink"])
        self.brand_meta = brand
        self.brand_assets: dict[str, Path] = {}  # ruta publicada -> fichero origen (logos)
        # duración total: puede superar la del clip (tarjetas de cierre sobre negro)
        self.dur = float(sb.get("duration", sb["source"]["duration"]))
        canvas = sb.get("canvas", {})
        self.W = int(canvas.get("width", 1920)); self.H = int(canvas.get("height", 1080)); self.fps = int(canvas.get("fps", 30))
        self.narrow = self.W < 1400  # vertical o cuadrado: columnas y tipografías compactas (ver CSS .narrow)
        self.html: list[str] = []
        self.js: list[str] = []
        self.uses_split = False
        self.uses_draw = False
        self.sb_dir: Path | None = None
        self.assets: set[str] = set()
        self.warnings: list[str] = []

    # ---------- helpers ----------
    def corners(self) -> str:
        return '<i class="c tl"></i><i class="c tr"></i><i class="c bl"></i><i class="c br"></i>'

    def timed(self, o: dict, extra_style: str = "", cls: str = "clip", tag: str = "div", inner: str = "", z: int = 4, track: int = 4) -> None:
        self.html.append(
            f'<{tag} id="{o["id"]}" class="{cls}" data-start="{o["start"]}" data-duration="{round(o["end"] - o["start"], 3)}" '
            f'data-track-index="{track}" style="z-index:{z};{extra_style}">{inner}</{tag}>')

    def fade_out(self, sel: str, end: float, d: float = 0.2) -> None:
        self.js.append(f'tl.to("{sel}", {{ opacity: 0, duration: {d} }}, {round(end - d, 3)});')

    def pop(self, sel: str, at: float, d: float = 0.18) -> None:
        self.js.append(f'tl.fromTo("{sel}", {{ opacity: 0, y: 26 }}, {{ opacity: 1, y: 0, duration: {d}, ease: "power3.out" }}, {at});')

    def reveal(self, sel: str, at: float, mode: str = "fade", d: float = 0.18) -> None:
        """Entrada de un texto envuelto en .w > .wi: fade (por defecto), rise (máscara) o chars (SplitText)."""
        if mode == "rise":
            self.js.append(f'tl.set("{sel}", {{ opacity: 1 }}, {at}); tl.fromTo("{sel} .wi", {{ yPercent: 110 }}, {{ yPercent: 0, duration: {max(d, 0.3)}, ease: "power3.out" }}, {at});')
        elif mode == "chars":
            self.uses_split = True
            self.js.append(f'{{ const sp = SplitText.create("{sel} .wi", {{ type: "chars" }}); tl.set("{sel}", {{ opacity: 1 }}, {at}); '
                           f'tl.fromTo(sp.chars, {{ yPercent: 60, opacity: 0 }}, {{ yPercent: 0, opacity: 1, duration: 0.28, stagger: 0.025, ease: "power3.out" }}, {at}); }}')
        else:
            self.pop(sel, at, d)

    def box_in(self, sel: str, at: float) -> None:
        self.js.append(f'tl.fromTo("{sel}", {{ opacity: 0, scale: 0.9 }}, {{ opacity: 1, scale: 1, duration: 0.2, ease: "power2.out" }}, {at});')

    def asset(self, rel: str) -> str:
        self.assets.add(rel)
        return rel

    def logo_width(self, pub: str | None, height: int = 30) -> int:
        """Ancho que ocupará el logo a `height` px (PNG/JPG por sus dimensiones, SVG por viewBox); 30 si no se sabe."""
        if not pub:
            return 0
        src = next((f for k, f in self.brand_assets.items() if k == pub), None)
        try:
            if src and src.suffix.lower() == ".svg":
                txt = src.read_text(encoding="utf-8", errors="ignore")
                m = re.search(r'viewBox="[\d.\-]+[ ,]+[\d.\-]+[ ,]+([\d.]+)[ ,]+([\d.]+)"', txt)
                if m:
                    return round(height * float(m.group(1)) / float(m.group(2)))
            elif src:
                import struct
                with open(src, "rb") as f:
                    head = f.read(26)
                if head[:8] == b"\x89PNG\r\n\x1a\n":
                    w, h = struct.unpack(">II", head[16:24])
                    return round(height * w / h)
        except Exception:
            pass
        return height

    def brand_logo(self, variant: str = "isotipo") -> str | None:
        """Publica el logo de la marca como assets/brand/<fichero> y devuelve la ruta relativa, o None si no hay."""
        files = self.brand_meta.get("logo_files") or {}
        rel = files.get(variant) or files.get("isotipo")
        if not rel or not self.brand_dir:
            return None
        src = self.brand_dir / rel
        if not src.exists():
            self.warnings.append(f"logo de marca no encontrado: {src}"); return None
        pub = f"assets/brand/{src.name}"
        self.brand_assets[pub] = src
        return pub

    # ---------- overlays ----------
    def lower_third(self, o: dict) -> None:
        i = o["id"]; t = o["start"]
        title = esc(o["title"]); sub = esc(o.get("subtitle", ""))
        logo = self.brand_logo("isotipo")
        mark = f'<img class="lt-logo" src="{logo}" alt="">' if logo else '<span class="cur">◌</span>'
        inner = (f'<i class="c tl"></i><i class="c br"></i>'
                 f'<div class="line"><span class="mask" id="{i}-l1">{mark}&nbsp;{title}&nbsp;&nbsp;&nbsp;&nbsp;×</span></div>'
                 + (f'<div class="line"><span class="mask" id="{i}-l2">{sub}<span class="cur">▌</span></span></div>' if sub else ""))
        # la caja se dimensiona sola (width: max-content) y el "tecleo" es un clip-path: no dependemos de estimar
        # el ancho de la fuente (Space Mono, Poppins o lo que cargue el navegador)
        self.timed(o, f"left:{o['x']}px; top:{o['y']}px;", cls="lower", inner=inner, z=4, track=3)
        self.js.append(f'tl.fromTo("#{i}", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.2 }}, {t});')
        self.js.append(f'tl.fromTo("#{i}-l1", {{ clipPath: "inset(0 100% 0 0)" }}, {{ clipPath: "inset(0 0% 0 0)", duration: {round(min(0.9, 0.05 * len(o["title"]) + 0.3), 2)}, ease: "none" }}, {round(t + 0.1, 3)});')
        if sub:
            self.js.append(f'tl.fromTo("#{i}-l2", {{ clipPath: "inset(0 100% 0 0)" }}, {{ clipPath: "inset(0 0% 0 0)", duration: {round(min(1.0, 0.03 * len(sub) + 0.2), 2)}, ease: "none" }}, {round(t + 0.75, 3)});')
        self.fade_out(f"#{i}", o["end"], 0.25)

    def box(self, o: dict) -> None:
        est = 54 * 0.5 * len(o["text"]) + 52  # Poppins/Inter a 54 px: ~0,5 em por carácter
        if o["x"] + est > self.W:
            self.warnings.append(f"box {o['id']}: '{o['text']}' probablemente se sale del lienzo por la derecha "
                                 f"(x {o['x']} + ~{round(est)} px > {self.W}); acorta el texto o muévelo a x <= {max(0, round(self.W - est))}")
        self.timed(o, f"left:{o['x']}px; top:{o['y']}px;", cls="box", inner=self.corners() + esc(o["text"]), z=4, track=4)
        self.box_in(f"#{o['id']}", o.get("at", o["start"]))
        self.fade_out(f"#{o['id']}", o["end"])

    def kinetic(self, o: dict) -> None:
        i = o["id"]; size = o.get("size", 124)
        rows = []
        for li, line in enumerate(o["lines"]):
            mode = o.get("reveal", "fade")
            spans = "".join(f'<span class="w{" accent" if w.get("accent") else ""}{" rise" if mode == "rise" else ""}" id="{i}-{li}-{wi}"><span class="wi">{esc(w["text"])}</span></span>' for wi, w in enumerate(line))
            rows.append(f"<div>{spans}</div>")
        color = o.get("color")
        cls = "kin onlight" if color else "kin"
        self.timed(o, f"left:{o['x']}px; top:{o['y']}px; font-size:{size}px;" + (f" color:{color};" if color else ""), cls=cls, inner="".join(rows), z=4, track=5)
        for li, line in enumerate(o["lines"]):
            for wi, w in enumerate(line):
                self.reveal(f"#{i}-{li}-{wi}", w["at"], o.get("reveal", "fade"))
        self.fade_out(f"#{i}", o["end"])

    def behind(self, o: dict) -> None:
        """Texto detrás del hablante: capa 2 = texto, capa 3 = vídeo con alfa (solo en su tramo)."""
        i = o["id"]; size = o.get("size", 240)
        mode = o.get("reveal", "fade")
        self.timed(o, "", cls="clip behind", inner=f'<div class="w{" rise" if mode == "rise" else ""}" id="{i}-w" style="font-size:{size}px;"><span class="wi">{esc(o["text"])}</span></div>', z=2, track=1)
        m = self.asset(o["matte"]); ms = o.get("matte_start", o["start"]); me = o.get("matte_end", o["end"])
        self.html.append(f'<video id="{i}-fg" class="clip cover" data-start="{ms}" data-duration="{round(me - ms, 3)}" data-track-index="2" '
                         f'src="{m}" muted playsinline style="z-index:3"></video>')
        at = o.get("at", o["start"])
        if mode in ("rise", "chars"):
            self.reveal(f"#{i}-w", at, mode, 0.4)
        else:
            self.js.append(f'tl.fromTo("#{i}-w", {{ opacity: 0, scale: 1.15 }}, {{ opacity: 1, scale: 1, duration: 0.5, ease: "power3.out" }}, {at});')
        self.fade_out(f"#{i}-w", o["end"], 0.25)

    def pointer(self, o: dict) -> None:
        """Callout con punto + línea que crece hasta la caja. La línea se calcula sola desde el punto a la caja."""
        i = o["id"]; dx, dy = o["dot"]; bx, by = o["box"]; at = o.get("at", o["start"])
        # la línea apunta a la esquina inferior izquierda o inferior derecha de la caja, la más cercana al punto
        box_h = 80
        target_x = bx if bx >= dx else bx + max(120, 0.62 * 54 * len(o["text"]) + 52)
        target_y = by + box_h
        ang = math.degrees(math.atan2(target_y - dy, target_x - dx)); length = math.hypot(target_x - dx, target_y - dy)
        inner = (f'<div class="dot" id="{i}-dot" style="left:{dx - 9}px; top:{dy - 9}px;"></div>'
                 f'<div class="conn" id="{i}-line" style="left:{dx}px; top:{dy - 1}px; transform: rotate({round(ang, 2)}deg);"></div>'
                 f'<div class="box" id="{i}-box" style="left:{bx}px; top:{by}px;">{self.corners()}{esc(o["text"])}</div>')
        self.timed(o, "", cls="clip", inner=inner, z=4, track=6)
        self.js.append(f'tl.fromTo("#{i}-dot", {{ scale: 0 }}, {{ scale: 1, duration: 0.2, ease: "back.out(2)" }}, {at});')
        self.js.append(f'tl.fromTo("#{i}-line", {{ width: 0 }}, {{ width: {round(length)}, duration: 0.3, ease: "power3.out" }}, {round(at + 0.12, 3)});')
        self.box_in(f"#{i}-box", round(at + 0.35, 3))
        self.fade_out(f"#{i}", o["end"])

    def card(self, o: dict) -> None:
        i = o["id"]; bg = o.get("bg", "black"); t = o.get("title", {}); s = o.get("subtitle")
        t = {"text": t} if isinstance(t, str) else t            # "title": "Hola" vale igual que {"text": "Hola"}
        s = {"text": s} if isinstance(s, str) else s
        mode = t.get("reveal", "fade")
        inner = f'<div class="big w{" rise" if mode == "rise" else ""}" id="{i}-t" style="font-size:{t.get("size", 190)}px;"><span class="wi">{esc(t["text"])}</span></div>'
        if s:
            inner += f'<div class="small" id="{i}-s" style="font-size:{s.get("size", 72)}px;">{esc(s["text"])}</div>'
        self.timed(o, "", cls=f"clip card {bg}", inner=inner, z=5, track=6)
        if mode in ("rise", "chars"):
            self.reveal(f"#{i}-t", t.get("at", o["start"]), mode, 0.35)
        else:
            self.js.append(f'tl.fromTo("#{i}-t", {{ opacity: 0, y: 30 }}, {{ opacity: 1, y: 0, duration: 0.3, ease: "power3.out" }}, {t.get("at", o["start"])});')
        if s:
            self.js.append(f'tl.fromTo("#{i}-s", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.3 }}, {s.get("at", o["start"] + 0.4)});')

    def list_focus(self, o: dict) -> None:
        """Lista donde el foco (etiqueta + icono) salta de ítem en ítem al decirse cada uno."""
        i = o["id"]; bg = o.get("bg", "white"); size = o.get("size", 96); label = esc(o.get("label", "New"))
        row_h = round(size * 1.2); gap = 26
        items = "".join(f'<div class="lab" style="height:{row_h}px"></div><div class="item" id="{i}-it{k}" style="font-size:{size}px">{esc(it["text"])}</div>'
                        for k, it in enumerate(o["items"]))
        inner = (f'<div class="list" style="grid-template-columns: {round(size * 3.1)}px {round(size * 8.5)}px; row-gap:{gap}px;">'
                 f'<div class="newlabel" id="{i}-new" style="height:{row_h}px; font-size:{size}px;"><span>{label}</span>'
                 f'<span class="icon" style="width:{size}px;height:{size}px;"><i></i></span></div>{items}</div>')
        self.timed(o, "", cls=f"clip card {bg}", inner=inner, z=5, track=6)
        self.js.append(f'tl.fromTo("#{i} .item", {{ opacity: 0, x: -30 }}, {{ opacity: 1, x: 0, duration: 0.3, stagger: 0.12, ease: "power3.out" }}, {o["start"] + 0.05});')
        ink, grey = self.brand["ink"], self.brand["grey"]
        for k, it in enumerate(o["items"]):
            at = it["at"]
            if k > 0:
                self.js.append(f'tl.to("#{i}-new", {{ y: {k * (row_h + gap)}, duration: 0.35, ease: "power3.inOut" }}, {at});')
                self.js.append(f'tl.set("#{i}-it{k - 1}", {{ color: "{grey}" }}, {at});')
            self.js.append(f'tl.set("#{i}-it{k}", {{ color: "{ink}" }}, {at});')

    def card_words(self, o: dict) -> None:
        """Pizarra con frase que aparece palabra a palabra; `initial: true` pinta la inicial con el color de acento."""
        i = o["id"]; bg = o.get("bg", "black"); size = o.get("size", 118)
        rows = []
        for li, line in enumerate(o["lines"]):
            spans = []
            for wi, w in enumerate(line):
                txt = esc(w["text"])
                if w.get("initial") and len(w["text"]) > 1:
                    txt = f"<b>{esc(w['text'][0])}</b>{esc(w['text'][1:])}"
                if w.get("accent"):
                    txt = f'<span class="accent">{txt}</span>'
                spans.append(f'<span class="w" id="{i}-{li}-{wi}">{txt}</span>')
            rows.append(f'<div class="row" style="font-size:{size}px">{"".join(spans)}</div>')
        self.timed(o, "", cls=f"clip card cw {bg}", inner="".join(rows), z=5, track=6)
        for li, line in enumerate(o["lines"]):
            for wi, w in enumerate(line):
                self.pop(f"#{i}-{li}-{wi}", w["at"], 0.25)

    def image(self, o: dict) -> None:
        """Imagen o captura que entra con pop (captura de UI, logo, foto)."""
        i = o["id"]; src = self.asset(o["src"])
        self.timed(o, f"left:{o['x']}px; top:{o['y']}px; width:{o['w']}px;", cls="img", inner=f'<img src="{src}" alt="">', z=4, track=7)
        self.js.append(f'tl.fromTo("#{i}", {{ opacity: 0, scale: 0.92, y: 20 }}, {{ opacity: 1, scale: 1, y: 0, duration: 0.35, ease: "power3.out" }}, {o.get("at", o["start"])});')
        self.fade_out(f"#{i}", o["end"])

    def broll(self, o: dict) -> None:
        """B-roll: vídeo o imagen de apoyo. `full` (por defecto) tapa al hablante; `pip: {x,y,w,h}` lo pone en una ventana.
        `in` recorta el punto de entrada del clip (data-media-start), `ken_burns` anima escala/paneo, `credit` firma
        la esquina, `caption` rotula abajo. Entra y sale con fundido corto."""
        i = o["id"]; at = o.get("at", o["start"]); src = self.asset(o["src"])
        is_video = Path(src).suffix.lower() in (".mp4", ".webm", ".mov", ".m4v")
        pip = o.get("pip")
        cls = "clip broll " + ("pip" if pip else "full")
        style = f"left:{pip['x']}px; top:{pip['y']}px; width:{pip['w']}px; height:{pip['h']}px; inset:auto;" if pip else ""
        dur = round(o["end"] - o["start"], 3)
        media_start = f' data-media-start="{o["in"]}"' if o.get("in") else ""
        loop = ' data-loop="true"' if o.get("loop") else ""
        if is_video:
            media = (f'<video id="{i}-m" data-start="{o["start"]}" data-duration="{dur}" data-track-index="5"{media_start}{loop} '
                     f'src="{src}" muted playsinline></video>')
        else:
            media = f'<img id="{i}-m" src="{src}" alt="">'
        credit = f'<div class="credit">{esc(o["credit"])}</div>' if o.get("credit") else ""
        cap = f'<div class="cap" id="{i}-c">{esc(o["caption"])}</div>' if o.get("caption") else ""
        # el contenedor NO lleva data-start (un <video> temporizado dentro de otro elemento temporizado confunde al
        # extractor de HyperFrames): su visibilidad la lleva la opacidad; el vídeo tiene su propia ventana.
        self.html.append(f'<div id="{i}" class="{cls}" style="z-index:{5 if not pip else 4};{style}">{media}{cap}{credit}</div>')
        fade = float(o.get("fade", 0.25))
        self.js.append(f'tl.fromTo("#{i}", {{ opacity: 0 }}, {{ opacity: 1, duration: {fade} }}, {at});')
        kb = o.get("ken_burns")
        if kb:
            s0 = float(kb.get("from", 1.0)); s1 = float(kb.get("to", 1.12))
            pan = kb.get("pan", "none"); dx = {"left": -3, "right": 3}.get(pan, 0); dy = {"up": -3, "down": 3}.get(pan, 0)
            self.js.append(f'tl.fromTo("#{i}-m", {{ scale: {s0}, xPercent: 0, yPercent: 0 }}, {{ scale: {s1}, xPercent: {dx}, yPercent: {dy}, duration: {dur}, ease: "none" }}, {o["start"]});')
        if o.get("caption"):
            self.js.append(f'tl.fromTo("#{i}-c", {{ opacity: 0, y: 16 }}, {{ opacity: 1, y: 0, duration: 0.3, ease: "power3.out" }}, {round(at + 0.2, 3)});')
        self.fade_out(f"#{i}", o["end"], fade)

    # ---------- venta ----------
    def hook(self, o: dict) -> None:
        """Gancho de los primeros segundos: 1–3 líneas grandes con resaltado por línea (estilo Shorts/TikTok)."""
        i = o["id"]; at = o.get("at", o["start"]); size = int(o.get("size", 96 if self.narrow else 110))
        bg = o.get("bg", "accent")
        lines = o.get("lines") or [o["text"]]
        x = int(o.get("x", 60)); w = int(o.get("w", self.W - 2 * x)); y = int(o.get("y", 160 if self.narrow else 90))
        for t in lines:
            est = HOOK_EM * size * len(t) + 40   # negrita de titular: ~0,465 em por carácter, más el relleno del resaltado
            if est > w:
                self.warnings.append(f"hook {i}: '{t}' probablemente se parte en dos líneas (~{round(est)} px > {w}) y deja una "
                                     f"palabra huérfana; acórtala o usa size <= {int((w - 40) / (HOOK_EM * len(t)))}")
        # cada línea por encima de la siguiente: los descendentes (g, y, p) se pintan sobre la caja de abajo, no debajo
        inner = "".join(f'<div style="position:relative; z-index:{100 - k}"><span class="hl" id="{i}-l{k}">{esc(t)}</span></div>' for k, t in enumerate(lines))
        color = f" color:{o['color']};" if o.get("color") else ""
        lh = highlight_line_height(lines, 1.15)
        tall = f" line-height:{lh};" if lh != 1.15 else ""
        self.timed(o, f"inset:auto; left:{x}px; top:{y}px; width:{w}px; height:max-content; font-size:{size}px;{color}{tall}", cls=f"clip hook {bg}", inner=inner, z=6, track=4)
        self.js.append(f'tl.set("#{i}", {{ opacity: 1 }}, {at});')
        for k in range(len(lines)):
            self.js.append(f'tl.fromTo("#{i}-l{k}", {{ opacity: 0, scale: 0.85 }}, {{ opacity: 1, scale: 1, duration: 0.22, ease: "back.out(2)" }}, {round(at + 0.12 * k, 3)});')
        self.fade_out(f"#{i}", o["end"], 0.25)

    def _qr_svg(self, data: str) -> str:
        """QR como <img> PNG en data URI: un SVG inline con cientos de módulos triplicaba el tiempo de captura."""
        try:
            import segno
            import io
            import base64
            buf = io.BytesIO()
            segno.make(data, error="m").save(buf, kind="png", scale=10, border=1, dark="#0A0A0A", light="#FFFFFF")
            return f'<img src="data:image/png;base64,{base64.b64encode(buf.getvalue()).decode("ascii")}" alt="QR" style="width:100%;height:100%;display:block;image-rendering:pixelated">'
        except Exception as e:  # segno ausente o dato inválido: sin QR, pero el resto del CTA sigue
            self.warnings.append(f"cta: no se pudo generar el QR ({e})")
            return ""

    def cta(self, o: dict) -> None:
        """Llamada a la acción: título, precio (con precio anterior tachado), descuento, código, línea ("Link in bio") y QR."""
        i = o["id"]; at = o.get("at", o["start"]); bg = o.get("bg", "accent")
        parts = []
        if o.get("title"):
            parts.append(f'<div class="title">{esc(o["title"])}</div>')
        if o.get("price"):
            parts.append(f'<div class="price">{esc(str(o["price"]))}' + (f'<s>{esc(str(o["old_price"]))}</s>' if o.get("old_price") else "") + '</div>')
        if o.get("discount"):
            parts.append(f'<div class="pill">{esc(o["discount"])}</div>')
        if o.get("code"):
            parts.append(f'<div class="code">{esc(o.get("code_label", "CODE"))} <b>{esc(o["code"])}</b></div>')
        if o.get("line"):
            parts.append(f'<div class="line">{esc(o["line"])}</div>')
        qr = f'<div class="qr">{self._qr_svg(o["url"])}</div>' if o.get("url") and o.get("qr", True) else ""
        inner = f'<div class="col">{"".join(parts)}</div>{qr}'
        x, y, w = self.cta_box(o)
        self.timed(o, f"inset:auto; left:{x}px; top:{y}px; width:{w}px; height:max-content;", cls=f"clip cta {bg}", inner=inner, z=6, track=4)
        self.js.append(f'tl.fromTo("#{i}", {{ opacity: 0, y: 40 }}, {{ opacity: 1, y: 0, duration: 0.35, ease: "power3.out" }}, {at});')
        self.fade_out(f"#{i}", o["end"], 0.3)

    def cta_box(self, o: dict) -> tuple[int, int, int]:
        """Posición por defecto del CTA: fuera de la columna de iconos (vertical) y encima de los subtítulos."""
        x = int(o.get("x", 60))
        w = int(o.get("w", self.W - x - (170 if self.narrow else x)))
        cs = self.sb.get("caption_style") or {}
        if self.sb.get("captions") or cs:
            bottom = int(cs.get("bottom", 200 if self.narrow else 56))
            size = int(cs.get("size", 72 if self.narrow else 64)) if cs else 40
            cap_top = self.H - bottom - round(size * 2.4)
        else:
            cap_top = self.H - 80
        y = int(o.get("y", cap_top - 440 - 24))
        return x, y, w

    def steps(self, o: dict) -> None:
        """Indicador de progreso "1 / 3 · Tape the stencil" que cambia en el `at` de cada paso (visible start–end)."""
        i = o["id"]; items = o["items"]; total = int(o.get("total", len(items)))
        x = int(o.get("x", 60)); y = int(o.get("y", 60)); size = int(o.get("size", 34))
        labels = "".join(f'<span class="lab" id="{i}-s{k}">{esc(it["label"])}</span>' for k, it in enumerate(items))
        nums = "".join(f'<span class="lab" id="{i}-n{k}" style="left:14px">{k + 1} / {total}</span>' for k in range(len(items)))
        longest = max((len(it["label"]) for it in items), default=6)
        inner = f'<span class="n" style="visibility:hidden">{total} / {total}</span>{nums}{labels}'
        self.timed(o, f"left:{x}px; top:{y}px; font-size:{size}px; width:{round(size * 0.55 * longest + 150)}px; height:{round(size * 1.9)}px;", cls="clip steps", inner=inner, z=6, track=4)
        self.js.append(f'tl.fromTo("#{i}", {{ opacity: 0, x: -20 }}, {{ opacity: 1, x: 0, duration: 0.3 }}, {o["start"]});')
        for k, it in enumerate(items):
            t = it.get("at", o["start"]); nxt = items[k + 1].get("at", o["end"]) if k + 1 < len(items) else o["end"]
            for sel in (f"#{i}-s{k}", f"#{i}-n{k}"):
                self.js.append(f'tl.set("{sel}", {{ visibility: "visible" }}, {t}); tl.set("{sel}", {{ visibility: "hidden" }}, {nxt});')
        self.fade_out(f"#{i}", o["end"], 0.25)

    def before_after(self, o: dict) -> None:
        """Antes/después: dos imágenes (o dos instantes `before_t`/`after_t` del propio clip) con barrido de izquierda a derecha."""
        i = o["id"]; at = o.get("at", o["start"]); dur = float(o.get("duration", 1.2))
        srcs = {}
        for key in ("before", "after"):
            if o.get(key):
                srcs[key] = self.asset(o[key])
            elif o.get(f"{key}_t") is not None and self.sb_dir is not None:
                from .media import frame_at
                video = Path(self.sb_dir) / self.sb["source"]["video"]
                rel = f"assets/ba_{i}_{key}.jpg"
                dst = Path(self.dir) / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                frame_at(video, float(o[f"{key}_t"]), dst)
                srcs[key] = rel
            else:
                self.warnings.append(f"before_after {i}: falta '{key}' o '{key}_t'")
                srcs[key] = ""
        w = int(o.get("w", self.W - 120)); h = int(o.get("h", round(w * 9 / 16)))
        x = int(o.get("x", (self.W - w) // 2)); y = int(o.get("y", (self.H - h) // 2))
        inner = (f'<img class="before" src="{srcs["before"]}" alt=""><img class="after" id="{i}-a" src="{srcs["after"]}" alt="">'
                 f'<div class="bar" id="{i}-bar"></div><span class="lbl b">{esc(o.get("label_before", "Before"))}</span><span class="lbl a">{esc(o.get("label_after", "After"))}</span>')
        self.timed(o, f"left:{x}px; top:{y}px; width:{w}px; height:{h}px;", cls="clip ba", inner=inner, z=5, track=6)
        self.js.append(f'tl.fromTo("#{i}", {{ opacity: 0, scale: 0.96 }}, {{ opacity: 1, scale: 1, duration: 0.3, ease: "power3.out" }}, {at});')
        self.js.append(f'tl.fromTo("#{i}-a", {{ clipPath: "inset(0 100% 0 0)" }}, {{ clipPath: "inset(0 0% 0 0)", duration: {dur}, ease: "power2.inOut" }}, {round(at + 0.4, 3)});')
        self.js.append(f'tl.fromTo("#{i}-bar", {{ x: 0 }}, {{ x: {w - 6}, duration: {dur}, ease: "power2.inOut" }}, {round(at + 0.4, 3)});')
        self.fade_out(f"#{i}", o["end"], 0.3)

    def brand_card(self, o: dict) -> None:
        """Tarjeta de marca (apertura o cierre): logo + título + subtítulo + endorsement, sobre negro o acento."""
        i = o["id"]; bg = o.get("bg", "black"); at = o.get("at", o["start"])
        variant = o.get("logo", {"black": "on_dark", "accent": "on_accent", "white": "on_light"}.get(bg, "on_dark"))
        logo = self.brand_logo(variant)
        title = o.get("title", ""); sub = o.get("subtitle", self.brand_meta.get("tagline", ""))
        endorse = o.get("endorsement", self.brand_meta.get("endorsement", ""))
        inner = ""
        if logo:
            inner += f'<img id="{i}-logo" class="bc-logo" src="{logo}" alt="" style="width:{o.get("logo_width", 520)}px">'
        mode = o.get("reveal", "fade")
        if title:
            inner += f'<div id="{i}-t" class="bc-title w{" rise" if mode == "rise" else ""}"><span class="wi">{esc(title)}</span></div>'
        if sub:
            inner += f'<div id="{i}-s" class="bc-sub">{esc(sub)}</div>'
        if endorse:
            inner += f'<div id="{i}-e" class="bc-endorse">{esc(endorse)}</div>'
        self.timed(o, "", cls=f"clip card bc {bg}", inner=inner, z=5, track=6)
        step = 0.0
        for sel, present in ((f"#{i}-logo", bool(logo)), (f"#{i}-t", bool(title)), (f"#{i}-s", bool(sub)), (f"#{i}-e", bool(endorse))):
            if present:
                if sel == f"#{i}-t" and mode in ("rise", "chars"):
                    self.reveal(sel, round(at + step, 3), mode, 0.45)
                else:
                    self.js.append(f'tl.fromTo("{sel}", {{ opacity: 0, y: 24 }}, {{ opacity: 1, y: 0, duration: 0.45, ease: "power3.out" }}, {round(at + step, 3)});')
                step += 0.18

    def chart(self, o: dict) -> None:
        kind = o.get("kind", "bar")
        if kind == "bar":
            self._chart_bar(o)
        elif kind == "counter":
            self._chart_counter(o)
        else:
            self.warnings.append(f"chart {o.get('id')}: kind desconocido '{kind}' (bar, counter)")

    def _chart_frame(self, o: dict, cls: str) -> tuple[str, str]:
        """Clase y estilo inline según sea tarjeta a pantalla completa (bg) o panel flotante (panel: {x,y,w})."""
        if o.get("panel"):
            pnl = o["panel"]
            return f"clip {cls} panel", f"left:{pnl['x']}px; top:{pnl['y']}px; width:{pnl['w']}px;" + (f" height:{pnl['h']}px;" if pnl.get("h") else "")
        bg = o.get("bg", "accent")
        return f"clip card {cls} {bg}", ""

    def _chart_bar(self, o: dict) -> None:
        """Barras horizontales agrupadas; la fila `hero` entra la última y se destaca con caja (T10c)."""
        i = o["id"]; at = o.get("at", o["start"])
        series = list(o["series"])
        if o.get("sort") in ("asc", "desc"):
            series.sort(key=lambda r: r["value"], reverse=o["sort"] == "desc")
        hero = o.get("hero")
        vmax = max((r["value"] for r in series), default=1) or 1
        unit = o.get("unit", ""); dec = o.get("decimals", 2)
        # ancho de la barra más larga: ancho del marco menos márgenes, columna de grupo, etiqueta y sitio para el valor
        portrait = not o.get("panel") and self.H > self.W
        if o.get("panel"):
            scale = max(200, o["panel"]["w"] - 88 - 200 - 320 - 170)
        elif portrait:
            # la barra usa el ancho entero menos los márgenes y el sitio del valor más largo (Space Mono a 46 px ≈ 28 px/carácter)
            longest = max((len(f"{r['value']:.{o.get('decimals', 2)}f}{unit}") for r in series), default=4)
            scale = max(200, self.W - 128 - 28 * longest - 24)
        else:
            scale = (self.W - 96 - 110 - 210 - 150) if self.narrow else (self.W - 280 - 200 - 320 - 170)
        rows_html = []
        prev_group = None
        for k, r in enumerate(series):
            grp = r.get("group", "")
            grp_html = f'<span>{esc(grp)}</span>' if grp and grp != prev_group else ""
            prev_group = grp or prev_group
            is_hero = hero is not None and r.get("label") == hero
            w = max(6, round(r["value"] / vmax * scale))
            val = f"{r['value']:.{dec}f}{unit}"
            hero_box = f'<div class="hero-box" id="{i}-hb">{self.corners()}</div>' if is_hero else ""
            rows_html.append(
                f'<div class="row{" hero" if is_hero else ""}" id="{i}-r{k}"><div class="grp">{grp_html}</div>'
                f'<div class="lbl">{esc(r["label"])}</div><div class="track" style="width:{(self.W - 128) if portrait else scale + 180}px"><div class="fill" id="{i}-f{k}" style="width:{w}px"></div>'
                f'<div class="val" id="{i}-v{k}" style="left:{w + 16}px">{esc(val)}</div></div>{hero_box}</div>')
        title = o.get("title", ""); sub = o.get("subtitle", "")
        inner = (f'<div class="ch-title" id="{i}-t">{esc(title)}</div>' if title else "") + \
                (f'<div class="ch-sub">{esc(sub)}</div>' if sub else "") + f'<div class="rows">{"".join(rows_html)}</div>'
        cls, style = self._chart_frame(o, "chart portrait" if portrait else "chart")
        self.timed(o, style, cls=cls, inner=inner, z=5 if not o.get("panel") else 4, track=6)
        if title:
            self.js.append(f'tl.fromTo("#{i}-t", {{ opacity: 0, y: 20 }}, {{ opacity: 1, y: 0, duration: 0.3, ease: "power3.out" }}, {at});')
        step = o.get("stagger", 0.13); t0 = at + (0.3 if title else 0.05)
        for k, r in enumerate(series):
            tk = round(t0 + k * step, 3)
            self.js.append(f'tl.to("#{i}-r{k}", {{ opacity: 1, duration: 0.2 }}, {tk});')
            self.js.append(f'tl.fromTo("#{i}-f{k}", {{ scaleX: 0 }}, {{ scaleX: 1, duration: 0.6, ease: "power3.out" }}, {round(tk + 0.05, 3)});')
            self.js.append(f'tl.to("#{i}-v{k}", {{ opacity: 1, duration: 0.4 }}, {round(tk + 0.25, 3)});')
        if hero is not None:
            th = round(t0 + len(series) * step + 0.45, 3)
            self.js.append(f'tl.fromTo("#{i}-hb", {{ opacity: 0, scale: 1.04 }}, {{ opacity: 1, scale: 1, duration: 0.35, ease: "power2.out" }}, {th});')

    def _chart_counter(self, o: dict) -> None:
        """Cifra grande que cuenta desde 0 hasta `value` (T10f), con etiqueta y subtítulo."""
        i = o["id"]; at = o.get("at", o["start"])
        value = float(o["value"]); dec = int(o.get("decimals", 0)); dur = float(o.get("duration", 1.2))
        prefix = esc(o.get("prefix", "")); suffix = esc(o.get("suffix", ""))
        start_txt = f"{0:.{dec}f}"
        inner = (f'<div class="num" id="{i}-n">{prefix}<span id="{i}-nv">{start_txt}</span><b>{suffix}</b></div>'
                 + (f'<div class="lab" id="{i}-l">{esc(o["label"])}</div>' if o.get("label") else "")
                 + (f'<div class="sub">{esc(o["subtitle"])}</div>' if o.get("subtitle") else ""))
        cls, style = self._chart_frame(o, "counter")
        self.timed(o, style, cls=cls, inner=inner, z=5 if not o.get("panel") else 4, track=6)
        self.js.append(f'tl.fromTo("#{i}-n", {{ opacity: 0, y: 30 }}, {{ opacity: 1, y: 0, duration: 0.35, ease: "power3.out" }}, {at});')
        # contador: tween sobre un objeto; onUpdate escribe el texto (funciona con seek, que es lo que usa el render)
        self.js.append(f'{{ const c = {{ v: 0 }}; const el = () => document.getElementById("{i}-nv"); '
                       f'tl.to(c, {{ v: {value}, duration: {dur}, ease: "power2.out", onUpdate: () => {{ const e = el(); if (e) e.textContent = c.v.toFixed({dec}); }} }}, {round(at + 0.1, 3)}); }}')
        if o.get("label"):
            self.js.append(f'tl.fromTo("#{i}-l", {{ opacity: 0, y: 20 }}, {{ opacity: 1, y: 0, duration: 0.35, ease: "power3.out" }}, {round(at + 0.35, 3)});')

    def draw(self, o: dict) -> None:
        """Icono o trazo que se dibuja (DrawSVG): `icon` de la lista incluida, `paths` propios o un `src` SVG inline."""
        i = o["id"]; at = o.get("at", o["start"]); dur = o.get("duration", 0.6)
        color = o.get("color", "#ffffff"); sw = o.get("stroke_width", 2)
        if o.get("src"):
            svg = (Path(self.sb_dir) / o["src"]).read_text(encoding="utf-8") if self.sb_dir else Path(o["src"]).read_text(encoding="utf-8")
            svg = safe_svg(svg[svg.find("<svg"):], f"overlay {i} (draw.src)")
        else:
            paths = o.get("paths") or ICONS.get(o.get("icon", "check")) or ICONS["check"]
            vb = o.get("viewBox", "0 0 24 24")
            svg = f'<svg viewBox="{vb}" xmlns="http://www.w3.org/2000/svg" stroke-width="{sw}">' + "".join(f'<path d="{d}"/>' for d in paths) + "</svg>"
        style = f"left:{o['x']}px; top:{o['y']}px; width:{o['w']}px; height:{o.get('h', o['w'])}px; color:{color};"
        self.timed(o, style, cls="draw", inner=svg, z=4, track=7)
        self.uses_draw = True
        self.js.append(f'tl.set("#{i}", {{ opacity: 1 }}, {at}); tl.fromTo("#{i} svg *", {{ drawSVG: "0%" }}, {{ drawSVG: "100%", duration: {dur}, stagger: {round(dur * 0.35, 3)}, ease: "power2.inOut" }}, {at});')
        self.fade_out(f"#{i}", o["end"])

    # ---------- subtítulos ----------
    def _bright_caption_band(self, bottom: int, height: int, samples: int = 8) -> bool:
        """¿La franja donde van los subtítulos es clara en el vídeo de origen? Mira `samples` fotogramas repartidos y la
        da por clara si en al menos un tercio la luminancia media pasa de 0,62 (un gráfico sobre blanco, una mesa, el
        fondo desenfocado de un vertical con blur). Sin vídeo, o si no se puede leer, False: no cambia nada."""
        src = (self.sb.get("source") or {}).get("video")
        if not src or not self.sb_dir:
            return False
        path = Path(self.sb_dir) / src
        if not path.exists():
            return False
        try:
            import cv2
            cap = cv2.VideoCapture(str(path))
            n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0
            if n <= 0:
                cap.release(); return False
            bright = seen = 0
            for k in range(samples):
                cap.set(cv2.CAP_PROP_POS_FRAMES, int((k + 0.5) * n / samples))
                ok, frame = cap.read()
                if not ok:
                    continue
                h = frame.shape[0]
                y1 = h - int(bottom * h / self.H); y0 = max(0, y1 - int(height * h / self.H))
                band = cv2.cvtColor(frame[y0:y1], cv2.COLOR_BGR2GRAY)
                if band.size:
                    seen += 1
                    bright += band.mean() / 255 > 0.62
            cap.release()
            return seen > 0 and bright * 3 >= seen
        except Exception:  # noqa: BLE001
            return False

    def captions(self, sb: dict) -> None:
        """Por frase (`captions`, preset `phrase`) o por palabras (`caption_style.preset` = `pages` | `karaoke`, a
        partir de `caption_style.words`, un words.json relativo al storyboard)."""
        style = sb.get("caption_style") or {}
        preset = style.get("preset", "phrase")
        bottom = int(style.get("bottom", 56 if not self.narrow else 200))
        if preset in ("pages", "karaoke"):
            from .captions import load_words, pages as make_pages
            wp = style.get("words", "words.json")
            src = (Path(self.sb_dir) / wp) if self.sb_dir else Path(wp)
            if not src.exists():
                self.warnings.append(f"caption_style.words no encontrado: {src}; sin subtítulos"); return
            pgs = make_pages(load_words(src), max_words=int(style.get("max_words", 4)),
                             max_gap=float(style.get("max_gap", 0.6)), hold=float(style.get("hold", 0.8)),
                             max_chars=int(style.get("max_chars", 22 if self.narrow else 30)))
            size = int(style.get("size", 72 if self.narrow else 64))
            upper = " upper" if style.get("uppercase", True) else ""
            backdrop = style.get("backdrop", "auto")
            if backdrop == "auto":
                bright = self._bright_caption_band(bottom, round(size * 2.4))
                backdrop = "box" if bright else "none"
                if bright:
                    self.warnings.append("subtítulos: la franja de abajo es clara en el vídeo; se ponen sobre caja (caption_style.backdrop "
                                         "box/stroke/none para elegir otra cosa)")
            upper += f" bd-{backdrop}" if backdrop in ("box", "stroke") else ""
            html_pages = []
            for k, p in enumerate(pgs):
                ws = "".join(f'<span class="pw" id="pg{k}w{j}">{esc(w["text"])}</span>' for j, w in enumerate(p["words"]))
                html_pages.append(f'<div class="pg" id="pg{k}">{ws}</div>')
            self.html.append(f'<div id="caps" class="clip pages mode-{preset}{upper}" data-start="0" data-duration="{self.dur}" data-track-index="8" '
                             f'style="z-index:9; inset:auto; left:0; right:0; bottom:{bottom}px; height:{round(size * 2.4)}px; font-size:{size}px;">{"".join(html_pages)}</div>')
            acc = self.brand["accent"]
            for k, p in enumerate(pgs):
                self.js.append(f'tl.set("#pg{k}", {{ visibility: "visible" }}, {p["start"]}); tl.set("#pg{k}", {{ visibility: "hidden" }}, {p["end"]});')
                for j, w in enumerate(p["words"]):
                    sel = f"#pg{k}w{j}"
                    if preset == "pages":
                        self.js.append(f'tl.fromTo("{sel}", {{ opacity: 0, scale: 0.7 }}, {{ opacity: 1, scale: 1, duration: 0.14, ease: "back.out(2)" }}, {w["start"]});')
                    else:
                        self.js.append(f'tl.set("{sel}", {{ color: "{acc}", scale: 1.08 }}, {w["start"]}); tl.set("{sel}", {{ color: "rgba(255,255,255,.92)", scale: 1 }}, {max(w["end"], w["start"] + 0.08)});')
            self.caption_count = len(pgs)
            return
        caps = sb.get("captions", [])
        self.caption_count = len(caps)
        if caps:
            spans = "".join(f'<span id="cap{k}">{esc(c["text"])}</span>' for k, c in enumerate(caps))
            self.html.append(f'<div id="caps" class="clip caps" data-start="0" data-duration="{self.dur}" data-track-index="8" '
                             f'style="z-index:9; inset:auto; left:0; right:0; bottom:{bottom}px; height:70px;">{spans}</div>')
            for k, c in enumerate(caps):
                self.js.append(f'tl.set("#cap{k}", {{ visibility: "visible" }}, {c["start"]}); tl.set("#cap{k}", {{ visibility: "hidden" }}, {c["end"]});')

    # ---------- documento ----------
    def build(self) -> str:
        sb = self.sb; src = sb["source"]
        video = self.asset(src["video"])
        clip_dur = float(src["duration"])
        self.html.append(f'<video id="bg" class="clip cover" data-start="0" data-duration="{clip_dur}" data-track-index="0" src="{video}" muted playsinline style="z-index:1"></video>')
        if src.get("audio"):
            audio = self.asset(src["audio"])
            self.html.append(f'<audio id="voice" data-start="0" data-duration="{clip_dur}" data-track-index="9" src="{audio}"></audio>')
        for o in sb.get("overlays", []):
            t = o["type"]
            if t not in OVERLAY_TYPES:
                self.warnings.append(f"overlay {o.get('id')}: tipo desconocido '{t}', ignorado"); continue
            getattr(self, t)(o)
        self.captions(sb)
        b = self.brand
        css = (CSS.replace("{W}", str(self.W)).replace("{H}", str(self.H)).replace("{accent}", b["accent"]).replace("{on_accent}", b["on_accent"]).replace("{ink}", b["ink"])
               .replace("{paper}", b["paper"]).replace("{grey}", b["grey"]).replace("{sans}", b["sans"]).replace("{mono}", b["mono"])
               .replace("{capsize}", str(b["caption_font_size"])))
        body = "\n      ".join(self.html); js = "\n      ".join(self.js)
        fl = self.brand_meta.get("font_link")
        font_link = f'    <link rel="stylesheet" href="{esc(fl)}">\n' if fl else ""
        plugins = ""
        if self.uses_split:
            plugins += f'    <script src="https://cdn.jsdelivr.net/npm/gsap@{GSAP_VERSION}/dist/SplitText.min.js"></script>\n'
        if self.uses_draw:
            plugins += f'    <script src="https://cdn.jsdelivr.net/npm/gsap@{GSAP_VERSION}/dist/DrawSVGPlugin.min.js"></script>\n'
        font_link = plugins + font_link
        reg = []
        if self.uses_split:
            reg.append("SplitText")
        if self.uses_draw:
            reg.append("DrawSVGPlugin")
        js = (f"gsap.registerPlugin({', '.join(reg)});\n      " if reg else "") + js
        lang = sb.get("meta", {}).get("lang", "es")
        return f"""<!doctype html>
<html lang="{lang}" data-resolution="{"portrait" if self.H > self.W else "landscape"}">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width={self.W}, height={self.H}" />
    <script src="https://cdn.jsdelivr.net/npm/gsap@{GSAP_VERSION}/dist/gsap.min.js"></script>
{font_link}    <style>{css}    </style>
  </head>
  <body>
    <!-- Generado por Frame28 a partir de storyboard.json. Edita el storyboard, no este fichero. -->
    <div id="root" class="{"narrow" if self.narrow else ""}" data-composition-id="main" data-start="0" data-duration="{self.dur}" data-width="{self.W}" data-height="{self.H}">
      {body}
    </div>
    <script>
      const tl = gsap.timeline({{ paused: true }});
      {js}
      window.__timelines = window.__timelines || {{}};
      window.__timelines["main"] = tl;
      tl.seek(0);
    </script>
  </body>
</html>
"""


# ── Seguridad del HTML generado (F28-84) ─────────────────────────────────────────────────────────────────────────────
# El storyboard lo escribe el agente a partir de transcripciones, vídeos y webs de clientes: una inyección de prompt podía
# colar un id, un color, una ruta o un SVG que ejecutara JS en el Chrome de check/render (con red). Los textos ya se
# escapan con esc(); el resto de valores se valida aquí, en la entrada, con el formato que puede tener cada campo.
ID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,63}$")                        # también lo exige GSAP: un espacio rompía el selector
COLOR_RE = re.compile(r"^(#[0-9a-fA-F]{3,8}|rgba?\(\s*[\d.%\s,]+\)|hsla?\(\s*[\d.%\s,deg]+\)|[a-zA-Z]{3,20})$")
PATH_D_RE = re.compile(r"^[MmLlHhVvCcSsQqTtAaZz0-9eE\s,.+-]+$")
VIEWBOX_RE = re.compile(r"^-?[\d.]+(\s+-?[\d.]+){3}$")
LANG_RE = re.compile(r"^[a-z]{2,3}(-[A-Za-z]{2,4})?$")
NUM_KEYS = {"start", "end", "at", "x", "y", "w", "h", "size", "duration", "value", "stroke_width", "logo_width", "in",
            "before_t", "after_t", "matte_start", "matte_end", "decimals", "stagger", "total", "bottom", "max_words"}
PATH_KEYS = {"src", "matte", "before", "after"}
BG_TOKENS = {"black", "white", "accent", "none"}
ENUMS = {"reveal": {"fade", "rise", "chars"}, "kind": {"bar", "counter"}, "pan": {"left", "right", "up", "down"},
         "sort": {"asc", "desc"}}
SVG_BAD = re.compile(r"<\s*script|<\s*foreignObject|\bon[a-z]+\s*=|javascript\s*:|<\s*iframe|<\s*object|<\s*embed", re.I)
CSS_BAD = re.compile(r"[<>{};]|/\*|\\")


def _is_num(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def safe_rel_path(v) -> bool:
    """Ruta relativa al storyboard: sin unidad ni esquema, sin comillas ni < >, y `..` solo al principio (los storyboards
    de work/ usan ../clip.mp4; "a/../../b" no). Que la copia no escriba fuera del proyecto lo vigila build_project."""
    if not isinstance(v, str) or not v.strip() or len(v) > 400:
        return False
    if v.startswith(("/", "\\")) or re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", v) or any(c in v for c in "\"'<>`\r\n\t"):
        return False
    parts = [p for p in re.split(r"[\\/]", v) if p not in ("", ".")]
    ups = 0
    while ups < len(parts) and parts[ups] == "..":
        ups += 1
    return ups < len(parts) and ".." not in parts[ups:]


def _walk(o, path: str, errs: list[str]) -> None:
    if isinstance(o, dict):
        for k, v in o.items():
            p = f"{path}.{k}"
            if k in NUM_KEYS and not (_is_num(v) or v is None):
                errs.append(f"{p}: tiene que ser un número")
            elif k in ("dot", "box") and isinstance(v, list) and not (len(v) == 2 and all(_is_num(x) for x in v)):
                errs.append(f"{p}: tiene que ser [x, y] con números")
            elif k == "color" and not (isinstance(v, str) and COLOR_RE.match(v.strip())):
                errs.append(f"{p}: color no válido (#hex, rgb(), hsl() o un nombre)")
            elif k == "bg" and not (isinstance(v, str) and (v in BG_TOKENS or COLOR_RE.match(v.strip()))):
                errs.append(f"{p}: fondo no válido (black, white, accent, none o un color)")
            elif k in PATH_KEYS and isinstance(v, str) and not safe_rel_path(v):
                errs.append(f"{p}: ruta no permitida (relativa al storyboard, .. solo al principio, sin C:\\ ni esquemas)")
            elif k in ENUMS and v is not None and v not in ENUMS[k]:
                errs.append(f"{p}: valor no válido '{v}' ({', '.join(sorted(ENUMS[k]))})")
            elif k == "paths" and not (isinstance(v, list) and all(isinstance(d, str) and PATH_D_RE.match(d) for d in v)):
                errs.append(f"{p}: cada trazado SVG solo admite órdenes y números (M, L, C, Z…)")
            elif k == "viewBox" and not (isinstance(v, str) and VIEWBOX_RE.match(v.strip())):
                errs.append(f"{p}: viewBox tiene que ser cuatro números")
            else:
                _walk(v, p, errs)
    elif isinstance(o, list):
        for n, v in enumerate(o):
            _walk(v, f"{path}[{n}]", errs)


def safety_errors(sb: dict) -> list[str]:
    """Formatos de lo que acaba en atributos, estilos, JS o rutas del HTML generado (los textos se escapan aparte)."""
    errs: list[str] = []
    for n, o in enumerate(sb.get("overlays", [])):
        oid = o.get("id")
        if oid is not None and not (isinstance(oid, str) and ID_RE.match(oid)):
            errs.append(f"overlays[{n}].id: '{oid}' no vale: letra inicial y luego letras, cifras, - o _ (sin espacios)")
        _walk({k: v for k, v in o.items() if k not in ("id", "type")}, f"overlays[{n}]", errs)
    src = sb.get("source") or {}
    for k in ("video", "audio"):
        if src.get(k) is not None and not safe_rel_path(src[k]):
            errs.append(f"source.{k}: ruta no permitida (relativa al storyboard, .. solo al principio, sin C:\\ ni esquemas)")
    lang = (sb.get("meta") or {}).get("lang")
    if lang and not (isinstance(lang, str) and LANG_RE.match(lang)):
        errs.append(f"meta.lang: '{lang}' no es un idioma (es, en, pt-BR…)")
    for n, c in enumerate(sb.get("captions", []) or []):
        for k in ("start", "end"):
            if k in c and not _is_num(c[k]):
                errs.append(f"captions[{n}].{k}: tiene que ser un número")
    return errs


HEX_RE = re.compile(r"^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})([0-9a-fA-F]{2})?$")


def _rgb(color: str) -> tuple[float, float, float] | None:
    m = HEX_RE.match(color.strip()) if isinstance(color, str) else None
    if not m:
        return None
    h = m.group(1)
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def _luminance(rgb) -> float:
    def lin(c):
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (lin(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(a: str, b: str) -> float | None:
    """Contraste WCAG entre dos colores hex (#rgb o #rrggbb); None si alguno no es hex."""
    ra, rb = _rgb(a), _rgb(b)
    if ra is None or rb is None:
        return None
    la, lb = sorted((_luminance(ra), _luminance(rb)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


ON_ACCENT_LIGHT = "#FFFFFF"


def on_accent_color(accent: str, ink: str) -> str:
    """Color del texto sobre el acento: la tinta de la marca si da 4,5:1 o más; si no, el blanco cuando gana en contraste.
    Con colores que no son hex (rgb(), nombres) se queda la tinta, como antes."""
    c_ink = contrast_ratio(ink, accent)
    c_white = contrast_ratio(ON_ACCENT_LIGHT, accent)
    if c_ink is None or c_white is None or c_ink >= 4.5 or c_ink >= c_white:
        return ink
    return ON_ACCENT_LIGHT


def brand_errors(brand: dict) -> list[str]:
    """Valores de la marca que van dentro del <style> generado: colores con formato de color y fuentes sin caracteres que
    cierren la regla o la etiqueta."""
    errs = []
    if brand.get("accent_pending"):
        cands = ", ".join(str(c.get("color")) for c in brand.get("accent_candidates", []) if isinstance(c, dict))[:120]
        errs.append("marca.accent: por confirmar (brand from-site no lo encontró con certeza"
                    + (f"; candidatos: {cands}" if cands else "") + "). Pregunta al usuario y guárdalo con: "
                    "frame28 brand set <marca> --accent #RRGGBB")
    for k in ("accent", "ink", "paper", "grey", "border", "on_accent"):
        v = brand.get(k)
        if v is not None and not (isinstance(v, str) and COLOR_RE.match(v.strip())):
            errs.append(f"marca.{k}: color no válido '{v}'")
    for k in ("sans", "mono"):
        v = brand.get(k)
        if v is not None and (not isinstance(v, str) or CSS_BAD.search(v)):
            errs.append(f"marca.{k}: tipografía con caracteres no permitidos (< > {{ }} ; \\)")
    if "caption_font_size" in brand and not _is_num(brand["caption_font_size"]):
        errs.append("marca.caption_font_size: tiene que ser un número")
    fl = brand.get("font_link")
    if fl and not (isinstance(fl, str) and fl.startswith("https://") and not re.search(r"[\"'<>`\s\\]", fl)):
        errs.append("marca.font_link: tiene que ser una URL https:// sin comillas, espacios ni < >")
    return errs


def safe_svg(svg: str, origin: str) -> str:
    """El SVG de draw.src entra tal cual en la página: sin scripts, manejadores on…= ni enlaces javascript:."""
    if SVG_BAD.search(svg):
        raise SystemExit(f"{origin}: el SVG trae scripts, manejadores de eventos o contenido incrustado; usa uno limpio (solo trazos)")
    return svg


def validate(sb: dict) -> list[str]:
    """Validación ligera del storyboard: devuelve lista de errores (vacía si es válido)."""
    errs = []
    if sb.get("version") != 1:
        errs.append("version debe ser 1")
    src = sb.get("source") or {}
    for k in ("video", "duration"):
        if k not in src:
            errs.append(f"source.{k} es obligatorio")
    dur = float(sb.get("duration", src.get("duration", 0)) or 0)
    ids = set()
    for n, o in enumerate(sb.get("overlays", [])):
        p = f"overlays[{n}]"
        for k in ("type", "id", "start", "end"):
            if k not in o:
                errs.append(f"{p}: falta '{k}'")
        if o.get("id") in ids:
            errs.append(f"{p}: id duplicado '{o.get('id')}'")
        ids.add(o.get("id"))
        if o.get("type") not in OVERLAY_TYPES:
            errs.append(f"{p}: tipo desconocido '{o.get('type')}' (válidos: {sorted(OVERLAY_TYPES)})")
        if "start" in o and "end" in o:
            if o["end"] <= o["start"]:
                errs.append(f"{p}: end debe ser > start")
            if dur and o["end"] > dur + 0.01:
                errs.append(f"{p}: end {o['end']} supera la duración {dur}")
        t = o.get("type")
        req = {"lower_third": ["x", "y", "title"], "box": ["x", "y", "text"], "kinetic": ["x", "y", "lines"],
               "behind": ["text", "matte"], "pointer": ["dot", "box", "text"], "card": ["title"],
               "list_focus": ["items"], "card_words": ["lines"], "image": ["src", "x", "y", "w"], "brand_card": [], "chart": ["kind"], "draw": ["x", "y", "w"],
               "broll": ["src"], "hook": [], "cta": [], "steps": ["items"], "before_after": []}.get(t, [])
        if t == "hook" and not (o.get("text") or o.get("lines")):
            errs.append(f"{p} (hook): falta 'text' o 'lines'")
        for k in req:
            if k not in o:
                errs.append(f"{p} ({t}): falta '{k}'")
        if t == "chart":
            if o.get("kind") == "bar" and not o.get("series"):
                errs.append(f"{p} (chart bar): falta 'series' [{{label, value, group?}}]")
            if o.get("kind") == "counter" and "value" not in o:
                errs.append(f"{p} (chart counter): falta 'value'")
    for n, c in enumerate(sb.get("captions", [])):
        for k in ("start", "end", "text"):
            if k not in c:
                errs.append(f"captions[{n}]: falta '{k}'")
    cs = sb.get("caption_style")
    if cs is not None:
        if not isinstance(cs, dict):
            errs.append("caption_style debe ser un objeto {preset, words?, size?, bottom?, max_words?, uppercase?}")
        elif cs.get("preset", "phrase") not in ("phrase", "pages", "karaoke"):
            errs.append(f"caption_style.preset desconocido '{cs.get('preset')}' (phrase, pages, karaoke)")
    cv = sb.get("canvas") or {}
    if cv and (int(cv.get("width", 1920)) < 480 or int(cv.get("height", 1080)) < 480):
        errs.append("canvas demasiado pequeño (mínimo 480 px de lado)")
    if sb.get("platform") not in (None, "tiktok", "reels", "shorts", "youtube", "pdp"):
        errs.append("platform debe ser tiktok, reels, shorts, youtube o pdp")
    errs += safety_errors(sb)
    if isinstance(sb.get("brand"), dict):
        errs += brand_errors(sb["brand"])
    return errs


def platform_warnings(sb: dict) -> list[str]:
    """Zonas de la interfaz del móvil que tapan overlays en vertical: columna derecha de iconos, franja inferior
    (descripción, barra) y franja superior. Solo avisa; el storyboard decide."""
    plat = sb.get("platform")
    W = int(sb.get("canvas", {}).get("width", 1920)); H = int(sb.get("canvas", {}).get("height", 1080))
    if not plat or plat in ("youtube", "pdp") or H <= W:
        return []
    from .graphics import overlay_bbox, _iou
    zones = {"columna derecha de iconos": [W - 150, int(0.35 * H), W, int(0.88 * H)],
             "franja inferior (descripción y barra)": [0, int(0.84 * H), W, H],
             "franja superior (estado y pestañas)": [0, 0, W, int(0.08 * H)]}
    out = []
    for o in sb.get("overlays", []):
        bb = overlay_bbox(o, W, H)
        if bb is None:
            continue
        for name, z in zones.items():
            if _iou(bb, z) > 0.03 or (bb[0] < z[2] and bb[2] > z[0] and bb[1] < z[3] and bb[3] > z[1] and (min(bb[2], z[2]) - max(bb[0], z[0])) * (min(bb[3], z[3]) - max(bb[1], z[1])) > 0.15 * (bb[2] - bb[0]) * (bb[3] - bb[1])):
                out.append(f"{o['id']} ({o['type']}) cae en la {name} de {plat}")
                break
    caps = sb.get("caption_style") or {}
    if sb.get("captions") or caps:
        bottom = int(caps.get("bottom", 200 if H > W else 56))
        if bottom < int(0.16 * H):
            out.append(f"subtítulos a {bottom} px del borde: en {plat} quedan bajo la descripción; usa caption_style.bottom >= {int(0.16 * H)}")
    return out


def build_project(storyboard_path: str | Path, out_dir: str | Path, copy_assets: bool = True) -> dict:
    sb_path = Path(storyboard_path)
    sb = json.loads(sb_path.read_text(encoding="utf-8-sig"))
    errs = validate(sb)
    if errs:
        raise SystemExit("Storyboard inválido:\n  - " + "\n  - ".join(errs))
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    b = Builder(sb, out)
    b.sb_dir = sb_path.parent
    b.warnings.extend(platform_warnings(sb))
    from .i18n import leftovers
    b.warnings.extend(f"sin traducir: {w}" for w in leftovers(sb))
    html_text = b.build()
    (out / "index.html").write_text(html_text, encoding="utf-8")
    (out / "hyperframes.json").write_text(json.dumps({
        "$schema": "https://hyperframes.heygen.com/schema/hyperframes.json",
        "registry": "https://raw.githubusercontent.com/heygen-com/hyperframes/main/registry",
        "paths": {"blocks": "compositions", "components": "compositions/components", "assets": "assets"},
        "media": {"autoProxy": True}}, indent=2), encoding="utf-8")
    (out / "package.json").write_text(json.dumps({
        "name": out.name, "private": True, "type": "module",
        "scripts": {"dev": f"npx --yes hyperframes@{HYPERFRAMES_VERSION} preview", "check": f"npx --yes hyperframes@{HYPERFRAMES_VERSION} check",
                    "render": f"npx --yes hyperframes@{HYPERFRAMES_VERSION} render"}}, indent=2), encoding="utf-8")
    if not (out / "meta.json").exists():
        (out / "meta.json").write_text(json.dumps({"id": out.name, "name": sb.get("meta", {}).get("title", out.name)}, indent=2), encoding="utf-8")
    copied = []
    if copy_assets:
        for rel in sorted(b.assets):
            if not safe_rel_path(rel):   # ya lo filtra validate(); por si un asset llega por otro camino
                b.warnings.append(f"asset con ruta no permitida, no se copia: {rel}"); continue
            src = (sb_path.parent / rel)
            dst = out / rel
            if not dst.resolve().is_relative_to(out.resolve()):   # ../clip.mp4: se usa en su sitio, nunca se escribe fuera
                if not dst.exists():
                    b.warnings.append(f"asset fuera del proyecto, no se copia: {rel} (no existe {dst}; pon el proyecto junto a él)")
                continue
            if src.exists():
                dst.parent.mkdir(parents=True, exist_ok=True)
                if src.resolve() != dst.resolve():
                    shutil.copy2(src, dst)
                copied.append(rel)
            else:
                b.warnings.append(f"asset no encontrado: {src}")
        for pub, srcfile in b.brand_assets.items():
            dst = out / pub; dst.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(srcfile, dst); copied.append(pub)
    return {"project": str(out), "index": str(out / "index.html"), "overlays": len(sb.get("overlays", [])),
            "captions": getattr(b, "caption_count", len(sb.get("captions", []))), "canvas": [b.W, b.H],
            "assets": copied, "warnings": b.warnings}
