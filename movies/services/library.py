"""Persistência dos títulos sorteados e da lista do visitante."""

from datetime import date
from decimal import Decimal, InvalidOperation

from django.db import transaction

from ..models import Favorite, Generation, Title

HISTORY_DISPLAY_LIMIT = 8
HISTORY_STORAGE_LIMIT = 50


def _parse_date(value):
    if not value:
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def _parse_rating(value):
    try:
        rating = Decimal(str(value)).quantize(Decimal("0.1"))
    except (InvalidOperation, TypeError, ValueError):
        return None
    return rating if Decimal(0) <= rating <= Decimal(10) else None


@transaction.atomic
def record_generation(visitor_id, title_data, genre_id, genre_name, min_rating):
    """Atualiza um snapshot mínimo do TMDB e registra um sorteio."""

    try:
        tmdb_id = int(title_data["id"])
    except (KeyError, TypeError, ValueError):
        return None

    media_type = title_data.get("media_type", Title.MOVIE)
    if media_type not in {Title.MOVIE, Title.TV}:
        media_type = Title.MOVIE

    title, _created = Title.objects.update_or_create(
        tmdb_id=tmdb_id,
        media_type=media_type,
        defaults={
            "name": str(title_data.get("title") or "Título sem nome")[:255],
            "original_name": str(title_data.get("original_title") or "")[:255],
            "poster_url": str(title_data.get("poster_url") or "")[:500],
            "release_date": _parse_date(title_data.get("release_date")),
            "vote_average": _parse_rating(title_data.get("vote_average")),
        },
    )

    Generation.objects.create(
        visitor_id=visitor_id,
        title=title,
        genre_id=int(genre_id) if genre_id else None,
        genre_name=(genre_name or "")[:100],
        min_rating=_parse_rating(min_rating) or Decimal(0),
    )

    stale_ids = list(
        Generation.objects.filter(visitor_id=visitor_id)
        .values_list("pk", flat=True)[HISTORY_STORAGE_LIMIT:]
    )
    if stale_ids:
        Generation.objects.filter(pk__in=stale_ids).delete()
    return title


def get_library(visitor_id):
    if not visitor_id:
        return {"history": [], "favorites": []}

    history = list(
        Generation.objects.filter(visitor_id=visitor_id)
        .select_related("title")[:HISTORY_DISPLAY_LIMIT]
    )
    favorites = list(
        Favorite.objects.filter(visitor_id=visitor_id)
        .select_related("title")[:HISTORY_DISPLAY_LIMIT]
    )
    return {"history": history, "favorites": favorites}


def is_favorite(visitor_id, title):
    return bool(
        visitor_id
        and title
        and Favorite.objects.filter(visitor_id=visitor_id, title=title).exists()
    )


@transaction.atomic
def toggle_favorite(visitor_id, title):
    favorite, created = Favorite.objects.get_or_create(
        visitor_id=visitor_id,
        title=title,
    )
    if not created:
        favorite.delete()
    return created
