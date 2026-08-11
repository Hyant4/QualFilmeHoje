import hashlib
import hmac
import json
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse

from movies.models import Favorite, Title, WhatsAppContact
from movies.views import whatsapp_webhook

APP_SECRET = "test-meta-app-secret"
VERIFY_TOKEN = "test-webhook-token"


@override_settings(
    META_APP_SECRET=APP_SECRET,
    WHATSAPP_VERIFY_TOKEN=VERIFY_TOKEN,
    WHATSAPP_ACCESS_TOKEN="test-access-token",
    WHATSAPP_PHONE_NUMBER_ID="123456789",
    WHATSAPP_GRAPH_API_VERSION="v25.0",
)
class WhatsAppWebhookTests(TestCase):
    def setUp(self):
        cache.clear()

    def _signature(self, body):
        digest = hmac.new(APP_SECRET.encode(), body, hashlib.sha256).hexdigest()
        return f"sha256={digest}"

    def _payload(self, *, message_id="wamid.1", sender="5585999990000", text="favoritos"):
        return {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "messages": [
                                    {"id": message_id, "from": sender, "type": "text", "text": {"body": text}}
                                ]
                            }
                        }
                    ]
                }
            ],
        }

    def _post(self, payload, signature=None):
        body = json.dumps(payload).encode()
        return self.client.post(
            reverse("movies:whatsapp_webhook"),
            data=body,
            content_type="application/json",
            HTTP_X_HUB_SIGNATURE_256=signature or self._signature(body),
        )

    def test_meta_can_verify_the_webhook(self):
        response = self.client.get(
            reverse("movies:whatsapp_webhook"),
            {"hub.mode": "subscribe", "hub.verify_token": VERIFY_TOKEN, "hub.challenge": "abc123"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"abc123")

    def test_webhook_rejects_an_invalid_signature(self):
        response = self._post(self._payload(), signature="sha256=invalid")

        self.assertEqual(response.status_code, 403)

    def test_webhook_rejects_an_oversized_body_before_parsing(self):
        body = b"x" * (256 * 1024 + 1)
        response = self.client.post(
            reverse("movies:whatsapp_webhook"),
            data=body,
            content_type="application/json",
            HTTP_X_HUB_SIGNATURE_256=self._signature(body),
        )

        self.assertEqual(response.status_code, 413)

    def test_webhook_rejects_an_invalid_content_length(self):
        request = RequestFactory().post(
            reverse("movies:whatsapp_webhook"),
            data=b"{}",
            content_type="application/json",
        )
        request.META["CONTENT_LENGTH"] = "not-a-number"

        response = whatsapp_webhook(request)

        self.assertEqual(response.status_code, 400)

    @patch("movies.views.send_text_message")
    def test_favorites_command_marks_contact_verified_and_replies(self, send_message):
        user = get_user_model().objects.create_user(
            username="cinefilo", email="cinefilo@example.com", password="senha-forte"
        )
        contact = WhatsAppContact.objects.create(
            user=user, phone_number="+5585999990000"
        )
        title = Title.objects.create(
            tmdb_id=42, media_type=Title.MOVIE, name="Filme favorito", vote_average=8.5
        )
        Favorite.objects.create(user=user, visitor_id="00000000-0000-0000-0000-000000000001", title=title)

        response = self._post(self._payload())

        self.assertEqual(response.status_code, 200)
        contact.refresh_from_db()
        self.assertTrue(contact.is_verified)
        send_message.assert_called_once()
        self.assertEqual(send_message.call_args.args[0], "5585999990000")
        self.assertIn("Filme favorito", send_message.call_args.args[1])

    @patch("movies.views.send_text_message")
    def test_duplicate_message_is_not_answered_twice(self, send_message):
        user = get_user_model().objects.create_user(
            username="duplicado", email="duplicado@example.com", password="senha-forte"
        )
        WhatsAppContact.objects.create(user=user, phone_number="+5585999990000")
        payload = self._payload(message_id="wamid.duplicada")

        self._post(payload)
        self._post(payload)

        send_message.assert_called_once()
