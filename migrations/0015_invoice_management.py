import decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("kehem", "0014_author_blogpost_category_tag_delete_kehem_blog_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="CompanyProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("company_name", models.CharField(default="KEHEM IT", max_length=160)),
                ("address", models.TextField(blank=True)),
                ("phone", models.CharField(blank=True, max_length=40)),
                ("email", models.EmailField(blank=True, max_length=254)),
                ("website", models.URLField(blank=True)),
                ("logo", models.ImageField(blank=True, null=True, upload_to="invoice/company/")),
                ("vat_number", models.CharField(blank=True, max_length=80)),
                ("tax_number", models.CharField(blank=True, max_length=80)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"verbose_name_plural": "Company profile"},
        ),
        migrations.CreateModel(
            name="InvoiceSequence",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("date", models.DateField(unique=True)),
                ("last_number", models.PositiveIntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name="InvoiceSetting",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("invoice_prefix", models.CharField(default="INV", max_length=12)),
                ("invoice_footer", models.TextField(blank=True, default="Thank you for choosing KEHEM IT.")),
                (
                    "default_tax",
                    models.DecimalField(
                        decimal_places=2,
                        default=decimal.Decimal("0.00"),
                        max_digits=5,
                        validators=[MinValueValidator(decimal.Decimal("0.00"))],
                    ),
                ),
                ("default_currency", models.CharField(default="BDT", max_length=8)),
                ("default_notes", models.TextField(blank=True)),
                ("signature", models.ImageField(blank=True, null=True, upload_to="invoice/signatures/")),
                ("bank_information", models.TextField(blank=True)),
                ("payment_instructions", models.TextField(blank=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"verbose_name_plural": "Invoice settings"},
        ),
        migrations.CreateModel(
            name="Invoice",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("invoice_number", models.CharField(db_index=True, max_length=40, unique=True)),
                ("version", models.PositiveIntegerField(default=1)),
                ("customer_name", models.CharField(db_index=True, max_length=160)),
                ("customer_company", models.CharField(blank=True, db_index=True, max_length=160)),
                ("customer_address", models.TextField(blank=True)),
                ("customer_phone", models.CharField(blank=True, db_index=True, max_length=40)),
                ("customer_email", models.EmailField(blank=True, max_length=254)),
                ("invoice_date", models.DateField(db_index=True)),
                ("due_date", models.DateField(blank=True, null=True)),
                ("currency", models.CharField(default="BDT", max_length=8)),
                ("notes", models.TextField(blank=True)),
                ("payment_terms", models.TextField(blank=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("draft", "Draft"),
                            ("pending", "Pending"),
                            ("paid", "Paid"),
                            ("cancelled", "Cancelled"),
                            ("overdue", "Overdue"),
                        ],
                        db_index=True,
                        default="draft",
                        max_length=16,
                    ),
                ),
                ("shipping", models.DecimalField(decimal_places=2, default=decimal.Decimal("0.00"), max_digits=14)),
                ("service_charge", models.DecimalField(decimal_places=2, default=decimal.Decimal("0.00"), max_digits=14)),
                ("extra_cost", models.DecimalField(decimal_places=2, default=decimal.Decimal("0.00"), max_digits=14)),
                ("additional_discount", models.DecimalField(decimal_places=2, default=decimal.Decimal("0.00"), max_digits=14)),
                ("subtotal", models.DecimalField(decimal_places=2, default=decimal.Decimal("0.00"), max_digits=14)),
                ("discount_total", models.DecimalField(decimal_places=2, default=decimal.Decimal("0.00"), max_digits=14)),
                ("tax_total", models.DecimalField(decimal_places=2, default=decimal.Decimal("0.00"), max_digits=14)),
                ("grand_total", models.DecimalField(decimal_places=2, default=decimal.Decimal("0.00"), max_digits=14)),
                ("paid_amount", models.DecimalField(decimal_places=2, default=decimal.Decimal("0.00"), max_digits=14)),
                ("balance", models.DecimalField(decimal_places=2, default=decimal.Decimal("0.00"), max_digits=14)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deleted_at", models.DateTimeField(blank=True, db_index=True, null=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="kehem_invoices",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at"],
                "permissions": (
                    ("manage_invoice_settings", "Can manage invoice settings"),
                    ("view_invoice_history", "Can view invoice history"),
                ),
            },
        ),
        migrations.CreateModel(
            name="InvoiceItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("position", models.PositiveIntegerField(default=0)),
                ("description", models.CharField(max_length=500)),
                (
                    "quantity",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=12,
                        validators=[MinValueValidator(decimal.Decimal("0.01"))],
                    ),
                ),
                (
                    "unit_price",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=14,
                        validators=[MinValueValidator(decimal.Decimal("0.00"))],
                    ),
                ),
                ("discount_percent", models.DecimalField(decimal_places=2, default=decimal.Decimal("0.00"), max_digits=5)),
                ("tax_percent", models.DecimalField(decimal_places=2, default=decimal.Decimal("0.00"), max_digits=5)),
                ("line_total", models.DecimalField(decimal_places=2, default=decimal.Decimal("0.00"), max_digits=14)),
                (
                    "invoice",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="items",
                        to="kehem.invoice",
                    ),
                ),
            ],
            options={"ordering": ["position", "id"]},
        ),
        migrations.CreateModel(
            name="InvoiceHistory",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("version", models.PositiveIntegerField()),
                ("snapshot", models.JSONField()),
                ("changed_at", models.DateTimeField(auto_now_add=True)),
                (
                    "changed_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="kehem_invoice_changes",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "invoice",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="history",
                        to="kehem.invoice",
                    ),
                ),
            ],
            options={"ordering": ["-version", "-changed_at"]},
        ),
        migrations.AddIndex(
            model_name="invoice",
            index=models.Index(fields=["status", "-created_at"], name="kehem_invoi_status_4fece9_idx"),
        ),
        migrations.AddIndex(
            model_name="invoice",
            index=models.Index(fields=["customer_name", "-created_at"], name="kehem_invoi_custome_4ae847_idx"),
        ),
        migrations.AddConstraint(
            model_name="invoicehistory",
            constraint=models.UniqueConstraint(
                fields=("invoice", "version"),
                name="unique_kehem_invoice_version",
            ),
        ),
    ]
