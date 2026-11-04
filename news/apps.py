# AppConfig is Django's configuration class for an application.
from django.apps import AppConfig


class NewsConfig(AppConfig):
    """Configuration for our news application."""

    # Django uses BigAutoField for automatically generated IDs.
    default_auto_field = "django.db.models.BigAutoField"

    # This tells Django the name of our application.
    name = "news"

    def ready(self):
        # Importing signals here makes sure Django loads them
        # when the news application starts.
        import news.signals  # noqa: F401
