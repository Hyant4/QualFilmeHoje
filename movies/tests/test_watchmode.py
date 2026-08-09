from unittest.mock import patch

from django.core.cache import cache
from django.test import SimpleTestCase

from movies.services.watchmode import _normalise_sources, get_streaming_groups


class WatchmodeServiceTests(SimpleTestCase):
    def setUp(self):
        cache.clear()

    def test_sources_are_grouped_and_unsafe_links_are_ignored(self):
        sources = [
            {
                "source_id": 1,
                "name": "Prime Video",
                "type": "sub",
                "region": "BR",
                "web_url": "https://primevideo.com/detail/example",
                "format": "4K",
            },
            {
                "source_id": 2,
                "name": "Link inseguro",
                "type": "free",
                "web_url": "javascript:alert(1)",
            },
        ]
        catalog = {1: {"name": "Prime Video", "logo_url": "https://example.com/logo.png"}}

        groups = _normalise_sources(sources, catalog)

        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0]["key"], "sub")
        self.assertEqual(groups[0]["providers"][0]["provider_name"], "Prime Video")
        self.assertEqual(groups[0]["providers"][0]["format"], "4K")

    @patch("movies.services.watchmode._source_catalog", return_value={})
    @patch("movies.services.watchmode._get")
    def test_tmdb_id_is_used_and_result_is_cached(self, mock_get, _mock_catalog):
        mock_get.return_value = [
            {
                "source_id": 1,
                "name": "Netflix",
                "type": "sub",
                "web_url": "https://netflix.com/title/123",
            }
        ]

        first = get_streaming_groups("movie", 278)
        second = get_streaming_groups("movie", 278)

        self.assertEqual(first, second)
        mock_get.assert_called_once_with("/title/movie-278/sources/", regions="BR")
