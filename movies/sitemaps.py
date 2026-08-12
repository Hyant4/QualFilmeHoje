from types import SimpleNamespace
from urllib.parse import urlsplit

from django.conf import settings
from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import Title


class CanonicalSitemap(Sitemap):
    def get_urls(self, page=1, site=None, protocol=None):
        site_url = urlsplit(settings.SITE_URL)
        canonical_site = SimpleNamespace(
            domain=site_url.netloc,
            name="QualFilmeHoje",
        )
        return super().get_urls(
            page=page,
            site=canonical_site,
            protocol=site_url.scheme,
        )


class StaticSitemap(CanonicalSitemap):

    def items(self):
        return ("movies:home", "movies:random_movies")

    def location(self, item):
        return reverse(item)


class TitleSitemap(CanonicalSitemap):

    def items(self):
        return Title.objects.only(
            "tmdb_id",
            "media_type",
            "updated_at",
        ).order_by("-updated_at")

    def location(self, item):
        return reverse(
            "movies:title_detail",
            args=(item.media_type, item.tmdb_id),
        )

    def lastmod(self, item):
        return item.updated_at
