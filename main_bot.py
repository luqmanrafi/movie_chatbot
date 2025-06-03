# main_bot.py
import logging
from telegram.ext import Application, CommandHandler # Perhatikan Application di sini

# Import konfigurasi dan handler
from config import TELEGRAM_TOKEN
from bot_handlers import start_handler, cari_judul_handler

# Setup logging biar rapi
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    """Start the bot."""
    logger.info(f"Mencoba start bot dengan token: '{TELEGRAM_TOKEN}'")
    if not TELEGRAM_TOKEN:
        logger.critical("TELEGRAM_TOKEN tidak ditemukan atau kosong! Bot tidak bisa start. Cek file .env dan config.py!")
        return

    try:
        application = Application.builder().token(TELEGRAM_TOKEN).build()
    except Exception as e:
        logger.critical(f"Gagal memulai Application: {e}")
        logger.critical("Pastikan TELEGRAM_TOKEN di file .env string token yang valid dari BotFather.")
        return

    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(CommandHandler("carijudul", cari_judul_handler))

    logger.info("Bot memulai poll dengan Application...")
    try:
        application.run_polling()
    except Exception as e:
        logger.critical(f"Error menjalankan polling: {e}")

if __name__ == '__main__':
    main()