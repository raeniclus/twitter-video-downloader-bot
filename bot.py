import logging
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp

from web import start_web_server
threading.Thread(target=start_web_server, daemon=True).start()

# --- Configurar logs para depuración ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("¡Hola! Envíame o comparte cualquier enlace de X (Twitter) con video y te lo descargaré.")

async def process_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    
    # Validar si el texto parece un enlace de X / Twitter
    if not any(domain in url for domain in ["twitter.com", "x.com"]):
        await update.message.reply_text("Por favor, envía un enlace válido de X (Twitter).")
        return

    status_msg = await update.message.reply_text("⏳ Procesando tu video, dame un momento...")

    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': 'downloads/%(id)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
    }

    file_path = None
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)

        await status_msg.edit_text("⬆️ Subiendo video a Telegram...")
        
        with open(file_path, 'rb') as video:
            await update.message.reply_video(video=video, caption="¡Aquí tienes tu video! 🎬")
            
        await status_msg.delete()

    except Exception as e:
        logging.error(f"Error procesando video: {e}")
        await status_msg.edit_text("❌ Ocurrió un error al intentar descargar el video. Verifica el enlace o inténtalo más tarde.")
    
    finally:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)

if __name__ == '__main__':
    if not TOKEN:
        raise ValueError("No se encontró la variable TELEGRAM_BOT_TOKEN.")
        
    os.makedirs("downloads", exist_ok=True)
    
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_video))
    
    print("Bot en marcha...")
    app.run_polling()