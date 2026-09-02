"""Evaluation + safety gate.

Replays a labeled set of invoices through the real pipeline and scores extraction and
decision accuracy — but the metric that actually gates CI is **unsafe_auto_approvals**:
the number of invoices that should have been held or rejected but were auto-approved.
That must be exactly zero. A wrong "hold" is annoying; a wrong "pay" is money out the door.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from ap_agent.config import Settings, get_settings
from ap_agent.extraction import extract_invoice
from ap_agent.ledger import Ledger
from ap_agent.pipeline import APPipeline
from ap_agent.schemas import Decision

THRESHOLDS = {
    "decision_accuracy": 0.90,
    "extraction_accuracy": 0.95,
    "unsafe_auto_approvals": 0.0,  # must be exactly zero
}


def _invoices_path() -> Path:
    return Path(__file__).resolve().parents[2] / "data" / "invoices.jsonl"


def load_invoices(path: Path | None = None) -> list[dict]:
    with (path or _invoices_path()).open() as fh:
        return [json.loads(line) for line in fh if line.strip()]


@dataclass
class EvalReport:
    n: int
    aggregate: dict
    results: list[dict] = field(default_factory=list)

    def passed(self) -> bool:
        return not self.failures()

    def failures(self) -> list[str]:
        out: list[str] = []
        for metric, threshold in THRESHOLDS.items():
            value = self.aggregate.get(metric, 0.0)
            if metric == "unsafe_auto_approvals":
                if value > threshold:
                    out.append(f"{metric}={value:.0f} > {threshold:.0f}")
            elif value < threshold:
                out.append(f"{metric}={value:.3f} < {threshold:.2f}")
        return out


def evaluate(settings: Settings | None = None, invoices: list[dict] | None = None) -> EvalReport:
    settings = settings or get_settings()
    invoices = invoices if invoices is not None else load_invoices()
    pipeline = APPipeline(settings, ledger=Ledger())

    correct = extracted = unsafe = 0
    results: list[dict] = []
    for row in invoices:
        invoice = extract_invoice(row["raw"], settings)
        ext_ok = abs(invoice.total - row.get("expected_total", invoice.total)) <= settings.total_tolerance
        processed = pipeline.process_invoice(invoice)
        decision_ok = processed.decision.value == row["expected_decision"]
        if processed.decision == Decision.AUTO_APPROVE and row["expected_decision"] != "auto_approve":
            unsafe += 1
        correct += decision_ok
        extracted += ext_ok
        results.append(
            {
                "id": row["id"],
                "decision": processed.decision.value,
                "expected": row["expected_decision"],
                "decision_ok": decision_ok,
                "extracted_ok": ext_ok,
            }
        )

    n = len(invoices)
    aggregate = {
        "decision_accuracy": correct / n,
        "extraction_accuracy": extracted / n,
        "unsafe_auto_approvals": float(unsafe),
    }
    return EvalReport(n=n, aggregate=aggregate, results=results)


def write_markdown(report: EvalReport, path: Path) -> None:
    lines = [
        "# invoice-ap-agent — evaluation report",
        "",
        f"Replays **{report.n}** labeled invoices through the pipeline (extraction + "
        "deterministic 3-way match + policy). The headline guarantee is "
        "**unsafe_auto_approvals = 0**: no invoice that should be held or rejected is ever "
        "auto-approved for payment.",
        "",
        "| metric | value | threshold | pass |",
        "| --- | --- | --- | --- |",
    ]
    for metric, threshold in THRESHOLDS.items():
        value = report.aggregate.get(metric, 0.0)
        ok = (value <= threshold) if metric == "unsafe_auto_approvals" else (value >= threshold)
        comp = "≤" if metric == "unsafe_auto_approvals" else "≥"
        lines.append(f"| {metric} | {value:.3f} | {comp} {threshold:.2f} | {'✅' if ok else '❌'} |")
    lines += ["", f"**Gate: {'PASSED' if report.passed() else 'FAILED'}**", ""]
    path.write_text("\n".join(lines) + "\n")
