"""Leitura JSON limitada, sem encaminhar credenciais em redirects."""

import json
from urllib.request import HTTPRedirectHandler, build_opener

MAX_JSON_RESPONSE_BYTES = 2 * 1024 * 1024


class ExternalResponseError(Exception):
    """A resposta externa nao e JSON confiavel dentro dos limites locais."""


class NoRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        # A urllib reutiliza headers como Authorization/X-API-Key em redirects.
        # Bloquear o redirect evita vazamento cross-origin e SSRF indireto.
        return None


_NO_REDIRECT_OPENER = build_opener(NoRedirectHandler)


def open_json(request, *, timeout, max_bytes=MAX_JSON_RESPONSE_BYTES):
    with _NO_REDIRECT_OPENER.open(request, timeout=timeout) as response:
        content_type = response.headers.get_content_type().casefold()
        if content_type not in {"application/json", "application/problem+json"}:
            raise ExternalResponseError("Content-Type externo nao e JSON.")

        content_length = response.headers.get("Content-Length")
        if content_length:
            try:
                declared_size = int(content_length)
            except ValueError as error:
                raise ExternalResponseError("Content-Length externo invalido.") from error
            if declared_size < 0 or declared_size > max_bytes:
                raise ExternalResponseError("Resposta externa excedeu o limite.")

        body = response.read(max_bytes + 1)
        if len(body) > max_bytes:
            raise ExternalResponseError("Resposta externa excedeu o limite.")
        try:
            payload = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ExternalResponseError("JSON externo invalido.") from error
        if not isinstance(payload, dict | list):
            raise ExternalResponseError("Schema JSON externo invalido.")
        return payload
