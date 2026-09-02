"""The AP pipeline: extract -> 3-way match -> policy decision -> audit."""

from __future__ import annotations

from ap_agent.config import Settings, get_settings
from ap_agent.extraction import extract_invoice
from ap_agent.ledger import Ledger
from ap_agent.matching import three_way_match
from ap_agent.policy import decide
from ap_agent.schemas import Invoice, ProcessedInvoice


class APPipeline:
    def __init__(self, settings: Settings | None = None, ledger: Ledger | None = None) -> None:
        self.settings = settings or get_settings()
        self.ledger = ledger if ledger is not None else Ledger()

    def process_invoice(self, invoice: Invoice) -> ProcessedInvoice:
        is_duplicate = self.ledger.is_duplicate(invoice.invoice_id)
        po = self.ledger.purchase_order(invoice.po_id)
        grn = self.ledger.goods_receipt(invoice.po_id)
        match = three_way_match(invoice, po, grn, self.settings)
        result = decide(invoice, match, is_duplicate=is_duplicate, settings=self.settings)
        self.ledger.record(invoice.invoice_id)
        return result

    def process_text(self, raw: str) -> ProcessedInvoice:
        return self.process_invoice(extract_invoice(raw, self.settings))
