"""Invoice extraction."""

from __future__ import annotations

from ap_agent.extraction import extract_invoice_rules

_RAW = (
    "INVOICE\nInvoice #: INV-1001\nPO #: PO-5001\nVendor: Acme Corp\n"
    "Line: WIDGET-A | qty 10 | unit 5.00 | 50.00\n"
    "Line: WIDGET-B | qty 2 | unit 20.00 | 40.00\n"
    "Subtotal: 90.00\nTax: 9.00\nTotal: 99.00"
)


def test_extract_fields():
    inv = extract_invoice_rules(_RAW)
    assert inv.invoice_id == "INV-1001"
    assert inv.po_id == "PO-5001"
    assert inv.vendor == "Acme Corp"
    assert len(inv.lines) == 2
    assert inv.lines[0].sku == "WIDGET-A"


def test_total_is_not_subtotal():
    # Regression: 'Total:' must not match inside 'Subtotal:'.
    inv = extract_invoice_rules(_RAW)
    assert inv.subtotal == 90.0
    assert inv.total == 99.0


def test_missing_po_is_none():
    inv = extract_invoice_rules("Invoice #: INV-9\nPO #: NONE\nVendor: X\nTotal: 5.00")
    assert inv.po_id is None
