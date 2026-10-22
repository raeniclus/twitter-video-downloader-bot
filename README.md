# Video Downloader

Herramienta personal para descargar videos de Twitter (X) y TikTok sin anuncios. Incluye dos formas de uso que comparten el mismo código: un bot de Telegram y una página web.

## Funcionalidades

- **Bot de Telegram:** envías un enlace de Twitter (X) y recibes el video como archivo `.mp4`. Por ahora no admite TikTok.
- **Página web:** pegas un enlace de Twitter (X) o TikTok, el video se reproduce en el navegador y puedes guardarlo con un botón de descarga. Está pensada para usarse desde el teléfono y no requiere instalar nada.

## Cómo funciona

`bot.py` inicia el bot de Telegram (con polling) y, en un hilo aparte, el servidor web definido en `web.py`. La extracción del video la hace [yt-dlp](https://github.com/yt-dlp/yt-dlp).

- El bot descarga el video a la carpeta temporal `downloads/`, lo envía por Telegram y borra el archivo al terminar.
- La página web no guarda nada en disco. Obtiene la dirección directa del video y la retransmite desde el servidor, porque X rechaza (error 403) las peticiones directas desde el navegador a `video.twimg.com`.
- El servidor web solo acepta enlaces de `x.com`, `twitter.com` y `tiktok.com` (incluidos los enlaces cortos `vm.tiktok.com` y `vt.tiktok.com`).

## Estructura del proyecto

```
bot.py            Bot de Telegram y arranque del servidor web
web.py            Página web y retransmisión del video
logo.jpg          Imagen de la cabecera y del icono de la página
requirements.txt  Dependencias con versión fija
.gitignore
README.md
```

## Requisitos

- Python 3.10 o superior
- Un token de bot de Telegram, que se obtiene con [@BotFather](https://t.me/BotFather)
- Opcional: `ffmpeg`, que yt-dlp usa para unir pistas de video y audio cuando X las entrega por separado

## Ejecución local

1. Clona el repositorio y entra a la carpeta:

   ```
   git clone https://github.com/raeniclus/twitter-video-downloader-bot.git
   cd twitter-video-downloader-bot
   ```

2. Crea y activa un entorno virtual:

   ```
   python -m venv venv
   venv\Scripts\Activate.ps1        # Windows (PowerShell)
   source venv/bin/activate         # Linux / macOS
   ```

3. Instala las dependencias:

   ```
   pip install -r requirements.txt
   ```

4. Define el token (dura solo mientras la terminal siga abierta) y ejecuta:

   ```
   $env:TELEGRAM_BOT_TOKEN="tu_token"     # Windows (PowerShell)
   export TELEGRAM_BOT_TOKEN="tu_token"   # Linux / macOS

   python bot.py
   ```

La página web queda disponible en `http://localhost:10000`. Se puede cambiar el puerto con la variable de entorno `PORT`.

## Despliegue en Render

El proyecto está pensado para el plan gratuito de Render como **Web Service**. Debe ser un Web Service y no un Background Worker, porque el plan gratuito exige que la aplicación escuche en un puerto HTTP, y `web.py` cumple esa función.

1. En Render, crea un nuevo **Web Service** y conecta este repositorio.
2. Configura:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python bot.py`
   - **Instance Type:** Free
3. Agrega la variable de entorno `TELEGRAM_BOT_TOKEN` con el token de tu bot.
4. Crea el servicio. Cuando el estado sea **Live**, la página web estará en la dirección `https://<nombre-del-servicio>.onrender.com`.

Cada `git push` a la rama `main` vuelve a desplegar el servicio automáticamente.

## Mantener el servicio activo

El plan gratuito de Render suspende el servicio tras 15 minutos sin tráfico HTTP entrante, y al suspenderse el bot deja de responder. Para evitarlo se usa un monitor externo gratuito, por ejemplo [UptimeRobot](https://uptimerobot.com):

- Tipo de monitor: **HTTP(s)**
- URL: la dirección raíz del servicio, sin parámetros (`https://<nombre-del-servicio>.onrender.com`)
- Intervalo: 5 minutos

La página raíz responde de inmediato sin consultar a X, por lo que sirve como verificación de estado.

## Limitaciones

- Los bots de Telegram solo pueden enviar archivos de hasta 50 MB. Los videos más pesados fallan en el bot, pero se pueden ver y descargar desde la página web.
- Render puede reiniciar un servicio gratuito en cualquier momento. Tras un reinicio o una suspensión, la primera petición tarda más de lo normal.
- El tráfico de video de la página web pasa por el servidor y cuenta contra el ancho de banda incluido en el plan gratuito.
- No hay autenticación: cualquier persona que conozca la dirección del servicio o el nombre del bot puede usarlos.
- Solo funciona con publicaciones que yt-dlp pueda extraer. Las publicaciones privadas o restringidas no se pueden descargar, y las publicaciones de TikTok que son fotos en lugar de video tampoco.
- TikTok puede bloquear las peticiones que vienen de servidores como los de Render, por lo que algunos enlaces pueden fallar de forma intermitente.
- YouTube no está soportado: bloquea con frecuencia las IP de servidores en la nube.

## Mantenimiento

X cambia con frecuencia y las versiones antiguas de yt-dlp dejan de funcionar. Si las descargas empiezan a fallar, actualiza la versión de `yt-dlp` en `requirements.txt` y haz push para que Render vuelva a desplegar.

## Aviso

Descarga únicamente contenido que tengas derecho a guardar y respeta los términos de uso de X.

## Licencia

MIT