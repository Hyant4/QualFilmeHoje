import re
import uuid
from unittest.mock import patch
from urllib.parse import urlparse

from allauth.account.adapter import get_adapter
from allauth.account.models import EmailAddress
from allauth.account.signals import password_changed
from allauth.mfa.adapter import get_adapter as get_mfa_adapter
from allauth.mfa.models import Authenticator
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.core import mail
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from movies.models import Favorite, Generation, Title

GOOGLE_PROVIDER_SETTINGS = {
    "google": {
        "APPS": [
            {
                "client_id": "test-client.apps.googleusercontent.com",
                "secret": "test-secret",
                "key": "",
            }
        ],
        "SCOPE": ["profile", "email"],
        "OAUTH_PKCE_ENABLED": True,
    }
}


class AuthenticationTests(TestCase):
    password = "CinemaPortfolio2026!"

    def create_user(self, email="pessoa@example.com", username=None):
        user = get_user_model().objects.create_user(
            username=username or email.split("@", maxsplit=1)[0],
            email=email,
            password=self.password,
        )
        EmailAddress.objects.update_or_create(
            user=user,
            email=email,
            defaults={"verified": True, "primary": True},
        )
        return user

    def test_login_and_signup_pages_offer_both_methods(self):
        with override_settings(
            GOOGLE_AUTH_CONFIGURED=True,
            SOCIALACCOUNT_PROVIDERS=GOOGLE_PROVIDER_SETTINGS,
        ):
            login_response = self.client.get(reverse("account_login"))
            signup_response = self.client.get(reverse("account_signup"))

        self.assertEqual(login_response.status_code, 200)
        self.assertContains(login_response, "Continuar com Google")
        self.assertContains(login_response, "E-mail")
        self.assertContains(login_response, "Senha")
        self.assertContains(login_response, "Esqueci minha senha")
        self.assertContains(login_response, 'rel="icon"')
        self.assertEqual(signup_response.status_code, 200)
        self.assertContains(signup_response, "Criar com Google")
        self.assertContains(signup_response, "Nome de usuário")
        self.assertContains(signup_response, "Confirme a senha")
        self.assertContains(signup_response, "link para confirmar seu e-mail")
        self.assertContains(signup_response, "Use pelo menos 12 caracteres")
        self.assertContains(signup_response, "Palavra!Filme27Lugar")
        self.assertContains(signup_response, "não copie este exemplo")

    def test_email_signup_requires_confirmation_before_authentication(self):
        response = self.client.post(
            reverse("account_signup"),
            {
                "username": "nova_pessoa",
                "email": "nova@example.com",
                "password1": self.password,
                "password2": self.password,
            },
        )

        self.assertRedirects(response, reverse("account_email_verification_sent"))
        user = get_user_model().objects.get(email="nova@example.com")
        self.assertEqual(user.username, "nova_pessoa")
        email_address = EmailAddress.objects.get(user=user, email=user.email)
        self.assertFalse(email_address.verified)
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].subject,
            "Confirme seu e-mail no QualFilmeHoje",
        )
        self.assertIn("/accounts/confirm-email/", mail.outbox[0].body)

        confirmation_url = re.search(
            r"https?://[^\s]+(/accounts/confirm-email/[^\s]+/)",
            mail.outbox[0].body,
        )
        self.assertIsNotNone(confirmation_url)
        confirmation_path = confirmation_url.group(1)
        confirmation_page = self.client.get(confirmation_path)
        self.assertContains(confirmation_page, "Confirmar e entrar")

        confirmed_response = self.client.post(confirmation_path)
        self.assertRedirects(confirmed_response, reverse("movies:home"))

        email_address.refresh_from_db()
        self.assertTrue(email_address.verified)
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)

    def test_signup_rejects_short_common_and_numeric_passwords(self):
        for index, password in enumerate(("Aa1!curta", "password1234", "123456789012")):
            response = self.client.post(
                reverse("account_signup"),
                {
                    "username": f"fraca_{index}",
                    "email": f"fraca_{index}@example.com",
                    "password1": password,
                    "password2": password,
                },
            )

            self.assertEqual(response.status_code, 200)
            self.assertFalse(
                get_user_model().objects.filter(email=f"fraca_{index}@example.com").exists()
            )

    def test_password_recovery_changes_password_by_email_link(self):
        user = self.create_user("recuperar@example.com")

        request_response = self.client.post(
            reverse("account_reset_password"),
            {"email": user.email},
        )

        self.assertRedirects(
            request_response,
            reverse("account_reset_password_done"),
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].subject,
            "Redefina sua senha do QualFilmeHoje",
        )
        reset_url = re.search(
            r"https?://[^\s]+(/accounts/password/reset/key/[^\s]+/)",
            mail.outbox[0].body,
        )
        self.assertIsNotNone(reset_url)

        reset_page = self.client.get(reset_url.group(1), follow=True)
        self.assertEqual(reset_page.status_code, 200)
        self.assertContains(reset_page, "Crie uma nova senha")
        reset_path = urlparse(reset_page.request["PATH_INFO"]).path
        new_password = "NovaSenhaCinema2026!"
        changed_response = self.client.post(
            reset_path,
            {"password1": new_password, "password2": new_password, "action": ""},
        )

        self.assertRedirects(
            changed_response,
            reverse("account_reset_password_from_key_done"),
        )
        user.refresh_from_db()
        self.assertTrue(user.check_password(new_password))
        self.assertFalse(user.check_password(self.password))

    def test_password_change_invalidates_other_sessions_only(self):
        user = self.create_user("sessoes@example.com")
        current_browser = Client()
        other_browser = Client()
        current_browser.force_login(user)
        other_browser.force_login(user)
        current_key = current_browser.session.session_key
        other_key = other_browser.session.session_key
        request = current_browser.get(reverse("movies:privacy")).wsgi_request

        password_changed.send(
            sender=user.__class__,
            request=request,
            user=user,
        )

        self.assertTrue(Session.objects.filter(session_key=current_key).exists())
        self.assertFalse(Session.objects.filter(session_key=other_key).exists())

    def test_session_lifetime_and_privacy_page(self):
        self.assertEqual(settings.SESSION_COOKIE_AGE, 12 * 60 * 60)
        self.assertTrue(settings.SESSION_EXPIRE_AT_BROWSER_CLOSE)
        self.assertTrue(settings.SESSION_COOKIE_HTTPONLY)
        self.assertEqual(settings.SESSION_COOKIE_SAMESITE, "Lax")
        self.assertTrue(settings.CSRF_COOKIE_HTTPONLY)
        self.assertFalse(settings.ACCOUNT_SESSION_REMEMBER)

        response = self.client.get(reverse("movies:privacy"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Cookies estritamente necessários")
        self.assertContains(response, "Login com Google")
        self.assertContains(response, "TMDB")
        self.assertContains(response, "Watchmode")
        self.assertContains(response, "Brevo")

    def test_google_profile_name_generates_unique_username(self):
        user = get_user_model()(
            email="hyan.google@example.com",
            first_name="Hyan",
            last_name="Souza",
        )

        get_adapter().populate_username(None, user)

        self.assertEqual(user.username, "hyan_souza")

    def test_google_username_gets_suffix_when_name_is_already_used(self):
        self.create_user("outra@example.com", username="hyan_souza")
        user = get_user_model()(
            email="hyan.google@example.com",
            first_name="Hyan",
            last_name="Souza",
        )

        get_adapter().populate_username(None, user)

        self.assertTrue(user.username.startswith("hyan_souza"))
        self.assertNotEqual(user.username, "hyan_souza")

    def test_email_login_and_post_logout(self):
        user = self.create_user()

        login_response = self.client.post(
            reverse("account_login"),
            {"login": user.email, "password": self.password},
        )
        self.assertRedirects(login_response, reverse("movies:home"))
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)

        logout_response = self.client.post(reverse("account_logout"))
        self.assertRedirects(logout_response, reverse("movies:home"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_anonymous_library_is_attached_on_login(self):
        visitor_id = uuid.uuid4()
        session = self.client.session
        session["visitor_id"] = str(visitor_id)
        session.save()
        title = Title.objects.create(
            tmdb_id=101,
            media_type=Title.MOVIE,
            name="Filme preservado",
        )
        generation = Generation.objects.create(
            visitor_id=visitor_id,
            title=title,
            min_rating=7.0,
        )
        favorite = Favorite.objects.create(visitor_id=visitor_id, title=title)
        user = self.create_user()

        response = self.client.post(
            reverse("account_login"),
            {"login": user.email, "password": self.password},
        )

        self.assertRedirects(response, reverse("movies:home"))
        generation.refresh_from_db()
        favorite.refresh_from_db()
        self.assertEqual(generation.user, user)
        self.assertEqual(favorite.user, user)

    def test_login_merge_deduplicates_existing_account_favorite(self):
        visitor_id = uuid.uuid4()
        other_visitor_id = uuid.uuid4()
        session = self.client.session
        session["visitor_id"] = str(visitor_id)
        session.save()
        title = Title.objects.create(
            tmdb_id=202,
            media_type=Title.TV,
            name="Série sem duplicata",
        )
        user = self.create_user()
        Favorite.objects.create(visitor_id=other_visitor_id, user=user, title=title)
        Favorite.objects.create(visitor_id=visitor_id, title=title)

        self.client.post(
            reverse("account_login"),
            {"login": user.email, "password": self.password},
        )

        self.assertEqual(Favorite.objects.filter(user=user, title=title).count(), 1)
        self.assertFalse(
            Favorite.objects.filter(visitor_id=visitor_id, user__isnull=True).exists()
        )

    def test_home_header_reflects_authentication_state(self):
        anonymous_response = self.client.get(reverse("movies:home"))
        self.assertContains(anonymous_response, ">Entrar</a>")

        user = self.create_user("cinema@example.com", username="cinefilo")
        self.client.force_login(user)
        authenticated_response = self.client.get(reverse("movies:home"))
        self.assertContains(authenticated_response, "cinefilo")
        self.assertContains(authenticated_response, ">Sair</button>")

    def test_home_header_uses_google_full_name(self):
        user = self.create_user("google@example.com", username="hyan_souza")
        user.first_name = "Hyan"
        user.last_name = "Souza"
        user.save(update_fields=["first_name", "last_name"])
        self.client.force_login(user)

        response = self.client.get(reverse("movies:home"))

        self.assertContains(response, "Hyan Souza")

    @patch("movies.views.get_random_title")
    @patch("movies.views.get_genres", return_value=[])
    def test_authenticated_generation_is_saved_to_account(
        self,
        _mock_genres,
        mock_random_title,
    ):
        mock_random_title.return_value = {
            "id": 303,
            "title": "Filme da conta",
            "media_type": "movie",
            "vote_average": 8.0,
            "reviews": [],
            "provider_groups": [],
            "credit_sections": [],
        }
        user = self.create_user()
        self.client.force_login(user)

        response = self.client.post(
            reverse("movies:generate_movie"),
            {"media_type": "movie", "min_rating": "7.0"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Generation.objects.get().user, user)

    def test_account_can_favorite_title_generated_in_another_session(self):
        user = self.create_user()
        title = Title.objects.create(
            tmdb_id=404,
            media_type=Title.MOVIE,
            name="Filme de outro navegador",
        )
        Generation.objects.create(
            visitor_id=uuid.uuid4(),
            user=user,
            title=title,
            min_rating=6.0,
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse("movies:toggle_favorite"),
            {"media_type": "movie", "tmdb_id": "404"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["favorited"])
        self.assertTrue(Favorite.objects.filter(user=user, title=title).exists())

    def test_google_login_starts_with_post_and_never_exposes_secret(self):
        with override_settings(
            GOOGLE_AUTH_CONFIGURED=True,
            GOOGLE_CLIENT_SECRET="test-secret",
            SOCIALACCOUNT_PROVIDERS=GOOGLE_PROVIDER_SETTINGS,
        ):
            response = self.client.post(reverse("google_login"))
            login_page = self.client.get(reverse("account_login"))

        self.assertEqual(response.status_code, 302)
        self.assertIn("accounts.google.com", response["Location"])
        self.assertNotContains(login_page, "test-secret")

    def test_admin_login_uses_allauth_and_requires_totp(self):
        anonymous = self.client.get(
            reverse("admin:login"),
            {"next": reverse("admin:index")},
        )
        self.assertRedirects(
            anonymous,
            f"{reverse('account_login')}?next={reverse('admin:index')}",
            fetch_redirect_response=False,
        )

        staff = self.create_user("admin@example.com", username="admin_seguro")
        staff.is_staff = True
        staff.is_superuser = True
        staff.save(update_fields=["is_staff", "is_superuser"])
        self.client.force_login(staff)

        enrollment = self.client.get(reverse("admin:index"))
        self.assertRedirects(
            enrollment,
            reverse("mfa_activate_totp"),
            fetch_redirect_response=False,
        )

        authenticator = Authenticator.objects.create(
            user=staff,
            type=Authenticator.Type.TOTP,
            data={},
        )
        allowed = self.client.get(reverse("admin:index"))

        self.assertEqual(allowed.status_code, 200)
        self.assertFalse(get_mfa_adapter().can_delete_authenticator(authenticator))
