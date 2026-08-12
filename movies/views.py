import json
import logging
import math
import uuid
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlsplit, urlunsplit

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from .models import Title
from .security import rate_limit
from .services.library import (
    get_library,
    is_favorite,
    record_generation,
    save_title_snapshot,
    toggle_favorite,
)
from .services.tmdb import (
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

DEFAULT_MIN_RATING = 6.0
DEFAULT_MAX_RATING = 10.0
MIN_RELEASE_YEAR = 1900
MAX_GENRE_ID = 999_999
MAX_TMDB_ID = 2_147_483_647
CSP_REPORT_MAX_BYTES = 16 * 1024
logger = logging.getLogger(__name__)


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

    genre_value = request.POST.get("genre_id", "")
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
    return media_type, genre_id, min_rating, max_rating, min_release_year


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
    context.update(get_library(_visitor_id(request), user=request.user))
    return render(request, "movies/home.html", context)


@require_POST
@rate_limit("generate", ip=(30, 300), user=(20, 300), methods={"POST"})
def generate_movie(request):
    media_type, genre_id, min_rating, max_rating, min_release_year = _parse_filters(
        request
    )
    genre_sets, genres_error = _safe_genres()
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
    }

    try:
        movie = get_random_title(
            media_type,
            genre_id or None,
            min_rating,
            max_rating,
            min_release_year=min_release_year,
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
        movie = get_title_details(media_type, tmdb_id)
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
