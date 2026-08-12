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


def _random_movies_json_ld():
    page_url = f"{settings.SITE_URL}/filmes-aleatorios/"
    homepage_url = f"{settings.SITE_URL}/"
    return json.dumps(
        {
            "@context": "https://schema.org",
            "@type": "WebPage",
            "@id": f"{page_url}#webpage",
            "url": page_url,
            "name": "Sorteador de filmes aleatórios",
            "description": (
                "Entenda como usar o sorteador gratuito de filmes aleatórios "
                "e escolha o que assistir por gênero, nota e ano."
            ),
            "inLanguage": "pt-BR",
            "isPartOf": {
                "@id": f"{homepage_url}#website",
                "url": homepage_url,
                "name": "QualFilmeHoje",
            },
            "mainEntity": {
                "@id": f"{homepage_url}#app",
                "@type": "WebApplication",
                "name": "QualFilmeHoje",
                "url": homepage_url,
                "applicationCategory": "EntertainmentApplication",
                "isAccessibleForFree": True,
            },
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
        and url_name in {"home", "random_movies", "title_detail"}
    )

    page_metadata = {
        "home": {
            "title": "Qual filme assistir hoje? | QualFilmeHoje",
            "description": (
                "Descubra qual filme assistir hoje com um sorteador gratuito. "
                "Filtre por gênero, nota e ano, veja o trailer e onde assistir no Brasil."
            ),
        },
        "random_movies": {
            "title": "Sorteador de filmes aleatórios | QualFilmeHoje",
            "description": (
                "Use um sorteador gratuito de filmes aleatórios e encontre o que "
                "assistir por gênero, nota e ano, com trailer e opções de streaming."
            ),
        },
    }.get(url_name, {})

    json_ld = ""
    if is_indexable and url_name == "home":
        json_ld = _homepage_json_ld()
    elif is_indexable and url_name == "random_movies":
        json_ld = _random_movies_json_ld()

    return {
        "site_url": settings.SITE_URL,
        "canonical_url": f"{settings.SITE_URL}{request.path}",
        "seo_robots": "index, follow" if is_indexable else "noindex, follow",
        "google_site_verification": settings.GOOGLE_SITE_VERIFICATION,
        "bing_site_verification": settings.BING_SITE_VERIFICATION,
        "seo_title": page_metadata.get("title", "QualFilmeHoje"),
        "seo_description": page_metadata.get(
            "description",
            "Encontre filmes e séries para assistir com o QualFilmeHoje.",
        ),
        "seo_json_ld": json_ld,
    }
