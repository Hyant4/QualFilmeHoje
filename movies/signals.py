import uuid

from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver

from .services.library import merge_visitor_library


@receiver(user_logged_in, dispatch_uid="movies.merge_visitor_library_on_login")
def merge_library_on_login(sender, request, user, **kwargs):
    """Mantém favoritos e sorteios feitos antes de o visitante entrar."""

    if request is None:
        return

    visitor_value = request.session.get("visitor_id")
    try:
        visitor_id = uuid.UUID(str(visitor_value))
    except (TypeError, ValueError, AttributeError):
        return

    merge_visitor_library(visitor_id, user)
