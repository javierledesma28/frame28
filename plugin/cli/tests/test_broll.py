"""broll: sidecar de licencia con lo que sale en el clip (personas, marcas) para no usarlo mal en un anuncio."""
from __future__ import annotations

import json
from pathlib import Path

from frame28 import broll


def test_content_flags_people_brands_and_unknown():
    # F28-199: Pexels prohíbe sugerir que las personas respaldan un producto; Pixabay, el uso comercial de marcas
    f = broll.content_flags({"tags": "woman, laptop, office", "query": "working"})
    assert f["people"] and not f["brands"] and f["ad_use"] == "evitar en anuncios"
    f = broll.content_flags({"tags": "coffee, starbucks, cup", "query": "coffee"})
    assert f["brands"] and f["ad_use"] == "evitar en anuncios"
    f = broll.content_flags({"tags": "wood, workshop, saw", "query": "sawdust"})
    assert not f["people"] and not f["brands"] and f["ad_use"] == "ok" and f["notes"] == []
    f = broll.content_flags({"tags": "", "query": "sharpening knife"})               # vídeo de Pexels sin etiquetas
    assert f["ad_use"] == "revisar" and "mira el clip" in f["notes"][0]
    assert broll.content_flags({"tags": "", "query": "happy family"})["people"]       # la consulta también cuenta


def test_fetch_writes_the_content_flags_in_the_sidecar(tmp_path, monkeypatch):
    from frame28 import env
    monkeypatch.setattr(env, "fetch_atomic", lambda url, dst, **k: Path(dst).write_bytes(b"x"))
    item = {"id": "pixabay-1", "provider": "pixabay", "kind": "photo", "url": "https://x/1.jpg", "page": "https://pixabay.com/1",
            "author": "a", "license": "Pixabay Content License", "width": 10, "height": 10, "duration": None,
            "tags": "man, smiling, portrait", "query": "smile"}
    r = broll.fetch(item, tmp_path)
    side = json.loads(Path(r["sidecar"]).read_text(encoding="utf-8"))
    assert side["content"]["people"] is True and side["content"]["ad_use"] == "evitar en anuncios" and side["tags"] == "man, smiling, portrait"
