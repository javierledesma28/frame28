"""Smoke del CLI (click.testing): las órdenes puras responden, --json es JSON y los errores de formato son cortos."""
from __future__ import annotations

import json

import pytest

from click.testing import CliRunner

from frame28 import __version__
from frame28.captions import TranscriptFormatError
from frame28.cli import main
from conftest import POC, words_from, write_json


def run(*args):
    return CliRunner().invoke(main, [str(a) for a in args], catch_exceptions=False)


def test_version():
    r = run("--version")
    assert r.exit_code == 0 and __version__ in r.output


def test_storyboard_validate_and_schema():
    r = run("storyboard", "validate", POC / "clip-javier" / "storyboard-gsap.json")
    assert r.exit_code == 0 and "Storyboard válido" in r.output
    r = run("storyboard", "schema")
    assert r.exit_code == 0 and "pointer" in r.output


def test_storyboard_validate_fails_with_list(tmp_path):
    p = write_json(tmp_path / "sb.json", {"version": 1, "source": {"video": "v", "duration": 1}, "overlays": [{"type": "box", "id": "b", "start": 0, "end": 2}]})
    r = CliRunner().invoke(main, ["storyboard", "validate", str(p)])
    assert r.exit_code == 1 and "supera la duración" in r.output


def test_captions_pages_and_export(tmp_path, javier_words):
    r = run("captions", "pages", javier_words, "--json")
    pages = json.loads(r.output)
    assert r.exit_code == 0 and pages and all(len(p["words"]) <= 4 for p in pages)
    r = run("captions", "export", javier_words, "-o", tmp_path / "s.srt", "--json")
    assert r.exit_code == 0 and json.loads(r.output)["cues"] >= 1 and (tmp_path / "s.srt").exists()


def test_cut_plan_writes_json_and_short_error_on_bad_input(tmp_path, javier_words):
    r = run("cut", "plan", javier_words, "-o", tmp_path / "cuts.json")
    assert r.exit_code == 0
    cuts = json.loads((tmp_path / "cuts.json").read_text(encoding="utf-8"))
    assert cuts["keep"] and cuts["result_duration"] <= cuts["source_duration"]
    bad = write_json(tmp_path / "bad.json", [{"text": "x"}])
    r = CliRunner().invoke(main, ["cut", "plan", str(bad), "-o", str(tmp_path / "c.json")])
    assert r.exit_code != 0
    # el punto de entrada `cli:run` lo convierte en "Error: …" y exit 2, sin traza
    assert isinstance(r.exception, TranscriptFormatError) and "start/end" in str(r.exception)


def test_clips_plan_and_scaffold(tmp_path):
    cp = write_json(tmp_path / "captions.json", [{"start": 0, "end": 8, "text": "Isn't glass too slippery? Not at all."},
                                                    {"start": 8, "end": 16, "text": "Set the speed to 3 and go slowly."},
                                                    {"start": 16, "end": 24, "text": "And that's it, look at that, beautiful."}])
    r = run("clips", "plan", cp, "--lang", "en", "-o", tmp_path / "clips.json", "--json")
    assert r.exit_code == 0
    plan = json.loads((tmp_path / "clips.json").read_text(encoding="utf-8"))
    assert plan["clips"] and plan["clips"][0]["id"] == "s1"
    d = tmp_path / "clips" / "s1"; d.mkdir(parents=True)
    write_json(d / "words.json", words_from("look at that", start=16.0))
    r = run("clips", "scaffold", tmp_path / "clips.json", "s1", "--dir", d, "--brand", "think28", "--json")
    assert r.exit_code == 0, r.output
    assert (d / "storyboard.json").exists()


def test_reframe_map_points_and_gestures(tmp_path):
    res = write_json(tmp_path / "reframe.json", {"mode": "crop", "source": [1920, 1080], "out": [1080, 1920], "crop": [608, 1080], "path": [[0.0, 960.0]]})
    r = run("reframe-map", res, "--point", "960,540,0.5", "--point", "100,540,0.5", "--json")
    assert r.exit_code == 0
    pts = json.loads(r.output)["points"]
    assert pts[0]["out"] == [540, 960] and pts[0]["visible"] and not pts[1]["visible"]
    g = write_json(tmp_path / "gestures.json", {"canvas": [1920, 1080], "events": [], "pointer_suggestions": [
        {"id": "p1", "type": "pointer", "start": 0.4, "end": 1.6, "at": 0.5, "dot": [960, 540], "box": [1050, 330], "text": "aquí", "confidence": "high"}]})
    r = run("reframe-map", res, "--gestures", g, "-o", tmp_path / "vertical.json")
    assert r.exit_code == 0 and "p1" in r.output and "fuera del encuadre" not in r.output
    assert json.loads((tmp_path / "vertical.json").read_text(encoding="utf-8"))["pointer_suggestions"][0]["visible"]
    r = CliRunner().invoke(main, ["reframe-map", str(res)])
    assert r.exit_code == 2 and "--gestures" in r.output


def test_i18n_extract_and_apply(tmp_path, grabado_short):
    sbp = write_json(tmp_path / "storyboard.json", {**grabado_short, "brand": "think28"})
    r = run("i18n", "extract", sbp, "-o", tmp_path / "strings.json")
    assert r.exit_code == 0, r.output
    data = json.loads((tmp_path / "strings.json").read_text(encoding="utf-8"))
    assert "hook.lines.0" in data["strings"]
    data["strings"]["hook.lines.0"]["text"] = "De cero a esto"
    write_json(tmp_path / "strings.es.json", data)
    r = run("i18n", "apply", sbp, tmp_path / "strings.es.json", "--lang", "es", "--json")
    assert r.exit_code == 0, r.output
    out = json.loads((tmp_path / "storyboard.es.json").read_text(encoding="utf-8"))
    assert out["meta"]["lang"] == "es" and out["overlays"][0]["lines"][0] == "De cero a esto"


def test_brand_list_and_broll_providers():
    r = run("brand", "list")
    assert r.exit_code == 0 and "think28" in r.output
    r = run("broll", "providers")
    assert r.exit_code == 0 and "pexels" in r.output.lower()


def test_clips_markers_writes_json(tmp_path):
    cp = write_json(tmp_path / "captions.json", [{"start": 0, "end": 8, "text": "Anyone can do this."},
                                                    {"start": 8, "end": 16, "text": "Set the speed to 3 and go slowly."},
                                                    {"start": 16, "end": 24, "text": "And that's it, look at that, beautiful."}])
    r = run("clips", "markers", cp, "--lang", "en", "--canvas", "1080x1920", "-o", tmp_path / "markers.json")
    assert r.exit_code == 0, r.output
    assert "before_after" in r.output and "res1" in r.output and "prom1" in r.output
    data = json.loads((tmp_path / "markers.json").read_text(encoding="utf-8"))
    assert data["canvas"] == [1080, 1920] and data["results"] == 1


def test_render_sheet_covers_the_whole_video():
    # día 6: la hoja de un vídeo de 160 s enseñaba solo los primeros 20 s (un fotograma por segundo, 4×5)
    from frame28.media import sheet_plan
    assert sheet_plan(10.0) == (1.0, 4, 5)
    for dur in (28.0, 60.0, 160.0, 600.0):
        every, cols, rows = sheet_plan(dur)
        assert 20 <= cols * rows <= 48 and abs(every * cols * rows - dur) < 0.05   # la rejilla llega al final
    assert sheet_plan(160.0)[1:] == (6, 8) and sheet_plan(28.0)[1:] == (6, 4)


def test_render_args_workers_raise_node_heap_and_gpu_flag(tmp_path):
    # día 6: el render solo usaba 6 de 16 núcleos; con más trabajadores hay que subir el heap de Node
    from frame28.render import NODE_HEAP_MB, render_args
    args, env = render_args(tmp_path / "x.mp4")
    assert args[:2] == ["render", "-o"] and "-w" not in args and "--gpu" not in args and env == {}
    args, env = render_args(tmp_path / "x.mp4", workers=10, gpu=True, node_options="--no-warnings")
    assert args[args.index("-w") + 1] == "10" and args[-1] == "--gpu"
    assert env["NODE_OPTIONS"] == f"--no-warnings --max-old-space-size={NODE_HEAP_MB}"
    assert render_args(tmp_path / "x.mp4", workers=4)[1] == {}                                   # pocos trabajadores: heap por defecto
    assert render_args(tmp_path / "x.mp4", workers=10, node_options="--max-old-space-size=6000")[1] == {}   # el del usuario manda


def test_transcribe_device_auto_picks_gpu_only_when_ready():
    # la máquina tenía GPU y todo iba por CPU: `auto` la usa si hay dispositivo y librerías, y si no, CPU como siempre
    from frame28.transcribe import pick_device
    assert pick_device('auto', 'auto', ready=(True, '1 GPU CUDA con cuBLAS y cuDNN'))[:2] == ('cuda', 'float16')
    dev, comp, why = pick_device('auto', 'auto', ready=(False, 'GPU detectada, falta cudnn64_9.dll'))
    assert (dev, comp) == ('cpu', 'int8') and 'cudnn' in why
    assert pick_device('cpu', 'auto')[:2] == ('cpu', 'int8')
    assert pick_device('auto', 'int8_float16', ready=(True, 'ok'))[:2] == ('cuda', 'int8_float16')   # el cómputo explícito manda
    assert pick_device('cpu', 'int8')[2] == 'elegido a mano'


def test_encoder_uses_the_gpu_by_default_when_it_can(monkeypatch):
    # F28-114, premisa de Javier: si la GPU puede, la GPU (5x más rápido); sin NVIDIA todo sigue en CPU sin pedir nada
    from frame28 import env
    monkeypatch.delenv(env.ENCODER_ENV, raising=False)
    monkeypatch.setattr(env, "nvenc_ready", lambda *a, **k: (True, "h264_nvenc funciona"))
    assert env.encoder_mode() == "auto" and env.use_gpu_encoder()
    a = env.encoder_args(18)
    assert a[:2] == ["-c:v", "h264_nvenc"] and a[a.index("-cq") + 1] == "18"
    monkeypatch.setattr(env, "nvenc_ready", lambda *a, **k: (False, "sin GPU NVIDIA"))
    assert not env.use_gpu_encoder() and env.encoder_args(16)[:4] == ["-c:v", "libx264", "-crf", "16"]
    monkeypatch.setenv(env.ENCODER_ENV, "nvenc")                         # forzado aunque la prueba diga que no
    assert env.use_gpu_encoder() and env.encoder_mode() == "nvenc"
    for v, mode in (("gpu", "nvenc"), ("x264", "cpu"), ("libx264", "cpu"), ("CPU", "cpu"), ("loquesea", "auto"), ("", "auto")):
        monkeypatch.setenv(env.ENCODER_ENV, v)
        assert env.encoder_mode() == mode, v
    assert env.use_gpu_encoder(False) is False and env.encoder_args()[1] == "libx264"    # --cpu
    monkeypatch.setattr(env, "nvenc_ready", lambda *a, **k: (False, "x"))
    assert env.use_gpu_encoder(True) is True                                               # --gpu


def test_nvenc_probe_is_cached_per_ffmpeg(tmp_path, monkeypatch):
    from frame28 import env
    ff = tmp_path / "ffmpeg.exe"
    ff.write_bytes(b"x" * 10)
    monkeypatch.setattr(env, "ffmpeg", lambda: str(ff))
    calls = []
    probe = lambda f: calls.append(f) or (True, "h264_nvenc funciona")
    cache = tmp_path / "nvenc.json"
    assert env.nvenc_ready(cache, now=100, probe=probe) == (True, "h264_nvenc funciona") and len(calls) == 1
    assert env.nvenc_ready(cache, now=100 + env.NVENC_TTL - 1, probe=probe)[0] and len(calls) == 1     # de la caché
    ff.write_bytes(b"x" * 11)                                                                           # otro ffmpeg: se prueba
    assert env.nvenc_ready(cache, now=200, probe=lambda f: (False, "No NVENC capable devices found")) == (False, "No NVENC capable devices found")
    assert env.nvenc_ready(cache, now=200 + env.NVENC_TTL + 1, probe=probe)[0] and len(calls) == 2     # caducada: se prueba
    monkeypatch.setattr(env, "ffmpeg", lambda: None)
    assert env.nvenc_ready(cache, probe=probe) == (False, "sin ffmpeg")


def test_batch_passes_workers_and_gpu_to_render(tmp_path, monkeypatch):
    import inspect
    from frame28 import clips
    sig = inspect.signature(clips.batch)
    assert sig.parameters["workers"].default is None and sig.parameters["gpu"].default is None
    src = inspect.getsource(clips.batch)
    assert "workers=workers, gpu=gpu" in src                              # llegan al render de cada variante


def test_doctor_release_row_compares_versions():
    # HANDOFF (2026-10-01): un usuario con una instalación vieja no sabía que había versión nueva ni cómo actualizar
    from frame28.doctor import release_newer
    assert release_newer("0.4.0", "v0.5.0") is True
    assert release_newer("0.4.0", "v0.4.0") is False
    assert release_newer("0.10.0", "v0.9.9") is False          # compara números, no texto
    assert release_newer("0.4.0", None) is None and release_newer("0.4.0", "rc") is None
    assert release_newer(None, "v0.5.0") is None


def test_doctor_release_cache(tmp_path, monkeypatch):
    # F28-11: sin red, doctor esperaba el timeout de GitHub en cada ejecución; y sin token GitHub da 60 consultas por hora
    from frame28 import doctor as D
    calls = []
    answer = {"tag": "v0.6.0"}
    monkeypatch.setattr(D, "_fetch_release", lambda url, timeout: calls.append(url) or answer["tag"])
    cache = tmp_path / "release.json"
    assert D.latest_release(cache=cache, now=1000) == "v0.6.0" and len(calls) == 1
    assert D.latest_release(cache=cache, now=1000 + D.RELEASE_TTL - 1) == "v0.6.0" and len(calls) == 1   # de la caché
    answer["tag"] = None                                                                                  # se cae la red
    assert D.latest_release(cache=cache, now=1000 + D.RELEASE_TTL + 1) is None and len(calls) == 2
    assert D.latest_release(cache=cache, now=1000 + D.RELEASE_TTL + 60) is None and len(calls) == 2     # el fallo también se recuerda
    answer["tag"] = "v0.7.0"
    assert D.latest_release(cache=cache, now=1000 + D.RELEASE_TTL + D.RELEASE_FAIL_TTL + 2) == "v0.7.0" and len(calls) == 3
    assert D.latest_release(url="https://otra", cache=cache, now=1000 + D.RELEASE_TTL + D.RELEASE_FAIL_TTL + 3) == "v0.7.0"
    assert len(calls) == 4                                                                                 # otra URL: no vale la caché
    cache.write_text("{roto", encoding="utf-8")
    assert D.latest_release(cache=cache, now=0) == "v0.7.0" and len(calls) == 5                         # caché rota: se pregunta


def test_doctor_plugin_installed(tmp_path):
    from frame28.doctor import plugin_installed
    f = tmp_path / "installed_plugins.json"
    assert plugin_installed(f) == (False, None)                                                            # sin Claude Code
    f.write_text('{"version": 2, "plugins": {"frame28@think28": [{"scope": "user", "version": "0.4.0"},'
                 ' {"scope": "project", "version": "0.5.0"}], "otro@x": [{"version": "9.9.9"}]}}', encoding="utf-8")
    assert plugin_installed(f) == (True, "0.5.0")                                                          # la más nueva de las dos
    f.write_text('{"frame28@think28": {"version": "0.3.1"}}', encoding="utf-8")                           # formato plano antiguo
    assert plugin_installed(f) == (True, "0.3.1")
    f.write_text('{"plugins": {"otro@x": [{"version": "1.0.0"}]}}', encoding="utf-8")
    assert plugin_installed(f) == (True, None)                                                             # Claude Code sí, el plugin no
    f.write_text("[1, 2]", encoding="utf-8")
    assert plugin_installed(f) == (True, None)
    f.write_text("no es json", encoding="utf-8")
    assert plugin_installed(f) == (True, None)


def test_doctor_version_rows():
    from frame28.doctor import CLI_UPGRADE, PLUGIN_INSTALL, PLUGIN_UPGRADE, version_rows
    cli, plug = version_rows("0.5.0", "v0.6.0", (True, "0.4.0"))
    assert cli["name"] == "última release (CLI)" and not cli["ok"] and cli["fix"] == CLI_UPGRADE and "v0.6.0 publicada" in cli["detail"]
    assert plug["name"] == "plugin (Claude Code)" and not plug["ok"] and plug["fix"] == PLUGIN_UPGRADE and plug["detail"].startswith("0.4.0")
    assert all(r["optional"] for r in (cli, plug))                                                        # nunca bloquean «Todo listo»
    cli, plug = version_rows("0.6.0", "v0.6.0", (True, "0.6.0"))
    assert cli["ok"] and plug["ok"] and cli["fix"] == plug["fix"] == "" and plug["detail"] == "0.6.0 al día"
    cli, plug = version_rows("0.6.0", None, (True, "0.6.0"))                                              # sin red
    assert cli["ok"] and plug["ok"] and "sin respuesta" in cli["detail"]
    _, plug = version_rows("0.6.0", "v0.6.0", (True, None))
    assert not plug["ok"] and plug["fix"] == PLUGIN_INSTALL
    _, plug = version_rows("0.6.0", "v0.6.0", (False, None))
    assert not plug["ok"] and plug["fix"].endswith(PLUGIN_INSTALL) and "Claude Code" in plug["detail"]


def test_avisos_de_descarga_por_stderr(tmp_path, monkeypatch, capsys):
    from pathlib import Path
    # F28-83: «Descargando modelo…» salía por stdout y rompía el JSON de matte/speaker/gestures/prep en la primera ejecución
    from frame28 import env
    monkeypatch.setattr(env, "fetch_atomic", lambda url, dest, sha=None, **k: (Path(dest).parent.mkdir(parents=True, exist_ok=True),
                                                                         Path(dest).write_bytes(b"modelo")))
    got = env.download("https://example.invalid/m.onnx", tmp_path / "sub" / "m.onnx", "modelo de prueba")
    out = capsys.readouterr()
    assert got.read_bytes() == b"modelo" and out.out == "" and "Descargando modelo de prueba" in out.err


def test_ningun_modulo_escribe_avisos_por_stdout():
    from pathlib import Path
    # Las órdenes devuelven JSON por stdout: solo cli.py (click.echo) escribe ahí; un print() suelto lo rompe
    import re
    pkg = Path(__file__).resolve().parents[1] / "frame28"
    bad = [f"{f.name}:{n}" for f in pkg.glob("*.py") for n, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1)
           if re.search(r"(?<![\w.])print\(", line) and "file=sys.stderr" not in line]
    assert bad == [], f"print() a stdout en: {bad} (usa env.note)"


def test_gpu_decode_only_for_h264_hevc_with_nvenc(monkeypatch):
    # F28-115, medido: H.264/HEVC ganan ~30 % decodificando en la GPU con el camino entero en ella; AV1 pierde (66 s vs 27 s)
    from frame28 import env, media
    monkeypatch.setattr(env, "use_gpu_encoder", lambda *a: True)
    monkeypatch.setattr(env, "nvdec_ready", lambda: True)
    h264 = {"video": {"codec": "h264", "width": 1920, "height": 1080}}
    pre, vf = media.gpu_decode_args(h264, 30, None)
    assert pre == ["-hwaccel", "cuda", "-hwaccel_output_format", "cuda"] and vf == "fps=30,scale_cuda=format=yuv420p"
    assert media.gpu_decode_args({"video": {"codec": "hevc", "width": 3840, "height": 2160}}, 30, 1920)[1] == \
        "fps=30,scale_cuda=w=1920:h=1080:format=yuv420p"
    assert media.gpu_decode_args({"video": {"codec": "h264", "width": 1080, "height": 1920}}, 30, 1280)[1] == \
        "fps=30,scale_cuda=w=720:h=1280:format=yuv420p"                     # vertical: el lado largo, como scale_filter
    assert media.gpu_decode_args({"video": {"codec": "av1", "width": 1920, "height": 1080}}, 30, None) is None
    # rango completo (móviles): la vía de CPU también deja yuvj420p (medido), así que la GPU no cambia el resultado
    assert media.gpu_decode_args({"video": {"codec": "h264", "width": 1920, "height": 1080, "pix_fmt": "yuvj420p"}}, 30, None)
    monkeypatch.setattr(env, "use_gpu_encoder", lambda *a: False)        # --cpu o sin NVENC: nada de GPU
    assert media.gpu_decode_args(h264, 30, None) is None
    monkeypatch.setattr(env, "use_gpu_encoder", lambda *a: True)
    monkeypatch.setattr(env, "nvdec_ready", lambda: False)
    assert media.gpu_decode_args(h264, 30, None) is None
    assert media.scaled_size({"width": 1921, "height": 1081}, 1000) == (1000, 562) and media.scaled_size({}, 1000) is None


# ── F28-81: check aprobaba aunque HyperFrames no llegara a ejecutarse, y nunca salía con error ───────────────────────
HF_OK = """Layout
  ℹ t=5.42s text_occluded span.wi > div:nth-of-type(10) inside #bh-fg "E" — Text is hidden beneath an opaque element.
  0 error(s), 0 warning(s), 16 info(s)

Contrast
  ✗ #end-s 2.82:1 (need 3:1, t=18.417s)
    Try rgb(90,90,90); source index.html
  0 error(s), 2 warning(s), 0 info(s)

◇  Check passed
"""
HF_FAIL = """Lint
  ✗ media_missing_id <video src="assets/b.mp4"> — every media element needs an id
  1 error(s), 0 warning(s), 0 info(s)

◇  Check failed
"""
HF_OLD_OCCLUDED = """Layout
  ✗ t=5.42s text_occluded #bh-w "N" — Text is hidden beneath an opaque element.
  1 error(s), 0 warning(s), 0 info(s)
◇  Check failed
"""
NPM_DOWN = "npm error code ENOTFOUND\nnpm error network request to https://registry.npmjs.org/hyperframes failed\n"


def test_parse_check_reads_hyperframes_output():
    from frame28.render import parse_check
    ok = parse_check(0, HF_OK)
    assert ok["passed"] and ok["ran"] and ok["errors"] == [] and len(ok["contrast_warnings"]) == 1
    bad = parse_check(1, HF_FAIL)
    assert not bad["passed"] and bad["errors"][0].startswith("✗ media_missing_id")
    old = parse_check(1, HF_OLD_OCCLUDED)                      # el falso positivo del texto detrás no tumba el check
    assert old["passed"] and len(old["known_false_positives"]) == 1


@pytest.mark.parametrize("rc, out", [(1, NPM_DOWN), (0, ""), (0, "algo que no es la salida de HyperFrames"), (127, "npx no encontrado")])
def test_parse_check_fails_when_hyperframes_did_not_run(rc, out):
    from frame28.render import parse_check
    r = parse_check(rc, out)
    assert not r["passed"] and not r["ran"] and "no llegó a ejecutarse" in r["errors"][0] and "doctor" in r["errors"][0]


def test_parse_check_does_not_approve_errors_it_cannot_read():
    from frame28.render import parse_check
    r = parse_check(1, "Lint\n  3 error(s), 0 warning(s)\n◇  Check failed\n")
    assert not r["passed"] and r["ran"] and "no se pudieron leer" in r["errors"][0]


def test_check_command_exit_code(monkeypatch, tmp_path):
    from click.testing import CliRunner
    from frame28 import render as R
    from frame28.cli import main
    monkeypatch.setattr(R, "_hf", lambda *a, **k: (_ for _ in ()).throw(FileNotFoundError()))
    r = CliRunner().invoke(main, ["check", str(tmp_path)])
    assert r.exit_code == 1 and "✗ check falló" in r.output and "npx no encontrado" in r.output
    class Done:
        returncode, stdout, stderr = 0, HF_OK, ""
    monkeypatch.setattr(R, "_hf", lambda *a, **k: Done())
    r = CliRunner().invoke(main, ["check", str(tmp_path)])
    assert r.exit_code == 0 and "✓ check pasó" in r.output and "aviso de contraste" in r.output
    r = CliRunner().invoke(main, ["check", str(tmp_path), "--json"])
    assert r.exit_code == 0 and json.loads(r.output)["passed"] is True


# ── F28-82: descargas atómicas y con SHA-256 ─────────────────────────────────────────────────────────────────────────
class _Resp:
    def __init__(self, data, length=None):
        self.data, self.headers = data, {"Content-Length": str(len(data) if length is None else length)}
        self.pos = 0
    def __enter__(self): return self
    def __exit__(self, *a): return False
    def read(self, n):
        chunk = self.data[self.pos:self.pos + n]; self.pos += n
        return chunk


def test_fetch_atomic_complete_truncated_and_bad_hash(tmp_path, monkeypatch):
    import hashlib
    from frame28 import env
    good = b"x" * 200_000
    sha = hashlib.sha256(good).hexdigest()
    monkeypatch.setattr("urllib.request.urlopen", lambda req, timeout: _Resp(good))
    dest = tmp_path / "m" / "model.onnx"
    assert env.fetch_atomic("https://h/m", dest, sha) == dest and dest.read_bytes() == good
    calls = []
    def cut(req, timeout):                       # el servidor anuncia 200 000 bytes y la conexión se corta a la mitad
        calls.append(1); return _Resp(good[:100_000], length=len(good))
    monkeypatch.setattr("urllib.request.urlopen", cut)
    other = tmp_path / "otro.onnx"
    with pytest.raises(SystemExit, match="incompleta"):
        env.fetch_atomic("https://h/m", other, sha)
    assert not other.exists() and len(calls) == 2 and not list(tmp_path.glob("*.part-*"))   # reintenta y no deja restos
    monkeypatch.setattr("urllib.request.urlopen", lambda req, timeout: _Resp(b"y" * 10))
    with pytest.raises(SystemExit, match="no es el esperado"):
        env.fetch_atomic("https://h/m", other, sha)
    assert not other.exists()


def test_download_replaces_a_corrupt_model(tmp_path, monkeypatch, capsys):
    import hashlib
    from frame28 import env
    good = b"modelo bueno"
    sha = hashlib.sha256(good).hexdigest()
    dest = tmp_path / "rvm.onnx"
    dest.write_bytes(b"model")                                       # lo que deja una descarga cortada
    assert not env.model_ok(dest, sha)
    monkeypatch.setattr("urllib.request.urlopen", lambda req, timeout: _Resp(good))
    env.download("https://h/m", dest, "modelo de prueba", sha)
    assert dest.read_bytes() == good and env.model_ok(dest, sha) and "corrupto" in capsys.readouterr().err
    monkeypatch.setattr("urllib.request.urlopen", lambda req, timeout: (_ for _ in ()).throw(AssertionError("no debía bajar")))
    assert env.download("https://h/m", dest, "modelo de prueba", sha) == dest   # bueno: no se vuelve a bajar
    assert not env.model_ok(tmp_path / "no-existe.onnx", sha)


def test_models_are_pinned_with_hashes():
    from frame28 import audio, env, pose
    for sha in (env.RVM_MODEL_SHA256, pose.POSE_MODEL_SHA256, audio.RNNOISE_MODEL_SHA256):
        assert len(sha) == 64 and int(sha, 16) >= 0
    assert "/master/" not in audio.RNNOISE_MODEL_URL                   # fijado a un commit, no a una rama que cambia


# ── F28-86: errores habituales como mensajes, no trazas ──────────────────────────────────────────────────────────────
def test_storyboard_with_bom_is_read(tmp_path):
    # PowerShell 5.1 (Set-Content -Encoding UTF8) guarda con BOM y json.loads reventaba con una traza
    sb = {"version": 1, "source": {"video": "c.mp4", "duration": 5}, "overlays": []}
    p = tmp_path / "sb.json"
    p.write_bytes(b"\xef\xbb\xbf" + json.dumps(sb).encode("utf-8"))
    r = CliRunner().invoke(main, ["storyboard", "validate", str(p)])
    assert r.exit_code == 0 and "Storyboard válido." in r.output


def test_card_title_as_plain_text_builds(tmp_path):
    from frame28.build import build_project
    sb = {"version": 1, "source": {"video": "c.mp4", "duration": 5}, "canvas": {"width": 1920, "height": 1080},
          "overlays": [{"type": "card", "id": "c1", "start": 0, "end": 2, "title": "Hola", "subtitle": "qué tal"}]}
    p = tmp_path / "sb.json"; p.write_text(json.dumps(sb), encoding="utf-8")
    res = build_project(p, tmp_path / "project", copy_assets=False)
    html = (tmp_path / "project" / "index.html").read_text(encoding="utf-8")
    assert res["overlays"] == 1 and "Hola" in html and "qué tal" in html


def test_render_timeout_grows_with_the_video(tmp_path, monkeypatch):
    from frame28.render import render_timeout
    monkeypatch.delenv("FRAME28_RENDER_TIMEOUT", raising=False)
    (tmp_path / "index.html").write_text('<div data-duration="19.5"><div data-duration="10.0">', encoding="utf-8")
    assert render_timeout(tmp_path) == 3600                                  # un clip corto: el mínimo de una hora
    (tmp_path / "index.html").write_text('<div data-duration="600">', encoding="utf-8")
    assert render_timeout(tmp_path) == 36000                                 # 10 min de vídeo: 10 h de margen
    monkeypatch.setenv("FRAME28_RENDER_TIMEOUT", "120")
    assert render_timeout(tmp_path) == 120
    monkeypatch.delenv("FRAME28_RENDER_TIMEOUT")
    assert render_timeout(tmp_path / "no-existe") == 3600


def test_friendly_errors():
    import subprocess
    import urllib.error
    from frame28.cli import friendly_error
    msg, code = friendly_error(urllib.error.HTTPError("https://tienda.example/logo.png", 403, "Forbidden", {}, None))
    assert code == 3 and "403" in msg and "anti-bots" in msg and "--logo-url" in msg
    assert friendly_error(urllib.error.URLError("getaddrinfo failed"))[1] == 3
    try:
        json.loads('{"a": 1,}')
    except json.JSONDecodeError as e:
        msg, code = friendly_error(e)
    assert code == 2 and "línea 1" in msg
    msg, code = friendly_error(subprocess.TimeoutExpired(["C:/x/npx.cmd", "hyperframes"], 300))
    assert code == 4 and "npx.cmd" in msg and "300 s" in msg
    assert "doctor" in friendly_error(FileNotFoundError(2, "No such file", "ffmpeg"))[0]
    assert friendly_error(ValueError("x")) is None


def test_run_prints_short_errors_and_debug_shows_the_trace(monkeypatch, capsys):
    import urllib.error
    from frame28 import cli
    def boom():
        raise urllib.error.HTTPError("https://t.example", 403, "Forbidden", {}, None)
    monkeypatch.setattr(cli, "main", boom)
    monkeypatch.delenv("FRAME28_DEBUG", raising=False)
    with pytest.raises(SystemExit) as e:
        cli.run()
    err = capsys.readouterr().err
    assert e.value.code == 3 and err.startswith("Error: ") and "Traceback" not in err
    monkeypatch.setattr(cli, "main", lambda: (_ for _ in ()).throw(ZeroDivisionError("raro")))
    with pytest.raises(SystemExit) as e:
        cli.run()
    assert e.value.code == 1 and "FRAME28_DEBUG=1" in capsys.readouterr().err
    monkeypatch.setenv("FRAME28_DEBUG", "1")
    with pytest.raises(ZeroDivisionError):
        cli.run()


def test_npx_cmd_skips_cmd_exe_on_windows(tmp_path):
    # F28-87: npx.cmd lanzado por cmd.exe partía una ruta con & (C:\Clientes\R&D\) y ejecutaba el resto como otra orden
    from frame28.env import npx_cmd
    d = tmp_path / "nodejs"
    (d / "node_modules" / "npm" / "bin").mkdir(parents=True)
    (d / "npx.cmd").write_text("@echo off", encoding="ascii")
    (d / "node.exe").write_bytes(b"")
    (d / "node_modules" / "npm" / "bin" / "npx-cli.js").write_text("", encoding="utf-8")
    assert npx_cmd(str(d / "npx.cmd")) == [str(d / "node.exe"), str(d / "node_modules" / "npm" / "bin" / "npx-cli.js")]
    (d / "node_modules" / "npm" / "bin" / "npx-cli.js").unlink()
    assert npx_cmd(str(d / "npx.cmd")) == [str(d / "npx.cmd")]          # sin npx-cli.js: el .cmd tal cual
    assert npx_cmd("/usr/bin/npx.sh") == ["/usr/bin/npx.sh"]              # fuera de Windows, npx tal cual


def test_probe_measures_loudness_on_audio_only(monkeypatch):
    # F28-90: volumedetect decodificaba también el vídeo (8,8 s frente a 0,6 s en un AV1 de 197 s); y quien solo quería
    # dimensiones o duración pagaba esa pasada entera
    from frame28 import media
    calls = []
    ffprobe_json = json.dumps({"format": {"duration": "10.0", "bit_rate": "1000"}, "streams": [
        {"codec_type": "video", "codec_name": "h264", "width": 1920, "height": 1080, "r_frame_rate": "30/1", "pix_fmt": "yuv420p"},
        {"codec_type": "audio", "codec_name": "aac", "sample_rate": "48000", "channels": 2}]})
    class R:
        def __init__(self, out="", err=""): self.returncode, self.stdout, self.stderr = 0, out, err
    def fake_run(cmd, **k):
        calls.append(cmd)
        return R(ffprobe_json) if "ffprobe" in str(cmd[0]).lower() or "-show_entries" in cmd else R(err="mean_volume: -20.5 dB\nmax_volume: -1.0 dB")
    monkeypatch.setattr(media, "run", fake_run)
    monkeypatch.setattr(media, "ffprobe", lambda: "ffprobe"); monkeypatch.setattr(media, "ffmpeg", lambda: "ffmpeg")
    info = media.probe("v.mp4")
    assert info["audio"]["mean_db"] == -20.5 and info["video"]["width"] == 1920
    vol = [c for c in calls if "volumedetect" in c][0]
    assert vol.count("-vn") == 2 and vol.index("-vn") < vol.index("-i")              # el vídeo ni se decodifica
    calls.clear()
    fast = media.probe("v.mp4", loudness=False)
    assert len(calls) == 1 and "mean_db" not in fast["audio"] and fast["duration"] == 10.0


def test_doctor_requires_node_22():
    # F28-104: doctor daba por buena cualquier versión de Node; HyperFrames necesita la 22
    from frame28.doctor import NODE_MIN, node_major
    assert NODE_MIN == 22
    assert node_major("v18.19.0") == 18 and node_major("v22.11.0") == 22 and node_major("") == 0 and node_major("x") == 0
