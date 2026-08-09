import uuid

from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST

from .models import Generation, Title
from .services.library import (
    get_library,
    is_favorite,
    record_generation,
    toggle_favorite,
)
from .services.tmdb import TMDBError, get_genres, get_random_title

DEFAULT_MIN_RATING = 6.0


def _safe_genres():
    genre_sets = {"movie": [], "tv": []}
    errors = []
    for media_type in genre_sets:
        try:
            genre_sets[media_type] = get_genres(media_type)
        except TMDBError as exc:
            errors.append(str(exc))
    return genre_sets, errors[0] if errors else None


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
    min_rating = min(max(min_rating, 0.0), 10.0)
    return media_type, genre_id, min_rating


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
    genre_sets, error = _safe_genres()
    context = {
        "movie_genres": genre_sets["movie"],
        "tv_genres": genre_sets["tv"],
        "error": error,
        "selected_media_type": "movie",
        "selected_min_rating": DEFAULT_MIN_RATING,
    }
    context.update(get_library(_visitor_id(request)))
    return render(request, "movies/home.html", context)


@require_POST
def generate_movie(request):
    media_type, genre_id, min_rating = _parse_filters(request)
    genre_sets, genres_error = _safe_genres()
    context = {
        "movie_genres": genre_sets["movie"],
        "tv_genres": genre_sets["tv"],
        "selected_media_type": media_type,
        "selected_genre": genre_id,
        "selected_min_rating": min_rating,
    }

    try:
        movie = get_random_title(media_type, genre_id or None, min_rating)
        visitor_id = _visitor_id(request, create=True)
        saved_title = record_generation(
            visitor_id,
            movie,
            genre_id or None,
            _genre_name(genre_sets, media_type, genre_id),
            min_rating,
        )
        movie["can_favorite"] = saved_title is not None
        movie["is_favorite"] = is_favorite(visitor_id, saved_title)
        context["movie"] = movie
    except TMDBError as exc:
        context["error"] = str(exc)

    if genres_error and "error" not in context:
        context["error"] = genres_error
    context.update(get_library(_visitor_id(request)))
    return render(request, "movies/home.html", context)


@require_POST
def toggle_title_favorite(request):
    media_type = request.POST.get("media_type", "")
    tmdb_id = request.POST.get("tmdb_id", "")
    if media_type not in {Title.MOVIE, Title.TV} or not tmdb_id.isdigit():
        return JsonResponse({"error": "Título inválido."}, status=400)

    visitor_id = _visitor_id(request, create=True)
    title = get_object_or_404(Title, media_type=media_type, tmdb_id=int(tmdb_id))
    if not Generation.objects.filter(visitor_id=visitor_id, title=title).exists():
        return JsonResponse({"error": "Este título não pertence ao seu histórico."}, status=404)

    favorited = toggle_favorite(visitor_id, title)
    return JsonResponse(
        {
            "favorited": favorited,
            "message": (
                "Adicionado aos favoritos." if favorited else "Removido dos favoritos."
            ),
        }
    )
