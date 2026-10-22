import html
import os
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import parse_qs, quote, urlparse

import yt_dlp

HOSTS = {
    "x.com", "www.x.com", "twitter.com", "www.twitter.com", "mobile.twitter.com",
    "tiktok.com", "www.tiktok.com", "m.tiktok.com", "vm.tiktok.com", "vt.tiktok.com",
}
LOGO = Path(__file__).with_name("logo.jpg")
CACHE_TTL = 600  # el navegador pide el video por trozos; así no se re-resuelve cada vez
_cache = {}  # shortcut: sin límite de tamaño, basta para uso personal

# Estilo: sistema "warm parchment" de DESIGN.md en versión oscura, con la paleta turquesa de la imagen.
# Se usan @URL@, @AF@ y @BODY@ con replace porque el CSS lleva llaves y rompería .format().
PAGE = """<!doctype html><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<meta name=color-scheme content=dark><meta name=theme-color content="#091012">
<title>Video Downloader</title>
<link rel=icon href=/logo.jpg>
<style>
:root{color-scheme:dark;--canvas:#091012;--card:#0f191c;--nested:#152327;--line:#1b2d31;--edge:#2b474c;
--ink:#e4f2ef;--soft:#a6c3bf;--muted:#7a9a96;--accent:#3db8a4;
--serif:'Anthropic Serif',Charter,'Source Serif 4',Georgia,serif;
--sans:'Anthropic Sans',system-ui,-apple-system,'Segoe UI',Roboto,sans-serif;
--mono:ui-monospace,'SF Mono',Menlo,Consolas,monospace}
*{box-sizing:border-box}
body{margin:0;background:var(--canvas);color:var(--ink);font:400 14px/1.5 var(--sans)}
body::before{content:"";position:fixed;inset:0;pointer-events:none;opacity:.07;
background-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='160' height='160'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='.8' numOctaves='2' stitchTiles='stitch'/></filter><rect width='100%25' height='100%25' filter='url(%23n)'/></svg>")}
main{position:relative;max-width:640px;margin:0 auto;padding:24px 16px 48px}
.hero{position:relative;aspect-ratio:2/1;border-radius:24px;overflow:hidden;border:1px solid var(--line)}
.hero img{display:block;width:100%;height:100%;object-fit:cover;object-position:50% 40%;filter:brightness(.8) saturate(.9)}
.hero::after{content:"";position:absolute;inset:0;
background:repeating-linear-gradient(0deg,rgba(0,0,0,.22) 0 1px,transparent 1px 3px),linear-gradient(to top,var(--canvas),transparent 40%)}
h1{font:400 32px/1.2 var(--serif);margin:24px 0 8px}
.dot{display:inline-block;width:8px;height:8px;margin-left:8px;border-radius:50%;background:var(--accent)}
.sub{font-size:16px;color:var(--soft);margin:0 0 32px}
.card{background:var(--card);border:1px solid var(--line);border-radius:24px;padding:24px}
.chips{display:flex;gap:8px;margin:0 0 16px}
.chips span{padding:2px 10px;border-radius:8px;background:var(--nested);color:var(--soft);font:500 12px var(--mono)}
input{width:100%;padding:10px 12px;background:transparent;color:var(--ink);border:1px solid var(--edge);
border-radius:8px;font:inherit;font-size:16px}
input::placeholder{color:var(--muted)}
input:focus{outline:2px solid var(--accent);outline-offset:2px}
.row{display:flex;gap:8px;margin-top:20px}
.btn{display:inline-block;padding:8px 20px;border-radius:8px;border:1px solid transparent;background:var(--ink);
color:#071012;font:500 15px var(--sans);text-decoration:none;cursor:pointer;transition:background-color .2s ease}
.btn:hover{background:#cde4df}
.ghost{background:transparent;color:var(--ink);border-color:var(--edge)}
.ghost:hover{background:var(--nested)}
video{display:block;width:100%;max-height:70vh;margin-top:24px;border-radius:16px;background:#000}
.note{margin:24px 0 0;padding:16px;border-radius:16px;background:var(--nested);color:var(--soft)}
footer{margin-top:48px;text-align:center;color:var(--muted);font:400 12px var(--mono)}
footer .dot{width:6px;height:6px;margin:0 8px 1px 0}
</style>
<main>
<div class=hero><img src=/logo.jpg alt=""></div>
<h1>Video Downloader<span class=dot></span></h1>
<p class=sub>Pega un enlace de Twitter o TikTok, míralo aquí y guárdalo. Sin anuncios.</p>
<div class=card>
<div class=chips><span>twitter</span><span>tiktok</span></div>
<form><input name=url placeholder="Pega el enlace de Twitter o TikTok" value="@URL@" autocomplete=off inputmode=url@AF@>
<div class=row><button class=btn>Ver video</button></div></form>@BODY@
</div>
<footer><span class=dot></span>made by reuniclus</footer>
</main>"""


def resolve(url):
    """Devuelve (url_directa, headers) del mp4; no descarga nada al disco."""
    hit = _cache.get(url)
    if hit and hit[0] > time.time():
        return hit[1], hit[2]
    opts = {"quiet": True, "no_warnings": True, "format": "best[ext=mp4]/best"}
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
    info = (info.get("entries") or [info])[0]
    direct, headers = info["url"], info.get("http_headers") or {}
    _cache[url] = (time.time() + CACHE_TTL, direct, headers)
    return direct, headers


class Handler(BaseHTTPRequestHandler):
    def do_HEAD(self):
        # UptimeRobot puede sondear con HEAD; sin esto el servidor respondería 501 y el monitor marcaría caída.
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        q = parse_qs(parsed.query)
        url = q.get("url", [""])[0].strip()
        if parsed.path == "/v":
            return self.stream(url, "dl" in q)
        if parsed.path == "/logo.jpg":
            try:
                return self.send_body(LOGO.read_bytes(), "image/jpeg", "public, max-age=86400")
            except OSError:
                return self.send_error(404)
        body = ""
        if url:
            if urlparse(url).hostname in HOSTS:
                src = "/v?url=" + quote(url, safe="")
                body = (
                    f'<video src="{src}" controls playsinline></video>'
                    f'<div class=row><a class="btn ghost" href="{src}&dl=1">Descargar video</a></div>'
                )
            else:
                body = '<p class=note>Solo enlaces de Twitter o TikTok.</p>'
        # @URL@ va al final: así lo pegado por el usuario nunca se vuelve a procesar
        page = PAGE.replace("@BODY@", body).replace("@AF@", "" if url else " autofocus")
        self.send_body(page.replace("@URL@", html.escape(url, quote=True)).encode(), "text/html; charset=utf-8")

    def stream(self, url, download):
        # El navegador no puede pedir video.twimg.com directo (403); lo traemos nosotros.
        try:
            if urlparse(url).hostname not in HOSTS:  # evita usar el server con otros sitios
                raise ValueError("host no permitido")
            direct, headers = resolve(url)
            req = urllib.request.Request(direct, headers=dict(headers))
            if self.headers.get("Range"):  # necesario para poder avanzar/retroceder el video
                req.add_header("Range", self.headers["Range"])
            up = urllib.request.urlopen(req, timeout=30)
        except HTTPError as e:
            self.send_error(502, f"El sitio respondió {e.code}")
            return
        except Exception:
            self.send_error(502, "No se pudo obtener el video")
            return
        with up:
            self.send_response(up.status)
            for h in ("Content-Type", "Content-Length", "Content-Range", "Accept-Ranges"):
                if up.headers.get(h):
                    self.send_header(h, up.headers[h])
            if download:
                self.send_header("Content-Disposition", 'attachment; filename="video.mp4"')
            self.end_headers()
            try:
                while chunk := up.read(64 * 1024):
                    self.wfile.write(chunk)
            except (BrokenPipeError, ConnectionResetError):
                pass  # el navegador cerró la conexión (normal al saltar en el video)

    def send_body(self, data, content_type, cache=None):
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        if cache:
            self.send_header("Cache-Control", cache)
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format, *args):
        return


def start_web_server():
    port = int(os.environ.get("PORT", 10000))
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()