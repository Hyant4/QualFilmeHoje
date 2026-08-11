from django.urls import path
from django.contrib.sitemaps.views import sitemap

from . import views
from .sitemaps import StaticSitemap, TitleSitemap

app_name = "movies"

sitemaps = {
    "static": StaticSitemap,
    "titles": TitleSitemap,
}

urlpatterns = [
    path("", views.home, name="home"),
    path("robots.txt", views.robots_txt, name="robots_txt"),
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="sitemap"),
    path("privacidade/", views.privacy, name="privacy"),
    path("security/csp-report/", views.csp_report, name="csp_report"),
    path("gerar/", views.generate_movie, name="generate_movie"),
    path(
        "titulo/<str:media_type>/<int:tmdb_id>/",
        views.title_detail,
        name="title_detail",
    ),
    path("favoritos/alternar/", views.toggle_title_favorite, name="toggle_favorite"),
]
