import html
import os
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.parse import parse_qs, quote, urlparse

import yt_dlp

HOSTS = {"x.com", "www.x.com", "twitter.com", "www.twitter.com", "mobile.twitter.com"}
CACHE_TTL = 600  # el navegador pide el video por trozos; así no se re-resuelve cada vez
_cache = {}  # shortcut: sin límite de tamaño, basta para uso personal

# Estilo: versión oscura del sistema "warm parchment" de DESIGN.md (tinta clara sobre carbón cálido, arcilla solo como detalle).
# Se usan @URL@, @AF@ y @BODY@ con replace porque el CSS lleva llaves y rompería .format().
PAGE = """<!doctype html><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<meta name=color-scheme content=dark><meta name=theme-color content="#1c1c1a">
<title>Videos de X</title>
<style>
:root{color-scheme:dark;--canvas:#1c1c1a;--card:#262624;--nested:#30302e;--line:#373734;--edge:#4a4a46;
--ink:#f8f8f6;--soft:#b7b7b5;--muted:#9c9a92;--clay:#d97757;
--serif:'Anthropic Serif',Charter,'Source Serif 4',Georgia,serif;
--sans:'Anthropic Sans',system-ui,-apple-system,'Segoe UI',Roboto,sans-serif}
*{box-sizing:border-box}
body{margin:0;background:var(--canvas);color:var(--ink);font:400 14px/1.5 var(--sans)}
main{max-width:640px;margin:0 auto;padding:48px 16px 64px}
h1{font:400 30px/1.2 var(--serif);margin:0 0 8px}
.dot{display:inline-block;width:8px;height:8px;margin-left:8px;border-radius:50%;background:var(--clay)}
.sub{font-size:16px;color:var(--soft);margin:0 0 32px}
.card{background:var(--card);border:1px solid var(--line);border-radius:24px;padding:24px}
input{width:100%;padding:10px 12px;background:transparent;color:var(--ink);border:1px solid var(--edge);
border-radius:8px;font:inherit;font-size:16px}
input::placeholder{color:var(--muted)}
input:focus{outline:2px solid var(--muted);outline-offset:2px}
.row{display:flex;gap:8px;margin-top:8px}
.btn{display:inline-block;padding:8px 20px;border-radius:8px;border:1px solid transparent;background:var(--ink);
color:#121212;font:500 15px var(--sans);text-decoration:none;cursor:pointer;transition:background-color .2s ease}
.btn:hover{background:#e7e6e1}
.ghost{background:transparent;color:var(--ink);border-color:var(--edge)}
.ghost:hover{background:var(--nested)}
video{display:block;width:100%;max-height:70vh;margin-top:24px;border-radius:16px;background:#000}
.note{margin:24px 0 0;padding:16px;border-radius:16px;background:var(--nested);color:var(--soft)}
</style>
<main>
<h1>Videos de X<span class=dot></span></h1>
<p class=sub>Pega el enlace, míralo aquí y guárdalo. Sin anuncios.</p>
<div class=card>
<form><input name=url placeholder="Pega el enlace de X" value="@URL@" autocomplete=off inputmode=url@AF@>
<div class=row><button class=btn>Ver video</button></div></form>@BODY@
</div>
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
    def do_GET(self):
        parsed = urlparse(self.path)
        q = parse_qs(parsed.query)
        url = q.get("url", [""])[0].strip()
        if parsed.path == "/v":
            return self.stream(url, "dl" in q)
        body = ""
        if url:
            if urlparse(url).hostname in HOSTS:
                src = "/v?url=" + quote(url, safe="")
                body = (
                    f'<video src="{src}" controls playsinline></video>'
                    f'<div class=row style="margin-top:16px"><a class="btn ghost" href="{src}&dl=1">Descargar video</a></div>'
                )
            else:
                body = '<p class=note>Solo enlaces de x.com o twitter.com.</p>'
        # @URL@ va al final: así lo pegado por el usuario nunca se vuelve a procesar
        page = PAGE.replace("@BODY@", body).replace("@AF@", "" if url else " autofocus")
        self.send_html(page.replace("@URL@", html.escape(url, quote=True)))

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
            self.send_error(502, f"X respondió {e.code}")
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

    def send_html(self, text):
        out = text.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(out)))
        self.end_headers()
        self.wfile.write(out)

    def log_message(self, format, *args):
        return


def start_web_server():
    port = int(os.environ.get("PORT", 10000))
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()