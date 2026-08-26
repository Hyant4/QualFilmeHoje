"""Validação, cache opaco e orquestração do filtro por linguagem natural."""

import hashlib
import hmac

from django.conf import settings
from django.core.cache import cache
from pydantic import ValidationError

from movies.ai.filter_mapping import UnsupportedFilterIntent, map_intent_to_suggestion
from movies.ai.gemini import (
    GeminiFilterError,
    GeminiFilterUnavailable,
    interpret_filter,
)
from movies.ai.schemas import FilterSuggestion

CACHE_KEY_VERSION = "v1"


class InvalidFilterInput(ValueError):
    """O texto recebido não respeita o contrato público do endpoint."""


class FilterInterpretationUnavailable(RuntimeError):
    """O provedor não está pronto para atender a requisição."""


class FilterInterpretationUnsupported(RuntimeError):
    """A resposta é válida, mas não há filtro equivalente na interface."""


def normalise_filter_text(value) -> str:
    if not isinstance(value, str):
        raise InvalidFilterInput("O texto deve ser uma string.")
    if len(value) > settings.AI_FILTER_MAX_TEXT_CHARS:
        raise InvalidFilterInput("O texto excede o limite permitido.")
    if any(ord(character) < 32 and not character.isspace() for character in value):
        raise InvalidFilterInput("O texto contém caracteres de controle.")
    text = " ".join(value.split())
    if not text:
        raise InvalidFilterInput("O texto não pode ficar vazio.")
    if len(text) > settings.AI_FILTER_MAX_TEXT_CHARS:
        raise InvalidFilterInput("O texto excede o limite permitido.")
    return text


def _cache_key(text: str) -> str:
    derived_key = hmac.new(
        settings.SECRET_KEY.encode("utf-8"),
        b"qualfilmehoje:ai-filter-cache:v1",
        hashlib.sha256,
    ).digest()
    digest = hmac.new(
        derived_key,
        text.casefold().encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return f"ai-filter:{CACHE_KEY_VERSION}:{digest}"


def _get_cached_suggestion(key: str):
    cached_value = cache.get(key)
    if not isinstance(cached_value, dict):
        return None
    try:
        return FilterSuggestion.model_validate(cached_value)
    except ValidationError:
        cache.delete(key)
        return None


def interpret_text_filter(value) -> FilterSuggestion:
    """Retorna apenas filtros seguros e nunca persiste a frase original."""

    text = normalise_filter_text(value)
    key = _cache_key(text)
    suggestion = _get_cached_suggestion(key)
    if suggestion is not None:
        return suggestion

    try:
        intent = interpret_filter(text)
    except (GeminiFilterUnavailable, GeminiFilterError) as error:
        raise FilterInterpretationUnavailable(
            "Provedor de filtro indisponível."
        ) from error

    try:
        suggestion = map_intent_to_suggestion(intent)
    except UnsupportedFilterIntent as error:
        raise FilterInterpretationUnsupported(
            "Filtro sem suporte na interface."
        ) from error
    if settings.AI_FILTER_CACHE_SECONDS:
        cache.set(
            key,
            suggestion.model_dump(mode="json"),
            timeout=settings.AI_FILTER_CACHE_SECONDS,
        )
    return suggestion
