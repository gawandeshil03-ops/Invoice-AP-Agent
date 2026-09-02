"""Policy decisions."""

from __future__ import annotations

from ap_agent.config import Settings
from ap_agent.matching import three_way_match
from ap_agent.policy import decide
from ap_agent.schemas import Decision, GoodsReceipt, Invoice, LineItem, PurchaseOrder


def _setup(qty=10, unit=5.0, total=55.0, sub=50.0, tax=5.0, vendor="Acme"):
    inv = Invoice(
        invoice_id="INV-1",
        po_id="PO-1",
        vendor=vendor,
        lines=[LineItem(sku="A", quantity=qty, unit_price=unit, amount=round(qty * unit, 2))],
        subtotal=sub,
        tax=tax,
        total=total,
    )
    po = PurchaseOrder(
        po_id="PO-1", vendor="Acme", lines=[LineItem(sku="A", quantity=10, unit_price=5.0, amount=50.0)]
    )
    grn = GoodsReceipt(po_id="PO-1", received={"A": 10})
    return inv, po, grn


def test_clean_auto_approves():
    inv, po, grn = _setup()
    res = decide(inv, three_way_match(inv, po, grn))
    assert res.decision == Decision.AUTO_APPROVE


def test_soft_exception_holds():
    inv, po, grn = _setup(unit=5.5, sub=55.0, tax=5.5, total=60.5)
    res = decide(inv, three_way_match(inv, po, grn))
    assert res.decision == Decision.HOLD_FOR_REVIEW


def test_hard_failure_rejects():
    inv, po, grn = _setup(vendor="Other")
    res = decide(inv, three_way_match(inv, po, grn))
    assert res.decision == Decision.REJECT


def test_over_budget_holds():
    inv, po, grn = _setup()
    res = decide(inv, three_way_match(inv, po, grn), settings=Settings(auto_approve_under=10.0))
    assert res.decision == Decision.HOLD_FOR_REVIEW


def test_duplicate_rejects():
    inv, po, grn = _setup()
    res = decide(inv, three_way_match(inv, po, grn), is_duplicate=True)
    assert res.decision == Decision.REJECT
