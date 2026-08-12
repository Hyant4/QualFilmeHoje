"""Links diretos de streaming fornecidos pela Watchmode.

A chave fica no servidor e as respostas são armazenadas em cache para poupar a
cota mensal do plano gratuito.
"""

import math
import os
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request

from django.core.cache import cache

from .http_client import ExternalResponseError, open_json
from .urls import (
    STREAMING_HOSTS,
    WATCHMODE_IMAGE_HOSTS,
    safe_https_url,
)

API_BASE_URL = "https://api.watchmode.com/v1"
REGION = "BR"
LINK_CACHE_SECONDS = 6 * 60 * 60
CATALOG_CACHE_SECONDS = 7 * 24 * 60 * 60
REQUEST_TIMEOUT_SECONDS = 3
MAX_RESPONSE_BYTES = 1024 * 1024
MAX_TMDB_ID = 2_147_483_647

SOURCE_GROUPS = (
    ("sub", "Incluso na assinatura"),
    ("free", "Grátis"),
    ("tve", "Canal de TV"),
    ("rent", "Aluguel"),
    ("buy", "Compra"),
)


class WatchmodeError(Exception):
    """Falha recuperável ao obter links diretos."""


def _get(path, **params):
    api_key = os.getenv("WATCHMODE_API_KEY")
    if not api_key or api_key.startswith("cole-sua-chave"):
        raise WatchmodeError("Os links diretos ainda não foram configurados.")

    query = urlencode({key: value for key, value in params.items() if value is not None})
    url = f"{API_BASE_URL}{path}"
    if query:
        url = f"{url}?{query}"
    request = Request(
        url,
        headers={
            "X-API-Key": api_key,
            "Accept": "application/json",
            "User-Agent": "QualFilmeHoje/1.0",
        },
    )

    try:
        payload = open_json(
            request,
            timeout=REQUEST_TIMEOUT_SECONDS,
            max_bytes=MAX_RESPONSE_BYTES,
        )
        if not isinstance(payload, list):
            raise ExternalResponseError("A Watchmode nao retornou uma lista JSON.")
        return payload
    except HTTPError as error:
        if error.code == 404:
            return []
        if error.code == 401:
            message = "A chave da Watchmode não foi aceita."
        elif error.code == 429:
            message = "A cota de links diretos foi atingida temporariamente."
        else:
            message = "Os links diretos estão temporariamente indisponíveis."
        raise WatchmodeError(message) from error
    except (URLError, TimeoutError) as error:
        raise WatchmodeError("A busca por links diretos demorou para responder.") from error
    except (ExternalResponseError, TypeError) as error:
        raise WatchmodeError("A Watchmode devolveu uma resposta inesperada.") from error


def _safe_int(value):
    if isinstance(value, bool):
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return parsed if 1 <= parsed <= MAX_TMDB_ID else None


def _safe_text(value, maximum):
    return str(value)[:maximum] if isinstance(value, str | int | float) else ""


def _source_catalog():
    cache_key = "watchmode:source-catalog:BR"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    sources = _get("/sources/", regions=REGION, types="sub,purchase,free,tve")
    catalog = {}
    for source in sources:
        if not isinstance(source, dict):
            continue
        source_id = _safe_int(source.get("id"))
        if source_id is None:
            continue
        catalog[source_id] = {
            "name": _safe_text(source.get("name"), 120) or "Plataforma",
            "logo_url": safe_https_url(
                source.get("logo_100px"), WATCHMODE_IMAGE_HOSTS
            ),
        }
    cache.set(cache_key, catalog, CATALOG_CACHE_SECONDS)
    return catalog


def _normalise_sources(sources, catalog):
    by_type = {key: [] for key, _label in SOURCE_GROUPS}
    seen = set()

    if not isinstance(sources, list):
        return []

    for source in sources:
        if not isinstance(source, dict):
            continue
        source_type = source.get("type")
        web_url = safe_https_url(source.get("web_url"), STREAMING_HOSTS)
        if source_type not in by_type or not web_url:
            continue

        source_id = _safe_int(source.get("source_id"))
        source_info = catalog.get(source_id, {})
        name = (
            _safe_text(source.get("name"), 120)
            or source_info.get("name")
            or "Plataforma"
        )
        price = source.get("price")
        if (
            not isinstance(price, int | float)
            or isinstance(price, bool)
            or not math.isfinite(float(price))
            or not 0 <= float(price) <= 100_000
        ):
            price = None
        unique_key = (source_type, source_id or name.casefold(), web_url)
        if unique_key in seen:
            continue
        seen.add(unique_key)
        by_type[source_type].append(
            {
                "source_id": source_id,
                "provider_name": name,
                "logo_url": source_info.get("logo_url", ""),
                "web_url": web_url,
                "format": _safe_text(source.get("format"), 30),
                "price": price,
            }
        )

    return [
        {"key": key, "label": label, "providers": by_type[key]}
        for key, label in SOURCE_GROUPS
        if by_type[key]
    ]


def get_streaming_groups(media_type, tmdb_id):
    """Retorna plataformas agrupadas, com URL web direta para o título."""

    if media_type not in {"movie", "tv"}:
        raise WatchmodeError("Tipo de titulo invalido para a Watchmode.")
    tmdb_id = _safe_int(tmdb_id)
    if tmdb_id is None:
        raise WatchmodeError("ID de titulo invalido para a Watchmode.")
    cache_key = f"watchmode:links:{REGION}:{media_type}:{tmdb_id}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    watchmode_id = f"{media_type}-{tmdb_id}"
    sources = _get(f"/title/{watchmode_id}/sources/", regions=REGION)
    try:
        catalog = _source_catalog()
    except WatchmodeError:
        catalog = {}

    groups = _normalise_sources(sources, catalog)
    cache.set(cache_key, groups, LINK_CACHE_SECONDS)
    return groups
