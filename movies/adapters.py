from allauth.account.adapter import DefaultAccountAdapter
from allauth.account.utils import user_email, user_field, user_username


class QualFilmeHojeAccountAdapter(DefaultAccountAdapter):
    """Gera um username legível para cadastros sociais sem sobrescrever escolhas."""

    def populate_username(self, request, user):
        if user_username(user):
            return

        first_name = user_field(user, "first_name") or ""
        last_name = user_field(user, "last_name") or ""
        full_name = f"{first_name} {last_name}".strip()
        username = self.generate_unique_username(
            [full_name, user_email(user), "usuario"]
        )
        user_username(user, username)
