from datetime import date, timedelta
from unittest.mock import patch

from django.core.cache import cache
from django.test import SimpleTestCase
from django.utils import timezone

from movies.services.tmdb import (
    TMDBError,
    get_now_playing_movies,
    get_genres,
    get_random_movie,
    get_random_title,
    get_recent_top_movies,
    get_recent_top_series,
    get_title_details,
    get_upcoming_movies,
)


class TMDBServiceTests(SimpleTestCase):
    def setUp(self):
        cache.clear()
        get_genres.cache_clear()

    @patch("movies.services.tmdb._get")
    def test_genres_use_shared_cache_between_process_local_caches(self, mock_get):
        mock_get.return_value = {"genres": [{"id": 18, "name": "Drama"}]}

        first = get_genres("movie")
        get_genres.cache_clear()
        second = get_genres("movie")

        self.assertEqual(first, second)
        mock_get.assert_called_once_with("/genre/movie/list", language="pt-BR")

    @patch("movies.services.tmdb._get")
    def test_recent_top_movies_are_normalised_and_limited(self, mock_get):
        mock_get.return_value = {
            "results": [
                {
                    "id": index,
                    "title": f"Filme {index}",
                    "release_date": "2026-01-01",
                    "vote_average": 9.5 - index / 10,
                    "vote_count": 500,
                    "poster_path": f"/poster-{index}.jpg",
                }
                for index in range(1, 13)
            ]
        }

        movies = get_recent_top_movies()

        self.assertEqual(len(movies), 10)
        self.assertEqual(movies[0]["media_type"], "movie")
        self.assertEqual(movies[0]["poster_url"], "https://image.tmdb.org/t/p/w500/poster-1.jpg")
        discover_call = mock_get.call_args
        self.assertEqual(discover_call.args[0], "/discover/movie")
        self.assertEqual(discover_call.kwargs["sort_by"], "vote_average.desc")
        self.assertEqual(discover_call.kwargs["vote_count.gte"], 20)
        oldest = date.fromisoformat(discover_call.kwargs["primary_release_date.gte"])
        newest = date.fromisoformat(discover_call.kwargs["primary_release_date.lte"])
        self.assertEqual((newest - oldest).days, 30)
        self.assertNotIn("region", discover_call.kwargs)

    @patch("movies.services.tmdb._get")
    def test_recent_top_series_are_normalised_and_limited(self, mock_get):
        mock_get.return_value = {
            "results": [
                {
                    "id": index,
                    "name": f"Série {index}",
                    "original_name": f"Show {index}",
                    "first_air_date": "2026-01-01",
                    "vote_average": 9.5 - index / 10,
                    "vote_count": 300,
                    "poster_path": f"/series-{index}.jpg",
                }
                for index in range(1, 13)
            ]
        }

        series = get_recent_top_series()

        self.assertEqual(len(series), 10)
        self.assertEqual(series[0]["media_type"], "tv")
        self.assertEqual(series[0]["title"], "Série 1")
        self.assertEqual(series[0]["release_date"], "2026-01-01")
        discover_call = mock_get.call_args
        self.assertEqual(discover_call.args[0], "/discover/tv")
        oldest = date.fromisoformat(discover_call.kwargs["first_air_date.gte"])
        newest = date.fromisoformat(discover_call.kwargs["first_air_date.lte"])
        self.assertEqual((newest - oldest).days, 30)

    @patch("movies.services.tmdb._get")
    def test_now_playing_movies_are_localised_for_brazil(self, mock_get):
        mock_get.return_value = {
            "results": [
                {
                    "id": index,
                    "title": f"Filme no cinema {index}",
                    "release_date": "2026-08-01",
                    "vote_average": 8.4,
                    "vote_count": 200,
                    "poster_path": f"/cinema-{index}.jpg",
                }
                for index in range(1, 13)
            ]
        }

        movies = get_now_playing_movies()

        self.assertEqual(len(movies), 10)
        self.assertEqual(movies[0]["media_type"], "movie")
        self.assertEqual(movies[0]["availability_kind"], "cinema")
        self.assertEqual(movies[0]["availability_label"], "Onde assistir · Nos cinemas")
        mock_get.assert_called_once_with(
            "/movie/now_playing",
            language="pt-BR",
            region="BR",
            page=1,
        )

    @patch("movies.services.tmdb._get")
    def test_upcoming_movies_only_include_future_releases_in_date_order(self, mock_get):
        today = timezone.localdate()
        near_release = today + timedelta(days=4)
        later_release = today + timedelta(days=18)
        mock_get.return_value = {
            "results": [
                {
                    "id": 1,
                    "title": "Já lançado",
                    "release_date": (today - timedelta(days=1)).isoformat(),
                },
                {
                    "id": 2,
                    "title": "Estreia distante",
                    "release_date": later_release.isoformat(),
                },
                {
                    "id": 3,
                    "title": "Próxima estreia",
                    "release_date": near_release.isoformat(),
                },
                {"id": 4, "title": "Sem data", "release_date": ""},
            ]
        }

        movies = get_upcoming_movies()

        self.assertEqual([movie["id"] for movie in movies], [3, 2])
        self.assertEqual(movies[0]["availability_kind"], "upcoming")
        self.assertEqual(
            movies[0]["availability_label"],
            f"Estreia em {near_release.strftime('%d/%m/%Y')}",
        )
        mock_get.assert_called_once_with(
            "/movie/upcoming",
            language="pt-BR",
            region="BR",
            page=1,
        )

    @patch("movies.services.tmdb.get_streaming_groups", return_value=[])
    @patch("movies.services.tmdb._fetch_title_extras")
    def test_title_details_use_tmdb_id(self, mock_extras, mock_streaming):
        mock_extras.return_value = {
            "details": {"id": 88, "title": "Ficha teste"},
            "videos": {"results": []},
            "reviews": {"results": []},
            "credits": {"crew": [], "cast": []},
        }

        title = get_title_details("movie", 88)

        self.assertEqual(title["title"], "Ficha teste")
        self.assertEqual(title["media_type"], "movie")
        mock_extras.assert_called_once_with(88, "movie")
        mock_streaming.assert_called_once_with("movie", 88)

    @patch("movies.services.tmdb._get")
    def test_empty_catalog_raises_readable_error(self, mock_get):
        mock_get.return_value = {"total_pages": 0, "total_results": 0, "results": []}

        with self.assertRaisesMessage(TMDBError, "Não encontrei filmes"):
            get_random_movie(min_rating=9.5)

    @patch(
        "movies.services.tmdb.get_streaming_groups",
        return_value=[
            {
                "key": "sub",
                "label": "Incluso na assinatura",
                "providers": [
                    {
                        "provider_name": "Stream",
                        "web_url": "https://example.com/watch/42",
                    }
                ],
            }
        ],
    )
    @patch("movies.services.tmdb._get")
    def test_movie_contains_trailer_reviews_and_provider_groups(
        self, mock_get, mock_streaming
    ):
        def response(path, **params):
            if path == "/discover/movie":
                return {"total_pages": 1, "total_results": 1, "results": [{"id": 42}]}
            if path == "/movie/42":
                return {
                    "id": 42,
                    "title": "Filme teste",
                    "poster_path": "/poster.jpg",
                    "backdrop_path": "/backdrop.jpg",
                    "videos": {
                        "results": [
                            {
                                "site": "YouTube",
                                "key": "abc123",
                                "type": "Trailer",
                                "official": True,
                                "size": 1080,
                            }
                        ]
                    },
                    "reviews": {
                        "results": [
                            {
                                "id": "review-1",
                                "author": "Ana",
                                "content": "Ótimo filme.",
                                "author_details": {"rating": 8},
                            }
                        ]
                    },
                    "credits": {
                        "crew": [
                            {"name": "Diretora Teste", "job": "Director"},
                            {"name": "Roteirista Teste", "job": "Screenplay"},
                        ],
                        "cast": [{"name": "Atriz Teste", "order": 0}],
                    },
                }
            raise AssertionError(f"Chamada inesperada: {path} {params}")

        mock_get.side_effect = response
        movie = get_random_movie(
            genre_id="18",
            min_rating="7.5",
            max_rating="8.4",
            min_release_year=2001,
        )

        discover_call = next(call for call in mock_get.call_args_list if call.args[0] == "/discover/movie")
        self.assertEqual(discover_call.kwargs["vote_average.gte"], 7.5)
        self.assertEqual(discover_call.kwargs["vote_average.lte"], 8.4)
        self.assertEqual(discover_call.kwargs["with_genres"], "18")
        self.assertEqual(
            discover_call.kwargs["primary_release_date.gte"], "2001-01-01"
        )
        details_call = next(call for call in mock_get.call_args_list if call.args[0] == "/movie/42")
        self.assertEqual(
            details_call.kwargs["append_to_response"],
            "videos,reviews,credits",
        )
        self.assertEqual(movie["trailer"]["key"], "abc123")
        self.assertEqual(movie["reviews"][0]["author"], "Ana")
        self.assertEqual(movie["provider_groups"][0]["label"], "Incluso na assinatura")
        self.assertEqual(
            movie["provider_groups"][0]["providers"][0]["web_url"],
            "https://example.com/watch/42",
        )
        mock_streaming.assert_called_once_with("movie", 42)
        self.assertEqual(movie["credit_sections"][0]["names"], ["Diretora Teste"])
        self.assertEqual(movie["credit_sections"][2]["names"], ["Atriz Teste"])

    @patch("movies.services.tmdb.get_streaming_groups", return_value=[])
    @patch("movies.services.tmdb._get")
    def test_movie_advanced_filters_are_combined_in_one_discover_call(
        self, mock_get, _mock_streaming
    ):
        def response(path, **params):
            if path == "/discover/movie":
                return {"total_pages": 1, "total_results": 1, "results": [{"id": 42}]}
            if path == "/movie/42":
                return {
                    "id": 42,
                    "title": "Suspense curto",
                    "videos": {"results": []},
                    "reviews": {"results": []},
                    "credits": {"crew": [], "cast": []},
                }
            if path.endswith(("/videos", "/reviews")):
                return {"results": []}
            raise AssertionError(f"Chamada inesperada: {path} {params}")

        mock_get.side_effect = response
        get_random_title(
            "movie",
            runtime_filter="up_to_90",
            certification="14",
            special_category="korean_thriller",
        )

        discover_call = next(call for call in mock_get.call_args_list if call.args[0] == "/discover/movie")
        self.assertEqual(discover_call.kwargs["with_runtime.lte"], 90)
        self.assertNotIn("with_runtime.gte", discover_call.kwargs)
        self.assertEqual(discover_call.kwargs["certification_country"], "BR")
        self.assertEqual(discover_call.kwargs["certification"], "14")
        self.assertEqual(discover_call.kwargs["region"], "BR")
        self.assertEqual(discover_call.kwargs["with_origin_country"], "KR")
        self.assertEqual(discover_call.kwargs["with_original_language"], "ko")
        self.assertEqual(discover_call.kwargs["with_genres"], "53")

    @patch("movies.services.tmdb.get_streaming_groups", return_value=[])
    @patch("movies.services.tmdb._get")
    def test_dorama_combines_category_and_selected_genre(self, mock_get, _mock_streaming):
        def response(path, **params):
            if path == "/discover/tv":
                return {"total_pages": 1, "total_results": 1, "results": [{"id": 7}]}
            if path == "/tv/7":
                return {
                    "id": 7,
                    "name": "Dorama teste",
                    "videos": {"results": []},
                    "reviews": {"results": []},
                    "aggregate_credits": {"crew": [], "cast": []},
                }
            if path.endswith(("/videos", "/reviews")):
                return {"results": []}
            raise AssertionError(f"Chamada inesperada: {path} {params}")

        mock_get.side_effect = response
        get_random_title(
            "tv",
            genre_id="10749",
            runtime_filter="90_to_120",
            certification="18",
            special_category="korean_drama",
        )

        discover_call = next(call for call in mock_get.call_args_list if call.args[0] == "/discover/tv")
        self.assertEqual(discover_call.kwargs["with_genres"], "10749,18")
        self.assertEqual(discover_call.kwargs["with_origin_country"], "KR")
        self.assertEqual(discover_call.kwargs["with_runtime.gte"], 90)
        self.assertEqual(discover_call.kwargs["with_runtime.lte"], 120)
        self.assertNotIn("certification", discover_call.kwargs)

    @patch("movies.services.tmdb.get_streaming_groups", return_value=[])
    @patch("movies.services.tmdb._get")
    def test_series_uses_tv_endpoints_and_normalises_fields(
        self, mock_get, mock_streaming
    ):
        def response(path, **params):
            if path == "/discover/tv":
                return {"total_pages": 1, "total_results": 1, "results": [{"id": 7}]}
            if path == "/tv/7":
                return {
                    "id": 7,
                    "name": "Série teste",
                    "original_name": "Test show",
                    "first_air_date": "2025-02-01",
                    "episode_run_time": [48],
                    "created_by": [{"name": "Criadora Teste"}],
                    "videos": {"results": []},
                    "reviews": {"results": []},
                    "aggregate_credits": {
                        "crew": [],
                        "cast": [{"name": "Ator Teste", "order": 0}],
                    },
                }
            if path.endswith(("/videos", "/reviews")):
                return {"results": []}
            raise AssertionError(f"Chamada inesperada: {path} {params}")

        mock_get.side_effect = response
        series = get_random_title(
            "tv", genre_id="18", min_rating="7.4", min_release_year=2010
        )

        discover_call = next(call for call in mock_get.call_args_list if call.args[0] == "/discover/tv")
        self.assertEqual(discover_call.kwargs["vote_average.gte"], 7.4)
        self.assertEqual(discover_call.kwargs["first_air_date.gte"], "2010-01-01")
        self.assertEqual(series["title"], "Série teste")
        self.assertEqual(series["release_date"], "2025-02-01")
        self.assertEqual(series["runtime"], 48)
        self.assertEqual(series["credit_sections"][0]["label"], "Criação")
        mock_streaming.assert_called_once_with("tv", 7)
        details_call = next(call for call in mock_get.call_args_list if call.args[0] == "/tv/7")
        self.assertEqual(
            details_call.kwargs["append_to_response"],
            "videos,reviews,aggregate_credits",
        )

    @patch("movies.services.tmdb._get")
    def test_rating_is_limited_to_tmdb_range(self, mock_get):
        mock_get.return_value = {"total_pages": 0, "total_results": 0, "results": []}

        with self.assertRaises(TMDBError):
            get_random_movie(min_rating=99)

        discover_call = mock_get.call_args_list[0]
        self.assertEqual(discover_call.kwargs["vote_average.gte"], 10.0)
        self.assertEqual(discover_call.kwargs["vote_average.lte"], 10.0)

    @patch("movies.services.tmdb.random.sample")
    @patch("movies.services.tmdb.get_streaming_groups")
    @patch("movies.services.tmdb._fetch_title_extras")
    @patch("movies.services.tmdb._get")
    def test_title_with_direct_link_is_preferred(
        self, mock_get, mock_extras, mock_streaming, mock_sample
    ):
        candidates = [{"id": 1}, {"id": 2}]
        mock_get.return_value = {
            "total_pages": 1,
            "total_results": 2,
            "results": candidates,
        }
        mock_sample.return_value = candidates
        mock_streaming.side_effect = [
            [],
            [
                {
                    "key": "sub",
                    "label": "Incluso na assinatura",
                    "providers": [
                        {
                            "provider_name": "Stream",
                            "web_url": "https://example.com/title/2",
                        }
                    ],
                }
            ],
        ]
        mock_extras.return_value = {
            "details": {"id": 2, "title": "Com link"},
            "videos": {"results": []},
            "reviews": {"results": []},
            "credits": {"crew": [], "cast": []},
        }

        title = get_random_title("movie", min_rating=7.0)

        self.assertEqual(title["id"], 2)
        self.assertEqual(title["provider_groups"][0]["providers"][0]["web_url"], "https://example.com/title/2")
        self.assertEqual(mock_streaming.call_count, 2)

    @patch("movies.services.tmdb.random.randint", return_value=2)
    @patch("movies.services.tmdb._get")
    def test_discovery_first_page_is_cached(self, mock_get, _mock_randint):
        first_page = {
            "total_pages": 2,
            "total_results": 20,
            "results": [{"id": 1}],
        }
        second_page = {"results": [{"id": 2}]}
        mock_get.side_effect = [first_page, second_page, second_page]
        filters = {"language": "pt-BR", "vote_average.gte": 7.0}

        from movies.services.tmdb import _load_discovery_page

        _load_discovery_page("movie", None, 7.0, 10.0, filters)
        _load_discovery_page("movie", None, 7.0, 10.0, filters)

        first_page_calls = [
            call
            for call in mock_get.call_args_list
            if call.args[0] == "/discover/movie" and call.kwargs["page"] == 1
        ]
        self.assertEqual(len(first_page_calls), 1)
        self.assertEqual(mock_get.call_count, 2)
