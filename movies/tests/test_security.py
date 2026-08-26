import json
from datetime import timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.core.cache import cache
from django.db import DatabaseError
from django.http import HttpResponse
from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from movies.infrastructure.rate_limits import consume_rate_limit
from movies.models import RateLimitBucket
from movies.security import get_client_ip, rate_limit
from movies.services.tmdb import TMDBNotFound, _fetch_title_extras, get_title_details
from movies.use_cases.home import parse_filters


class DeploymentHeaderTests(SimpleTestCase):
    def test_vercel_static_assets_receive_nosniff(self):
        config = json.loads(
            Path(settings.BASE_DIR, "vercel.json").read_text(encoding="utf-8")
        )

        static_rule = next(
            rule for rule in config["headers"] if rule["source"] == "/static/(.*)"
        )
        headers = {
            header["key"].casefold(): header["value"]
            for header in static_rule["headers"]
        }
        self.assertEqual(headers["x-content-type-options"], "nosniff")


class InputValidationTests(SimpleTestCase):
    def test_filters_reject_nan_unicode_ids_and_huge_values(self):
        request = RequestFactory().post(
            "/gerar/",
            {
                "media_type": "movie",
                "genre_id": "²",
                "min_rating": "NaN",
                "max_rating": "9" * 100,
                "min_release_year": "9" * 100,
            },
        )

        self.assertEqual(
            parse_filters(request),
            (
                "movie",
                "",
                6.0,
                10.0,
                1900,
                timezone.localdate().year,
                "",
                "",
                "",
            ),
        )

    def test_filters_reject_oversized_rating_text(self):
        request = RequestFactory().post(
            "/gerar/",
            {
                "min_rating": "1234567",
                "max_rating": "1234567",
            },
        )

        parsed = parse_filters(request)

        self.assertEqual(parsed[2], 6.0)
        self.assertEqual(parsed[3], 10.0)


class ApplicationRateLimitTests(TestCase):
    def setUp(self):
        RateLimitBucket.objects.all().delete()
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

    @patch("movies.infrastructure.rate_limits.connection")
    def test_postgresql_upsert_qualifies_target_columns(self, db_connection):
        db_connection.vendor = "postgresql"
        db_connection.ops.quote_name.side_effect = lambda value: f'"{value}"'
        cursor = db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchone.return_value = (1, timezone.now() + timedelta(seconds=60))

        accepted, _retry_after = consume_rate_limit(
            "test",
            "ip",
            "203.0.113.10",
            2,
            60,
        )

        sql, parameters = cursor.execute.call_args.args
        table = '"qualfilmehoje_rate_limit"'
        self.assertTrue(accepted)
        self.assertIn(f'{table}."reset_at"', sql)
        self.assertIn(f'{table}."request_count"', sql)
        self.assertEqual(len(parameters), 4)
        self.assertNotIn("203.0.113.10", sql)

    def test_identifier_is_stored_only_as_an_opaque_hmac(self):
        protected = rate_limit("test", ip=(2, 60), methods={"GET"})(
            lambda _request: HttpResponse("ok")
        )
        request = self.factory.get("/protegido/")
        request.user = AnonymousUser()
        request.META["REMOTE_ADDR"] = "203.0.113.10"

        protected(request)

        bucket = RateLimitBucket.objects.get()
        self.assertTrue(bucket.bucket_key.startswith("v2:"))
        self.assertNotIn("203.0.113.10", bucket.bucket_key)
        self.assertNotIn("test", bucket.bucket_key)

    def test_expired_bucket_starts_a_new_window(self):
        protected = rate_limit("test", ip=(1, 60), methods={"GET"})(
            lambda _request: HttpResponse("ok")
        )
        request = self.factory.get("/protegido/")
        request.user = AnonymousUser()
        request.META["REMOTE_ADDR"] = "203.0.113.10"
        self.assertEqual(protected(request).status_code, 200)
        self.assertEqual(protected(request).status_code, 429)

        RateLimitBucket.objects.update(
            reset_at=timezone.now() - timedelta(seconds=1)
        )

        self.assertEqual(protected(request).status_code, 200)
        bucket = RateLimitBucket.objects.get()
        self.assertEqual(bucket.request_count, 1)

    def test_different_ip_has_an_independent_bucket(self):
        protected = rate_limit("test", ip=(1, 60), methods={"GET"})(
            lambda _request: HttpResponse("ok")
        )
        statuses = []
        for address in ("203.0.113.10", "203.0.113.20"):
            request = self.factory.get("/protegido/")
            request.user = AnonymousUser()
            request.META["REMOTE_ADDR"] = address
            statuses.append(protected(request).status_code)

        self.assertEqual(statuses, [200, 200])
        self.assertEqual(RateLimitBucket.objects.count(), 2)

    def test_different_scope_has_an_independent_bucket(self):
        first_scope = rate_limit("first", ip=(1, 60), methods={"GET"})(
            lambda _request: HttpResponse("ok")
        )
        second_scope = rate_limit("second", ip=(1, 60), methods={"GET"})(
            lambda _request: HttpResponse("ok")
        )
        request = self.factory.get("/protegido/")
        request.user = AnonymousUser()
        request.META["REMOTE_ADDR"] = "203.0.113.10"

        self.assertEqual(first_scope(request).status_code, 200)
        self.assertEqual(first_scope(request).status_code, 429)
        self.assertEqual(second_scope(request).status_code, 200)
        self.assertEqual(RateLimitBucket.objects.count(), 2)

    def test_different_user_has_an_independent_bucket(self):
        protected = rate_limit("test", user=(1, 60), methods={"GET"})(
            lambda _request: HttpResponse("ok")
        )
        statuses = []
        for user_id in (41, 42):
            request = self.factory.get("/protegido/")
            request.user = SimpleNamespace(is_authenticated=True, pk=user_id)
            statuses.append(protected(request).status_code)

        self.assertEqual(statuses, [200, 200])
        self.assertEqual(RateLimitBucket.objects.count(), 2)
        for bucket_key in RateLimitBucket.objects.values_list(
            "bucket_key", flat=True
        ):
            self.assertRegex(bucket_key, r"^v2:[0-9a-f]{64}$")

    def test_method_outside_scope_does_not_consume_a_bucket(self):
        protected = rate_limit("test", ip=(1, 60), methods={"POST"})(
            lambda _request: HttpResponse("ok")
        )
        request = self.factory.get("/protegido/")
        request.user = AnonymousUser()
        request.META["REMOTE_ADDR"] = "203.0.113.10"

        response = protected(request)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(RateLimitBucket.objects.exists())

    @patch(
        "movies.security.consume_rate_limit",
        side_effect=DatabaseError("offline"),
    )
    def test_store_failure_fails_closed(self, _consume):
        protected = rate_limit("test", ip=(1, 60), methods={"GET"})(
            lambda _request: HttpResponse("ok")
        )
        request = self.factory.get("/protegido/")
        request.user = AnonymousUser()
        request.META["REMOTE_ADDR"] = "203.0.113.10"

        with self.assertLogs("movies.security", level="ERROR"):
            response = protected(request)

        self.assertEqual(response.status_code, 503)

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
