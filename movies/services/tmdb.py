"""Cliente do TMDB usado pelo QualFilmeHoje.

Todas as chamadas são feitas no servidor para que o token nunca chegue ao
navegador do visitante.
"""

import math
import os
import random
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from functools import lru_cache
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request

from django.core.cache import cache
from django.utils import timezone

from .http_client import ExternalResponseError, open_json
from .urls import TMDB_REVIEW_HOSTS, safe_https_url
from .watchmode import WatchmodeError, get_streaming_groups

API_BASE_URL = "https://api.themoviedb.org/3"
POSTER_BASE_URL = "https://image.tmdb.org/t/p/w500"
BACKDROP_BASE_URL = "https://image.tmdb.org/t/p/w1280"
DISCOVERY_CACHE_SECONDS = 10 * 60
TITLE_CACHE_SECONDS = 12 * 60 * 60
TITLE_NOT_FOUND_CACHE_SECONDS = 30 * 60
TRENDS_CACHE_SECONDS = 30 * 60
RELEASE_LISTS_CACHE_SECONDS = 30 * 60
RECENT_RELEASE_DAYS = 30
TRENDS_MIN_VOTES = 20
MAX_STREAMING_CANDIDATES = 2
MAX_TMDB_ID = 2_147_483_647
MIN_RELEASE_YEAR = 1900


class TMDBError(Exception):
    """Erro de integração exibível para o usuário final."""


class TMDBNotFound(TMDBError):
    """O ID foi validado, mas nao existe no catalogo do TMDB."""


def _get(path, **params):
    token = os.getenv("TMDB_ACCESS_TOKEN")
    if not token or token.startswith("cole-seu-token"):
        raise TMDBError("Configure o TMDB_ACCESS_TOKEN no arquivo .env.")

    query = urlencode({key: value for key, value in params.items() if value is not None})
    request = Request(
        f"{API_BASE_URL}{path}?{query}",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "User-Agent": "QualFilmeHoje/1.0",
        },
    )

    try:
        payload = open_json(request, timeout=10)
        if not isinstance(payload, dict):
            raise ExternalResponseError("O TMDB nao retornou um objeto JSON.")
        return payload
    except HTTPError as error:
        if error.code == 404:
            raise TMDBNotFound("O titulo nao foi encontrado no TMDB.") from error
        if error.code == 401:
            message = "O token do TMDB não é válido. Confira o arquivo .env."
        elif error.code == 429:
            message = "Muitas consultas foram feitas. Aguarde um instante e tente novamente."
        else:
            message = "Não foi possível consultar o TMDB agora."
        raise TMDBError(message) from error
    except (URLError, TimeoutError) as error:
        raise TMDBError("O TMDB demorou para responder. Tente novamente.") from error
    except (ExternalResponseError, TypeError) as error:
        raise TMDBError("O TMDB devolveu uma resposta inesperada.") from error


@lru_cache(maxsize=2)
def get_genres(media_type="movie"):
    if media_type not in {"movie", "tv"}:
        media_type = "movie"
    raw_genres = _get(f"/genre/{media_type}/list", language="pt-BR").get("genres")
    genres = []
    for genre in _as_list(raw_genres):
        if not isinstance(genre, dict):
            continue
        genre_id = _safe_nonnegative_int(genre.get("id"), maximum=MAX_TMDB_ID)
        name = _safe_text(genre.get("name"), maximum=100)
        if genre_id and name:
            genres.append({"id": genre_id, "name": name})
    return genres


def _normalise_rating(value):
    try:
        rating = float(value)
    except (TypeError, ValueError):
        return 0.0
    if not math.isfinite(rating):
        return 0.0
    return min(max(rating, 0.0), 10.0)


def _validate_title_id(value):
    value = str(value or "").strip()
    if not value or len(value) > 10 or not value.isascii() or not value.isdecimal():
        raise TMDBError("Titulo invalido.")
    title_id = int(value)
    if not 1 <= title_id <= MAX_TMDB_ID:
        raise TMDBError("Titulo invalido.")
    return title_id


def _as_dict(value):
    return value if isinstance(value, dict) else {}


def _as_list(value):
    return value if isinstance(value, list) else []


def _safe_text(value, *, maximum):
    return str(value)[:maximum] if isinstance(value, str | int | float) else ""


def _tmdb_image_url(base_url, path):
    if not isinstance(path, str) or not re.fullmatch(r"/[A-Za-z0-9._/-]{1,250}", path):
        return ""
    return f"{base_url}{path}"


def _safe_nonnegative_int(value, *, maximum=2_147_483_647):
    if isinstance(value, bool):
        return 0
    try:
        parsed = int(value)
    except (TypeError, ValueError, OverflowError):
        return 0
    return parsed if 0 <= parsed <= maximum else 0


def _safe_date(value):
    value = _safe_text(value, maximum=10)
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError:
        return ""


def _choose_trailer(videos):
    youtube_videos = []
    for video in _as_list(videos):
        if not isinstance(video, dict) or video.get("site") != "YouTube":
            continue
        key = video.get("key")
        if not isinstance(key, str) or not re.fullmatch(r"[A-Za-z0-9_-]{6,20}", key):
            continue
        youtube_videos.append(video)
    if not youtube_videos:
        return None

    def score(video):
        video_type = video.get("type")
        return (
            video_type == "Trailer",
            bool(video.get("official")),
            video_type == "Teaser",
            video.get("size", 0),
        )

    trailer = dict(max(youtube_videos, key=score))
    trailer["embed_url"] = f"https://www.youtube-nocookie.com/embed/{trailer['key']}"
    trailer["youtube_url"] = f"https://www.youtube.com/watch?v={trailer['key']}"
    return trailer


def _normalise_reviews(reviews):
    normalised = []
    for review in _as_list(reviews)[:6]:
        if not isinstance(review, dict):
            continue
        author_details = _as_dict(review.get("author_details"))
        rating = _normalise_rating(author_details.get("rating"))
        normalised.append(
            {
                "id": _safe_text(review.get("id"), maximum=100),
                "author": _safe_text(review.get("author"), maximum=120)
                or "Usuário do TMDB",
                "rating": rating,
                "content": _safe_text(review.get("content"), maximum=5000),
                "created_at": _safe_text(review.get("created_at"), maximum=40),
                "url": safe_https_url(review.get("url"), TMDB_REVIEW_HOSTS),
            }
        )
    return normalised


def _person_names(people, limit=None):
    names = []
    seen = set()
    for person in _as_list(people):
        if not isinstance(person, dict):
            continue
        name = _safe_text(person.get("name"), maximum=120)
        if not name or name in seen:
            continue
        seen.add(name)
        names.append(name)
        if limit and len(names) >= limit:
            break
    return names


def _crew_jobs(person):
    if not isinstance(person, dict):
        return set()
    jobs = {_safe_text(person.get("job"), maximum=60)}
    jobs.update(
        _safe_text(job.get("job"), maximum=60)
        for job in _as_list(person.get("jobs"))
        if isinstance(job, dict)
    )
    return {job for job in jobs if job}


def _normalise_credits(credits, details, media_type):
    credits = _as_dict(credits)
    details = _as_dict(details)
    crew = [person for person in _as_list(credits.get("crew")) if isinstance(person, dict)]
    cast = sorted(
        [person for person in _as_list(credits.get("cast")) if isinstance(person, dict)],
        key=lambda person: (
            person.get("order") if isinstance(person.get("order"), int) else 9999
        ),
    )
    writer_jobs = {"Screenplay", "Writer", "Story", "Teleplay", "Novel", "Characters"}

    if media_type == "tv":
        leadership_label = "Criação"
        leadership = _person_names(details.get("created_by", []), limit=4)
    else:
        leadership_label = "Direção"
        leadership = _person_names(
            [person for person in crew if "Director" in _crew_jobs(person)],
            limit=4,
        )

    writers = _person_names(
        [person for person in crew if _crew_jobs(person) & writer_jobs],
        limit=6,
    )
    main_cast = _person_names(cast, limit=6)

    return [
        {"label": leadership_label, "names": leadership},
        {"label": "Roteiro", "names": writers},
        {"label": "Elenco principal", "names": main_cast},
    ]


def _fetch_title_extras(title_id, media_type):
    title_id = _validate_title_id(title_id)
    cache_key = f"tmdb:title-extras:v2:{media_type}:{title_id}"
    missing_cache_key = f"tmdb:title-missing:v1:{media_type}:{title_id}"
    if cache.get(missing_cache_key):
        raise TMDBNotFound("O titulo nao foi encontrado no TMDB.")
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    credits_key = "aggregate_credits" if media_type == "tv" else "credits"
    try:
        details = _get(
            f"/{media_type}/{title_id}",
            language="pt-BR",
            append_to_response=f"videos,reviews,{credits_key}",
        )
    except TMDBNotFound:
        cache.set(missing_cache_key, True, TITLE_NOT_FOUND_CACHE_SECONDS)
        raise
    if _validate_title_id(details.get("id")) != title_id:
        raise TMDBError("O TMDB devolveu um titulo diferente do solicitado.")
    data = {
        "details": details,
        "videos": _as_dict(details.get("videos")),
        "reviews": _as_dict(details.get("reviews")),
        "credits": _as_dict(details.get(credits_key)),
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
                name: executor.submit(_get, path, **params)
                for name, (path, params) in fallback_requests.items()
            }
            for name, future in futures.items():
                data[name] = _as_dict(future.result())

    cache.set(cache_key, data, TITLE_CACHE_SECONDS)
    return data


def _build_title_payload(data, media_type, provider_groups=None, streaming_error=None):
    """Converte a resposta detalhada do TMDB no formato usado pelas telas."""

    data = _as_dict(data)
    details = _as_dict(data.get("details"))
    title_id = _validate_title_id(details.get("id"))
    name_field = "name" if media_type == "tv" else "title"
    original_field = "original_name" if media_type == "tv" else "original_title"
    date_field = "first_air_date" if media_type == "tv" else "release_date"
    genres = []
    for genre in _as_list(details.get("genres"))[:20]:
        if not isinstance(genre, dict):
            continue
        genre_name = _safe_text(genre.get("name"), maximum=100)
        if genre_name:
            genres.append(
                {
                    "id": _safe_nonnegative_int(
                        genre.get("id"), maximum=MAX_TMDB_ID
                    ),
                    "name": genre_name,
                }
            )

    title = {
        "id": title_id,
        "media_type": media_type,
        "media_label": "Série" if media_type == "tv" else "Filme",
        "title": _safe_text(details.get(name_field), maximum=255)
        or "Título sem nome",
        "original_title": _safe_text(details.get(original_field), maximum=255),
        "release_date": _safe_date(details.get(date_field)),
        "vote_average": _normalise_rating(details.get("vote_average")),
        "vote_count": _safe_nonnegative_int(details.get("vote_count")),
        "overview": _safe_text(details.get("overview"), maximum=5000),
        "tagline": _safe_text(details.get("tagline"), maximum=500),
        "genres": genres,
        "number_of_seasons": _safe_nonnegative_int(
            details.get("number_of_seasons"), maximum=1000
        ),
    }
    if media_type == "tv":
        runtimes = _as_list(details.get("episode_run_time"))
        runtime = runtimes[0] if runtimes else None
    else:
        runtime = details.get("runtime")
    runtime = _safe_nonnegative_int(runtime, maximum=24 * 60)
    title["runtime"] = runtime or None

    title["poster_url"] = _tmdb_image_url(
        POSTER_BASE_URL, details.get("poster_path")
    )
    title["backdrop_url"] = _tmdb_image_url(
        BACKDROP_BASE_URL, details.get("backdrop_path")
    )
    title["provider_groups"] = _as_list(provider_groups)
    if streaming_error:
        title["streaming_error"] = _safe_text(streaming_error, maximum=300)
    videos = _as_dict(data.get("videos"))
    reviews = _as_dict(data.get("reviews"))
    title["trailer"] = _choose_trailer(videos.get("results"))
    title["reviews"] = _normalise_reviews(reviews.get("results"))
    title["credit_sections"] = _normalise_credits(
        data.get("credits"), details, media_type
    )
    return title


def get_title_details(media_type, title_id, *, include_streaming=True):
    """Busca a ficha completa de um filme ou série pelo ID do TMDB."""

    if media_type not in {"movie", "tv"}:
        raise TMDBError("Tipo de título inválido.")
    title_id = _validate_title_id(title_id)
    data = _fetch_title_extras(title_id, media_type)
    provider_groups = []
    streaming_error = None
    if include_streaming:
        try:
            # O Watchmode so recebe IDs que o TMDB acabou de validar.
            provider_groups = get_streaming_groups(media_type, title_id)
        except WatchmodeError as error:
            streaming_error = str(error)
    return _build_title_payload(data, media_type, provider_groups, streaming_error)


def _get_recent_top_titles(media_type, limit=10):
    """Retorna filmes ou séries recentes com as melhores avaliações."""

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

    data = _get(f"/discover/{media_type}", **filters)
    ranked_results = sorted(
        [item for item in _as_list(data.get("results")) if isinstance(item, dict)],
        key=lambda item: (
            _normalise_rating(item.get("vote_average")),
            item.get("vote_count") or 0,
        ),
        reverse=True,
    )
    titles = []
    for item in ranked_results:
        try:
            item_id = _validate_title_id(item.get("id"))
        except TMDBError:
            continue
        title = _safe_text(
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
                    _safe_text(item.get("original_title"), maximum=255)
                    if media_type == "movie"
                    else _safe_text(item.get("original_name"), maximum=255)
                )
                or "",
                "overview": _safe_text(item.get("overview"), maximum=5000),
                "release_date": (
                    _safe_date(item.get("release_date"))
                    if media_type == "movie"
                    else _safe_date(item.get("first_air_date"))
                )
                or "",
                "vote_average": _normalise_rating(item.get("vote_average")),
                "vote_count": _safe_nonnegative_int(item.get("vote_count")),
                "poster_url": _tmdb_image_url(
                    POSTER_BASE_URL, item.get("poster_path")
                ),
            }
        )
        if len(titles) == limit:
            break

    cache.set(cache_key, titles, TRENDS_CACHE_SECONDS)
    return titles


def get_recent_top_movies(limit=10):
    return _get_recent_top_titles("movie", limit)


def get_recent_top_series(limit=10):
    return _get_recent_top_titles("tv", limit)


def _normalise_release_list_item(item, availability_kind):
    if not isinstance(item, dict):
        return None
    try:
        item_id = _validate_title_id(item.get("id"))
    except TMDBError:
        return None
    title = _safe_text(item.get("title"), maximum=255)
    if not title:
        return None

    release_date = _safe_date(item.get("release_date"))
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
        "original_title": _safe_text(item.get("original_title"), maximum=255),
        "overview": _safe_text(item.get("overview"), maximum=5000),
        "release_date": release_date,
        "release_date_value": parsed_release_date,
        "vote_average": _normalise_rating(item.get("vote_average")),
        "vote_count": _safe_nonnegative_int(item.get("vote_count")),
        "poster_url": _tmdb_image_url(POSTER_BASE_URL, item.get("poster_path")),
        "availability_kind": availability_kind,
        "availability_label": availability_label,
    }


def _get_movie_release_list(list_name, limit=10):
    """Retorna filmes em cartaz ou próximos lançamentos para o Brasil."""

    if list_name not in {"now_playing", "upcoming"}:
        raise TMDBError("Lista de lançamentos inválida.")

    limit = min(max(int(limit), 1), 20)
    today = timezone.localdate()
    cache_key = f"tmdb:movie-releases:v1:{list_name}:BR:{today.isoformat()}:{limit}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    data = _get(
        f"/movie/{list_name}",
        language="pt-BR",
        region="BR",
        page=1,
    )
    availability_kind = "cinema" if list_name == "now_playing" else "upcoming"
    titles = []
    seen_ids = set()
    for item in _as_list(data.get("results")):
        normalised = _normalise_release_list_item(item, availability_kind)
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


def get_now_playing_movies(limit=10):
    return _get_movie_release_list("now_playing", limit)


def get_upcoming_movies(limit=10):
    return _get_movie_release_list("upcoming", limit)


def _discovery_cache_key(
    media_type, genre_id, min_rating, max_rating, min_release_year=None
):
    genre_key = genre_id or "all"
    min_key = f"{min_rating:.1f}".replace(".", "-")
    max_key = f"{max_rating:.1f}".replace(".", "-")
    year_key = min_release_year or "all"
    return f"tmdb:discover:v3:{media_type}:{genre_key}:{min_key}:{max_key}:{year_key}"


def _find_streaming_candidate(media_type, candidates):
    streaming_error = None
    for candidate in candidates[:MAX_STREAMING_CANDIDATES]:
        if not isinstance(candidate, dict):
            continue
        try:
            title_id = _validate_title_id(candidate.get("id"))
            groups = get_streaming_groups(media_type, title_id)
        except WatchmodeError as error:
            streaming_error = str(error)
            break
        except TMDBError:
            continue
        if groups:
            return title_id, groups, None
    return _validate_title_id(candidates[0]["id"]), [], streaming_error


def _discovery_candidates(results):
    candidates = []
    for item in _as_list(results):
        if not isinstance(item, dict):
            continue
        try:
            title_id = _validate_title_id(item.get("id"))
        except TMDBError:
            continue
        candidates.append({"id": title_id})
    return candidates


def _load_discovery_page(
    media_type,
    genre_id,
    min_rating,
    max_rating,
    filters,
    min_release_year=None,
):
    cache_key = _discovery_cache_key(
        media_type, genre_id, min_rating, max_rating, min_release_year
    )
    first_page = cache.get(cache_key)
    if first_page is None:
        first_page = _get(f"/discover/{media_type}", page=1, **filters)
        cache.set(cache_key, first_page, DISCOVERY_CACHE_SECONDS)

    total_results = _safe_nonnegative_int(first_page.get("total_results"))
    first_results = _discovery_candidates(first_page.get("results"))
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
        return first_results

    page_data = _get(
        f"/discover/{media_type}", page=random.randint(1, total_pages), **filters
    )
    return _discovery_candidates(page_data.get("results")) or first_results


def get_random_title(
    media_type="movie",
    genre_id=None,
    min_rating=0,
    max_rating=10,
    min_release_year=None,
):
    if media_type not in {"movie", "tv"}:
        media_type = "movie"

    min_rating = _normalise_rating(min_rating)
    max_rating = max(_normalise_rating(max_rating), min_rating)
    if min_release_year is not None:
        try:
            min_release_year = int(min_release_year)
        except (TypeError, ValueError, OverflowError):
            min_release_year = MIN_RELEASE_YEAR
        min_release_year = min(
            max(min_release_year, MIN_RELEASE_YEAR), timezone.localdate().year
        )
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
                str(parsed_genre_id)
                if 1 <= parsed_genre_id <= MAX_TMDB_ID
                else None
            )
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
    elif min_release_year is not None:
        filters["first_air_date.gte"] = f"{min_release_year}-01-01"
    if genre_id:
        filters["with_genres"] = genre_id

    results = _load_discovery_page(
        media_type,
        genre_id,
        min_rating,
        max_rating,
        filters,
        min_release_year,
    )
    candidates = random.sample(
        results, k=min(MAX_STREAMING_CANDIDATES, len(results))
    )
    first_title_id = candidates[0]["id"]

    with ThreadPoolExecutor(max_workers=2) as executor:
        first_details_future = executor.submit(
            _fetch_title_extras, first_title_id, media_type
        )
        streaming_future = executor.submit(
            _find_streaming_candidate, media_type, candidates
        )
        title_id, provider_groups, streaming_error = streaming_future.result()
        if title_id == first_title_id:
            data = first_details_future.result()
        else:
            data = _fetch_title_extras(title_id, media_type)
    return _build_title_payload(data, media_type, provider_groups, streaming_error)


def get_random_movie(
    genre_id=None, min_rating=0, max_rating=10, min_release_year=None
):
    return get_random_title(
        "movie", genre_id, min_rating, max_rating, min_release_year
    )


def get_random_series(
    genre_id=None, min_rating=0, max_rating=10, min_release_year=None
):
    return get_random_title("tv", genre_id, min_rating, max_rating, min_release_year)
