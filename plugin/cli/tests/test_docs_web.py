"""F28-121: las páginas de frame28.t28.io pintan sin esperar a Google Fonts (costaba ~0,9 s de FCP móvil), tienen favicon
(su 404 era un error de consola en las tres) y meta description, y el asistente de instalación pasa la accesibilidad.
Y ningún fichero de texto versionado lleva un NUL: uno colado en CLAUDE.md hacía que grep lo tratara como binario."""
import re
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
DOCS = REPO / "docs"
PAGINAS = ["instalar/index.html", "instalar/en/index.html", "roadmap/index.html", "presentacion/deck.html",
           "presentacion/index.html"]
INSTALAR = PAGINAS[:2]
BINARIOS = {".png", ".ico", ".jpg", ".jpeg", ".gif", ".webp", ".mp4", ".wav", ".webm", ".woff", ".woff2", ".ttf", ".onnx",
            ".zip", ".pdf"}


def read(rel: str) -> str:
    t = (DOCS / rel).read_text(encoding="utf-8")
    if rel == "presentacion/deck.html":                        # el build mete la hoja de marca en index.html
        t += (DOCS / "presentacion" / "think28-brand.css").read_text(encoding="utf-8")
    return t


@pytest.mark.parametrize("rel", PAGINAS)
def test_fuentes_sin_bloquear_el_render(rel):
    t = read(rel)
    fuera = re.sub(r"<noscript>.*?</noscript>", "", t, flags=re.S)
    hojas = re.findall(r"<link[^>]*fonts\.googleapis\.com/css2[^>]*>", fuera)
    assert len(hojas) == 1 and 'media="print"' in hojas[0] and 'id="t28-fuentes"' in hojas[0]
    assert 'getElementById("t28-fuentes")' in t and 'l.media="all"' in t
    # tras el primer pintado con contenido: si las fuentes acaban antes, Lighthouse las cuenta como bloqueantes; los dos
    # requestAnimationFrame no bastan con la máquina cargada (el fotograma se presenta tarde) y quedan para navegadores viejos
    assert 'getEntriesByName("first-contentful-paint")' in t and '{type:"paint",buffered:true}' in t
    assert "requestAnimationFrame(function(){requestAnimationFrame(pinto)})" in t
    assert "setTimeout(pinto,3e3)" in t                                # una pestaña que nunca registra el FCP también las carga
    assert re.search(r"<noscript><link rel=\"stylesheet\" href=\"https://fonts\.googleapis\.com/css2", t)
    assert '"Inter Fallback";src:local("Arial")' in t and "'Inter Fallback'" in t   # declarada y usada en la pila
    # Space Mono avanza 0,612 em y Consolas 0,550: sin reserva del mismo ancho la cabecera de /instalar/ cambiaba de líneas
    assert '"Space Mono Fallback";src:local("Courier New")' in t and "size-adjust:102%" in t
    assert not re.search(r"'Space Mono'(?!,\s*'Space Mono Fallback')", t)


@pytest.mark.parametrize("rel", PAGINAS)
def test_favicon_y_descripcion(rel):
    t = read(rel)
    assert '<link rel="icon" href="/favicon.ico"' in t and '<link rel="icon" href="/brand/think28-isotipo.svg"' in t
    assert re.search(r'<meta name="description" content="[^"]{50,}">', t)


def test_favicon_ico_valido():
    b = (DOCS / "favicon.ico").read_bytes()
    assert b[:4] == b"\x00\x00\x01\x00" and b[4] >= 1                # cabecera ICO con al menos una imagen
    assert (DOCS / "brand" / "think28-isotipo.svg").is_file()
    assert "favicon.ico" in (DOCS / "index.html").read_text(encoding="utf-8")


@pytest.mark.parametrize("rel", INSTALAR)
def test_instalar_accesible(rel):
    t = read(rel)
    assert t.count("<main>") == 1 and t.index("</header>") < t.index("<main>") < t.index("</main>") < t.index("<footer>")
    m = re.search(r"--mute:#([0-9a-fA-F]{3,6});", t)
    assert m and m.group(1).lower() not in ("555", "555555")           # 2,65:1 sobre el fondo; #8a8a8a da 5,7:1


def test_roadmap_y_deck():
    assert '<a class="logo" href="https://t28.io">' in read("roadmap/index.html")   # el nombre lo da el SVG (role=img)
    for rel in ("presentacion/deck.html", "presentacion/index.html"):
        assert 'class="slide cover is-active"' in read(rel)          # la portada se ve antes de que llegue el JS del motor


def test_deck_no_maqueta_lo_que_no_se_ve():
    # las 19 slides maquetadas de golpe costaban 473 ms antes del primer pintado (traza en vivo); ahora solo la visible
    css = (DOCS / "presentacion" / "engine" / "deck.css").read_text(encoding="utf-8")
    js = (DOCS / "presentacion" / "engine" / "deck.js").read_text(encoding="utf-8")
    regla = ".deck-stage > .slide:not(.is-active):not(.is-exit){content-visibility:hidden}"
    assert regla in css and regla in read("presentacion/index.html")              # index.html reconstruido
    assert ".deck-midiendo .deck-stage > .slide{content-visibility:visible !important}" in css
    assert "content-visibility:visible !important;" in css.split("@media print")[1]  # al imprimir salen todas
    cuerpo = js[js.index("function check()"):js.index("return bad;")]                # check() sigue midiendo todas
    assert "classList.add('deck-midiendo')" in cuerpo and "classList.remove('deck-midiendo')" in cuerpo
    # y por eso el chequeo automático solo corre al editar: publicado eran 753 ms de hilo principal tras el FCP por visita
    assert "var editando = location.protocol === 'file:'" in js
    llamadas = [x.strip() for x in js.splitlines() if "setTimeout(check," in x]
    assert llamadas and all(x.startswith(("if (editando", "else if (editando")) for x in llamadas)


def test_el_motor_del_deck_es_neutro():
    # F28-109: el motor no lleva el logo ni el nombre de otra marca; la marca la pone el deck (think28-brand.css)
    pres = DOCS / "presentacion"
    ajenas = ("fund" "anet", "semi" "crol")  # partidas: el repo entero tampoco debe contener la palabra (grep de F28-109)
    for f in [pres / "deck.html", pres / "index.html", *sorted((pres / "engine").iterdir())]:
        t = f.read_text(encoding="utf-8").lower()
        assert not any(m in t for m in ajenas), f.name
    assert "data:image/png" not in (pres / "engine" / "logo.css").read_text(encoding="utf-8")
    assert "--brand-logo:url(" in (pres / "think28-brand.css").read_text(encoding="utf-8")
    assert "window.Deck = {" in (pres / "engine" / "deck.js").read_text(encoding="utf-8")


def test_roadmap_no_maqueta_lo_que_queda_lejos():
    # 1.530 objetos en el primer Layout y otra vez al llegar las fuentes; en móvil ninguna versión se ve al cargar
    t = read("roadmap/index.html")
    assert ".version { content-visibility: auto; contain-intrinsic-size: auto calc(200px + var(--n, 8) * 92px); }" in t
    assert "contain-intrinsic-size: auto calc(220px + var(--n, 8) * 190px)" in t        # filas apiladas bajo 640 px
    assert 'style="--n:${items.length}"' in t                                            # el alto estimado sale de los ítems


def test_ningun_texto_versionado_lleva_nul():
    try:
        out = subprocess.run(["git", "ls-files", "-z"], cwd=REPO, capture_output=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        pytest.skip("sin git o fuera de un checkout")
    rutas = [p for p in out.decode("utf-8").split("\0") if p and Path(p).suffix.lower() not in BINARIOS]
    malos = [p for p in rutas if (REPO / p).is_file() and b"\0" in (REPO / p).read_bytes()]
    assert not malos
