# invoice-ap-agent — evaluation report

Replays **12** labeled invoices through the pipeline (extraction + deterministic 3-way match + policy). The headline guarantee is **unsafe_auto_approvals = 0**: no invoice that should be held or rejected is ever auto-approved for payment.

| metric | value | threshold | pass |
| --- | --- | --- | --- |
| decision_accuracy | 1.000 | ≥ 0.90 | ✅ |
| extraction_accuracy | 1.000 | ≥ 0.95 | ✅ |
| unsafe_auto_approvals | 0.000 | ≤ 0.00 | ✅ |

**Gate: PASSED**

