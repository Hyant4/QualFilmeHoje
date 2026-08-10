from django.contrib import admin

from .models import Favorite, Generation, Title, WhatsAppContact


@admin.register(Title)
class TitleAdmin(admin.ModelAdmin):
    list_display = ("name", "media_type", "tmdb_id", "vote_average", "updated_at")
    list_filter = ("media_type",)
    search_fields = ("name", "original_name", "tmdb_id")


@admin.register(Generation)
class GenerationAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "genre_name", "min_rating", "created_at")
    list_filter = ("title__media_type", "created_at")
    search_fields = ("title__name", "visitor_id", "user__email")
    date_hierarchy = "created_at"


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "created_at")
    list_filter = ("title__media_type", "created_at")
    search_fields = ("title__name", "visitor_id", "user__email")


@admin.register(WhatsAppContact)
class WhatsAppContactAdmin(admin.ModelAdmin):
    list_display = ("user", "phone_number", "is_verified", "updated_at")
    list_filter = ("is_verified",)
    search_fields = ("phone_number", "user__email", "user__username")
