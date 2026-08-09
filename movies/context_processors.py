from django.conf import settings


def authentication(_request):
    """Disponibiliza apenas o estado público da integração nos templates."""

    return {
        "google_auth_configured": settings.GOOGLE_AUTH_CONFIGURED,
        "email_features_enabled": settings.EMAIL_FEATURES_ENABLED,
    }
