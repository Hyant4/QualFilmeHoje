"""Vocabulário permitido pelo filtro de IA.

Os filtros efetivos do TMDB continuam no serviço de descoberta. Este módulo
deriva deles o catálogo que o Gemini e o mapeador podem usar, para que uma
chave sem suporte em filme ou série nunca seja anunciada ao modelo.
"""

from movies.services.tmdb_discovery import SPECIAL_CATEGORIES

REGULAR_GENRE_VALUES = {
    "movie": {
        "action": "28",
        "adventure": "12",
        "animation": "16",
        "comedy": "35",
        "crime": "80",
        "documentary": "99",
        "drama": "18",
        "family": "10751",
        "fantasy": "14",
        "history": "36",
        "horror": "27",
        "music": "10402",
        "mystery": "9648",
        "romance": "10749",
        "science_fiction": "878",
        "thriller": "53",
        "war": "10752",
        "western": "37",
    },
    "tv": {
        "action": "10759",
        "adventure": "10759",
        "animation": "16",
        "comedy": "35",
        "crime": "80",
        "documentary": "99",
        "drama": "18",
        "family": "10751",
        "fantasy": "10765",
        "mystery": "9648",
        "science_fiction": "10765",
        "war": "10768",
        "western": "37",
    },
}

PROFILE_ALIASES = {
    "movie": {
        "korean_thriller": ("thriller coreano", "filme coreano de suspense"),
        "korean_romance": ("romance coreano", "filme romântico coreano"),
        "space_exploration": (
            "filme espacial",
            "exploração espacial",
            "astronautas",
        ),
    },
    "tv": {
        "korean_drama": ("dorama", "drama coreano"),
        "korean_thriller": (
            "suspense coreano",
            "thriller coreano",
            "série coreana de mistério",
            "dorama policial",
        ),
        "korean_romance": ("dorama romântico", "romance coreano"),
        "space_exploration": (
            "série espacial",
            "exploração espacial",
            "astronautas",
        ),
    },
}


def available_genre_keys():
    keys = set()
    for media_type, genres in REGULAR_GENRE_VALUES.items():
        keys.update(genres)
        keys.update(SPECIAL_CATEGORIES[media_type])
    return tuple(sorted(keys))


def is_supported_genre_key(media_type, genre_key):
    return genre_key in REGULAR_GENRE_VALUES.get(
        media_type, {}
    ) or genre_key in SPECIAL_CATEGORIES.get(media_type, {})


def profile_prompt_guidance():
    lines = []
    for media_type, profiles in PROFILE_ALIASES.items():
        content_type = "filmes" if media_type == "movie" else "séries"
        for key, aliases in profiles.items():
            if key not in SPECIAL_CATEGORIES[media_type]:
                raise RuntimeError(f"Perfil inválido: {media_type}/{key}")
            quoted_aliases = ", ".join(f'"{alias}"' for alias in aliases)
            lines.append(f"- {key} ({content_type}): {quoted_aliases}.")
    return "\n".join(lines)
