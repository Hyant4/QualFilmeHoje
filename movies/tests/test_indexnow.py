import json
from unittest.mock import patch
from urllib.error import URLError

from django.core.cache import cache
from django.db import DatabaseError
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from movies.models import Title
from movies.services.indexnow import submit_url
from movies.services.library import save_title_snapshot

CANONICAL_SITE = "https://qualfilmehoje.vercel.app"
INDEXNOW_KEY = "a8c7cb6034564b13897e893feebabe4e"


class _IndexNowResponse:
    status = 202

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self, amount):
        return b""[:amount]


class IndexNowEndpointTests(SimpleTestCase):
    def test_key_is_public_at_the_site_root(self):
        response = self.client.get(reverse("movies:indexnow_key"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), INDEXNOW_KEY)
        self.assertTrue(response["Content-Type"].startswith("text/plain"))
        self.assertEqual(response["X-Robots-Tag"], "noindex")


@override_settings(
    INDEXNOW_ENABLED=True,
    INDEXNOW_KEY=INDEXNOW_KEY,
    SITE_URL=CANONICAL_SITE,
)
class IndexNowClientTests(SimpleTestCase):
    def setUp(self):
        cache.clear()

    @patch("movies.services.indexnow._INDEXNOW_OPENER.open")
    def test_submits_expected_payload_and_deduplicates_url(self, opener):
        opener.return_value = _IndexNowResponse()
        url = f"{CANONICAL_SITE}/titulo/movie/42/"

        self.assertTrue(submit_url(url))
        self.assertTrue(submit_url(url))

        opener.assert_called_once()
        request = opener.call_args.args[0]
        payload = json.loads(request.data.decode("utf-8"))
        self.assertEqual(request.full_url, "https://api.indexnow.org/indexnow")
        self.assertEqual(payload["host"], "qualfilmehoje.vercel.app")
        self.assertEqual(payload["key"], INDEXNOW_KEY)
        self.assertEqual(
            payload["keyLocation"],
            f"{CANONICAL_SITE}/{INDEXNOW_KEY}.txt",
        )
        self.assertEqual(payload["urlList"], [url])

    @patch("movies.services.indexnow._INDEXNOW_OPENER.open")
    def test_rejects_foreign_url_and_absorbs_network_failure(self, opener):
        self.assertFalse(submit_url("https://attacker.example/title/42"))
        opener.assert_not_called()

        opener.side_effect = URLError("offline")
        self.assertFalse(submit_url(f"{CANONICAL_SITE}/titulo/movie/42/"))

    @patch("movies.services.indexnow.cache.get", side_effect=DatabaseError("offline"))
    @patch("movies.services.indexnow._INDEXNOW_OPENER.open")
    def test_cache_failure_does_not_block_submission(self, opener, _cache_get):
        opener.return_value = _IndexNowResponse()

        self.assertTrue(submit_url(f"{CANONICAL_SITE}/titulo/movie/42/"))


class IndexNowPersistenceTests(TestCase):
    @patch("movies.services.library.submit_title_url")
    def test_only_new_title_schedules_notification(self, submit_title_url):
        payload = {
            "id": 42,
            "media_type": Title.MOVIE,
            "title": "Filme novo",
        }

        with self.captureOnCommitCallbacks(execute=True):
            save_title_snapshot(payload)
        with self.captureOnCommitCallbacks(execute=True):
            save_title_snapshot(payload)

        submit_title_url.assert_called_once_with(media_type="movie", tmdb_id=42)
