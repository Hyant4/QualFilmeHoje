import json
from unittest.mock import patch

from django.contrib.auth.models import AnonymousUser
from django.core.cache import cache
from django.http import HttpResponse
from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from movies.security import get_client_ip, rate_limit
from movies.services.tmdb import TMDBNotFound, _fetch_title_extras, get_title_details
from movies.views import _parse_filters


class InputValidationTests(SimpleTestCase):
    def test_filters_reject_nan_unicode_ids_and_huge_values(self):
        request = RequestFactory().post(
            "/gerar/",
            {
                "media_type": "movie",
                "genre_id": "²",
                "min_rating": "NaN",
                "max_rating": "9" * 100,
            },
        )

        self.assertEqual(_parse_filters(request), ("movie", "", 6.0, 10.0))


class ApplicationRateLimitTests(SimpleTestCase):
    def setUp(self):
        cache.clear()
        self.factory = RequestFactory()

    def test_ip_limit_returns_429_and_retry_after(self):
        protected = rate_limit(
            "test",
            ip=(2, 60),
            methods={"GET"},
        )(lambda _request: HttpResponse("ok"))

        responses = []
        for _index in range(3):
            request = self.factory.get("/protegido/")
            request.user = AnonymousUser()
            request.META["REMOTE_ADDR"] = "203.0.113.10"
            responses.append(protected(request))

        self.assertEqual([response.status_code for response in responses], [200, 200, 429])
        self.assertIn("Retry-After", responses[-1])

    @override_settings(IS_VERCEL=True)
    def test_only_the_trusted_proxy_side_of_xff_is_used(self):
        request = self.factory.get(
            "/",
            HTTP_X_FORWARDED_FOR="198.51.100.20, 203.0.113.30",
        )
        request.META["REMOTE_ADDR"] = "127.0.0.1"

        self.assertEqual(get_client_ip(request), "203.0.113.30")


class ExternalLookupOrderingTests(SimpleTestCase):
    def setUp(self):
        cache.clear()

    @patch("movies.services.tmdb._get")
    def test_missing_title_is_negatively_cached(self, mock_get):
        mock_get.side_effect = TMDBNotFound("ausente")

        with self.assertRaises(TMDBNotFound):
            _fetch_title_extras(999, "movie")
        with self.assertRaises(TMDBNotFound):
            _fetch_title_extras(999, "movie")

        self.assertEqual(mock_get.call_count, 1)

    @patch("movies.services.tmdb.get_streaming_groups")
    @patch("movies.services.tmdb._fetch_title_extras")
    def test_tmdb_validation_precedes_watchmode(self, mock_extras, mock_streaming):
        order = []

        def extras(_title_id, _media_type):
            order.append("tmdb")
            return {
                "details": {"id": 88, "title": "Ficha teste"},
                "videos": {"results": []},
                "reviews": {"results": []},
                "credits": {"crew": [], "cast": []},
            }

        def streaming(_media_type, _title_id):
            order.append("watchmode")
            return []

        mock_extras.side_effect = extras
        mock_streaming.side_effect = streaming

        get_title_details("movie", 88)

        self.assertEqual(order, ["tmdb", "watchmode"])


class CSPTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_policy_starts_in_report_only_mode(self):
        response = self.client.get(reverse("account_login"))

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("Content-Security-Policy", response)
        policy = response["Content-Security-Policy-Report-Only"]
        self.assertIn("script-src 'self'", policy)
        self.assertIn("frame-src https://www.youtube-nocookie.com", policy)
        self.assertIn("report-uri /security/csp-report/", policy)
        self.assertNotIn("'unsafe-inline'", policy)

    def test_report_endpoint_redacts_queries_and_ignores_script_samples(self):
        payload = {
            "csp-report": {
                "document-uri": "https://example.com/path?token=secret",
                "blocked-uri": "https://evil.example/x.js?private=value",
                "violated-directive": "script-src",
                "script-sample": "sensitive inline script",
            }
        }

        with self.assertLogs("movies.views", level="WARNING") as logs:
            response = self.client.post(
                reverse("movies:csp_report"),
                data=json.dumps(payload),
                content_type="application/csp-report",
            )

        self.assertEqual(response.status_code, 204)
        rendered = " ".join(logs.output)
        self.assertNotIn("token=secret", rendered)
        self.assertNotIn("private=value", rendered)
        self.assertNotIn("sensitive inline script", rendered)

    def test_oversized_report_is_rejected(self):
        response = self.client.post(
            reverse("movies:csp_report"),
            data=b"x" * (16 * 1024 + 1),
            content_type="application/csp-report",
        )

        self.assertEqual(response.status_code, 413)
