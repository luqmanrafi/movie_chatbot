import requests
import logging

from config import TMDB_API_BASE_URL, TMDB_API_KEY #
logger = logging.getLogger(__name__)

_genre_cache = None

def get_genres():
    """
    Mengambil dan menyimpan cache daftar genre film dari TMDB.
    """
    global _genre_cache
    if _genre_cache:
        return _genre_cache

    api_url = f"{TMDB_API_BASE_URL}/genre/movie/list"
    params = {'api_key': TMDB_API_KEY, 'language': 'id-ID'}
    try:
        response = requests.get(api_url, params=params)
        response.raise_for_status()
        _genre_cache = {genre['id']: genre['name'] for genre in response.json()['genres']}
        logger.info("Cache genre berhasil dimuat.")
        return _genre_cache
    except requests.exceptions.RequestException as e:
        logger.error(f"Error mengambil genre TMDB: {e}")
        return {} # Kembalikan dict kosong jika error
    except Exception as e:
        logger.error(f"Error tidak dikenali di get_genres: {e}")
        return {}


def search_movie_by_title(movie_title, count=5): #
    """
    Mencari film berdasarkan judul di TMDB.
    Mengembalikan daftar film yang ditemukan (hingga 'count') atau None jika tidak ada.
    """ #

    if not movie_title: #
        return None #

    api_url = f"{TMDB_API_BASE_URL}/search/movie" #
    params = { #
        'api_key': TMDB_API_KEY, #
        'query': movie_title, #
        'language': 'id-ID', #
        'page': 1 #
    }

    try:
        response = requests.get(api_url, params=params) #
        response.raise_for_status() #
        data = response.json() #

        if data['results']: #
            return data['results'][:count] #
        else:
            return None #

    except requests.exceptions.RequestException as e: #
        logger.error(f"Error memanggil TMDB API untuk judul '{movie_title}': {e}") #
        raise #
    except Exception as e: #
        logger.error(f"Error tidak dikenali di search_movie_by_title: {e}") #
        raise #

def get_movie_details(movie_id):
    """
    Mengambil detail lengkap film berdasarkan ID dari TMDB.
    Juga mengambil video (trailer) dan kredit (pemeran).
    """
    if not movie_id:
        return None

    api_url = f"{TMDB_API_BASE_URL}/movie/{movie_id}"
    params = {
        'api_key': TMDB_API_KEY,
        'language': 'id-ID',
        'append_to_response': 'videos,credits'
    }
    try:
        response = requests.get(api_url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error memanggil TMDB API untuk detail film ID '{movie_id}': {e}")
        raise
    except Exception as e:
        logger.error(f"Error tidak dikenali di get_movie_details: {e}")
        raise

def get_similar_movies(movie_id, count=5):
    """
    Mengambil daftar film serupa berdasarkan ID film dari TMDB.
    """
    if not movie_id:
        return None
    api_url = f"{TMDB_API_BASE_URL}/movie/{movie_id}/similar"
    params = {'api_key': TMDB_API_KEY, 'language': 'id-ID', 'page': 1}
    try:
        response = requests.get(api_url, params=params)
        response.raise_for_status()
        data = response.json()
        return data.get('results', [])[:count]
    except requests.exceptions.RequestException as e:
        logger.error(f"Error mengambil film serupa untuk ID '{movie_id}': {e}")
        return [] # Kembalikan daftar kosong jika error
    except Exception as e:
        logger.error(f"Error tidak dikenali di get_similar_movies: {e}")
        return []

def get_popular_movies(count=5):
    """
    Mengambil daftar film populer dari TMDB.
    """
    api_url = f"{TMDB_API_BASE_URL}/movie/popular"
    params = {'api_key': TMDB_API_KEY, 'language': 'id-ID', 'page': 1}
    try:
        response = requests.get(api_url, params=params)
        response.raise_for_status()
        data = response.json()
        return data.get('results', [])[:count]
    except requests.exceptions.RequestException as e:
        logger.error(f"Error mengambil film populer: {e}")
        return []
    except Exception as e:
        logger.error(f"Error tidak dikenali di get_popular_movies: {e}")
        return []

def get_top_rated_movies(count=5):
    """
    Mengambil daftar film dengan rating tertinggi dari TMDB.
    """
    api_url = f"{TMDB_API_BASE_URL}/movie/top_rated"
    params = {'api_key': TMDB_API_KEY, 'language': 'id-ID', 'page': 1}
    try:
        response = requests.get(api_url, params=params)
        response.raise_for_status()
        data = response.json()
        return data.get('results', [])[:count]
    except requests.exceptions.RequestException as e:
        logger.error(f"Error mengambil film rating tertinggi: {e}")
        return []
    except Exception as e:
        logger.error(f"Error tidak dikenali di get_top_rated_movies: {e}")
        return []

def discover_movies_by_genre(genre_name, count=5):
    """
    Menemukan film berdasarkan nama genre dari TMDB.
    """
    all_genres_map = get_genres() # Memastikan cache genre dimuat
    genre_id = None
    for gid, name in all_genres_map.items():
        if name.lower() == genre_name.lower():
            genre_id = gid
            break
    
    if not genre_id:
        logger.warning(f"Genre ID untuk '{genre_name}' tidak ditemukan.")
        return []

    api_url = f"{TMDB_API_BASE_URL}/discover/movie"
    params = {
        'api_key': TMDB_API_KEY,
        'language': 'id-ID',
        'sort_by': 'popularity.desc',
        'with_genres': str(genre_id),
        'page': 1
    }
    try:
        response = requests.get(api_url, params=params)
        response.raise_for_status()
        data = response.json()
        return data.get('results', [])[:count]
    except requests.exceptions.RequestException as e:
        logger.error(f"Error menemukan film berdasarkan genre '{genre_name}': {e}")
        return []
    except Exception as e:
        logger.error(f"Error tidak dikenali di discover_movies_by_genre: {e}")
        return []