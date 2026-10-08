"""brand from-site (F28-79): la marca propuesta no hereda nada de Think28, el acento sale del logo y del CSS (también de
las hojas enlazadas), el logo del header gana a la og:image (que se recorta) y la confianza se dice. Sin red: la web es
un diccionario de URL → contenido."""
import json

import cv2
import numpy as np
import pytest
from click.testing import CliRunner

from frame28 import brandsite as S
from frame28 import build
from frame28.cli import main
from conftest import write_json

YELLOW, BLUE, PINK = (0, 210, 255), (151, 74, 11), (161, 119, 234)    # BGR de #FFD200, #0B4A97, #EA77A1


def png(w, h, bg, shapes=(), alpha=False) -> bytes:
    im = np.full((h, w, 4 if alpha else 3), (*bg, 0) if alpha else bg, np.uint8)
    for (x0, y0, x1, y1), color in shapes:
        im[y0:y1, x0:x1] = (*color, 255) if alpha else color
    return cv2.imencode(".png", im)[1].tobytes()


@pytest.fixture()
def web(monkeypatch):
    site: dict[str, object] = {}

    monkeypatch.setattr(S, "host_is_public", lambda url: not any(h in url for h in ("169.254.", "localhost", "127.0.0.1", "10.0.")))

    def fake_get(url, binary=False, timeout=30, max_bytes=S.MAX_PAGE, public_only=True):
        S._check_url(url, public_only)                      # la misma regla que el código real
        if url not in site:
            raise OSError(f"404 {url}")
        data = site[url]
        if isinstance(data, str):
            return data.encode() if binary else data
        return data
    monkeypatch.setattr(S, "_get", fake_get)
    return site


# La marca DTC del hallazgo (amarillo sobre azul) con un botón de promo rosa en el CSS de Shopify
PAGE = """<html><head><title>Marca DTC</title><meta property="og:image" content="/social.png">
<link rel="stylesheet" href="/assets/theme.css"><link rel="stylesheet" href="https://fonts.example/x.css"></head>
<body><header><a class="cart" href="/cart"><img src="/cart.png"></a><a class="site-logo" href="/"><img src="/logo.png" alt="Marca DTC"></a></header>
<main><h1>Hola</h1></main></body></html>"""
THEME = (":root{--color-button: 234,119,161; --color-base-text: 18,18,18}"
         + ".hero{background:#FFD200}" * 8 + ".nav{background:#0b4a97;color:#fff}" * 5
         + "body{font-family: 'Poppins', sans-serif; color:#121212}")


def test_marca_dtc_amarillo_sobre_azul_sin_nada_de_think28(web, tmp_path):
    web.update({"https://marca.example/": PAGE, "https://marca.example/assets/theme.css": THEME,
                "https://marca.example/logo.png": png(400, 120, (255, 255, 255), [((10, 10, 390, 110), YELLOW), ((60, 40, 340, 80), BLUE)]),
                "https://marca.example/cart.png": png(24, 24, (0, 0, 0)), "https://marca.example/social.png": png(1200, 630, (255, 255, 255))})
    r = S.from_site("https://marca.example/", "marca-dtc", tmp_path)
    assert r["accent"] == "#ffd200" and "logo" in r["accent_sources"] and r["confidence"] == "alta"
    assert "#0b4a97" in r["secondary"] and "#ea77a1" not in (r["accent"],)                     # el rosa del botón no gana
    assert r["logo"]["kind"] == "header" and r["logo"]["url"].endswith("/logo.png")             # el logo, no el carrito ni la social
    assert r["font"] == "Poppins" and r["stylesheets"] == 1 and r["stylesheet_errors"]          # la hoja de terceros falló sin romper
    text = (tmp_path / "marca-dtc.json").read_text(encoding="utf-8")
    brand = json.loads(text)
    assert not any(k in brand for k in ("voice", "logo_rules", "logos"))                         # nada heredado de otra marca
    assert "t28" not in text.lower() and "think28" not in text.lower()
    assert brand["site"] == "marca.example" and set(brand["logo_files"]) == {"on_light", "isotipo", "on_accent", "on_dark"}
    assert (tmp_path / "marca-dtc" / "on_dark.png").exists()


def test_og_image_recortada_y_avisada(web, tmp_path):
    web.update({"https://b.example/": '<html><head><meta property="og:image" content="https://b.example/og.png"></head><body></body></html>',
                "https://b.example/og.png": png(1200, 630, (250, 250, 250), [((450, 260, 750, 360), BLUE)])})
    r = S.from_site("https://b.example/", "b", tmp_path)
    assert r["logo"]["kind"] == "og:image"
    h, w = cv2.imread(str(tmp_path / "b" / "original.png")).shape[:2]
    assert w < 400 and h < 200                                                                    # recortada a su contenido
    assert any("og:image" in x for x in r["warnings"]) and r["accent"] == "#0b4a97"


def test_sin_colores_ni_logo_no_se_inventa_el_acento(web, tmp_path):
    web["https://c.example/"] = "<html><body><p>texto</p></body></html>"
    r = S.from_site("https://c.example/", "c", tmp_path)
    assert r["confidence"] == "baja" and r["accent"] is None and r["accent_status"] == "a confirmar" and r["candidates"] == []
    assert any("pídele el acento" in x for x in r["warnings"]) and any("--logo-url" in x for x in r["warnings"])
    assert any("frame28 brand set c --accent" in x for x in r["warnings"])
    brand = json.loads((tmp_path / "c.json").read_text(encoding="utf-8"))
    assert "accent" not in brand and brand["accent_pending"] is True and "on_accent" not in brand


def test_svg_en_linea_del_header(web, tmp_path):
    svg = '<svg class="logo" viewBox="0 0 100 30">' + '<path fill="#E30613" d="M0 0h100v30H0z"/>' * 3 + '<path fill="#1D1D1B" d="M1 1"/></svg>'
    web["https://d.example/"] = f'<html><body><header><a href="/" class="brand">{svg}</a></header><style>.x{{color:#e30613}}</style></body></html>'
    r = S.from_site("https://d.example/", "d", tmp_path)
    assert r["logo"]["kind"] == "svg en línea" and (tmp_path / "d" / "original.svg").read_text(encoding="utf-8").startswith("<svg")
    assert r["accent"] == "#e30613" and r["logo_colors"][0] == "#e30613"


def test_logo_pedido_gana(web, tmp_path):
    web.update({"https://e.example/": PAGE, "https://otro.example/mi-logo.svg": '<svg><path fill="#00A651" d="M0 0"/></svg>'})
    r = S.from_site("https://e.example/", "e", tmp_path, logo_url="https://otro.example/mi-logo.svg")
    assert r["logo"]["kind"] == "pedido" and r["accent"] == "#00a651"


def test_colores_css_y_hojas():
    assert S.css_colors("a{color:#fd0;background:rgb(11, 74, 151)} b{color:#FFFFFF}") == ["#ffdd00", "#0b4a97"]
    sheets = S.stylesheets('<link href="/a.css" rel="stylesheet"><link rel="stylesheet" href="https://cdn.x/b.css">'
                           '<link rel="icon" href="/i.png">', "https://www.marca.example/")
    assert sheets == ["https://www.marca.example/a.css", "https://cdn.x/b.css"]                  # las del sitio primero


def test_descargas_solo_http_y_con_tope(monkeypatch):
    with pytest.raises(ValueError, match="esquema"):
        S._get("file:///etc/passwd")

    class Big:
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def read(self, n): return b"x" * n

    class Opener:
        def open(self, req, timeout): return Big()
    monkeypatch.setattr(S.urllib.request, "build_opener", lambda *h: Opener())
    with pytest.raises(ValueError, match="demasiado grande"):
        S._get("https://x.example/", max_bytes=10, public_only=False)


# ── F28-85: lo que dice la web solo se baja de hosts públicos, también tras redirecciones ────────────────────────────
@pytest.mark.parametrize("addr, public", [("93.184.216.34", True), ("169.254.169.254", False), ("10.1.2.3", False),
                                          ("192.168.1.10", False), ("127.0.0.1", False), ("::1", False), ("fe80::1", False)])
def test_host_is_public(monkeypatch, addr, public):
    monkeypatch.setattr("socket.getaddrinfo", lambda host, port: [(None, None, None, None, (addr, 0))])
    assert S.host_is_public("https://algo.example/x.png") is public


def test_host_that_does_not_resolve_is_not_public(monkeypatch):
    def boom(host, port):
        raise OSError("no resuelve")
    monkeypatch.setattr("socket.getaddrinfo", boom)
    assert not S.host_is_public("https://no-existe.example/")
    assert not S.host_is_public("not a url")


def test_get_refuses_internal_and_redirects_to_internal(monkeypatch):
    monkeypatch.setattr(S, "host_is_public", lambda url: "169.254." not in url)
    with pytest.raises(ValueError, match="interna"):
        S._get("http://169.254.169.254/latest/meta-data/")
    guard = S._GuardedRedirect(public_only=True)
    with pytest.raises(ValueError, match="interna"):
        guard.redirect_request(None, None, 302, "Found", {}, "http://169.254.169.254/x")
    with pytest.raises(ValueError, match="esquema"):
        guard.redirect_request(None, None, 302, "Found", {}, "file:///etc/passwd")


def test_page_pointing_to_internal_or_non_image_logos_is_skipped(web, tmp_path):
    page = ('<html><head><meta property="og:image" content="http://169.254.169.254/latest/meta-data/iam">'
            '<link rel="icon" href="https://k.example/icon.png"></head><body>'
            '<header><img class="logo" src="http://localhost:8080/admin/logo.png"></header></body></html>')
    web.update({"https://k.example/": page, "https://k.example/icon.png": "<html>no soy una imagen</html>"})
    r = S.from_site("https://k.example/", "k", tmp_path)
    errs = " ".join(r["logo"].get("errors", []))
    assert "interna" in errs and "no es una imagen" in errs
    assert not (tmp_path / "k" / "original.png").exists() and not (tmp_path / "k" / "original.svg").exists()
    assert any("--logo-url" in w for w in r["warnings"])


def test_user_given_urls_are_trusted(web, tmp_path):
    # la web y --logo-url las pone el usuario (puede ser su servidor local de pruebas)
    web.update({"http://localhost:3000/": "<html><body></body></html>",
                "http://localhost:3000/logo.svg": '<svg><path fill="#00A651" d="M0 0"/></svg>'})
    r = S.from_site("http://localhost:3000/", "local", tmp_path, logo_url="http://localhost:3000/logo.svg")
    assert r["logo"]["kind"] == "pedido" and r["accent"] == "#00a651"


def test_looks_like_image():
    assert S.looks_like_image(b"\x89PNG\r\n\x1a\n....") and S.looks_like_image(b"\xff\xd8\xff\xe0")
    assert S.looks_like_image(b"  <svg xmlns='x'></svg>") and S.looks_like_image(b"<?xml version='1.0'?><svg/>")
    assert S.looks_like_image(b"RIFF\x00\x00\x00\x00WEBPVP8 ")
    assert not S.looks_like_image(b"<html><body>404</body></html>") and not S.looks_like_image(b'{"error": 1}')


# ── F28-299: widgets de terceros, colores de librerías, var(--…) en la fuente y «acento a confirmar» ─────────────────
# Lo visto en 20 webs DTC reales: en 5 el acento salía solo de Okendo (--oke-*) o Judge.me (--jdgm-*), en una del admin de
# WordPress, en otra de Swiper; en 6 la fuente quedaba como «var»; y nunca se decía «no lo sé».
WIDGETS = (":root{--oke-button-backgroundcolor:#fc199d;--oke-button-bordercolor:#fc199d;--oke-highlightcolor:#ff32ac;"
           "--jdgm-primary-color:#026725;--wp-admin-theme-color:#007cba;--swiper-theme-color:#007aff}"
           + ".oke-button{background:#fc199d}" * 6 + ".jdgm-star{color:#026725}" * 3)


def _site(web, host, css, logo_bgr):
    """Una web con header (carrito + logo), una hoja CSS propia y un logo PNG de un color."""
    web.update({f"https://{host}/": PAGE.replace("/assets/theme.css", "/own.css"), f"https://{host}/own.css": css,
                f"https://{host}/logo.png": png(400, 120, (255, 255, 255), [((10, 10, 390, 110), logo_bgr)]),
                f"https://{host}/cart.png": png(24, 24, (0, 0, 0)), f"https://{host}/social.png": png(1200, 630, (255, 255, 255))})


def test_widgets_de_terceros_no_dan_el_acento(web, tmp_path):
    _site(web, "w.example", WIDGETS + "body{font-family:'Lato',sans-serif}", BLUE)
    r = S.from_site("https://w.example/", "w", tmp_path)
    assert r["accent"] == "#0b4a97" and r["accent_status"] == "ok" and r["confidence"] == "alta" and r["accent_sources"] == ["logo"]
    assert not any(s.startswith(("--oke", "--jdgm", "--wp-admin", "--swiper")) for c in r["candidates"] for s in c["sources"])
    assert {"oke-button-backgroundcolor", "jdgm-primary-color", "wp-admin-theme-color", "swiper-theme-color"} <= set(r["ignored_vars"])
    assert "#fc199d" not in [c["color"] for c in r["candidates"]]                       # ni por frecuencia: es el color del widget
    assert {"#007aff", "#007cba"} <= set(r["ignored_colors"])
    assert any("widgets de terceros" in w and "--oke-*" in w and "--jdgm-*" in w for w in r["warnings"])
    assert json.loads((tmp_path / "w.json").read_text(encoding="utf-8"))["accent"] == "#0b4a97"


def test_logo_y_tema_discrepan_queda_a_confirmar_y_brand_set_lo_guarda(web, tmp_path):
    # logo rojo, pero el tema (variable propia + botones) usa magenta: no se decide por el usuario
    css = ":root{--color-base-accent-1:#db008b}" + ".btn{background:#db008b}" * 10 + "body{font-family:Figtree,sans-serif}"
    _site(web, "x.example", css, (1, 0, 232))                                          # BGR de #E80001
    r = S.from_site("https://x.example/", "x", tmp_path)
    assert r["accent"] is None and r["accent_status"] == "a confirmar" and r["confidence"] == "media"
    assert {"#db008b", "#e80001"} <= {c["color"] for c in r["candidates"]} and r["accent_suggested"] == "#db008b"
    assert any("a confirmar" in w and "#e80001 (logo)" in w for w in r["warnings"])
    assert any("frame28 brand set x --accent" in w for w in r["warnings"])
    brand = json.loads((tmp_path / "x.json").read_text(encoding="utf-8"))
    assert "accent" not in brand and brand["accent_pending"] is True and brand["accent_candidates"][0]["color"] == "#db008b"
    # build y cover se niegan diciendo qué hacer: nada de rellenar con el rosa por defecto
    with pytest.raises(SystemExit, match="por confirmar.*brand set"):
        build.load_brand_file(tmp_path / "x.json")
    # el usuario elige: brand set guarda el acento, calcula el texto sobre acento y quita lo pendiente
    res = CliRunner().invoke(main, ["brand", "set", str(tmp_path / "x.json"), "--accent", "#E80001", "--json"], catch_exceptions=False)
    assert res.exit_code == 0 and json.loads(res.output)["accent"] == "#E80001" and json.loads(res.output)["accent_pending"] is False
    brand = build.load_brand_file(tmp_path / "x.json")
    assert brand["accent"] == "#E80001" and brand["on_accent"] and "accent_pending" not in brand and "accent_candidates" not in brand
    res = CliRunner().invoke(main, ["brand", "set", str(tmp_path / "x.json"), "--accent", "rojo"])
    assert res.exit_code != 0
    # la salida legible de from-site lo dice sin reventar (no hay acento que imprimir)
    res = CliRunner().invoke(main, ["brand", "from-site", "https://x.example/", "--name", "x2", "--out", str(tmp_path)],
                             catch_exceptions=False)
    assert res.exit_code == 0 and "ACENTO A CONFIRMAR" in res.output and "candidatos: #db008b" in res.output
    assert "frame28 brand set x2 --accent" in res.output


def test_colores_por_defecto_de_librerias_no_cuentan(web, tmp_path):
    css = ".btn-primary{background:#0d6efd}" * 30 + ".x{color:#2a7f62}" * 4 + ":root{--swiper-theme-color:#007aff}"
    web["https://l.example/"] = f"<html><head><style>{css}</style></head><body><p>sin logo</p></body></html>"
    r = S.from_site("https://l.example/", "l", tmp_path)
    assert r["accent"] is None and r["accent_status"] == "a confirmar" and r["accent_suggested"] == "#2a7f62"
    assert "#0d6efd" not in [c["color"] for c in r["candidates"]] and {"#0d6efd", "#007aff"} <= set(r["ignored_colors"])


def test_fuente_con_var_resuelta():
    css = (':root{--font-body-family:"Figtree", sans-serif;--font-heading:var(--font-body-family);'
           '--env-font-family:inherit;--env-font-family:inter}'
           + "body{font-family:var(--font-heading)}" * 3 + 'h1{font-family:var(--no-existe, "Lora", serif)}'
           + "p{font-family:var(--env-font-family)}" * 2 + '.sys{font-family:"system_ui",-apple-system,Roboto,sans-serif}'
           + '.i{font-family:"Font Awesome 5 Free"}.v{font-family:var(--sin-definir)}')
    an = S.analyze_html(f"<html><head><style>{css}</style></head><body></body></html>", "https://f.example/")
    assert an["fonts"][0] == ("Figtree", 3) and ("Lora", 1) in an["fonts"] and ("inter", 2) in an["fonts"]
    assert all(f.lower() not in ("var", "roboto") and "awesome" not in f.lower() for f, _ in an["fonts"])
    assert S.first_family("var(--sin-definir)") is None and S.first_family("'Open Sans Condensed', sans-serif") == "Open Sans Condensed"
    assert S.first_family("Roboto, sans-serif") == "Roboto" and S.first_family("-apple-system, Roboto") is None


def test_una_sombra_del_logo_en_el_css_no_contradice_pero_otro_tono_si(web, tmp_path):
    _site(web, "r.example", ".a{color:#ff4343}" * 3, (0, 0, 255))                   # logo rojo; el CSS repite un rojo claro
    r = S.from_site("https://r.example/", "r", tmp_path)
    assert r["accent"] == "#ff0000" and r["confidence"] == "alta"                    # rojo del logo (aunque sea el de YouTube en el CSS)
    _site(web, "b.example", ".a{color:#0000ff}" * 3, (0, 0, 255))                   # mismo logo, pero el CSS tira a azul
    r = S.from_site("https://b.example/", "b", tmp_path)
    assert r["accent"] is None and r["accent_status"] == "a confirmar" and r["accent_suggested"] == "#ff0000"


def test_marca_guardada_sin_acento_no_se_rellena_con_el_rosa(tmp_path):
    p = write_json(tmp_path / "sin.json", {"name": "sin", "ink": "#111111"})
    with pytest.raises(SystemExit, match="marca.accent: falta"):
        build.load_brand_file(p)
    assert build.load_brand_file(write_json(tmp_path / "ok.json", {"name": "ok", "accent": "#123456"}))["accent"] == "#123456"
