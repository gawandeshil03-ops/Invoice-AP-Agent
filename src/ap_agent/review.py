"""Human-in-the-loop review queue for invoices held for review."""

from __future__ import annotations

from ap_agent.schemas import Decision, ProcessedInvoice


class ReviewQueue:
    """Invoices that need a human. Approving pays them; rejecting blocks them."""

    def __init__(self) -> None:
        self._pending: dict[str, ProcessedInvoice] = {}

    def submit(self, processed: ProcessedInvoice) -> bool:
        if processed.decision == Decision.HOLD_FOR_REVIEW:
            self._pending[processed.invoice.invoice_id] = processed
            return True
        return False

    @property
    def pending(self) -> list[ProcessedInvoice]:
        return list(self._pending.values())

    def approve(self, invoice_id: str) -> Decision:
        self._pending.pop(invoice_id, None)
        return Decision.AUTO_APPROVE

    def reject(self, invoice_id: str) -> Decision:
        self._pending.pop(invoice_id, None)
        return Decision.REJECT
