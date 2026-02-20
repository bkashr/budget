"""Goal CRUD and progress calculations."""

from __future__ import annotations

from datetime import date, datetime

from database import execute, fetchall, fetchone

GOAL_TYPES = ("target_balance", "contribution_cap", "debt_payoff", "custom")


def add_goal(
    goal_type: str,
    name: str,
    link_type: str | None = None,
    link_id: int | None = None,
    target_amount: float | None = None,
    target_date: str | None = None,
    year: int | None = None,
    contribution_limit: float | None = None,
    contributed_so_far: float | None = None,
    current_amount_override: float | None = None,
) -> int:
    if goal_type not in GOAL_TYPES:
        raise ValueError(f"Unsupported goal type: {goal_type}")

    start_amount = None
    if goal_type == "debt_payoff" and link_type == "debt" and link_id:
        debt = fetchone("SELECT balance FROM debts WHERE id = ?", (link_id,))
        if not debt:
            raise ValueError("Debt not found for debt_payoff goal")
        start_amount = float(debt["balance"])
        if target_amount is None:
            target_amount = 0.0

    return execute(
        """
        INSERT INTO goals(
            type, name, link_type, link_id, start_amount, target_amount, target_date,
            year, contribution_limit, contributed_so_far, current_amount_override, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            goal_type,
            name,
            link_type,
            link_id,
            start_amount,
            target_amount,
            target_date,
            year,
            contribution_limit,
            contributed_so_far,
            current_amount_override,
            date.today().isoformat(),
        ),
    )


def update_goal(goal_id: int, **kwargs) -> None:
    allowed = {
        "name",
        "link_type",
        "link_id",
        "start_amount",
        "target_amount",
        "target_date",
        "year",
        "contribution_limit",
        "contributed_so_far",
        "current_amount_override",
    }
    changes = {k: v for k, v in kwargs.items() if k in allowed}
    if not changes:
        return

    set_clause = ", ".join(f"{key} = ?" for key in changes)
    params = tuple(changes.values()) + (goal_id,)
    execute(f"UPDATE goals SET {set_clause} WHERE id = ?", params)


def delete_goal(goal_id: int) -> None:
    execute("DELETE FROM goals WHERE id = ?", (goal_id,))


def list_goals() -> list:
    return fetchall("SELECT * FROM goals ORDER BY id")


def _days_remaining(target_date: str | None) -> int | None:
    if not target_date:
        return None
    target = datetime.strptime(target_date, "%Y-%m-%d").date()
    return (target - date.today()).days


def _linked_current_amount(goal_row) -> float:
    link_type = goal_row["link_type"]
    link_id = goal_row["link_id"]

    if goal_row["type"] == "custom" and goal_row["current_amount_override"] is not None:
        return float(goal_row["current_amount_override"])

    if goal_row["type"] == "contribution_cap":
        return float(goal_row["contributed_so_far"] or 0.0)

    if link_type == "account" and link_id:
        row = fetchone("SELECT balance FROM accounts WHERE id = ?", (link_id,))
        return float(row["balance"]) if row else 0.0

    if link_type == "debt" and link_id:
        row = fetchone("SELECT balance FROM debts WHERE id = ?", (link_id,))
        return float(row["balance"]) if row else 0.0

    if link_type == "category" and link_id:
        row = fetchone(
            """
            SELECT
                COALESCE((SELECT SUM(amount) FROM allocations WHERE category_id = ?), 0) -
                COALESCE((SELECT SUM(amount) FROM expenses WHERE category_id = ?), 0) AS balance
            """,
            (link_id, link_id),
        )
        return float(row["balance"]) if row else 0.0

    return float(goal_row["current_amount_override"] or 0.0)


def get_goal_progress() -> list[dict]:
    progress_rows = []
    for goal in list_goals():
        goal_type = goal["type"]
        target_amount = float(goal["target_amount"] or 0.0)
        current_amount = _linked_current_amount(goal)
        days_remaining = _days_remaining(goal["target_date"])

        remaining = 0.0
        daily_needed = None
        progress = None

        if goal_type == "target_balance" or goal_type == "custom":
            remaining = round(target_amount - current_amount, 2)
            if days_remaining is not None and days_remaining > 0 and remaining > 0:
                daily_needed = round(remaining / days_remaining, 2)

        elif goal_type == "contribution_cap":
            limit = float(goal["contribution_limit"] or 0.0)
            remaining = round(limit - current_amount, 2)
            if days_remaining is not None and days_remaining > 0 and remaining > 0:
                daily_needed = round(remaining / days_remaining, 2)
            target_amount = limit

        elif goal_type == "debt_payoff":
            target_amount = float(goal["target_amount"] or 0.0)
            remaining = round(max(current_amount - target_amount, 0.0), 2)
            if days_remaining is not None and days_remaining > 0 and remaining > 0:
                daily_needed = round(remaining / days_remaining, 2)

            start_amount = float(goal["start_amount"] or current_amount)
            denominator = start_amount - target_amount
            if denominator > 0:
                progress = round((start_amount - current_amount) / denominator, 4)

        status = "COMPLETE" if remaining <= 0 else "ACTIVE"
        behind = False
        if status == "ACTIVE" and daily_needed is not None and days_remaining is not None:
            behind = days_remaining <= 30 and daily_needed > (target_amount * 0.02 if target_amount > 0 else 10)

        progress_rows.append(
            {
                "id": int(goal["id"]),
                "name": goal["name"],
                "type": goal_type,
                "target_amount": round(target_amount, 2),
                "target_date": goal["target_date"],
                "current_amount": round(current_amount, 2),
                "remaining": round(remaining, 2),
                "days_remaining": days_remaining,
                "daily_needed": daily_needed,
                "status": status,
                "behind": behind,
                "progress": progress,
            }
        )
    return progress_rows
