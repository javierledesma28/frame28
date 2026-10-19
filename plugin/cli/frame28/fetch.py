"""fetch: trae un vídeo (o solo su audio) desde su enlace al ordenador de quien monta, con yt-dlp (F28-358, decisión A-312).

Orden de cada descarga, y por qué:
1. Enlace válido: solo http(s), sin usuario ni contraseña y sin hosts locales o privados (SSRF en el PC del cliente).
2. Metadatos con `-J`, sin descargar: título, duración, subtítulos, capítulos y el tamaño de los formatos elegidos.
3. Una página con varios vídeos (extractor genérico) no se baja a ciegas: se listan y se pregunta cuál (`--pick`). La prueba
   de Research bajó 108 MB de una página del NASA SVS sin saber qué vídeo era. Listas y canales no se bajan.
4. DRM: se para y no busca otra vía.
5. Derechos: la primera descarga de cada fuente exige `--rights own|licensed`, nunca por defecto; la respuesta queda en
   `<out>.source.json` y en el manifiesto del proyecto con la versión del aviso aceptado.
6. Topes de duración y tamaño (3 h y 2 GB por defecto); pasarlos es repetir la orden con un tope mayor.
7. Caché del proyecto por (fuente, modo, tramo): «ya lo tienes» en vez de volver a bajarlo; `--force` lo repite.

Cuando falta una respuesta de la persona no se descarga nada: `FetchStop` lleva lo que hay que preguntarle y cómo repetir la
orden (el CLI lo imprime en JSON y sale con código 3). Los errores de yt-dlp salen traducidos, con el siguiente paso.
"""
from __future__ import annotations

import ipaddress
import json
import re
import socket
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

from .env import find_tool, note, run

# Cota inferior de yt-dlp (F28-91): las webs cambian y un yt-dlp viejo falla con errores que no dicen que es viejo. Se sube a
# la última estable en cada release (release-check lo comprueba).
YTDLP_MIN = "2026.8.19"

# Aviso de derechos de Seguridad (informes/seguridad/2026-10-19-F28-287-descarga-legal.md, texto b). Si cambia el texto,
# cambia la versión: las confirmaciones guardadas con otra versión ya no valen y se vuelve a preguntar.
NOTICE_VERSION = "2026-10-19"
NOTICE = {
    "es": ("Antes de descargar: ¿este vídeo es tuyo (de tu marca) o tienes permiso de su titular para editarlo y "
           "publicarlo? Se descarga en tu ordenador y guardamos tu respuesta con el proyecto. Montarlo no te da derechos "
           "que no tengas. Algunas plataformas, como YouTube, solo permiten descargar con su propia herramienta (YouTube "
           "Studio, para tus vídeos); cumplir sus condiciones te corresponde a ti."),
    "en": ("Before downloading: is this video yours (your brand's), or do you have the rights holder's permission to edit "
           "and publish it? It downloads to your computer and we save your answer with the project. Editing it doesn't "
           "give you rights you don't have. Some platforms, such as YouTube, only allow downloads through their own tools "
           "(YouTube Studio, for your own videos); complying with their terms is up to you."),
}
NOTICE_OPTIONS = {
    "es": [{"label": "Es mío", "rights": "own"}, {"label": "Tengo permiso del titular", "rights": "licensed"},
           {"label": "Cancelar", "rights": None}],
    "en": [{"label": "It's mine", "rights": "own"}, {"label": "I have the rights holder's permission", "rights": "licensed"},
           {"label": "Cancel", "rights": None}],
}
NOTICE_SHORT = {
    "es": "Solo vídeos tuyos o con permiso de su titular; cumplir las condiciones de la plataforma te corresponde a ti.",
    "en": "Only videos you own or have the rights holder's permission to use; complying with the platform's terms is up to you.",
}
RIGHTS = ("own", "licensed")

MAX_DURATION_S = 3 * 3600      # topes por defecto, como el mercado (OpusClip 10 h, Klap 2 h, Munch 4 h; 2–15 GB)
MAX_SIZE_B = 2 * 1024 ** 3
LOCAL_SUFFIXES = (".localhost", ".local", ".internal", ".lan", ".home.arpa")
MANIFEST = Path(".frame28") / "fetch.json"


class FetchError(Exception):
    """Error con el mensaje para la persona (en nuestro idioma y con el siguiente paso)."""

    def __init__(self, message: str, kind: str = "other"):
        super().__init__(message)
        self.kind = kind


class FetchStop(Exception):
    """Falta una respuesta de la persona: `payload` dice qué preguntar y cómo repetir la orden. No se ha descargado nada."""

    def __init__(self, payload: dict):
        super().__init__(payload.get("message", ""))
        self.payload = payload


# ---------- enlace ----------

def _blocked_ip(ip: ipaddress._BaseAddress) -> bool:
    mapped = getattr(ip, "ipv4_mapped", None)
    if mapped:
        ip = mapped
    return not ip.is_global or ip.is_multicast


def check_url(url: str, resolve=socket.getaddrinfo) -> str:
    """El enlace limpio, o FetchError si no es http(s), lleva credenciales o apunta a un host local o privado (también si el
    nombre resuelve a uno: `localtest.me` → 127.0.0.1). yt-dlp vuelve a resolver el nombre al descargar; esto cierra lo que
    se puede cerrar desde aquí."""
    url = (url or "").strip()
    if any(ord(c) < 32 for c in url):
        raise FetchError("El enlace tiene caracteres de control: cópialo de nuevo desde el navegador.", "url")
    p = urllib.parse.urlsplit(url)
    if p.scheme.lower() not in ("http", "https"):
        raise FetchError("Solo se descargan enlaces http(s) de una página o plataforma de vídeo. Si tienes el archivo, "
                         "pásamelo directamente.", "url")
    if "@" in p.netloc:
        raise FetchError("El enlace lleva usuario o contraseña: Frame28 no los usa. Pásame el enlace sin ellos.", "url")
    host = (p.hostname or "").rstrip(".").lower()
    if not host:
        raise FetchError("Al enlace le falta el servidor: cópialo de nuevo desde el navegador.", "url")
    private = FetchError(f"El enlace apunta a un equipo local o de una red privada ({host}): solo se descargan vídeos "
                         "publicados en internet. Si el archivo está en tu ordenador, pásame la ruta.", "url")
    if host == "localhost" or host.endswith(LOCAL_SUFFIXES):
        raise private
    try:
        ips = [ipaddress.ip_address(host)]
    except ValueError:
        try:
            ips = [ipaddress.ip_address(a[4][0].split("%")[0]) for a in resolve(host, None)]
        except (socket.gaierror, UnicodeError, OSError) as e:
            raise FetchError(f"No encuentro el servidor del enlace ({host}): comprueba que está bien escrito y que hay "
                             "conexión.", "network") from e
    if any(_blocked_ip(ip) for ip in ips):
        raise private
    return url


# ---------- yt-dlp ----------

def _date_version(v: str) -> tuple[int, ...]:
    return tuple(int(x) for x in re.findall(r"\d+", v)[:4])


def ytdlp_cmd(path_ytdlp: str | None, path_version: str | None, uv: str, channel: str = "stable") -> list[str]:
    """yt-dlp del PATH solo si no es anterior a YTDLP_MIN; si no, el de uv (`uv tool run`, entorno efímero que no instala
    nada) con la cota inferior y el extra `default` (trae yt-dlp-ejs, que resuelve el reto de JavaScript de YouTube). El
    canal nightly son las prerreleases que yt-dlp publica en PyPI: arreglan YouTube semanas antes que la estable."""
    if channel != "nightly" and path_ytdlp and path_version and _date_version(path_version) >= _date_version(YTDLP_MIN):
        return [path_ytdlp]
    pre = ["--prerelease", "allow"] if channel == "nightly" else []
    return [uv, "tool", "run", *pre, "--python", "3.12", "--from", f"yt-dlp[default]>={YTDLP_MIN}", "yt-dlp"]


def js_runtime_args(deno: str | None, node: str | None, node_version: str = "") -> list[str]:
    """yt-dlp necesita un motor de JavaScript para YouTube desde la 2025.11.12: Deno lo usa solo; Node (22 o superior) hay
    que pedirlo. Sin ninguno, YouTube se degrada o falla."""
    from .doctor import NODE_MIN, node_major
    if deno:
        return []
    if node and node_major(node_version) >= NODE_MIN:
        return ["--js-runtimes", "node"]
    return []


# Errores de yt-dlp → (tipo, mensaje). El orden importa: «not a bot» también sugiere --cookies y no es un vídeo privado.
EXPLAIN = [
    ("drm", r"\bDRM\b", "Este vídeo tiene protección anticopia (DRM): Frame28 no lo descarga ni busca otra vía. Pide el "
                        "archivo original a su titular y pásamelo."),
    ("blocked", r"not a bot|HTTP Error 429|Too Many Requests|rate[- ]limit",
     "La plataforma está frenando las descargas desde tu red ahora mismo. Prueba de nuevo en unos minutos; si sigue, "
     "descarga el archivo desde la propia plataforma (YouTube Studio, si es tu canal de YouTube) y pásame el fichero."),
    ("forbidden", r"HTTP Error 403",
     "La plataforma rechazó la descarga (HTTP 403). Suele arreglarse con una versión más nueva de yt-dlp, que ya se probó; "
     "si sigue, prueba en unos minutos o descarga el archivo desde la propia plataforma y pásamelo."),
    ("private", r"private video|video is private|confirm your age|login required|\blog ?in\b|requires authentication|"
                r"members[- ]only|join this channel|--cookies|cookies-from-browser",
     "Este vídeo es privado o exige iniciar sesión en la plataforma, y Frame28 no usa tu sesión. Si es tuyo, descárgalo "
     "desde la propia plataforma (YouTube Studio en YouTube) y pásame el fichero."),
    ("js", r"javascript runtime|js runtime|js-runtimes|challenge solving|\bejs\b",
     "Falta un motor de JavaScript para YouTube (Deno, o Node 22 o superior). Instala Node desde https://nodejs.org o "
     "repite el instalador de Frame28, y vuelve a probar."),
    ("live", r"premieres in|live event will begin|is live|is_live|currently live",
     "Es una emisión en directo o un estreno que aún no ha terminado: espera a que acabe y vuelve a probar."),
    ("unavailable", r"video (is )?unavailable|has been removed|no longer available|available in your country|geo.?restrict",
     "El vídeo no está disponible: se borró, es privado o está bloqueado en tu país."),
    ("notfound", r"unsupported url|HTTP Error 404|no video could be found|there'?s no video|is not a valid url",
     "No hay ningún vídeo en ese enlace, o la plataforma no está soportada. Comprueba el enlace; si tienes el archivo, "
     "pásamelo directamente."),
    ("broken", r"requested format is not available|no video formats found|unable to extract|signature extraction|"
               r"nsig extraction",
     "yt-dlp no entiende ahora mismo esa página (la plataforma cambió algo); ya se probó con la versión más nueva. Prueba "
     "más tarde o pásame el archivo."),
    ("network", r"unable to download webpage|getaddrinfo|name or service not known|timed out|connection reset|"
                r"failed to resolve|network is unreachable|urlopen error",
     "No hay conexión con la plataforma: comprueba la red y vuelve a probar."),
]
RETRY_NIGHTLY = ("forbidden", "broken", "js")   # lo que una yt-dlp más nueva suele arreglar
NO_JS = r"no supported javascript runtime|javascript runtime could not|without a js runtime"


def explain(stderr: str) -> tuple[str, str]:
    """(tipo, mensaje para la persona) a partir de la salida de yt-dlp. Nunca «report this issue» ni «yt-dlp -U»: son
    instrucciones que el cliente no puede seguir desde el plugin."""
    errors = [ln for ln in (stderr or "").splitlines() if "ERROR" in ln] or (stderr or "").strip().splitlines()[-1:]
    text = "\n".join(errors)
    for kind, rx, msg in EXPLAIN:
        if re.search(rx, text, re.I):
            if kind in ("forbidden", "broken") and re.search(NO_JS, stderr or "", re.I):
                break   # el ERROR es la consecuencia; la causa está en un WARNING: sin motor de JavaScript
            return kind, msg
    if re.search(NO_JS, stderr or "", re.I):
        return next((k, m) for k, _, m in EXPLAIN if k == "js")
    last = re.sub(r"^ERROR:\s*", "", errors[-1] if errors else "sin salida").strip()
    last = re.split(r";\s*please report|\s*Confirm you are on the latest|\s*please report this issue", last, flags=re.I)[0]
    return "other", f"yt-dlp no pudo con ese enlace: {last[:200]}. Si tienes el archivo, pásamelo directamente."


class YtDlp:
    """yt-dlp con su motor de JavaScript y ffmpeg. Si la estable falla con algo que suele arreglar una versión más nueva,
    repite una vez con la nightly (FRAME28_YTDLP_CHANNEL=nightly la usa siempre)."""

    def __init__(self, channel: str | None = None):
        import os
        from .env import ffmpeg
        self.channel = (channel or os.environ.get("FRAME28_YTDLP_CHANNEL") or "stable").lower()
        path = find_tool("yt-dlp", "FRAME28_YTDLP")
        self.path, self.version = path, (run([path, "--version"]).stdout.strip() if path else None)
        self.uv = find_tool("uv") or "uv"
        node = find_tool("node")
        node_ver = run([node, "--version"]).stdout.strip() if node else ""
        self.common = (["--no-progress", "--ffmpeg-location", str(Path(ffmpeg()).parent)]
                       + js_runtime_args(find_tool("deno"), node, node_ver))
        self.retried = False

    def base(self) -> list[str]:
        return ytdlp_cmd(self.path, self.version, self.uv, self.channel)

    def call(self, args: list[str]):
        r = run(self.base() + self.common + args)
        if r.returncode != 0 and self.channel != "nightly":
            kind, _ = explain(r.stderr or r.stdout)
            if kind in RETRY_NIGHTLY:
                note("  La versión estable de yt-dlp falló con esta página; pruebo con la más nueva (nightly).")
                self.channel, self.retried = "nightly", True
                r = run(self.base() + self.common + args)
        return r


# ---------- piezas ----------

def parse_seconds(text: str) -> float:
    """«90», «1:30», «1:02:03», «2.5» → segundos."""
    parts = str(text).strip().split(":")
    try:
        nums = [float(p) for p in parts]
    except ValueError as e:
        raise FetchError(f"No entiendo el tiempo «{text}»: usa segundos (90) o mm:ss (1:30).", "args") from e
    s = 0.0
    for n in nums:
        s = s * 60 + n
    return s


def parse_section(text: str | None) -> tuple[float, float] | None:
    if not text:
        return None
    m = re.fullmatch(r"\s*([\d:.]+)\s*-\s*([\d:.]+)\s*", text)
    if not m:
        raise FetchError(f"El tramo «{text}» no se entiende: escríbelo como inicio-fin, p. ej. 1:20-2:05.", "args")
    a, b = parse_seconds(m.group(1)), parse_seconds(m.group(2))
    if b <= a:
        raise FetchError(f"El tramo «{text}» acaba antes de empezar.", "args")
    return a, b


def parse_duration(text: str | float | int) -> float:
    """«3h», «90m», «600», «600s» → segundos."""
    m = re.fullmatch(r"\s*([\d.]+)\s*(h|m|min|s)?\s*", str(text).lower())
    if not m:
        raise FetchError(f"No entiendo el tope de duración «{text}»: usa 3h, 90m o 600.", "args")
    return float(m.group(1)) * {"h": 3600, "m": 60, "min": 60}.get(m.group(2) or "s", 1)


def parse_size(text: str | float | int) -> int:
    """«2GB», «500MB», «500M», «1500000» (bytes) → bytes."""
    m = re.fullmatch(r"\s*([\d.]+)\s*(gb|g|mb|m|kb|k|b)?\s*", str(text).lower())
    if not m:
        raise FetchError(f"No entiendo el tope de tamaño «{text}»: usa 2GB o 500MB.", "args")
    unit = (m.group(2) or "b")[0]
    return int(float(m.group(1)) * {"g": 1024 ** 3, "m": 1024 ** 2, "k": 1024, "b": 1}[unit])


def human_size(n: float | None) -> str:
    if not n:
        return "?"
    return f"{n / 1024 ** 3:.1f} GB" if n >= 1024 ** 3 else f"{n / 1024 ** 2:.0f} MB"


def human_duration(s: float | None) -> str:
    if not s:
        return "?"
    s = int(round(s))
    return f"{s // 3600}:{s % 3600 // 60:02d}:{s % 60:02d}" if s >= 3600 else f"{s // 60}:{s % 60:02d}"


def has_drm(info: dict) -> bool:
    return bool(info.get("_has_drm")) or any(f.get("has_drm") for f in info.get("formats") or [])


def estimate_size(info: dict) -> float | None:
    """Bytes de los formatos que se van a bajar (el `-J` va con el mismo `-f`), o por bitrate × duración si la plataforma
    no da tamaños; None si no hay forma de saberlo."""
    parts = info.get("requested_formats") or [info]
    total = 0.0
    for f in parts:
        size = f.get("filesize") or f.get("filesize_approx")
        if not size and f.get("tbr") and info.get("duration"):
            size = float(f["tbr"]) * 1000 / 8 * float(info["duration"])
        if not size:
            return None
        total += float(size)
    return total


def source_key(info: dict) -> str:
    return f"{info.get('extractor_key') or info.get('extractor') or 'web'}:{info.get('id') or info.get('webpage_url')}"


def subtitle_langs(info: dict) -> dict:
    """Los subtítulos manuales y, de los automáticos, el del idioma en que se habla (YouTube lo marca `<idioma>-orig`); el
    resto son más de cien traducciones automáticas de ese mismo texto y solo se cuentan."""
    auto = list(info.get("automatic_captions") or {})
    orig = sorted(k[:-len("-orig")] for k in auto if k.endswith("-orig"))
    translated = sorted(k for k in auto if not k.endswith("-orig"))
    return {"manual": sorted((info.get("subtitles") or {}).keys()), "auto": orig or translated[:40],
            "auto_translated": len(translated) if orig else 0}


def chapters(info: dict) -> list[dict]:
    return [{"start": c.get("start_time"), "end": c.get("end_time"), "title": c.get("title")}
            for c in info.get("chapters") or []]


def summary(info: dict) -> dict:
    """Lo que la persona necesita para decidir: qué es, de quién, cuánto dura y qué trae."""
    return {"title": info.get("title"), "uploader": info.get("uploader") or info.get("channel"),
            "duration": info.get("duration"), "upload_date": info.get("upload_date"), "language": info.get("language"),
            "webpage_url": info.get("webpage_url") or info.get("original_url"),
            "extractor": info.get("extractor_key") or info.get("extractor"), "id": info.get("id"),
            "subtitles": subtitle_langs(info), "chapters": chapters(info), "estimated_size": estimate_size(info)}


def load_manifest(root: Path) -> dict:
    p = root / MANIFEST
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            data.setdefault("sources", {}); data.setdefault("files", {})
            return data
    except (OSError, ValueError):
        pass
    return {"version": 1, "sources": {}, "files": {}}


def save_manifest(root: Path, data: dict) -> None:
    p = root / MANIFEST
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def rights_stop(url: str, info: dict) -> FetchStop:
    return FetchStop({
        "ok": False, "needs": "rights", "downloaded": False,
        "message": "Antes de descargar hay que confirmar los derechos: enseña `notice` a la persona con sus tres respuestas.",
        "notice": NOTICE, "options": NOTICE_OPTIONS, "notice_version": NOTICE_VERSION, "source": summary(info),
        "next": ("Si responde «Es mío», repite la orden con --rights own; si responde «Tengo permiso del titular», con "
                 "--rights licensed. Si cancela o no responde, no descargues. Nunca elijas la respuesta por ella."),
    })


def pick_stop(url: str, info: dict, entries: list[dict]) -> FetchStop:
    # el nombre del fichero ayuda cuando la página titula todos igual («Página (1)», «Página (2)»…): pasó en el NASA SVS
    shown = [{"n": i + 1, "title": e.get("title"), "duration": e.get("duration"),
              "name": urllib.parse.unquote(Path(urllib.parse.urlsplit(e.get("url") or "").path).name) or None,
              "url": e.get("url") or e.get("webpage_url")} for i, e in enumerate(entries[:30])]
    return FetchStop({
        "ok": False, "needs": "pick", "downloaded": False,
        "message": f"Esta página tiene {len(entries)} vídeos: pregunta a la persona cuál quiere; no se baja ninguno a ciegas.",
        "page": info.get("title") or url, "entries": shown,
        "next": "Repite la orden con --pick N (el número de la lista que elija).",
    })


def limit_stop(what: str, value: float, limit: float, info: dict) -> FetchStop:
    if what == "duration":
        msg = (f"El vídeo dura {human_duration(value)} y el tope es {human_duration(limit)}. Pregunta a la persona si lo "
               "quiere entero o solo un tramo.")
        cap = f"{int(value // 3600) + 1}h" if value >= 3600 else f"{int(value // 60) + 1}m"
        nxt = (f"Para bajarlo entero, repite con --max-duration {cap}; para un tramo, con --section inicio-fin "
               "(p. ej. 1:20-2:05).")
    else:
        msg = (f"El vídeo ocupará unos {human_size(value)} y el tope es {human_size(limit)}. Pregunta a la persona si lo "
               "quiere igualmente, a menos resolución o solo un tramo.")
        nxt = (f"Repite con --max-size {int(value / 1024 ** 3) + 1}GB para confirmarlo, con --max-height 720 para que ocupe "
               "menos o con --section inicio-fin.")
    return FetchStop({"ok": False, "needs": "limit", "limit": what, "downloaded": False, "message": msg,
                      "source": summary(info), "next": nxt})


# ---------- la orden ----------

def fetch(url: str, out: str | Path | None = None, *, rights: str | None = None, audio: bool = False,
          subs: str | None = None, section: str | None = None, pick: int | None = None,
          max_duration: str | float = MAX_DURATION_S, max_size: str | int = MAX_SIZE_B, max_height: int = 1080,
          force: bool = False, info_only: bool = False, ytdlp: YtDlp | None = None, resolve=socket.getaddrinfo) -> dict:
    """Descarga `url` (vídeo MP4 ≤ max_height, o solo audio M4A) en `out` y deja `<out>.source.json`. Ver el docstring del
    módulo para el orden y los FetchStop."""
    url = check_url(url, resolve)
    if rights is not None and rights not in RIGHTS:
        raise FetchError(f"--rights tiene que ser own (es tuyo) o licensed (tienes permiso del titular), no «{rights}».", "args")
    sec = parse_section(section)
    max_d, max_b = parse_duration(max_duration), parse_size(max_size)
    out = Path(out or ("input.m4a" if audio else "input.mp4")).with_suffix(".m4a" if audio else ".mp4")
    root = out.parent
    mode = "audio" if audio else f"video{max_height}"
    fmt = "ba[ext=m4a]/ba" if audio else f"bv*[height<={max_height}][ext=mp4]+ba[ext=m4a]/b[ext=mp4]/b"
    y = ytdlp or YtDlp()

    def probe(target: str) -> dict:
        r = y.call(["-J", "--flat-playlist", "--no-playlist", "-f", fmt, target])
        if r.returncode != 0:
            kind, msg = explain(r.stderr or r.stdout)
            raise FetchError(msg, kind)
        try:
            return json.loads((r.stdout or "").strip().splitlines()[-1])
        except (ValueError, IndexError) as e:
            raise FetchError("yt-dlp no devolvió los datos del vídeo. Prueba de nuevo; si sigue, pásame el archivo.") from e

    info, target, picked = probe(url), url, None
    if info.get("_type") in ("playlist", "multi_video"):
        entries = [e for e in info.get("entries") or [] if e]
        generic = (info.get("extractor_key") or info.get("extractor") or "").lower() == "generic"
        if info.get("_type") == "playlist" and not generic:
            raise FetchError("El enlace es una lista o un canal, no un vídeo: pásame el enlace del vídeo concreto. Bajar "
                             "listas o canales enteros no está disponible.", "playlist")
        if not entries:
            raise FetchError(explain("ERROR: no video could be found")[1], "notfound")
        if len(entries) > 1 and pick is None:
            raise pick_stop(url, info, entries)
        n = pick or 1
        if not 1 <= n <= len(entries):
            raise FetchError(f"--pick {n} no está en la lista: la página tiene {len(entries)} vídeos.", "args")
        entry = entries[n - 1]
        target = check_url(entry.get("url") or entry.get("webpage_url") or "", resolve)
        picked = {"n": n, "of": len(entries), "page": url, "url": target}
        info = probe(target)
        if info.get("_type") in ("playlist", "multi_video"):
            raise FetchError("Ese elemento de la página es otra lista: pásame el enlace del vídeo concreto.", "playlist")
    if has_drm(info):
        raise FetchError(EXPLAIN[0][2], "drm")
    if info_only:
        return {"ok": True, "downloaded": False, "url": url, "picked": picked, "source": summary(info),
                "notice_short": NOTICE_SHORT}

    key = source_key(info)
    manifest = load_manifest(root)
    known = manifest["sources"].get(key)
    if rights is None:
        if not known or known.get("notice_version") != NOTICE_VERSION:
            raise rights_stop(url, info)
        consent = known
    else:
        consent = {"rights": rights, "confirmed_at": now(), "notice_version": NOTICE_VERSION}

    duration = info.get("duration")
    span = (sec[1] - sec[0]) if sec else duration
    if span and span > max_d:
        raise limit_stop("duration", span, max_d, info)
    size = estimate_size(info)
    if size and sec and duration:
        size = size * min(1.0, (sec[1] - sec[0]) / duration)
    if size and size > max_b:
        raise limit_stop("size", size, max_b, info)

    cache_key = f"{key}|{mode}|{sec[0]:g}-{sec[1]:g}" if sec else f"{key}|{mode}"
    hit = manifest["files"].get(cache_key)
    if hit and not force and Path(hit.get("file", "")).exists():
        have = Path(hit["file"])
        side_path = have.with_suffix(".source.json")
        side = json.loads(side_path.read_text(encoding="utf-8")) if side_path.exists() else {"file": hit["file"]}
        if subs:   # el vídeo ya está: solo faltan sus subtítulos
            r = y.call(["--no-playlist", "--skip-download", "-o", str(have.with_suffix("")) + ".%(ext)s", "--write-subs",
                        "--write-auto-subs", "--sub-langs", subs, "--convert-subs", "srt", target])
            if r.returncode != 0:
                kind, msg = explain(r.stderr or r.stdout)
                raise FetchError(msg, kind)
            side["subtitles"] = {**subtitle_langs(info), "files": sorted(str(x) for x in have.parent.glob(have.stem + ".*.srt"))}
            side_path.write_text(json.dumps(side, indent=1, ensure_ascii=False), encoding="utf-8")
        if rights is not None:   # una confirmación nueva queda registrada aunque no se descargue nada
            manifest["sources"][key] = {**consent, "url": url, "title": info.get("title")}
            save_manifest(root, manifest)
        return {**side, "ok": True, "downloaded": False, "cached": True,
                "message": f"Ya lo tienes en {hit['file']} (descargado el {hit.get('fetched_at', '?')}); --force lo repite."}

    out.parent.mkdir(parents=True, exist_ok=True)
    # --force-overwrites siempre: lo que ya está bajado lo decide la caché; yt-dlp solo mira el nombre y daba por bueno el
    # input.mp4 de otro vídeo
    args = ["--no-playlist", "-f", fmt, "-o", str(out.with_suffix("")) + ".%(ext)s", "--max-filesize", str(max_b),
            "--force-overwrites"]
    args += ["-x", "--audio-format", "m4a"] if audio else ["--merge-output-format", "mp4", "--remux-video", "mp4"]
    if sec:
        args += ["--download-sections", f"*{sec[0]:g}-{sec[1]:g}"]
    if subs:
        args += ["--write-subs", "--write-auto-subs", "--sub-langs", subs, "--convert-subs", "srt"]
    known = ", ".join(x for x in (human_duration(span) if span else "", f"unos {human_size(size)}" if size else "") if x)
    note(f"  Descargando «{info.get('title') or target}»" + (f" ({known})" if known else "") + ": tarda según la red.")
    r = y.call(args + [target])
    if r.returncode != 0:
        kind, msg = explain(r.stderr or r.stdout)
        raise FetchError(msg, kind)
    if not out.exists():
        if re.search(r"max-filesize|larger than max", (r.stdout or "") + (r.stderr or ""), re.I):
            raise limit_stop("size", max(size or 0, max_b + 1), max_b, info)
        raise FetchError(f"yt-dlp terminó sin dejar {out.name}. Prueba de nuevo con --force; si sigue, pásame el archivo.")

    sub_files = sorted(str(p) for p in out.parent.glob(out.stem + ".*.srt")) if subs else []
    side = {"url": url, "title": info.get("title"), "duration": duration, "uploader": info.get("uploader") or info.get("channel"),
            "upload_date": info.get("upload_date"), "language": info.get("language"), "file": str(out),
            "extractor": info.get("extractor_key"),
            "id": info.get("id"), "mode": "audio" if audio else "video", "section": list(sec) if sec else None,
            "picked": picked, "bytes": out.stat().st_size, "chapters": chapters(info),
            "subtitles": {**subtitle_langs(info), "files": sub_files},
            "rights": consent["rights"], "confirmed_at": consent["confirmed_at"], "notice_version": consent["notice_version"],
            "ytdlp_channel": y.channel}
    out.with_suffix(".source.json").write_text(json.dumps(side, indent=1, ensure_ascii=False), encoding="utf-8")
    manifest["sources"][key] = {**consent, "url": url, "title": info.get("title")}
    manifest["files"][cache_key] = {"file": str(out), "bytes": side["bytes"], "fetched_at": now(),
                                    "source": key}
    save_manifest(root, manifest)
    nxt = []
    if not subs and (side["subtitles"]["manual"] or side["subtitles"]["auto"]):
        nxt.append("El vídeo trae subtítulos propios (`subtitles`): ofrécelos como transcripción inmediata o para "
                   "comprobar la nuestra; se bajan repitiendo con --subs <idioma>.")
    return {**side, "ok": True, "downloaded": True, "cached": False, "next": nxt}
