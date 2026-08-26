"""Contratos internos e públicos do filtro assistido por IA."""

from typing import Literal

from django.utils import timezone
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .filter_catalog import available_genre_keys

MediaType = Literal["movie", "tv"]
RuntimeFilter = Literal["up_to_90", "90_to_120", "over_120"]
Certification = Literal["L", "10", "12", "14", "16", "18"]


class FilterIntent(BaseModel):
    """Intenção estruturada produzida pelo modelo, antes do mapeamento seguro."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        allow_inf_nan=False,
    )

    media_type: MediaType | None = Field(default=None)
    genre_key: str | None = Field(default=None)
    min_release_year: int | None = Field(default=None, ge=1900)
    min_rating: float | None = Field(default=None, ge=0, le=10)
    max_rating: float | None = Field(default=None, ge=0, le=10)
    runtime_filter: RuntimeFilter | None = Field(default=None)
    certification: Certification | None = Field(default=None)

    @field_validator("min_release_year")
    @classmethod
    def release_year_cannot_be_in_the_future(cls, value):
        if value is not None and value > timezone.localdate().year:
            raise ValueError("O ano de lançamento não pode estar no futuro.")
        return value

    @field_validator("genre_key")
    @classmethod
    def genre_key_must_come_from_the_catalog(cls, value):
        if value is not None and value not in available_genre_keys():
            raise ValueError("A chave de gênero não pertence ao catálogo.")
        return value

    @model_validator(mode="after")
    def maximum_rating_cannot_be_lower_than_minimum(self):
        if (
            self.min_rating is not None
            and self.max_rating is not None
            and self.max_rating < self.min_rating
        ):
            raise ValueError("A nota máxima não pode ser menor que a mínima.")
        return self


class FilterSuggestion(BaseModel):
    """Valores exatos que a interface atual sabe aplicar ao formulário."""

    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    media_type: MediaType | None = None
    genre_value: str | None = None
    min_release_year: int | None = Field(default=None, ge=1900)
    min_rating: float | None = Field(default=None, ge=0, le=10)
    max_rating: float | None = Field(default=None, ge=0, le=10)
    runtime_filter: RuntimeFilter | None = None
    certification: Certification | None = None

    def public_payload(self):
        filters = self.model_dump(exclude_none=True, mode="json")
        return {
            "filters": filters,
            "applied_fields": list(filters),
        }
