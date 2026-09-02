# Agent / contributor guide

Orientation for an AI agent or new contributor working in this repo.

## What this is

Accounts-payable invoice processing built to the principle **"an agent that knows when
*not* to be an agent."** An LLM (optional) extracts messy invoice text into structured
fields; everything consequential — the 3-way match and the pay/hold/reject decision — is
deterministic, typed, tested code. **Fully offline by default.**

## Layout

```
src/ap_agent/
  extraction.py   messy text -> Invoice (rules parser; optional openai/anthropic)
  ledger.py       purchase orders, goods receipts, duplicate tracking
  matching.py     deterministic 3-way match -> hard/soft exceptions
  policy.py       match -> Decision (auto_approve / hold_for_review / reject)
  pipeline.py     extract -> match -> decide -> record
  review.py       human-in-the-loop queue for held invoices
  evals.py        labeled-invoice eval + safety gate (THRESHOLDS)
  cli.py          run / eval / demo
data/             purchase_orders.jsonl · goods_receipts.jsonl · invoices.jsonl
tests/            one file per module
reports/          audit_report_example.md (committed proof)
```

## Conventions

- Python 3.11+ (CI pins 3.12). `from __future__ import annotations` everywhere. Ruff for
  lint/format (`make fmt`, `make lint`); line length 110.
- **The LLM only extracts.** Matching, math, and the decision are deterministic. Never
  move that logic into a prompt — it must be auditable and unit-tested.
- **Conservative by construction.** Hard failures (missing PO, math error, over-billing,
  duplicate) reject; soft exceptions (price variance, over budget) hold; only a clean,
  in-budget invoice auto-approves. Payment is irreversible, so the bias is toward review.
- **Never hand-write metrics.** Every number in the README/report comes from `evaluate()`.
  Change behavior, regenerate (`make report`), update the README.

## Definition of done

```bash
make lint   # ruff clean
make test   # all tests pass
make eval   # safety gate exits 0 (unsafe_auto_approvals == 0)
```

The same checks run in CI ([.github/workflows/ci.yml](.github/workflows/ci.yml)).

## Extending

- New check: add it to `matching.py` (hard vs soft), add a test, add a labeled invoice.
- Real extraction: set `AP_EXTRACTOR=openai`; the JSON is validated by the `Invoice` schema.
- New policy threshold: add to `config.py` and surface it in `policy.decide`.
