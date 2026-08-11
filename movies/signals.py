import uuid

from allauth.account.signals import password_changed, password_reset
from django.contrib.auth import SESSION_KEY
from django.contrib.auth.signals import user_logged_in
from django.contrib.sessions.models import Session
from django.dispatch import receiver
from django.utils import timezone

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


def _invalidate_user_sessions(user, *, keep_session_key=None):
    """Remove sessões autenticadas do usuário sem confiar em dados do cliente."""

    session_keys = []
    sessions = Session.objects.filter(expire_date__gte=timezone.now())
    for session in sessions.iterator(chunk_size=200):
        if session.session_key == keep_session_key:
            continue
        # O backend assinado do Django converte sessões corrompidas em {}.
        session_user_id = session.get_decoded().get(SESSION_KEY)
        if str(session_user_id or "") == str(user.pk):
            session_keys.append(session.session_key)

    if session_keys:
        Session.objects.filter(session_key__in=session_keys).delete()


@receiver(password_changed, dispatch_uid="movies.invalidate_other_sessions_on_change")
def invalidate_other_sessions_on_password_change(sender, request, user, **kwargs):
    current_session_key = (
        request.session.session_key
        if request is not None and hasattr(request, "session")
        else None
    )
    _invalidate_user_sessions(user, keep_session_key=current_session_key)


@receiver(password_reset, dispatch_uid="movies.invalidate_sessions_on_reset")
def invalidate_sessions_on_password_reset(sender, request, user, **kwargs):
    _invalidate_user_sessions(user)
