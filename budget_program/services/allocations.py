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


def get_all_categories() -> list[dict]:
    rows = fetchall(
        """
        SELECT id, name, parent_id, allocation_pct
        FROM categories
        ORDER BY parent_id IS NOT NULL, id
        """
    )
    return [dict(r) for r in rows]


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
    if amount <= 0:
        raise ValueError("Expense amount must be greater than zero.")

    category = fetchone("SELECT id FROM categories WHERE id = ?", (category_id,))
    if not category:
        raise ValueError("Category not found.")

    return execute(
        "INSERT INTO expenses(date, amount, category_id, paid_amount, note, tags) VALUES (?, ?, ?, 0, ?, ?)",
        (expense_date, amount, category_id, note.strip() or None, tags.strip() or None),
    )


def update_expense(expense_id: int, category_id: int | None = None, note: str | None = None, tags: str | None = None) -> None:
    expense = fetchone("SELECT id FROM expenses WHERE id = ?", (expense_id,))
    if not expense:
        raise ValueError("Expense not found.")

    if category_id is not None:
        category = fetchone("SELECT id FROM categories WHERE id = ?", (category_id,))
        if not category:
            raise ValueError("Category not found.")
        execute("UPDATE expenses SET category_id = ? WHERE id = ?", (category_id, expense_id))

    if note is not None:
        execute("UPDATE expenses SET note = ? WHERE id = ?", (note.strip() or None, expense_id))

    if tags is not None:
        execute("UPDATE expenses SET tags = ? WHERE id = ?", (tags.strip() or None, expense_id))


def list_recent_expenses(limit: int = 20) -> list[dict]:
    rows = fetchall(
        """
        SELECT
            e.id,
            e.date,
            e.amount,
            e.paid_amount,
            e.category_id,
            c.name AS category_name,
            e.note,
            e.tags
        FROM expenses e
        LEFT JOIN categories c ON c.id = e.category_id
        ORDER BY e.date DESC, e.id DESC
        LIMIT ?
        """,
        (limit,),
    )

    result = []
    for row in rows:
        amount = float(row["amount"])
        paid_amount = float(row["paid_amount"])
        remaining = round(max(amount - paid_amount, 0.0), 2)
        result.append(
            {
                "id": int(row["id"]),
                "date": row["date"],
                "amount": round(amount, 2),
                "paid_amount": round(paid_amount, 2),
                "remaining": remaining,
                "is_paid": remaining <= 0.0,
                "category_id": int(row["category_id"]),
                "category_name": row["category_name"],
                "note": row["note"],
                "tags": row["tags"],
            }
        )

    return result


def get_pending_expenses(limit: int = 20) -> list[dict]:
    rows = fetchall(
        """
        SELECT
            e.id,
            e.date,
            e.amount,
            e.paid_amount,
            e.category_id,
            c.name AS category_name,
            e.note
        FROM expenses e
        LEFT JOIN categories c ON c.id = e.category_id
        WHERE e.amount > e.paid_amount
        ORDER BY e.date DESC, e.id DESC
        LIMIT ?
        """,
        (limit,),
    )

    pending = []
    for row in rows:
        amount = float(row["amount"])
        paid_amount = float(row["paid_amount"])
        pending.append(
            {
                "id": int(row["id"]),
                "date": row["date"],
                "category_id": int(row["category_id"]),
                "category_name": row["category_name"],
                "amount": round(amount, 2),
                "paid_amount": round(paid_amount, 2),
                "remaining": round(amount - paid_amount, 2),
                "note": row["note"],
            }
        )

    return pending


def allocate_from_account(
    account_id: int,
    target_type: str,
    target_id: int,
    amount: float,
    allocation_date: str | None = None,
    note: str = "",
) -> int:
    if amount <= 0:
        raise ValueError("Allocation amount must be greater than zero.")

    account = fetchone("SELECT id, name, balance FROM accounts WHERE id = ?", (account_id,))
    if not account:
        raise ValueError("Account not found.")

    old_account_balance = float(account["balance"])
    if amount > old_account_balance:
        raise ValueError("Insufficient account balance for this allocation.")

    target_type = (target_type or "").strip().lower()
    if target_type not in {"expense", "debt"}:
        raise ValueError("target_type must be either 'expense' or 'debt'.")

    if target_type == "expense":
        expense = fetchone("SELECT id, amount, paid_amount FROM expenses WHERE id = ?", (target_id,))
        if not expense:
            raise ValueError("Expense not found.")
        remaining = round(float(expense["amount"]) - float(expense["paid_amount"]), 2)
        if remaining <= 0:
            raise ValueError("Expense is already fully paid.")
        if amount > remaining:
            raise ValueError(f"Allocation exceeds expense remaining amount (${remaining:.2f}).")

        execute(
            "UPDATE expenses SET paid_amount = ROUND(paid_amount + ?, 2) WHERE id = ?",
            (amount, target_id),
        )
    else:
        debt = fetchone("SELECT id, balance FROM debts WHERE id = ?", (target_id,))
        if not debt:
            raise ValueError("Debt not found.")
        debt_balance = float(debt["balance"])
        if debt_balance <= 0:
            raise ValueError("Debt is already paid off.")
        if amount > debt_balance:
            raise ValueError(f"Allocation exceeds debt balance (${debt_balance:.2f}).")

        execute(
            "UPDATE debts SET balance = ROUND(balance - ?, 2) WHERE id = ?",
            (amount, target_id),
        )

    new_account_balance = round(old_account_balance - amount, 2)
    execute("UPDATE accounts SET balance = ? WHERE id = ?", (new_account_balance, account_id))

    allocation_date = allocation_date or date.today().isoformat()
    allocation_id = execute(
        """
        INSERT INTO account_allocations(date, account_id, target_type, target_id, amount, note)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (allocation_date, account_id, target_type, target_id, amount, note.strip() or None),
    )

    execute(
        """
        INSERT INTO balance_updates(date, entity_type, entity_id, old_balance, new_balance, note)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            allocation_date,
            "account",
            account_id,
            old_account_balance,
            new_account_balance,
            note.strip() or f"Allocated ${amount:.2f} to {target_type} {target_id}",
        ),
    )

    return allocation_id


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
