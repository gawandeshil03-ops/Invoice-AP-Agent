"""Deterministic 3-way match: invoice vs purchase order vs goods receipt.

This is the heart of AP automation and it is *all typed code* — no model gets to decide
whether the numbers line up. Hard failures (missing PO, math errors, over-billing) block
payment; soft exceptions (price variance) route to a human.
"""

from __future__ import annotations

from ap_agent.config import Settings
from ap_agent.schemas import (
    Exception,
    GoodsReceipt,
    Invoice,
    MatchResult,
    PurchaseOrder,
    Severity,
)


def _hard(code: str, detail: str) -> Exception:
    return Exception(code=code, severity=Severity.HARD, detail=detail)


def _soft(code: str, detail: str) -> Exception:
    return Exception(code=code, severity=Severity.SOFT, detail=detail)


def _check_math(invoice: Invoice, tol: float) -> list[Exception]:
    out: list[Exception] = []
    for ln in invoice.lines:
        if abs(ln.quantity * ln.unit_price - ln.amount) > tol:
            out.append(_hard("math_line", f"{ln.sku}: qty*unit != amount ({ln.amount})"))
    if abs(sum(ln.amount for ln in invoice.lines) - invoice.subtotal) > tol:
        out.append(_hard("math_subtotal", "line amounts do not sum to subtotal"))
    if abs(invoice.subtotal + invoice.tax - invoice.total) > tol:
        out.append(_hard("math_total", "subtotal + tax != total"))
    return out


def three_way_match(
    invoice: Invoice,
    po: PurchaseOrder | None,
    grn: GoodsReceipt | None,
    settings: Settings | None = None,
) -> MatchResult:
    settings = settings or Settings()
    exceptions: list[Exception] = _check_math(invoice, settings.total_tolerance)

    if po is None:
        exceptions.append(_hard("no_po", f"no purchase order for {invoice.po_id!r}"))
        return MatchResult(matched=False, exceptions=exceptions)

    if invoice.vendor.strip().lower() != po.vendor.strip().lower():
        exceptions.append(_hard("vendor_mismatch", f"invoice '{invoice.vendor}' != PO '{po.vendor}'"))

    po_lines = {ln.sku: ln for ln in po.lines}
    received = grn.received if grn else {}
    for ln in invoice.lines:
        po_line = po_lines.get(ln.sku)
        if po_line is None:
            exceptions.append(_hard("unknown_sku", f"{ln.sku} not on PO"))
            continue
        if ln.quantity > po_line.quantity:
            exceptions.append(
                _hard("over_billed_qty", f"{ln.sku}: billed {ln.quantity} > ordered {po_line.quantity}")
            )
        if ln.quantity > received.get(ln.sku, 0):
            exceptions.append(
                _hard(
                    "over_billed_receipt",
                    f"{ln.sku}: billed {ln.quantity} > received {received.get(ln.sku, 0)}",
                )
            )
        if po_line.unit_price > 0:
            variance = abs(ln.unit_price - po_line.unit_price) / po_line.unit_price
            if variance > settings.price_tolerance:
                exceptions.append(
                    _soft(
                        "price_variance",
                        f"{ln.sku}: unit {ln.unit_price} vs PO {po_line.unit_price} ({variance:.0%})",
                    )
                )

    matched = not any(e.severity == Severity.HARD for e in exceptions)
    return MatchResult(matched=matched, exceptions=exceptions)
