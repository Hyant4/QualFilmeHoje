import re
import uuid
from unittest.mock import patch
from urllib.parse import urlparse

from allauth.account.adapter import get_adapter
from allauth.account.models import EmailAddress
from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from movies.models import Favorite, Generation, Title, WhatsAppContact

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

    def test_whatsapp_number_is_optional_and_normalized_for_the_account(self):
        user = self.create_user()
        self.client.force_login(user)

        settings_response = self.client.get(reverse("movies:whatsapp_settings"))
        self.assertEqual(settings_response.status_code, 200)
        self.assertContains(settings_response, "Seu número do WhatsApp")

        response = self.client.post(
            reverse("movies:whatsapp_settings"),
            {"phone_number": "(85) 99999-0000"},
        )

        self.assertRedirects(response, reverse("movies:whatsapp_settings"))
        contact = WhatsAppContact.objects.get(user=user)
        self.assertEqual(contact.phone_number, "+5585999990000")
        self.assertFalse(contact.is_verified)

    def test_whatsapp_number_cannot_be_shared_by_two_accounts(self):
        first_user = self.create_user("primeira@example.com")
        second_user = self.create_user("segunda@example.com")
        WhatsAppContact.objects.create(
            user=first_user, phone_number="+5585999990000"
        )
        self.client.force_login(second_user)

        response = self.client.post(
            reverse("movies:whatsapp_settings"),
            {"phone_number": "+55 85 99999-0000"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Este número já está vinculado a outra conta.")
        self.assertFalse(WhatsAppContact.objects.filter(user=second_user).exists())

    def test_whatsapp_number_can_be_removed(self):
        user = self.create_user()
        WhatsAppContact.objects.create(user=user, phone_number="+5585999990000")
        self.client.force_login(user)

        response = self.client.post(
            reverse("movies:whatsapp_settings"),
            {"phone_number": ""},
        )

        self.assertRedirects(response, reverse("movies:whatsapp_settings"))
        self.assertFalse(WhatsAppContact.objects.filter(user=user).exists())
