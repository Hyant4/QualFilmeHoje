import json
import re
from unittest.mock import patch
from xml.etree import ElementTree

from django.test import TestCase, override_settings
from django.urls import reverse

from movies.models import Title
from movies.services.tmdb import TMDBError, TMDBNotFound

CANONICAL_SITE = "https://qualfilmehoje.vercel.app"
GOOGLE_VERIFICATION_TOKEN = "8J1E6sV8WN1zxIrmvUWlcKWKDZ8lurm1bycxUgO2ssc"
BING_VERIFICATION_TOKEN = "BAADAFCE767CC2A73B3A5DEF51A06BC7"


@override_settings(SITE_URL=CANONICAL_SITE)
class SEOEndpointsTests(TestCase):
    def test_home_exposes_google_search_console_verification(self):
        response = self.client.get(reverse("movies:home"))

        self.assertContains(
            response,
            f'<meta name="google-site-verification" content="{GOOGLE_VERIFICATION_TOKEN}">',
        )

    def test_home_exposes_bing_webmaster_verification(self):
        response = self.client.get(reverse("movies:home"))

        self.assertContains(
            response,
            f'<meta name="msvalidate.01" content="{BING_VERIFICATION_TOKEN}">',
        )

    def test_robots_allows_public_pages_and_references_sitemap(self):
        response = self.client.get(reverse("movies:robots_txt"))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response["Content-Type"].startswith("text/plain"))
        body = response.content.decode()
        self.assertIn("User-agent: *\nAllow: /", body)
        self.assertIn("Disallow: /admin/", body)
        self.assertIn(
            f"Sitemap: {CANONICAL_SITE}/sitemap.xml",
            body,
        )

    def test_sitemap_contains_only_canonical_indexable_urls(self):
        title = Title.objects.create(
            tmdb_id=42,
            media_type=Title.MOVIE,
            name="Filme indexável",
        )

        response = self.client.get(reverse("movies:sitemap"))

        self.assertEqual(response.status_code, 200)
        self.assertIn("xml", response["Content-Type"])
        root = ElementTree.fromstring(response.content)
        namespace = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        locations = [node.text for node in root.findall("s:url/s:loc", namespace)]
        self.assertIn(f"{CANONICAL_SITE}/", locations)
        self.assertIn(
            f"{CANONICAL_SITE}{reverse('movies:random_movies')}",
            locations,
        )
        self.assertIn(
            f"{CANONICAL_SITE}{reverse('movies:title_detail', args=(title.media_type, title.tmdb_id))}",
            locations,
        )
        self.assertNotIn(f"{CANONICAL_SITE}/privacidade/", locations)
        self.assertNotContains(response, "<priority>")
        self.assertNotContains(response, "<changefreq>")


@override_settings(
    SITE_URL=CANONICAL_SITE,
    GOOGLE_SITE_VERIFICATION="google-verification-token",
)
class SEOMetadataTests(TestCase):
    def test_home_has_canonical_metadata_and_valid_json_ld(self):
        response = self.client.get(reverse("movies:home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Qual filme assistir hoje? | QualFilmeHoje",
        )
        self.assertContains(
            response,
            f'<link rel="canonical" href="{CANONICAL_SITE}/">',
            html=True,
        )
        self.assertContains(response, '<meta name="robots" content="index, follow">')
        self.assertContains(
            response,
            '<meta name="google-site-verification" content="google-verification-token">',
        )

        html = response.content.decode()
        match = re.search(
            r'<script type="application/ld\+json">(.*?)</script>',
            html,
            re.DOTALL,
        )
        self.assertIsNotNone(match)
        payload = json.loads(match.group(1))
        types = {entry["@type"] for entry in payload["@graph"]}
        self.assertEqual(payload["@context"], "https://schema.org")
        self.assertEqual(types, {"WebSite", "WebApplication"})
        app = next(
            entry for entry in payload["@graph"] if entry["@type"] == "WebApplication"
        )
        self.assertEqual(app["offers"]["price"], "0")
        self.assertEqual(app["offers"]["priceCurrency"], "BRL")
        self.assertNotIn("[Website URL]", json.dumps(payload))

        html = response.content.decode()
        self.assertEqual(len(re.findall(r"<h1(?:\s|>)", html)), 1)
        self.assertContains(
            response,
            f'href="{reverse("movies:random_movies")}"',
        )

    def test_random_movies_page_has_unique_metadata_content_and_schema(self):
        path = reverse("movies:random_movies")
        response = self.client.get(path)

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Sorteador de filmes aleatórios | QualFilmeHoje",
        )
        self.assertContains(
            response,
            f'<link rel="canonical" href="{CANONICAL_SITE}{path}">',
        )
        self.assertContains(response, '<meta name="robots" content="index, follow">')
        self.assertContains(response, "Filmes aleatórios, mas dentro do seu gosto")
        self.assertContains(
            response,
            f'href="{reverse("movies:home")}#gerador"',
        )

        html = response.content.decode()
        self.assertEqual(len(re.findall(r"<h1(?:\s|>)", html)), 1)
        title = re.search(r"<title>(.*?)</title>", html).group(1)
        self.assertLessEqual(len(title), 60)
        description = re.search(
            r'<meta name="description" content="(.*?)">',
            html,
        ).group(1)
        self.assertGreaterEqual(len(description), 120)
        self.assertLessEqual(len(description), 160)

        match = re.search(
            r'<script type="application/ld\+json">(.*?)</script>',
            html,
            re.DOTALL,
        )
        self.assertIsNotNone(match)
        payload = json.loads(match.group(1))
        self.assertEqual(payload["@type"], "WebPage")
        self.assertEqual(payload["url"], f"{CANONICAL_SITE}{path}")
        self.assertEqual(payload["mainEntity"]["@type"], "WebApplication")

    def test_privacy_and_account_pages_are_noindex(self):
        privacy = self.client.get(reverse("movies:privacy"))
        login = self.client.get("/accounts/login/")

        self.assertContains(
            privacy,
            '<meta name="robots" content="noindex, follow">',
        )
        self.assertContains(
            login,
            '<meta name="robots" content="noindex, follow">',
        )

    @patch("movies.views.get_title_details")
    def test_title_page_has_its_own_canonical_and_description(self, mock_details):
        mock_details.return_value = {
            "id": 88,
            "title": "Um filme com um nome deliberadamente muito longo para SEO",
            "media_type": "movie",
            "backdrop_url": "https://image.tmdb.org/t/p/w1280/backdrop.jpg",
            "reviews": [],
            "provider_groups": [],
            "credit_sections": [],
        }

        path = reverse("movies:title_detail", args=("movie", 88))
        response = self.client.get(path)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'<link rel="canonical" href="{CANONICAL_SITE}{path}">')
        self.assertContains(
            response,
            "Veja sinopse, trailer, avaliação, elenco e onde assistir Um filme com um nome deliberadamente muito longo para SEO no Brasil.",
        )
        html = response.content.decode()
        title = re.search(r"<title>(.*?)</title>", html).group(1)
        self.assertLessEqual(len(title), 59)
        self.assertEqual(len(re.findall(r"<h1(?:\s|>)", html)), 1)
        mock_details.assert_called_once_with("movie", 88, include_streaming=False)
        self.assertContains(
            response,
            'alt="Imagem de fundo de Um filme com um nome deliberadamente muito longo para SEO"',
        )
        self.assertNotContains(response, 'type="application/ld+json"')

    @patch("movies.views.get_title_details", side_effect=TMDBNotFound("Ausente"))
    def test_missing_title_returns_404_and_noindex(self, _mock_details):
        response = self.client.get(
            reverse("movies:title_detail", args=("movie", 999))
        )

        self.assertEqual(response.status_code, 404)
        self.assertContains(
            response,
            '<meta name="robots" content="noindex, nofollow">',
            status_code=404,
        )

    @patch("movies.views.get_title_details", side_effect=TMDBError("Indisponível"))
    def test_temporary_title_error_returns_503_and_noindex(self, _mock_details):
        response = self.client.get(
            reverse("movies:title_detail", args=("tv", 999))
        )

        self.assertEqual(response.status_code, 503)
        self.assertContains(
            response,
            '<meta name="robots" content="noindex, nofollow">',
            status_code=503,
        )
