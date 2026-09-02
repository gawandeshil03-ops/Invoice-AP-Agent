"""Typed domain model for accounts-payable processing."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class Decision(str, Enum):
    AUTO_APPROVE = "auto_approve"  # clean match, within policy
    HOLD_FOR_REVIEW = "hold_for_review"  # exceptions -> human
    REJECT = "reject"  # hard violation -> refuse


class Severity(str, Enum):
    HARD = "hard"  # blocks payment outright (duplicate, no PO, math error, over-billing)
    SOFT = "soft"  # needs human judgement (price variance, over budget)


class LineItem(BaseModel):
    sku: str
    quantity: float
    unit_price: float
    amount: float


class Invoice(BaseModel):
    invoice_id: str
    po_id: str | None = None
    vendor: str
    lines: list[LineItem] = Field(default_factory=list)
    subtotal: float = 0.0
    tax: float = 0.0
    total: float = 0.0


class PurchaseOrder(BaseModel):
    po_id: str
    vendor: str
    lines: list[LineItem] = Field(default_factory=list)


class GoodsReceipt(BaseModel):
    po_id: str
    received: dict[str, float] = Field(default_factory=dict)  # sku -> qty received


class Exception(BaseModel):
    code: str
    severity: Severity
    detail: str


class MatchResult(BaseModel):
    matched: bool
    exceptions: list[Exception] = Field(default_factory=list)

    @property
    def hard_failures(self) -> list[Exception]:
        return [e for e in self.exceptions if e.severity == Severity.HARD]


class ProcessedInvoice(BaseModel):
    invoice: Invoice
    decision: Decision
    exceptions: list[Exception] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)

    @property
    def auto_approved(self) -> bool:
        return self.decision == Decision.AUTO_APPROVE
