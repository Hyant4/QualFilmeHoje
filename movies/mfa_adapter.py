from allauth.mfa.adapter import DefaultMFAAdapter
from allauth.mfa.models import Authenticator


class QualFilmeHojeMFAAdapter(DefaultMFAAdapter):
    """Mantem TOTP obrigatorio enquanto a conta possuir acesso ao admin."""

    def can_delete_authenticator(self, authenticator):
        if (
            authenticator.user.is_staff
            and authenticator.type == Authenticator.Type.TOTP
        ):
            return False
        return super().can_delete_authenticator(authenticator)
