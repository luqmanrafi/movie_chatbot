import requests
import logging

from config import TMDB_API_BASE_URL, TMDB_API_KEY
logger = logging.getLogger(__name__)

def search_movie_by_title(movie_title):
    """
    Mencari film berdasarkan judul di TMDB.
    Mengembalikan data film pertama yang ditemukan atau none jika tidak ada.
    """

    if not movie_title:
        return None

    api_url = f"{TMDB_API_BASE_URL}/search/movie"
    params = {
        'api_key': TMDB_API_KEY,
        'query': movie_title,
        'language': 'id-ID',
        'page': 1
    }

    try:
        response = requests.get(api_url, params=params)
        response.raise_for_status()
        data = response.json()

        if data['results']:
            return data['results'][0]
        else:
            return None

    except requests.exceptions.RequestException as e:
        logger.error(f"Error memanggil TMDB API untuk judul '{movie_title}f': {e}")
        raise
    except Exception as e:
        logger.error(f"Error tidak dikenali di search_movie_title: {e}")
        raise