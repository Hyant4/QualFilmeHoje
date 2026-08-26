import uuid
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from movies.models import Favorite, Generation, Title
from movies.services.tmdb import TMDBError, TMDBNotFound
from movies.tests.factories import create_title, create_user, tmdb_title_payload


class MovieViewTests(TestCase):
    def test_favorites_page_renders_four_column_cards_and_account_note(self):
        visitor_id = uuid.uuid4()
        session = self.client.session
        session["visitor_id"] = str(visitor_id)
        session.save()
        title = create_title(
            tmdb_id=321,
            media_type="movie",
            name="Filme guardado",
            poster_url="https://image.tmdb.org/t/p/w500/poster.jpg",
            vote_average=8.4,
        )
        Favorite.objects.create(visitor_id=visitor_id, title=title)

        response = self.client.get(reverse("movies:favorites"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Minha lista")
        self.assertContains(response, "Filme guardado")
        self.assertContains(response, 'class="favorites-grid"')
        self.assertContains(response, "Crie uma conta gratuita")
        self.assertContains(response, "poster.jpg")

    def test_authenticated_favorites_page_uses_profile_list_without_signup_note(self):
        user = create_user(
            username="colecionador",
            email="colecionador@example.com",
            password="CinemaPortfolio2026!",
        )
        title = create_title(
            tmdb_id=654,
            media_type="tv",
            name="Série do perfil",
        )
        Favorite.objects.create(visitor_id=uuid.uuid4(), user=user, title=title)
        self.client.force_login(user)

        response = self.client.get(reverse("movies:favorites"))

        self.assertContains(response, "Série do perfil")
        self.assertNotContains(response, "Crie uma conta gratuita")

    @patch(
        "movies.views.get_upcoming_movies",
        return_value=[
            {
                "id": 66,
                "media_type": "movie",
                "title": "Filme futuro",
                "release_date": "2026-09-20",
                "availability_label": "Estreia em 20/09/2026",
            }
        ],
    )
    @patch(
        "movies.views.get_now_playing_movies",
        return_value=[
            {
                "id": 55,
                "media_type": "movie",
                "title": "Filme no cinema",
                "release_date": "2026-08-01",
                "vote_average": 8.1,
                "availability_label": "Onde assistir · Nos cinemas",
            }
        ],
    )
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
        self,
        _mock_genres,
        _mock_movie_trends,
        _mock_series_trends,
        _mock_now_playing,
        _mock_upcoming,
    ):
        response = self.client.get(reverse("movies:home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<script type="module" src="/static/movies/js/site.js"></script>')
        self.assertContains(response, 'data-media-option="movie"')
        self.assertContains(response, 'type="range"')
        self.assertContains(response, 'step="0.1"')
        self.assertContains(response, 'name="min_release_year"')
        self.assertContains(response, 'name="max_release_year"')
        self.assertContains(response, 'name="runtime_filter"')
        self.assertContains(response, 'name="certification"')
        self.assertNotContains(response, 'name="special_category"')
        self.assertNotContains(response, ">Estilo<")
        self.assertContains(response, 'value="special:korean_thriller"')
        self.assertContains(response, 'value="special:korean_drama"')
        self.assertContains(response, "Thriller coreano")
        self.assertContains(response, "Dorama coreano")
        self.assertContains(response, 'step="1"')
        self.assertContains(response, "Janela de lançamento")
        self.assertContains(response, "Faixa de notas no TMDB")
        self.assertContains(response, "Séries")
        self.assertContains(response, "A partir de")
        self.assertContains(response, "Até")
        self.assertContains(response, "hero-session-focus.webp")
        self.assertContains(response, "logo-q.png", count=5)
        self.assertContains(response, 'rel="icon"')
        self.assertContains(response, "Escolha sua sessão")
        self.assertContains(response, "tv-screen-glow")
        self.assertContains(response, "ualFilmeHoje")
        self.assertContains(response, 'class="hero-title-main"')
        self.assertContains(response, "Os 10 filmes em alta")
        self.assertContains(response, "Filme em alta")
        self.assertContains(
            response,
            reverse("movies:title_detail", args=("movie", 99)),
        )
        self.assertContains(response, "As 10 séries em alta")
        self.assertContains(response, "Série em alta")
        self.assertContains(
            response,
            reverse("movies:title_detail", args=("tv", 77)),
        )
        self.assertContains(response, "Nos cinemas")
        self.assertContains(response, "Filme no cinema")
        self.assertContains(response, "Onde assistir · Nos cinemas")
        self.assertContains(
            response,
            reverse("movies:title_detail", args=("movie", 55)),
        )
        self.assertContains(response, "Em breve")
        self.assertContains(response, "Filme futuro")
        self.assertContains(response, "Estreia em 20/09/2026")
        self.assertContains(
            response,
            reverse("movies:title_detail", args=("movie", 66)),
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
            "backdrop_url": "https://image.tmdb.org/t/p/w1280/backdrop-teste.jpg",
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
                "min_release_year": "2001",
                "max_release_year": "2012",
            },
        )

        self.assertEqual(response.status_code, 200)
        mock_random.assert_called_once_with(
            "movie",
            "18",
            7.5,
            9.0,
            min_release_year=2001,
            max_release_year=2012,
            include_streaming=False,
        )
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
        self.assertContains(response, 'data-has-backdrop="true"')
        self.assertContains(response, 'data-hero-backdrop')
        self.assertContains(response, "backdrop-teste.jpg")
        rendered = response.content.decode()
        self.assertLess(rendered.index('class="session-panel"'), rendered.index('class="result-section'))
        self.assertLess(rendered.index('class="result-section'), rendered.index('class="discovery-copy"'))
        self.assertLess(rendered.index('class="discovery-copy"'), rendered.index('class="trends-section"'))

    @patch("movies.views.get_random_title")
    @patch("movies.views.get_genres", return_value=[])
    def test_generate_passes_advanced_movie_filters(self, _mock_genres, mock_random):
        mock_random.return_value = None

        response = self.client.post(
            reverse("movies:generate_movie"),
            {
                "media_type": "movie",
                "runtime_filter": "up_to_90",
                "certification": "14",
                "genre_id": "special:korean_thriller",
            },
        )

        self.assertEqual(response.status_code, 200)
        mock_random.assert_called_once_with(
            "movie",
            None,
            6.0,
            10.0,
            min_release_year=1900,
            include_streaming=False,
            runtime_filter="up_to_90",
            certification="14",
            special_category="korean_thriller",
        )
        self.assertContains(response, '<option value="up_to_90" selected>')
        self.assertContains(response, '<option value="14" selected>')
        self.assertContains(response, '<option value="special:korean_thriller" selected>')

    @patch("movies.views.get_random_title")
    @patch("movies.views.get_genres", return_value=[])
    def test_series_ignores_movie_certification_and_accepts_dorama(self, _mock_genres, mock_random):
        mock_random.return_value = None

        response = self.client.post(
            reverse("movies:generate_movie"),
            {
                "media_type": "tv",
                "runtime_filter": "90_to_120",
                "certification": "18",
                "genre_id": "special:korean_drama",
            },
        )

        mock_random.assert_called_once_with(
            "tv",
            None,
            6.0,
            10.0,
            min_release_year=1900,
            include_streaming=False,
            runtime_filter="90_to_120",
            special_category="korean_drama",
        )
        self.assertContains(
            response,
            'class="field certification-field" data-movie-only hidden',
        )
        self.assertContains(
            response,
            'select id="certification" name="certification" disabled',
        )

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
    def test_anonymous_generation_is_kept_out_of_database(
        self, _mock_genres, mock_random
    ):
        mock_random.return_value = tmdb_title_payload(
            id=77,
            title="Filme no navegador",
            vote_average=7.7,
        )

        response = self.client.post(
            reverse("movies:generate_movie"),
            {"media_type": "movie", "min_rating": "6.5"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Title.objects.exists())
        self.assertFalse(Generation.objects.exists())
        self.assertContains(response, 'id="anonymous-history-item"')
        self.assertContains(response, "Filme no navegador")

    def test_anonymous_home_does_not_read_legacy_generation_history(self):
        visitor_id = uuid.uuid4()
        session = self.client.session
        session["visitor_id"] = str(visitor_id)
        session.save()
        title = create_title(
            tmdb_id=78,
            media_type=Title.MOVIE,
            name="Historico antigo",
        )
        Generation.objects.create(
            visitor_id=visitor_id,
            title=title,
            min_rating=6.0,
        )

        response = self.client.get(reverse("movies:home"))

        self.assertNotContains(response, "Historico antigo")
        self.assertContains(response, "data-browser-history-list")

    @patch("movies.views.get_random_title")
    @patch("movies.views.get_genres", return_value=[])
    def test_invalid_filters_are_normalised(self, _mock_genres, mock_random):
        mock_random.return_value = {"title": "Filme", "reviews": [], "provider_groups": []}

        response = self.client.post(
            reverse("movies:generate_movie"),
            {"genre_id": "não-é-id", "min_rating": "não-é-nota"},
        )

        self.assertEqual(response.status_code, 200)
        mock_random.assert_called_once_with(
            "movie", None, 6.0, 10.0, min_release_year=1900, include_streaming=False
        )

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
        mock_random.assert_called_once_with(
            "tv", "10765", 6.1, 8.7, min_release_year=1900, include_streaming=False
        )
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

        mock_random.assert_called_once_with(
            "movie", None, 8.4, 8.4, min_release_year=1900, include_streaming=False
        )

    @patch("movies.views.get_random_title")
    @patch("movies.views.get_genres", return_value=[])
    def test_release_year_is_limited_to_supported_range(
        self, _mock_genres, mock_random
    ):
        mock_random.return_value = {
            "title": "Filme",
            "reviews": [],
            "provider_groups": [],
        }

        response = self.client.post(
            reverse("movies:generate_movie"),
            {"min_release_year": "9999", "max_release_year": "2000"},
        )

        self.assertEqual(response.status_code, 200)
        mock_random.assert_called_once_with(
            "movie",
            None,
            6.0,
            10.0,
            min_release_year=timezone.localdate().year,
            max_release_year=timezone.localdate().year,
            include_streaming=False,
        )

    def test_favorite_can_be_added_and_removed_only_from_visitor_history(self):
        visitor_id = uuid.uuid4()
        session = self.client.session
        session["visitor_id"] = str(visitor_id)
        session.save()
        title = create_title(
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
        title = create_title(tmdb_id=7, media_type=Title.TV, name="Série conhecida")

        response = self.client.post(
            reverse("movies:toggle_favorite"),
            {"media_type": "tv", "tmdb_id": "7"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["favorited"])
        self.assertIn("minha lista", response.json()["message"])
        self.assertTrue(Favorite.objects.filter(title=title).exists())

    @patch("movies.views.get_title_details")
    def test_trending_title_details_get_does_not_write_business_data(self, mock_details):
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
        self.assertFalse(Title.objects.filter(tmdb_id=88, media_type="movie").exists())
        self.assertNotIn("sessionid", self.client.cookies)
        mock_details.assert_called_once_with("movie", 88, include_streaming=False)

    @patch("movies.views.get_streaming_groups")
    @patch("movies.views.get_title_details")
    def test_streaming_links_are_returned_as_json(
        self,
        mock_details,
        mock_streaming,
    ):
        call_order = []

        def validate_title(*_args, **_kwargs):
            call_order.append("tmdb")

        def fetch_streaming(*_args):
            call_order.append("watchmode")
            return [
                {
                    "key": "sub",
                    "label": "Incluso na assinatura",
                    "providers": [
                        {
                            "provider_name": "Stream Teste",
                            "web_url": "https://example.com/watch/88",
                        }
                    ],
                }
            ]

        mock_details.side_effect = validate_title
        mock_streaming.side_effect = fetch_streaming

        response = self.client.get(
            reverse("movies:streaming_links", args=("movie", 88))
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["groups"][0]["key"], "sub")
        self.assertEqual(response["Cache-Control"], "private, max-age=21600")
        mock_details.assert_called_once_with("movie", 88, include_streaming=False)
        mock_streaming.assert_called_once_with("movie", 88)
        self.assertEqual(call_order, ["tmdb", "watchmode"])

    @patch("movies.views.get_streaming_groups")
    @patch(
        "movies.views.get_title_details",
        side_effect=TMDBNotFound("O título não foi encontrado no TMDB."),
    )
    def test_streaming_links_do_not_call_watchmode_for_missing_title(
        self,
        _mock_details,
        mock_streaming,
    ):
        response = self.client.get(
            reverse("movies:streaming_links", args=("movie", 999))
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["groups"], [])
        mock_streaming.assert_not_called()

    def test_streaming_links_reject_invalid_media_type(self):
        response = self.client.get(
            reverse("movies:streaming_links", args=("invalid", 88))
        )

        self.assertEqual(response.status_code, 400)

    @patch("movies.views.get_title_details")
    def test_favorite_post_persists_a_title_not_seen_before(self, mock_details):
        mock_details.return_value = {
            "id": 91,
            "title": "Persistido somente no POST",
            "original_title": "Saved on POST",
            "media_type": "movie",
            "release_date": "2026-04-10",
            "vote_average": 8.1,
        }

        response = self.client.post(
            reverse("movies:toggle_favorite"),
            {"media_type": "movie", "tmdb_id": "91"},
        )

        self.assertEqual(response.status_code, 200)
        mock_details.assert_called_once_with(
            "movie",
            91,
            include_streaming=False,
        )
        title = Title.objects.get(tmdb_id=91, media_type="movie")
        self.assertTrue(Favorite.objects.filter(title=title).exists())

    def test_favorite_endpoint_rejects_get(self):
        response = self.client.get(reverse("movies:toggle_favorite"))

        self.assertEqual(response.status_code, 405)

    def test_invalid_favorite_does_not_create_session_or_business_data(self):
        response = self.client.post(
            reverse("movies:toggle_favorite"),
            {"media_type": "invalid", "tmdb_id": "not-an-id"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertNotIn("sessionid", self.client.cookies)
        self.assertFalse(Title.objects.exists())
        self.assertFalse(Favorite.objects.exists())
