"""Text reporting helpers for dashboard and history views."""

from __future__ import annotations

from database import fetchall
from services.budget import compute_budget_plan
from services.goals import get_goal_progress


def get_dashboard_data() -> dict:
    accounts = fetchall("SELECT * FROM accounts ORDER BY type, name")
    debts = fetchall("SELECT * FROM debts ORDER BY type, name")
    plan = compute_budget_plan()
    goals = get_goal_progress()

    return {
        "accounts": accounts,
        "debts": debts,
        "plan": plan,
        "goals": goals,
    }


def print_dashboard() -> None:
    data = get_dashboard_data()
    plan = data["plan"]

    print("\n=== DASHBOARD ===")

    print("\nAccounts")
    if not data["accounts"]:
        print("  (none)")
    else:
        for a in data["accounts"]:
            print(f"  [{a['id']}] {a['name']} ({a['type']}) - ${a['balance']:.2f}")

    print("\nDebts")
    if not data["debts"]:
        print("  (none)")
    else:
        for d in data["debts"]:
            print(f"  [{d['id']}] {d['name']} ({d['type']}) - ${d['balance']:.2f}")

    print("\nMonthly Budget")
    print(f"  Income:        ${plan['monthly_income']:.2f} ({plan['income_basis']})")
    print(f"  Subscriptions: -${plan['subscriptions_total']:.2f}")
    print(f"  Goal savings:  -${plan['goals_total']:.2f}")
    print(f"  Spendable:     ${plan['spendable']:.2f}")

    print("\n  Category plan (spent / planned this month)")
    if not plan["categories"]:
        print("    (none)")
    else:
        for c in plan["categories"]:
            status = " OVERSPENT" if c["overspent"] else ""
            print(
                f"    [{c['id']}] {c['name']} ({c['allocation_pct']:.1f}%): "
                f"${c['spent']:.2f} / ${c['planned']:.2f} (left ${c['remaining']:.2f}){status}"
            )

    for warning in plan["warnings"]:
        print(f"  ! {warning}")

    print("\nGoals")
    if not data["goals"]:
        print("  (none)")
    else:
        for g in data["goals"]:
            behind_text = " BEHIND" if g["behind"] else ""
            monthly = f"${g['monthly_needed']:.2f}/mo" if g["monthly_needed"] is not None else "N/A"
            days = g["days_remaining"] if g["days_remaining"] is not None else "N/A"
            print(
                f"  [{g['id']}] {g['name']} ({g['type']}) | target=${g['target_amount']:.2f} "
                f"current=${g['current_amount']:.2f} remaining=${g['remaining']:.2f} "
                f"days={days} needed={monthly} status={g['status']}{behind_text}"
            )


def print_history(limit: int = 10) -> None:
    print("\n=== HISTORY ===")

    income = fetchall("SELECT * FROM income_entries ORDER BY date DESC, id DESC LIMIT ?", (limit,))
    expenses = fetchall("SELECT * FROM expenses ORDER BY date DESC, id DESC LIMIT ?", (limit,))
    updates = fetchall("SELECT * FROM balance_updates ORDER BY date DESC, id DESC LIMIT ?", (limit,))

    print("\nRecent Income")
    if not income:
        print("  (none)")
    else:
        for p in income:
            print(f"  [{p['id']}] {p['date']} amount=${p['amount']:.2f} source={p['source'] or '-'} note={p['note'] or '-'}")

    print("\nRecent Expenses")
    if not expenses:
        print("  (none)")
    else:
        for e in expenses:
            print(
                f"  [{e['id']}] {e['date']} category={e['category_id']} amount=${e['amount']:.2f} "
                f"note={e['note'] or '-'} tags={e['tags'] or '-'}"
            )

    print("\nRecent Balance Updates")
    if not updates:
        print("  (none)")
    else:
        for u in updates:
            print(
                f"  [{u['id']}] {u['date']} {u['entity_type']}:{u['entity_id']} "
                f"${u['old_balance']:.2f} -> ${u['new_balance']:.2f} note={u['note'] or '-'}"
            )
