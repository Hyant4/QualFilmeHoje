"""Cliente mínimo e seguro para a WhatsApp Cloud API da Meta."""

import hashlib
import hmac
import json
import logging
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT_SECONDS = 8


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
    if not recipient or not body:
        raise WhatsAppError("A mensagem do WhatsApp está inválida.")

    url = (
        "https://graph.facebook.com/"
        f"{settings.WHATSAPP_GRAPH_API_VERSION}/"
        f"{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
    )
    payload = json.dumps(
        {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": str(recipient).lstrip("+"),
            "type": "text",
            "text": {"preview_url": False, "body": str(body)[:4096]},
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
        with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            return json.load(response)
    except HTTPError as error:
        logger.warning("A Meta recusou uma resposta do WhatsApp: HTTP %s", error.code)
        raise WhatsAppError("A Meta recusou a mensagem.") from error
    except (URLError, TimeoutError) as error:
        logger.warning("Não foi possível responder pelo WhatsApp: %s", error)
        raise WhatsAppError("A Meta não respondeu a tempo.") from error
    except (json.JSONDecodeError, UnicodeDecodeError, TypeError) as error:
        raise WhatsAppError("A Meta devolveu uma resposta inválida.") from error
