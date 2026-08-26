import json
from pathlib import Path
from unittest.mock import patch

from django.contrib.staticfiles import finders
from django.core.cache import cache
from django.test import Client, SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from pydantic import ValidationError

from movies.ai.filter_mapping import UnsupportedFilterIntent, map_intent_to_suggestion
from movies.ai.gemini import GeminiFilterError
from movies.ai.schemas import FilterIntent
from movies.models import RateLimitBucket
from movies.use_cases.filter_interpretation import _cache_key


class FilterIntentTests(SimpleTestCase):
    def test_mapper_returns_only_values_rendered_by_the_form(self):
        suggestion = map_intent_to_suggestion(
            FilterIntent(
                media_type="movie",
                genre_key="korean_thriller",
                min_release_year=2020,
                min_rating=7.5,
                max_rating=9.0,
                runtime_filter="up_to_90",
                certification="14",
            )
        )

        self.assertEqual(
            suggestion.public_payload()["filters"],
            {
                "media_type": "movie",
                "genre_value": "special:korean_thriller",
                "min_release_year": 2020,
                "min_rating": 7.5,
                "max_rating": 9.0,
                "runtime_filter": "up_to_90",
                "certification": "14",
            },
        )

    def test_schema_rejects_invalid_ranges_and_unknown_fields(self):
        with self.assertRaises(ValidationError):
            FilterIntent(min_rating=8.0, max_rating=7.0)
        with self.assertRaises(ValidationError):
            FilterIntent(media_type="movie", unexpected="value")

    def test_mapper_rejects_a_media_category_the_form_cannot_apply(self):
        with self.assertRaises(UnsupportedFilterIntent):
            map_intent_to_suggestion(
                FilterIntent(media_type="tv", genre_key="japanese_horror")
            )

    def test_cache_key_does_not_expose_the_phrase(self):
        text = "quero um filme de suspense"

        key = _cache_key(text)

        self.assertNotIn(text, key)
        self.assertRegex(key, r"^ai-filter:v1:[0-9a-f]{64}$")


@override_settings(AI_FILTER_ENABLED=True, AI_FILTER_CACHE_SECONDS=600)
class AiFilterEndpointTests(TestCase):
    def setUp(self):
        cache.clear()
        RateLimitBucket.objects.all().delete()
        self.url = reverse("movies:interpret_filter")

    def post_json(self, payload):
        return self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type="application/json",
            HTTP_ACCEPT="application/json",
        )

    @patch("movies.use_cases.filter_interpretation.interpret_filter")
    def test_valid_request_returns_server_mapped_values(self, mock_interpret):
        mock_interpret.return_value = FilterIntent(
            media_type="movie",
            genre_key="thriller",
            runtime_filter="up_to_90",
        )

        response = self.post_json({"texto": "quero um thriller curto"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Cache-Control"], "no-store")
        self.assertEqual(response["X-Content-Type-Options"], "nosniff")
        self.assertEqual(
            response.json(),
            {
                "filters": {
                    "media_type": "movie",
                    "genre_value": "53",
                    "runtime_filter": "up_to_90",
                },
                "applied_fields": ["media_type", "genre_value", "runtime_filter"],
            },
        )
        mock_interpret.assert_called_once_with("quero um thriller curto")

    @patch("movies.use_cases.filter_interpretation.interpret_filter")
    def test_normalised_repeat_uses_cache_without_a_second_model_call(
        self, mock_interpret
    ):
        mock_interpret.return_value = FilterIntent(media_type="tv", genre_key="drama")

        first = self.post_json({"texto": "  quero   uma série dramática  "})
        second = self.post_json({"texto": "quero uma série dramática"})

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(first.json(), second.json())
        mock_interpret.assert_called_once_with("quero uma série dramática")

    @patch("movies.use_cases.filter_interpretation.interpret_filter")
    def test_invalid_request_shapes_and_oversized_body_skip_the_model(
        self, mock_interpret
    ):
        invalid = self.client.post(
            self.url,
            data="not json",
            content_type="application/json",
            HTTP_ACCEPT="application/json",
        )
        wrong_content_type = self.client.post(
            self.url,
            data=json.dumps({"texto": "ok"}),
            content_type="text/plain",
            HTTP_ACCEPT="application/json",
        )
        oversized = self.client.post(
            self.url,
            data=json.dumps({"texto": "x" * 5000}),
            content_type="application/json",
            HTTP_ACCEPT="application/json",
        )

        self.assertEqual(
            [
                invalid.status_code,
                wrong_content_type.status_code,
                oversized.status_code,
            ],
            [400, 400, 413],
        )
        mock_interpret.assert_not_called()

    @patch("movies.use_cases.filter_interpretation.interpret_filter")
    def test_provider_failure_is_generic_and_does_not_reflect_input(
        self, mock_interpret
    ):
        mock_interpret.side_effect = GeminiFilterError("texto privado não deve voltar")

        response = self.post_json({"texto": "filme para hoje"})

        self.assertEqual(response.status_code, 503)
        self.assertNotIn("texto privado", response.content.decode())
        self.assertIn("temporariamente indisponível", response.json()["error"])

    def test_get_is_not_allowed_and_csrf_is_required(self):
        self.assertEqual(self.client.get(self.url).status_code, 405)

        csrf_client = Client(enforce_csrf_checks=True)
        response = csrf_client.post(
            self.url,
            data=json.dumps({"texto": "filme curto"}),
            content_type="application/json",
            HTTP_ACCEPT="application/json",
        )

        self.assertEqual(response.status_code, 403)


@override_settings(AI_FILTER_ENABLED=False)
class DisabledAiFilterTests(TestCase):
    def test_disabled_endpoint_returns_not_found_without_rate_limit_bucket(self):
        response = self.client.post(
            reverse("movies:interpret_filter"),
            data=json.dumps({"texto": "filme curto"}),
            content_type="application/json",
            HTTP_ACCEPT="application/json",
        )

        self.assertEqual(response.status_code, 404)
        self.assertFalse(RateLimitBucket.objects.exists())


class AiFilterFrontendTests(SimpleTestCase):
    def test_frontend_uses_same_origin_requests_without_html_injection(self):
        source = Path(finders.find("movies/js/ai-filter.js")).read_text(
            encoding="utf-8"
        )

        self.assertIn('credentials: "same-origin"', source)
        self.assertIn('"X-CSRFToken": csrfToken', source)
        self.assertIn("qualfilmehoje:apply-ai-filter", source)
        self.assertNotIn("innerHTML", source)
