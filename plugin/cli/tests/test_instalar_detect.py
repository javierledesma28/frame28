"""docs/instalar/detect.js: la pestaña que abre /instalar según el navegador (F28-255). Se ejecuta con Node."""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

DETECT = Path(__file__).resolve().parents[3] / "docs" / "instalar" / "detect.js"
CASES = [
    # (user-agent, navigator.platform, userAgentData.platform, mobile) → (os, mobile)
    ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Safari/537.36", "Win32", "Windows", False, "win", False),
    ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Safari/537.36 Edg/129.0", "Win32", "Windows", False, "win", False),
    ("Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:131.0) Gecko/20100101 Firefox/131.0", "Win32", None, False, "win", False),
    ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Safari/605.1.15", "MacIntel", None, False, "mac", False),
    ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Safari/537.36", "MacIntel", "macOS", False, "mac", False),
    ("Mozilla/5.0 (Macintosh; Intel Mac OS X 14.6; rv:131.0) Gecko/20100101 Firefox/131.0", "MacIntel", None, False, "mac", False),
    ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Safari/537.36", "Linux x86_64", "Linux", False, "linux", False),
    ("Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:131.0) Gecko/20100101 Firefox/131.0", "Linux x86_64", None, False, "linux", False),
    ("Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Mobile Safari/537.36", "Linux armv8l", "Android", True, None, True),
    ("Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1", "iPhone", None, False, None, True),
    ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1", "MacIntel", None, False, None, True),  # iPad
    ("Mozilla/5.0 (compatible; Bot/1.0)", "", None, False, None, False),
]


@pytest.mark.skipif(not shutil.which("node"), reason="hace falta Node")
def test_detect_os_for_each_browser_and_system():
    js = f"const {{detectOS}} = require({json.dumps(str(DETECT))});" \
         f"console.log(JSON.stringify({json.dumps([c[:4] for c in CASES])}.map(c => detectOS(...c))));"
    out = json.loads(subprocess.run(["node", "-e", js], capture_output=True, text=True, check=True).stdout)
    for case, got in zip(CASES, out):
        assert (got["os"], got["mobile"]) == (case[4], case[5]), (case[0][:60], got)
