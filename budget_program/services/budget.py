"""Budget projection engine.

The budget is "reserve off the top": expected income minus recurring
subscriptions minus planned goal savings leaves the *spendable* amount, which is
then split across flexible categories by their allocation percentage. Everything
is normalized to a monthly basis so cadences (weekly pay, yearly subscriptions,
etc.) can be compared on equal footing.
"""

from __future__ import annotations

from datetime import date

from database import execute, fetchall, fetchone
from services.goals import get_goal_progress

# How many of each cadence occur in a month, used to normalize any recurring
# amount to a monthly figure.
MONTHLY_FACTORS = {
    "weekly": 52.0 / 12.0,
    "biweekly": 26.0 / 12.0,
    "semimonthly": 2.0,
    "monthly": 1.0,
    "quarterly": 1.0 / 3.0,
    "yearly": 1.0 / 12.0,
}

INCOME_CADENCES = ("weekly", "biweekly", "semimonthly", "monthly")
RECURRING_CADENCES = ("weekly", "biweekly", "monthly", "quarterly", "yearly")


def to_monthly(amount: float, cadence: str) -> float:
    """Convert an amount that recurs on the given cadence into a monthly amount."""
    return float(amount) * MONTHLY_FACTORS.get(cadence, 1.0)


def _current_month() -> str:
    return date.today().strftime("%Y-%m")


# --- Income profile (expected, optional) ------------------------------------

def get_income_profile() -> dict | None:
    row = fetchone("SELECT expected_amount, cadence, updated_at FROM income_profile WHERE id = 1")
    if not row or row["expected_amount"] is None:
        return None
    return {
        "expected_amount": float(row["expected_amount"]),
        "cadence": row["cadence"],
        "monthly": round(to_monthly(float(row["expected_amount"]), row["cadence"]), 2),
        "updated_at": row["updated_at"],
    }


def set_income_profile(expected_amount: float | None, cadence: str) -> None:
    if expected_amount is not None:
        if cadence not in INCOME_CADENCES:
            raise ValueError(f"Income cadence must be one of {', '.join(INCOME_CADENCES)}.")
        if float(expected_amount) < 0:
            raise ValueError("Expected income cannot be negative.")
    execute(
        """
        INSERT INTO income_profile(id, expected_amount, cadence, updated_at)
        VALUES (1, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            expected_amount = excluded.expected_amount,
            cadence = excluded.cadence,
            updated_at = excluded.updated_at
        """,
        (expected_amount, cadence, date.today().isoformat()),
    )


def expected_monthly_income() -> float | None:
    profile = get_income_profile()
    return profile["monthly"] if profile else None


# --- Actual income log (ad-hoc) ---------------------------------------------

def add_income(amount: float, income_date: str | None = None, source: str = "", note: str = "") -> int:
    if amount <= 0:
        raise ValueError("Income amount must be greater than zero.")
    income_date = income_date or date.today().isoformat()
    return execute(
        "INSERT INTO income_entries(date, amount, source, note) VALUES (?, ?, ?, ?)",
        (income_date, float(amount), source.strip() or None, note.strip() or None),
    )


def list_recent_income(limit: int = 20) -> list[dict]:
    rows = fetchall(
        "SELECT id, date, amount, source, note FROM income_entries ORDER BY date DESC, id DESC LIMIT ?",
        (limit,),
    )
    return [
        {
            "id": int(r["id"]),
            "date": r["date"],
            "amount": round(float(r["amount"]), 2),
            "source": r["source"],
            "note": r["note"],
        }
        for r in rows
    ]


def income_received_this_month() -> float:
    row = fetchone(
        "SELECT COALESCE(SUM(amount), 0) AS total FROM income_entries WHERE substr(date, 1, 7) = ?",
        (_current_month(),),
    )
    return round(float(row["total"]) if row else 0.0, 2)


# --- Recurring subscriptions -------------------------------------------------

def add_recurring(name: str, amount: float, cadence: str, category_id: int | None = None, due_day: int | None = None) -> int:
    if not name.strip():
        raise ValueError("Subscription name is required.")
    if amount <= 0:
        raise ValueError("Subscription amount must be greater than zero.")
    if cadence not in RECURRING_CADENCES:
        raise ValueError(f"Cadence must be one of {', '.join(RECURRING_CADENCES)}.")
    return execute(
        """
        INSERT INTO recurring_expenses(name, amount, cadence, category_id, due_day, active, created_at)
        VALUES (?, ?, ?, ?, ?, 1, ?)
        """,
        (name.strip(), float(amount), cadence, category_id, due_day, date.today().isoformat()),
    )


def delete_recurring(recurring_id: int) -> None:
    execute("DELETE FROM recurring_expenses WHERE id = ?", (recurring_id,))


def list_recurring(active_only: bool = True) -> list[dict]:
    query = """
        SELECT r.id, r.name, r.amount, r.cadence, r.category_id, r.due_day, r.active,
               c.name AS category_name
        FROM recurring_expenses r
        LEFT JOIN categories c ON c.id = r.category_id
    """
    if active_only:
        query += " WHERE r.active = 1"
    query += " ORDER BY r.name"
    rows = fetchall(query)
    return [
        {
            "id": int(r["id"]),
            "name": r["name"],
            "amount": round(float(r["amount"]), 2),
            "cadence": r["cadence"],
            "monthly": round(to_monthly(float(r["amount"]), r["cadence"]), 2),
            "category_id": r["category_id"],
            "category_name": r["category_name"],
            "due_day": r["due_day"],
            "active": bool(r["active"]),
        }
        for r in rows
    ]


def monthly_subscriptions_total() -> float:
    return round(sum(r["monthly"] for r in list_recurring(active_only=True)), 2)


# --- Goal savings ------------------------------------------------------------

def goal_monthly_contributions() -> list[dict]:
    """Required monthly savings for each active, deadline-bound goal."""
    contributions = []
    for goal in get_goal_progress():
        if goal["status"] != "ACTIVE":
            continue
        days = goal["days_remaining"]
        remaining = float(goal["remaining"] or 0.0)
        if remaining <= 0:
            continue
        if days is None:
            # No deadline -> contributing is discretionary, not a fixed reserve.
            monthly = 0.0
        elif days <= 0:
            monthly = remaining  # Past due: needs the whole remaining now.
        else:
            months = max(days / 30.44, 1.0)
            monthly = remaining / months
        contributions.append(
            {
                "id": goal["id"],
                "name": goal["name"],
                "type": goal["type"],
                "remaining": round(remaining, 2),
                "monthly": round(monthly, 2),
                "days_remaining": days,
            }
        )
    return contributions


def monthly_goal_savings_total() -> float:
    return round(sum(g["monthly"] for g in goal_monthly_contributions()), 2)


# --- Flexible categories -----------------------------------------------------

def _top_level_categories() -> list:
    return fetchall(
        "SELECT id, name, allocation_pct FROM categories WHERE parent_id IS NULL ORDER BY id"
    )


def _spent_this_month_by_category() -> dict[int, float]:
    rows = fetchall(
        """
        SELECT category_id, COALESCE(SUM(amount), 0) AS spent
        FROM expenses
        WHERE substr(date, 1, 7) = ?
        GROUP BY category_id
        """,
        (_current_month(),),
    )
    return {int(r["category_id"]): float(r["spent"]) for r in rows}


def allocation_total() -> float:
    row = fetchone(
        "SELECT COALESCE(SUM(allocation_pct), 0.0) AS total FROM categories WHERE parent_id IS NULL"
    )
    return round(float(row["total"]) if row else 0.0, 2)


def allocation_total_is_valid() -> tuple[bool, float]:
    total = allocation_total()
    return abs(total - 100.0) <= 0.01, total


# --- The full plan -----------------------------------------------------------

def compute_budget_plan() -> dict:
    """Build the monthly budget: income, reserves, spendable, and per-category plan."""
    expected = expected_monthly_income()
    received_mtd = income_received_this_month()

    if expected is not None:
        monthly_income = expected
        income_basis = "expected"
    else:
        monthly_income = received_mtd
        income_basis = "actual_mtd"

    subscriptions_total = monthly_subscriptions_total()
    goals_total = monthly_goal_savings_total()
    reserved = round(subscriptions_total + goals_total, 2)
    spendable = round(monthly_income - reserved, 2)
    spendable_for_split = max(spendable, 0.0)

    spent_map = _spent_this_month_by_category()
    categories = []
    for cat in _top_level_categories():
        pct = float(cat["allocation_pct"])
        planned = round(spendable_for_split * pct / 100.0, 2)
        spent = round(spent_map.get(int(cat["id"]), 0.0), 2)
        categories.append(
            {
                "id": int(cat["id"]),
                "name": cat["name"],
                "allocation_pct": round(pct, 2),
                "planned": planned,
                "spent": spent,
                "remaining": round(planned - spent, 2),
                "overspent": spent > planned,
            }
        )

    warnings = []
    if spendable < 0:
        warnings.append(
            f"Fixed commitments (${reserved:,.2f}/mo) exceed income "
            f"(${monthly_income:,.2f}/mo) by ${abs(spendable):,.2f}."
        )
    valid_alloc, alloc_total = allocation_total_is_valid()
    if categories and not valid_alloc:
        warnings.append(f"Category percentages total {alloc_total:.1f}%, not 100%.")
    if income_basis == "actual_mtd":
        warnings.append(
            "No expected income set; budget is based on money received so far this month."
        )

    return {
        "income_basis": income_basis,
        "monthly_income": round(monthly_income, 2),
        "expected_monthly_income": expected,
        "income_received_mtd": received_mtd,
        "subscriptions_total": subscriptions_total,
        "goals_total": goals_total,
        "reserved": reserved,
        "spendable": spendable,
        "categories": categories,
        "subscriptions": list_recurring(active_only=True),
        "goal_contributions": goal_monthly_contributions(),
        "warnings": warnings,
    }
