"""Factories pequenas para manter os testes focados no comportamento relevante."""

from itertools import count

from allauth.account.models import EmailAddress
from django.contrib.auth import get_user_model

from movies.models import Title

DEFAULT_USER_PASSWORD = "CinemaPortfolio2026!"

_title_sequence = count(1)
_user_sequence = count(1)
_tmdb_payload_sequence = count(10_000)


def create_user(
    email=None,
    *,
    username=None,
    password=DEFAULT_USER_PASSWORD,
    verified=True,
    **attributes,
):
    sequence = next(_user_sequence)
    email = email or f"pessoa-{sequence}@example.com"
    username = username or email.split("@", maxsplit=1)[0]
    user = get_user_model().objects.create_user(
        username=username,
        email=email,
        password=password,
        **attributes,
    )
    if verified:
        EmailAddress.objects.update_or_create(
            user=user,
            email=email,
            defaults={"verified": True, "primary": True},
        )
    return user


def create_title(**attributes):
    sequence = next(_title_sequence)
    defaults = {
        "tmdb_id": sequence,
        "media_type": Title.MOVIE,
        "name": f"Filme de teste {sequence}",
    }
    defaults.update(attributes)
    return Title.objects.create(**defaults)


def tmdb_title_payload(**overrides):
    sequence = next(_tmdb_payload_sequence)
    payload = {
        "id": sequence,
        "title": f"Filme de teste {sequence}",
        "media_type": Title.MOVIE,
        "vote_average": 8.0,
        "reviews": [],
        "provider_groups": [],
        "credit_sections": [],
    }
    payload.update(overrides)
    return payload
