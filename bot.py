import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp

# Configurar logs para depuración
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

    status_msg = await update.message.reply_text("⏳ Descargando video desde X...")
    
    video_path = None
    
    # 1. PASO DE DESCARGA
    try:
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': f'downloads/{update.effective_user.id}_%(id)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': False,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if info:
                video_path = ydl.prepare_filename(info)

    except Exception as e:
        logging.error(f"Error en yt-dlp: {e}")

    # 2. PASO DE ENVÍO (Solo se ejecuta si el archivo realmente está grabado en disco)
    if video_path and os.path.exists(video_path):
        try:
            await status_msg.edit_text("⬆️ Subiendo video a Telegram...")
            
            with open(video_path, 'rb') as video_file:
                await update.message.reply_video(video=video_file, caption="Aquí tienes tu video 🎬")
                
            await status_msg.delete()
        except Exception as send_error:
            logging.error(f"Error enviando archivo a Telegram: {send_error}")
        finally:
            if os.path.exists(video_path):
                os.remove(video_path)
    else:
        # Solo se muestra este mensaje si DE VERDAD falló la creación del archivo
        await status_msg.edit_text("❌ No se pudo descargar el video. Verifica que el enlace sea público.")

if __name__ == "__main__":
    os.makedirs("downloads", exist_ok=True)
    
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_video))
    
    print("Bot en marcha...")
    app.run_polling()