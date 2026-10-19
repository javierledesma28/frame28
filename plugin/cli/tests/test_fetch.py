"""`frame28 fetch` v2 (F28-358, decisión A-312): enlace seguro, puerta de derechos, selector de vídeos, topes, caché,
subtítulos y errores en nuestro idioma. Sin red: yt-dlp se sustituye por un doble que responde como él."""
from __future__ import annotations

import json
import socket
import subprocess
from datetime import datetime
from pathlib import Path

import pytest
from click.testing import CliRunner

from frame28 import fetch as F
from frame28.cli import main

YT = "https://www.youtube.com/watch?v=FkgVB19I6xw"
PAGE = "https://svs.example.org/15012"


def public(host, port):
    return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 0))]


def video(**kw) -> dict:
    base = {"_type": "video", "id": "FkgVB19I6xw", "extractor_key": "Youtube", "title": "Apollo 11 (dominio público)",
            "language": "en",
            "uploader": "NASA", "duration": 46, "upload_date": "20190716", "webpage_url": YT,
            "requested_formats": [{"filesize": 6_000_000}, {"filesize": 2_000_000}],
            "subtitles": {"en": [{}]}, "automatic_captions": {"es": [{}], "en-orig": [{}]},
            "chapters": [{"start_time": 0, "end_time": 20, "title": "Despegue"}]}
    base.update(kw)
    return base


class FakeYtDlp:
    """Responde como yt-dlp: `-J` con los datos del destino; una descarga deja el fichero (y los .srt si se piden)."""

    def __init__(self, infos: dict, fail_download: tuple[int, str] | None = None, write_file: bool = True,
                 stdout: str = ""):
        self.infos, self.fail_download, self.write_file, self.stdout = infos, fail_download, write_file, stdout
        self.channel = "stable"
        self.calls: list[list[str]] = []

    @property
    def downloads(self) -> list[list[str]]:
        return [c for c in self.calls if "-J" not in c]

    def call(self, args):
        self.calls.append(list(args))
        target = args[-1]
        if "-J" in args:
            v = self.infos[target]
            if isinstance(v, tuple):
                return subprocess.CompletedProcess(args, v[0], "", v[1])
            return subprocess.CompletedProcess(args, 0, "[debug] ruido\n" + json.dumps(v), "")
        if self.fail_download:
            return subprocess.CompletedProcess(args, self.fail_download[0], "", self.fail_download[1])
        stem = args[args.index("-o") + 1].replace(".%(ext)s", "")
        if "--skip-download" not in args and self.write_file:
            Path(stem + (".m4a" if "-x" in args else ".mp4")).write_bytes(b"x" * 1000)
        if "--sub-langs" in args:
            for lang in args[args.index("--sub-langs") + 1].split(","):
                Path(f"{stem}.{lang}.srt").write_text("1\n00:00:00,000 --> 00:00:01,000\nhola\n", encoding="utf-8")
        return subprocess.CompletedProcess(args, 0, self.stdout, "")


def run_fetch(y, tmp_path, url=YT, **kw):
    kw.setdefault("out", tmp_path / "input.mp4")
    return F.fetch(url, ytdlp=y, resolve=public, **kw)


# ---------- enlace (SSRF en el PC del cliente) ----------

@pytest.mark.parametrize("url", [
    "file:///etc/passwd", "ftp://example.com/v.mp4", "javascript:alert(1)", "//example.com/v", "example.com/v",
    "https://user:clave@www.youtube.com/watch?v=x", "https://@www.youtube.com/watch?v=x",
    "http://localhost:8000/v.mp4", "http://LOCALHOST./v", "http://foo.localhost/v", "http://nas.local/v.mp4",
    "http://router.lan/", "http://x.internal/", "http://printer.home.arpa/",
    "http://127.0.0.1/", "http://0.0.0.0/", "http://10.0.0.5/", "http://172.16.3.4/", "http://192.168.1.10/v.mp4",
    "http://169.254.169.254/latest/meta-data/", "http://100.64.0.1/", "http://[::1]/", "http://[fe80::1]/",
    "http://[fd00::1]/", "http://[::ffff:127.0.0.1]/", "http://224.0.0.1/", "https://www.you\ntube.com/", "https:///v",
])
def test_check_url_rejects_unsafe_links(url):
    with pytest.raises(F.FetchError) as e:
        F.check_url(url, resolve=public)
    assert e.value.kind == "url"


def test_check_url_rejects_names_that_resolve_to_private_addresses():
    def to_loopback(host, port):
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 0))]

    def mixed(host, port):   # basta con una dirección privada entre las públicas
        return public(host, port) + [(socket.AF_INET6, socket.SOCK_STREAM, 6, "", ("fe80::1%12", 0, 0, 0))]

    for resolve in (to_loopback, mixed):
        with pytest.raises(F.FetchError) as e:
            F.check_url("https://localtest.me/v.mp4", resolve=resolve)
        assert e.value.kind == "url" and "red privada" in str(e.value)


def test_check_url_accepts_public_links_and_reports_unknown_hosts():
    assert F.check_url(f"  {YT} ", resolve=public) == YT
    assert F.check_url("http://93.184.216.34/v.mp4", resolve=public) == "http://93.184.216.34/v.mp4"

    def nxdomain(host, port):
        raise socket.gaierror(11001, "getaddrinfo failed")
    with pytest.raises(F.FetchError) as e:
        F.check_url("https://no-existe.example/v", resolve=nxdomain)
    assert e.value.kind == "network" and "no-existe.example" in str(e.value)


def test_unsafe_link_never_reaches_ytdlp(tmp_path):
    y = FakeYtDlp({})
    with pytest.raises(F.FetchError):
        F.fetch("http://192.168.1.10/v.mp4", tmp_path / "input.mp4", rights="own", ytdlp=y, resolve=public)
    assert y.calls == []


# ---------- errores en nuestro idioma ----------

@pytest.mark.parametrize("stderr,kind", [
    ("ERROR: [youtube] x: Sign in to confirm you're not a bot. Use --cookies-from-browser or --cookies", "blocked"),
    ("ERROR: unable to download video data: HTTP Error 429: Too Many Requests", "blocked"),
    ("ERROR: unable to download video data: HTTP Error 403: Forbidden", "forbidden"),
    ("ERROR: [youtube] x: Private video. Sign in if you've been granted access to this video", "private"),
    ("ERROR: [youtube] x: Sign in to confirm your age. This video may be inappropriate for some users.", "private"),
    ("ERROR: [youtube] x: Join this channel to get access to members-only content like this video", "private"),
    ("ERROR: [vimeo] 1: This video requires authentication; log in with --username", "private"),
    ("ERROR: [youtube] x: This live event will begin in 3 hours.", "live"),
    ("ERROR: [youtube] x: Video unavailable. This video has been removed by the uploader", "unavailable"),
    ("ERROR: [youtube] x: The uploader has not made this video available in your country", "unavailable"),
    ("ERROR: [youtube] aaaaaaaaaaa: This video is unavailable", "unavailable"),
    ("ERROR: Unsupported URL: https://example.com/no-es-un-video", "notfound"),
    ("ERROR: [generic] Unable to download webpage: HTTP Error 404: Not Found (caused by <HTTPError 404>)", "notfound"),
    ("ERROR: [youtube] x: Requested format is not available. Use --list-formats", "broken"),
    ("ERROR: [youtube] x: Unable to extract nsig function code; please report this issue", "broken"),
    ("ERROR: [Brightcove] 1: This video is DRM protected", "drm"),
    ("ERROR: [generic] Unable to download webpage: <urlopen error [Errno 11001] getaddrinfo failed>", "network"),
])
def test_explain_classifies_real_ytdlp_errors(stderr, kind):
    got, msg = F.explain("[debug] algo\n" + stderr)
    assert got == kind
    assert "report" not in msg.lower() and "yt-dlp -U" not in msg and msg.endswith(".")


def test_explain_blames_the_missing_js_runtime_not_the_403():
    err = ("WARNING: [youtube] No supported JavaScript runtime could be found. Only deno is enabled by default; "
           "some formats may be missing.\nERROR: unable to download video data: HTTP Error 403: Forbidden")
    assert F.explain(err)[0] == "js"
    assert F.explain("WARNING: No supported JavaScript runtime could be found\nERROR: Requested format is not available")[0] == "js"


def test_explain_unknown_error_drops_the_report_instructions():
    kind, msg = F.explain("ERROR: [foo] 1: algo raro pasó; please report this issue on https://github.com/yt-dlp/yt-dlp")
    assert kind == "other" and "algo raro pasó" in msg and "report" not in msg and "github" not in msg
    assert F.explain("")[0] == "other"


def test_messages_never_ask_for_cookies_or_updates():
    for kind, _, msg in F.EXPLAIN:
        low = msg.lower()
        assert "--cookies" not in low and "-u" not in low.split() and "report" not in low, kind


# ---------- yt-dlp: versión, canal y motor de JavaScript ----------

def test_js_runtime_args():
    assert F.js_runtime_args("/usr/bin/deno", "/usr/bin/node", "v24.1.0") == []
    assert F.js_runtime_args(None, "/usr/bin/node", "v22.12.0") == ["--js-runtimes", "node"]
    assert F.js_runtime_args(None, "/usr/bin/node", "v20.11.0") == []
    assert F.js_runtime_args(None, None) == []


def _bare_ytdlp(channel="stable"):
    y = object.__new__(F.YtDlp)
    y.path, y.version, y.uv, y.channel, y.common, y.retried = None, None, "uv", channel, ["--no-progress"], False
    return y


def test_ytdlp_retries_once_with_nightly_on_errors_a_newer_version_fixes(monkeypatch):
    seen = []
    answers = iter([subprocess.CompletedProcess([], 1, "", "ERROR: unable to download video data: HTTP Error 403: Forbidden"),
                    subprocess.CompletedProcess([], 0, "{}", "")])
    monkeypatch.setattr(F, "run", lambda cmd, **k: seen.append(cmd) or next(answers))
    y = _bare_ytdlp()
    assert y.call(["-J", YT]).returncode == 0
    assert "--prerelease" not in seen[0] and seen[1][seen[1].index("--prerelease") + 1] == "allow"
    assert y.channel == "nightly" and y.retried


@pytest.mark.parametrize("channel,stderr", [
    ("stable", "ERROR: [youtube] x: Private video. Sign in if you've been granted access"),   # no lo arregla otra versión
    ("nightly", "ERROR: unable to download video data: HTTP Error 403: Forbidden"),            # ya es la más nueva
])
def test_ytdlp_does_not_retry_when_it_cannot_help(monkeypatch, channel, stderr):
    seen = []
    monkeypatch.setattr(F, "run", lambda cmd, **k: seen.append(cmd) or subprocess.CompletedProcess(cmd, 1, "", stderr))
    assert _bare_ytdlp(channel).call(["-J", YT]).returncode == 1
    assert len(seen) == 1


def test_ytdlp_channel_from_environment(monkeypatch):
    monkeypatch.setenv("FRAME28_YTDLP_CHANNEL", "nightly")
    monkeypatch.setattr(F, "find_tool", lambda *a: None)
    monkeypatch.setattr("frame28.env.ffmpeg", lambda: "/opt/ffmpeg/bin/ffmpeg")
    y = F.YtDlp()
    assert y.channel == "nightly" and "--prerelease" in y.base()


# ---------- piezas ----------

def test_parsers():
    assert F.parse_seconds("90") == 90 and F.parse_seconds("1:30") == 90 and F.parse_seconds("1:02:03") == 3723
    assert F.parse_section("1:20-2:05") == (80, 125) and F.parse_section(" 10 - 20.5 ") == (10, 20.5)
    assert F.parse_section(None) is None
    assert F.parse_duration("3h") == 10800 and F.parse_duration("90m") == 5400 and F.parse_duration("600") == 600
    assert F.parse_duration("10s") == 10 and F.parse_duration(7200) == 7200
    assert F.parse_size("2GB") == 2 * 1024 ** 3 and F.parse_size("500MB") == F.parse_size("500m") == 500 * 1024 ** 2
    assert F.parse_size(F.MAX_SIZE_B) == F.MAX_SIZE_B
    for bad in (lambda: F.parse_section("2:00-1:00"), lambda: F.parse_section("ayer"), lambda: F.parse_duration("mucho"),
                lambda: F.parse_size("2 TB"), lambda: F.parse_seconds("1:xx")):
        with pytest.raises(F.FetchError) as e:
            bad()
        assert e.value.kind == "args"
    assert F.human_duration(46) == "0:46" and F.human_duration(3723) == "1:02:03" and F.human_duration(None) == "?"
    assert F.human_size(500 * 1024 ** 2) == "500 MB" and F.human_size(3 * 1024 ** 3) == "3.0 GB"


def test_estimate_size():
    assert F.estimate_size(video()) == 8_000_000
    by_rate = {"duration": 100, "requested_formats": [{"tbr": 800}, {"filesize_approx": 1000}]}
    assert F.estimate_size(by_rate) == 800 * 1000 / 8 * 100 + 1000
    assert F.estimate_size({"duration": 100, "requested_formats": [{}]}) is None


def test_summary_and_subtitles():
    s = F.summary(video())
    assert s["title"].startswith("Apollo") and s["duration"] == 46 and s["extractor"] == "Youtube" and s["language"] == "en"
    assert s["subtitles"] == {"manual": ["en"], "auto": ["en"], "auto_translated": 1}   # el original, no las traducciones
    other = F.subtitle_langs({"automatic_captions": {"fr": [{}], "de": [{}]}})              # sin «-orig»: todos
    assert other == {"manual": [], "auto": ["de", "fr"], "auto_translated": 0}
    assert s["chapters"] == [{"start": 0, "end": 20, "title": "Despegue"}]


def test_notice_texts():
    assert NOTICE_SHORT_ES == F.NOTICE_SHORT["es"]
    for lang in ("es", "en"):
        assert F.NOTICE[lang] and [o["rights"] for o in F.NOTICE_OPTIONS[lang]] == ["own", "licensed", None]
    assert [o["label"] for o in F.NOTICE_OPTIONS["es"]] == ["Es mío", "Tengo permiso del titular", "Cancelar"]


NOTICE_SHORT_ES = "Solo vídeos tuyos o con permiso de su titular; cumplir las condiciones de la plataforma te corresponde a ti."


# ---------- puerta de derechos ----------

def test_no_download_without_a_rights_answer(tmp_path):
    y = FakeYtDlp({YT: video()})
    with pytest.raises(F.FetchStop) as e:
        run_fetch(y, tmp_path)
    p = e.value.payload
    assert p["needs"] == "rights" and p["downloaded"] is False and p["notice_version"] == F.NOTICE_VERSION
    assert set(p["notice"]) == {"es", "en"} and len(p["options"]["es"]) == 3
    assert "--rights own" in p["next"] and "--rights licensed" in p["next"] and "Nunca" in p["next"]
    assert p["source"]["title"].startswith("Apollo")
    assert y.downloads == [] and not (tmp_path / "input.mp4").exists() and not (tmp_path / ".frame28").exists()


def test_invalid_rights_value(tmp_path):
    with pytest.raises(F.FetchError) as e:
        run_fetch(FakeYtDlp({YT: video()}), tmp_path, rights="yes")
    assert e.value.kind == "args"


def test_download_records_the_rights_answer(tmp_path):
    y = FakeYtDlp({YT: video()})
    r = run_fetch(y, tmp_path, rights="licensed")
    assert r["downloaded"] is True and (tmp_path / "input.mp4").exists()
    (args,) = y.downloads
    assert args[-1] == YT and args[args.index("-f") + 1].startswith("bv*[height<=1080]")
    assert args[args.index("--merge-output-format") + 1] == "mp4" and "--force-overwrites" in args
    assert args[args.index("--max-filesize") + 1] == str(F.MAX_SIZE_B) and "--no-playlist" in args
    side = json.loads((tmp_path / "input.source.json").read_text(encoding="utf-8"))
    assert side["rights"] == "licensed" and side["notice_version"] == F.NOTICE_VERSION
    assert datetime.fromisoformat(side["confirmed_at"]).tzinfo is not None
    assert side["url"] == YT and side["id"] == "FkgVB19I6xw" and side["mode"] == "video" and side["bytes"] == 1000
    assert side["chapters"][0]["title"] == "Despegue" and side["subtitles"]["manual"] == ["en"]
    manifest = json.loads((tmp_path / ".frame28" / "fetch.json").read_text(encoding="utf-8"))
    assert manifest["sources"]["Youtube:FkgVB19I6xw"]["rights"] == "licensed"
    assert any("subtítulos" in n and "--subs" in n for n in r["next"])          # el director los ofrece


def test_rights_are_asked_once_per_source_and_again_when_the_notice_changes(tmp_path, monkeypatch):
    y = FakeYtDlp({YT: video()})
    run_fetch(y, tmp_path, rights="own")
    r = run_fetch(y, tmp_path, audio=True)                                       # otra forma, misma fuente: no pregunta
    assert r["downloaded"] is True and r["rights"] == "own"
    monkeypatch.setattr(F, "NOTICE_VERSION", "2099-01-01")                       # aviso nuevo: las respuestas viejas no valen
    with pytest.raises(F.FetchStop) as e:
        run_fetch(y, tmp_path, section="0-10")
    assert e.value.payload["needs"] == "rights"


def test_rights_belong_to_the_project_folder(tmp_path):
    y = FakeYtDlp({YT: video()})
    run_fetch(y, tmp_path, out=tmp_path / "a" / "input.mp4", rights="own")
    with pytest.raises(F.FetchStop):
        run_fetch(y, tmp_path, out=tmp_path / "b" / "input.mp4")


def test_info_needs_no_rights_and_downloads_nothing(tmp_path):
    y = FakeYtDlp({YT: video()})
    r = run_fetch(y, tmp_path, info_only=True)
    assert r["downloaded"] is False and r["source"]["subtitles"]["auto"] == ["en"] and y.downloads == []
    assert r["notice_short"]["es"] == NOTICE_SHORT_ES


# ---------- caché, audio, tramo y subtítulos ----------

def test_cache_hit_and_force(tmp_path):
    y = FakeYtDlp({YT: video()})
    run_fetch(y, tmp_path, rights="own")
    r = run_fetch(y, tmp_path)
    assert r["cached"] is True and r["downloaded"] is False and "--force" in r["message"] and len(y.downloads) == 1
    assert r["rights"] == "own"
    r = run_fetch(y, tmp_path, force=True)
    assert r["downloaded"] is True and len(y.downloads) == 2


def test_cache_is_per_mode_and_section(tmp_path):
    y = FakeYtDlp({YT: video()})
    run_fetch(y, tmp_path, rights="own")
    run_fetch(y, tmp_path, out=tmp_path / "tramo.mp4", section="0:00-0:30")
    run_fetch(y, tmp_path, out=tmp_path / "tramo.mp4", section="0-30")        # el mismo tramo escrito de otra forma: caché
    assert len(y.downloads) == 2
    assert y.downloads[1][y.downloads[1].index("--download-sections") + 1] == "*0-30"


def test_audio_only(tmp_path):
    y = FakeYtDlp({YT: video()})
    r = F.fetch(YT, tmp_path / "voz.mp4", audio=True, rights="own", ytdlp=y, resolve=public)   # la extensión la pone --audio
    assert r["file"].endswith("voz.m4a") and (tmp_path / "voz.m4a").exists() and r["mode"] == "audio"
    (args,) = y.downloads
    assert args[args.index("-x") + 1: args.index("-x") + 3] == ["--audio-format", "m4a"]
    assert args[args.index("-f") + 1] == "ba[ext=m4a]/ba" and "--merge-output-format" not in args


def test_default_output_names(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    y = FakeYtDlp({YT: video()})
    assert F.fetch(YT, rights="own", ytdlp=y, resolve=public)["file"] == "input.mp4"
    assert F.fetch(YT, audio=True, ytdlp=y, resolve=public)["file"] == "input.m4a"
    assert (tmp_path / ".frame28" / "fetch.json").exists()


def test_subtitles_with_the_download(tmp_path):
    y = FakeYtDlp({YT: video()})
    r = run_fetch(y, tmp_path, rights="own", subs="es,en")
    (args,) = y.downloads
    assert args[args.index("--sub-langs") + 1] == "es,en" and "--write-auto-subs" in args
    assert args[args.index("--convert-subs") + 1] == "srt"
    assert sorted(Path(f).name for f in r["subtitles"]["files"]) == ["input.en.srt", "input.es.srt"]
    assert r["next"] == []


def test_subtitles_later_only_fetch_the_subtitles(tmp_path):
    y = FakeYtDlp({YT: video()})
    run_fetch(y, tmp_path, rights="own")
    r = run_fetch(y, tmp_path, subs="en")
    assert r["cached"] is True and "--skip-download" in y.downloads[-1]
    assert [Path(f).name for f in r["subtitles"]["files"]] == ["input.en.srt"]
    side = json.loads((tmp_path / "input.source.json").read_text(encoding="utf-8"))
    assert side["subtitles"]["files"] == r["subtitles"]["files"] and side["rights"] == "own"


# ---------- páginas con varios vídeos, listas y DRM ----------

def page(n: int, extractor="Generic") -> dict:
    return {"_type": "playlist", "extractor_key": extractor, "title": "Página con vídeos", "webpage_url": PAGE,
            "entries": [{"_type": "url", "url": f"https://svs.example.org/vis/{i}.mp4", "title": f"Vídeo {i}",
                         "duration": 30 * i} for i in range(1, n + 1)]}


def test_page_with_several_videos_asks_which(tmp_path):
    entry2 = video(id="2", extractor_key="Generic", title="Vídeo 2", webpage_url="https://svs.example.org/vis/2.mp4")
    y = FakeYtDlp({PAGE: page(3), "https://svs.example.org/vis/2.mp4": entry2})
    with pytest.raises(F.FetchStop) as e:
        run_fetch(y, tmp_path, url=PAGE, rights="own")
    p = e.value.payload
    assert p["needs"] == "pick" and [x["n"] for x in p["entries"]] == [1, 2, 3] and "--pick" in p["next"]
    assert [x["name"] for x in p["entries"]] == ["1.mp4", "2.mp4", "3.mp4"]
    assert y.downloads == []
    with pytest.raises(F.FetchStop) as e:                                          # elegido: ahora los derechos de ese
        run_fetch(y, tmp_path, url=PAGE, pick=2)
    assert e.value.payload["needs"] == "rights" and e.value.payload["source"]["title"] == "Vídeo 2"
    r = run_fetch(y, tmp_path, url=PAGE, pick=2, rights="own")
    assert y.downloads[-1][-1] == "https://svs.example.org/vis/2.mp4"
    assert r["picked"] == {"n": 2, "of": 3, "page": PAGE, "url": "https://svs.example.org/vis/2.mp4"} and r["url"] == PAGE


def test_pick_out_of_range_and_private_entries(tmp_path):
    y = FakeYtDlp({PAGE: page(3)})
    with pytest.raises(F.FetchError) as e:
        run_fetch(y, tmp_path, url=PAGE, pick=5)
    assert e.value.kind == "args"
    bad = page(2)
    bad["entries"][1]["url"] = "http://192.168.0.2/v.mp4"
    with pytest.raises(F.FetchError) as e:
        run_fetch(FakeYtDlp({PAGE: bad}), tmp_path, url=PAGE, pick=2)
    assert e.value.kind == "url"


def test_page_with_one_video_goes_straight_on(tmp_path):
    one = "https://svs.example.org/vis/1.mp4"
    y = FakeYtDlp({PAGE: page(1), one: video(id="1", extractor_key="Generic")})
    assert run_fetch(y, tmp_path, url=PAGE, rights="own")["downloaded"] is True
    assert y.downloads[-1][-1] == one


def test_playlists_and_channels_are_refused(tmp_path):
    y = FakeYtDlp({YT: page(5, extractor="YoutubeTab")})
    with pytest.raises(F.FetchError) as e:
        run_fetch(y, tmp_path, rights="own")
    assert e.value.kind == "playlist" and y.downloads == []


def test_drm_stops_without_looking_for_another_way(tmp_path):
    y = FakeYtDlp({YT: video(formats=[{"format_id": "1", "has_drm": True}])})
    with pytest.raises(F.FetchError) as e:
        run_fetch(y, tmp_path, rights="own")
    assert e.value.kind == "drm" and "DRM" in str(e.value) and y.downloads == []
    assert len(y.calls) == 1


# ---------- topes ----------

def test_duration_limit_asks_and_a_higher_limit_confirms(tmp_path):
    long = video(duration=4 * 3600, requested_formats=[{"filesize": 1_000_000}])
    y = FakeYtDlp({YT: long})
    with pytest.raises(F.FetchStop) as e:
        run_fetch(y, tmp_path, rights="own")
    p = e.value.payload
    assert p["needs"] == "limit" and p["limit"] == "duration" and "--max-duration 5h" in p["next"] and "--section" in p["next"]
    assert "--max-duration 1m;" in F.limit_stop("duration", 46, 10, video()).payload["next"]   # corto: en minutos
    assert y.downloads == []
    assert run_fetch(y, tmp_path, rights="own", max_duration="5h")["downloaded"] is True
    assert run_fetch(y, tmp_path, out=tmp_path / "t.mp4", section="0-600")["downloaded"] is True   # un tramo cabe


def test_size_limit_scales_with_the_section(tmp_path):
    big = video(duration=1000, requested_formats=[{"filesize": 3 * 1024 ** 3}])
    y = FakeYtDlp({YT: big})
    with pytest.raises(F.FetchStop) as e:
        run_fetch(y, tmp_path, rights="own")
    assert e.value.payload["limit"] == "size" and "--max-size 4GB" in e.value.payload["next"]
    assert run_fetch(y, tmp_path, rights="own", section="0-100")["downloaded"] is True     # ~300 MB
    r = run_fetch(y, tmp_path, out=tmp_path / "entero.mp4", max_size="4GB")
    assert r["downloaded"] is True
    assert y.downloads[-1][y.downloads[-1].index("--max-filesize") + 1] == str(4 * 1024 ** 3)


def test_ytdlp_max_filesize_abort_becomes_a_limit_question(tmp_path):
    y = FakeYtDlp({YT: video(requested_formats=[{}])}, write_file=False,
                  stdout="[download] File is larger than max-filesize (3000000000 bytes > 2147483648 bytes). Aborting.")
    with pytest.raises(F.FetchStop) as e:
        run_fetch(y, tmp_path, rights="own")
    assert e.value.payload["limit"] == "size"
    assert not (tmp_path / "input.source.json").exists()


# ---------- errores de la descarga ----------

def test_errors_come_out_translated(tmp_path):
    y = FakeYtDlp({YT: (1, "ERROR: [youtube] FkgVB19I6xw: Video unavailable. This video is private")})
    with pytest.raises(F.FetchError) as e:
        run_fetch(y, tmp_path, rights="own")
    assert e.value.kind in ("private", "unavailable") and "ERROR" not in str(e.value)
    y = FakeYtDlp({YT: video()}, fail_download=(1, "ERROR: unable to download video data: HTTP Error 403: Forbidden"))
    with pytest.raises(F.FetchError) as e:
        run_fetch(y, tmp_path, rights="own")
    assert e.value.kind == "forbidden" and "403" in str(e.value)
    assert not (tmp_path / ".frame28" / "fetch.json").exists()          # nada registrado si no se bajó


def test_missing_output_without_reason(tmp_path):
    y = FakeYtDlp({YT: video()}, write_file=False)
    with pytest.raises(F.FetchError) as e:
        run_fetch(y, tmp_path, rights="own")
    assert "--force" in str(e.value)


# ---------- la orden ----------

def test_cli_stop_prints_json_and_exits_3(monkeypatch):
    def stop(url, out, **kw):
        assert kw["rights"] is None                     # nunca hay respuesta por defecto
        raise F.rights_stop(url, video())
    monkeypatch.setattr(F, "fetch", stop)
    r = CliRunner().invoke(main, ["fetch", YT])
    assert r.exit_code == 3
    payload = json.loads(r.stdout[r.stdout.index("{"):])
    assert payload["needs"] == "rights" and payload["notice"]["es"]


def test_cli_passes_the_options_and_error_exits_1(monkeypatch):
    seen = {}

    def fake(url, out, **kw):
        seen.update(kw, url=url, out=out)
        raise F.FetchError("No hay ningún vídeo en ese enlace.", "notfound")
    monkeypatch.setattr(F, "fetch", fake)
    r = CliRunner().invoke(main, ["fetch", YT, "-o", "x.m4a", "--rights", "own", "--audio", "--subs", "es",
                                  "--section", "1:00-2:00", "--pick", "2", "--max-duration", "90m", "--max-size", "500MB",
                                  "--force"])
    assert r.exit_code == 1 and "No hay ningún vídeo" in r.output
    assert seen["out"] == "x.m4a" and seen["rights"] == "own" and seen["audio"] and seen["subs"] == "es"
    assert seen["section"] == "1:00-2:00" and seen["pick"] == 2 and seen["max_duration"] == "90m"
    assert seen["max_size"] == "500MB" and seen["force"]


def test_cli_rejects_other_rights_values():
    r = CliRunner().invoke(main, ["fetch", YT, "--rights", "yes"])
    assert r.exit_code == 2
