"""
Django settings for Guestman tests.

Includes all apps needed to run the full Guestman test suite.
"""

SECRET_KEY = "test-secret-key-for-guestman-tests"

DEBUG = True

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "guestman",
    "guestman.contrib.identifiers",
    "guestman.contrib.consent",
    "guestman.contrib.preferences",
    "guestman.contrib.insights",
    "guestman.contrib.loyalty",
    "guestman.contrib.timeline",
    "guestman.contrib.manychat",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

USE_TZ = True
TIME_ZONE = "America/Sao_Paulo"

# Manychat webhook secret for tests
MANYCHAT_WEBHOOK_SECRET = ""
