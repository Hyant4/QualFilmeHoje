"""Fachada compatível para os módulos especializados da integração TMDB.

O transporte, a normalização, o catálogo e a descoberta vivem em módulos
separados. Esta fachada preserva a API histórica usada pelas views e testes.
"""

import random
from functools import lru_cache

from . import tmdb_catalog, tmdb_client, tmdb_discovery, tmdb_payloads
from .watchmode import get_streaming_groups

API_BASE_URL = tmdb_client.API_BASE_URL
TMDBError = tmdb_client.TMDBError
TMDBNotFound = tmdb_client.TMDBNotFound
BRAZIL_CERTIFICATIONS = tmdb_discovery.BRAZIL_CERTIFICATIONS
DISCOVERY_CACHE_SECONDS = tmdb_discovery.DISCOVERY_CACHE_SECONDS
MAX_STREAMING_CANDIDATES = tmdb_discovery.MAX_STREAMING_CANDIDATES
MIN_RELEASE_YEAR = tmdb_discovery.MIN_RELEASE_YEAR
RUNTIME_FILTERS = tmdb_discovery.RUNTIME_FILTERS
SPECIAL_CATEGORIES = tmdb_discovery.SPECIAL_CATEGORIES
BACKDROP_BASE_URL = tmdb_payloads.BACKDROP_BASE_URL
MAX_TMDB_ID = tmdb_payloads.MAX_TMDB_ID
POSTER_BASE_URL = tmdb_payloads.POSTER_BASE_URL
_as_dict = tmdb_payloads.as_dict
_as_list = tmdb_payloads.as_list
_choose_trailer = tmdb_payloads.choose_trailer
_normalise_credits = tmdb_payloads.normalise_credits
_normalise_rating = tmdb_payloads.normalise_rating
_normalise_reviews = tmdb_payloads.normalise_reviews
_safe_date = tmdb_payloads.safe_date
_safe_nonnegative_int = tmdb_payloads.safe_nonnegative_int
_safe_text = tmdb_payloads.safe_text
_tmdb_image_url = tmdb_payloads.tmdb_image_url
_validate_title_id = tmdb_payloads.validate_title_id

GENRES_CACHE_SECONDS = tmdb_catalog.GENRES_CACHE_SECONDS
TITLE_CACHE_SECONDS = tmdb_catalog.TITLE_CACHE_SECONDS
TITLE_NOT_FOUND_CACHE_SECONDS = tmdb_catalog.TITLE_NOT_FOUND_CACHE_SECONDS
TRENDS_CACHE_SECONDS = tmdb_catalog.TRENDS_CACHE_SECONDS
RELEASE_LISTS_CACHE_SECONDS = tmdb_catalog.RELEASE_LISTS_CACHE_SECONDS
RECENT_RELEASE_DAYS = tmdb_catalog.RECENT_RELEASE_DAYS
TRENDS_MIN_VOTES = tmdb_catalog.TRENDS_MIN_VOTES


def _get(path, **params):
    return tmdb_client.fetch_json(path, **params)


@lru_cache(maxsize=2)
def get_genres(media_type="movie"):
    return tmdb_catalog.get_genres(media_type, fetch=_get)


def _fetch_title_extras(title_id, media_type):
    return tmdb_catalog.fetch_title_extras(title_id, media_type, fetch=_get)


def _build_title_payload(data, media_type, provider_groups=None, streaming_error=None):
    return tmdb_payloads.build_title_payload(
        data, media_type, provider_groups, streaming_error
    )


def get_title_details(media_type, title_id, *, include_streaming=True):
    """Busca a ficha completa de um filme ou série pelo ID do TMDB."""

    return tmdb_catalog.get_title_details(
        media_type,
        title_id,
        include_streaming=include_streaming,
        fetch_title=_fetch_title_extras,
        streaming_getter=get_streaming_groups,
        payload_builder=_build_title_payload,
    )


def _get_recent_top_titles(media_type, limit=10):
    return tmdb_catalog.get_recent_top_titles(media_type, limit, fetch=_get)


def get_recent_top_movies(limit=10):
    return _get_recent_top_titles("movie", limit)


def get_recent_top_series(limit=10):
    return _get_recent_top_titles("tv", limit)


def _normalise_release_list_item(item, availability_kind):
    return tmdb_catalog.normalise_release_list_item(item, availability_kind)


def _get_movie_release_list(list_name, limit=10):
    return tmdb_catalog.get_movie_release_list(list_name, limit, fetch=_get)


def get_now_playing_movies(limit=10):
    return _get_movie_release_list("now_playing", limit)


def get_upcoming_movies(limit=10):
    return _get_movie_release_list("upcoming", limit)


def _discovery_cache_key(
    media_type,
    genre_id,
    min_rating,
    max_rating,
    min_release_year=None,
    runtime_filter=None,
    certification=None,
    special_category=None,
):
    return tmdb_discovery.discovery_cache_key(
        media_type,
        genre_id,
        min_rating,
        max_rating,
        min_release_year,
        runtime_filter,
        certification,
        special_category,
    )


def _find_streaming_candidate(media_type, candidates):
    return tmdb_discovery.find_streaming_candidate(
        media_type,
        candidates,
        streaming_getter=get_streaming_groups,
    )


def _discovery_candidates(results):
    return tmdb_discovery.discovery_candidates(results)


def _load_discovery_page(
    media_type,
    genre_id,
    min_rating,
    max_rating,
    filters,
    min_release_year=None,
    runtime_filter=None,
    certification=None,
    special_category=None,
):
    return tmdb_discovery.load_discovery_page(
        media_type,
        genre_id,
        min_rating,
        max_rating,
        filters,
        min_release_year,
        runtime_filter,
        certification,
        special_category,
        fetch=_get,
        randint=random.randint,
    )


def get_random_title(
    media_type="movie",
    genre_id=None,
    min_rating=0,
    max_rating=10,
    min_release_year=None,
    *,
    include_streaming=True,
    runtime_filter=None,
    certification=None,
    special_category=None,
):
    return tmdb_discovery.get_random_title(
        media_type,
        genre_id,
        min_rating,
        max_rating,
        min_release_year,
        include_streaming=include_streaming,
        runtime_filter=runtime_filter,
        certification=certification,
        special_category=special_category,
        load_page=_load_discovery_page,
        sample=random.sample,
        fetch_title=_fetch_title_extras,
        payload_builder=_build_title_payload,
        streaming_getter=get_streaming_groups,
    )


def get_random_movie(
    genre_id=None, min_rating=0, max_rating=10, min_release_year=None
):
    return get_random_title(
        "movie", genre_id, min_rating, max_rating, min_release_year
    )


def get_random_series(
    genre_id=None, min_rating=0, max_rating=10, min_release_year=None
):
    return get_random_title("tv", genre_id, min_rating, max_rating, min_release_year)
