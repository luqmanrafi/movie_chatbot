import telegram
import logging
import requests
from config import TMDB_API_BASE_URL, TMDB_IMAGE_BASE_URL
from tmdb_service import search_movie_by_title
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

logger = logging.getLogger(__name__)

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_html(
        rf"Hai {user.mention_html()}! Selamat datang di CineBot. Kamu bisa cari judul film dengan menggunakan command /carijudul [Judul film yang ingin dicari] untuk mulai mencari judul",
    )

async def cari_judul_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        movie_title = " ".join(context.args)

        if not movie_title:
            await update.message.reply_text(
                "Judul filmnya apa nih bro/sis? 🤔 Kasih tau dong!\n"
                "Contoh: `/carijudul Inception`"
            )
            return
        logger.info(f"User {update.effective_user} mencari judul: {movie_title}")

        movie_data = search_movie_by_title(movie_title)
        if movie_data:
            title = movie_data.get("title", "Judul tidak ditemukan")
            overview = movie_data.get("overview", "Sinopsis tidak tersedia")
            release_date = movie_data.get("release_date", "Tanggal rilis tidak diketahui")
            poster_path = movie_data.get("poster_path")

            message = f"🎬 *{telegram.helpers.escape_markdown(title, version=2)}*\n\n"
            message += f"🗓️ Rilis: {telegram.helpers.escape_markdown(release_date, version=2)}\n\n"
            message += f"📝 *Sinopsis singkat:*\n{telegram.helpers.escape_markdown(overview[:200] + '...', version =2)}"

            if poster_path:
                poster_url = f"{TMDB_IMAGE_BASE_URL}{poster_path}"
                await context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    photo=poster_url,
                    caption=message,
                    parse_mode=ParseMode.MARKDOWN_V2
                )
            else:
                await update.message.reply_text(message, parse_mode=telegram.ParseMode.MARKDOWN_V2)
        else:
            await update.message.reply_text(
                f"Film '{telegram.helpers.escape_markdown(movie_title, version=2)}' tidak ditemukan\\. Periksa ulang judulnya atau cari film lain",
                parse_mode=ParseMode.MARKDOWN_V2
            )
    except requests.exceptions.RequestException:
        await update.message.reply_text("Terjadi gangguan ke koneksi database film. Coba lagi nanti")
    except Exception as e:
        logger.error(f"Error tidak dikenali: {e}")
        await update.message.reply_text("Ada error pada sistem. Coba lagi nanti")
