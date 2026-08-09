import uuid
from concurrent.futures import ThreadPoolExecutor

from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET, require_POST

from .models import Title
from .services.library import (
    get_library,
    is_favorite,
    record_generation,
    save_title_snapshot,
    toggle_favorite,
)
from .services.tmdb import (
    TMDBError,
    get_genres,
    get_now_playing_movies,
    get_random_title,
    get_recent_top_movies,
    get_recent_top_series,
    get_title_details,
    get_upcoming_movies,
)

DEFAULT_MIN_RATING = 6.0
DEFAULT_MAX_RATING = 10.0


def _safe_genres():
    genre_sets = {"movie": [], "tv": []}
    errors = []
    for media_type in genre_sets:
        try:
            genre_sets[media_type] = get_genres(media_type)
        except TMDBError as exc:
            errors.append(str(exc))
    return genre_sets, errors[0] if errors else None


def _safe_home_rows():
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
            row_name: executor.submit(getter)
            for row_name, getter in getters.items()
        }
        for row_name, future in futures.items():
            try:
                results[row_name] = future.result()
            except TMDBError as exc:
                errors[row_name] = str(exc)
    return results, errors


def _safe_landing_data():
    """Carrega filtros e carrosséis em paralelo para não atrasar a landing page."""

    with ThreadPoolExecutor(max_workers=2) as executor:
        genres_future = executor.submit(_safe_genres)
        rows_future = executor.submit(_safe_home_rows)
        genre_sets, genres_error = genres_future.result()
        rows, row_errors = rows_future.result()
    return genre_sets, genres_error, rows, row_errors


def _parse_filters(request):
    media_type = request.POST.get("media_type", "movie")
    if media_type not in {"movie", "tv"}:
        media_type = "movie"

    genre_id = request.POST.get("genre_id", "").strip()
    if genre_id and not genre_id.isdigit():
        genre_id = ""

    try:
        min_rating = float(request.POST.get("min_rating", DEFAULT_MIN_RATING))
    except (TypeError, ValueError):
        min_rating = DEFAULT_MIN_RATING
    try:
        max_rating = float(request.POST.get("max_rating", DEFAULT_MAX_RATING))
    except (TypeError, ValueError):
        max_rating = DEFAULT_MAX_RATING
    min_rating = min(max(min_rating, 0.0), 10.0)
    max_rating = min(max(max_rating, min_rating), 10.0)
    return media_type, genre_id, min_rating, max_rating


def _visitor_id(request, *, create=False):
    value = request.session.get("visitor_id")
    if value:
        try:
            return uuid.UUID(value)
        except (TypeError, ValueError, AttributeError):
            pass
    if not create:
        return None

    visitor_id = uuid.uuid4()
    request.session["visitor_id"] = str(visitor_id)
    return visitor_id


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


def home(request):
    genre_sets, error, rows, row_errors = _safe_landing_data()
    context = {
        "movie_genres": genre_sets["movie"],
        "tv_genres": genre_sets["tv"],
        "error": error,
        "selected_media_type": "movie",
        "selected_min_rating": DEFAULT_MIN_RATING,
        "selected_max_rating": DEFAULT_MAX_RATING,
        "trending_movies": rows["movie"],
        "trending_series": rows["tv"],
        "now_playing_movies": rows["now_playing"],
        "upcoming_movies": rows["upcoming"],
        "trends_error": row_errors["movie"],
        "series_trends_error": row_errors["tv"],
        "now_playing_error": row_errors["now_playing"],
        "upcoming_error": row_errors["upcoming"],
    }
    context.update(get_library(_visitor_id(request), user=request.user))
    return render(request, "movies/home.html", context)


@require_POST
def generate_movie(request):
    media_type, genre_id, min_rating, max_rating = _parse_filters(request)
    genre_sets, genres_error = _safe_genres()
    context = {
        "movie_genres": genre_sets["movie"],
        "tv_genres": genre_sets["tv"],
        "selected_media_type": media_type,
        "selected_genre": genre_id,
        "selected_min_rating": min_rating,
        "selected_max_rating": max_rating,
    }

    try:
        movie = get_random_title(
            media_type, genre_id or None, min_rating, max_rating
        )
        visitor_id = _visitor_id(request, create=True)
        saved_title = record_generation(
            visitor_id,
            movie,
            genre_id or None,
            _genre_name(genre_sets, media_type, genre_id),
            min_rating,
            user=request.user,
        )
        movie["can_favorite"] = saved_title is not None
        movie["is_favorite"] = is_favorite(
            visitor_id,
            saved_title,
            user=request.user,
        )
        context["movie"] = movie
    except TMDBError as exc:
        context["error"] = str(exc)

    if genres_error and "error" not in context:
        context["error"] = genres_error
    rows, row_errors = _safe_home_rows()
    context["trending_movies"] = rows["movie"]
    context["trending_series"] = rows["tv"]
    context["now_playing_movies"] = rows["now_playing"]
    context["upcoming_movies"] = rows["upcoming"]
    context["trends_error"] = row_errors["movie"]
    context["series_trends_error"] = row_errors["tv"]
    context["now_playing_error"] = row_errors["now_playing"]
    context["upcoming_error"] = row_errors["upcoming"]
    context.update(get_library(_visitor_id(request), user=request.user))
    return render(request, "movies/home.html", context)


@require_GET
def title_detail(request, media_type, tmdb_id):
    if media_type not in {Title.MOVIE, Title.TV}:
        return render(
            request,
            "movies/home.html",
            {
                "is_detail_page": True,
                "error": "Tipo de título inválido.",
                "selected_media_type": "movie",
            },
            status=404,
        )

    context = {
        "is_detail_page": True,
        "selected_media_type": media_type,
    }
    try:
        movie = get_title_details(media_type, tmdb_id)
        visitor_id = _visitor_id(request, create=True)
        saved_title = save_title_snapshot(movie)
        movie["can_favorite"] = saved_title is not None
        movie["is_favorite"] = is_favorite(
            visitor_id,
            saved_title,
            user=request.user,
        )
        context["movie"] = movie
    except TMDBError as exc:
        context["error"] = str(exc)
    return render(request, "movies/home.html", context)


@require_POST
def toggle_title_favorite(request):
    media_type = request.POST.get("media_type", "")
    tmdb_id = request.POST.get("tmdb_id", "")
    if media_type not in {Title.MOVIE, Title.TV} or not tmdb_id.isdigit():
        return JsonResponse({"error": "Título inválido."}, status=400)

    visitor_id = _visitor_id(request, create=True)
    title = get_object_or_404(Title, media_type=media_type, tmdb_id=int(tmdb_id))
    favorited = toggle_favorite(visitor_id, title, user=request.user)
    return JsonResponse(
        {
            "favorited": favorited,
            "message": (
                "Adicionado à minha lista." if favorited else "Removido da minha lista."
            ),
        }
    )
