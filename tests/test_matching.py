"""Deterministic 3-way match."""

from __future__ import annotations

from ap_agent.matching import three_way_match
from ap_agent.schemas import GoodsReceipt, Invoice, LineItem, PurchaseOrder


def _po():
    return PurchaseOrder(
        po_id="PO-1", vendor="Acme", lines=[LineItem(sku="A", quantity=10, unit_price=5.0, amount=50.0)]
    )


def _grn():
    return GoodsReceipt(po_id="PO-1", received={"A": 10})


def _invoice(qty=10, unit=5.0, vendor="Acme", total=55.0, sub=50.0, tax=5.0):
    return Invoice(
        invoice_id="INV-1",
        po_id="PO-1",
        vendor=vendor,
        lines=[LineItem(sku="A", quantity=qty, unit_price=unit, amount=round(qty * unit, 2))],
        subtotal=sub,
        tax=tax,
        total=total,
    )


def test_clean_match():
    res = three_way_match(_invoice(), _po(), _grn())
    assert res.matched
    assert res.exceptions == []


def test_no_po_is_hard_failure():
    res = three_way_match(_invoice(), None, None)
    assert not res.matched
    assert any(e.code == "no_po" for e in res.hard_failures)


def test_over_billed_quantity_is_hard():
    res = three_way_match(_invoice(qty=20, sub=100.0, tax=10.0, total=110.0), _po(), _grn())
    assert any(e.code == "over_billed_qty" for e in res.hard_failures)


def test_vendor_mismatch_is_hard():
    res = three_way_match(_invoice(vendor="Other"), _po(), _grn())
    assert any(e.code == "vendor_mismatch" for e in res.hard_failures)


def test_price_variance_is_soft():
    res = three_way_match(_invoice(unit=5.5, sub=55.0, tax=5.5, total=60.5), _po(), _grn())
    assert res.matched  # soft only -> still "matched" (no hard failure)
    assert any(e.code == "price_variance" and e.severity.value == "soft" for e in res.exceptions)


def test_math_error_is_hard():
    bad = _invoice(total=999.0)  # subtotal 50 + tax 5 != 999
    res = three_way_match(bad, _po(), _grn())
    assert any(e.code == "math_total" for e in res.hard_failures)
