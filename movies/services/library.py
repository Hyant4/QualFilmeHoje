"""Persistência dos títulos sorteados e da lista do visitante."""

from datetime import date
from decimal import Decimal, InvalidOperation

from django.db import transaction

from ..models import Favorite, Generation, Title
from .urls import TMDB_IMAGE_HOSTS, safe_https_url

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
    if not rating.is_finite():
        return None
    return rating if Decimal(0) <= rating <= Decimal(10) else None


def _account_user(user):
    return user if getattr(user, "is_authenticated", False) else None


def save_title_snapshot(title_data):
    """Cria ou atualiza o snapshot mínimo de um título vindo do TMDB."""
    try:
        raw_id = str(title_data["id"]).strip()
        if (
            not raw_id
            or len(raw_id) > 10
            or not raw_id.isascii()
            or not raw_id.isdecimal()
        ):
            return None
        tmdb_id = int(raw_id)
    except (KeyError, TypeError, ValueError):
        return None
    if not 1 <= tmdb_id <= 2_147_483_647:
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
            "poster_url": safe_https_url(
                title_data.get("poster_url"), TMDB_IMAGE_HOSTS
            ),
            "release_date": _parse_date(title_data.get("release_date")),
            "vote_average": _parse_rating(title_data.get("vote_average")),
        },
    )
    return title


@transaction.atomic
def record_generation(
    visitor_id,
    title_data,
    genre_id,
    genre_name,
    min_rating,
    *,
    user=None,
):
    """Atualiza um snapshot mínimo do TMDB e registra um sorteio."""

    title = save_title_snapshot(title_data)
    if title is None:
        return None

    account_user = _account_user(user)
    Generation.objects.create(
        visitor_id=visitor_id,
        user=account_user,
        title=title,
        genre_id=(
            int(genre_id)
            if genre_id
            and str(genre_id).isascii()
            and str(genre_id).isdecimal()
            and 1 <= int(genre_id) <= 2_147_483_647
            else None
        ),
        genre_name=(genre_name or "")[:100],
        min_rating=_parse_rating(min_rating) or Decimal(0),
    )

    generations = Generation.objects.filter(user=account_user) if account_user else (
        Generation.objects.filter(visitor_id=visitor_id, user__isnull=True)
    )
    stale_ids = list(generations.values_list("pk", flat=True)[HISTORY_STORAGE_LIMIT:])
    if stale_ids:
        Generation.objects.filter(pk__in=stale_ids).delete()
    return title


def get_library(visitor_id, *, user=None):
    account_user = _account_user(user)
    if not visitor_id and not account_user:
        return {"history": [], "favorites": []}

    generation_filter = {"user": account_user} if account_user else {
        "visitor_id": visitor_id,
        "user__isnull": True,
    }
    favorite_filter = {"user": account_user} if account_user else {
        "visitor_id": visitor_id,
        "user__isnull": True,
    }
    history = list(
        Generation.objects.filter(**generation_filter)
        .select_related("title")[:HISTORY_DISPLAY_LIMIT]
    )
    favorites = list(
        Favorite.objects.filter(**favorite_filter)
        .select_related("title")[:HISTORY_DISPLAY_LIMIT]
    )
    return {"history": history, "favorites": favorites}


def is_favorite(visitor_id, title, *, user=None):
    account_user = _account_user(user)
    return bool(
        (visitor_id or account_user)
        and title
        and Favorite.objects.filter(
            **(
                {"user": account_user, "title": title}
                if account_user
                else {
                    "visitor_id": visitor_id,
                    "user__isnull": True,
                    "title": title,
                }
            )
        ).exists()
    )


@transaction.atomic
def toggle_favorite(visitor_id, title, *, user=None):
    account_user = _account_user(user)
    lookup = (
        {"user": account_user, "title": title}
        if account_user
        else {"visitor_id": visitor_id, "user__isnull": True, "title": title}
    )
    favorite, created = Favorite.objects.get_or_create(
        **lookup,
        defaults={"visitor_id": visitor_id},
    )
    if not created:
        favorite.delete()
        return False
    return True


@transaction.atomic
def merge_visitor_library(visitor_id, user):
    """Transfere a biblioteca anônima do navegador para a conta autenticada."""

    account_user = _account_user(user)
    if not visitor_id or not account_user:
        return

    Generation.objects.filter(
        visitor_id=visitor_id,
        user__isnull=True,
    ).update(user=account_user)

    anonymous_favorites = list(
        Favorite.objects.select_for_update().filter(
            visitor_id=visitor_id,
            user__isnull=True,
        )
    )
    for favorite in anonymous_favorites:
        duplicate_exists = Favorite.objects.filter(
            user=account_user,
            title_id=favorite.title_id,
        ).exclude(pk=favorite.pk).exists()
        if duplicate_exists:
            favorite.delete()
        else:
            favorite.user = account_user
            favorite.save(update_fields=("user",))
