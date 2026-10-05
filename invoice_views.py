from __future__ import annotations

import json
from datetime import date

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpRequest, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from .invoice_services import (
    create_invoice,
    get_invoice_defaults,
    peek_invoice_number,
    serialize_invoice,
    update_invoice,
)
from .models import CompanyProfile, Invoice, InvoiceSetting


def _can_edit(user) -> bool:
    if user.is_superuser:
        return True
    return bool(user.is_staff and (user.staff_role or "").lower() != "read only")


def _error_response(exc: ValidationError, status: int = 400) -> JsonResponse:
    if hasattr(exc, "message_dict"):
        errors = exc.message_dict
    else:
        errors = {"detail": exc.messages}
    return JsonResponse({"ok": False, "errors": errors}, status=status)


def _json_body(request: HttpRequest) -> dict:
    try:
        return json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError as exc:
        raise ValidationError("Invalid JSON payload.") from exc


def _profile_data(profile: CompanyProfile) -> dict:
    return {
        "company_name": profile.company_name,
        "address": profile.address,
        "phone": profile.phone,
        "email": profile.email,
        "website": profile.website,
        "vat_number": profile.vat_number,
        "tax_number": profile.tax_number,
        "logo_url": profile.logo.url if profile.logo else "",
    }


def _settings_data(settings: InvoiceSetting) -> dict:
    return {
        "invoice_prefix": settings.invoice_prefix,
        "invoice_footer": settings.invoice_footer,
        "default_tax": str(settings.default_tax),
        "default_currency": settings.default_currency,
        "default_notes": settings.default_notes,
        "bank_information": settings.bank_information,
        "payment_instructions": settings.payment_instructions,
        "signature_url": settings.signature.url if settings.signature else "",
    }


@login_required(login_url="/676e11f5b8cf16405f49cba58e6216405f49cba5/admin/login/")
def invoice_workspace(request: HttpRequest):
    profile, settings = get_invoice_defaults()
    today = timezone.localdate()
    context = {
        "company_json": json.dumps(_profile_data(profile)),
        "settings_json": json.dumps(_settings_data(settings)),
        "suggested_number": peek_invoice_number(today),
        "today": today.isoformat(),
        "default_due_date": date.fromordinal(today.toordinal() + 14).isoformat(),
        "can_edit": _can_edit(request.user),
    }
    return render(request, "kehem/invoice_workspace.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def invoice_collection_api(request: HttpRequest):
    if request.method == "POST":
        if not _can_edit(request.user):
            return JsonResponse({"ok": False, "detail": "Read-only access."}, status=403)
        try:
            invoice = create_invoice(_json_body(request), request.user)
        except ValidationError as exc:
            return _error_response(exc)
        return JsonResponse({"ok": True, "invoice": serialize_invoice(invoice)}, status=201)

    invoices = (
        Invoice.objects.filter(deleted_at__isnull=True)
        .select_related("created_by")
        .prefetch_related("items")
    )
    query = request.GET.get("q", "").strip()
    status_filter = request.GET.get("status", "").strip().lower()
    customer = request.GET.get("customer", "").strip()
    date_from = request.GET.get("date_from", "").strip()
    date_to = request.GET.get("date_to", "").strip()
    ordering = request.GET.get("ordering", "-created_at")
    allowed_ordering = {
        "-created_at",
        "created_at",
        "-grand_total",
        "grand_total",
        "invoice_number",
        "-invoice_number",
    }
    if query:
        invoices = invoices.filter(
            Q(invoice_number__icontains=query)
            | Q(customer_name__icontains=query)
            | Q(customer_phone__icontains=query)
            | Q(customer_company__icontains=query)
            | Q(status__icontains=query)
        )
    if status_filter in dict(Invoice.STATUS_CHOICES):
        invoices = invoices.filter(status=status_filter)
    if customer:
        invoices = invoices.filter(
            Q(customer_name__icontains=customer)
            | Q(customer_company__icontains=customer)
        )
    if date_from:
        invoices = invoices.filter(invoice_date__gte=date_from)
    if date_to:
        invoices = invoices.filter(invoice_date__lte=date_to)
    invoices = invoices.order_by(ordering if ordering in allowed_ordering else "-created_at")

    paginator = Paginator(invoices, 12)
    page = paginator.get_page(request.GET.get("page", 1))
    return JsonResponse(
        {
            "ok": True,
            "results": [serialize_invoice(invoice) for invoice in page.object_list],
            "pagination": {
                "page": page.number,
                "pages": paginator.num_pages,
                "count": paginator.count,
                "has_next": page.has_next(),
                "has_previous": page.has_previous(),
            },
        }
    )


@login_required
@require_http_methods(["GET", "PUT", "DELETE"])
def invoice_detail_api(request: HttpRequest, invoice_id: int):
    invoice = get_object_or_404(
        Invoice.objects.select_related("created_by").prefetch_related("items"),
        pk=invoice_id,
        deleted_at__isnull=True,
    )
    if request.method == "GET":
        return JsonResponse(
            {"ok": True, "invoice": serialize_invoice(invoice, include_history=True)}
        )
    if not _can_edit(request.user):
        return JsonResponse({"ok": False, "detail": "Read-only access."}, status=403)
    if request.method == "DELETE":
        invoice.deleted_at = timezone.now()
        invoice.save(update_fields=["deleted_at", "updated_at"])
        return JsonResponse({"ok": True})
    try:
        invoice = update_invoice(invoice, _json_body(request), request.user)
    except ValidationError as exc:
        return _error_response(exc)
    return JsonResponse({"ok": True, "invoice": serialize_invoice(invoice)})


@login_required
@require_http_methods(["GET", "POST"])
def invoice_settings_api(request: HttpRequest):
    profile, settings = get_invoice_defaults()
    if request.method == "GET":
        return JsonResponse(
            {
                "ok": True,
                "company": _profile_data(profile),
                "settings": _settings_data(settings),
            }
        )
    if not _can_edit(request.user):
        return JsonResponse({"ok": False, "detail": "Read-only access."}, status=403)

    company_fields = (
        "company_name",
        "address",
        "phone",
        "email",
        "website",
        "vat_number",
        "tax_number",
    )
    setting_fields = (
        "invoice_prefix",
        "invoice_footer",
        "default_tax",
        "default_currency",
        "default_notes",
        "bank_information",
        "payment_instructions",
    )
    for field in company_fields:
        if field in request.POST:
            setattr(profile, field, request.POST[field].strip())
    for field in setting_fields:
        if field in request.POST:
            setattr(settings, field, request.POST[field].strip())
    if request.FILES.get("logo"):
        profile.logo = request.FILES["logo"]
    if request.FILES.get("signature"):
        settings.signature = request.FILES["signature"]
    profile.full_clean()
    settings.full_clean()
    profile.save()
    settings.save()
    return JsonResponse(
        {
            "ok": True,
            "company": _profile_data(profile),
            "settings": _settings_data(settings),
            "next_number": peek_invoice_number(),
        }
    )
