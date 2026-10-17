import html
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

import yt_dlp

HOSTS = {"x.com", "www.x.com", "twitter.com", "www.twitter.com", "mobile.twitter.com"}

PAGE = """<!doctype html><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>Video X</title>
<body style="font-family:sans-serif;max-width:600px;margin:1rem auto;padding:0 1rem">
<form><input name=url placeholder="Pega el enlace de X" value="{url}"
 style="width:100%;padding:.6rem;box-sizing:border-box" autofocus>
<button style="margin-top:.5rem;padding:.6rem 1rem">Ver video</button></form>{body}"""


def resolve(url):
    # Solo resuelve la URL directa del mp4; no descarga nada al disco.
    opts = {"quiet": True, "no_warnings": True, "format": "best[ext=mp4]/best"}
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
    return (info.get("entries") or [info])[0]["url"]


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        url = parse_qs(urlparse(self.path).query).get("url", [""])[0].strip()
        body = ""
        if url:
            try:
                if urlparse(url).hostname not in HOSTS:  # evita usar el server con otros sitios
                    raise ValueError("host no permitido")
                v = html.escape(resolve(url), quote=True)
                body = (
                    f'<video src="{v}" controls playsinline style="width:100%;margin-top:1rem"></video>'
                    f'<p><a href="{v}">Abrir video directo</a> (clic derecho o mantén presionado → guardar)</p>'
                )
            except Exception:
                body = "<p>No se pudo obtener el video. Revisa el enlace.</p>"
        out = PAGE.format(url=html.escape(url, quote=True), body=body).encode()
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
