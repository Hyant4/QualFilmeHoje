from django.conf import settings
from django.db import models


class Title(models.Model):
    MOVIE = "movie"
    TV = "tv"
    MEDIA_TYPE_CHOICES = (
        (MOVIE, "Filme"),
        (TV, "Série"),
    )

    tmdb_id = models.PositiveBigIntegerField("ID do TMDB")
    media_type = models.CharField("tipo", max_length=5, choices=MEDIA_TYPE_CHOICES)
    name = models.CharField("título", max_length=255)
    original_name = models.CharField("título original", max_length=255, blank=True)
    poster_url = models.URLField("URL do pôster", max_length=500, blank=True)
    release_date = models.DateField("data de lançamento", null=True, blank=True)
    vote_average = models.DecimalField(
        "nota no TMDB", max_digits=3, decimal_places=1, null=True, blank=True
    )
    updated_at = models.DateTimeField("atualizado em", auto_now=True)

    class Meta:
        verbose_name = "título"
        verbose_name_plural = "títulos"
        ordering = ("name",)
        constraints = (
            models.UniqueConstraint(
                fields=("media_type", "tmdb_id"),
                name="unique_tmdb_title_by_media_type",
            ),
        )

    def __str__(self):
        return self.name

    @property
    def release_year(self):
        return self.release_date.year if self.release_date else None


class Generation(models.Model):
    visitor_id = models.UUIDField("visitante", db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="title_generations",
        verbose_name="usuário",
        null=True,
        blank=True,
    )
    title = models.ForeignKey(
        Title,
        on_delete=models.CASCADE,
        related_name="generations",
        verbose_name="título",
    )
    genre_id = models.PositiveIntegerField("ID do gênero", null=True, blank=True)
    genre_name = models.CharField("gênero", max_length=100, blank=True)
    min_rating = models.DecimalField("nota mínima", max_digits=3, decimal_places=1)
    created_at = models.DateTimeField("sorteado em", auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "sorteio"
        verbose_name_plural = "sorteios"
        ordering = ("-created_at",)
        indexes = (
            models.Index(
                fields=("visitor_id", "-created_at"),
                name="generation_visitor_date_idx",
            ),
            models.Index(
                fields=("user", "-created_at"),
                name="generation_user_date_idx",
            ),
        )

    def __str__(self):
        return f"{self.title} — {self.created_at:%d/%m/%Y %H:%M}"


class Favorite(models.Model):
    visitor_id = models.UUIDField("visitante", db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="title_favorites",
        verbose_name="usuário",
        null=True,
        blank=True,
    )
    title = models.ForeignKey(
        Title,
        on_delete=models.CASCADE,
        related_name="favorites",
        verbose_name="título",
    )
    created_at = models.DateTimeField("favoritado em", auto_now_add=True)

    class Meta:
        verbose_name = "favorito"
        verbose_name_plural = "favoritos"
        ordering = ("-created_at",)
        constraints = (
            models.UniqueConstraint(
                fields=("visitor_id", "title"),
                name="unique_favorite_per_visitor",
            ),
            models.UniqueConstraint(
                fields=("user", "title"),
                condition=models.Q(user__isnull=False),
                name="unique_favorite_per_user",
            ),
        )
        indexes = (
            models.Index(
                fields=("visitor_id", "-created_at"),
                name="favorite_visitor_date_idx",
            ),
            models.Index(
                fields=("user", "-created_at"),
                name="favorite_user_date_idx",
            ),
        )

    def __str__(self):
        return str(self.title)


class SharedCacheEntry(models.Model):
    """Tabela gerenciada usada pelo DatabaseCache nas funcoes da Vercel."""

    cache_key = models.CharField(max_length=255, primary_key=True)
    value = models.TextField()
    expires = models.DateTimeField(db_index=True)

    class Meta:
        db_table = "qualfilmehoje_cache"
        verbose_name = "entrada de cache"
        verbose_name_plural = "entradas de cache"

    def __str__(self):
        return self.cache_key
