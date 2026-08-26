"""Descoberta e seleção aleatória de títulos do TMDB."""

import hashlib
import json
from concurrent.futures import ThreadPoolExecutor

from django.core.cache import cache
from django.utils import timezone

from .tmdb_client import TMDBError
from .tmdb_payloads import (
    MAX_TMDB_ID,
    as_list,
    normalise_rating,
    safe_nonnegative_int,
    validate_title_id,
)
from .watchmode import WatchmodeError

DISCOVERY_CACHE_SECONDS = 30 * 60
MAX_STREAMING_CANDIDATES = 2
MIN_RELEASE_YEAR = 1900

RUNTIME_FILTERS = {
    "up_to_90": (None, 90),
    "90_to_120": (90, 120),
    "over_120": (120, None),
}

# Temas prometem um assunto específico, portanto não podem depender somente de
# gêneros amplos. Os filtros regionais e os gêneros do TMDB continuam podendo
# ser representados sem uma keyword fixa.
THEME_CATEGORY_KEYS = frozenset(
    {
        "korean_romance",
        "anime",
        "space_exploration",
        "time_travel",
        "superhero",
        "survival",
        "heist",
        "true_story",
        "road_trip",
        "coming_of_age",
        "psychological_horror",
        "post_apocalyptic",
        "zombie",
        "found_footage",
        "courtroom_drama",
    }
)

SPECIAL_CATEGORIES = {
    "movie": {
        "korean_thriller": {
            "label": "Thriller coreano",
            "with_origin_country": "KR",
            "with_original_language": "ko",
            "with_genres": "53",
        },
        "korean_romance": {
            "label": "Romance coreano",
            "with_origin_country": "KR",
            "with_original_language": "ko",
            "with_genres": "10749",
            "with_keywords": "9840",
        },
        "anime": {
            "label": "Anime",
            "with_origin_country": "JP",
            "with_original_language": "ja",
            "with_genres": "16",
            "with_keywords": "210024",
        },
        "japanese_horror": {
            "label": "Terror japonês",
            "with_origin_country": "JP",
            "with_original_language": "ja",
            "with_genres": "27",
        },
        "brazilian_cinema": {
            "label": "Cinema brasileiro",
            "with_origin_country": "BR",
            "with_original_language": "pt",
        },
        "space_exploration": {
            "label": "Espaço e exploração espacial",
            "with_genres": "878",
            "with_keywords": "3801",
        },
        "time_travel": {
            "label": "Viagem no tempo",
            "with_keywords": "4379",
        },
        "superhero": {
            "label": "Super-heróis",
            "with_keywords": "9715",
        },
        "survival": {
            "label": "Sobrevivência",
            "with_keywords": "10349",
        },
        "heist": {
            "label": "Assaltos e golpes",
            "with_keywords": "10051",
        },
        "true_story": {
            "label": "Baseado em fatos reais",
            "with_keywords": "9672",
        },
        "road_trip": {
            "label": "Viagem de estrada",
            "with_keywords": "7312",
        },
        "coming_of_age": {
            "label": "Amadurecimento",
            "with_keywords": "10683",
        },
        "psychological_horror": {
            "label": "Terror psicológico",
            "with_genres": "27",
            "with_keywords": "295907",
        },
        "post_apocalyptic": {
            "label": "Pós-apocalipse",
            "with_keywords": "4458",
        },
        "zombie": {
            "label": "Zumbis",
            "with_genres": "27",
            "with_keywords": "12377",
        },
        "found_footage": {
            "label": "Found footage",
            "with_genres": "27",
            "with_keywords": "163053",
        },
        "courtroom_drama": {
            "label": "Drama de tribunal",
            "with_genres": "18",
            "with_keywords": "214780",
        },
    },
    "tv": {
        "korean_drama": {
            "label": "Dorama coreano",
            "with_origin_country": "KR",
            "with_original_language": "ko",
            "with_genres": "18",
        },
        "korean_thriller": {
            "label": "Suspense coreano",
            "with_origin_country": "KR",
            "with_original_language": "ko",
            "with_genres": "9648",
            "with_keywords": "288394",
        },
        "korean_romance": {
            "label": "Dorama romântico",
            "with_origin_country": "KR",
            "with_original_language": "ko",
            "with_genres": "18",
            "with_keywords": "9840",
            "without_genres": "10759",
        },
        "anime": {
            "label": "Anime",
            "with_origin_country": "JP",
            "with_original_language": "ja",
            "with_genres": "16",
            "with_keywords": "210024",
        },
        "brazilian_drama": {
            "label": "Drama brasileiro",
            "with_origin_country": "BR",
            "with_original_language": "pt",
            "with_genres": "18",
        },
        "space_exploration": {
            "label": "Espaço e exploração espacial",
            "with_genres": "10765",
            "with_keywords": "3801",
        },
        "time_travel": {
            "label": "Viagem no tempo",
            "with_keywords": "4379",
        },
        "superhero": {
            "label": "Super-heróis",
            "with_keywords": "9715",
        },
        "survival": {
            "label": "Sobrevivência",
            "with_keywords": "10349",
        },
        "true_story": {
            "label": "Baseado em fatos reais",
            "with_keywords": "9672",
        },
        "coming_of_age": {
            "label": "Amadurecimento",
            "with_keywords": "10683",
        },
        "post_apocalyptic": {
            "label": "Pós-apocalipse",
            "with_keywords": "4458",
        },
        "zombie": {
            "label": "Zumbis",
            "with_genres": "10765",
            "with_keywords": "12377",
        },
        "courtroom_drama": {
            "label": "Drama de tribunal",
            "with_genres": "18",
            "with_keywords": "214780",
        },
    },
}

BRAZIL_CERTIFICATIONS = {"L", "10", "12", "14", "16", "18"}


def _category_cache_signature(media_type, special_category):
    """Muda a chave de cache quando os filtros de uma categoria mudam."""

    category = SPECIAL_CATEGORIES.get(media_type, {}).get(special_category)
    if category is None:
        return "none"
    encoded = json.dumps(
        category,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()[:12]


def discovery_cache_key(
    media_type,
    genre_id,
    min_rating,
    max_rating,
    min_release_year=None,
    max_release_year=None,
    runtime_filter=None,
    certification=None,
    special_category=None,
):
    genre_key = genre_id or "all"
    min_key = f"{min_rating:.1f}".replace(".", "-")
    max_key = f"{max_rating:.1f}".replace(".", "-")
    min_year_key = min_release_year or "all"
    max_year_key = max_release_year or "all"
    runtime_key = runtime_filter or "any"
    certification_key = certification or "any"
    category_key = special_category or "any"
    category_signature = _category_cache_signature(media_type, special_category)
    return (
        f"tmdb:discover:v6:{media_type}:{genre_key}:{min_key}:{max_key}:"
        f"{min_year_key}:{max_year_key}:{runtime_key}:{certification_key}:"
        f"{category_key}:{category_signature}"
    )


def find_streaming_candidate(media_type, candidates, *, streaming_getter):
    streaming_error = None
    for candidate in candidates[:MAX_STREAMING_CANDIDATES]:
        if not isinstance(candidate, dict):
            continue
        try:
            title_id = validate_title_id(candidate.get("id"))
            groups = streaming_getter(media_type, title_id)
        except WatchmodeError as error:
            streaming_error = str(error)
            break
        except TMDBError:
            continue
        if groups:
            return title_id, groups, None
    return validate_title_id(candidates[0]["id"]), [], streaming_error


def discovery_candidates(results):
    candidates = []
    for item in as_list(results):
        if not isinstance(item, dict):
            continue
        try:
            title_id = validate_title_id(item.get("id"))
        except TMDBError:
            continue
        candidates.append({"id": title_id})
    return candidates


def load_discovery_page(
    media_type,
    genre_id,
    min_rating,
    max_rating,
    filters,
    min_release_year=None,
    max_release_year=None,
    runtime_filter=None,
    certification=None,
    special_category=None,
    *,
    fetch,
    randint,
):
    cache_key = discovery_cache_key(
        media_type,
        genre_id,
        min_rating,
        max_rating,
        min_release_year,
        max_release_year,
        runtime_filter,
        certification,
        special_category,
    )
    pool_cache_key = f"{cache_key}:candidate-pool"
    cached_pool = cache.get(pool_cache_key)
    if cached_pool is not None:
        return cached_pool

    first_page = cache.get(cache_key)
    if first_page is None:
        first_page = fetch(f"/discover/{media_type}", page=1, **filters)
        cache.set(cache_key, first_page, DISCOVERY_CACHE_SECONDS)

    total_results = safe_nonnegative_int(first_page.get("total_results"))
    first_results = discovery_candidates(first_page.get("results"))
    if not total_results or not first_results:
        content_name = "séries" if media_type == "tv" else "filmes"
        raise TMDBError(
            f"Não encontrei {content_name} para esses filtros. "
            "Diminua a nota, escolha outro gênero ou altere o ano."
        )

    try:
        total_pages = int(first_page.get("total_pages", 1))
    except (TypeError, ValueError, OverflowError):
        total_pages = 1
    total_pages = min(max(total_pages, 1), 500)
    if total_pages == 1:
        cache.set(pool_cache_key, first_results, DISCOVERY_CACHE_SECONDS)
        return first_results

    page_number = randint(1, total_pages)
    page_cache_key = f"{cache_key}:page:{page_number}"
    page_data = cache.get(page_cache_key)
    if page_data is None:
        page_data = fetch(f"/discover/{media_type}", page=page_number, **filters)
        cache.set(page_cache_key, page_data, DISCOVERY_CACHE_SECONDS)

    candidates = first_results + discovery_candidates(page_data.get("results"))
    unique_candidates = []
    seen_ids = set()
    for candidate in candidates:
        title_id = candidate["id"]
        if title_id in seen_ids:
            continue
        seen_ids.add(title_id)
        unique_candidates.append(candidate)
    candidate_pool = unique_candidates or first_results
    cache.set(pool_cache_key, candidate_pool, DISCOVERY_CACHE_SECONDS)
    return candidate_pool


def get_random_title(
    media_type="movie",
    genre_id=None,
    min_rating=0,
    max_rating=10,
    min_release_year=None,
    max_release_year=None,
    *,
    include_streaming=True,
    runtime_filter=None,
    certification=None,
    special_category=None,
    load_page,
    sample,
    fetch_title,
    payload_builder,
    streaming_getter,
):
    if media_type not in {"movie", "tv"}:
        media_type = "movie"

    min_rating = normalise_rating(min_rating)
    max_rating = max(normalise_rating(max_rating), min_rating)
    current_year = timezone.localdate().year
    if min_release_year is not None:
        try:
            min_release_year = int(min_release_year)
        except (TypeError, ValueError, OverflowError):
            min_release_year = MIN_RELEASE_YEAR
        min_release_year = min(max(min_release_year, MIN_RELEASE_YEAR), current_year)
    if max_release_year is not None:
        try:
            max_release_year = int(max_release_year)
        except (TypeError, ValueError, OverflowError):
            max_release_year = current_year
        max_release_year = min(max(max_release_year, MIN_RELEASE_YEAR), current_year)
    if min_release_year is not None and max_release_year is not None:
        max_release_year = max(max_release_year, min_release_year)
    if genre_id is not None:
        genre_value = str(genre_id).strip()
        if (
            not genre_value
            or len(genre_value) > 10
            or not genre_value.isascii()
            or not genre_value.isdecimal()
        ):
            genre_id = None
        else:
            parsed_genre_id = int(genre_value)
            genre_id = (
                str(parsed_genre_id) if 1 <= parsed_genre_id <= MAX_TMDB_ID else None
            )
    runtime_filter = runtime_filter if runtime_filter in RUNTIME_FILTERS else None
    certification = str(certification or "").strip().upper()
    if media_type != "movie" or certification not in BRAZIL_CERTIFICATIONS:
        certification = None
    category_filters = SPECIAL_CATEGORIES.get(media_type, {}).get(special_category)
    if category_filters is None:
        special_category = None
    filters = {
        "language": "pt-BR",
        "include_adult": "false",
        "watch_region": "BR",
        "with_watch_monetization_types": "flatrate|free|ads|rent|buy",
        "vote_average.gte": min_rating,
        "vote_average.lte": max_rating,
        "vote_count.gte": 50,
        "sort_by": "popularity.desc",
    }
    if media_type == "movie":
        filters["include_video"] = "false"
        if min_release_year is not None:
            filters["primary_release_date.gte"] = f"{min_release_year}-01-01"
        if max_release_year is not None:
            filters["primary_release_date.lte"] = f"{max_release_year}-12-31"
    else:
        if min_release_year is not None:
            filters["first_air_date.gte"] = f"{min_release_year}-01-01"
        if max_release_year is not None:
            filters["first_air_date.lte"] = f"{max_release_year}-12-31"
    if category_filters:
        filters.update(
            {key: value for key, value in category_filters.items() if key != "label"}
        )
    category_genre = filters.get("with_genres")
    if genre_id:
        filters["with_genres"] = (
            f"{genre_id},{category_genre}"
            if category_genre and category_genre != genre_id
            else genre_id
        )
    if runtime_filter:
        runtime_min, runtime_max = RUNTIME_FILTERS[runtime_filter]
        if runtime_min is not None:
            filters["with_runtime.gte"] = runtime_min
        if runtime_max is not None:
            filters["with_runtime.lte"] = runtime_max
    if certification:
        filters.update(
            {
                "region": "BR",
                "certification_country": "BR",
                "certification": certification,
            }
        )

    results = load_page(
        media_type,
        genre_id,
        min_rating,
        max_rating,
        filters,
        min_release_year,
        max_release_year,
        runtime_filter,
        certification,
        special_category,
    )
    candidates = sample(results, k=min(MAX_STREAMING_CANDIDATES, len(results)))
    first_title_id = candidates[0]["id"]

    if not include_streaming:
        data = fetch_title(first_title_id, media_type)
        return payload_builder(data, media_type)

    with ThreadPoolExecutor(max_workers=2) as executor:
        first_details_future = executor.submit(fetch_title, first_title_id, media_type)
        streaming_future = executor.submit(
            find_streaming_candidate,
            media_type,
            candidates,
            streaming_getter=streaming_getter,
        )
        title_id, provider_groups, streaming_error = streaming_future.result()
        if title_id == first_title_id:
            data = first_details_future.result()
        else:
            data = fetch_title(title_id, media_type)
    return payload_builder(data, media_type, provider_groups, streaming_error)
