"""Cliente mínimo e seguro para a WhatsApp Cloud API da Meta."""

import hashlib
import hmac
import json
import logging
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request

from django.conf import settings

from .http_client import ExternalResponseError, open_json

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT_SECONDS = 8
MAX_RESPONSE_BYTES = 512 * 1024


class WhatsAppError(Exception):
    """Falha recuperável na comunicação com a WhatsApp Cloud API."""


def webhook_signature_is_valid(payload, signature):
    """Valida a assinatura HMAC enviada pela Meta sem interpretar o corpo."""

    app_secret = settings.META_APP_SECRET
    if not app_secret or not signature or not signature.startswith("sha256="):
        return False
    expected = hmac.new(
        app_secret.encode("utf-8"), payload, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, f"sha256={expected}")


def send_text_message(recipient, body):
    """Envia uma resposta de texto para uma conversa iniciada pelo usuário."""

    if not settings.WHATSAPP_ACCESS_TOKEN or not settings.WHATSAPP_PHONE_NUMBER_ID:
        raise WhatsAppError("A API do WhatsApp ainda não foi configurada.")
    recipient = str(recipient or "").lstrip("+")
    if not re.fullmatch(r"[0-9]{10,15}", recipient) or not isinstance(body, str):
        raise WhatsAppError("A mensagem do WhatsApp está inválida.")
    body = body.strip()[:4096]
    if not body:
        raise WhatsAppError("A mensagem do WhatsApp está inválida.")
    api_version = settings.WHATSAPP_GRAPH_API_VERSION
    phone_number_id = settings.WHATSAPP_PHONE_NUMBER_ID
    if not re.fullmatch(r"v[0-9]{1,3}\.[0-9]{1,3}", api_version):
        raise WhatsAppError("A versão da API do WhatsApp está inválida.")
    if not re.fullmatch(r"[0-9]{5,30}", phone_number_id):
        raise WhatsAppError("O identificador do WhatsApp está inválido.")

    url = (
        "https://graph.facebook.com/"
        f"{api_version}/"
        f"{phone_number_id}/messages"
    )
    payload = json.dumps(
        {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient,
            "type": "text",
            "text": {"preview_url": False, "body": body},
        }
    ).encode("utf-8")
    request = Request(
        url,
        data=payload,
        method="POST",
        headers={
            "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "QualFilmeHoje/1.0",
        },
    )
    try:
        response = open_json(
            request,
            timeout=REQUEST_TIMEOUT_SECONDS,
            max_bytes=MAX_RESPONSE_BYTES,
        )
        if not isinstance(response, dict):
            raise ExternalResponseError("A Meta não retornou um objeto JSON.")
        return response
    except HTTPError as error:
        logger.warning("A Meta recusou uma resposta do WhatsApp: HTTP %s", error.code)
        raise WhatsAppError("A Meta recusou a mensagem.") from error
    except (URLError, TimeoutError) as error:
        logger.warning("Não foi possível responder pelo WhatsApp: %s", error)
        raise WhatsAppError("A Meta não respondeu a tempo.") from error
    except (ExternalResponseError, TypeError) as error:
        raise WhatsAppError("A Meta devolveu uma resposta inválida.") from error
