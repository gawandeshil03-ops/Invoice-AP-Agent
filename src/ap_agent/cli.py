"""Command-line interface."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from rich.console import Console
from rich.table import Table

from ap_agent.config import get_settings
from ap_agent.evals import THRESHOLDS, evaluate, load_invoices, write_markdown
from ap_agent.ledger import Ledger
from ap_agent.pipeline import APPipeline
from ap_agent.review import ReviewQueue

console = Console()

_COLOR = {"auto_approve": "green", "hold_for_review": "yellow", "reject": "red"}


def _cmd_run(_args) -> int:
    pipeline = APPipeline(get_settings(), ledger=Ledger())
    queue = ReviewQueue()
    table = Table(title="invoice-ap-agent · processing")
    table.add_column("invoice")
    table.add_column("vendor")
    table.add_column("total", justify="right")
    table.add_column("decision")
    table.add_column("reasons")
    for row in load_invoices():
        processed = pipeline.process_text(row["raw"])
        queue.submit(processed)
        color = _COLOR.get(processed.decision.value, "white")
        table.add_row(
            processed.invoice.invoice_id,
            processed.invoice.vendor,
            f"{processed.invoice.total:,.2f}",
            f"[{color}]{processed.decision.value}[/]",
            ", ".join(processed.reasons),
        )
    console.print(table)
    console.print(f"[yellow]{len(queue.pending)} invoice(s) awaiting human review.[/]")
    return 0


def _cmd_eval(args) -> int:
    report = evaluate(get_settings())
    table = Table(title="invoice-ap-agent · evaluation")
    table.add_column("metric")
    table.add_column("value", justify="right")
    table.add_column("threshold", justify="right")
    table.add_column("", justify="center")
    for metric, threshold in THRESHOLDS.items():
        value = report.aggregate.get(metric, 0.0)
        ok = (value <= threshold) if metric == "unsafe_auto_approvals" else (value >= threshold)
        table.add_row(metric, f"{value:.3f}", f"{threshold:.2f}", "✅" if ok else "❌")
    console.print(table)
    if args.report:
        write_markdown(report, Path(args.report))
        console.print(f"[dim]wrote report to {args.report}[/]")
    if report.passed():
        console.print(f"[bold green]GATE PASSED[/] over {report.n} invoices")
        return 0
    console.print(f"[bold red]GATE FAILED[/]: {', '.join(report.failures())}")
    return 1


def _cmd_demo(_args) -> int:
    pipeline = APPipeline(get_settings(), ledger=Ledger())
    for row in load_invoices()[:6]:
        processed = pipeline.process_text(row["raw"])
        color = _COLOR.get(processed.decision.value, "white")
        console.print(
            f"[{color}]{processed.decision.value:16s}[/] {processed.invoice.invoice_id}  "
            f"{processed.invoice.vendor:14s}  ${processed.invoice.total:>8,.2f}  "
            f"({', '.join(processed.reasons)})"
        )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ap-agent", description="Accounts-payable invoice agent.")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("run", help="Process every invoice and print the decisions.").set_defaults(func=_cmd_run)

    p_eval = sub.add_parser("eval", help="Run the evaluation suite + safety gate.")
    p_eval.add_argument("--report", default=None, help="Write a markdown report to this path.")
    p_eval.set_defaults(func=_cmd_eval)

    sub.add_parser("demo", help="Process a few invoices.").set_defaults(func=_cmd_demo)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
