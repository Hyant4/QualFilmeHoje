import re
import uuid
from unittest.mock import patch
from urllib.parse import urlparse

from allauth.account.models import EmailAddress
from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
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

    def create_user(self, email="pessoa@example.com"):
        user = get_user_model().objects.create_user(
            username=email,
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
        self.assertContains(signup_response, "Confirme a senha")
        self.assertContains(signup_response, "link para confirmar seu e-mail")

    def test_email_signup_requires_confirmation_before_authentication(self):
        response = self.client.post(
            reverse("account_signup"),
            {
                "email": "nova@example.com",
                "password1": self.password,
                "password2": self.password,
            },
        )

        self.assertRedirects(response, reverse("account_email_verification_sent"))
        user = get_user_model().objects.get(email="nova@example.com")
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

        user = self.create_user("cinema@example.com")
        self.client.force_login(user)
        authenticated_response = self.client.get(reverse("movies:home"))
        self.assertContains(authenticated_response, "cinema@example.com")
        self.assertContains(authenticated_response, ">Sair</button>")

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
