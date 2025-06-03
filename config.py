import os

from dotenv import load_dotenv

load_dotenv()
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TMDB_API_KEY:
    raise ValueError("TMDB_API_KEY belum ditambahkan didalam environment")
if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN belum ditambahkan")

TMDB_API_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500/"
