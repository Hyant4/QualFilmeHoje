import uuid
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from movies.models import Favorite, Generation, Title
from movies.services.tmdb import TMDBError


class MovieViewTests(TestCase):
    @patch("movies.views.get_genres", return_value=[{"id": 18, "name": "Drama"}])
    def test_home_renders_generator_and_rating_slider(self, _mock_genres):
        response = self.client.get(reverse("movies:home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-media-option="movie"')
        self.assertContains(response, 'type="range"')
        self.assertContains(response, 'step="0.1"')
        self.assertContains(response, "Séries")
        self.assertContains(response, "Nota mínima no TMDB")
        self.assertContains(response, "hero-pov.webp")
        self.assertContains(response, "logo-q.png", count=3)
        self.assertContains(response, "Escolhendo sua sessão")
        self.assertContains(response, "tv-screen-glow")
        self.assertContains(response, "ualFilmeHoje")

    @patch("movies.views.get_random_title")
    @patch("movies.views.get_genres", return_value=[{"id": 18, "name": "Drama"}])
    def test_generate_passes_selected_filters_and_renders_result(self, _mock_genres, mock_random):
        mock_random.return_value = {
            "id": 42,
            "title": "Filme teste",
            "vote_average": 8.2,
            "vote_count": 123,
            "release_date": "2024-01-01",
            "runtime": 120,
            "genres": [{"name": "Drama"}],
            "overview": "Uma sinopse.",
            "reviews": [],
            "provider_groups": [
                {
                    "key": "sub",
                    "label": "Incluso na assinatura",
                    "providers": [
                        {
                            "provider_name": "Stream Direto",
                            "web_url": "https://example.com/watch/movie",
                        }
                    ],
                }
            ],
            "credit_sections": [
                {"label": "Direção", "names": ["Diretora Teste"]},
                {"label": "Elenco principal", "names": ["Atriz Teste"]},
            ],
            "media_type": "movie",
        }

        response = self.client.post(
            reverse("movies:generate_movie"),
            {"media_type": "movie", "genre_id": "18", "min_rating": "7.5"},
        )

        self.assertEqual(response.status_code, 200)
        mock_random.assert_called_once_with("movie", "18", 7.5)
        self.assertContains(response, "Filme teste")
        self.assertContains(response, "Trailer")
        self.assertContains(response, "Reviews")
        self.assertContains(response, "Diretora Teste")
        self.assertContains(response, "★")
        self.assertContains(response, 'href="https://example.com/watch/movie"')
        self.assertEqual(Title.objects.count(), 1)
        self.assertEqual(Generation.objects.count(), 1)
        self.assertEqual(Generation.objects.get().genre_name, "Drama")

    @patch("movies.views.get_random_title", side_effect=TMDBError("Falha controlada"))
    @patch("movies.views.get_genres", side_effect=TMDBError("Falha nos gêneros"))
    def test_api_failure_does_not_escape_as_server_error(self, _mock_genres, _mock_random):
        response = self.client.post(reverse("movies:generate_movie"), {})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Falha controlada")

    @patch("movies.views.get_random_title")
    @patch("movies.views.get_genres", return_value=[])
    def test_invalid_filters_are_normalised(self, _mock_genres, mock_random):
        mock_random.return_value = {"title": "Filme", "reviews": [], "provider_groups": []}

        response = self.client.post(
            reverse("movies:generate_movie"),
            {"genre_id": "não-é-id", "min_rating": "não-é-nota"},
        )

        self.assertEqual(response.status_code, 200)
        mock_random.assert_called_once_with("movie", None, 6.0)

    @patch("movies.views.get_random_title")
    @patch("movies.views.get_genres", return_value=[])
    def test_series_selection_is_preserved(self, _mock_genres, mock_random):
        mock_random.return_value = {
            "title": "Série teste",
            "media_type": "tv",
            "reviews": [],
            "provider_groups": [],
            "credit_sections": [],
        }

        response = self.client.post(
            reverse("movies:generate_movie"),
            {"media_type": "tv", "genre_id": "10765", "min_rating": "6.1"},
        )

        self.assertEqual(response.status_code, 200)
        mock_random.assert_called_once_with("tv", "10765", 6.1)
        self.assertContains(response, 'value="tv" data-media-input')
        self.assertContains(response, "Série teste")

    def test_favorite_can_be_added_and_removed_only_from_visitor_history(self):
        visitor_id = uuid.uuid4()
        session = self.client.session
        session["visitor_id"] = str(visitor_id)
        session.save()
        title = Title.objects.create(
            tmdb_id=42,
            media_type=Title.MOVIE,
            name="Filme teste",
        )
        Generation.objects.create(
            visitor_id=visitor_id,
            title=title,
            min_rating=7.0,
        )

        url = reverse("movies:toggle_favorite")
        response = self.client.post(url, {"media_type": "movie", "tmdb_id": "42"})

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["favorited"])
        self.assertTrue(Favorite.objects.filter(visitor_id=visitor_id, title=title).exists())

        response = self.client.post(url, {"media_type": "movie", "tmdb_id": "42"})

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["favorited"])
        self.assertFalse(Favorite.objects.filter(visitor_id=visitor_id, title=title).exists())

    def test_favorite_rejects_title_outside_visitor_history(self):
        Title.objects.create(tmdb_id=7, media_type=Title.TV, name="Série alheia")

        response = self.client.post(
            reverse("movies:toggle_favorite"),
            {"media_type": "tv", "tmdb_id": "7"},
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(Favorite.objects.count(), 0)

    def test_favorite_endpoint_rejects_get(self):
        response = self.client.get(reverse("movies:toggle_favorite"))

        self.assertEqual(response.status_code, 405)
