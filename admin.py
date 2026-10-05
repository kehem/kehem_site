from django.contrib import admin
from .models import *
# Register your models here.
admin.site.register(kehem_note)
admin.site.register(ShortURL)
admin.site.register(BlogPost)
admin.site.register(Category)
admin.site.register(Tag)
admin.site.register(Author)


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 0
    readonly_fields = ("line_total",)


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = (
        "invoice_number",
        "customer_name",
        "status",
        "grand_total",
        "currency",
        "version",
        "created_at",
    )
    list_filter = ("status", "currency", "invoice_date")
    search_fields = (
        "invoice_number",
        "customer_name",
        "customer_company",
        "customer_phone",
    )
    readonly_fields = (
        "invoice_number",
        "version",
        "subtotal",
        "discount_total",
        "tax_total",
        "grand_total",
        "balance",
        "created_at",
        "updated_at",
    )
    inlines = (InvoiceItemInline,)


@admin.register(CompanyProfile)
class CompanyProfileAdmin(admin.ModelAdmin):
    list_display = ("company_name", "email", "phone", "updated_at")


@admin.register(InvoiceSetting)
class InvoiceSettingAdmin(admin.ModelAdmin):
    list_display = ("invoice_prefix", "default_currency", "default_tax", "updated_at")


@admin.register(InvoiceHistory)
class InvoiceHistoryAdmin(admin.ModelAdmin):
    list_display = ("invoice", "version", "changed_by", "changed_at")
    readonly_fields = ("invoice", "version", "snapshot", "changed_by", "changed_at")


admin.site.register(InvoiceSequence)
