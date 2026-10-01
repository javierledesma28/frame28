"""Frame28: herramientas deterministas para videos de presentación con hablante a cámara."""

# Única fuente de la versión del CLI: pyproject.toml la lee de aquí (hatch). plugin.json, marketplace.json y el README
# se suben a mano; `python scripts/release-check.py` comprueba que los cuatro coinciden antes de etiquetar.
__version__ = "0.4.0"
# Compositor pineado: subirlo exige pasar la regresión de poc/clip-javier y poc/clip-grabado.
HYPERFRAMES_VERSION = "0.8.105"
# GSAP se carga por CDN en el HTML generado (build y cover): el render necesita red; `frame28 doctor` lo comprueba.
GSAP_VERSION = "3.15.0"
