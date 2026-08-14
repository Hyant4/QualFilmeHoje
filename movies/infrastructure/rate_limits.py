"""Persistencia atomica dos contadores de limite de requisicoes."""

import hashlib
import hmac
import math
from datetime import timedelta

from django.conf import settings
from django.db import DatabaseError, NotSupportedError, connection
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from movies.models import RateLimitBucket

SUPPORTED_DATABASES = frozenset({"postgresql", "sqlite"})


def _identifier_key(scope, dimension, identifier):
    """Gera uma chave opaca sem persistir IP, usuario ou escopo em texto aberto."""

    derived_key = hmac.new(
        settings.SECRET_KEY.encode("utf-8"),
        b"qualfilmehoje:rate-limit-identities:v2",
        hashlib.sha256,
    ).digest()
    payload = f"{scope}\0{dimension}\0{identifier}".encode()
    digest = hmac.new(derived_key, payload, hashlib.sha256).hexdigest()
    return f"v2:{digest}"


def _normalise_reset_at(value):
    if isinstance(value, str):
        value = parse_datetime(value)
    if value is None:
        raise DatabaseError("O banco nao retornou o vencimento do contador.")
    if timezone.is_naive(value):
        value = timezone.make_aware(value, timezone.get_current_timezone())
    return value


def consume_rate_limit(scope, dimension, identifier, limit, window_seconds):
    """Incrementa um bucket em uma unica instrucao atomica e retorna a decisao."""

    limit = int(limit)
    window_seconds = int(window_seconds)
    if limit < 1 or window_seconds < 1:
        raise ValueError("Limite e janela precisam ser numeros positivos.")
    if connection.vendor not in SUPPORTED_DATABASES:
        raise NotSupportedError(
            f"Backend {connection.vendor!r} nao suporta o contador atomico."
        )

    now = timezone.now()
    next_reset = now + timedelta(seconds=window_seconds)
    bucket_key = _identifier_key(scope, dimension, identifier)
    quote = connection.ops.quote_name
    table = quote(RateLimitBucket._meta.db_table)
    key_column = quote(RateLimitBucket._meta.get_field("bucket_key").column)
    count_column = quote(RateLimitBucket._meta.get_field("request_count").column)
    reset_column = quote(RateLimitBucket._meta.get_field("reset_at").column)
    sql = f"""
        INSERT INTO {table} ({key_column}, {count_column}, {reset_column})
        VALUES (%s, 1, %s)
        ON CONFLICT ({key_column}) DO UPDATE SET
            {count_column} = CASE
                WHEN {reset_column} <= %s THEN 1
                ELSE {count_column} + 1
            END,
            {reset_column} = CASE
                WHEN {reset_column} <= %s THEN excluded.{reset_column}
                ELSE {reset_column}
            END
        RETURNING {count_column}, {reset_column}
    """
    with connection.cursor() as cursor:
        cursor.execute(sql, [bucket_key, next_reset, now, now])
        request_count, reset_at = cursor.fetchone()

    reset_at = _normalise_reset_at(reset_at)
    retry_after = max(1, math.ceil((reset_at - now).total_seconds()))
    return request_count <= limit, retry_after
