"""CustomerIdentifier model for multi-channel deduplication."""

import re

from django.db import models
from django.utils.translation import gettext_lazy as _


class IdentifierType(models.TextChoices):
    """Supported identifier types."""

    PHONE = "phone", _("Telefone")
    EMAIL = "email", "Email"
    INSTAGRAM = "instagram", "Instagram"
    FACEBOOK = "facebook", "Facebook"
    WHATSAPP = "whatsapp", "WhatsApp"
    TELEGRAM = "telegram", "Telegram"
    MANYCHAT = "manychat", "Manychat ID"


class CustomerIdentifier(models.Model):
    """
    Unique customer identifier.

    Allows:
    - Finding customer by any channel
    - Detecting duplicates across channels
    - Maintaining identifier history
    """

    customer = models.ForeignKey(
        "guestman.Customer",
        on_delete=models.CASCADE,
        related_name="identifiers",
        verbose_name=_("cliente"),
    )
    identifier_type = models.CharField(
        _("tipo"),
        max_length=20,
        choices=IdentifierType.choices,
    )
    identifier_value = models.CharField(
        _("valor"),
        max_length=255,
        help_text=_("Valor normalizado (telefone sem formatação, email minúsculo)"),
    )
    is_primary = models.BooleanField(
        _("principal"),
        default=False,
        help_text=_("Identificador principal deste tipo"),
    )
    verified_at = models.DateTimeField(
        _("verificado em"),
        null=True,
        blank=True,
        help_text=_("Quando foi verificado (ex: OTP)"),
    )

    # Audit
    created_at = models.DateTimeField(_("criado em"), auto_now_add=True)
    source_system = models.CharField(_("sistema de origem"), max_length=100, blank=True)

    class Meta:
        verbose_name = _("identificador")
        verbose_name_plural = _("identificadores")
        unique_together = ["identifier_type", "identifier_value"]
        indexes = [
            models.Index(fields=["identifier_type", "identifier_value"]),
        ]

    def __str__(self):
        return f"{self.get_identifier_type_display()}: {self.identifier_value}"

    def save(self, *args, **kwargs):
        # Normalize value
        if self.identifier_type == IdentifierType.PHONE:
            self.identifier_value = self._normalize_phone(self.identifier_value)
        elif self.identifier_type == IdentifierType.EMAIL:
            self.identifier_value = self.identifier_value.lower().strip()

        # Ensure only one primary per type/customer
        if self.is_primary:
            CustomerIdentifier.objects.filter(
                customer=self.customer,
                identifier_type=self.identifier_type,
                is_primary=True,
            ).exclude(pk=self.pk).update(is_primary=False)

        super().save(*args, **kwargs)

    @staticmethod
    def _normalize_phone(phone: str) -> str:
        """Remove formatting, keep only digits."""
        digits = re.sub(r"\D", "", phone)
        # Add country code if not present (Brazil)
        if len(digits) == 11:  # DDD + number
            digits = f"55{digits}"
        return digits
