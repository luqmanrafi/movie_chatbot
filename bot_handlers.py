import telegram
import logging
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from config import TMDB_IMAGE_BASE_URL
from tmdb_service import (
    search_movie_by_title,
    get_movie_details,
    get_similar_movies,
    get_popular_movies,
    discover_movies_by_genre,
    get_genres
)

logger = logging.getLogger(__name__)

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE): #
    user = update.effective_user #
    get_genres() 
    await update.message.reply_html( #
        rf"Hai {user.mention_html()}! Selamat datang di CineBot. Kamu bisa cari judul film dengan menggunakan perintah /carijudul [Judul film] atau ketik langsung judulnya. Gunakan /rekomendasi untuk mendapatkan saran film.", #
    )

async def display_single_movie_details(update_or_query, context: ContextTypes.DEFAULT_TYPE, movie_data: dict, message_intro: str = None):
    message_target = update_or_query.message if hasattr(update_or_query, 'message') else update_or_query.callback_query.message
    chat_id_to_send = message_target.chat_id

    if not movie_data:
        await message_target.reply_text("Detail film tidak ditemukan.")
        return

    movie_id = movie_data.get("id")
    # Selalu coba ambil detail terbaru jika belum lengkap, terutama untuk videos dan credits
    if 'runtime' not in movie_data or 'genres' not in movie_data or 'videos' not in movie_data or 'credits' not in movie_data:
        logger.info(f"Mengambil detail lengkap untuk movie ID: {movie_id} karena data awal kurang lengkap.")
        detailed_movie_info = get_movie_details(movie_id) # Fungsi ini mengambil 'videos' dan 'credits'
        if detailed_movie_info:
            movie_data.update(detailed_movie_info)
        else:
            logger.warning(f"Gagal mengambil detail lengkap untuk movie ID: {movie_id}. Menampilkan dengan data seadanya.")
            # Tidak perlu return, tampilkan saja apa yang ada jika gagal fetch detail

    # Helper untuk escape, agar lebih singkat
    def esc(text):
        if text is None:
            return ""
        return telegram.helpers.escape_markdown(str(text), version=2)

    title = movie_data.get("title", "Judul tidak ditemukan")
    overview = movie_data.get("overview", "Sinopsis tidak tersedia")
    release_date = movie_data.get("release_date", "Tanggal rilis tidak diketahui")
    poster_path = movie_data.get("poster_path")
    
    rating_val = movie_data.get("vote_average")
    rating_str = f"{rating_val:.1f}/10" if rating_val and isinstance(rating_val, (float, int)) and rating_val > 0 else "N/A"
    
    genres_list = movie_data.get("genres", [])
    genre_names = ", ".join([g.get("name", "") for g in genres_list if g.get("name")]) if genres_list else "Tidak diketahui"
    
    runtime_min = movie_data.get("runtime")
    runtime_str = f"{runtime_min} menit" if runtime_min and isinstance(runtime_min, int) and runtime_min > 0 else "N/A"
    
    tagline = movie_data.get("tagline", "")
    original_language = movie_data.get("original_language", "N/A")

    message_parts = []
    if message_intro:
        message_parts.append(esc(message_intro))

    message_parts.append(f"🎬 *{esc(title)}*")
    if tagline:
        message_parts.append(f"_{esc(tagline)}_")
    
    message_parts.append(f"\n🗓️ Rilis: {esc(release_date)}")
    message_parts.append(f"⭐ Rating: {esc(rating_str)}")
    message_parts.append(f"🎭 Genre: {esc(genre_names)}")
    message_parts.append(f"⏳ Durasi: {esc(runtime_str)}")
    message_parts.append(f"🌐 Bahasa Asli: {esc(original_language.upper())}")
    
    overview_text_to_escape = overview[:300] + ('...' if len(overview) > 300 else '')
    message_parts.append(f"\n📝 *Sinopsis singkat:*\n{esc(overview_text_to_escape)}")

    final_message = "\n".join(filter(None, message_parts)) # filter(None, ...) untuk menghapus string kosong jika ada

    logger.debug(f"Final caption data untuk movie ID {movie_id}:\n{final_message}")


    keyboard = []
    if movie_id:
        keyboard.append([
            InlineKeyboardButton("🎬 Lihat Trailer", callback_data=f"trailer_{movie_id}"),
            InlineKeyboardButton("🧑‍🎤 Info Pemeran", callback_data=f"cast_{movie_id}")
        ])
        keyboard.append([
            InlineKeyboardButton("🍿 Film Serupa", callback_data=f"similar_{movie_id}")
        ])
    reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None

    try:
        if poster_path:
            poster_url = f"{TMDB_IMAGE_BASE_URL}{poster_path}"
            if hasattr(update_or_query, 'callback_query') and update_or_query.callback_query.message.photo:
                await context.bot.edit_message_caption(
                    chat_id=chat_id_to_send, message_id=message_target.message_id,
                    caption=final_message, parse_mode=ParseMode.MARKDOWN_V2, reply_markup=reply_markup
                )
            else:
                await context.bot.send_photo(
                    chat_id=chat_id_to_send, photo=poster_url,
                    caption=final_message, parse_mode=ParseMode.MARKDOWN_V2, reply_markup=reply_markup
                )
        else:
            if hasattr(update_or_query, 'callback_query'):
                await context.bot.edit_message_text(
                    text=final_message, chat_id=chat_id_to_send, message_id=message_target.message_id,
                    parse_mode=ParseMode.MARKDOWN_V2, reply_markup=reply_markup
                )
            else:
                 await message_target.reply_text(
                     final_message, parse_mode=ParseMode.MARKDOWN_V2, reply_markup=reply_markup
                 )
    except telegram.error.BadRequest as e:
        # Log ini PENTING untuk debugging
        logger.error(
            f"Terjadi BadRequest saat menampilkan detail film (ID: {movie_id}). Error: {e}. "
            f"Caption yang dicoba (panjang {len(final_message)}):\n-----\n{final_message}\n-----",
            exc_info=True
        )
        # Fallback dengan pesan yang sangat sederhana TANPA MARKDOWN
        fallback_text = f"Info untuk film: {title}\n(Gagal menampilkan detail lengkap karena format pesan)"
        await message_target.reply_text(fallback_text, parse_mode=None, reply_markup=reply_markup if poster_path else None) # Markup mungkin masih berguna
    except Exception as e:
        logger.error(f"Error tidak terduga saat menampilkan detail film (ID: {movie_id}): {e}", exc_info=True)
        await message_target.reply_text("Maaf, terjadi kesalahan sistem saat menampilkan info film.", parse_mode=None)


async def display_movie_list(update_or_query, context: ContextTypes.DEFAULT_TYPE, movies: list, intro_message: str):
    message_target = update_or_query.message if hasattr(update_or_query, 'message') else update_or_query.callback_query.message
    if not movies:
        await message_target.reply_text("Tidak ada film yang cocok dengan kriteriamu saat ini.")
        return

    keyboard = []
    escaped_intro_message = telegram.helpers.escape_markdown(intro_message, version=2)
    message_text_for_md = escaped_intro_message + "\n" # Pesan teks akan pakai MD

    # Buat daftar teks film untuk fallback jika MD gagal
    fallback_movie_texts = []

    for movie in movies[:5]: 
        release_year = movie.get("release_date", "N/A").split('-')[0] if movie.get("release_date") else "N/A"
        button_text_unescaped = f"{movie.get('title', 'Judul Tidak Ada')} ({release_year})"
        keyboard.append([InlineKeyboardButton(button_text_unescaped, callback_data=f"movie_select_{movie.get('id')}")])
        fallback_movie_texts.append(f"- {button_text_unescaped}")
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        # Coba kirim dengan MarkdownV2
        await message_target.reply_text(message_text_for_md, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN_V2)
    except telegram.error.BadRequest as e:
        logger.warning(f"Gagal mengirim daftar film dengan MarkdownV2: {e}. Mencoba tanpa Markdown.")
        # Fallback: kirim intro biasa + daftar film sebagai teks biasa
        fallback_text = intro_message + "\n" + "\n".join(fallback_movie_texts)
        await message_target.reply_text(fallback_text, reply_markup=reply_markup, parse_mode=None)


async def cari_judul_handler(update: Update, context: ContextTypes.DEFAULT_TYPE): #
    try:
        movie_title_parts = context.args
        movie_title = ""
        if not movie_title_parts: 
            if update.message and update.message.text:
                command_candidate = update.message.text.split(" ")[0]
                if command_candidate.startswith('/'):
                    movie_title = update.message.text[len(command_candidate):].strip()
                else: 
                    movie_title = update.message.text.strip()

                if not movie_title: 
                    msg_no_title = "Judul filmnya apa nih bro/sis? 🤔 Kasih tau dong!\nContoh: `/carijudul Inception` atau ketik `cariin film Inception`"
                    await update.message.reply_text(
                        telegram.helpers.escape_markdown(msg_no_title, version=2),
                        parse_mode=ParseMode.MARKDOWN_V2
                    )
                    return
            else: 
                await update.message.reply_text("Format pencarian sepertinya salah. Coba lagi ya.")
                return
        else:
             movie_title = " ".join(movie_title_parts)

        logger.info(f"Pengguna {update.effective_user.first_name} mencari judul: {movie_title}")
        movies_data = search_movie_by_title(movie_title, count=3)

        if movies_data:
            if len(movies_data) == 1:
                await display_single_movie_details(update, context, movies_data[0])
            else:
                await display_movie_list(update, context, movies_data, f"Aku menemukan beberapa film yang cocok dengan '{telegram.helpers.escape_markdown(movie_title,version=2)}', pilih salah satu:")
        else:
            await update.message.reply_text(
                f"Film '{telegram.helpers.escape_markdown(movie_title, version=2)}' tidak ditemukan\\. Periksa ulang judulnya atau cari film lain",
                parse_mode=ParseMode.MARKDOWN_V2
            )
    except requests.exceptions.RequestException:
        await update.message.reply_text("Terjadi gangguan koneksi ke database film. Coba lagi nanti.")
    except Exception as e:
        logger.error(f"Error tidak dikenali di cari_judul_handler: {e}", exc_info=True)
        await update.message.reply_text("Ada error pada sistem. Coba lagi nanti.")

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text.lower()
    logger.info(f"Pengguna {update.effective_user.first_name} mengirim teks: {user_text}")

    search_keywords = ["cariin film", "info film", "tentang film", "search movie", "cari", "film apa"]
    recommendation_keywords = ["rekomendasiin film", "kasih film", "film bagus dong", "rekomendasi", "suggest movie", "rekomen film"]
    genre_keywords = ["genre", "jenis"]

    detected_intent = None
    extracted_data = {}

    for keyword in recommendation_keywords:
        if user_text.startswith(keyword) or keyword in user_text :
            detected_intent = "recommend_movie"
            # Coba hapus keyword utama dulu untuk sisa teks
            temp_text = user_text
            for kw in sorted(recommendation_keywords, key=len, reverse=True): # Hapus keyword terpanjang dulu
                if kw in temp_text:
                    temp_text = temp_text.replace(kw, "", 1).strip() # Hanya replace sekali

            remaining_text = temp_text
            
            potential_genre_parts = []
            words = remaining_text.split()
            genre_keyword_found_at_idx = -1

            for i, word in enumerate(words):
                if word in genre_keywords:
                    genre_keyword_found_at_idx = i
                    break
            
            if genre_keyword_found_at_idx != -1:
                # Ambil kata setelah keyword genre
                if genre_keyword_found_at_idx + 1 < len(words):
                    potential_genre_parts.append(words[genre_keyword_found_at_idx+1])
                    # Coba ambil kata kedua jika ada dan bukan keyword lain
                    if genre_keyword_found_at_idx + 2 < len(words) and \
                       not any(kw in words[genre_keyword_found_at_idx+2] for kw in search_keywords + recommendation_keywords + genre_keywords):
                        potential_genre_parts.append(words[genre_keyword_found_at_idx+2])
            elif remaining_text: # Jika tidak ada keyword "genre", anggap sisa teks adalah nama genre
                 potential_genre_parts = words # Ambil semua kata sisa

            if potential_genre_parts:
                # Bersihkan dari kata-kata umum seperti "film" jika masih ada
                cleaned_genre_name = " ".join(pt for pt in potential_genre_parts if pt not in ["film"])
                if cleaned_genre_name:
                    extracted_data["genre"] = cleaned_genre_name
            break 

    if not detected_intent:
        for keyword in search_keywords:
            if user_text.startswith(keyword): # Lebih prioritas jika keyword di awal
                detected_intent = "search_movie"
                title_query = user_text.replace(keyword, "", 1).strip() 
                if title_query:
                    extracted_data["movie_title"] = title_query
                else: 
                    detected_intent = None 
                break

    if detected_intent == "search_movie" and extracted_data.get("movie_title"):
        logger.info(f"NLP: Maksud=search_movie, Judul='{extracted_data['movie_title']}'")
        context.args = extracted_data["movie_title"].split()
        await cari_judul_handler(update, context)
    elif detected_intent == "recommend_movie":
        genre = extracted_data.get("genre")
        logger.info(f"NLP: Maksud=recommend_movie, Genre='{genre if genre else 'Umum'}'")
        await handle_recommendation_request(update, context, genre=genre, source="NLP Text")
    else:
        # Fallback: jika tidak ada maksud jelas, anggap sebagai pencarian judul
        logger.info(f"NLP: Tidak ada maksud jelas, mencoba sebagai pencarian judul: '{user_text}'")
        context.args = user_text.split() 
        await cari_judul_handler(update, context)


async def handle_recommendation_request(update: Update, context: ContextTypes.DEFAULT_TYPE, genre: str = None, source: str = "Unknown"):
    message_target = update.message if update.message else update.callback_query.message
    try:
        if genre:
            genre_clean = genre.replace("genre", "").replace("jenis","").strip()
            if not genre_clean : 
                 logger.info(f"Permintaan rekomendasi umum (source: {source}, genre awal: '{genre}')")
                 movies = get_popular_movies(count=5)
                 if movies:
                     await display_movie_list(update, context, movies, "Berikut beberapa film populer yang mungkin kamu suka:")
                 else:
                     await message_target.reply_text("Maaf, tidak bisa mendapatkan rekomendasi film populer saat ini.")
                 return

            logger.info(f"Permintaan rekomendasi untuk genre: {genre_clean} (source: {source})")
            movies = discover_movies_by_genre(genre_clean, count=5)
            if movies:
                escaped_genre = telegram.helpers.escape_markdown(genre_clean, version=2)
                await display_movie_list(update, context, movies, f"Berikut rekomendasi film genre *{escaped_genre}*:")
            else:
                await message_target.reply_text(f"Maaf, tidak ada film genre '{telegram.helpers.escape_markdown(genre_clean,version=2)}' yang bisa kutemukan atau genrenya tidak valid\\.", parse_mode=ParseMode.MARKDOWN_V2)
        else:
            logger.info(f"Permintaan rekomendasi umum (source: {source})")
            movies = get_popular_movies(count=5) 
            if movies:
                await display_movie_list(update, context, movies, "Berikut beberapa film populer yang mungkin kamu suka:")
            else:
                await message_target.reply_text("Maaf, tidak bisa mendapatkan rekomendasi film populer saat ini.")
    except requests.exceptions.RequestException:
        await message_target.reply_text("Terjadi gangguan koneksi ke database film. Coba lagi nanti.")
    except Exception as e:
        logger.error(f"Error tidak dikenali di handle_recommendation_request: {e}", exc_info=True)
        await message_target.reply_text("Ada error pada sistem saat memproses rekomendasi. Coba lagi nanti.")


async def recommend_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    genre_name = None
    if context.args:
        if context.args[0].lower() == "genre" and len(context.args) > 1:
            genre_name = " ".join(context.args[1:])
        else:
            genre_name = " ".join(context.args)
    
    await handle_recommendation_request(update, context, genre=genre_name, source="Perintah /rekomendasi")


async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer() 

    data = query.data
    logger.info(f"Callback query diterima: {data} dari user {query.from_user.first_name}")

    try:
        if data.startswith("movie_select_"):
            movie_id = int(data.split("_")[2])
            logger.info(f"User memilih movie ID: {movie_id} dari daftar.")
            movie_details = get_movie_details(movie_id)
            if movie_details:
                await display_single_movie_details(query, context, movie_details, message_intro="Kamu memilih:")
            else:
                try:
                    await query.edit_message_text(text="Maaf, detail film tidak ditemukan.")
                except telegram.error.BadRequest: 
                    await query.message.reply_text("Maaf, detail film tidak ditemukan.")


        elif data.startswith("trailer_"):
            movie_id = int(data.split("_")[1])
            logger.info(f"Permintaan trailer untuk movie ID: {movie_id}")
            movie_details = get_movie_details(movie_id) 
            videos = movie_details.get('videos', {}).get('results', [])
            youtube_trailers = [v for v in videos if v['site'].lower() == 'youtube' and v['type'].lower() in ('trailer', 'teaser')]

            if youtube_trailers:
                trailer = youtube_trailers[0] 
                trailer_url = f"https://www.youtube.com/watch?v={trailer['key']}"
                # URL biasanya aman dan tidak memerlukan escaping untuk link preview, tapi teks di sekitarnya iya
                message_text = f"🎬 Ini dia trailernya: {telegram.helpers.escape_markdown(trailer_url, version=2)}"
                
                await query.message.reply_text(message_text, parse_mode=ParseMode.MARKDOWN_V2, disable_web_page_preview=False)
            else:
                await query.message.reply_text("Maaf, trailer tidak ditemukan untuk film ini.")

        elif data.startswith("cast_"):
            movie_id = int(data.split("_")[1])
            logger.info(f"Permintaan info pemeran untuk movie ID: {movie_id}")
            movie_details = get_movie_details(movie_id) 
            cast_list = movie_details.get('credits', {}).get('cast', [])
            
            if cast_list:
                message_parts = ["*Daftar Pemeran Utama:*"]
                for actor in cast_list[:7]: 
                    actor_name = telegram.helpers.escape_markdown(actor['name'], version=2)
                    char_name = telegram.helpers.escape_markdown(actor['character'], version=2)
                    message_parts.append(f"\\- {actor_name} sebagai {char_name}")
                final_message = "\n".join(message_parts)
                await query.message.reply_text(final_message, parse_mode=ParseMode.MARKDOWN_V2)
            else:
                await query.message.reply_text("Maaf, info pemeran tidak ditemukan.")

        elif data.startswith("similar_"):
            movie_id = int(data.split("_")[1])
            logger.info(f"Permintaan film serupa untuk movie ID: {movie_id}")
            similar_movies_list = get_similar_movies(movie_id, count=5)
            if similar_movies_list:
                await display_movie_list(query, context, similar_movies_list, "Berikut beberapa film yang mirip:")
            else:
                await query.message.reply_text("Tidak ditemukan film serupa untuk saat ini.")
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Error RequestException di handle_callback_query: {e}", exc_info=True)
        await query.message.reply_text("Terjadi gangguan koneksi ke database film. Coba lagi nanti.")
    except telegram.error.BadRequest as e:
        # Log yang lebih spesifik untuk BadRequest di level ini
        logger.error(f"Error BadRequest di handle_callback_query (level atas): {e}", exc_info=True)
        await query.message.reply_text("Terjadi kesalahan format saat memproses permintaanmu. Coba lagi nanti.", parse_mode=None)
    except Exception as e:
        logger.error(f"Error tidak dikenali (umum) di handle_callback_query: {e}", exc_info=True)
        await query.message.reply_text("Ada error pada sistem saat memproses permintaanmu. Coba lagi nanti.")