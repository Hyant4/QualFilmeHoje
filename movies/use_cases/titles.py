"""Casos de uso de detalhe, streaming e favoritos de um título."""

from movies.models import Title
from movies.services.tmdb import TMDBError, TMDBNotFound
from movies.services.watchmode import WatchmodeError

from .home import MAX_TMDB_ID, parse_ascii_int


def build_title_detail_context(
    media_type,
    tmdb_id,
    *,
    user,
    visitor_id,
    get_title_details,
    is_favorite,
):
    if media_type not in {Title.MOVIE, Title.TV}:
        return (
            {
                "is_detail_page": True,
                "error": "Tipo de título inválido.",
                "selected_media_type": "movie",
            },
            404,
        )

    context = {
        "is_detail_page": True,
        "selected_media_type": media_type,
    }
    try:
        movie = get_title_details(media_type, tmdb_id, include_streaming=False)
        movie["streaming_deferred"] = True
        saved_title = Title.objects.filter(
            media_type=media_type,
            tmdb_id=tmdb_id,
        ).first()
        movie["can_favorite"] = True
        movie["is_favorite"] = is_favorite(visitor_id, saved_title, user=user)
        context["movie"] = movie
    except TMDBNotFound as exc:
        context["error"] = str(exc)
        context["seo_noindex_override"] = True
        return context, 404
    except TMDBError as exc:
        context["error"] = str(exc)
        context["seo_noindex_override"] = True
        return context, 503
    return context, 200


def get_streaming_payload(
    media_type,
    tmdb_id,
    *,
    title_validator,
    streaming_getter,
):
    if media_type not in {Title.MOVIE, Title.TV}:
        return {"error": "Tipo de título inválido."}, 400
    try:
        # Reaproveita o cache da página de detalhes e impede que IDs não
        # confirmados pelo catálogo do TMDB cheguem à Watchmode.
        title_validator(media_type, tmdb_id, include_streaming=False)
    except TMDBNotFound as exc:
        return {"groups": [], "error": str(exc)}, 404
    except TMDBError as exc:
        return {"groups": [], "error": str(exc)}, 503
    try:
        groups = streaming_getter(media_type, tmdb_id)
    except WatchmodeError as exc:
        return {"groups": [], "error": str(exc)}, 503
    return {"groups": groups}, 200


def toggle_title_favorite(
    payload,
    *,
    user,
    resolve_visitor_id,
    get_title_details,
    save_title_snapshot,
    toggle_favorite,
):
    media_type = payload.get("media_type", "")
    tmdb_id = parse_ascii_int(payload.get("tmdb_id", ""), maximum=MAX_TMDB_ID)
    if media_type not in {Title.MOVIE, Title.TV} or tmdb_id is None:
        return {"error": "Título inválido."}, 400

    visitor_id = resolve_visitor_id(create=True)
    title = Title.objects.filter(media_type=media_type, tmdb_id=tmdb_id).first()
    if title is None:
        try:
            title_data = get_title_details(
                media_type,
                tmdb_id,
                include_streaming=False,
            )
        except TMDBError as exc:
            return {"error": str(exc)}, 503
        title = save_title_snapshot(title_data)
    if title is None:
        return {"error": "Título inválido."}, 400
    favorited = toggle_favorite(visitor_id, title, user=user)
    return (
        {
            "favorited": favorited,
            "message": (
                "Adicionado à minha lista."
                if favorited
                else "Removido da minha lista."
            ),
        },
        200,
    )
