"""Notifica buscadores participantes quando uma URL publica e criada."""

import hashlib
import json
import logging
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, build_opener

from django.conf import settings
from django.core.cache import cache
from django.db import DatabaseError
from django.urls import reverse

from .http_client import NoRedirectHandler

INDEXNOW_ENDPOINT = "https://api.indexnow.org/indexnow"
INDEXNOW_TIMEOUT_SECONDS = 1.5
INDEXNOW_RESPONSE_LIMIT = 1024
INDEXNOW_DEDUPLICATION_SECONDS = 24 * 60 * 60
MAX_TMDB_ID = 2_147_483_647

logger = logging.getLogger(__name__)
_INDEXNOW_OPENER = build_opener(NoRedirectHandler)


def _canonical_url(url):
    if not isinstance(url, str) or len(url) > 2048:
        return ""
    submitted = urlsplit(url)
    canonical = urlsplit(settings.SITE_URL)
    if (
        submitted.scheme != canonical.scheme
        or submitted.netloc != canonical.netloc
        or submitted.username
        or submitted.password
        or submitted.fragment
    ):
        return ""
    return url


def submit_url(url):
    """Envia uma URL canonica sem propagar falhas para a requisicao do usuario."""

    if not settings.INDEXNOW_ENABLED:
        return False
    url = _canonical_url(url)
    if not url:
        return False

    cache_digest = hashlib.sha256(url.encode("utf-8")).hexdigest()
    cache_key = f"indexnow:submitted:v1:{cache_digest}"
    try:
        if cache.get(cache_key):
            return True
    except DatabaseError as error:
        logger.warning("Cache indisponivel ao consultar IndexNow: %s", error)

    key_location = f"{settings.SITE_URL}/{settings.INDEXNOW_KEY}.txt"
    payload = json.dumps(
        {
            "host": urlsplit(settings.SITE_URL).netloc,
            "key": settings.INDEXNOW_KEY,
            "keyLocation": key_location,
            "urlList": [url],
        },
        separators=(",", ":"),
    ).encode("utf-8")
    request = Request(
        INDEXNOW_ENDPOINT,
        data=payload,
        method="POST",
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "Accept": "application/json",
            "User-Agent": "QualFilmeHoje/1.0",
        },
    )

    try:
        with _INDEXNOW_OPENER.open(
            request,
            timeout=INDEXNOW_TIMEOUT_SECONDS,
        ) as response:
            response.read(INDEXNOW_RESPONSE_LIMIT + 1)
            if response.status not in {200, 202}:
                return False
    except (HTTPError, URLError, TimeoutError, OSError) as error:
        logger.warning("Falha recuperavel ao notificar IndexNow: %s", error)
        return False

    try:
        cache.set(cache_key, True, INDEXNOW_DEDUPLICATION_SECONDS)
    except DatabaseError as error:
        logger.warning("Cache indisponivel ao registrar IndexNow: %s", error)
    return True


def submit_title_url(media_type, tmdb_id):
    """Monta e envia a URL publica de um filme ou serie validos."""

    if media_type not in {"movie", "tv"} or isinstance(tmdb_id, bool):
        return False
    try:
        tmdb_id = int(tmdb_id)
    except (TypeError, ValueError, OverflowError):
        return False
    if not 1 <= tmdb_id <= MAX_TMDB_ID:
        return False
    path = reverse("movies:title_detail", args=(media_type, tmdb_id))
    return submit_url(f"{settings.SITE_URL}{path}")
