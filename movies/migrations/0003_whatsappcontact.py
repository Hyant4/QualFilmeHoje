# Generated manually for the optional WhatsApp account linkage.

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("movies", "0002_favorite_user_generation_user_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="WhatsAppContact",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "phone_number",
                    models.CharField(
                        help_text="Formato internacional, por exemplo +5585999990000.",
                        max_length=16,
                        unique=True,
                        verbose_name="número do WhatsApp",
                    ),
                ),
                (
                    "is_verified",
                    models.BooleanField(default=False, verbose_name="confirmado no WhatsApp"),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="criado em")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="atualizado em")),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=models.deletion.CASCADE,
                        related_name="whatsapp_contact",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="usuário",
                    ),
                ),
            ],
            options={
                "verbose_name": "contato do WhatsApp",
                "verbose_name_plural": "contatos do WhatsApp",
            },
        ),
    ]
