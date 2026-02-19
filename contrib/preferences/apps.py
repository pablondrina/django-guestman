"""Preferences app config."""

from django.apps import AppConfig


class PreferencesConfig(AppConfig):
    name = "guestman.contrib.preferences"
    label = "guestman_preferences"
    verbose_name = "Guestman Preferences"
