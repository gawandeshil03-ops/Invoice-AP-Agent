"""The ledger: purchase orders, goods receipts, and duplicate tracking."""

from __future__ import annotations

import json
from pathlib import Path

from ap_agent.schemas import GoodsReceipt, LineItem, PurchaseOrder


def _data(name: str) -> Path:
    return Path(__file__).resolve().parents[2] / "data" / name


class Ledger:
    def __init__(
        self,
        purchase_orders: dict[str, PurchaseOrder] | None = None,
        goods_receipts: dict[str, GoodsReceipt] | None = None,
    ) -> None:
        self.purchase_orders = purchase_orders if purchase_orders is not None else self._load_pos()
        self.goods_receipts = goods_receipts if goods_receipts is not None else self._load_grns()
        self._seen: set[str] = set()

    @staticmethod
    def _load_pos() -> dict[str, PurchaseOrder]:
        out: dict[str, PurchaseOrder] = {}
        with _data("purchase_orders.jsonl").open() as fh:
            for line in fh:
                if not line.strip():
                    continue
                d = json.loads(line)
                po = PurchaseOrder(
                    po_id=d["po_id"],
                    vendor=d["vendor"],
                    lines=[LineItem(**ln) for ln in d["lines"]],
                )
                out[po.po_id] = po
        return out

    @staticmethod
    def _load_grns() -> dict[str, GoodsReceipt]:
        out: dict[str, GoodsReceipt] = {}
        with _data("goods_receipts.jsonl").open() as fh:
            for line in fh:
                if not line.strip():
                    continue
                d = json.loads(line)
                out[d["po_id"]] = GoodsReceipt(po_id=d["po_id"], received=d["received"])
        return out

    def purchase_order(self, po_id: str | None) -> PurchaseOrder | None:
        return self.purchase_orders.get(po_id or "")

    def goods_receipt(self, po_id: str | None) -> GoodsReceipt | None:
        return self.goods_receipts.get(po_id or "")

    def is_duplicate(self, invoice_id: str) -> bool:
        return invoice_id in self._seen

    def record(self, invoice_id: str) -> None:
        self._seen.add(invoice_id)
