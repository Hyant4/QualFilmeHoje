from django.urls import path

from . import views

app_name = "movies"

urlpatterns = [
    path("", views.home, name="home"),
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
