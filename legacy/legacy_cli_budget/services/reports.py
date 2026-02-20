"""Text reporting helpers for dashboard and history views."""

from __future__ import annotations

from database import fetchall
from services.allocations import get_category_balances
from services.goals import get_goal_progress


def get_dashboard_data() -> dict:
    accounts = fetchall("SELECT * FROM accounts ORDER BY type, name")
    debts = fetchall("SELECT * FROM debts ORDER BY type, name")
    categories = get_category_balances()
    goals = get_goal_progress()

    return {
        "accounts": accounts,
        "debts": debts,
        "categories": categories,
        "goals": goals,
    }


def print_dashboard() -> None:
    data = get_dashboard_data()

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

    print("\nCategory Balances")
    if not data["categories"]:
        print("  (none)")
    else:
        for c in data["categories"]:
            status = " ⚠️ OVERSPENT" if c["overspent"] else ""
            indent = "    " if c["parent_id"] else "  "
            pct = f" ({c['allocation_pct']:.2f}%)" if c["parent_id"] is None else ""
            print(
                f"{indent}[{c['id']}] {c['name']}{pct}: "
                f"allocated=${c['allocated']:.2f} spent=${c['spent']:.2f} available=${c['available']:.2f}{status}"
            )

    print("\nGoals")
    if not data["goals"]:
        print("  (none)")
    else:
        for g in data["goals"]:
            behind_text = " BEHIND" if g["behind"] else ""
            daily = f"${g['daily_needed']:.2f}/day" if g["daily_needed"] is not None else "N/A"
            days = g["days_remaining"] if g["days_remaining"] is not None else "N/A"
            print(
                f"  [{g['id']}] {g['name']} ({g['type']}) | target=${g['target_amount']:.2f} "
                f"current=${g['current_amount']:.2f} remaining=${g['remaining']:.2f} "
                f"days={days} daily_needed={daily} status={g['status']}{behind_text}"
            )


def print_history(limit: int = 10) -> None:
    print("\n=== HISTORY ===")

    paychecks = fetchall("SELECT * FROM paychecks ORDER BY date DESC, id DESC LIMIT ?", (limit,))
    expenses = fetchall("SELECT * FROM expenses ORDER BY date DESC, id DESC LIMIT ?", (limit,))
    updates = fetchall("SELECT * FROM balance_updates ORDER BY date DESC, id DESC LIMIT ?", (limit,))

    print("\nRecent Paychecks")
    if not paychecks:
        print("  (none)")
    else:
        for p in paychecks:
            print(f"  [{p['id']}] {p['date']} amount=${p['amount']:.2f} note={p['note'] or '-'}")

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
