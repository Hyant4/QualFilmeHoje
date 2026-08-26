"""Mapeia a intenção da IA para os valores permitidos pelo formulário."""

from .filter_catalog import (
    REGULAR_GENRE_VALUES,
    SPECIAL_CATEGORIES,
    is_supported_genre_key,
)
from .schemas import FilterIntent, FilterSuggestion


class UnsupportedFilterIntent(ValueError):
    """A preferência é válida, mas a tela não pode aplicá-la para essa mídia."""


def _genre_value(media_type, genre_key):
    if not media_type or not genre_key:
        return None
    if not is_supported_genre_key(media_type, genre_key):
        raise UnsupportedFilterIntent(f"Filtro não suportado: {media_type}/{genre_key}")
    if genre_key in SPECIAL_CATEGORIES[media_type]:
        return f"special:{genre_key}"
    return REGULAR_GENRE_VALUES[media_type].get(genre_key)


def map_intent_to_suggestion(intent: FilterIntent) -> FilterSuggestion:
    """Descarta combinações que a tela atual não consegue representar."""

    media_type = intent.media_type
    return FilterSuggestion(
        media_type=media_type,
        genre_value=_genre_value(media_type, intent.genre_key),
        min_release_year=intent.min_release_year,
        min_rating=intent.min_rating,
        max_rating=intent.max_rating,
        runtime_filter=intent.runtime_filter,
        certification=(intent.certification if media_type == "movie" else None),
    )
