# main_bot.py
import logging
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters

from config import TELEGRAM_TOKEN
from bot_handlers import (
    start_handler,
    cari_judul_handler,
    handle_text_message,
    recommend_handler,
    handle_callback_query
)
from tmdb_service import get_genres 

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO 
    # Pertimbangkan untuk mengubah ke logging.DEBUG saat mengatasi masalah ini untuk log yang lebih detail
    # level=logging.DEBUG
)
logger = logging.getLogger(__name__)

def main():
    logger.info(f"Mencoba start bot dengan token: '{TELEGRAM_TOKEN[:5]}...'")
    if not TELEGRAM_TOKEN:
        logger.critical("TELEGRAM_TOKEN tidak ditemukan atau kosong! Bot tidak bisa start. Cek file .env dan config.py!")
        return

    try:
        logger.info("Memuat cache genre dari TMDB...")
        if not get_genres(): # Panggil get_genres untuk mengisi cache di awal
            logger.warning("Cache genre kosong setelah percobaan muat awal. Mungkin ada masalah koneksi ke TMDB.")
        else:
            logger.info("Cache genre berhasil dimuat atau sudah ada.")

        application = Application.builder().token(TELEGRAM_TOKEN).build()
    except Exception as e:
        logger.critical(f"Gagal memulai Application: {e}", exc_info=True)
        logger.critical("Pastikan TELEGRAM_TOKEN di file .env string token yang valid dari BotFather.")
        return

    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(CommandHandler("carijudul", cari_judul_handler))
    application.add_handler(CommandHandler("rekomendasi", recommend_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    application.add_handler(CallbackQueryHandler(handle_callback_query))

    logger.info("Bot memulai poll dengan Application...")
    try:
        application.run_polling()
    except Exception as e:
        logger.critical(f"Error menjalankan polling: {e}", exc_info=True)

if __name__ == '__main__':
    main()