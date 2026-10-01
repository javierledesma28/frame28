# -*- coding: utf-8 -*-
"""Ensambla frame28.app: plantilla común (head, cabecera, pie) + fragmentos de `src/{es,en}/` + condiciones desde
`content/*.md`. El HTML resultante se commitea y Cloudflare Pages sirve `site/` tal cual, sin build en el despliegue.

    uv run --with markdown python site/build.py        # desde la raíz del repo (o desde site/)

Lo que cambia entre publicaciones vive en CONFIG (plazas de Fundadores, buzón, si el caso es público).
"""
from __future__ import annotations

import re
from pathlib import Path

import markdown

SITE = Path(__file__).resolve().parent
CONFIG = {
    "seats": 5,                      # plazas libres de Fundadores
    "mail": "hola@frame28.app",      # buzón que responde (y remite del formulario)
    "case_public": False,            # True solo con permiso escrito del cliente; el nombre real nunca se escribe aquí hasta entonces
    "case_brand": "[[marca]]",       # nombre público del cliente del caso cuando case_public sea True
    "case_slug": "marca",            # carpeta casos/<slug>/ y en/cases/<slug>/
    "year": 2026,
}

STRINGS = {
    "es": {
        "lang": "es", "home": "/", "alt_lang": "English", "alt_href": "/en/", "font_lang": "es",
        "nav": [("Cómo funciona", "/#como-funciona"), ("Precios", "/#precios"), ("Fundadores", "/fundadores/"), ("Preguntas", "/#faq")],
        "cta": ("Contacto", "/contacto/"),
        "footer": [("Área de clientes", "/kb/"), ("Curso online", "/curso/"), ("Plugin abierto", "https://frame28.t28.io"), ("Roadmap", "https://frame28.t28.io/roadmap/"),
                   ("Condiciones", "/condiciones/"), ("Contacto", "/contacto/"), ("GitHub", "https://github.com/javierledesma28/frame28")],
        "footer_line": "Frame28 es un producto de <a href=\"https://t28.io\">Think28</a> · © {year} Think28",
        "form": {
            "name": "Nombre", "email": "Email", "brand": "Marca o web", "video": "Enlace al vídeo (YouTube, Drive, lo que tengas)",
            "interest": "Qué te interesa", "options": [("launch", "Launch · paquete de arranque"), ("studio", "Studio · mensual"),
                                                        ("team", "Team · en tu equipo"), ("founders", "Fundadores"), ("cloud", "Lista de espera de Cloud")],
            "message": "Mensaje (opcional)", "send": "Enviar", "sending": "Enviando…",
            "privacy": "Solo usamos estos datos para responderte. Nada de listas ni terceros.",
            "ok": "Recibido. Te escribimos en un día laborable desde {mail}.",
            "err": "No se ha podido enviar. Escríbenos directamente a {mail}.",
        },
    },
    "en": {
        "lang": "en", "home": "/en/", "alt_lang": "Español", "alt_href": "/", "font_lang": "en",
        "nav": [("How it works", "/en/#how"), ("Pricing", "/en/#pricing"), ("Founders", "/en/founders/"), ("FAQ", "/en/#faq")],
        "cta": ("Contact", "/en/contact/"),
        "footer": [("Customer area", "/en/kb/"), ("Online course", "/en/course/"), ("Open plugin", "https://frame28.t28.io"), ("Roadmap", "https://frame28.t28.io/roadmap/"),
                   ("Terms", "/en/terms/"), ("Contact", "/en/contact/"), ("GitHub", "https://github.com/javierledesma28/frame28")],
        "footer_line": "Frame28 is a <a href=\"https://t28.io\">Think28</a> product · © {year} Think28",
        "form": {
            "name": "Name", "email": "Email", "brand": "Brand or website", "video": "Link to the video (YouTube, Drive, whatever you have)",
            "interest": "What you're interested in", "options": [("launch", "Launch · starter package"), ("studio", "Studio · monthly"),
                                                                  ("team", "Team · in-house"), ("founders", "Founders"), ("cloud", "Cloud waitlist")],
            "message": "Message (optional)", "send": "Send", "sending": "Sending…",
            "privacy": "We only use this to reply to you. No lists, no third parties.",
            "ok": "Received. We'll write to you within one business day from {mail}.",
            "err": "It couldn't be sent. Email us directly at {mail}.",
        },
    },
}

PAGES = [
    # (idioma, fragmento, ruta publicada, title, description)
    ("es", "index.html", "index.html", "Frame28 · Envías un vídeo. Recibes la campaña.",
     "Convertimos un vídeo de tu marca en el largo montado, shorts verticales con ganchos distintos, portada, ficha de producto, subtítulos y versiones en otros idiomas. Generado por código, revisado por una persona, entregado en días."),
    ("es", "fundadores.html", "fundadores/index.html", "Fundadores · Frame28", "Cinco marcas con el precio de lanzamiento congelado doce meses, voto en el roadmap y canal directo."),
    ("es", "contacto.html", "contacto/index.html", "Contacto · Frame28", "Cuéntanos qué vendes y mándanos un vídeo. Respondemos en un día laborable."),
    ("en", "index.html", "en/index.html", "Frame28 · Send the video. Get the campaign.",
     "We turn one brand video into the edited long version, vertical shorts with different hooks, a cover, a product-page version, subtitles and translated versions. Generated by code, reviewed by a person, delivered in days."),
    ("en", "founders.html", "en/founders/index.html", "Founders · Frame28", "Five brands with launch pricing locked for twelve months, a vote on the roadmap and a direct line."),
    ("en", "contact.html", "en/contact/index.html", "Contact · Frame28", "Tell us what you sell and send us a video. We reply within one business day."),
]
TERMS = [
    ("es", "content/condiciones.es.md", "condiciones/index.html", "Condiciones del servicio · Frame28"),
    ("en", "content/terms.en.md", "en/terms/index.html", "Terms of Service · Frame28"),
]

CASE = {
    "es": {
        True: """<h2>Caso: {brand}</h2>
      <p class="muted" style="margin-top:12px">{brand} vende kits de grabado a cientos de miles de clientes y publica tutoriales por material. Tomamos su tutorial de vidrio (3:17) y, sin grabar nada nuevo, salió el paquete completo: el largo con pasos en pantalla, notas de seguridad, tarjeta de producto y prueba social; tres shorts de treinta segundos con un gancho distinto cada uno; la portada de YouTube y la versión 1:1 para la ficha; y la versión en español con los mismos tiempos.</p>
      <p style="margin-top:20px"><a class="btn" href="/casos/{slug}/">Ver el caso completo</a></p>""",
        False: """<h2>Caso: un fabricante de kits de grabado</h2>
      <p class="muted" style="margin-top:12px">Un tutorial de 3:17 ya publicado, sin grabar nada nuevo. Salió el largo con pasos en pantalla, notas de seguridad, tarjeta de producto y prueba social; tres shorts de treinta segundos con un gancho distinto cada uno; la portada y la versión 1:1 para la ficha; y la versión en español con los mismos tiempos. Pídenos la muestra y te la enseñamos.</p>
      <p style="margin-top:20px"><a class="btn" href="#contacto" data-plan="launch">Pedir la muestra</a></p>""",
    },
    "en": {
        True: """<h2>Case: {brand}</h2>
      <p class="muted" style="margin-top:12px">{brand} sells engraving kits to hundreds of thousands of customers and publishes one tutorial per material. We took their glass tutorial (3:17) and, without shooting anything new, the whole package came out: the long video with on-screen steps, safety notes, product card and social proof; three thirty-second shorts, each with a different hook; the YouTube cover and the 1:1 product-page version; and a Spanish version with the same timing.</p>
      <p style="margin-top:20px"><a class="btn" href="/en/cases/{slug}/">See the full case</a></p>""",
        False: """<h2>Case: an engraving-kit brand</h2>
      <p class="muted" style="margin-top:12px">A 3:17 tutorial already published, nothing new shot. Out came the long video with on-screen steps, safety notes, product card and social proof; three thirty-second shorts, each with a different hook; the cover and the 1:1 product-page version; and a Spanish version with the same timing. Ask for the sample and we'll show you.</p>
      <p style="margin-top:20px"><a class="btn" href="#contact" data-plan="launch">Ask for the sample</a></p>""",
    },
}


def form_html(lang: str, preselect: str | None = None) -> str:
    f = STRINGS[lang]["form"]; mail = CONFIG["mail"]
    opts = "".join(f'<option value="{v}"{" selected" if v == preselect else ""}>{t}</option>' for v, t in f["options"])
    return f"""<form class="form" method="post" action="/api/contact" data-ok="{f['ok'].format(mail=mail)}" data-err="{f['err'].format(mail=mail)}" data-sending="{f['sending']}">
      <input type="hidden" name="lang" value="{lang}">
      <input type="hidden" name="page" value="">
      <div class="row">
        <label>{f['name']}<input type="text" name="name" required autocomplete="name" maxlength="120"></label>
        <label>{f['email']}<input type="email" name="email" required autocomplete="email" maxlength="200"></label>
      </div>
      <div class="row">
        <label>{f['brand']}<input type="text" name="brand" autocomplete="organization" maxlength="200"></label>
        <label>{f['interest']}<select name="interest">{opts}</select></label>
      </div>
      <label>{f['video']}<input type="url" name="video" placeholder="https://" maxlength="500"></label>
      <label>{f['message']}<textarea name="message" maxlength="4000"></textarea></label>
      <label class="hp" aria-hidden="true">Website<input type="text" name="website" tabindex="-1" autocomplete="off"></label>
      <div class="msg" role="status" aria-live="polite"></div>
      <div><button class="btn" type="submit">{f['send']}</button></div>
      <p class="privacy">{f['privacy']}</p>
    </form>"""


FORM_JS = """<script>
(function () {
  // Formularios: envío por fetch con mensaje en la página; sin JS, el POST normal al mismo endpoint también funciona.
  var q = new URLSearchParams(location.search);   // vuelta del envío sin JS: /contacto/?ok=1 o ?error=1
  document.querySelectorAll('form.form').forEach(function (form) {
    form.querySelector('input[name=page]').value = location.pathname;
    if (q.has('ok') || q.has('error')) {
      var m = form.querySelector('.msg'); m.textContent = q.has('ok') ? form.dataset.ok : form.dataset.err; m.className = 'msg ' + (q.has('ok') ? 'ok' : 'err');
    }
    form.addEventListener('submit', function (ev) {
      ev.preventDefault();
      var msg = form.querySelector('.msg'); var btn = form.querySelector('button[type=submit]'); var label = btn.textContent;
      msg.className = 'msg'; form.classList.add('busy'); btn.textContent = form.dataset.sending;
      var data = {}; new FormData(form).forEach(function (v, k) { data[k] = v; });
      fetch(form.action, { method: 'POST', headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' }, body: JSON.stringify(data) })
        .then(function (r) { return r.ok ? r.json() : Promise.reject(r); })
        .then(function () { msg.textContent = form.dataset.ok; msg.className = 'msg ok'; form.reset(); })
        .catch(function () { msg.textContent = form.dataset.err; msg.className = 'msg err'; })
        .finally(function () { form.classList.remove('busy'); btn.textContent = label; });
    });
  });
  // Los botones de precios preseleccionan el interés en el formulario de la misma página.
  document.querySelectorAll('[data-plan]').forEach(function (a) {
    a.addEventListener('click', function () {
      var sel = document.querySelector('form.form select[name=interest]');
      if (sel) sel.value = a.dataset.plan;
    });
  });
})();
</script>"""


def layout(lang: str, title: str, description: str, body: str, path: str, noindex: bool = False) -> str:
    s = STRINGS[lang]
    nav = "".join(f'<a href="{h}">{t}</a>' for t, h in s["nav"])
    foot = "".join(f'<a href="{h}">{t}</a>' for t, h in s["footer"])
    canonical = "https://frame28.app/" + path.replace("index.html", "")
    robots = '<meta name="robots" content="noindex, nofollow">\n' if noindex else ""
    return f"""<!doctype html>
<html lang="{s['lang']}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{title}</title>
<meta name="description" content="{description}">
{robots}<link rel="canonical" href="{canonical}">
<link rel="alternate" hreflang="es" href="https://frame28.app/">
<link rel="alternate" hreflang="en" href="https://frame28.app/en/">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{description}">
<meta property="og:type" content="website">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="https://frame28.app/assets/og.png">
<meta name="theme-color" content="#0A0A0A">
<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&family=Space+Mono:wght@400;700&display=swap">
<link rel="stylesheet" href="/assets/site.css">
</head>
<body>
<header class="top">
  <div class="wrap">
    <a class="brand" href="{s['home']}">Frame28 <small>by Think28</small></a>
    <nav class="nav">{nav}<a class="lang" href="{s['alt_href']}" hreflang="{'en' if lang == 'es' else 'es'}">{s['alt_lang']}</a><a class="btn sm" href="{s['cta'][1]}">{s['cta'][0]}</a></nav>
  </div>
</header>
<main>
{body}
</main>
<footer>
  <div class="wrap">
    <a href="https://t28.io"><img src="/assets/think28-horizontal.svg" alt="Think28 · Digital Growth Partner" width="440" height="72"></a>
    <div class="links">{foot}</div>
    <p>{s['footer_line'].format(year=CONFIG['year'])}</p>
  </div>
</footer>
{FORM_JS}
</body>
</html>
"""


def fill(lang: str, html: str) -> str:
    seats = str(CONFIG["seats"])
    html = html.replace("{{SEATS}}", seats)
    html = html.replace("{{FORM_ES}}", form_html("es")).replace("{{FORM_EN}}", form_html("en"))
    html = html.replace("{{FORM_ES_FOUNDERS}}", form_html("es", "founders")).replace("{{FORM_EN_FOUNDERS}}", form_html("en", "founders"))
    case = {k: CASE[k][CONFIG["case_public"]].replace("{brand}", CONFIG["case_brand"]).replace("{slug}", CONFIG["case_slug"]) for k in ("es", "en")}
    if CONFIG["case_public"]:
        assert "[[" not in CONFIG["case_brand"], "case_public=True exige el nombre real del cliente en CONFIG['case_brand'] (con su permiso escrito)"
    html = html.replace("{{CASE_ES}}", case["es"]).replace("{{CASE_EN}}", case["en"])
    assert "{{" not in html, re.search(r"\{\{[^}]+\}\}", html).group(0)
    return html


def terms_html(md_path: Path) -> tuple[str, str]:
    text = md_path.read_text(encoding="utf-8")
    text = re.sub(r"<!--.*?-->\s*", "", text, count=1, flags=re.S)       # la nota interna del borrador no se publica
    m = re.match(r"# (.+)\n", text); h1 = (m.group(1) if m else md_path.stem).split(" · ")[0]   # sin el sufijo interno "· contrato base (ES)"
    text = text[m.end():] if m else text
    body = markdown.markdown(text, extensions=["tables", "sane_lists"])
    body = re.sub(r"\[\[(.+?)\]\]", r'<span class="todo">[[\1]]</span>', body)   # huecos visibles hasta rellenarlos
    return h1, body


# ---------- área de clientes: base de conocimiento y curso (tras Cloudflare Access) ----------
SECTIONS = {
    # clave: (idioma → ruta publicada, título, descripción del índice, etiqueta de minutos, texto de "volver")
    "kb": {
        "es": ("kb", "Base de conocimiento", "Lo que necesitas saber para sacarle partido a Frame28: qué mandar, cómo grabar, cómo revisar y qué puedes publicar.", "min de lectura", "Base de conocimiento"),
        "en": ("en/kb", "Knowledge base", "What you need to get the most out of Frame28: what to send, how to shoot, how to review and what you can publish.", "min read", "Knowledge base"),
    },
    "curso": {
        "es": ("curso", "Curso online", "Seis lecciones cortas, grabadas a cámara y montadas con Frame28. Incluido en Launch, Studio y Team.", "min", "Curso online"),
        "en": ("en/course", "Online course", "Six short lessons, shot to camera and edited with Frame28. Included with Launch, Studio and Team.", "min", "Online course"),
    },
}
GATE = {
    "es": ("Área de clientes", "Acceso con el email con el que contrataste. Incluido en Launch (12 meses), Studio y Team.", "/contacto/", "¿Aún no eres cliente?"),
    "en": ("Customer area", "Sign in with the email you ordered with. Included with Launch (12 months), Studio and Team.", "/en/contact/", "Not a customer yet?"),
}
TIER_LABEL = {"es": {"all": "todos los planes", "team": "solo Team"}, "en": {"all": "all plans", "team": "Team only"}}
VIDEO_PENDING = {"es": "Vídeo en preparación: se graba a cámara y se monta con Frame28. Mientras tanto, el guion está debajo.",
                 "en": "Video in preparation: shot to camera and edited with Frame28. The script is below in the meantime."}


def front_matter(text: str) -> tuple[dict, str]:
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if not m:
        return {}, text
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1); meta[k.strip()] = v.strip()
    return meta, text[m.end():]


def render_md(text: str) -> str:
    body = markdown.markdown(text, extensions=["tables", "sane_lists"])
    return re.sub(r"\[\[(.+?)\]\]", r'<span class="todo">[[\1]]</span>', body)


def gate_html(lang: str) -> str:
    g = GATE[lang]
    return f'<div class="gate"><span class="eyebrow">{g[0]}</span><span class="muted small">{g[1]} <a href="{g[2]}">{g[3]}</a></span></div>'


def render_section(key: str, lang: str) -> list[str]:
    base, title, desc, mins_label, back = SECTIONS[key][lang]
    src = sorted((SITE / "content" / key / lang).glob("*.md"))
    entries = []
    for p in src:
        meta, body = front_matter(p.read_text(encoding="utf-8"))
        entries.append({"slug": p.stem.split("-", 1)[-1] if p.stem[:2].isdigit() else p.stem, "meta": meta, "body": body, "order": int(meta.get("order", 99))})
    entries.sort(key=lambda e: e["order"])
    out = []
    # índice
    cards = []
    for e in entries:
        m = e["meta"]; tier = m.get("tier", "all")
        badge = f'<span class="tag">{TIER_LABEL[lang][tier]}</span>' if tier != "all" else ""
        cards.append(f'<a class="card entry" href="/{base}/{e["slug"]}/"><span class="n">{e["order"]:02d} · {m.get("minutes", "")} {mins_label}</span>'
                     f'<h3>{m.get("title", e["slug"])}</h3><p class="muted">{m.get("summary", "")}</p>{badge}</a>')
    body = (f'<section class="hero"><div class="wrap" style="grid-template-columns:1fr"><div class="copy">{gate_html(lang)}'
            f'<p class="eyebrow">{title}</p><h1>{title}</h1><p class="lead">{desc}</p></div></div></section>'
            f'<section><div class="wrap"><div class="grid c2 entries">{"".join(cards)}</div></div></section>')
    path = f"{base}/index.html"
    (SITE / path).parent.mkdir(parents=True, exist_ok=True)
    (SITE / path).write_text(layout(lang, f"{title} · Frame28", desc, body, path, noindex=True), encoding="utf-8", newline="\n"); out.append(path)
    # páginas
    for i, e in enumerate(entries):
        m = e["meta"]; prev = entries[i - 1] if i > 0 else None; nxt = entries[i + 1] if i + 1 < len(entries) else None
        video = ""
        if key == "curso":
            url = m.get("video", "")
            video = (f'<div class="video"><iframe src="{url}" title="{m.get("title", "")}" allow="fullscreen" loading="lazy"></iframe></div>' if url
                     else f'<div class="video pending"><span>{VIDEO_PENDING[lang]}</span></div>')
        nav = '<nav class="pager">'
        nav += f'<a href="/{base}/{prev["slug"]}/">← {prev["meta"].get("title", "")}</a>' if prev else "<span></span>"
        nav += f'<a href="/{base}/">{back}</a>'
        nav += f'<a href="/{base}/{nxt["slug"]}/">{nxt["meta"].get("title", "")} →</a>' if nxt else "<span></span>"
        nav += "</nav>"
        tier = m.get("tier", "all")
        badge = f' <span class="tag">{TIER_LABEL[lang][tier]}</span>' if tier != "all" else ""
        body = (f'<section><div class="wrap"><article class="prose">{gate_html(lang)}'
                f'<p class="eyebrow">{title} · {e["order"]:02d} · {m.get("minutes", "")} {mins_label}{badge}</p>'
                f'<h1>{m.get("title", "")}</h1><p class="lead">{m.get("summary", "")}</p>{video}{render_md(e["body"])}{nav}</article></div></section>')
        path = f"{base}/{e['slug']}/index.html"
        (SITE / path).parent.mkdir(parents=True, exist_ok=True)
        (SITE / path).write_text(layout(lang, f"{m.get('title', '')} · {title} · Frame28", m.get("summary", ""), body, path, noindex=True), encoding="utf-8", newline="\n"); out.append(path)
    return out


def main() -> None:
    out_paths = []
    for key in SECTIONS:
        for lang in ("es", "en"):
            out_paths += render_section(key, lang)
    for lang, frag, path, title, desc in PAGES:
        body = fill(lang, (SITE / "src" / lang / frag).read_text(encoding="utf-8"))
        html = layout(lang, title, desc, body, path)
        p = SITE / path; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(html, encoding="utf-8", newline="\n"); out_paths.append(path)
    for lang, md, path, title in TERMS:
        h1, body = terms_html(SITE / md)
        body = f'<section><div class="wrap"><article class="prose"><h1>{h1}</h1>{body}</article></div></section>'
        html = layout(lang, title, title, body, path)
        p = SITE / path; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(html, encoding="utf-8", newline="\n"); out_paths.append(path)
    print("\n".join(f"  {p}" for p in out_paths))
    todo = sum((SITE / p).read_text(encoding="utf-8").count('class="todo"') for p in out_paths)
    print(f"  {len(out_paths)} páginas · plazas Fundadores: {CONFIG['seats']} · caso público: {CONFIG['case_public']} · huecos [[…]] en condiciones: {todo}")


if __name__ == "__main__":
    main()
