"""F28-116: matte (RVM) usa CUDA cuando el extra gpu trae onnxruntime-gpu, con caída a CPU (el OCR solo si se pide: en
CPU fue más rápido), y la instalación con el extra no deja onnxruntime y onnxruntime-gpu a la vez (comparten el módulo y
se pisan los ficheros)."""
from __future__ import annotations

import re
import sys
import types
from pathlib import Path

import pytest

from frame28 import doctor as D
from frame28 import env, graphics, matte

CLI = Path(__file__).resolve().parents[1]
CUDA = ["TensorrtExecutionProvider", "CUDAExecutionProvider", "CPUExecutionProvider"]
CPU = ["CPUExecutionProvider"]


@pytest.fixture(autouse=True)
def _no_dlls(monkeypatch):
    monkeypatch.setattr(env, "enable_cuda_dlls", lambda: [])
    monkeypatch.delenv(env.ONNX_ENV, raising=False)


@pytest.mark.parametrize("gpu, var, available, want", [
    (None, "", CUDA, ["CUDAExecutionProvider", "CPUExecutionProvider"]),   # auto: CUDA delante, CPU de caída
    (None, "", CPU, CPU),                                                    # sin el extra: CPU sin avisar
    (False, "", CUDA, CPU),                                                  # --cpu
    (None, "cpu", CUDA, CPU),                                                # FRAME28_ONNX=cpu
    (True, "cpu", CUDA, ["CUDAExecutionProvider", "CPUExecutionProvider"]),  # --gpu manda sobre la variable
    (None, "auto", CUDA, ["CUDAExecutionProvider", "CPUExecutionProvider"]),
])
def test_onnx_providers(monkeypatch, gpu, var, available, want):
    if var:
        monkeypatch.setenv(env.ONNX_ENV, var)
    assert env.onnx_providers(gpu, available=available) == want


def test_onnx_gpu_without_cuda_is_an_error_not_a_silent_cpu(monkeypatch):
    with pytest.raises(SystemExit, match="doctor"):
        env.onnx_providers(True, available=CPU)
    monkeypatch.setenv(env.ONNX_ENV, "gpu")
    with pytest.raises(SystemExit):
        env.onnx_providers(None, available=CPU)


def test_never_tensorrt_first():
    # onnxruntime-gpu anuncia TensorRT primero; sin sus librerías, ponerlo delante solo llena la salida de errores
    assert "TensorrtExecutionProvider" not in env.onnx_providers(None, available=CUDA)


def test_gpu_extra_brings_cuda12_onnxruntime_and_the_excludes_file_removes_the_cpu_one():
    py = (CLI / "pyproject.toml").read_text(encoding="utf-8")
    gpu = re.search(r"^gpu = \[(.*?)^\]", py, re.S | re.M).group(1)
    assert "nvidia-cublas-cu12" in gpu and "nvidia-cudnn-cu12" in gpu
    # 1.27 pasó a CUDA 13 (otras librerías, más gigas y sin GPU anteriores a Turing): CUDA 12, como faster-whisper
    assert re.search(r'"onnxruntime-gpu\[cuda,cudnn\]>=[\d.]+,<1\.27;', gpu)
    reqs = [l.strip() for l in (CLI / env.GPU_EXCLUDES).read_text(encoding="utf-8").splitlines()
            if l.strip() and not l.lstrip().startswith("#")]
    assert reqs == ["onnxruntime"]
    assert env.GPU_EXCLUDES_URL.endswith("/plugin/cli/" + env.GPU_EXCLUDES)


def test_gpu_install_cmd_always_excludes_cpu_onnxruntime():
    ed = env.gpu_install_cmd("C:/repo/plugin/cli/")
    # con las versiones exactas de las pruebas también en el extra gpu (F28-91)
    assert '--editable "C:/repo/plugin/cli[gpu,probado]"' in ed and '--excludes "C:/repo/plugin/cli/excluir-gpu.txt"' in ed
    git = env.gpu_install_cmd()
    assert f'"frame28[gpu,probado] @ {env.GIT_SPEC}"' in git and env.GIT_SPEC.startswith("git+https://github.com/javierledesma28/frame28")
    assert "--excludes " + env.GPU_EXCLUDES_URL in git
    assert all("--reinstall" in c and "--python 3.12" in c for c in (ed, git))


class _Dist:
    def __init__(self, name, files):
        self.metadata = {"Name": name}
        self.files = files


def test_onnxruntime_dists_finds_every_package_that_ships_the_module(monkeypatch):
    import importlib.metadata as md
    fake = [_Dist("onnxruntime", ["onnxruntime/__init__.py"]), _Dist("onnxruntime_gpu", ["onnxruntime\\__init__.py"]),
            _Dist("onnxruntime-extensions", ["onnxruntime_extensions/__init__.py"]), _Dist("numpy", None)]
    monkeypatch.setattr(md, "distributions", lambda: fake)
    assert env.onnxruntime_dists() == ["onnxruntime", "onnxruntime-gpu"]


def test_doctor_onnx_rows(monkeypatch):
    rows = D.onnx_rows(["onnxruntime", "onnxruntime-gpu"], CUDA, editable_dir="C:/r/plugin/cli")
    dup = next(r for r in rows if r["name"] == "onnxruntime (un solo paquete)")
    assert not dup["ok"] and not dup["optional"] and "--excludes" in dup["fix"]
    ok = D.onnx_rows(["onnxruntime-gpu"], CUDA, editable_dir=None)
    assert [r["name"] for r in ok] == ["gpu (matte y OCR)"] and ok[0]["ok"]
    cpu = D.onnx_rows(["onnxruntime"], CPU, editable_dir=None)
    assert not cpu[0]["ok"] and cpu[0]["optional"] and "--excludes" in cpu[0]["fix"] and "git+" in cpu[0]["fix"]


def test_doctor_gpu_hints_use_the_install_cmd():
    src = (CLI / "frame28" / "doctor.py").read_text(encoding="utf-8")
    assert 'plugin/cli[gpu]" --python 3.12 --reinstall' not in src      # la orden vieja dejaba onnxruntime y -gpu juntos


class _Sess:
    def __init__(self, path, providers):
        self.asked = providers
        self.providers = [p for p in providers if p != "CUDAExecutionProvider"] if "nocuda" in path else providers

    def get_providers(self):
        return self.providers


@pytest.mark.parametrize("model, want", [("rvm.onnx", "CUDAExecutionProvider"), ("nocuda.onnx", "CPUExecutionProvider")])
def test_matte_reports_the_provider_it_really_got(monkeypatch, model, want):
    # si CUDA no llega a cargar, onnxruntime sigue en CPU sin error: el informe tiene que decirlo
    monkeypatch.setitem(sys.modules, "onnxruntime", types.SimpleNamespace(InferenceSession=_Sess, get_available_providers=lambda: CUDA))
    monkeypatch.setattr(matte, "ensure_rvm_model", lambda: model)
    sess, provider = matte._session()
    assert sess.asked == ["CUDAExecutionProvider", "CPUExecutionProvider"] and provider == want
    sess, provider = matte._session(False)
    assert sess.asked == CPU and provider == "CPUExecutionProvider"


def test_ocr_engine_runs_on_cpu_unless_cuda_is_asked_for(monkeypatch):
    # medido (F28-116): el OCR en CUDA fue más lento que en CPU; la GPU solo con --gpu o FRAME28_ONNX=gpu
    seen = []
    monkeypatch.setitem(sys.modules, "rapidocr", types.SimpleNamespace(RapidOCR=lambda params=None: seen.append(params) or "eng"))
    monkeypatch.setattr(env, "onnx_providers", lambda gpu=None, available=None: ["CUDAExecutionProvider", "CPUExecutionProvider"] if gpu is not False else CPU)
    graphics._ocr_engine()
    graphics._ocr_engine(False)
    assert seen == [None, None]
    graphics._ocr_engine(True)
    monkeypatch.setenv(env.ONNX_ENV, "gpu")
    graphics._ocr_engine()
    assert seen[2] == seen[3] and seen[2]["EngineConfig.onnxruntime.use_cuda"] is True
    assert seen[2]["EngineConfig.onnxruntime.cuda_ep_cfg.cudnn_conv_algo_search"] == "HEURISTIC"   # DEFAULT = plan de reserva de cuDNN 9, más lento que la CPU
    assert graphics._ocr_provider(object()) == "desconocido"
