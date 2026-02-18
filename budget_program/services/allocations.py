"""Paycheck allocation and category balance calculations."""

from __future__ import annotations

from datetime import date

from database import execute, fetchall, fetchone

ALLOCATION_TOLERANCE = 0.01


def get_top_level_categories() -> list:
    return fetchall(
        """
        SELECT id, name, allocation_pct
        FROM categories
        WHERE parent_id IS NULL
        ORDER BY id
        """
    )


def allocation_total_is_valid() -> tuple[bool, float]:
    row = fetchone(
        """
        SELECT COALESCE(SUM(allocation_pct), 0.0) AS total
        FROM categories
        WHERE parent_id IS NULL
        """
    )
    total = float(row["total"] if row else 0.0)
    return abs(total - 100.0) <= ALLOCATION_TOLERANCE, total


def add_paycheck(amount: float, paycheck_date: str | None = None, note: str = "") -> int:
    valid, total = allocation_total_is_valid()
    if not valid:
        raise ValueError(f"Top-level category allocations must total 100%. Current total: {total:.2f}%")

    paycheck_date = paycheck_date or date.today().isoformat()
    paycheck_id = execute(
        "INSERT INTO paychecks(date, amount, note) VALUES (?, ?, ?)",
        (paycheck_date, amount, note.strip() or None),
    )

    categories = get_top_level_categories()
    if not categories:
        raise ValueError("No top-level categories found. Run setup or manage categories first.")

    running_total = 0.0
    for idx, category in enumerate(categories):
        pct = float(category["allocation_pct"])
        if idx == len(categories) - 1:
            allocation_amt = round(amount - running_total, 2)
        else:
            allocation_amt = round(amount * (pct / 100.0), 2)
            running_total += allocation_amt

        execute(
            "INSERT INTO allocations(paycheck_id, category_id, amount) VALUES (?, ?, ?)",
            (paycheck_id, int(category["id"]), allocation_amt),
        )

    return paycheck_id


def add_expense(expense_date: str, amount: float, category_id: int, note: str = "", tags: str = "") -> int:
    return execute(
        "INSERT INTO expenses(date, amount, category_id, note, tags) VALUES (?, ?, ?, ?, ?)",
        (expense_date, amount, category_id, note.strip() or None, tags.strip() or None),
    )


def get_category_balances() -> list[dict]:
    rows = fetchall(
        """
        SELECT
            c.id,
            c.name,
            c.parent_id,
            c.allocation_pct,
            COALESCE(SUM(a.amount), 0) AS allocated,
            COALESCE((
                SELECT SUM(e.amount)
                FROM expenses e
                WHERE e.category_id = c.id
            ), 0) AS spent
        FROM categories c
        LEFT JOIN allocations a ON a.category_id = c.id
        GROUP BY c.id
        ORDER BY c.parent_id IS NOT NULL, c.id
        """
    )

    result = []
    for row in rows:
        allocated = float(row["allocated"])
        spent = float(row["spent"])
        available = round(allocated - spent, 2)
        result.append(
            {
                "id": int(row["id"]),
                "name": row["name"],
                "parent_id": row["parent_id"],
                "allocation_pct": float(row["allocation_pct"]),
                "allocated": round(allocated, 2),
                "spent": round(spent, 2),
                "available": available,
                "overspent": available < 0,
            }
        )
    return result
