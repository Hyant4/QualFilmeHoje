"""Cliente do TMDB usado pelo QualFilmeHoje.

Todas as chamadas são feitas no servidor para que o token nunca chegue ao
navegador do visitante.
"""

import json
import os
import random
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from functools import lru_cache
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.core.cache import cache

from .watchmode import WatchmodeError, get_streaming_groups

API_BASE_URL = "https://api.themoviedb.org/3"
POSTER_BASE_URL = "https://image.tmdb.org/t/p/w500"
BACKDROP_BASE_URL = "https://image.tmdb.org/t/p/w1280"
DISCOVERY_CACHE_SECONDS = 10 * 60
TITLE_CACHE_SECONDS = 12 * 60 * 60
TRENDS_CACHE_SECONDS = 30 * 60
RECENT_RELEASE_DAYS = 30
TRENDS_MIN_VOTES = 20
MAX_STREAMING_CANDIDATES = 2


class TMDBError(Exception):
    """Erro de integração exibível para o usuário final."""


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
        with urlopen(request, timeout=10) as response:
            return json.load(response)
    except HTTPError as error:
        if error.code == 401:
            message = "O token do TMDB não é válido. Confira o arquivo .env."
        elif error.code == 429:
            message = "Muitas consultas foram feitas. Aguarde um instante e tente novamente."
        else:
            message = "Não foi possível consultar o TMDB agora."
        raise TMDBError(message) from error
    except (URLError, TimeoutError) as error:
        raise TMDBError("O TMDB demorou para responder. Tente novamente.") from error
    except (json.JSONDecodeError, UnicodeDecodeError, TypeError) as error:
        raise TMDBError("O TMDB devolveu uma resposta inesperada.") from error


@lru_cache(maxsize=2)
def get_genres(media_type="movie"):
    if media_type not in {"movie", "tv"}:
        media_type = "movie"
    return _get(f"/genre/{media_type}/list", language="pt-BR").get("genres", [])


def _normalise_rating(value):
    try:
        rating = float(value)
    except (TypeError, ValueError):
        return 0.0
    return min(max(rating, 0.0), 10.0)


def _choose_trailer(videos):
    youtube_videos = [video for video in videos if video.get("site") == "YouTube" and video.get("key")]
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

    trailer = max(youtube_videos, key=score)
    trailer["embed_url"] = f"https://www.youtube-nocookie.com/embed/{trailer['key']}"
    trailer["youtube_url"] = f"https://www.youtube.com/watch?v={trailer['key']}"
    return trailer


def _normalise_reviews(reviews):
    normalised = []
    for review in reviews[:6]:
        author_details = review.get("author_details") or {}
        normalised.append(
            {
                "id": review.get("id"),
                "author": review.get("author") or "Usuário do TMDB",
                "rating": author_details.get("rating"),
                "content": review.get("content") or "",
                "created_at": review.get("created_at"),
                "url": review.get("url"),
            }
        )
    return normalised


def _person_names(people, limit=None):
    names = []
    seen = set()
    for person in people:
        name = person.get("name")
        if not name or name in seen:
            continue
        seen.add(name)
        names.append(name)
        if limit and len(names) >= limit:
            break
    return names


def _crew_jobs(person):
    jobs = {person.get("job")}
    jobs.update(job.get("job") for job in person.get("jobs", []))
    return jobs


def _normalise_credits(credits, details, media_type):
    crew = credits.get("crew", [])
    cast = sorted(
        credits.get("cast", []),
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
    cache_key = f"tmdb:title-extras:v2:{media_type}:{title_id}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    credits_key = "aggregate_credits" if media_type == "tv" else "credits"
    details = _get(
        f"/{media_type}/{title_id}",
        language="pt-BR",
        append_to_response=f"videos,reviews,{credits_key}",
    )
    data = {
        "details": details,
        "videos": details.get("videos") or {},
        "reviews": details.get("reviews") or {},
        "credits": details.get(credits_key) or {},
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
                data[name] = future.result()

    cache.set(cache_key, data, TITLE_CACHE_SECONDS)
    return data


def _build_title_payload(data, media_type, provider_groups=None, streaming_error=None):
    """Converte a resposta detalhada do TMDB no formato usado pelas telas."""

    title = dict(data["details"])
    title["media_type"] = media_type
    title["media_label"] = "Série" if media_type == "tv" else "Filme"
    title["title"] = title.get("name") if media_type == "tv" else title.get("title")
    title["original_title"] = (
        title.get("original_name") if media_type == "tv" else title.get("original_title")
    )
    title["release_date"] = (
        title.get("first_air_date") if media_type == "tv" else title.get("release_date")
    )
    if media_type == "tv":
        runtimes = title.get("episode_run_time") or []
        title["runtime"] = runtimes[0] if runtimes else None

    title["poster_url"] = (
        f"{POSTER_BASE_URL}{title['poster_path']}" if title.get("poster_path") else ""
    )
    title["backdrop_url"] = (
        f"{BACKDROP_BASE_URL}{title['backdrop_path']}"
        if title.get("backdrop_path")
        else ""
    )
    title["provider_groups"] = provider_groups or []
    if streaming_error:
        title["streaming_error"] = streaming_error
    title["trailer"] = _choose_trailer(data["videos"].get("results", []))
    title["reviews"] = _normalise_reviews(data["reviews"].get("results", []))
    title["credit_sections"] = _normalise_credits(
        data["credits"], title, media_type
    )
    return title


def get_title_details(media_type, title_id):
    """Busca a ficha completa de um filme ou série pelo ID do TMDB."""

    if media_type not in {"movie", "tv"}:
        raise TMDBError("Tipo de título inválido.")
    try:
        title_id = int(title_id)
    except (TypeError, ValueError) as error:
        raise TMDBError("Título inválido.") from error

    with ThreadPoolExecutor(max_workers=2) as executor:
        details_future = executor.submit(_fetch_title_extras, title_id, media_type)
        streaming_future = executor.submit(get_streaming_groups, media_type, title_id)
        data = details_future.result()
        try:
            provider_groups = streaming_future.result()
            streaming_error = None
        except WatchmodeError as error:
            provider_groups = []
            streaming_error = str(error)
    return _build_title_payload(data, media_type, provider_groups, streaming_error)


def _get_recent_top_titles(media_type, limit=10):
    """Retorna filmes ou séries recentes com as melhores avaliações."""

    if media_type not in {"movie", "tv"}:
        raise TMDBError("Tipo de título inválido.")

    limit = min(max(int(limit), 1), 20)
    today = date.today()
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
        data.get("results", []),
        key=lambda item: (
            _normalise_rating(item.get("vote_average")),
            item.get("vote_count") or 0,
        ),
        reverse=True,
    )
    titles = []
    for item in ranked_results:
        title = item.get("title") if media_type == "movie" else item.get("name")
        if not item.get("id") or not title:
            continue
        titles.append(
            {
                "id": item["id"],
                "media_type": media_type,
                "title": title,
                "original_title": (
                    item.get("original_title")
                    if media_type == "movie"
                    else item.get("original_name")
                )
                or "",
                "overview": item.get("overview") or "",
                "release_date": (
                    item.get("release_date")
                    if media_type == "movie"
                    else item.get("first_air_date")
                )
                or "",
                "vote_average": _normalise_rating(item.get("vote_average")),
                "vote_count": item.get("vote_count") or 0,
                "poster_url": (
                    f"{POSTER_BASE_URL}{item['poster_path']}"
                    if item.get("poster_path")
                    else ""
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


def _discovery_cache_key(media_type, genre_id, min_rating, max_rating):
    genre_key = genre_id or "all"
    min_key = f"{min_rating:.1f}".replace(".", "-")
    max_key = f"{max_rating:.1f}".replace(".", "-")
    return f"tmdb:discover:v2:{media_type}:{genre_key}:{min_key}:{max_key}"


def _find_streaming_candidate(media_type, candidates):
    streaming_error = None
    for candidate in candidates[:MAX_STREAMING_CANDIDATES]:
        try:
            groups = get_streaming_groups(media_type, candidate["id"])
        except WatchmodeError as error:
            streaming_error = str(error)
            break
        if groups:
            return candidate["id"], groups, None
    return candidates[0]["id"], [], streaming_error


def _load_discovery_page(media_type, genre_id, min_rating, max_rating, filters):
    cache_key = _discovery_cache_key(media_type, genre_id, min_rating, max_rating)
    first_page = cache.get(cache_key)
    if first_page is None:
        first_page = _get(f"/discover/{media_type}", page=1, **filters)
        cache.set(cache_key, first_page, DISCOVERY_CACHE_SECONDS)

    total_results = first_page.get("total_results", 0)
    first_results = first_page.get("results", [])
    if not total_results or not first_results:
        content_name = "séries" if media_type == "tv" else "filmes"
        raise TMDBError(
            f"Não encontrei {content_name} para esses filtros. "
            "Diminua a nota ou tente outro gênero."
        )

    total_pages = min(max(int(first_page.get("total_pages", 1)), 1), 500)
    if total_pages == 1:
        return first_results

    page_data = _get(
        f"/discover/{media_type}", page=random.randint(1, total_pages), **filters
    )
    return page_data.get("results") or first_results


def get_random_title(media_type="movie", genre_id=None, min_rating=0, max_rating=10):
    if media_type not in {"movie", "tv"}:
        media_type = "movie"

    min_rating = _normalise_rating(min_rating)
    max_rating = max(_normalise_rating(max_rating), min_rating)
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
    if genre_id:
        filters["with_genres"] = genre_id

    results = _load_discovery_page(
        media_type, genre_id, min_rating, max_rating, filters
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


def get_random_movie(genre_id=None, min_rating=0, max_rating=10):
    return get_random_title("movie", genre_id, min_rating, max_rating)


def get_random_series(genre_id=None, min_rating=0, max_rating=10):
    return get_random_title("tv", genre_id, min_rating, max_rating)
