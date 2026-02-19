# Generated migration for ContactPoint and ExternalIdentity

import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("guestman", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ContactPoint",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "type",
                    models.CharField(
                        choices=[
                            ("whatsapp", "WhatsApp"),
                            ("phone", "Phone (voice/SMS)"),
                            ("email", "Email"),
                            ("instagram", "Instagram"),
                        ],
                        max_length=20,
                    ),
                ),
                (
                    "value_normalized",
                    models.CharField(
                        db_index=True,
                        help_text="Phone in E.164 (+5541999998888) or lowercase email.",
                        max_length=255,
                    ),
                ),
                (
                    "value_display",
                    models.CharField(
                        blank=True,
                        help_text="Friendly format for display.",
                        max_length=255,
                    ),
                ),
                ("is_primary", models.BooleanField(default=False)),
                ("is_verified", models.BooleanField(default=False)),
                (
                    "verification_method",
                    models.CharField(
                        choices=[
                            ("unverified", "Not verified"),
                            ("channel_asserted", "Channel Asserted"),
                            ("otp_whatsapp", "OTP via WhatsApp"),
                            ("otp_sms", "OTP via SMS"),
                            ("email_link", "Email Link"),
                            ("manual", "Manual (staff)"),
                        ],
                        default="unverified",
                        max_length=20,
                    ),
                ),
                ("verified_at", models.DateTimeField(blank=True, null=True)),
                (
                    "verification_ref",
                    models.CharField(
                        blank=True,
                        help_text="External reference (e.g., Manychat subscriber_id).",
                        max_length=255,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "customer",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="contact_points",
                        to="guestman.customer",
                    ),
                ),
            ],
            options={
                "verbose_name": "contact point",
                "verbose_name_plural": "contact points",
                "db_table": "guestman_contact_point",
                "ordering": ["-is_primary", "-created_at"],
            },
        ),
        migrations.CreateModel(
            name="ExternalIdentity",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "provider",
                    models.CharField(
                        choices=[
                            ("manychat", "ManyChat"),
                            ("whatsapp", "WhatsApp Business"),
                            ("instagram", "Instagram"),
                            ("facebook", "Facebook"),
                            ("google", "Google"),
                            ("apple", "Apple"),
                            ("telegram", "Telegram"),
                            ("other", "Other"),
                        ],
                        max_length=20,
                    ),
                ),
                (
                    "provider_uid",
                    models.CharField(
                        help_text="Unique ID in the provider (e.g., Manychat subscriber_id)",
                        max_length=255,
                    ),
                ),
                (
                    "provider_meta",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        help_text="Extra data: page_id, wa_id, ig_scoped_id, tags, etc.",
                    ),
                ),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "customer",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="external_identities",
                        to="guestman.customer",
                    ),
                ),
            ],
            options={
                "verbose_name": "external identity",
                "verbose_name_plural": "external identities",
                "db_table": "guestman_external_identity",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddConstraint(
            model_name="contactpoint",
            constraint=models.UniqueConstraint(
                fields=("type", "value_normalized"),
                name="guestman_unique_contact_value",
            ),
        ),
        migrations.AddConstraint(
            model_name="contactpoint",
            constraint=models.UniqueConstraint(
                condition=models.Q(is_primary=True),
                fields=("customer", "type"),
                name="guestman_unique_primary_per_type",
            ),
        ),
        migrations.AddIndex(
            model_name="contactpoint",
            index=models.Index(
                fields=["customer", "type", "is_primary"],
                name="guestman_co_custome_a1b2c3_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="contactpoint",
            index=models.Index(
                fields=["type", "value_normalized"],
                name="guestman_co_type_va_d4e5f6_idx",
            ),
        ),
        migrations.AddConstraint(
            model_name="externalidentity",
            constraint=models.UniqueConstraint(
                fields=("provider", "provider_uid"),
                name="guestman_unique_external_identity",
            ),
        ),
        migrations.AddIndex(
            model_name="externalidentity",
            index=models.Index(
                fields=["customer", "provider"],
                name="guestman_ex_custome_g7h8i9_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="externalidentity",
            index=models.Index(
                fields=["provider", "provider_uid"],
                name="guestman_ex_provide_j0k1l2_idx",
            ),
        ),
    ]
