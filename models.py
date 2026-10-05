from django.db import models
from django.db.models import Q
from django.utils.text import slugify
from django.utils import timezone
from django.urls import reverse
from django.conf import settings
from django.core.validators import MinValueValidator
from hashid_field import HashidField
from decimal import Decimal
import bleach
import markdown
import math
import re


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True, blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Categories"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True, blank=True)

    class Meta:
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Author(models.Model):
    name = models.CharField(max_length=150)

    title = models.CharField(
        max_length=150,
        blank=True
    )

    bio = models.TextField(blank=True)

    avatar = models.ImageField(
        upload_to="authors/",
        blank=True,
        null=True
    )

    linkedin = models.URLField(blank=True)
    twitter = models.URLField(blank=True)
    website = models.URLField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class BlogPostQuerySet(models.QuerySet):

    def published(self):
        return self.filter(
            status="published"
        ).filter(
            Q(published_at__lte=timezone.now()) | Q(published_at__isnull=True)
        )

    def featured(self):
        return self.published().filter(
            featured=True
        )


class BlogPost(models.Model):

    STATUS_CHOICES = (
        ("draft", "Draft"),
        ("scheduled", "Scheduled"),
        ("published", "Published"),
    )

    title = models.CharField(max_length=255)

    slug = models.SlugField(
        unique=True,
        max_length=255,
        blank=True
    )

    excerpt = models.TextField(
        max_length=500
    )

    content_markdown = models.TextField()

    content_html = models.TextField(
        editable=False,
        blank=True
    )

    cover_image = models.ImageField(
        upload_to="blog/covers/",
        blank=True,
        null=True
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name="posts"
    )

    author = models.ForeignKey(
        Author,
        on_delete=models.SET_NULL,
        null=True,
        related_name="posts"
    )

    tags = models.ManyToManyField(
        Tag,
        blank=True,
        related_name="posts"
    )

    # SEO

    meta_title = models.CharField(
        max_length=60,
        blank=True
    )

    meta_description = models.CharField(
        max_length=160,
        blank=True
    )

    canonical_url = models.URLField(
        blank=True
    )

    og_title = models.CharField(
        max_length=100,
        blank=True
    )

    og_description = models.CharField(
        max_length=200,
        blank=True
    )

    og_image = models.ImageField(
        upload_to="blog/og/",
        blank=True,
        null=True
    )

    no_index = models.BooleanField(
        default=False
    )

    # Publishing

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="draft"
    )

    featured = models.BooleanField(
        default=False
    )

    published_at = models.DateTimeField(
        blank=True,
        null=True
    )

    # Analytics

    read_time = models.PositiveIntegerField(
        default=1
    )

    views = models.PositiveIntegerField(
        default=0
    )

    # Timestamps

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    objects = BlogPostQuerySet.as_manager()

    class Meta:
        ordering = ["-published_at"]
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["status"]),
            models.Index(fields=["published_at"]),
            models.Index(fields=["featured"]),
        ]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        """Return the public URL used by the blog list API and sitemap."""
        slug = slugify(self.title) or self.slug or f"post-{self.pk}"
        return reverse(
            "blog_post_detail",
            kwargs={"slug": slug}
        )

    def calculate_read_time(self):
        words = len(
            re.findall(
                r"\w+",
                self.content_markdown
            )
        )

        return max(
            1,
            math.ceil(words / 225)
        )

    def render_html(self):
        html = markdown.markdown(
            self.content_markdown,
            extensions=[
                "fenced_code",
                "tables",
                "toc",
            ]
        )

        allowed_tags = bleach.sanitizer.ALLOWED_TAGS.union({
            "p",
            "pre",
            "code",
            "blockquote",
            "img",
            "table",
            "thead",
            "tbody",
            "tr",
            "td",
            "th",
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "h6",
        })

        return bleach.clean(
            html,
            tags=allowed_tags,
            strip=True
        )

    def save(self, *args, **kwargs):

        self.author, _ = Author.objects.get_or_create(
            name="KEHEM Team",
            defaults={
                "title": "KEHEM IT",
                "bio": "Design-led engineers building trusted websites, SaaS products, and business systems.",
            },
        )

        if not self.slug:
            self.slug = slugify(self.title)

        self.content_html = self.render_html()

        self.read_time = self.calculate_read_time()

        if not self.meta_title:
            self.meta_title = self.title[:60]

        if not self.meta_description:
            self.meta_description = self.excerpt[:160]

        if not self.og_title:
            self.og_title = self.meta_title

        if not self.og_description:
            self.og_description = self.meta_description

        if (
            self.status == "published"
            and not self.published_at
        ):
            self.published_at = timezone.now()

        super().save(*args, **kwargs)


class kehem_note(models.Model):
    title = models.CharField(max_length=100,default='Kehem Note')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    content = models.TextField(null=True, blank=True)
    def __str__(self):
        return str(self.title)
    

class Task(models.Model):
    task = models.CharField(max_length=500)
    date = models.DateField()
    completed = models.BooleanField(default=False)
    deleted = models.BooleanField(default=False)
    def __str__(self):
        return self.task
    
class ShortURL(models.Model):
    hashid = HashidField(null=True, blank=True, editable=False)
    original_url = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Ensure `id` is generated first before assigning `hashid`
        if not self.id:
            super().save(*args, **kwargs)  # Save to get an ID

        # Set `hashid` only if it's empty and `id` is available
        if not self.hashid and self.id:
            self.hashid = self.id  # HashidField will encode this automatically

        # Save once more to update hashid field
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.hashid)


class CompanyProfile(models.Model):
    company_name = models.CharField(max_length=160, default="KEHEM IT")
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=40, blank=True)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)
    logo = models.ImageField(upload_to="invoice/company/", blank=True, null=True)
    vat_number = models.CharField(max_length=80, blank=True)
    tax_number = models.CharField(max_length=80, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Company profile"

    def __str__(self):
        return self.company_name


class InvoiceSetting(models.Model):
    invoice_prefix = models.CharField(max_length=12, default="INV")
    invoice_footer = models.TextField(
        blank=True,
        default="Thank you for choosing KEHEM IT.",
    )
    default_tax = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    default_currency = models.CharField(max_length=8, default="BDT")
    default_notes = models.TextField(blank=True)
    signature = models.ImageField(
        upload_to="invoice/signatures/",
        blank=True,
        null=True,
    )
    bank_information = models.TextField(blank=True)
    payment_instructions = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Invoice settings"

    def __str__(self):
        return "Invoice settings"


class InvoiceSequence(models.Model):
    date = models.DateField(unique=True)
    last_number = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.date}: {self.last_number}"


class Invoice(models.Model):
    STATUS_DRAFT = "draft"
    STATUS_PENDING = "pending"
    STATUS_PAID = "paid"
    STATUS_CANCELLED = "cancelled"
    STATUS_OVERDUE = "overdue"
    STATUS_CHOICES = (
        (STATUS_DRAFT, "Draft"),
        (STATUS_PENDING, "Pending"),
        (STATUS_PAID, "Paid"),
        (STATUS_CANCELLED, "Cancelled"),
        (STATUS_OVERDUE, "Overdue"),
    )

    invoice_number = models.CharField(max_length=40, unique=True, db_index=True)
    version = models.PositiveIntegerField(default=1)
    customer_name = models.CharField(max_length=160, db_index=True)
    customer_company = models.CharField(max_length=160, blank=True, db_index=True)
    customer_address = models.TextField(blank=True)
    customer_phone = models.CharField(max_length=40, blank=True, db_index=True)
    customer_email = models.EmailField(blank=True)
    invoice_date = models.DateField(db_index=True)
    due_date = models.DateField(null=True, blank=True)
    currency = models.CharField(max_length=8, default="BDT")
    notes = models.TextField(blank=True)
    payment_terms = models.TextField(blank=True)
    status = models.CharField(
        max_length=16,
        choices=STATUS_CHOICES,
        default=STATUS_DRAFT,
        db_index=True,
    )
    shipping = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal("0.00")
    )
    service_charge = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal("0.00")
    )
    extra_cost = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal("0.00")
    )
    additional_discount = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal("0.00")
    )
    subtotal = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal("0.00")
    )
    discount_total = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal("0.00")
    )
    tax_total = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal("0.00")
    )
    grand_total = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal("0.00")
    )
    paid_amount = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal("0.00")
    )
    balance = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal("0.00")
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="kehem_invoices",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        permissions = (
            ("manage_invoice_settings", "Can manage invoice settings"),
            ("view_invoice_history", "Can view invoice history"),
        )
        indexes = [
            models.Index(fields=["status", "-created_at"]),
            models.Index(fields=["customer_name", "-created_at"]),
        ]

    @property
    def outstanding_amount(self):
        return max(self.balance, Decimal("0.00"))

    def __str__(self):
        return self.invoice_number


class InvoiceItem(models.Model):
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name="items",
    )
    position = models.PositiveIntegerField(default=0)
    description = models.CharField(max_length=500)
    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    unit_price = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    discount_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    tax_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    line_total = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    class Meta:
        ordering = ["position", "id"]

    def __str__(self):
        return self.description


class InvoiceHistory(models.Model):
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name="history",
    )
    version = models.PositiveIntegerField()
    snapshot = models.JSONField()
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="kehem_invoice_changes",
    )
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-version", "-changed_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["invoice", "version"],
                name="unique_kehem_invoice_version",
            )
        ]

    def __str__(self):
        return f"{self.invoice.invoice_number} v{self.version}"
