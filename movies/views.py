import json
import logging
import uuid
from urllib.parse import urlsplit, urlunsplit

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

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
    get_genres,
    get_now_playing_movies,
    get_random_title,
    get_recent_top_movies,
    get_recent_top_series,
    get_title_details,
    get_upcoming_movies,
)
from .services.watchmode import get_streaming_groups
from .use_cases import home as home_use_cases
from .use_cases import titles as title_use_cases
from .use_cases.filter_interpretation import (
    FilterInterpretationUnavailable,
    FilterInterpretationUnsupported,
    InvalidFilterInput,
    interpret_text_filter,
)

CSP_REPORT_MAX_BYTES = 16 * 1024
AI_FILTER_REQUEST_MAX_BYTES = 4 * 1024
logger = logging.getLogger(__name__)


@require_GET
def robots_txt(_request):
    lines = (
        "User-agent: *",
        "Allow: /",
        "Disallow: /admin/",
        "Disallow: /security/",
        "Disallow: /api/",
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
    context = home_use_cases.build_home_context(
        user=request.user,
        visitor_id=_visitor_id(request),
        get_library=get_library,
        get_genres=get_genres,
        get_recent_top_movies=get_recent_top_movies,
        get_recent_top_series=get_recent_top_series,
        get_now_playing_movies=get_now_playing_movies,
        get_upcoming_movies=get_upcoming_movies,
    )
    return render(request, "movies/home.html", context)


@require_POST
@rate_limit("generate", ip=(30, 300), user=(20, 300), methods={"POST"})
def generate_movie(request):
    context = home_use_cases.build_generation_context(
        payload=request.POST,
        user=request.user,
        resolve_visitor_id=lambda *, create: _visitor_id(request, create=create),
        get_library=get_library,
        get_genres=get_genres,
        get_recent_top_movies=get_recent_top_movies,
        get_recent_top_series=get_recent_top_series,
        get_now_playing_movies=get_now_playing_movies,
        get_upcoming_movies=get_upcoming_movies,
        get_random_title=get_random_title,
        record_generation=record_generation,
        is_favorite=is_favorite,
    )
    return render(request, "movies/home.html", context)


def _ai_filter_response(payload, *, status=200):
    response = JsonResponse(payload, status=status)
    response["Cache-Control"] = "no-store"
    response["X-Content-Type-Options"] = "nosniff"
    response["X-Robots-Tag"] = "noindex, nofollow"
    return response


@require_POST
def interpret_filter(request):
    """Traduz texto curto em valores que ja existem no formulario."""

    if not settings.AI_FILTER_ENABLED:
        return _ai_filter_response({"error": "Recurso indisponível."}, status=404)
    return _interpret_filter_limited(request)


@rate_limit("ai-filter", ip=(6, 300), user=(10, 300), methods={"POST"})
def _interpret_filter_limited(request):
    if request.content_type != "application/json":
        return _ai_filter_response(
            {"error": "Envie apenas um texto curto em JSON."}, status=400
        )

    body = request.body
    if len(body) > AI_FILTER_REQUEST_MAX_BYTES:
        return _ai_filter_response(
            {"error": "O texto enviado é grande demais."}, status=413
        )
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return _ai_filter_response(
            {"error": "Envie apenas um texto curto em JSON."}, status=400
        )
    if not isinstance(payload, dict) or set(payload) != {"texto"}:
        return _ai_filter_response(
            {"error": "Envie apenas um texto curto em JSON."}, status=400
        )

    try:
        suggestion = interpret_text_filter(payload["texto"])
    except InvalidFilterInput:
        return _ai_filter_response(
            {"error": "Escreva uma preferência curta para analisar."}, status=400
        )
    except FilterInterpretationUnsupported:
        return _ai_filter_response(
            {
                "error": (
                    "Entendi a preferência, mas ela ainda não pode ser "
                    "aplicada exatamente nos filtros. Ajuste manualmente."
                )
            },
            status=422,
        )
    except FilterInterpretationUnavailable:
        return _ai_filter_response(
            {
                "error": (
                    "O filtro por IA está temporariamente indisponível. "
                    "Tente de novo em instantes ou ajuste os filtros manualmente."
                )
            },
            status=503,
        )

    return _ai_filter_response(suggestion.public_payload())


@require_GET
@rate_limit("streaming-links", ip=(60, 300), user=(45, 300), methods={"GET"})
def streaming_links(_request, media_type, tmdb_id):
    payload, status = title_use_cases.get_streaming_payload(
        media_type,
        tmdb_id,
        title_validator=get_title_details,
        streaming_getter=get_streaming_groups,
    )
    response = JsonResponse(payload, status=status)
    response["Cache-Control"] = "private, max-age=21600"
    return response


@require_GET
@rate_limit("title-detail", ip=(120, 300), user=(90, 300), methods={"GET"})
def title_detail(request, media_type, tmdb_id):
    context, status = title_use_cases.build_title_detail_context(
        media_type,
        tmdb_id,
        user=request.user,
        visitor_id=_visitor_id(request),
        get_title_details=get_title_details,
        is_favorite=is_favorite,
    )
    return render(request, "movies/home.html", context, status=status)


@require_POST
@rate_limit("favorite", ip=(60, 300), user=(40, 300), methods={"POST"})
def toggle_title_favorite(request):
    payload, status = title_use_cases.toggle_title_favorite(
        request.POST,
        user=request.user,
        resolve_visitor_id=lambda *, create: _visitor_id(request, create=create),
        get_title_details=get_title_details,
        save_title_snapshot=save_title_snapshot,
        toggle_favorite=toggle_favorite,
    )
    return JsonResponse(payload, status=status)
