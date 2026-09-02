"""invoice-ap-agent — accounts-payable automation that knows when not to be an agent.

LLM-style extraction of messy invoices, then deterministic 3-way match (invoice / PO /
goods receipt), policy, and human-in-the-loop review for exceptions — with a safety gate
that no bad invoice is ever auto-approved. Runs fully offline.
"""

from __future__ import annotations

from ap_agent.config import Settings, get_settings
from ap_agent.evals import THRESHOLDS, EvalReport, evaluate
from ap_agent.extraction import extract_invoice
from ap_agent.ledger import Ledger
from ap_agent.matching import three_way_match
from ap_agent.pipeline import APPipeline
from ap_agent.policy import decide
from ap_agent.review import ReviewQueue
from ap_agent.schemas import Decision, Invoice, ProcessedInvoice

__version__ = "0.1.0"

__all__ = [
    "THRESHOLDS",
    "APPipeline",
    "Decision",
    "EvalReport",
    "Invoice",
    "Ledger",
    "ProcessedInvoice",
    "ReviewQueue",
    "Settings",
    "decide",
    "evaluate",
    "extract_invoice",
    "get_settings",
    "three_way_match",
    "__version__",
]
