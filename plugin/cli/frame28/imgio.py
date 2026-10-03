"""Leer y escribir imágenes con OpenCV en cualquier ruta (F28-88).

En Windows, cv2.imread y cv2.imwrite usan la página de códigos ANSI: con una ruta con acentos (…\\Campaña\\, un %TEMP%
bajo C:\\Users\\José\\) devuelven None / False sin escribir nada y sin error. Comprobado en esta máquina el 2026-10-03:
imwrite False y el fichero no existe. Aquí los bytes pasan por Python (que sí entiende la ruta) y OpenCV solo codifica y
decodifica en memoria; si algo falla, se dice. cv2.VideoCapture no tiene el problema (lo abre ffmpeg)."""
from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np


def imread(path: str | Path, flags: int = cv2.IMREAD_COLOR):
    """Como cv2.imread, también con acentos en la ruta. None si el fichero no existe o no es una imagen."""
    try:
        data = np.fromfile(str(path), dtype=np.uint8)
    except OSError:
        return None
    if data.size == 0:
        return None
    return cv2.imdecode(data, flags)


def imwrite(path: str | Path, img) -> Path:
    """Como cv2.imwrite, también con acentos en la ruta; el formato sale de la extensión. Lanza un error si no se pudo
    (antes se perdía en silencio y después ffmpeg o el storyboard fallaban buscando un PNG que no existía)."""
    p = Path(path)
    try:
        ok, buf = cv2.imencode(p.suffix or ".png", img)
    except cv2.error as e:   # extensión sin codificador u otra imagen que OpenCV no sabe guardar
        raise IOError(f"OpenCV no pudo codificar la imagen para {p}: {str(e).strip().splitlines()[-1][:160]}") from e
    if not ok:
        raise IOError(f"OpenCV no pudo codificar la imagen para {p}")
    p.parent.mkdir(parents=True, exist_ok=True)
    buf.tofile(str(p))
    return p
