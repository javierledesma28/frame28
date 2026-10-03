"""F28-88: OpenCV en Windows no lee ni escribe imágenes en rutas con acentos (devolvía None/False en silencio)."""
import cv2
import numpy as np
import pytest

from frame28 import brandsite
from frame28.imgio import imread, imwrite


def test_imgio_reads_and_writes_with_accents(tmp_path):
    d = tmp_path / "Campaña José" / "ñandú"
    img = np.zeros((10, 20, 3), np.uint8); img[:, :10] = (0, 0, 255)
    p = imwrite(d / "logo.png", img)                                   # crea la carpeta y escribe
    assert p.exists()
    back = imread(p)
    assert back is not None and back.shape == (10, 20, 3) and tuple(back[0, 0]) == (0, 0, 255)
    rgba = imread(p, cv2.IMREAD_UNCHANGED)
    assert rgba is not None and rgba.shape[:2] == (10, 20)
    assert imwrite(d / "foto.jpg", img).stat().st_size > 0             # el formato sale de la extensión
    assert imread(d / "no-existe.png") is None
    (d / "vacío.png").write_bytes(b"")
    assert imread(d / "vacío.png") is None


def test_imwrite_fails_loudly(tmp_path):
    with pytest.raises(IOError):
        imwrite(tmp_path / "x.formato-raro", np.zeros((2, 2, 3), np.uint8))


def test_brand_logo_variants_in_an_accented_folder(tmp_path):
    # antes: la marca quedaba sin variantes de logo y sin aviso si el trabajo vivía en …\Campaña\
    d = tmp_path / "Campaña"
    logo = np.full((40, 80, 4), 0, np.uint8); logo[10:30, 10:70] = (20, 20, 20, 255)
    imwrite(d / "original.png", logo)
    files = brandsite.logo_variants(d / "original.png", d / "marca", "#111111")
    assert set(files) == {"on_light", "isotipo", "on_accent", "on_dark"}
    assert all((d / "marca" / f"{k}.png").exists() for k in files)
    assert brandsite.image_colors(d / "original.png") == []          # gris oscuro: sin color de marca, pero leído


def test_gestures_annotation_reports_only_what_it_wrote(tmp_path):
    from frame28.pose import _annotate
    assert _annotate(tmp_path / "no.mp4", {"fps": 30}, [], [], tmp_path / "a.png") is False   # nada que anotar
    assert not (tmp_path / "a.png").exists()
