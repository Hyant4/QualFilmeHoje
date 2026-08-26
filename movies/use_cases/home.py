"""Casos de uso da landing page e da geração de recomendações."""

import math
from concurrent.futures import ThreadPoolExecutor

from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from movies.models import Title
from movies.services.tmdb import (
    BRAZIL_CERTIFICATIONS,
    RUNTIME_FILTERS,
    SPECIAL_CATEGORIES,
    TMDBError,
)

DEFAULT_MIN_RATING = 6.0
DEFAULT_MAX_RATING = 10.0
MIN_RELEASE_YEAR = 1900
MAX_GENRE_ID = 999_999
MAX_TMDB_ID = 2_147_483_647

RUNTIME_OPTIONS = (
    ("", "Qualquer duração"),
    ("up_to_90", "Até 90 minutos"),
    ("90_to_120", "De 90 a 120 minutos"),
    ("over_120", "Mais de 120 minutos"),
)
CERTIFICATION_OPTIONS = (
    ("", "Qualquer classificação"),
    ("L", "Livre"),
    ("10", "10 anos"),
    ("12", "12 anos"),
    ("14", "14 anos"),
    ("16", "16 anos"),
    ("18", "18 anos"),
)


def filter_options_context():
    return {
        "runtime_options": RUNTIME_OPTIONS,
        "certification_options": CERTIFICATION_OPTIONS,
        "movie_special_categories": [
            (key, value["label"]) for key, value in SPECIAL_CATEGORIES["movie"].items()
        ],
        "tv_special_categories": [
            (key, value["label"]) for key, value in SPECIAL_CATEGORIES["tv"].items()
        ],
        "ai_filter_enabled": settings.AI_FILTER_ENABLED,
        "ai_filter_max_text_chars": settings.AI_FILTER_MAX_TEXT_CHARS,
    }


def safe_genres(get_genres):
    genre_sets = {"movie": [], "tv": []}
    errors = []
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = {
            media_type: executor.submit(get_genres, media_type)
            for media_type in genre_sets
        }
        for media_type, future in futures.items():
            try:
                genre_sets[media_type] = future.result()
            except TMDBError as exc:
                errors.append(str(exc))
    return genre_sets, errors[0] if errors else None


def safe_home_rows(
    get_recent_top_movies,
    get_recent_top_series,
    get_now_playing_movies,
    get_upcoming_movies,
):
    getters = {
        "movie": get_recent_top_movies,
        "tv": get_recent_top_series,
        "now_playing": get_now_playing_movies,
        "upcoming": get_upcoming_movies,
    }
    results = {key: [] for key in getters}
    errors = {key: None for key in getters}
    with ThreadPoolExecutor(max_workers=len(getters)) as executor:
        futures = {
            row_name: executor.submit(getter) for row_name, getter in getters.items()
        }
        for row_name, future in futures.items():
            try:
                results[row_name] = future.result()
            except TMDBError as exc:
                errors[row_name] = str(exc)
    return results, errors


def safe_landing_data(
    *,
    get_genres,
    get_recent_top_movies,
    get_recent_top_series,
    get_now_playing_movies,
    get_upcoming_movies,
):
    """Carrega filtros e carrosséis em paralelo para não atrasar a landing page."""

    with ThreadPoolExecutor(max_workers=2) as executor:
        genres_future = executor.submit(safe_genres, get_genres)
        rows_future = executor.submit(
            safe_home_rows,
            get_recent_top_movies,
            get_recent_top_series,
            get_now_playing_movies,
            get_upcoming_movies,
        )
        genre_sets, genres_error = genres_future.result()
        rows, row_errors = rows_future.result()
    return genre_sets, genres_error, rows, row_errors


def parse_ascii_int(value, *, maximum):
    value = str(value or "").strip()
    if not value or len(value) > 10 or not value.isascii() or not value.isdecimal():
        return None
    parsed = int(value)
    return parsed if 1 <= parsed <= maximum else None


def _parse_rating(value, default):
    value = str(value or "").strip()
    if not value or len(value) > 6 or not value.isascii():
        return default
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    if not math.isfinite(parsed):
        return default
    return round(min(max(parsed, 0.0), 10.0), 1)


def _parse_release_year(value, default):
    current_year = timezone.localdate().year
    parsed = parse_ascii_int(value, maximum=9999)
    if parsed is None:
        return default
    return min(max(parsed, MIN_RELEASE_YEAR), current_year)


def parse_filters(request_or_payload):
    payload = getattr(request_or_payload, "POST", request_or_payload)
    media_type = payload.get("media_type", "movie")
    if media_type not in {"movie", "tv"}:
        media_type = "movie"

    genre_value = str(payload.get("genre_id", "")).strip()
    special_category = ""
    if genre_value.startswith("special:"):
        category_key = genre_value.removeprefix("special:")
        if category_key in SPECIAL_CATEGORIES[media_type]:
            special_category = category_key
        genre_id = ""
    else:
        genre_number = parse_ascii_int(genre_value, maximum=MAX_GENRE_ID)
        genre_id = str(genre_number) if genre_number is not None else ""

    min_rating = _parse_rating(
        payload.get("min_rating", DEFAULT_MIN_RATING), DEFAULT_MIN_RATING
    )
    max_rating = _parse_rating(
        payload.get("max_rating", DEFAULT_MAX_RATING), DEFAULT_MAX_RATING
    )
    max_rating = max(max_rating, min_rating)
    min_release_year = _parse_release_year(
        payload.get("min_release_year", MIN_RELEASE_YEAR), MIN_RELEASE_YEAR
    )
    max_release_year = _parse_release_year(
        payload.get("max_release_year", timezone.localdate().year),
        timezone.localdate().year,
    )
    max_release_year = max(max_release_year, min_release_year)
    runtime_filter = payload.get("runtime_filter", "")
    if runtime_filter not in RUNTIME_FILTERS:
        runtime_filter = ""
    certification = str(payload.get("certification", "")).strip().upper()
    if media_type != "movie" or certification not in BRAZIL_CERTIFICATIONS:
        certification = ""
    if not special_category:
        legacy_category = payload.get("special_category", "")
        if legacy_category in SPECIAL_CATEGORIES[media_type]:
            special_category = legacy_category
    return (
        media_type,
        genre_id,
        min_rating,
        max_rating,
        min_release_year,
        max_release_year,
        runtime_filter,
        certification,
        special_category,
    )


def _genre_name(genre_sets, media_type, genre_id):
    if not genre_id:
        return "Qualquer gênero"
    return next(
        (
            genre.get("name", "")
            for genre in genre_sets.get(media_type, [])
            if str(genre.get("id")) == genre_id
        ),
        "",
    )


def _landing_context(genre_sets, genres_error, rows, row_errors):
    current_year = timezone.localdate().year
    context = {
        "movie_genres": genre_sets["movie"],
        "tv_genres": genre_sets["tv"],
        "error": genres_error,
        "selected_media_type": "movie",
        "selected_min_rating": DEFAULT_MIN_RATING,
        "selected_max_rating": DEFAULT_MAX_RATING,
        "selected_min_release_year": MIN_RELEASE_YEAR,
        "selected_max_release_year": current_year,
        "min_release_year_limit": MIN_RELEASE_YEAR,
        "max_release_year_limit": current_year,
        "trending_movies": rows["movie"],
        "trending_series": rows["tv"],
        "now_playing_movies": rows["now_playing"],
        "upcoming_movies": rows["upcoming"],
        "trends_error": row_errors["movie"],
        "series_trends_error": row_errors["tv"],
        "now_playing_error": row_errors["now_playing"],
        "upcoming_error": row_errors["upcoming"],
    }
    context.update(filter_options_context())
    return context


def build_home_context(
    *,
    user,
    visitor_id,
    get_library,
    get_genres,
    get_recent_top_movies,
    get_recent_top_series,
    get_now_playing_movies,
    get_upcoming_movies,
):
    genre_sets, error, rows, row_errors = safe_landing_data(
        get_genres=get_genres,
        get_recent_top_movies=get_recent_top_movies,
        get_recent_top_series=get_recent_top_series,
        get_now_playing_movies=get_now_playing_movies,
        get_upcoming_movies=get_upcoming_movies,
    )
    context = _landing_context(genre_sets, error, rows, row_errors)
    context.update(get_library(visitor_id, user=user, include_favorites=False))
    return context


def build_generation_context(
    *,
    payload,
    user,
    resolve_visitor_id,
    get_library,
    get_genres,
    get_recent_top_movies,
    get_recent_top_series,
    get_now_playing_movies,
    get_upcoming_movies,
    get_random_title,
    record_generation,
    is_favorite,
):
    (
        media_type,
        genre_id,
        min_rating,
        max_rating,
        min_release_year,
        max_release_year,
        runtime_filter,
        certification,
        special_category,
    ) = parse_filters(payload)
    discovery_options = {
        key: value
        for key, value in {
            "runtime_filter": runtime_filter,
            "certification": certification,
            "special_category": special_category,
        }.items()
        if value
    }
    release_year_options = {"min_release_year": min_release_year}
    if payload.get("max_release_year") is not None:
        release_year_options["max_release_year"] = max_release_year
    with ThreadPoolExecutor(max_workers=3) as executor:
        genres_future = executor.submit(safe_genres, get_genres)
        rows_future = executor.submit(
            safe_home_rows,
            get_recent_top_movies,
            get_recent_top_series,
            get_now_playing_movies,
            get_upcoming_movies,
        )
        movie_future = executor.submit(
            get_random_title,
            media_type,
            genre_id or None,
            min_rating,
            max_rating,
            include_streaming=False,
            **release_year_options,
            **discovery_options,
        )
        genre_sets, genres_error = genres_future.result()
        rows, row_errors = rows_future.result()
        try:
            movie = movie_future.result()
            movie_error = None
        except TMDBError as exc:
            movie = None
            movie_error = str(exc)

    context = _landing_context(genre_sets, None, rows, row_errors)
    context.update(
        {
            "selected_media_type": media_type,
            "selected_genre": genre_id,
            "selected_min_rating": min_rating,
            "selected_max_rating": max_rating,
            "selected_min_release_year": min_release_year,
            "selected_max_release_year": max_release_year,
            "selected_runtime_filter": runtime_filter,
            "selected_certification": certification,
            "selected_special_category": special_category,
        }
    )

    if movie is not None:
        streaming_movie_id = parse_ascii_int(movie.get("id"), maximum=MAX_TMDB_ID)
        movie["streaming_deferred"] = bool(
            not movie.get("provider_groups")
            and movie.get("media_type") in {Title.MOVIE, Title.TV}
            and streaming_movie_id is not None
        )
        visitor_id = resolve_visitor_id(create=user.is_authenticated)
        genre_name = _genre_name(genre_sets, media_type, genre_id)
        if user.is_authenticated:
            saved_title = record_generation(
                visitor_id,
                movie,
                genre_id or None,
                genre_name,
                min_rating,
                user=user,
            )
        else:
            movie_id = parse_ascii_int(movie.get("id"), maximum=MAX_TMDB_ID)
            saved_title = (
                Title.objects.filter(media_type=media_type, tmdb_id=movie_id).first()
                if visitor_id and movie_id is not None
                else None
            )
            if movie_id is not None:
                context["anonymous_history_item"] = {
                    "id": movie_id,
                    "media_type": media_type,
                    "title": movie.get("title") or "Título sem nome",
                    "genre_name": genre_name or "Qualquer gênero",
                    "min_rating": min_rating,
                    "created_at": timezone.now().isoformat(),
                    "detail_url": reverse(
                        "movies:title_detail", args=(media_type, movie_id)
                    ),
                }
        movie["can_favorite"] = True
        movie["is_favorite"] = is_favorite(visitor_id, saved_title, user=user)
        context["movie"] = movie
    elif movie_error:
        context["error"] = movie_error

    if genres_error and "error" not in context:
        context["error"] = genres_error
    context.update(
        get_library(
            resolve_visitor_id(create=False),
            user=user,
            include_favorites=False,
        )
    )
    return context
