from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("movies", "0005_remove_whatsapp_integration")]

    operations = [
        migrations.CreateModel(
            name="RateLimitBucket",
            fields=[
                (
                    "bucket_key",
                    models.CharField(max_length=80, primary_key=True, serialize=False),
                ),
                ("request_count", models.PositiveIntegerField(default=0)),
                ("reset_at", models.DateTimeField(db_index=True)),
            ],
            options={
                "verbose_name": "contador de limite",
                "verbose_name_plural": "contadores de limite",
                "db_table": "qualfilmehoje_rate_limit",
            },
        ),
    ]
