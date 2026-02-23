"""Identifiers app config."""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class IdentifiersConfig(AppConfig):
    name = "guestman.contrib.identifiers"
    label = "guestman_identifiers"
    verbose_name = _("Identificadores")
