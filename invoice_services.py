from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from .models import (
    CompanyProfile,
    Invoice,
    InvoiceHistory,
    InvoiceItem,
    InvoiceSequence,
    InvoiceSetting,
)


MONEY = Decimal("0.01")


def money(value: Any, default: str = "0") -> Decimal:
    try:
        return Decimal(str(value if value not in (None, "") else default)).quantize(
            MONEY,
            rounding=ROUND_HALF_UP,
        )
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValidationError("Enter a valid monetary value.") from exc


def percentage(value: Any) -> Decimal:
    result = money(value)
    if result < 0 or result > 100:
        raise ValidationError("Percentages must be between 0 and 100.")
    return result


def get_invoice_defaults() -> tuple[CompanyProfile, InvoiceSetting]:
    profile, _ = CompanyProfile.objects.get_or_create(pk=1)
    settings, _ = InvoiceSetting.objects.get_or_create(pk=1)
    return profile, settings


def peek_invoice_number(for_date: date | None = None) -> str:
    for_date = for_date or timezone.localdate()
    settings = InvoiceSetting.objects.filter(pk=1).first()
    prefix = settings.invoice_prefix if settings else "INV"
    sequence = InvoiceSequence.objects.filter(date=for_date).first()
    next_number = (sequence.last_number if sequence else 0) + 1
    return f"{prefix}-{for_date:%Y%m%d}-{next_number:04d}"


def _next_invoice_number(for_date: date) -> str:
    settings = InvoiceSetting.objects.filter(pk=1).first()
    prefix = settings.invoice_prefix if settings else "INV"
    sequence, _ = InvoiceSequence.objects.select_for_update().get_or_create(
        date=for_date,
        defaults={"last_number": 0},
    )
    sequence.last_number += 1
    sequence.save(update_fields=["last_number"])
    return f"{prefix}-{for_date:%Y%m%d}-{sequence.last_number:04d}"


def _validated_items(payload: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Decimal]]:
    raw_items = payload.get("items") or []
    if not raw_items:
        raise ValidationError({"items": "Add at least one invoice item."})

    items: list[dict[str, Any]] = []
    subtotal = Decimal("0.00")
    discount_total = Decimal("0.00")
    tax_total = Decimal("0.00")

    for position, raw_item in enumerate(raw_items):
        description = str(raw_item.get("description", "")).strip()
        if not description:
            raise ValidationError({"items": "Every item needs a description."})

        quantity = money(raw_item.get("quantity"))
        unit_price = money(raw_item.get("unit_price"))
        discount_percent = percentage(raw_item.get("discount_percent", 0))
        tax_percent = percentage(raw_item.get("tax_percent", 0))
        if quantity <= 0:
            raise ValidationError({"items": "Quantity must be greater than zero."})
        if unit_price < 0:
            raise ValidationError({"items": "Unit price cannot be negative."})

        base = (quantity * unit_price).quantize(MONEY)
        discount = (base * discount_percent / 100).quantize(MONEY)
        taxable = base - discount
        tax = (taxable * tax_percent / 100).quantize(MONEY)
        line_total = taxable + tax
        subtotal += base
        discount_total += discount
        tax_total += tax
        items.append(
            {
                "position": position,
                "description": description,
                "quantity": quantity,
                "unit_price": unit_price,
                "discount_percent": discount_percent,
                "tax_percent": tax_percent,
                "line_total": line_total,
            }
        )

    return items, {
        "subtotal": subtotal.quantize(MONEY),
        "discount_total": discount_total.quantize(MONEY),
        "tax_total": tax_total.quantize(MONEY),
    }


def _invoice_values(payload: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    customer_name = str(payload.get("customer_name", "")).strip()
    if not customer_name:
        raise ValidationError({"customer_name": "Customer name is required."})

    try:
        invoice_date = date.fromisoformat(str(payload.get("invoice_date", "")))
    except ValueError as exc:
        raise ValidationError({"invoice_date": "Invoice date is required."}) from exc

    due_date_value = payload.get("due_date")
    try:
        due_date = date.fromisoformat(str(due_date_value)) if due_date_value else None
    except ValueError as exc:
        raise ValidationError({"due_date": "Enter a valid due date."}) from exc
    items, totals = _validated_items(payload)
    shipping = money(payload.get("shipping"))
    service_charge = money(payload.get("service_charge"))
    extra_cost = money(payload.get("extra_cost"))
    additional_discount = money(payload.get("additional_discount"))
    paid_amount = money(payload.get("paid_amount"))
    if min(shipping, service_charge, extra_cost, paid_amount) < 0:
        raise ValidationError(
            {"charges": "Charges and paid amount cannot be negative."}
        )
    grand_total = (
        totals["subtotal"]
        - totals["discount_total"]
        + totals["tax_total"]
        + shipping
        + service_charge
        + extra_cost
        - additional_discount
    ).quantize(MONEY)
    balance = (grand_total - paid_amount).quantize(MONEY)

    values = {
        "customer_name": customer_name,
        "customer_company": str(payload.get("customer_company", "")).strip(),
        "customer_address": str(payload.get("customer_address", "")).strip(),
        "customer_phone": str(payload.get("customer_phone", "")).strip(),
        "customer_email": str(payload.get("customer_email", "")).strip(),
        "invoice_date": invoice_date,
        "due_date": due_date,
        "currency": str(payload.get("currency", "BDT")).strip().upper()[:8],
        "notes": str(payload.get("notes", "")).strip(),
        "payment_terms": str(payload.get("payment_terms", "")).strip(),
        "status": str(payload.get("status", Invoice.STATUS_DRAFT)).lower(),
        "shipping": shipping,
        "service_charge": service_charge,
        "extra_cost": extra_cost,
        "additional_discount": additional_discount,
        "paid_amount": paid_amount,
        "balance": balance,
        "grand_total": grand_total,
        **totals,
    }
    if values["status"] not in dict(Invoice.STATUS_CHOICES):
        raise ValidationError({"status": "Choose a valid invoice status."})
    return values, items


def serialize_invoice(invoice: Invoice, include_history: bool = False) -> dict[str, Any]:
    result: dict[str, Any] = {
        "id": invoice.pk,
        "invoice_number": invoice.invoice_number,
        "version": invoice.version,
        "customer_name": invoice.customer_name,
        "customer_company": invoice.customer_company,
        "customer_address": invoice.customer_address,
        "customer_phone": invoice.customer_phone,
        "customer_email": invoice.customer_email,
        "invoice_date": invoice.invoice_date.isoformat(),
        "due_date": invoice.due_date.isoformat() if invoice.due_date else "",
        "currency": invoice.currency,
        "notes": invoice.notes,
        "payment_terms": invoice.payment_terms,
        "status": invoice.status,
        "shipping": str(invoice.shipping),
        "service_charge": str(invoice.service_charge),
        "extra_cost": str(invoice.extra_cost),
        "additional_discount": str(invoice.additional_discount),
        "subtotal": str(invoice.subtotal),
        "discount_total": str(invoice.discount_total),
        "tax_total": str(invoice.tax_total),
        "grand_total": str(invoice.grand_total),
        "paid_amount": str(invoice.paid_amount),
        "balance": str(invoice.balance),
        "outstanding_amount": str(invoice.outstanding_amount),
        "created_at": invoice.created_at.isoformat(),
        "updated_at": invoice.updated_at.isoformat(),
        "created_by": invoice.created_by.get_full_name() or invoice.created_by.email,
        "items": [
            {
                "id": item.pk,
                "description": item.description,
                "quantity": str(item.quantity),
                "unit_price": str(item.unit_price),
                "discount_percent": str(item.discount_percent),
                "tax_percent": str(item.tax_percent),
                "line_total": str(item.line_total),
            }
            for item in invoice.items.all()
        ],
    }
    if include_history:
        result["history"] = [
            {
                "version": entry.version,
                "changed_at": entry.changed_at.isoformat(),
                "changed_by": entry.changed_by.get_full_name()
                or entry.changed_by.email,
            }
            for entry in invoice.history.select_related("changed_by").all()
        ]
    return result


def _snapshot(invoice: Invoice) -> dict[str, Any]:
    return serialize_invoice(invoice)


@transaction.atomic
def create_invoice(payload: dict[str, Any], user) -> Invoice:
    values, items = _invoice_values(payload)
    values["invoice_number"] = _next_invoice_number(values["invoice_date"])
    invoice = Invoice.objects.create(created_by=user, **values)
    InvoiceItem.objects.bulk_create(
        [InvoiceItem(invoice=invoice, **item) for item in items]
    )
    return Invoice.objects.prefetch_related("items").get(pk=invoice.pk)


@transaction.atomic
def update_invoice(invoice: Invoice, payload: dict[str, Any], user) -> Invoice:
    invoice = (
        Invoice.objects.select_for_update()
        .prefetch_related("items")
        .get(pk=invoice.pk, deleted_at__isnull=True)
    )
    InvoiceHistory.objects.create(
        invoice=invoice,
        version=invoice.version,
        snapshot=_snapshot(invoice),
        changed_by=user,
    )
    values, items = _invoice_values(payload)
    for field, value in values.items():
        setattr(invoice, field, value)
    invoice.version += 1
    invoice.save()
    invoice.items.all().delete()
    InvoiceItem.objects.bulk_create(
        [InvoiceItem(invoice=invoice, **item) for item in items]
    )
    return Invoice.objects.prefetch_related("items").get(pk=invoice.pk)
