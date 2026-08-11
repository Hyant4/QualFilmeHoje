"""Controles de abuso que funcionam em varias instancias serverless."""

import hashlib
import hmac
import ipaddress
import logging
import time
from functools import wraps

from django.conf import settings
from django.core.cache import cache
from django.core.cache.backends.base import InvalidCacheBackendError
from django.db import DatabaseError
from django.http import HttpResponse, JsonResponse

logger = logging.getLogger(__name__)


def get_client_ip(request):
    """Retorna IP normalizado; so confia em XFF quando a Vercel e o proxy."""

    candidate = request.META.get("REMOTE_ADDR", "")
    if settings.IS_VERCEL:
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
        if forwarded:
            # O proxy confiavel e o ultimo salto da lista recebida pela app.
            candidate = forwarded.rsplit(",", maxsplit=1)[-1].strip()
    try:
        address = ipaddress.ip_address(candidate)
    except ValueError:
        return "unknown"
    if address.version == 6:
        # Evita rotacao barata dentro do /64 entregue ao mesmo cliente.
        return str(ipaddress.ip_network(f"{address}/64", strict=False))
    return str(address)


def _identifier_digest(dimension, value):
    payload = f"{dimension}:{value}".encode()
    return hmac.new(
        settings.SECRET_KEY.encode("utf-8"), payload, hashlib.sha256
    ).hexdigest()


def _consume(scope, dimension, identifier, limit, window_seconds):
    now = int(time.time())
    window = now // window_seconds
    retry_after = window_seconds - (now % window_seconds)
    digest = _identifier_digest(dimension, identifier)
    key = f"ratelimit:{scope}:{dimension}:{digest}:{window}"
    timeout = retry_after + 5

    if cache.add(key, 1, timeout=timeout):
        return True, retry_after
    try:
        count = cache.incr(key)
    except ValueError:
        # A entrada pode expirar entre add() e incr().
        cache.add(key, 1, timeout=timeout)
        count = 1
    return count <= limit, retry_after


def rate_limit(scope, *, ip=None, user=None, methods=None):
    """Aplica limites fixos ``(quantidade, segundos)`` por IP e usuario."""

    allowed_methods = {method.upper() for method in (methods or [])}

    def decorator(view_func):
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            if allowed_methods and request.method not in allowed_methods:
                return view_func(request, *args, **kwargs)

            checks = []
            if ip:
                checks.append(("ip", get_client_ip(request), *ip))
            if user and request.user.is_authenticated:
                checks.append(("user", str(request.user.pk), *user))

            try:
                for dimension, identifier, limit, window_seconds in checks:
                    accepted, retry_after = _consume(
                        scope,
                        dimension,
                        identifier,
                        int(limit),
                        int(window_seconds),
                    )
                    if not accepted:
                        wants_json = (
                            request.headers.get("x-requested-with")
                            == "XMLHttpRequest"
                            or "application/json"
                            in request.headers.get("accept", "")
                        )
                        if wants_json:
                            response = JsonResponse(
                                {
                                    "error": (
                                        "Muitas tentativas. Aguarde e tente novamente."
                                    )
                                },
                                status=429,
                            )
                        else:
                            response = HttpResponse(
                                "Muitas tentativas. Aguarde e tente novamente.",
                                status=429,
                                content_type="text/plain; charset=utf-8",
                            )
                        response["Retry-After"] = str(retry_after)
                        return response
            except (DatabaseError, InvalidCacheBackendError):
                logger.exception("O backend compartilhado de rate limit falhou.")
                return HttpResponse(
                    "Protecao temporariamente indisponivel. Tente novamente.",
                    status=503,
                    content_type="text/plain; charset=utf-8",
                )

            return view_func(request, *args, **kwargs)

        return wrapped

    return decorator
