"""Validação e normalização dos payloads não confiáveis recebidos do TMDB."""

import math
import re
from datetime import date

from .tmdb_client import TMDBError
from .urls import TMDB_REVIEW_HOSTS, safe_https_url

POSTER_BASE_URL = "https://image.tmdb.org/t/p/w500"
BACKDROP_BASE_URL = "https://image.tmdb.org/t/p/w1280"
MAX_TMDB_ID = 2_147_483_647


def normalise_rating(value):
    try:
        rating = float(value)
    except (TypeError, ValueError):
        return 0.0
    if not math.isfinite(rating):
        return 0.0
    return min(max(rating, 0.0), 10.0)


def validate_title_id(value):
    value = str(value or "").strip()
    if not value or len(value) > 10 or not value.isascii() or not value.isdecimal():
        raise TMDBError("Título inválido.")
    title_id = int(value)
    if not 1 <= title_id <= MAX_TMDB_ID:
        raise TMDBError("Título inválido.")
    return title_id


def as_dict(value):
    return value if isinstance(value, dict) else {}


def as_list(value):
    return value if isinstance(value, list) else []


def safe_text(value, *, maximum):
    return str(value)[:maximum] if isinstance(value, str | int | float) else ""


def tmdb_image_url(base_url, path):
    if not isinstance(path, str) or not re.fullmatch(
        r"/[A-Za-z0-9._/-]{1,250}", path
    ):
        return ""
    return f"{base_url}{path}"


def safe_nonnegative_int(value, *, maximum=2_147_483_647):
    if isinstance(value, bool):
        return 0
    try:
        parsed = int(value)
    except (TypeError, ValueError, OverflowError):
        return 0
    return parsed if 0 <= parsed <= maximum else 0


def safe_date(value):
    value = safe_text(value, maximum=10)
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError:
        return ""


def choose_trailer(videos):
    youtube_videos = []
    for video in as_list(videos):
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


def normalise_reviews(reviews):
    normalised = []
    for review in as_list(reviews)[:6]:
        if not isinstance(review, dict):
            continue
        author_details = as_dict(review.get("author_details"))
        normalised.append(
            {
                "id": safe_text(review.get("id"), maximum=100),
                "author": safe_text(review.get("author"), maximum=120)
                or "Usuário do TMDB",
                "rating": normalise_rating(author_details.get("rating")),
                "content": safe_text(review.get("content"), maximum=5000),
                "created_at": safe_text(review.get("created_at"), maximum=40),
                "url": safe_https_url(review.get("url"), TMDB_REVIEW_HOSTS),
            }
        )
    return normalised


def _person_names(people, limit=None):
    names = []
    seen = set()
    for person in as_list(people):
        if not isinstance(person, dict):
            continue
        name = safe_text(person.get("name"), maximum=120)
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
    jobs = {safe_text(person.get("job"), maximum=60)}
    jobs.update(
        safe_text(job.get("job"), maximum=60)
        for job in as_list(person.get("jobs"))
        if isinstance(job, dict)
    )
    return {job for job in jobs if job}


def normalise_credits(credits, details, media_type):
    credits = as_dict(credits)
    details = as_dict(details)
    crew = [person for person in as_list(credits.get("crew")) if isinstance(person, dict)]
    cast = sorted(
        [person for person in as_list(credits.get("cast")) if isinstance(person, dict)],
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


def build_title_payload(data, media_type, provider_groups=None, streaming_error=None):
    """Converte a resposta detalhada do TMDB no formato usado pelas telas."""

    data = as_dict(data)
    details = as_dict(data.get("details"))
    title_id = validate_title_id(details.get("id"))
    name_field = "name" if media_type == "tv" else "title"
    original_field = "original_name" if media_type == "tv" else "original_title"
    date_field = "first_air_date" if media_type == "tv" else "release_date"
    genres = []
    for genre in as_list(details.get("genres"))[:20]:
        if not isinstance(genre, dict):
            continue
        genre_name = safe_text(genre.get("name"), maximum=100)
        if genre_name:
            genres.append(
                {
                    "id": safe_nonnegative_int(genre.get("id"), maximum=MAX_TMDB_ID),
                    "name": genre_name,
                }
            )

    title = {
        "id": title_id,
        "media_type": media_type,
        "media_label": "Série" if media_type == "tv" else "Filme",
        "title": safe_text(details.get(name_field), maximum=255)
        or "Título sem nome",
        "original_title": safe_text(details.get(original_field), maximum=255),
        "release_date": safe_date(details.get(date_field)),
        "vote_average": normalise_rating(details.get("vote_average")),
        "vote_count": safe_nonnegative_int(details.get("vote_count")),
        "overview": safe_text(details.get("overview"), maximum=5000),
        "tagline": safe_text(details.get("tagline"), maximum=500),
        "genres": genres,
        "number_of_seasons": safe_nonnegative_int(
            details.get("number_of_seasons"), maximum=1000
        ),
    }
    if media_type == "tv":
        runtimes = as_list(details.get("episode_run_time"))
        runtime = runtimes[0] if runtimes else None
    else:
        runtime = details.get("runtime")
    runtime = safe_nonnegative_int(runtime, maximum=24 * 60)
    title["runtime"] = runtime or None
    title["poster_url"] = tmdb_image_url(POSTER_BASE_URL, details.get("poster_path"))
    title["backdrop_url"] = tmdb_image_url(
        BACKDROP_BASE_URL, details.get("backdrop_path")
    )
    title["provider_groups"] = as_list(provider_groups)
    if streaming_error:
        title["streaming_error"] = safe_text(streaming_error, maximum=300)
    videos = as_dict(data.get("videos"))
    reviews = as_dict(data.get("reviews"))
    title["trailer"] = choose_trailer(videos.get("results"))
    title["reviews"] = normalise_reviews(reviews.get("results"))
    title["credit_sections"] = normalise_credits(
        data.get("credits"), details, media_type
    )
    return title
