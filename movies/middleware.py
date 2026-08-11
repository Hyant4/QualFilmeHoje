from allauth.mfa.adapter import get_adapter
from allauth.mfa.models import Authenticator
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse


class AdminMFAMiddleware:
    """Impede que uma conta administrativa acesse o admin sem TOTP."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        admin_prefix = reverse("admin:index")
        user = request.user
        if (
            request.path.startswith(admin_prefix)
            and user.is_authenticated
            and user.is_staff
            and not get_adapter().is_mfa_enabled(
                user,
                types=[Authenticator.Type.TOTP],
            )
        ):
            messages.error(
                request,
                "Ative a autenticacao em duas etapas antes de acessar o admin.",
            )
            return redirect("mfa_activate_totp")
        return self.get_response(request)
