import json

from django.conf import settings
from django.templatetags.static import static


def authentication(_request):
    """Disponibiliza apenas o estado público da integração nos templates."""

    return {
        "google_auth_configured": settings.GOOGLE_AUTH_CONFIGURED,
        "email_features_enabled": settings.EMAIL_FEATURES_ENABLED,
    }


def _homepage_json_ld():
    homepage_url = f"{settings.SITE_URL}/"
    return json.dumps(
        {
            "@context": "https://schema.org",
            "@graph": [
                {
                    "@type": "WebSite",
                    "@id": f"{homepage_url}#website",
                    "url": homepage_url,
                    "name": "QualFilmeHoje",
                    "description": (
                        "Gerador gratuito de filmes e séries com filtros por "
                        "gênero, nota e ano, trailers e opções para assistir no Brasil."
                    ),
                    "inLanguage": "pt-BR",
                },
                {
                    "@type": "WebApplication",
                    "@id": f"{homepage_url}#app",
                    "name": "QualFilmeHoje",
                    "url": homepage_url,
                    "image": f"{settings.SITE_URL}{static('movies/images/og-qualfilmehoje.png')}",
                    "description": (
                        "Escolha gênero, faixa de notas e ano de lançamento para "
                        "receber uma sugestão de filme ou série e descobrir onde assistir."
                    ),
                    "applicationCategory": "EntertainmentApplication",
                    "operatingSystem": "Qualquer sistema com navegador moderno",
                    "browserRequirements": "Requer JavaScript e conexão com a internet",
                    "isAccessibleForFree": True,
                    "inLanguage": "pt-BR",
                    "offers": {
                        "@type": "Offer",
                        "price": "0",
                        "priceCurrency": "BRL",
                    },
                },
            ],
        },
        ensure_ascii=False,
        separators=(",", ":"),
    )


def seo_metadata(request):
    match = getattr(request, "resolver_match", None)
    namespace = getattr(match, "namespace", "")
    url_name = getattr(match, "url_name", "")
    is_indexable = (
        request.method == "GET"
        and namespace == "movies"
        and url_name in {"home", "title_detail"}
    )

    return {
        "site_url": settings.SITE_URL,
        "canonical_url": f"{settings.SITE_URL}{request.path}",
        "seo_robots": "index, follow" if is_indexable else "noindex, follow",
        "google_site_verification": settings.GOOGLE_SITE_VERIFICATION,
        "seo_json_ld": (
            _homepage_json_ld()
            if is_indexable and url_name == "home"
            else ""
        ),
    }
