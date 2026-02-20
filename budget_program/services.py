from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Iterable
from uuid import uuid4

from budget_program.db import get_conn


@dataclass
class AllocationTarget:
    target_type: str
    target_id: str
    percent: float


def new_id() -> str:
    return str(uuid4())


def round2(amount: float) -> float:
    return round(amount + 1e-9, 2)


def validate_allocation_total(percents: Iterable[float]) -> bool:
    return round2(sum(percents)) == 100.0


def compute_allocation_amounts(amount: float, targets: list[AllocationTarget]) -> list[tuple[AllocationTarget, float]]:
    if not targets:
        return []
    raw = [round2(amount * target.percent / 100.0) for target in targets]
    allocated = round2(sum(raw))
    remainder = round2(amount - allocated)
    if remainder:
        biggest_idx = max(range(len(targets)), key=lambda i: targets[i].percent)
        raw[biggest_idx] = round2(raw[biggest_idx] + remainder)
    return list(zip(targets, raw))


def list_rows(table: str) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(f"SELECT * FROM {table} ORDER BY name").fetchall()
    return [dict(r) for r in rows]


def upsert_item(table: str, item_id: str | None, fields: dict) -> None:
    item_id = item_id or new_id()
    cols = ["id", *fields.keys()]
    vals = [item_id, *fields.values()]
    placeholders = ",".join("?" for _ in cols)
    with get_conn() as conn:
        conn.execute(f"INSERT OR REPLACE INTO {table} ({','.join(cols)}) VALUES ({placeholders})", vals)


def delete_item(table: str, item_id: str) -> None:
    with get_conn() as conn:
        conn.execute(f"DELETE FROM {table} WHERE id=?", (item_id,))


def save_allocations(items: list[dict]) -> None:
    percents = [float(i["percent"]) for i in items]
    if not validate_allocation_total(percents):
        raise ValueError("Allocation percentages must total 100")
    with get_conn() as conn:
        conn.execute("DELETE FROM allocations")
        for item in items:
            conn.execute(
                "INSERT INTO allocations(id, target_type, target_id, percent) VALUES(?,?,?,?)",
                (new_id(), item["target_type"], item["target_id"], float(item["percent"])),
            )


def dashboard_summary() -> dict:
    with get_conn() as conn:
        assets = conn.execute("SELECT COALESCE(SUM(balance),0) AS total FROM accounts").fetchone()["total"]
        debts = conn.execute("SELECT COALESCE(SUM(balance),0) AS total FROM debts").fetchone()["total"]
        fixed = conn.execute("SELECT COALESCE(SUM(amount_monthly),0) AS total FROM fixed_expenses").fetchone()["total"]
        tx = conn.execute("SELECT * FROM transactions ORDER BY date_iso DESC LIMIT 10").fetchall()
    return {
        "assets": round2(assets),
        "debts": round2(debts),
        "net_worth": round2(assets - debts),
        "fixed": round2(fixed),
        "transactions": [dict(r) for r in tx],
    }


def create_income(amount: float, date_iso: str | None, note: str | None) -> None:
    tx_id = new_id()
    date_iso = date_iso or date.today().isoformat()
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO transactions(id, type, amount, date_iso, note, category, account_id) VALUES(?,?,?,?,?,?,?)",
            (tx_id, "INCOME", amount, date_iso, note, None, None),
        )
        targets = [AllocationTarget(r["target_type"], r["target_id"], r["percent"]) for r in conn.execute("SELECT * FROM allocations")]
        for target, alloc_amount in compute_allocation_amounts(amount, targets):
            conn.execute(
                "INSERT INTO allocation_events(id, transaction_id, target_type, target_id, amount) VALUES(?,?,?,?,?)",
                (new_id(), tx_id, target.target_type, target.target_id, alloc_amount),
            )
            if target.target_type == "account":
                conn.execute("UPDATE accounts SET balance=balance+? WHERE id=?", (alloc_amount, target.target_id))
            else:
                row = conn.execute("SELECT balance FROM debts WHERE id=?", (target.target_id,)).fetchone()
                if row:
                    new_balance = max(0.0, round2(row["balance"] - alloc_amount))
                    conn.execute("UPDATE debts SET balance=? WHERE id=?", (new_balance, target.target_id))


def create_expense(amount: float, date_iso: str, note: str | None, category: str | None, account_id: str | None) -> None:
    with get_conn() as conn:
        if account_id:
            conn.execute("UPDATE accounts SET balance=balance-? WHERE id=?", (amount, account_id))
        conn.execute(
            "INSERT INTO transactions(id, type, amount, date_iso, note, category, account_id) VALUES(?,?,?,?,?,?,?)",
            (new_id(), "EXPENSE", amount, date_iso, note, category, account_id),
        )


def default_checking_account_id() -> str | None:
    with get_conn() as conn:
        checking = conn.execute("SELECT id FROM accounts WHERE lower(type)='checking' ORDER BY name LIMIT 1").fetchone()
        if checking:
            return checking["id"]
        any_account = conn.execute("SELECT id FROM accounts ORDER BY name LIMIT 1").fetchone()
    return any_account["id"] if any_account else None
