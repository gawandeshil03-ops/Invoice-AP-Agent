"""Invoice extraction — messy text to a typed Invoice.

This is the *only* place an LLM belongs in this workflow: turning unstructured invoice
text into structured fields. The default extractor is a deterministic rules parser (so
the repo runs offline and the eval is reproducible); set ``AP_EXTRACTOR=openai`` to use a
model instead. Everything downstream of here is typed, testable code.
"""

from __future__ import annotations

import re

from ap_agent.config import Settings
from ap_agent.schemas import Invoice, LineItem

_INVOICE_ID = re.compile(r"Invoice\s*#:\s*(\S+)", re.I)
_PO_ID = re.compile(r"PO\s*#:\s*(\S+)", re.I)
_VENDOR = re.compile(r"Vendor:\s*(.+)", re.I)
_LINE = re.compile(
    r"Line:\s*(?P<sku>\S+)\s*\|\s*qty\s*(?P<qty>[\d.]+)\s*\|\s*unit\s*(?P<unit>[\d.]+)\s*\|\s*(?P<amt>[\d.]+)",
    re.I,
)
_SUBTOTAL = re.compile(r"^Subtotal:\s*([\d.]+)", re.I | re.M)
_TAX = re.compile(r"^Tax:\s*([\d.]+)", re.I | re.M)
_TOTAL = re.compile(r"^Total:\s*([\d.]+)", re.I | re.M)
_NULL_PO = {"none", "n/a", "na", "-", ""}


def _search_float(pattern: re.Pattern[str], text: str) -> float:
    m = pattern.search(text)
    return float(m.group(1)) if m else 0.0


def extract_invoice_rules(raw: str) -> Invoice:
    """Deterministic regex extraction from a semi-structured invoice."""
    inv_id = (m.group(1) if (m := _INVOICE_ID.search(raw)) else "UNKNOWN").strip()
    po_raw = m.group(1).strip() if (m := _PO_ID.search(raw)) else ""
    po_id = None if po_raw.lower() in _NULL_PO else po_raw
    vendor = m.group(1).strip() if (m := _VENDOR.search(raw)) else "UNKNOWN"
    lines = [
        LineItem(
            sku=m.group("sku"),
            quantity=float(m.group("qty")),
            unit_price=float(m.group("unit")),
            amount=float(m.group("amt")),
        )
        for m in _LINE.finditer(raw)
    ]
    return Invoice(
        invoice_id=inv_id,
        po_id=po_id,
        vendor=vendor,
        lines=lines,
        subtotal=_search_float(_SUBTOTAL, raw),
        tax=_search_float(_TAX, raw),
        total=_search_float(_TOTAL, raw),
    )


def extract_invoice(raw: str, settings: Settings | None = None) -> Invoice:
    settings = settings or Settings()
    if settings.extractor in ("openai", "anthropic"):
        try:
            return _extract_invoice_llm(raw, settings)
        except Exception:
            return extract_invoice_rules(raw)  # graceful fallback
    return extract_invoice_rules(raw)


def _extract_invoice_llm(raw: str, settings: Settings) -> Invoice:  # pragma: no cover - needs keys
    """Use a model to extract structured fields (JSON), validated by pydantic."""
    import json

    prompt = (
        "Extract this invoice as JSON with keys invoice_id, po_id, vendor, "
        "lines (list of {sku, quantity, unit_price, amount}), subtotal, tax, total.\n\n" + raw
    )
    if settings.extractor == "openai":
        from openai import OpenAI

        resp = OpenAI().chat.completions.create(
            model=settings.model,
            temperature=0,
            response_format={"type": "json_object"},
            messages=[{"role": "user", "content": prompt}],
        )
        payload = resp.choices[0].message.content or "{}"
    else:
        from anthropic import Anthropic

        resp = Anthropic().messages.create(
            model=settings.model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        payload = resp.content[0].text
    return Invoice.model_validate(json.loads(payload))
