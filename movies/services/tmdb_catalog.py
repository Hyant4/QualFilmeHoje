"""Consultas de catálogo, detalhes e listas do TMDB."""

from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta

from django.core.cache import cache
from django.utils import timezone

from .tmdb_client import TMDBError, TMDBNotFound
from .tmdb_payloads import (
    MAX_TMDB_ID,
    POSTER_BASE_URL,
    as_dict,
    as_list,
    build_title_payload,
    normalise_rating,
    safe_date,
    safe_nonnegative_int,
    safe_text,
    tmdb_image_url,
    validate_title_id,
)
from .watchmode import WatchmodeError

GENRES_CACHE_SECONDS = 7 * 24 * 60 * 60
TITLE_CACHE_SECONDS = 12 * 60 * 60
TITLE_NOT_FOUND_CACHE_SECONDS = 30 * 60
TRENDS_CACHE_SECONDS = 30 * 60
RELEASE_LISTS_CACHE_SECONDS = 30 * 60
RECENT_RELEASE_DAYS = 30
TRENDS_MIN_VOTES = 20


def get_genres(media_type, *, fetch):
    if media_type not in {"movie", "tv"}:
        media_type = "movie"
    cache_key = f"tmdb:genres:v1:{media_type}:pt-BR"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached
    raw_genres = fetch(f"/genre/{media_type}/list", language="pt-BR").get("genres")
    genres = []
    for genre in as_list(raw_genres):
        if not isinstance(genre, dict):
            continue
        genre_id = safe_nonnegative_int(genre.get("id"), maximum=MAX_TMDB_ID)
        name = safe_text(genre.get("name"), maximum=100)
        if genre_id and name:
            genres.append({"id": genre_id, "name": name})
    cache.set(cache_key, genres, GENRES_CACHE_SECONDS)
    return genres


def fetch_title_extras(title_id, media_type, *, fetch):
    title_id = validate_title_id(title_id)
    cache_key = f"tmdb:title-extras:v2:{media_type}:{title_id}"
    missing_cache_key = f"tmdb:title-missing:v1:{media_type}:{title_id}"
    if cache.get(missing_cache_key):
        raise TMDBNotFound("O título não foi encontrado no TMDB.")
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    credits_key = "aggregate_credits" if media_type == "tv" else "credits"
    try:
        details = fetch(
            f"/{media_type}/{title_id}",
            language="pt-BR",
            append_to_response=f"videos,reviews,{credits_key}",
        )
    except TMDBNotFound:
        cache.set(missing_cache_key, True, TITLE_NOT_FOUND_CACHE_SECONDS)
        raise
    if validate_title_id(details.get("id")) != title_id:
        raise TMDBError("O TMDB devolveu um título diferente do solicitado.")
    data = {
        "details": details,
        "videos": as_dict(details.get("videos")),
        "reviews": as_dict(details.get("reviews")),
        "credits": as_dict(details.get(credits_key)),
    }

    fallback_requests = {}
    if not data["videos"].get("results"):
        fallback_requests["videos"] = (
            f"/{media_type}/{title_id}/videos",
            {"language": "en-US"},
        )
    if not data["reviews"].get("results"):
        fallback_requests["reviews"] = (
            f"/{media_type}/{title_id}/reviews",
            {"language": "en-US", "page": 1},
        )

    if fallback_requests:
        with ThreadPoolExecutor(max_workers=len(fallback_requests)) as executor:
            futures = {
                name: executor.submit(fetch, path, **params)
                for name, (path, params) in fallback_requests.items()
            }
            for name, future in futures.items():
                data[name] = as_dict(future.result())

    cache.set(cache_key, data, TITLE_CACHE_SECONDS)
    return data


def get_title_details(
    media_type,
    title_id,
    *,
    include_streaming,
    fetch_title,
    streaming_getter,
    payload_builder=build_title_payload,
):
    if media_type not in {"movie", "tv"}:
        raise TMDBError("Tipo de título inválido.")
    title_id = validate_title_id(title_id)
    data = fetch_title(title_id, media_type)
    provider_groups = []
    streaming_error = None
    if include_streaming:
        try:
            provider_groups = streaming_getter(media_type, title_id)
        except WatchmodeError as error:
            streaming_error = str(error)
    return payload_builder(data, media_type, provider_groups, streaming_error)


def get_recent_top_titles(media_type, limit, *, fetch):
    if media_type not in {"movie", "tv"}:
        raise TMDBError("Tipo de título inválido.")

    limit = min(max(int(limit), 1), 20)
    today = timezone.localdate()
    cutoff = today - timedelta(days=RECENT_RELEASE_DAYS)
    cache_key = f"tmdb:recent-top:v5:{media_type}:{today.isoformat()}:{limit}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    date_field = "primary_release_date" if media_type == "movie" else "first_air_date"
    filters = {
        "language": "pt-BR",
        "include_adult": "false",
        f"{date_field}.gte": cutoff.isoformat(),
        f"{date_field}.lte": today.isoformat(),
        "vote_count.gte": TRENDS_MIN_VOTES,
        "sort_by": "vote_average.desc",
    }
    if media_type == "movie":
        filters["include_video"] = "false"
    else:
        filters["include_null_first_air_dates"] = "false"

    data = fetch(f"/discover/{media_type}", **filters)
    ranked_results = sorted(
        [item for item in as_list(data.get("results")) if isinstance(item, dict)],
        key=lambda item: (
            normalise_rating(item.get("vote_average")),
            item.get("vote_count") or 0,
        ),
        reverse=True,
    )
    titles = []
    for item in ranked_results:
        try:
            item_id = validate_title_id(item.get("id"))
        except TMDBError:
            continue
        title = safe_text(
            item.get("title") if media_type == "movie" else item.get("name"),
            maximum=255,
        )
        if not title:
            continue
        titles.append(
            {
                "id": item_id,
                "media_type": media_type,
                "title": title,
                "original_title": (
                    safe_text(item.get("original_title"), maximum=255)
                    if media_type == "movie"
                    else safe_text(item.get("original_name"), maximum=255)
                )
                or "",
                "overview": safe_text(item.get("overview"), maximum=5000),
                "release_date": (
                    safe_date(item.get("release_date"))
                    if media_type == "movie"
                    else safe_date(item.get("first_air_date"))
                )
                or "",
                "vote_average": normalise_rating(item.get("vote_average")),
                "vote_count": safe_nonnegative_int(item.get("vote_count")),
                "poster_url": tmdb_image_url(
                    POSTER_BASE_URL, item.get("poster_path")
                ),
            }
        )
        if len(titles) == limit:
            break

    cache.set(cache_key, titles, TRENDS_CACHE_SECONDS)
    return titles


def normalise_release_list_item(item, availability_kind):
    if not isinstance(item, dict):
        return None
    try:
        item_id = validate_title_id(item.get("id"))
    except TMDBError:
        return None
    title = safe_text(item.get("title"), maximum=255)
    if not title:
        return None

    release_date = safe_date(item.get("release_date"))
    try:
        parsed_release_date = date.fromisoformat(release_date)
    except (TypeError, ValueError):
        parsed_release_date = None

    if availability_kind == "cinema":
        availability_label = "Onde assistir · Nos cinemas"
    else:
        availability_label = (
            f"Estreia em {parsed_release_date.strftime('%d/%m/%Y')}"
            if parsed_release_date
            else "Estreia em breve"
        )

    return {
        "id": item_id,
        "media_type": "movie",
        "title": title,
        "original_title": safe_text(item.get("original_title"), maximum=255),
        "overview": safe_text(item.get("overview"), maximum=5000),
        "release_date": release_date,
        "release_date_value": parsed_release_date,
        "vote_average": normalise_rating(item.get("vote_average")),
        "vote_count": safe_nonnegative_int(item.get("vote_count")),
        "poster_url": tmdb_image_url(POSTER_BASE_URL, item.get("poster_path")),
        "availability_kind": availability_kind,
        "availability_label": availability_label,
    }


def get_movie_release_list(list_name, limit, *, fetch):
    if list_name not in {"now_playing", "upcoming"}:
        raise TMDBError("Lista de lançamentos inválida.")

    limit = min(max(int(limit), 1), 20)
    today = timezone.localdate()
    cache_key = f"tmdb:movie-releases:v1:{list_name}:BR:{today.isoformat()}:{limit}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    data = fetch(
        f"/movie/{list_name}",
        language="pt-BR",
        region="BR",
        page=1,
    )
    availability_kind = "cinema" if list_name == "now_playing" else "upcoming"
    titles = []
    seen_ids = set()
    for item in as_list(data.get("results")):
        normalised = normalise_release_list_item(item, availability_kind)
        if not normalised or normalised["id"] in seen_ids:
            continue
        if (
            list_name == "upcoming"
            and (
                normalised["release_date_value"] is None
                or normalised["release_date_value"] <= today
            )
        ):
            continue
        seen_ids.add(normalised["id"])
        titles.append(normalised)

    if list_name == "upcoming":
        titles.sort(
            key=lambda item: (
                item["release_date_value"],
                -(item["vote_count"] or 0),
            )
        )

    for title in titles:
        title.pop("release_date_value", None)
    titles = titles[:limit]
    cache.set(cache_key, titles, RELEASE_LISTS_CACHE_SECONDS)
    return titles
