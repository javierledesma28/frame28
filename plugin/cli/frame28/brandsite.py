"""Marca a partir de una web: colores, fuente y logo del sitio del cliente → brand.json listo para el storyboard.

Lo que hacía a mano el director con el primer caso de marca: bajar la portada y sus hojas de estilo, contar los colores,
leer las variables CSS de marca (Shopify y similares las exponen), la fuente más repetida, el logo (el del header antes
que la imagen social) y generar variantes del logo para fondo oscuro y de acento. Es una propuesta con su nivel de
confianza y sus avisos: el agente la revisa con el usuario (`frame28 brand show`) antes de usarla.

Hallado con una marca real (F28-79): la marca nueva heredaba logos, reglas de logo y voz de Think28 (copiaba
think28.json); el acento salía rosa (#EA77A1, un respaldo fijo) porque los colores de verdad estaban en las hojas CSS
enlazadas, y el logo era la og:image de 1200×630 con márgenes. Ahora: plantilla neutra, hojas CSS incluidas, el acento
puntúa los colores del logo y del CSS, el logo del header gana a la og:image (que se recorta a su contenido) y la salida
dice cuándo la confianza es baja.
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
CHROMA_MIN_SAT = 0.25    # un candidato a acento tiene color de verdad
MAX_PAGE = 3_000_000     # bytes: portada y hojas CSS
MAX_LOGO = 5_000_000
MAX_CSS_FILES = 6

# Variables CSS de widgets y librerías de terceros: su color es el del widget (o el valor por defecto de la librería), no el
# de la marca. Probado sobre 20 webs DTC (F28-299): en 5 el acento salía solo de Okendo (--oke-*) o Judge.me (--jdgm-*),
# en otra del admin de WordPress (--wp-admin-theme-color) y en otra de Swiper (--swiper-theme-color). El resto son widgets
# habituales en tiendas: reseñas, email, chat, cookies, sliders, reproductores, buscadores, fidelización y pagos.
THIRD_PARTY_VAR_PREFIXES = (
    "oke-", "jdgm-", "yotpo-", "stamped-", "loox-", "reviewsio-",                                            # reseñas
    "wp-admin-", "woocommerce", "wc-", "wpforms-", "gform",                                                   # WordPress y plugins
    "swiper-", "slick-", "splide-", "glide-", "flickity-", "plyr-", "pswp", "fancybox-", "lightbox-",          # sliders y reproductores
    "klaviyo-", "privy-", "omnisend-", "mailchimp-", "hubspot-", "hs-",                                        # email y marketing
    "gorgias-", "intercom-", "crisp-", "tidio-", "zendesk-", "drift-", "tawk-",                                # chat
    "onetrust-", "cky-", "pandectes-",                                                                        # cookies
    "hawksearch-", "algolia-", "searchspring-", "boost-", "nosto-", "rebuy-", "recharge-", "smile-", "loyaltylion-",
    "shopify-pay", "shop-pay", "payment-button", "paypal-", "klarna-", "afterpay-", "affirm-", "sezzle-", "gpay-", "applepay-",
    "trustpilot-", "elfsight-",
)
THIRD_PARTY_VAR_WORDS = ("cookie", "consent")
# Colores por defecto de librerías, pagos y redes sociales: aparecen en el CSS de muchas webs sin ser de la marca (Bootstrap,
# Swiper, Plyr, WordPress, WooCommerce, Shop Pay, PayPal, Google, Stripe, Facebook, X, Instagram, YouTube, Pinterest,
# WhatsApp, LinkedIn, Reddit, Discord, TikTok, Vimeo, Trustpilot). No cuentan como evidencia del CSS; en el logo sí.
LIBRARY_COLORS = frozenset({
    "#0d6efd", "#6610f2", "#6f42c1", "#d63384", "#dc3545", "#fd7e14", "#ffc107", "#198754", "#20c997", "#0dcaf0",
    "#007bff", "#28a745", "#17a2b8", "#007aff", "#00b3ff",
    "#007cba", "#0073aa", "#2271b1", "#3858e9", "#1e73be", "#720eec", "#7f54b3", "#96588a",
    "#5a31f4", "#ffc439", "#0070ba", "#003087", "#009cde", "#4285f4", "#ea4335", "#34a853", "#fbbc05", "#635bff",
    "#1877f2", "#4267b2", "#3b5998", "#1da1f2", "#e4405f", "#e1306c", "#c13584", "#ff0000", "#e60023", "#bd081c",
    "#25d366", "#128c7e", "#0077b5", "#0a66c2", "#ff4500", "#5865f2", "#7289da", "#ff0050", "#00f2ea", "#1ab7ea", "#00b67a",
    "#108474",   # Judge.me (visto como valor por defecto en su CSS y «configurado» igual en otra web)
})
WIDGET_FONT_WORDS = ("icon", "awesome", "emoji", "symbol", "glyph", "star", "judgeme", "jdgm", "okendo", "yotpo", "stamped",
                     "loox", "swiper", "slick", "icomoon", "klaviyo")
GENERIC_FONTS = frozenset({"inherit", "initial", "unset", "revert", "sans-serif", "serif", "monospace", "cursive", "fantasy",
                           "system-ui", "ui-sans-serif", "ui-serif", "ui-monospace", "ui-rounded", "math", "emoji", "fangsong"})
SYSTEM_FONTS = frozenset({"system_ui", "system-ui", "-apple-system", "blinkmacsystemfont", "segoe ui", "helvetica neue", "helvetica",
                          "arial", "times new roman", "times", "courier new", "courier", "georgia", "verdana", "tahoma",
                          "apple color emoji", "segoe ui emoji", "segoe ui symbol", "noto color emoji"})

# Lo que necesita el motor y nada más: ni logos, ni reglas de logo, ni voz de ninguna otra marca (antes se copiaba
# think28.json entero y un vídeo del cliente podía salir con elementos de Think28).
TEMPLATE = {
    "paper": "#FFFFFF", "grey": "#666666",
    "sans": 'Inter, "Segoe UI", Arial, sans-serif',
    "mono": '"Space Mono", "Cascadia Mono", Consolas, monospace',
    "display_weight": 800, "display_tracking": "-0.03em",
    "motion": {"standard_ms": 240, "fast_ms": 120, "slow_ms": 400},
    "caption_font_size": 40,
}


def host_is_public(url: str) -> bool:
    """¿Resuelve el host a direcciones públicas? No: localhost, la red local, link-local (169.254.169.254, los metadatos
    de la nube), reservadas o multicast. Si no resuelve, tampoco."""
    import ipaddress
    import socket
    host = urllib.parse.urlparse(url).hostname
    if not host:
        return False
    try:
        addrs = {a[4][0] for a in socket.getaddrinfo(host, None)}
    except OSError:
        return False
    for a in addrs:
        ip = ipaddress.ip_address(a.split("%")[0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast or ip.is_unspecified:
            return False
    return bool(addrs)


def _check_url(url: str, public_only: bool) -> None:
    if urllib.parse.urlparse(url).scheme not in ("http", "https"):
        raise ValueError(f"esquema no permitido: {url[:60]}")
    if public_only and not host_is_public(url):
        raise ValueError(f"dirección interna o que no resuelve, no se descarga: {url[:80]}")


class _GuardedRedirect(urllib.request.HTTPRedirectHandler):
    """Cada redirección pasa la misma comprobación que la URL original (una pública no puede llevar a una interna)."""

    def __init__(self, public_only: bool):
        self.public_only = public_only

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        _check_url(newurl, self.public_only)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _get(url: str, binary: bool = False, timeout: int = 30, max_bytes: int = MAX_PAGE, public_only: bool = True):
    """Solo http(s), con tope de tamaño y, para lo que dice la web (`public_only`), solo hosts públicos, también tras
    cada redirección (F28-85): una web comprometida con og:image a file:///… o http://169.254.169.254/… ya no mete un
    fichero local o una respuesta interna en la carpeta de la marca. Lo que pasa el usuario (la web, --logo-url) va con
    public_only=False."""
    _check_url(url, public_only)
    opener = urllib.request.build_opener(_GuardedRedirect(public_only))
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with opener.open(req, timeout=timeout) as r:
        data = r.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise ValueError(f"demasiado grande (más de {max_bytes // 1_000_000} MB): {url[:60]}")
    return data if binary else data.decode("utf-8", errors="replace")


def looks_like_image(data: bytes) -> bool:
    """PNG, JPEG, GIF, WebP, ICO o SVG por sus primeros bytes: un «logo» que es una página HTML o un JSON no se guarda."""
    head = data[:512].lstrip()
    return (data[:8] == b"\x89PNG\r\n\x1a\n" or data[:3] == b"\xff\xd8\xff" or data[:4] in (b"GIF8", b"\x00\x00\x01\x00")
            or (data[:4] == b"RIFF" and data[8:12] == b"WEBP") or head.startswith(b"<svg") or (head.startswith(b"<?xml") and b"<svg" in data[:2048]))


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


def _chromatic(h: str) -> bool:
    sat, lum = _sat_lum(_hex_to_rgb(h))
    return sat > CHROMA_MIN_SAT and 0.15 < lum < 0.88


def _hue(h: str) -> float:
    r, g, b = (c / 255 for c in _hex_to_rgb(h))
    mx, mn = max(r, g, b), min(r, g, b)
    if mx == mn:
        return 0.0
    d = mx - mn
    hue = ((g - b) / d) % 6 if mx == r else (b - r) / d + 2 if mx == g else (r - g) / d + 4
    return (hue * 60) % 360


def _hue_dist(a: str, b: str) -> float:
    d = abs(_hue(a) - _hue(b))
    return min(d, 360 - d)


def css_colors(text: str) -> list[str]:
    """Colores de un HTML o CSS: #rrggbb, #rgb y rgb()/rgba() (sin blanco ni negro puros)."""
    out = []
    for h in re.findall(r"#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})(?![0-9a-fA-F])", text):
        out.append("#" + ("".join(c * 2 for c in h) if len(h) == 3 else h).lower())
    for r, g, b in re.findall(r"rgba?\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})", text):
        if max(int(r), int(g), int(b)) <= 255:
            out.append("#%02x%02x%02x" % (int(r), int(g), int(b)))
    return [c for c in out if c not in ("#000000", "#ffffff")]


def stylesheets(html: str, base_url: str) -> list[str]:
    """Hojas CSS enlazadas de la portada, las del mismo sitio primero (las de terceros suelen ser fuentes o widgets)."""
    host = urllib.parse.urlparse(base_url).netloc.replace("www.", "")
    links = []
    for tag in re.findall(r"<link\b[^>]*>", html, re.I):
        if re.search(r"rel=[\"']?stylesheet", tag, re.I):
            m = re.search(r"href=[\"']([^\"']+)", tag, re.I)
            if m:
                links.append(urllib.parse.urljoin(base_url, m.group(1).replace("&amp;", "&")))
    own = [u for u in links if urllib.parse.urlparse(u).netloc.replace("www.", "").endswith(host)]
    return list(dict.fromkeys(own + [u for u in links if u not in own]))[:MAX_CSS_FILES]


def _attr_logo(tag: str) -> bool:
    return bool(re.search(r"logo|brand|marca", tag, re.I))


def third_party_var(name: str) -> str | None:
    """Prefijo del widget o librería de terceros al que pertenece la variable CSS, o None si es de la propia web."""
    n = name.lower().lstrip("-")
    for p in THIRD_PARTY_VAR_PREFIXES:
        if n.startswith(p):
            return p
    for w in THIRD_PARTY_VAR_WORDS:
        if w in n:
            return w
    return None


def custom_properties(text: str) -> dict[str, list[str]]:
    """Todas las variables CSS (--nombre: valor) del HTML y sus hojas, en orden (una puede definirse varias veces)."""
    props: dict[str, list[str]] = {}
    for name, val in re.findall(r"--([A-Za-z0-9_-]+)\s*:\s*([^;}]{1,200})", text):
        props.setdefault(name.lower(), []).append(val.strip())
    return props


def resolve_vars(value: str, props: dict[str, list[str]], depth: int = 0) -> str:
    """Sustituye cada var(--x[, respaldo]) por su definición (recursivo, hasta 6 niveles); sin definición, el respaldo.
    Las webs reales encadenan variables (--badge-font-family: var(--font-body--family)) y una misma variable puede estar
    definida varias veces (`inherit` y la buena): se usa la primera definición que se resuelve."""
    if depth > 6 or "var(" not in value:
        return value

    def sub(m: re.Match) -> str:
        name, fallback = m.group(1).lower(), (m.group(2) or "").strip()
        keyword = None   # `inherit`/`initial` en un ámbito no tapan la definición de verdad en otro
        for cand in props.get(name, []):
            r = resolve_vars(cand, props, depth + 1)
            if "var(" in r:
                continue
            if r.strip().lower() in ("inherit", "initial", "unset", "revert", "none"):
                keyword = keyword or r
                continue
            return r
        if fallback:
            return resolve_vars(fallback, props, depth + 1)
        return keyword if keyword is not None else m.group(0)
    return re.sub(r"var\(\s*--([A-Za-z0-9_-]+)\s*(?:,\s*([^()]*(?:\([^()]*\))?[^()]*))?\)", sub, value)


def first_family(value: str) -> str | None:
    """Primera familia con nombre propio de un `font-family` ya resuelto; None si la pila es genérica, de sistema, de
    iconos o sigue sin resolver (nunca devuelve «var»)."""
    fams = [f.strip().strip("'\"").strip() for f in value.replace("!important", "").split(",")]
    fams = [f for f in fams if f]
    if not fams or fams[0].lower() in SYSTEM_FONTS:
        return None
    for f in fams:
        low = f.lower()
        if low in GENERIC_FONTS or low in SYSTEM_FONTS or any(w in low for w in WIDGET_FONT_WORDS):
            continue
        return f if re.match(r"^[A-Za-z][A-Za-z0-9 _.-]{1,39}$", f) else None
    return None


def analyze_html(html: str, base_url: str, css: str = "") -> dict:
    """Colores (frecuencia en el HTML y sus hojas CSS), variables CSS de color de la propia web (las de widgets de terceros
    aparte, en `ignored_vars`), fuentes con las variables resueltas y candidatos a logo."""
    text = html + "\n" + css
    counts = Counter(css_colors(text))
    props = custom_properties(text)
    css_vars: dict[str, str] = {}
    ignored_vars: dict[str, str] = {}
    for name, val in re.findall(r"--([a-z0-9-]*(?:button|primary|accent|brand|highlight|main|theme)[a-z0-9-]*)\s*:\s*([^;}]{3,40})",
                                text, re.I):
        v = resolve_vars(val.strip(), props)
        m = re.match(r"^(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})$", v)
        if m:
            v = "#%02x%02x%02x" % tuple(int(x) for x in m.groups())
        found = css_colors(v)
        if found or re.match(r"^#[0-9a-fA-F]{6}$", v):
            color = (found[0] if found else v).lower()
            (ignored_vars if third_party_var(name) else css_vars).setdefault(name.lower(), color)
    fonts: Counter = Counter()
    spelling: dict[str, str] = {}
    for raw in re.findall(r"(?<![\w-])font-family\s*:\s*([^;}]{2,200})", text):   # no `--env-font-family:` (es una variable)
        fam = first_family(resolve_vars(raw, props))
        if fam:
            spelling.setdefault(fam.lower(), fam)
            fonts[fam.lower()] += 1
    # Logo: <img>/<svg> del header o con logo/brand en clase, id, alt o ruta; después iconos de alta resolución; la og:image al final
    header = (re.search(r"<header\b.*?</header>", html, re.I | re.S) or re.search(r"<nav\b.*?</nav>", html, re.I | re.S))
    head_html = header.group(0) if header else ""
    logos, inline_svg = [], None
    for scope, strong in ((head_html, True), (html, False)):
        tags = re.findall(r"<img\b[^>]*>", scope, re.I)
        for tag in sorted(tags, key=lambda t: not _attr_logo(t)):   # en el header, primero la que dice logo (no el carrito)
            src = re.search(r"\s(?:data-)?src=[\"']([^\"']+)", tag, re.I)
            if src and (strong or _attr_logo(tag)) and not src.group(1).startswith("data:"):
                logos.append(urllib.parse.urljoin(base_url, src.group(1).replace("&amp;", "&")))
        if inline_svg is None:
            for m in re.finditer(r"<svg\b[^>]*>.*?</svg>", scope, re.I | re.S):
                open_tag = m.group(0)[:m.group(0).find(">") + 1]
                if (strong or _attr_logo(open_tag)) and len(m.group(0)) > 80 and _attr_logo(open_tag + scope[max(0, m.start() - 200):m.start()]):
                    inline_svg = m.group(0)
                    break
    for m in re.findall(r"""(?:src|href|content)=["']([^"']*logo[^"']*\.(?:svg|png|webp|jpg)[^"']*)["']""", html, re.I):
        logos.append(urllib.parse.urljoin(base_url, m.replace("&amp;", "&")))
    icons = [urllib.parse.urljoin(base_url, h) for h in re.findall(
        r"<link\b[^>]*rel=[\"'](?:apple-touch-icon|icon)[\"'][^>]*href=[\"']([^\"']+\.(?:svg|png))[\"']", html, re.I)]
    og = re.search(r'property=["\']og:image["\']\s+content=["\']([^"\']+)', html) or \
        re.search(r'content=["\']([^"\']+)["\']\s+property=["\']og:image["\']', html)
    og_image = urllib.parse.urljoin(base_url, og.group(1)) if og else None
    title = re.search(r"<title>([^<]{1,120})</title>", html, re.I)
    desc = re.search(r'name=["\']description["\']\s+content=["\']([^"\']{1,300})', html, re.I)
    return {"colors": counts.most_common(20), "css_vars": css_vars, "ignored_vars": ignored_vars,
            "fonts": [(spelling[k], n) for k, n in fonts.most_common(5)],
            "logos": list(dict.fromkeys(logos))[:5], "inline_svg": inline_svg, "icons": list(dict.fromkeys(icons))[:3],
            "og_image": og_image, "title": title.group(1).strip() if title else "", "description": desc.group(1).strip() if desc else ""}


def svg_colors(svg: str) -> list[str]:
    """Colores de relleno y trazo de un SVG, por número de apariciones."""
    found = re.findall(r"(?:fill|stroke|stop-color)\s*[:=]\s*[\"']?\s*(#[0-9a-fA-F]{3,6}\b|rgba?\([^)]+\))", svg, re.I)
    return [c for c, _ in Counter(c2 for f in found for c2 in css_colors(f)).most_common()]


def image_colors(path: Path, top: int = 4) -> list[str]:
    """Colores dominantes con color de verdad de una imagen (cuantizados, por superficie)."""
    import cv2

    from .imgio import imread, imwrite
    import numpy as np
    im = imread(str(path), cv2.IMREAD_UNCHANGED)
    if im is None:
        return []
    if im.ndim == 2:
        return []
    alpha = im[:, :, 3] > 128 if im.shape[2] == 4 else np.ones(im.shape[:2], bool)
    px = im[:, :, :3][alpha].reshape(-1, 3)
    if len(px) == 0:
        return []
    keys = (px // 16).astype(np.int32)
    keys = keys[:, 0] * 256 + keys[:, 1] * 16 + keys[:, 2]
    uniq, inv, cnt = np.unique(keys, return_inverse=True, return_counts=True)
    sums = np.zeros((len(uniq), 3)); np.add.at(sums, inv, px)
    means = sums / cnt[:, None]                      # el color medio real de cada grupo, no el centro de la cuantización
    out = []
    for i in np.argsort(-cnt)[:64]:
        b, g, r = (int(round(x)) for x in means[i])
        h = "#%02x%02x%02x" % (r, g, b)
        if _chromatic(h) and all(sum(abs(x - y) for x, y in zip(_hex_to_rgb(h), _hex_to_rgb(o))) > 60 for o in out):
            out.append(h)
        if len(out) >= top:
            break
    return out


def propose(analysis: dict, logo_colors: list[str] | None = None) -> dict:
    """Acento = el color con más peso entre los del logo (5, 4, 3…), las variables CSS de marca de la propia web (4; de
    botón 2) y la frecuencia en el CSS (hasta 3). Las variables de widgets de terceros y los colores por defecto de
    librerías, pagos y redes no cuentan (F28-299). Confianza alta solo si manda el logo y ninguna otra fuente del CSS lo
    contradice; con media o baja el acento queda «a confirmar» con sus candidatos: se pregunta en vez de inventar.
    Tinta = el oscuro más frecuente."""
    score: Counter = Counter()
    why: dict[str, list[str]] = {}
    css_vars = {k: v for k, v in analysis["css_vars"].items() if v not in LIBRARY_COLORS}
    # Las reglas CSS del widget repiten el color de sus variables: ese color tampoco cuenta por frecuencia (si además es
    # el de la marca, lo dirán el logo o las variables propias de la web, como pasa cuando Okendo va configurado a juego)
    widget_colors = set(analysis.get("ignored_vars", {}).values())
    colors = [(h, n) for h, n in analysis["colors"] if h not in LIBRARY_COLORS and h not in widget_colors]
    ignored_colors = sorted({h for h, _ in analysis["colors"] if h in LIBRARY_COLORS}
                            | {v for v in analysis["css_vars"].values() if v in LIBRARY_COLORS})
    css_chroma = [h for h, _ in colors if _chromatic(h)] + [v for v in css_vars.values() if _chromatic(v)]

    def twin(c: str) -> str:   # el color del logo (cuantizado) se junta con su gemelo del CSS si son casi iguales
        near = [(sum(abs(a - b) for a, b in zip(_hex_to_rgb(c), _hex_to_rgb(h))), h) for h in css_chroma]
        d, h = min(near) if near else (999, c)
        return h if d <= 48 else c

    for n, c in enumerate(logo_colors or []):
        if _chromatic(c):
            c = twin(c)
            score[c] += max(1, 5 - n); why.setdefault(c, []).append("logo")
    for name, v in css_vars.items():
        if _chromatic(v) and "text" not in name:
            w = 2 if "button" in name else 1 if "highlight" in name else 4
            score[v] += w; why.setdefault(v, []).append(f"--{name}")
    chroma = [(h, n) for h, n in colors if _chromatic(h)]
    top_n = chroma[0][1] if chroma else 0
    for h, n in chroma:
        score[h] += round(3 * n / top_n, 2); why.setdefault(h, []).append(f"css x{n}")
    darks = [h for h, n in analysis["colors"] if _sat_lum(_hex_to_rgb(h))[1] < 0.22]
    ink = darks[0] if darks else "#111111"
    font = analysis["fonts"][0][0] if analysis["fonts"] else None
    warnings = []
    candidates = [{"color": h, "score": round(s, 2), "sources": why.get(h, [])} for h, s in score.most_common(5)]
    if score:
        accent, best = score.most_common(1)[0]
        sources = why.get(accent, [])
        # Contradice al logo otro color, de otro tono, que el CSS avale de verdad (variable propia o frecuencia alta). Otro
        # color del propio logo, o una sombra del mismo tono que el CSS repite, no es una contradicción.
        rivals = [h for h, s in score.most_common() if h != accent and s >= 3 and _hue_dist(h, accent) > 20
                  and any(x != "logo" for x in why.get(h, []))]
        if "logo" in sources and (len(sources) > 1 or not rivals):
            confidence = "alta"
        elif best >= 3:
            confidence = "media"
        else:
            confidence = "baja"
    else:
        accent, sources, confidence = None, [], "baja"
        warnings.append("no se encontró ningún color de marca en la web ni en el logo: pídele el acento al usuario")
    status = "ok" if confidence == "alta" else "a confirmar"
    if status == "a confirmar" and score:
        opts = "; ".join(f"{c['color']} ({', '.join(c['sources'])})" for c in candidates[:4])
        warnings.append(f"acento a confirmar (confianza {confidence}): el mejor candidato es {accent}, pero no lo avala el logo. "
                        f"Pregunta al usuario entre {opts}"
                        + (f"; sin contar {', '.join(ignored_colors[:4])} (colores de librerías, pagos o redes)" if ignored_colors else ""))
    if analysis.get("ignored_vars"):
        pref = sorted({p for p in (third_party_var(n) for n in analysis["ignored_vars"]) if p})
        warnings.append("variables CSS de widgets de terceros ignoradas (" + ", ".join(f"--{p}*" for p in pref)
                        + "): su color es del widget, no de la marca")
    if not font:
        warnings.append("no se detectó la fuente: se queda Inter")
    secondary = [h for h, _ in score.most_common(5) if h != accent][:4]
    logo = analysis.get("logos", [None])[0] if analysis.get("logos") else None
    return {"accent": accent if status == "ok" else None, "accent_suggested": accent, "accent_status": status,
            "candidates": candidates, "ignored_colors": ignored_colors, "ink": ink, "font": font, "secondary": secondary,
            "logo": logo, "confidence": confidence, "accent_sources": sources, "warnings": warnings}


def trim_image(path: Path, tol: int = 18, pad: float = 0.04) -> bool:
    """Recorta una imagen a su contenido (la og:image trae márgenes de color liso). True si recortó algo."""
    import cv2

    from .imgio import imread, imwrite
    import numpy as np
    im = imread(str(path), cv2.IMREAD_UNCHANGED)
    if im is None or im.ndim == 2:
        return False
    h, w = im.shape[:2]
    if im.shape[2] == 4 and (im[:, :, 3] < 16).any():
        mask = im[:, :, 3] > 16
    else:
        corner = np.median(np.array([im[0, 0, :3], im[0, -1, :3], im[-1, 0, :3], im[-1, -1, :3]]), axis=0)
        mask = np.abs(im[:, :, :3].astype(int) - corner).sum(axis=2) > tol
    ys, xs = np.where(mask)
    if len(xs) == 0:
        return False
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    p = int(pad * max(x1 - x0, y1 - y0))
    x0, y0, x1, y1 = max(0, x0 - p), max(0, y0 - p), min(w, x1 + p + 1), min(h, y1 + p + 1)
    if (x1 - x0) * (y1 - y0) > 0.92 * w * h:
        return False
    imwrite(str(path), im[y0:y1, x0:x1])
    return True


def logo_variants(png_path: Path, out_dir: Path, ink: str) -> dict:
    """Del logo original genera on_dark (claro si el logo es oscuro), on_accent (tinta) y on_light (original)."""
    import cv2

    from .imgio import imread, imwrite

    im = imread(str(png_path), cv2.IMREAD_UNCHANGED)
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
    imwrite(str(out_dir / "on_light.png"), im); files["on_light"] = out_dir.name + "/on_light.png"
    imwrite(str(out_dir / "isotipo.png"), im); files["isotipo"] = out_dir.name + "/isotipo.png"
    dark = im.copy(); dark[:, :, :3][op] = (b, g, r)
    imwrite(str(out_dir / "on_accent.png"), dark); files["on_accent"] = out_dir.name + "/on_accent.png"
    if lum < 0.45:  # logo oscuro: en fondo oscuro, en blanco
        white = im.copy(); white[:, :, :3][op] = 255
        imwrite(str(out_dir / "on_dark.png"), white); files["on_dark"] = out_dir.name + "/on_dark.png"
    else:
        imwrite(str(out_dir / "on_dark.png"), im); files["on_dark"] = out_dir.name + "/on_dark.png"
    return files


def _logo(an: dict, logo_url: str | None, ldir: Path, name: str, warnings: list[str]) -> tuple[dict, list[str]]:
    """Baja el logo (el pedido, el del header, uno en línea, un icono o la og:image recortada) y devuelve (info, colores)."""
    info: dict = {"url": None, "files": {}, "kind": None}
    cands = ([(logo_url, "pedido")] if logo_url else []) + [(u, "header") for u in an.get("logos", [])]
    if an.get("inline_svg") and not logo_url:
        ldir.mkdir(parents=True, exist_ok=True)
        (ldir / "original.svg").write_text(an["inline_svg"], encoding="utf-8")
        info.update(url="(svg en la página)", kind="svg en línea",
                    files={k: f"{name}/original.svg" for k in ("isotipo", "on_dark", "on_light", "on_accent")})
        return info, svg_colors(an["inline_svg"])
    cands += [(u, "icono") for u in an.get("icons", [])] + ([(an["og_image"], "og:image")] if an.get("og_image") else [])
    for url, kind in cands:
        try:
            data = _get(url, binary=True, timeout=60, max_bytes=MAX_LOGO, public_only=kind != "pedido")
            if not looks_like_image(data):
                raise ValueError("no es una imagen")
        except Exception as e:  # noqa: BLE001  (el siguiente candidato)
            info.setdefault("errors", []).append(f"{url[:80]}: {e}")
            continue
        ldir.mkdir(parents=True, exist_ok=True)
        if url.lower().split("?")[0].endswith(".svg") or data.lstrip()[:5] in (b"<svg ", b"<?xml"):
            (ldir / "original.svg").write_bytes(data)
            info.update(url=url, kind=kind, files={k: f"{name}/original.svg" for k in ("isotipo", "on_dark", "on_light", "on_accent")})
            return info, svg_colors(data.decode("utf-8", "replace"))
        raw = ldir / "original.png"
        raw.write_bytes(data)
        if kind == "og:image":
            trimmed = trim_image(raw)
            warnings.append("el logo es la imagen social (og:image)" + (", recortada a su contenido" if trimmed else "") +
                            ": comprueba que sea el logo y no una foto; si no, --logo-url")
        info.update(url=url, kind=kind, files=logo_variants(raw, ldir, "#111111"))
        return info, image_colors(raw)
    warnings.append("no se encontró el logo: pásalo con --logo-url")
    return info, []


def from_site(url: str, name: str, out_dir: str | Path = "brands", logo_url: str | None = None, tagline: str | None = None) -> dict:
    """Descarga la portada y sus hojas CSS, propone la marca y escribe <out_dir>/<name>.json (+ logos en <out_dir>/<name>/)."""
    html = _get(url, public_only=False)   # la web la da el usuario
    css_parts, css_errors = [], []
    for sheet in stylesheets(html, url):
        try:
            css_parts.append(_get(sheet, timeout=20))
        except Exception as e:  # noqa: BLE001
            css_errors.append(f"{sheet[:80]}: {e}")
    an = analyze_html(html, url, "\n".join(css_parts))
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    warnings: list[str] = []
    logo_info, logo_cols = _logo(an, logo_url, out / name, name, warnings)
    prop = propose(an, logo_cols)
    warnings = prop["warnings"] + warnings
    if logo_info.get("files") and logo_info.get("kind") != "svg en línea" and not logo_info["url"].lower().split("?")[0].endswith(".svg"):
        logo_info["files"] = logo_variants(out / name / "original.png", out / name, prop["ink"])   # con la tinta ya elegida
    host = urllib.parse.urlparse(url).netloc.replace("www.", "")
    brand = {"name": name, "site": host, "tagline": tagline or "", "endorsement": host, "source": url, **TEMPLATE,
             "ink": prop["ink"], "border": prop["ink"], "logo_files": logo_info.get("files", {})}
    if prop["accent"]:
        brand["accent"] = prop["accent"]
        from .build import on_accent_color   # aquí: build no importa brandsite, pero así no se carga si no hace falta
        brand["on_accent"] = on_accent_color(brand["accent"], brand["ink"])
    else:
        # Sin acento seguro no se inventa (F28-299): el fichero lo dice, build y cover se niegan hasta que el usuario elija
        brand["accent_pending"] = True
        brand["accent_candidates"] = prop["candidates"]
        warnings.append(f"cuando el usuario elija el acento: frame28 brand set {name} --accent #RRGGBB")
    if prop["font"]:
        fam = prop["font"]
        if fam.islower():   # `--env-font-family:inter`: Google Fonts quiere «Inter»
            fam = " ".join(w.capitalize() for w in fam.split())
        brand["sans"] = f'{fam}, Inter, "Segoe UI", Arial, sans-serif'
        brand["font_link"] = f"https://fonts.googleapis.com/css2?family={urllib.parse.quote(fam)}:wght@400;600;800&display=swap"
    path = out / f"{name}.json"
    path.write_text(json.dumps(brand, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"brand": str(path), "accent": prop["accent"], "accent_status": prop["accent_status"], "accent_suggested": prop["accent_suggested"],
            "candidates": prop["candidates"], "ink": brand["ink"], "on_accent": brand.get("on_accent"), "font": prop["font"],
            "secondary": prop["secondary"], "confidence": prop["confidence"], "accent_sources": prop["accent_sources"], "warnings": warnings,
            "logo": logo_info, "logo_colors": logo_cols, "title": an["title"], "description": an["description"],
            "top_colors": an["colors"][:8], "css_vars": an["css_vars"], "ignored_vars": an["ignored_vars"],
            "ignored_colors": prop["ignored_colors"], "fonts": an["fonts"], "stylesheets": len(css_parts),
            "stylesheet_errors": css_errors}
