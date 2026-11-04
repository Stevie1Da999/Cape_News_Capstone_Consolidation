"""Django settings for the News Application project."""

import os
from pathlib import Path


# BASE_DIR points to the main project folder.
BASE_DIR = Path(__file__).resolve().parent.parent

# Running locally is simple, but a deployed site must have its own secret.
DEBUG = os.getenv("DJANGO_DEBUG", "True").lower() == "true"
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "")
if not SECRET_KEY:
    if DEBUG:
        # This fallback is only for local practice. Never use it online.
        SECRET_KEY = "django-insecure-local-cape-news-only"
    else:
        raise RuntimeError("Set DJANGO_SECRET_KEY when DJANGO_DEBUG=False.")

# Docker uses these hosts, and an owner can add more using an environment var.
ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv(
        "DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost"
    ).split(",")
    if host.strip()
]


INSTALLED_APPS = [
    # Default Django apps.
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # REST Framework and its token authentication app.
    "rest_framework",
    "rest_framework.authtoken",

    # Our own news application.
    "news.apps.NewsConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# Django's development server handles CSS while DEBUG is on.
# WhiteNoise is needed when the Docker web server uses DEBUG=False.
if not DEBUG:
    MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")

ROOT_URLCONF = "news_project.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "news_project.wsgi.application"


# SQLite is kept as the easy development/test option. The final project can be
# switched to MariaDB by setting DB_ENGINE=mariadb and the DB_* variables.
if os.getenv("DB_ENGINE", "sqlite").lower() == "mariadb":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": os.getenv("DB_NAME", "news_application"),
            "USER": os.getenv("DB_USER", "news_user"),
            "PASSWORD": os.getenv("DB_PASSWORD", ""),
            "HOST": os.getenv("DB_HOST", "127.0.0.1"),
            "PORT": os.getenv("DB_PORT", "3306"),
            "OPTIONS": {"charset": "utf8mb4"},
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": os.getenv("SQLITE_PATH", str(BASE_DIR / "db.sqlite3")),
        }
    }


AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "UserAttributeSimilarityValidator"
        )
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"
    },
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Africa/Johannesburg"
USE_I18N = True
USE_TZ = True

# Static files include the small stylesheet used by the website.
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
# WhiteNoise serves the CSS files when DEBUG is off in Docker.
if not DEBUG:
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage"
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"
        },
    }

# Our User model stores the Reader, Editor and Journalist roles.
AUTH_USER_MODEL = "news.User"

# Token authentication is required for API use. Session authentication is also
# handy when manually testing through DRF's browser pages.
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}

# During development the email is printed in the terminal instead of being
# sent through a real mail provider. This lets the approval feature be tested.
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
DEFAULT_FROM_EMAIL = "Cape News <news@example.com>"

# Normal website authentication redirects.
LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
