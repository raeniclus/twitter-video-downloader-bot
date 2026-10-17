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

PAGE = """<!doctype html><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>Video X</title>
<body style="font-family:sans-serif;max-width:600px;margin:1rem auto;padding:0 1rem">
<form><input name=url placeholder="Pega el enlace de X" value="{url}"
 style="width:100%;padding:.6rem;box-sizing:border-box" autofocus>
<button style="margin-top:.5rem;padding:.6rem 1rem">Ver video</button></form>{body}"""


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
                    f'<video src="{src}" controls playsinline style="width:100%;margin-top:1rem"></video>'
                    f'<p><a href="{src}&dl=1">Descargar video</a></p>'
                )
            else:
                body = "<p>Solo enlaces de x.com o twitter.com.</p>"
        self.send_html(PAGE.format(url=html.escape(url, quote=True), body=body))

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