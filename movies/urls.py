from django.urls import path

from . import views

app_name = "movies"

urlpatterns = [
    path("", views.home, name="home"),
    path("gerar/", views.generate_movie, name="generate_movie"),
    path(
        "titulo/<str:media_type>/<int:tmdb_id>/",
        views.title_detail,
        name="title_detail",
    ),
    path("favoritos/alternar/", views.toggle_title_favorite, name="toggle_favorite"),
    path("conta/whatsapp/", views.whatsapp_settings, name="whatsapp_settings"),
    path("webhook/whatsapp/", views.whatsapp_webhook, name="whatsapp_webhook"),
]
