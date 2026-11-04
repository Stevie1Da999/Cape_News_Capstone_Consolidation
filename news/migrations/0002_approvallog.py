# Records approval notifications received by our own REST API.
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("news", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ApprovalLog",
            fields=[
                ("id", models.BigAutoField(
                    auto_created=True, primary_key=True, serialize=False,
                    verbose_name="ID"
                )),
                ("received_at", models.DateTimeField(auto_now_add=True)),
                ("article", models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="approval_log", to="news.article"
                )),
                ("approved_by", models.ForeignKey(
                    null=True, on_delete=django.db.models.deletion.SET_NULL,
                    related_name="approval_logs", to=settings.AUTH_USER_MODEL
                )),
            ],
        ),
    ]
