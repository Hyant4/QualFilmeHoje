"""Transporte HTTP autenticado para a API do TMDB."""

import os
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request

from .http_client import ExternalResponseError, open_json

API_BASE_URL = "https://api.themoviedb.org/3"


class TMDBError(Exception):
    """Erro de integração exibível para o usuário final."""


class TMDBNotFound(TMDBError):
    """O ID foi validado, mas não existe no catálogo do TMDB."""


def fetch_json(path, **params):
    """Executa uma chamada segura e retorna um objeto JSON do TMDB."""

    if not isinstance(path, str) or not re.fullmatch(
        r"/[A-Za-z0-9_./-]{1,200}", path
    ):
        raise TMDBError("Caminho inválido para a API do TMDB.")

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
            raise ExternalResponseError("O TMDB não retornou um objeto JSON.")
        return payload
    except HTTPError as error:
        if error.code == 404:
            raise TMDBNotFound("O título não foi encontrado no TMDB.") from error
        if error.code == 401:
            message = "O token do TMDB não é válido. Confira o arquivo .env."
        elif error.code == 429:
            message = (
                "Muitas consultas foram feitas. Aguarde um instante e tente novamente."
            )
        else:
            message = "Não foi possível consultar o TMDB agora."
        raise TMDBError(message) from error
    except (URLError, TimeoutError) as error:
        raise TMDBError("O TMDB demorou para responder. Tente novamente.") from error
    except (ExternalResponseError, TypeError) as error:
        raise TMDBError("O TMDB devolveu uma resposta inesperada.") from error
