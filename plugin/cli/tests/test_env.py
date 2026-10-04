"""env: descargas de modelos (aviso de licencia) y avisos de terceros al día con las dependencias."""
from __future__ import annotations

import re
from pathlib import Path

from frame28 import env

ROOT = Path(__file__).resolve().parents[3]


def test_download_tells_the_model_license_only_when_it_downloads(tmp_path, monkeypatch, capsys):
    # F28-198: el modelo de RVM es GPL-3 y lo baja el usuario; hay que decírselo al descargarlo
    dest = tmp_path / "m.onnx"
    monkeypatch.setattr(env, "fetch_atomic", lambda url, d, sha: Path(d).write_bytes(b"x"))
    monkeypatch.setattr(env, "model_ok", lambda d, sha: Path(d).exists())
    env.download("https://github.com/x/y/m.onnx", dest, "modelo de prueba", None, license="GPL-3.0 (prueba)")
    err = capsys.readouterr().err
    assert "Licencia: GPL-3.0 (prueba)" in err and "github.com" in err and "THIRD-PARTY-NOTICES" in err
    env.download("https://github.com/x/y/m.onnx", dest, "modelo de prueba", None, license="GPL-3.0 (prueba)")
    assert capsys.readouterr().err == ""                    # ya en caché: ni descarga ni aviso


def test_third_party_notices_cover_every_dependency():
    notices = (ROOT / "THIRD-PARTY-NOTICES.md").read_text(encoding="utf-8").lower()
    deps = re.search(r"^dependencies = \[(.*?)\]", (ROOT / "plugin/cli/pyproject.toml").read_text(encoding="utf-8"), re.S | re.M).group(1)
    names = [re.match(r"[a-z0-9_.-]+", d.strip().strip('",').lower()).group(0) for d in deps.splitlines() if d.strip().strip('",')]
    missing = [n for n in names if n not in notices]
    assert not missing, f"añade a THIRD-PARTY-NOTICES.md: {missing}"
    assert "gpl-3.0" in notices and "dentro del propio proceso" in notices
