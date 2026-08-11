from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("movies", "0003_whatsappcontact")]

    operations = [
        migrations.CreateModel(
            name="SharedCacheEntry",
            fields=[
                (
                    "cache_key",
                    models.CharField(
                        max_length=255,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("value", models.TextField()),
                ("expires", models.DateTimeField(db_index=True)),
            ],
            options={
                "verbose_name": "entrada de cache",
                "verbose_name_plural": "entradas de cache",
                "db_table": "qualfilmehoje_cache",
            },
        )
    ]
