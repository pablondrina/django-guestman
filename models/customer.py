"""Customer model (CORE - agnóstico)."""

import uuid as uuid_lib

from django.db import models
from django.utils.translation import gettext_lazy as _


class CustomerType(models.TextChoices):
    INDIVIDUAL = "individual", _("Pessoa Física")
    BUSINESS = "business", _("Pessoa Jurídica")


class Customer(models.Model):
    """
    Registered customer.

    CORE: Essential and channel-agnostic data only.
    Channel-specific data (Manychat, etc.) goes in contrib/identifiers and contrib/manychat.
    """

    # Identification (code + uuid pattern - see spec 000 section 12.2)
    code = models.CharField(
        _("código"),
        max_length=50,
        unique=True,
        help_text=_("Código único do cliente (ex: CLI-001)"),
    )
    uuid = models.UUIDField(default=uuid_lib.uuid4, editable=False, unique=True)

    # Basic data (first_name + last_name - see spec 000 section 12.5)
    first_name = models.CharField(_("nome"), max_length=100)
    last_name = models.CharField(_("sobrenome"), max_length=100, blank=True)
    customer_type = models.CharField(
        _("tipo"),
        max_length=20,
        choices=CustomerType.choices,
        default=CustomerType.INDIVIDUAL,
    )

    # Document (optional)
    document = models.CharField(
        _("documento"),
        max_length=20,
        blank=True,
        db_index=True,
        help_text=_("CPF ou CNPJ (apenas números)"),
    )

    # Primary contact (core - email and phone are universal)
    # DEPRECATED: Use ContactPoint for multi-channel contacts
    email = models.EmailField(_("email (legado)"), blank=True, db_index=True)
    phone = models.CharField(_("telefone (legado)"), max_length=20, blank=True, db_index=True)

    # Segmentation
    group = models.ForeignKey(
        "guestman.CustomerGroup",
        on_delete=models.PROTECT,
        related_name="customers",
        null=True,
        blank=True,
        verbose_name=_("grupo"),
    )

    # Status (is_active is appropriate - see spec 000 section 12.3)
    is_active = models.BooleanField(_("ativo"), default=True, db_index=True)

    # Internal notes (not visible to customer)
    notes = models.TextField(_("observações"), blank=True)

    # Extension point (see spec 000 section 12.4)
    metadata = models.JSONField(_("metadados"), default=dict, blank=True)

    # Audit (B.I.)
    created_at = models.DateTimeField(_("criado em"), auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(_("atualizado em"), auto_now=True)
    created_by = models.CharField(_("criado por"), max_length=255, blank=True)
    source_system = models.CharField(_("sistema de origem"), max_length=100, blank=True)

    class Meta:
        verbose_name = _("cliente")
        verbose_name_plural = _("clientes")
        ordering = ["first_name", "last_name"]
        indexes = [
            models.Index(fields=["code"]),
            models.Index(fields=["document"]),
            models.Index(fields=["phone"]),
            models.Index(fields=["email"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.code})"

    @property
    def name(self) -> str:
        """Full name (first + last)."""
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def price_list_code(self) -> str | None:
        """Applicable price list code."""
        if self.group and self.group.price_list_code:
            return self.group.price_list_code
        return None

    @property
    def default_address(self):
        """Customer's default address."""
        return self.addresses.filter(is_default=True).first()

    def save(self, *args, **kwargs):
        # Normalize phone to E.164 format (digits only, with country code)
        if self.phone:
            import re
            digits = re.sub(r"\D", "", self.phone)
            # Add Brazil country code if not present
            if len(digits) == 11:  # DDD + 9 digits
                digits = f"55{digits}"
            elif len(digits) == 10:  # DDD + 8 digits (landline)
                digits = f"55{digits}"
            self.phone = digits

        # Normalize email (lowercase)
        if self.email:
            self.email = self.email.lower().strip()

        # Set default group
        if not self.group_id:
            from guestman.models import CustomerGroup

            default_group = CustomerGroup.objects.filter(is_default=True).first()
            if default_group:
                self.group = default_group

        super().save(*args, **kwargs)
