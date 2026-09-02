"""Policy: turn a match result into an auditable decision.

The rule is deliberately conservative — payment is the irreversible action, so anything
with a hard failure is rejected and anything ambiguous (soft exception or over budget)
goes to a human. Only a clean, in-budget invoice auto-approves.
"""

from __future__ import annotations

from ap_agent.config import Settings
from ap_agent.schemas import (
    Decision,
    Exception,
    Invoice,
    MatchResult,
    ProcessedInvoice,
    Severity,
)


def decide(
    invoice: Invoice,
    match: MatchResult,
    *,
    is_duplicate: bool = False,
    settings: Settings | None = None,
) -> ProcessedInvoice:
    settings = settings or Settings()
    exceptions: list[Exception] = list(match.exceptions)
    reasons: list[str] = []

    if is_duplicate:
        exceptions.append(Exception(code="duplicate", severity=Severity.HARD, detail="invoice already seen"))

    if invoice.total > settings.auto_approve_under:
        exceptions.append(
            Exception(
                code="over_budget",
                severity=Severity.SOFT,
                detail=f"total {invoice.total} over auto-approve limit {settings.auto_approve_under}",
            )
        )

    hard = [e for e in exceptions if e.severity == Severity.HARD]
    soft = [e for e in exceptions if e.severity == Severity.SOFT]

    if hard:
        decision = Decision.REJECT
        reasons = [f"hard: {e.code}" for e in hard]
    elif soft:
        decision = Decision.HOLD_FOR_REVIEW
        reasons = [f"review: {e.code}" for e in soft]
    else:
        decision = Decision.AUTO_APPROVE
        reasons = ["clean 3-way match within policy"]

    return ProcessedInvoice(invoice=invoice, decision=decision, exceptions=exceptions, reasons=reasons)
