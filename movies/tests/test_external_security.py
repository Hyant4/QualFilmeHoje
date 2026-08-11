from unittest.mock import patch
from urllib.request import Request

from django.test import SimpleTestCase, TestCase

from movies.services.http_client import (
    ExternalResponseError,
    NoRedirectHandler,
    open_json,
)
from movies.services.library import save_title_snapshot
from movies.services.tmdb import _choose_trailer, _normalise_reviews
from movies.services.urls import STREAMING_HOSTS, safe_https_url
from movies.services.watchmode import WatchmodeError, get_streaming_groups


class _Headers:
    def __init__(self, content_type="application/json", content_length=None):
        self.content_type = content_type
        self.content_length = content_length

    def get_content_type(self):
        return self.content_type

    def get(self, name):
        return self.content_length if name == "Content-Length" else None


class _Response:
    def __init__(self, body, *, content_type="application/json", length=None):
        self.body = body
        self.headers = _Headers(content_type, length)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self, amount):
        return self.body[:amount]


class ExternalHTTPTests(SimpleTestCase):
    def test_redirects_are_not_followed_with_api_credentials(self):
        request = Request(
            "https://api.example.test/resource",
            headers={"Authorization": "Bearer secret"},
        )

        redirected = NoRedirectHandler().redirect_request(
            request,
            None,
            302,
            "Found",
            {},
            "https://attacker.example/collect",
        )

        self.assertIsNone(redirected)

    @patch("movies.services.http_client._NO_REDIRECT_OPENER.open")
    def test_json_reader_rejects_wrong_content_type_and_oversized_body(self, opener):
        request = Request("https://api.example.test/resource")
        opener.return_value = _Response(b"{}", content_type="text/html")
        with self.assertRaises(ExternalResponseError):
            open_json(request, timeout=1, max_bytes=10)

        opener.return_value = _Response(b'{"long": true}', length="14")
        with self.assertRaises(ExternalResponseError):
            open_json(request, timeout=1, max_bytes=10)

    def test_external_urls_require_https_and_an_allowlisted_host(self):
        self.assertEqual(
            safe_https_url(
                "https://www.primevideo.com/detail/example", STREAMING_HOSTS
            ),
            "https://www.primevideo.com/detail/example",
        )
        for unsafe in (
            "http://netflix.com/title/1",
            "https://netflix.com.evil.example/title/1",
            "https://user:password@netflix.com/title/1",
            "javascript:alert(1)",
        ):
            with self.subTest(unsafe=unsafe):
                self.assertEqual(safe_https_url(unsafe, STREAMING_HOSTS), "")

    def test_tmdb_trailers_and_reviews_are_normalised(self):
        self.assertIsNone(
            _choose_trailer(
                [{"site": "YouTube", "key": "bad/key", "type": "Trailer"}]
            )
        )
        reviews = _normalise_reviews(
            [
                {
                    "id": "1",
                    "author": "User",
                    "content": "x" * 6000,
                    "url": "https://attacker.example/review",
                    "author_details": {"rating": "NaN"},
                }
            ]
        )
        self.assertEqual(reviews[0]["url"], "")
        self.assertEqual(reviews[0]["rating"], 0.0)
        self.assertEqual(len(reviews[0]["content"]), 5000)

    def test_watchmode_rejects_invalid_ids_before_calling_the_api(self):
        with self.assertRaises(WatchmodeError), patch(
            "movies.services.watchmode._get"
        ) as api_get:
            get_streaming_groups("movie", "²")
        api_get.assert_not_called()


class ExternalPersistenceTests(TestCase):
    def test_snapshot_rejects_nan_and_untrusted_poster_hosts(self):
        title = save_title_snapshot(
            {
                "id": 42,
                "media_type": "movie",
                "title": "Teste",
                "vote_average": "NaN",
                "poster_url": "https://attacker.example/poster.jpg",
            }
        )

        self.assertIsNone(title.vote_average)
        self.assertEqual(title.poster_url, "")
        self.assertIsNone(save_title_snapshot({"id": "²", "title": "Inválido"}))
