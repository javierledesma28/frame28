"""Generador: storyboard.json → proyecto HyperFrames (index.html + assets).

El LLM decide el storyboard (qué técnica, qué texto, cuándo y dónde). Este módulo lo convierte de forma
determinista en HTML + CSS + una timeline GSAP, siguiendo las reglas que verificamos en la PoC:
capas con z-index explícito, todo elemento temporizado con id, posiciones inline, fades cortos.
"""
from __future__ import annotations

import html
import json
import math
import shutil
from pathlib import Path

from . import HYPERFRAMES_VERSION

OVERLAY_TYPES = {"lower_third", "box", "kinetic", "behind", "pointer", "card", "list_focus", "card_words", "image"}

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
      :root { --accent: {accent}; --ink: {ink}; --paper: {paper}; --grey: {grey}; --sans: {sans}; --mono: {mono}; }
      #root { position: relative; width: {W}px; height: {H}px; font-family: var(--sans); color: #fff; }
      .clip { position: absolute; inset: 0; }
      video.cover { width: 100%; height: 100%; object-fit: cover; }
      .c { position: absolute; width: 18px; height: 18px; border: 0 solid currentColor; }
      .tl { top: -6px; left: -6px; border-top-width: 3px; border-left-width: 3px; }
      .tr { top: -6px; right: -6px; border-top-width: 3px; border-right-width: 3px; }
      .bl { bottom: -6px; left: -6px; border-bottom-width: 3px; border-left-width: 3px; }
      .br { bottom: -6px; right: -6px; border-bottom-width: 3px; border-right-width: 3px; }
      .box { position: absolute; padding: 10px 26px; font-size: 54px; font-weight: 500; letter-spacing: -0.03em; color: #fff; background: rgba(0,0,0,.45); white-space: nowrap; opacity: 0; }
      .lower { position: absolute; font-family: var(--mono); font-size: 34px; color: #fff; opacity: 0; }
      .lower .line { overflow: hidden; white-space: nowrap; border: 1.5px solid rgba(255,255,255,.9); padding: 12px 22px; background: rgba(0,0,0,.45); }
      .lower .line + .line { border-top: 0; }
      .lower .mask { display: inline-block; overflow: hidden; white-space: nowrap; vertical-align: bottom; width: 0; }
      .lower .cur { color: var(--accent); }
      .lower .c { width: 18px; height: 18px; } .lower .tl { top: -9px; left: -9px; } .lower .br { bottom: -9px; right: -9px; }
      .kin { position: absolute; font-weight: 600; line-height: 1.02; letter-spacing: -0.045em; text-shadow: 0 6px 30px rgba(0,0,0,.55); }
      .kin .w { display: inline-block; opacity: 0; margin-right: 0.22em; }
      .accent { color: var(--accent); }
      .behind { display: flex; align-items: center; justify-content: center; }
      .behind .w { font-weight: 700; letter-spacing: -0.05em; white-space: nowrap; text-shadow: 0 8px 40px rgba(0,0,0,.35); opacity: 0; }
      .conn { position: absolute; height: 3px; background: #fff; transform-origin: left center; width: 0; }
      .dot { position: absolute; width: 18px; height: 18px; border-radius: 50%; background: #fff; box-shadow: 0 0 0 6px rgba(255,255,255,.25); transform: scale(0); }
      .card { display: flex; flex-direction: column; align-items: center; justify-content: center; }
      .card.black { background: #000; color: #fff; }
      .card.white { background: var(--paper); color: var(--ink); }
      .card.accent { background: var(--accent); color: var(--ink); }
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
      .caps span { visibility: hidden; position: absolute; left: 50%; transform: translateX(-50%); bottom: 0; background: #000; color: #fff; padding: 8px 20px; white-space: nowrap; font-size: {capsize}px; }
"""


def esc(s: str) -> str:
    return html.escape(str(s), quote=True)


class Builder:
    def __init__(self, sb: dict, project_dir: Path):
        self.sb = sb
        self.dir = project_dir
        brand = sb.get("brand", {})
        if isinstance(brand, str):  # "think28" → brands/think28.json incluido en el paquete, o ruta a un JSON propio
            cand = Path(__file__).with_name("brands") / f"{brand}.json"
            path = cand if cand.exists() else Path(brand)
            brand = json.loads(path.read_text(encoding="utf-8"))
        self.brand = {**DEFAULT_BRAND, **{k: v for k, v in brand.items() if k in DEFAULT_BRAND}}
        self.brand_meta = brand
        canvas = sb.get("canvas", {})
        self.W = int(canvas.get("width", 1920)); self.H = int(canvas.get("height", 1080)); self.fps = int(canvas.get("fps", 30))
        self.dur = float(sb["source"]["duration"])
        self.html: list[str] = []
        self.js: list[str] = []
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

    def box_in(self, sel: str, at: float) -> None:
        self.js.append(f'tl.fromTo("{sel}", {{ opacity: 0, scale: 0.9 }}, {{ opacity: 1, scale: 1, duration: 0.2, ease: "power2.out" }}, {at});')

    def asset(self, rel: str) -> str:
        self.assets.add(rel)
        return rel

    # ---------- overlays ----------
    def lower_third(self, o: dict) -> None:
        i = o["id"]; t = o["start"]
        title = esc(o["title"]); sub = esc(o.get("subtitle", ""))
        inner = (f'<i class="c tl"></i><i class="c br"></i>'
                 f'<div class="line"><span class="mask" id="{i}-l1"><span class="cur">◌</span>&nbsp;{title}&nbsp;&nbsp;&nbsp;&nbsp;×</span></div>'
                 + (f'<div class="line"><span class="mask" id="{i}-l2">{sub}<span class="cur">▌</span></span></div>' if sub else ""))
        self.timed(o, f"left:{o['x']}px; top:{o['y']}px;", cls="lower", inner=inner, z=4, track=3)
        w1 = 34 * 0.62 * (len(o["title"]) + 8); w2 = 34 * 0.62 * (len(o.get("subtitle", "")) + 2)
        self.js.append(f'tl.fromTo("#{i}", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.2 }}, {t});')
        self.js.append(f'tl.fromTo("#{i}-l1", {{ width: 0 }}, {{ width: {round(w1)}, duration: {round(min(0.9, 0.05 * len(o["title"]) + 0.3), 2)}, ease: "none" }}, {round(t + 0.1, 3)});')
        if sub:
            self.js.append(f'tl.fromTo("#{i}-l2", {{ width: 0 }}, {{ width: {round(w2)}, duration: {round(min(1.2, 0.04 * len(sub) + 0.3), 2)}, ease: "none" }}, {round(t + 0.9, 3)});')
        self.fade_out(f"#{i}", o["end"], 0.25)

    def box(self, o: dict) -> None:
        self.timed(o, f"left:{o['x']}px; top:{o['y']}px;", cls="box", inner=self.corners() + esc(o["text"]), z=4, track=4)
        self.box_in(f"#{o['id']}", o.get("at", o["start"]))
        self.fade_out(f"#{o['id']}", o["end"])

    def kinetic(self, o: dict) -> None:
        i = o["id"]; size = o.get("size", 124)
        rows = []
        for li, line in enumerate(o["lines"]):
            spans = "".join(f'<span class="w{" accent" if w.get("accent") else ""}" id="{i}-{li}-{wi}">{esc(w["text"])}</span>' for wi, w in enumerate(line))
            rows.append(f"<div>{spans}</div>")
        self.timed(o, f"left:{o['x']}px; top:{o['y']}px; font-size:{size}px;", cls="kin", inner="".join(rows), z=4, track=5)
        for li, line in enumerate(o["lines"]):
            for wi, w in enumerate(line):
                self.pop(f"#{i}-{li}-{wi}", w["at"])
        self.fade_out(f"#{i}", o["end"])

    def behind(self, o: dict) -> None:
        """Texto detrás del hablante: capa 2 = texto, capa 3 = vídeo con alfa (solo en su tramo)."""
        i = o["id"]; size = o.get("size", 240)
        self.timed(o, "", cls="clip behind", inner=f'<div class="w" id="{i}-w" style="font-size:{size}px;">{esc(o["text"])}</div>', z=2, track=1)
        m = self.asset(o["matte"]); ms = o.get("matte_start", o["start"]); me = o.get("matte_end", o["end"])
        self.html.append(f'<video id="{i}-fg" class="clip cover" data-start="{ms}" data-duration="{round(me - ms, 3)}" data-track-index="2" '
                         f'src="{m}" muted playsinline style="z-index:3"></video>')
        at = o.get("at", o["start"])
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
        inner = f'<div class="big" id="{i}-t" style="font-size:{t.get("size", 190)}px;">{esc(t["text"])}</div>'
        if s:
            inner += f'<div class="small" id="{i}-s" style="font-size:{s.get("size", 72)}px;">{esc(s["text"])}</div>'
        self.timed(o, "", cls=f"clip card {bg}", inner=inner, z=5, track=6)
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

    # ---------- documento ----------
    def build(self) -> str:
        sb = self.sb; src = sb["source"]
        video = self.asset(src["video"])
        self.html.append(f'<video id="bg" class="clip cover" data-start="0" data-duration="{self.dur}" data-track-index="0" src="{video}" muted playsinline style="z-index:1"></video>')
        if src.get("audio"):
            audio = self.asset(src["audio"])
            self.html.append(f'<audio id="voice" data-start="0" data-duration="{self.dur}" data-track-index="9" src="{audio}"></audio>')
        for o in sb.get("overlays", []):
            t = o["type"]
            if t not in OVERLAY_TYPES:
                self.warnings.append(f"overlay {o.get('id')}: tipo desconocido '{t}', ignorado"); continue
            getattr(self, t)(o)
        caps = sb.get("captions", [])
        if caps:
            spans = "".join(f'<span id="cap{k}">{esc(c["text"])}</span>' for k, c in enumerate(caps))
            self.html.append(f'<div id="caps" class="clip caps" data-start="0" data-duration="{self.dur}" data-track-index="8" '
                             f'style="z-index:9; inset:auto; left:0; right:0; bottom:56px; height:70px;">{spans}</div>')
            for k, c in enumerate(caps):
                self.js.append(f'tl.set("#cap{k}", {{ visibility: "visible" }}, {c["start"]}); tl.set("#cap{k}", {{ visibility: "hidden" }}, {c["end"]});')
        b = self.brand
        css = (CSS.replace("{W}", str(self.W)).replace("{H}", str(self.H)).replace("{accent}", b["accent"]).replace("{ink}", b["ink"])
               .replace("{paper}", b["paper"]).replace("{grey}", b["grey"]).replace("{sans}", b["sans"]).replace("{mono}", b["mono"])
               .replace("{capsize}", str(b["caption_font_size"])))
        body = "\n      ".join(self.html); js = "\n      ".join(self.js)
        lang = sb.get("meta", {}).get("lang", "es")
        return f"""<!doctype html>
<html lang="{lang}" data-resolution="landscape">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width={self.W}, height={self.H}" />
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
    <style>{css}    </style>
  </head>
  <body>
    <!-- Generado por Frame28 a partir de storyboard.json. Edita el storyboard, no este fichero. -->
    <div id="root" data-composition-id="main" data-start="0" data-duration="{self.dur}" data-width="{self.W}" data-height="{self.H}">
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


def validate(sb: dict) -> list[str]:
    """Validación ligera del storyboard: devuelve lista de errores (vacía si es válido)."""
    errs = []
    if sb.get("version") != 1:
        errs.append("version debe ser 1")
    src = sb.get("source") or {}
    for k in ("video", "duration"):
        if k not in src:
            errs.append(f"source.{k} es obligatorio")
    dur = float(src.get("duration", 0) or 0)
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
               "list_focus": ["items"], "card_words": ["lines"], "image": ["src", "x", "y", "w"]}.get(t, [])
        for k in req:
            if k not in o:
                errs.append(f"{p} ({t}): falta '{k}'")
    for n, c in enumerate(sb.get("captions", [])):
        for k in ("start", "end", "text"):
            if k not in c:
                errs.append(f"captions[{n}]: falta '{k}'")
    return errs


def build_project(storyboard_path: str | Path, out_dir: str | Path, copy_assets: bool = True) -> dict:
    sb_path = Path(storyboard_path)
    sb = json.loads(sb_path.read_text(encoding="utf-8"))
    errs = validate(sb)
    if errs:
        raise SystemExit("Storyboard inválido:\n  - " + "\n  - ".join(errs))
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    b = Builder(sb, out)
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
            src = (sb_path.parent / rel)
            dst = out / rel
            if src.exists():
                dst.parent.mkdir(parents=True, exist_ok=True)
                if src.resolve() != dst.resolve():
                    shutil.copy2(src, dst)
                copied.append(rel)
            else:
                b.warnings.append(f"asset no encontrado: {src}")
    return {"project": str(out), "index": str(out / "index.html"), "overlays": len(sb.get("overlays", [])),
            "captions": len(sb.get("captions", [])), "assets": copied, "warnings": b.warnings}
