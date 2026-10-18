"""F28-91: el motor se instala con techos de versión mayor y con las versiones exactas con las que pasaron las pruebas
(extra `probado`): el pyproject, el script que lo mantiene, la CI, release-check, los instaladores, `frame28 doctor` y
la cota inferior de yt-dlp."""
from __future__ import annotations

import importlib.metadata as md
import importlib.util
import os
import re
import sys
from pathlib import Path

import pytest
from packaging.requirements import Requirement

from frame28 import doctor as D
from frame28 import env, media

CLI = Path(__file__).resolve().parents[1]
REPO = CLI.parents[1]
PYPROJECT = (CLI / "pyproject.toml").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def fd():
    spec = importlib.util.spec_from_file_location("fijar_dependencias", REPO / "scripts" / "fijar-dependencias.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _extra(name: str) -> list[Requirement]:
    body = re.search(rf"^{name} = \[\n(.*?)^\]", PYPROJECT, re.S | re.M).group(1)
    return [Requirement(x) for x in re.findall(r'^\s*"([^"]+)",?\s*$', body, re.M)]


def test_cada_dependencia_directa_tiene_techo(fd):
    deps = [Requirement(d) for d in fd.dependencias(PYPROJECT)]
    assert len(deps) >= 9
    for r in deps:
        assert any(s.operator == "<" for s in r.specifier), f"{r.name} sin techo de versión mayor"
    # PyAV 19 rompe faster-whisper (metadata_errors): ese techo no se relaja con la regla general
    assert "<18" in str(next(r for r in deps if r.name == "av").specifier)


def test_el_extra_gpu_tambien_tiene_techos():
    for r in _extra("gpu"):
        assert any(s.operator == "<" for s in r.specifier), f"gpu: {r.name} sin techo"


def test_probado_fija_cada_dependencia_directa_con_una_version_que_cabe_en_su_rango(fd):
    pins = _extra("probado")
    assert pins and all(len(r.specifier) == 1 and next(iter(r.specifier)).operator == "==" for r in pins)
    por_nombre: dict[str, list[str]] = {}
    for r in pins:
        por_nombre.setdefault(fd.canon(r.name), []).append(next(iter(r.specifier)).version)
    for d in map(Requirement, fd.dependencias(PYPROJECT)):
        versiones = por_nombre.get(fd.canon(d.name))
        assert versiones, f"{d.name} sin versión probada"
        for v in versiones:  # puede haber una por plataforma o versión de Python (marcas)
            assert d.specifier.contains(v, prereleases=True), f"{d.name}=={v} fuera de {d.specifier}"
    # una sola línea por paquete y marca: dos pins sin marca del mismo paquete no se pueden instalar a la vez
    sin_marca = [fd.canon(r.name) for r in pins if r.marker is None]
    assert len(sin_marca) == len(set(sin_marca))


def test_probado_esta_ordenado_y_bien_formado(fd):
    lineas = fd.fijadas(PYPROJECT)
    assert all(fd.nombre_version(p) for p in lineas)
    assert fd.fijadas(fd.con_fijadas(PYPROJECT, list(reversed(lineas)))) == lineas  # el script lo rehace igual


def test_problemas_detecta_lo_que_falta_sobra_o_choca(fd):
    deps = ["click>=8.1,<9", "segno>=1.6,<2"]
    pins = ["click==8.5.0", "colorama==0.4.6 ; sys_platform == 'win32'", "segno==1.6.6"]
    assert fd.problemas(deps, pins, pins) == []
    # la resolución pide un paquete que el extra no fija y ya no pide uno que sí fija
    malos = fd.problemas(deps, pins, ["click==8.5.0", "segno==1.6.6", "nuevo==1.0"])
    assert "sin fijar: nuevo==1.0" in malos and any("colorama==0.4.6" in m for m in malos)
    assert fd.problemas(deps + ["numpy>=1.26,<3"], pins, pins) == ["dependencia directa sin fijar: numpy"]
    assert fd.problemas(deps, pins + ["roto"], pins) == ["línea sin `nombre==versión`: roto"]


def test_ci_y_release_check_prueban_con_las_versiones_exactas():
    ci = (REPO / ".github" / "workflows" / "tests.yml").read_text(encoding="utf-8")
    assert "uv run --extra probado --group dev pytest" in ci and "fijar-dependencias.py" in ci
    rc = (REPO / "scripts" / "release-check.py").read_text(encoding="utf-8")
    assert '"--extra", "probado"' in rc and "fijar-dependencias.py" in rc
    assert "refs/heads/{RELEASE_BRANCH}" in rc  # cada release adelanta la rama de la que instalan los clientes


def test_las_versiones_instaladas_son_las_probadas():
    """La suite corre con las versiones que reciben los clientes (`uv run --extra probado`): en la CI es obligatorio;
    en local se salta si se lanzó sin el extra."""
    pins = D.pinned_versions(md.requires("frame28"), env.PINNED_EXTRA)
    assert len(pins) > 20 and "click" in pins and "numpy" in pins
    installed = {D._canon(d.metadata["Name"] or ""): d.version for d in md.distributions()}
    row = D.pinned_row(pins, installed, None)
    if not row["ok"] and not os.environ.get("CI"):
        pytest.skip("suite lanzada sin --extra probado: " + row["detail"])
    assert row["ok"], row["detail"]


# ---------- de dónde y con qué se instala ----------

def test_install_spec_lleva_las_versiones_probadas():
    assert env.install_spec() == f"frame28[probado] @ {env.GIT_SPEC}"
    assert env.install_spec(gpu=True) == f"frame28[gpu,probado] @ {env.GIT_SPEC}"
    assert env.GIT_SPEC.startswith(f"git+{env.GIT_REPO}") and env.GIT_SPEC.endswith("#subdirectory=plugin/cli")
    ref = env.RELEASE_REF or "main"
    assert (f"@{env.RELEASE_REF}#" in env.GIT_SPEC) == bool(env.RELEASE_REF)
    assert f"/frame28/{ref}/plugin/cli/" in env.GPU_EXCLUDES_URL  # el fichero de exclusiones de la misma rama
    assert env.installer_cmd().endswith(("install.ps1 | iex", "install.sh | bash"))


def _instalador(nombre: str) -> str:
    return (REPO / "docs" / nombre).read_text(encoding="utf-8")


def test_install_sh_instala_el_motor_con_las_versiones_probadas():
    t = _instalador("install.sh")
    motor = re.search(r'^MOTOR_GIT="git\+\$REPO(.*?)"', t, re.M).group(1)
    assert "git+" + env.GIT_REPO + motor == env.GIT_SPEC          # el mismo origen que dice doctor
    assert f'GPU_EXCLUDES="{env.GPU_EXCLUDES_URL}"' in t
    assert 'EXTRAS="probado"' in t and 'EXTRAS="gpu,probado"' in t and "'frame28[$EXTRAS] @ $MOTOR_GIT'" in t
    assert "git+$REPO#subdirectory" not in t.replace('MOTOR_GIT="git+$REPO#subdirectory', "")  # nada instala main a pelo
    # instalación del instalador nuevo → upgrade; anterior → reinstalar con las versiones; editable → no se toca
    assert 'grep -q \'"probado"\'' in t and "uv tool upgrade frame28 || $INSTALL" in t and "grep -q 'editable'" in t
    # con curl | bash, una descarga cortada no ejecuta medio instalador
    assert re.search(r"^main\(\) \{\nset -u\n", t, re.M) and t.rstrip().endswith('main "$@"')


def test_install_ps1_instala_el_motor_con_las_versiones_probadas():
    t = _instalador("install.ps1")
    motor = re.search(r'^\$MotorGit = "git\+\$Repo(.*?)"', t, re.M).group(1)
    assert "git+" + env.GIT_REPO + motor == env.GIT_SPEC
    assert f'$GpuExcludes = "{env.GPU_EXCLUDES_URL}"' in t
    assert '$extras = "probado"' in t and '$extras = "gpu,probado"' in t and '"frame28[" + $extras + "] @ " + $MotorGit' in t
    assert "$rec -match '\"probado\"'" in t and "$rec -match 'editable'" in t
    assert 'install --python 3.12 --force "git+$Repo' not in t


# ---------- doctor ----------

REQUIRES = [
    "click<9,>=8.1",
    "nvidia-cublas-cu12<13,>=12; (sys_platform != 'darwin') and extra == 'gpu'",
    "click==8.5.0; extra == 'probado'",
    "colorama==0.4.6; sys_platform == 'win32' and extra == 'probado'",
    "colorama==0.0.1; sys_platform == 'nunca' and extra == 'probado'",
    "onnxruntime==1.30.0; extra == 'probado'",
    "pytest>=8; extra == 'dev'",
]


def test_pinned_versions_solo_las_del_extra_que_aplican_aqui():
    pins = D.pinned_versions(REQUIRES, "probado")
    assert pins["click"] == "8.5.0" and pins["onnxruntime"] == "1.30.0"
    assert "nvidia-cublas-cu12" not in pins and "pytest" not in pins
    assert ("colorama" in pins) == (sys.platform == "win32") and pins.get("colorama") != "0.0.1"
    assert D.pinned_versions(None, "probado") == {} and D.pinned_versions(["click>=8"], "probado") == {}


def test_pinned_row():
    pins = {"click": "8.5.0", "onnxruntime": "1.30.0"}
    assert D.pinned_row(pins, {"click": "8.5.0", "onnxruntime": "1.30.0"}, None)["ok"]
    # con el extra gpu, onnxruntime-gpu sustituye a onnxruntime
    assert D.pinned_row(pins, {"click": "8.5.0", "onnxruntime-gpu": "1.26.1"}, None)["ok"]
    mal = D.pinned_row(pins, {"click": "8.6.1"}, None)
    assert not mal["ok"] and mal["optional"] and "click 8.6.1 (probada 8.5.0)" in mal["detail"]
    assert "sin instalar: onnxruntime" in mal["detail"] and mal["fix"].startswith("repite el instalador: ")
    ed = D.pinned_row(pins, {}, "C:/repo/plugin/cli/")
    assert ed["fix"] == 'uv tool install --editable "C:/repo/plugin/cli[probado]" --python 3.12 --reinstall'
    # una editable con el extra gpu no lo pierde al ponerse las versiones probadas
    edg = D.pinned_row(pins, {"onnxruntime-gpu": "1.26.1"}, "C:/repo/plugin/cli/")
    assert edg["fix"] == env.gpu_install_cmd("C:/repo/plugin/cli/") and "[gpu,probado]" in edg["fix"]
    vieja = D.pinned_row({}, {"click": "8.6.1"}, None)
    assert not vieja["ok"] and "anterior a F28-91" in vieja["detail"]


def test_la_release_nueva_se_instala_con_el_instalador():
    rows = D.version_rows("0.4.0", "0.5.0", (True, "0.5.0"))
    cli = next(r for r in rows if r["name"] == "última release (CLI)")
    assert not cli["ok"] and env.installer_cmd() in cli["fix"]


# ---------- yt-dlp ----------

def test_ytdlp_del_path_solo_si_no_es_anterior_a_la_cota():
    nuevo = media.ytdlp_cmd("/usr/bin/yt-dlp", "2026.10.07", "uv")
    assert nuevo == ["/usr/bin/yt-dlp"]
    assert media.ytdlp_cmd("/usr/bin/yt-dlp", media.YTDLP_MIN, "uv") == ["/usr/bin/yt-dlp"]
    for path, ver in (("/usr/bin/yt-dlp", "2024.12.23"), ("/usr/bin/yt-dlp", "2026.8.1"), (None, None), ("/x/yt-dlp", "")):
        cmd = media.ytdlp_cmd(path, ver, "uv")
        assert cmd[:2] == ["uv", "tool"] and f"yt-dlp>={media.YTDLP_MIN}" in cmd and cmd[-1] == "yt-dlp", (path, ver)
