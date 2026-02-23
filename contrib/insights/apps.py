"""Insights app config."""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class InsightsConfig(AppConfig):
    name = "guestman.contrib.insights"
    label = "guestman_insights"
    verbose_name = _("Análise de Clientes")
