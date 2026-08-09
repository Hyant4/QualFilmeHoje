import uuid
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from movies.models import Favorite, Generation, Title
from movies.services.tmdb import TMDBError


class MovieViewTests(TestCase):
    @patch(
        "movies.views.get_recent_top_series",
        return_value=[
            {
                "id": 77,
                "media_type": "tv",
                "title": "Série em alta",
                "release_date": "2026-01-03",
                "vote_average": 8.9,
            }
        ],
    )
    @patch(
        "movies.views.get_recent_top_movies",
        return_value=[
            {
                "id": 99,
                "media_type": "movie",
                "title": "Filme em alta",
                "release_date": "2026-01-02",
                "vote_average": 9.1,
            }
        ],
    )
    @patch("movies.views.get_genres", return_value=[{"id": 18, "name": "Drama"}])
    def test_home_renders_generator_rating_slider_and_trends(
        self, _mock_genres, _mock_movie_trends, _mock_series_trends
    ):
        response = self.client.get(reverse("movies:home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-media-option="movie"')
        self.assertContains(response, 'type="range"')
        self.assertContains(response, 'step="0.1"')
        self.assertContains(response, "Nota máxima no TMDB")
        self.assertContains(response, "Séries")
        self.assertContains(response, "Nota mínima no TMDB")
        self.assertContains(response, "hero-pov.webp")
        self.assertContains(response, "logo-q.png", count=5)
        self.assertContains(response, 'rel="icon"')
        self.assertContains(response, "Escolhendo sua sessão")
        self.assertContains(response, "tv-screen-glow")
        self.assertContains(response, "ualFilmeHoje")
        self.assertContains(response, 'class="hero-title-main"')
        self.assertContains(response, "Tendências")
        self.assertContains(response, "Filme em alta")
        self.assertContains(
            response,
            reverse("movies:title_detail", args=("movie", 99)),
        )
        self.assertContains(response, "Top 10 séries")
        self.assertContains(response, "Série em alta")
        self.assertContains(
            response,
            reverse("movies:title_detail", args=("tv", 77)),
        )

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
            {
                "media_type": "movie",
                "genre_id": "18",
                "min_rating": "7.5",
                "max_rating": "9.0",
            },
        )

        self.assertEqual(response.status_code, 200)
        mock_random.assert_called_once_with("movie", "18", 7.5, 9.0)
        self.assertContains(response, "Filme teste")
        self.assertContains(response, "Trailer")
        self.assertContains(response, "Reviews")
        self.assertContains(response, "Diretora Teste")
        self.assertContains(response, "★")
        self.assertContains(response, 'class="title-facts"')
        self.assertContains(response, "2024")
        self.assertContains(response, "120 min")
        self.assertContains(response, 'class="quick-facts"')
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
        self.assertContains(response, 'data-error-alert')
        self.assertContains(response, "Sorteio não concluído")

    @patch("movies.views.get_random_title")
    @patch("movies.views.get_genres", return_value=[])
    def test_invalid_filters_are_normalised(self, _mock_genres, mock_random):
        mock_random.return_value = {"title": "Filme", "reviews": [], "provider_groups": []}

        response = self.client.post(
            reverse("movies:generate_movie"),
            {"genre_id": "não-é-id", "min_rating": "não-é-nota"},
        )

        self.assertEqual(response.status_code, 200)
        mock_random.assert_called_once_with("movie", None, 6.0, 10.0)

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
            {
                "media_type": "tv",
                "genre_id": "10765",
                "min_rating": "6.1",
                "max_rating": "8.7",
            },
        )

        self.assertEqual(response.status_code, 200)
        mock_random.assert_called_once_with("tv", "10765", 6.1, 8.7)
        self.assertContains(response, 'value="tv" data-media-input')
        self.assertContains(response, "Série teste")

    @patch("movies.views.get_random_title")
    @patch("movies.views.get_genres", return_value=[])
    def test_maximum_rating_never_stays_below_minimum(
        self, _mock_genres, mock_random
    ):
        mock_random.return_value = {
            "title": "Filme",
            "reviews": [],
            "provider_groups": [],
        }

        self.client.post(
            reverse("movies:generate_movie"),
            {"min_rating": "8.4", "max_rating": "6.0"},
        )

        mock_random.assert_called_once_with("movie", None, 8.4, 8.4)

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

    def test_known_title_can_be_added_to_my_list_without_generation(self):
        title = Title.objects.create(tmdb_id=7, media_type=Title.TV, name="Série conhecida")

        response = self.client.post(
            reverse("movies:toggle_favorite"),
            {"media_type": "tv", "tmdb_id": "7"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["favorited"])
        self.assertIn("minha lista", response.json()["message"])
        self.assertTrue(Favorite.objects.filter(title=title).exists())

    @patch("movies.views.get_title_details")
    def test_trending_title_opens_own_details_page(self, mock_details):
        mock_details.return_value = {
            "id": 88,
            "title": "Tendência teste",
            "original_title": "Test trend",
            "media_type": "movie",
            "vote_average": 8.8,
            "vote_count": 900,
            "release_date": "2026-03-12",
            "runtime": 110,
            "genres": [{"name": "Drama"}],
            "reviews": [],
            "provider_groups": [],
            "credit_sections": [],
        }

        response = self.client.get(
            reverse("movies:title_detail", args=("movie", 88))
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tendência teste")
        self.assertContains(response, "Informações do TMDB")
        self.assertContains(response, "Adicionar à minha lista")
        self.assertNotContains(response, 'class="hero"')
        self.assertTrue(Title.objects.filter(tmdb_id=88, media_type="movie").exists())

    def test_favorite_endpoint_rejects_get(self):
        response = self.client.get(reverse("movies:toggle_favorite"))

        self.assertEqual(response.status_code, 405)
