import json
import logging
import math
import uuid
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlsplit, urlunsplit

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from .models import Title
from .security import rate_limit
from .services.library import (
    get_favorites,
    get_library,
    is_favorite,
    record_generation,
    save_title_snapshot,
    toggle_favorite,
)
from .services.tmdb import (
    BRAZIL_CERTIFICATIONS,
    RUNTIME_FILTERS,
    SPECIAL_CATEGORIES,
    TMDBError,
    TMDBNotFound,
    get_genres,
    get_now_playing_movies,
    get_random_title,
    get_recent_top_movies,
    get_recent_top_series,
    get_title_details,
    get_upcoming_movies,
)
from .services.watchmode import WatchmodeError, get_streaming_groups

DEFAULT_MIN_RATING = 6.0
DEFAULT_MAX_RATING = 10.0
MIN_RELEASE_YEAR = 1900
MAX_GENRE_ID = 999_999
MAX_TMDB_ID = 2_147_483_647
CSP_REPORT_MAX_BYTES = 16 * 1024
logger = logging.getLogger(__name__)

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


def _filter_options_context():
    return {
        "runtime_options": RUNTIME_OPTIONS,
        "certification_options": CERTIFICATION_OPTIONS,
        "movie_special_categories": [
            (key, value["label"])
            for key, value in SPECIAL_CATEGORIES["movie"].items()
        ],
        "tv_special_categories": [
            (key, value["label"])
            for key, value in SPECIAL_CATEGORIES["tv"].items()
        ],
    }


@require_GET
def robots_txt(_request):
    lines = (
        "User-agent: *",
        "Allow: /",
        "Disallow: /admin/",
        "Disallow: /security/",
        "Disallow: /gerar/",
        "Disallow: /favoritos/",
        f"Sitemap: {settings.SITE_URL}/sitemap.xml",
    )
    return HttpResponse("\n".join(lines) + "\n", content_type="text/plain")


@require_GET
def indexnow_key(_request):
    response = HttpResponse(settings.INDEXNOW_KEY, content_type="text/plain")
    response["X-Robots-Tag"] = "noindex"
    response["Cache-Control"] = "public, max-age=86400"
    return response


def _sanitise_csp_report_value(key, value):
    if not isinstance(value, str | int | float):
        return ""
    text = " ".join(str(value).split())[:1000]
    if key.endswith("-uri") or key in {"documentURL", "blockedURL", "sourceFile"}:
        parts = urlsplit(text)
        if parts.scheme in {"http", "https"}:
            text = urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))
    return text


@csrf_exempt
@require_POST
@rate_limit("csp-report", ip=(60, 300), methods={"POST"})
def csp_report(request):
    """Recebe relatorios sem cookies sensiveis, queries ou amostras de script."""

    body = request.body
    if len(body) > CSP_REPORT_MAX_BYTES:
        return HttpResponse(status=413)
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return HttpResponse(status=400)

    entries = payload if isinstance(payload, list) else [payload]
    allowed_keys = {
        "blocked-uri",
        "blockedURL",
        "column-number",
        "columnNumber",
        "disposition",
        "document-uri",
        "documentURL",
        "effective-directive",
        "line-number",
        "lineNumber",
        "source-file",
        "sourceFile",
        "status-code",
        "violated-directive",
    }
    for entry in entries[:20]:
        if not isinstance(entry, dict):
            continue
        report = entry.get("csp-report", entry.get("body", entry))
        if not isinstance(report, dict):
            continue
        safe_report = {
            key: _sanitise_csp_report_value(key, report[key])
            for key in allowed_keys & report.keys()
        }
        logger.warning("CSP report-only violation: %s", safe_report)
    return HttpResponse(status=204)


def _safe_genres():
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


def _parse_ascii_int(value, *, maximum):
    value = str(value or "").strip()
    if not value or len(value) > 10 or not value.isascii() or not value.isdecimal():
        return None
    parsed = int(value)
    return parsed if 1 <= parsed <= maximum else None


def _parse_rating(value, default):
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    if not math.isfinite(parsed):
        return default
    return round(min(max(parsed, 0.0), 10.0), 1)


def _parse_min_release_year(value):
    current_year = timezone.localdate().year
    parsed = _parse_ascii_int(value, maximum=9999)
    if parsed is None:
        return MIN_RELEASE_YEAR
    return min(max(parsed, MIN_RELEASE_YEAR), current_year)


def _parse_filters(request):
    media_type = request.POST.get("media_type", "movie")
    if media_type not in {"movie", "tv"}:
        media_type = "movie"

    genre_value = str(request.POST.get("genre_id", "")).strip()
    special_category = ""
    if genre_value.startswith("special:"):
        category_key = genre_value.removeprefix("special:")
        if category_key in SPECIAL_CATEGORIES[media_type]:
            special_category = category_key
        genre_id = ""
    else:
        genre_number = _parse_ascii_int(genre_value, maximum=MAX_GENRE_ID)
        genre_id = str(genre_number) if genre_number is not None else ""

    min_rating = _parse_rating(
        request.POST.get("min_rating", DEFAULT_MIN_RATING), DEFAULT_MIN_RATING
    )
    max_rating = _parse_rating(
        request.POST.get("max_rating", DEFAULT_MAX_RATING), DEFAULT_MAX_RATING
    )
    max_rating = max(max_rating, min_rating)
    min_release_year = _parse_min_release_year(
        request.POST.get("min_release_year", MIN_RELEASE_YEAR)
    )
    runtime_filter = request.POST.get("runtime_filter", "")
    if runtime_filter not in RUNTIME_FILTERS:
        runtime_filter = ""
    certification = str(request.POST.get("certification", "")).strip().upper()
    if media_type != "movie" or certification not in BRAZIL_CERTIFICATIONS:
        certification = ""
    # Mantem compatibilidade com formularios abertos antes desta refatoracao.
    if not special_category:
        legacy_category = request.POST.get("special_category", "")
        if legacy_category in SPECIAL_CATEGORIES[media_type]:
            special_category = legacy_category
    return (
        media_type,
        genre_id,
        min_rating,
        max_rating,
        min_release_year,
        runtime_filter,
        certification,
        special_category,
    )


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


@require_GET
def privacy(request):
    return render(request, "movies/privacy.html")


@require_GET
def random_movies(request):
    return render(
        request,
        "movies/home.html",
        {
            "is_content_page": True,
            "selected_media_type": "movie",
        },
    )


@require_GET
def favorites(request):
    return render(
        request,
        "movies/favorites.html",
        {
            "favorites": get_favorites(
                _visitor_id(request),
                user=request.user,
            ),
        },
    )


def home(request):
    genre_sets, error, rows, row_errors = _safe_landing_data()
    current_year = timezone.localdate().year
    context = {
        "movie_genres": genre_sets["movie"],
        "tv_genres": genre_sets["tv"],
        "error": error,
        "selected_media_type": "movie",
        "selected_min_rating": DEFAULT_MIN_RATING,
        "selected_max_rating": DEFAULT_MAX_RATING,
        "selected_min_release_year": MIN_RELEASE_YEAR,
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
    context.update(_filter_options_context())
    context.update(
        get_library(
            _visitor_id(request),
            user=request.user,
            include_favorites=False,
        )
    )
    return render(request, "movies/home.html", context)


@require_POST
@rate_limit("generate", ip=(30, 300), user=(20, 300), methods={"POST"})
def generate_movie(request):
    (
        media_type,
        genre_id,
        min_rating,
        max_rating,
        min_release_year,
        runtime_filter,
        certification,
        special_category,
    ) = _parse_filters(request)
    discovery_options = {
        key: value
        for key, value in {
            "runtime_filter": runtime_filter,
            "certification": certification,
            "special_category": special_category,
        }.items()
        if value
    }
    with ThreadPoolExecutor(max_workers=3) as executor:
        genres_future = executor.submit(_safe_genres)
        rows_future = executor.submit(_safe_home_rows)
        movie_future = executor.submit(
            get_random_title,
            media_type,
            genre_id or None,
            min_rating,
            max_rating,
            min_release_year=min_release_year,
            include_streaming=False,
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

    current_year = timezone.localdate().year
    context = {
        "movie_genres": genre_sets["movie"],
        "tv_genres": genre_sets["tv"],
        "selected_media_type": media_type,
        "selected_genre": genre_id,
        "selected_min_rating": min_rating,
        "selected_max_rating": max_rating,
        "selected_min_release_year": min_release_year,
        "min_release_year_limit": MIN_RELEASE_YEAR,
        "max_release_year_limit": current_year,
        "selected_runtime_filter": runtime_filter,
        "selected_certification": certification,
        "selected_special_category": special_category,
    }
    context.update(_filter_options_context())

    if movie is not None:
        streaming_movie_id = _parse_ascii_int(
            movie.get("id"), maximum=MAX_TMDB_ID
        )
        movie["streaming_deferred"] = bool(
            not movie.get("provider_groups")
            and movie.get("media_type") in {Title.MOVIE, Title.TV}
            and streaming_movie_id is not None
        )
        visitor_id = _visitor_id(request, create=request.user.is_authenticated)
        genre_name = _genre_name(genre_sets, media_type, genre_id)
        if request.user.is_authenticated:
            saved_title = record_generation(
                visitor_id,
                movie,
                genre_id or None,
                genre_name,
                min_rating,
                user=request.user,
            )
        else:
            # O historico anonimo pertence ao navegador. Consultamos um snapshot
            # existente apenas para refletir o estado de favorito, sem gravar o
            # sorteio ou atualizar o titulo no Neon.
            movie_id = _parse_ascii_int(movie.get("id"), maximum=MAX_TMDB_ID)
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
        movie["is_favorite"] = is_favorite(
            visitor_id,
            saved_title,
            user=request.user,
        )
        context["movie"] = movie
    elif movie_error:
        context["error"] = movie_error

    if genres_error and "error" not in context:
        context["error"] = genres_error
    context["trending_movies"] = rows["movie"]
    context["trending_series"] = rows["tv"]
    context["now_playing_movies"] = rows["now_playing"]
    context["upcoming_movies"] = rows["upcoming"]
    context["trends_error"] = row_errors["movie"]
    context["series_trends_error"] = row_errors["tv"]
    context["now_playing_error"] = row_errors["now_playing"]
    context["upcoming_error"] = row_errors["upcoming"]
    context.update(
        get_library(
            _visitor_id(request),
            user=request.user,
            include_favorites=False,
        )
    )
    return render(request, "movies/home.html", context)


@require_GET
@rate_limit("streaming-links", ip=(60, 300), user=(45, 300), methods={"GET"})
def streaming_links(_request, media_type, tmdb_id):
    if media_type not in {Title.MOVIE, Title.TV}:
        return JsonResponse({"error": "Tipo de título inválido."}, status=400)
    try:
        groups = get_streaming_groups(media_type, tmdb_id)
    except WatchmodeError as exc:
        return JsonResponse({"groups": [], "error": str(exc)}, status=503)
    response = JsonResponse({"groups": groups})
    response["Cache-Control"] = "private, max-age=21600"
    return response


@require_GET
@rate_limit("title-detail", ip=(120, 300), user=(90, 300), methods={"GET"})
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
        movie = get_title_details(media_type, tmdb_id, include_streaming=False)
        movie["streaming_deferred"] = True
        visitor_id = _visitor_id(request)
        saved_title = Title.objects.filter(
            media_type=media_type,
            tmdb_id=tmdb_id,
        ).first()
        # A persistencia, quando necessaria, ocorre apenas no POST de favorito.
        movie["can_favorite"] = True
        movie["is_favorite"] = is_favorite(
            visitor_id,
            saved_title,
            user=request.user,
        )
        context["movie"] = movie
    except TMDBNotFound as exc:
        context["error"] = str(exc)
        context["seo_noindex_override"] = True
        return render(request, "movies/home.html", context, status=404)
    except TMDBError as exc:
        context["error"] = str(exc)
        context["seo_noindex_override"] = True
        return render(request, "movies/home.html", context, status=503)
    return render(request, "movies/home.html", context)


@require_POST
@rate_limit("favorite", ip=(60, 300), user=(40, 300), methods={"POST"})
def toggle_title_favorite(request):
    media_type = request.POST.get("media_type", "")
    tmdb_id = _parse_ascii_int(
        request.POST.get("tmdb_id", ""), maximum=MAX_TMDB_ID
    )
    if media_type not in {Title.MOVIE, Title.TV} or tmdb_id is None:
        return JsonResponse({"error": "Título inválido."}, status=400)

    visitor_id = _visitor_id(request, create=True)
    title = Title.objects.filter(media_type=media_type, tmdb_id=tmdb_id).first()
    if title is None:
        try:
            title_data = get_title_details(
                media_type,
                tmdb_id,
                include_streaming=False,
            )
        except TMDBError as exc:
            return JsonResponse({"error": str(exc)}, status=503)
        title = save_title_snapshot(title_data)
    if title is None:
        return JsonResponse({"error": "Titulo invalido."}, status=400)
    favorited = toggle_favorite(visitor_id, title, user=request.user)
    return JsonResponse(
        {
            "favorited": favorited,
            "message": (
                "Adicionado à minha lista." if favorited else "Removido da minha lista."
            ),
        }
    )
