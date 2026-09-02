"""Pipeline + review queue + evaluation gate."""

from __future__ import annotations

from ap_agent.evals import evaluate
from ap_agent.ledger import Ledger
from ap_agent.pipeline import APPipeline
from ap_agent.review import ReviewQueue
from ap_agent.schemas import Decision

_CLEAN = (
    "Invoice #: INV-1001\nPO #: PO-5001\nVendor: Acme Corp\n"
    "Line: WIDGET-A | qty 10 | unit 5.00 | 50.00\n"
    "Line: WIDGET-B | qty 2 | unit 20.00 | 40.00\n"
    "Subtotal: 90.00\nTax: 9.00\nTotal: 99.00"
)


def test_clean_invoice_auto_approves():
    res = APPipeline(ledger=Ledger()).process_text(_CLEAN)
    assert res.decision == Decision.AUTO_APPROVE


def test_duplicate_second_time_rejects():
    pipe = APPipeline(ledger=Ledger())
    first = pipe.process_text(_CLEAN)
    second = pipe.process_text(_CLEAN)
    assert first.decision == Decision.AUTO_APPROVE
    assert second.decision == Decision.REJECT


def test_review_queue_only_holds():
    queue = ReviewQueue()
    pipe = APPipeline(ledger=Ledger())
    approved = pipe.process_text(_CLEAN)
    assert queue.submit(approved) is False
    assert queue.pending == []


def test_eval_gate_passes():
    report = evaluate()
    assert report.passed(), report.failures()
    assert report.aggregate["unsafe_auto_approvals"] == 0.0
    assert report.aggregate["decision_accuracy"] == 1.0
