from allauth.account.models import EmailAddress
from django.test import TestCase

from movies.models import Title
from movies.tests.factories import create_title, create_user, tmdb_title_payload


class TestFactoriesTests(TestCase):
    def test_user_factory_creates_a_verified_account_with_overrides(self):
        user = create_user(
            "factory@example.com",
            username="factory-user",
            first_name="Pessoa",
        )

        self.assertEqual(user.username, "factory-user")
        self.assertEqual(user.first_name, "Pessoa")
        self.assertTrue(
            EmailAddress.objects.filter(
                user=user,
                email="factory@example.com",
                verified=True,
                primary=True,
            ).exists()
        )

    def test_title_factories_keep_defaults_isolated_and_accept_overrides(self):
        title = create_title(media_type=Title.TV, name="Série da factory")
        first_payload = tmdb_title_payload(title="Payload customizado")
        second_payload = tmdb_title_payload()
        first_payload["reviews"].append({"content": "Ótimo"})

        self.assertEqual(title.media_type, Title.TV)
        self.assertEqual(title.name, "Série da factory")
        self.assertEqual(first_payload["title"], "Payload customizado")
        self.assertEqual(second_payload["reviews"], [])
