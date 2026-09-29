# -*- coding: utf-8 -*-
"""
Genera un código QR como SVG con el color de la marca del deck, sin red.
Pensado para la tarjeta .qr-card del cierre; build.mjs lo embebe como data URI.

Uso:
    python engine/qr.py "https://frame28.app" qr.svg
    python engine/qr.py "<url>" <salida.svg> [--dark #0A0A0A] [--scale 8]

Requiere segno (puro Python):  python -m pip install segno
"""
import sys, argparse

try:
    import segno
except ImportError:
    sys.exit("Falta la librería segno: python -m pip install segno")

ap = argparse.ArgumentParser(description="QR SVG con el color de la marca")
ap.add_argument("texto", help="URL o texto a codificar")
ap.add_argument("salida", help="Fichero .svg de salida")
ap.add_argument("--dark", default="#0A0A0A", help="Color de los módulos (por defecto la tinta de Think28)")
ap.add_argument("--scale", type=int, default=8, help="Píxeles por módulo")
ap.add_argument("--error", default="m", choices=list("lmqh"), help="Nivel de corrección de errores")
a = ap.parse_args()

qr = segno.make(a.texto, error=a.error)
qr.save(a.salida, kind="svg", scale=a.scale, border=2, dark=a.dark, light=None, xmldecl=False)
print(f"QR {qr.version}-{qr.error} ({qr.symbol_size()[0]} modulos) -> {a.salida}")
