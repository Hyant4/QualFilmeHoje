from django.conf import settings
from django.contrib.sitemaps.views import sitemap
from django.urls import path

from . import views
from .sitemaps import StaticSitemap, TitleSitemap

app_name = "movies"

sitemaps = {
    "static": StaticSitemap,
    "titles": TitleSitemap,
}

urlpatterns = [
    path("", views.home, name="home"),
    path("filmes-aleatorios/", views.random_movies, name="random_movies"),
    path("robots.txt", views.robots_txt, name="robots_txt"),
    path(
        f"{settings.INDEXNOW_KEY}.txt",
        views.indexnow_key,
        name="indexnow_key",
    ),
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="sitemap"),
    path("privacidade/", views.privacy, name="privacy"),
    path("favoritos/", views.favorites, name="favorites"),
    path("security/csp-report/", views.csp_report, name="csp_report"),
    path("gerar/", views.generate_movie, name="generate_movie"),
    path(
        "api/interpretar-filtro/",
        views.interpret_filter,
        name="interpret_filter",
    ),
    path(
        "api/onde-assistir/<str:media_type>/<int:tmdb_id>/",
        views.streaming_links,
        name="streaming_links",
    ),
    path(
        "titulo/<str:media_type>/<int:tmdb_id>/",
        views.title_detail,
        name="title_detail",
    ),
    path("favoritos/alternar/", views.toggle_title_favorite, name="toggle_favorite"),
]
