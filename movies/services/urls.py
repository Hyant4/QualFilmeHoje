"""Allowlist central das URLs externas exibidas no site."""

from urllib.parse import urlsplit

TMDB_REVIEW_HOSTS = frozenset({"themoviedb.org"})
TMDB_IMAGE_HOSTS = frozenset({"image.tmdb.org"})
WATCHMODE_IMAGE_HOSTS = frozenset({"cdn.watchmode.com"})

STREAMING_HOSTS = frozenset(
    {
        "amazon.com",
        "amazon.com.br",
        "apple.com",
        "claro.com.br",
        "clarotvmais.com.br",
        "crunchyroll.com",
        "disneyplus.com",
        "globo.com",
        "google.com",
        "hbomax.com",
        "looke.com.br",
        "max.com",
        "mgmplus.com",
        "mubi.com",
        "netflix.com",
        "netmovies.com.br",
        "oldflix.com.br",
        "paramountplus.com",
        "plex.tv",
        "pluto.tv",
        "primevideo.com",
        "rakuten.tv",
        "starz.com",
        "telecine.com.br",
        "vivo.com.br",
        "watchmode.com",
        "youtube.com",
        "youtu.be",
    }
)


def _host_is_allowed(host, allowed_hosts):
    return any(host == allowed or host.endswith(f".{allowed}") for allowed in allowed_hosts)


def safe_https_url(value, allowed_hosts, *, max_length=2048):
    if not isinstance(value, str):
        return ""
    value = value.strip()
    if not value or len(value) > max_length or any(ord(char) < 32 for char in value):
        return ""
    try:
        parsed = urlsplit(value)
        host = (parsed.hostname or "").rstrip(".").casefold().encode("idna").decode("ascii")
        port = parsed.port
    except (UnicodeError, ValueError):
        return ""
    if (
        parsed.scheme.casefold() != "https"
        or not host
        or parsed.username is not None
        or parsed.password is not None
        or port not in {None, 443}
        or not _host_is_allowed(host, allowed_hosts)
    ):
        return ""
    return value
