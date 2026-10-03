"""brand from-site (F28-79): la marca propuesta no hereda nada de Think28, el acento sale del logo y del CSS (también de
las hojas enlazadas), el logo del header gana a la og:image (que se recorta) y la confianza se dice. Sin red: la web es
un diccionario de URL → contenido."""
import json

import cv2
import numpy as np
import pytest

from frame28 import brandsite as S

YELLOW, BLUE, PINK = (0, 210, 255), (151, 74, 11), (161, 119, 234)    # BGR de #FFD200, #0B4A97, #EA77A1


def png(w, h, bg, shapes=(), alpha=False) -> bytes:
    im = np.full((h, w, 4 if alpha else 3), (*bg, 0) if alpha else bg, np.uint8)
    for (x0, y0, x1, y1), color in shapes:
        im[y0:y1, x0:x1] = (*color, 255) if alpha else color
    return cv2.imencode(".png", im)[1].tobytes()


@pytest.fixture()
def web(monkeypatch):
    site: dict[str, object] = {}

    def fake_get(url, binary=False, timeout=30, max_bytes=S.MAX_PAGE):
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


def test_sin_colores_ni_logo_confianza_baja(web, tmp_path):
    web["https://c.example/"] = "<html><body><p>texto</p></body></html>"
    r = S.from_site("https://c.example/", "c", tmp_path)
    assert r["confidence"] == "baja" and r["accent"] == "#2F6FEB" and r["accent"] != "#EA77A1"
    assert any("provisional" in x for x in r["warnings"]) and any("--logo-url" in x for x in r["warnings"])


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
    monkeypatch.setattr(S.urllib.request, "urlopen", lambda req, timeout: Big())
    with pytest.raises(ValueError, match="demasiado grande"):
        S._get("https://x.example/", max_bytes=10)
