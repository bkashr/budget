"""CLI entrypoint for personal budget program."""

from __future__ import annotations

from datetime import date
from typing import Callable

from database import execute, fetchall, fetchone, has_initial_data, init_db
from services.allocations import add_expense, add_paycheck, allocation_total_is_valid
from services.goals import add_goal, delete_goal, get_goal_progress, list_goals, update_goal
from services.reports import print_dashboard, print_history

DEFAULT_CATEGORIES = [
    ("Savings & Debt", 40.0),
    ("Groceries", 20.0),
    ("Entertainment", 15.0),
    ("Clothing", 10.0),
    ("Misc", 15.0),
]


def prompt_text(message: str, default: str | None = None) -> str:
    raw = input(f"{message}{f' [{default}]' if default is not None else ''}: ").strip()
    return raw if raw else (default or "")


def prompt_float(message: str, default: float | None = None) -> float:
    while True:
        raw = prompt_text(message, str(default) if default is not None else None)
        try:
            return float(raw)
        except ValueError:
            print("Please enter a valid number.")


def prompt_int(message: str, default: int | None = None, allow_blank: bool = False) -> int | None:
    while True:
        raw = prompt_text(message, str(default) if default is not None else None)
        if allow_blank and not raw:
            return None
        try:
            return int(raw)
        except ValueError:
            print("Please enter a valid integer.")


def prompt_date(message: str, default_today: bool = True, allow_blank: bool = False) -> str | None:
    default = date.today().isoformat() if default_today else None
    while True:
        raw = prompt_text(message, default)
        if allow_blank and not raw:
            return None
        try:
            parts = raw.split("-")
            if len(parts) != 3:
                raise ValueError
            year, month, day = (int(p) for p in parts)
            return date(year, month, day).isoformat()
        except ValueError:
            print("Use YYYY-MM-DD format.")


def print_setup_dashboard() -> None:
    """Display current setup state during wizard."""
    print("\n" + "="*60)
    print("SETUP DASHBOARD - Current State")
    print("="*60)
    list_accounts()
    list_debts()
    list_categories()
    print("="*60 + "\n")


def setup_wizard() -> None:
    print("\n=== Setup Wizard ===")

    print("\nAdd accounts (leave name blank when done).")
    while True:
        print_setup_dashboard()
        name = prompt_text("Account name (blank to finish)")
        if not name:
            break
        institution = prompt_text("Institution", "")
        account_type = prompt_text("Type (checking/savings/hysa/401k/roth/brokerage/cash/etc)", "checking")
        balance = prompt_float("Current balance")
        rate_raw = prompt_text("Interest rate (optional)", "")
        rate = float(rate_raw) if rate_raw else None
        execute(
            "INSERT INTO accounts(name, institution, type, balance, interest_rate, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (name, institution or None, account_type, balance, rate, date.today().isoformat()),
        )
        print("✓ Account added")

    print("\nAdd debts (leave name blank when done).")
    while True:
        print_setup_dashboard()
        name = prompt_text("Debt name (blank to finish)")
        if not name:
            break
        institution = prompt_text("Institution/person", "")
        debt_type = prompt_text("Type (credit_card/loan/personal/medical/etc)", "personal")
        balance = prompt_float("Current balance")
        rate_raw = prompt_text("Interest rate (optional)", "")
        min_payment_raw = prompt_text("Minimum payment (optional)", "")
        due_day_raw = prompt_text("Due day 1-31 (optional)", "")
        execute(
            """
            INSERT INTO debts(name, institution, type, balance, interest_rate, min_payment, due_day, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                name,
                institution or None,
                debt_type,
                balance,
                float(rate_raw) if rate_raw else None,
                float(min_payment_raw) if min_payment_raw else None,
                int(due_day_raw) if due_day_raw else None,
                date.today().isoformat(),
            ),
        )
        print("✓ Debt added")

    set_initial_categories()


def set_initial_categories() -> None:
    print("\nCategories and allocation percentages (must total 100%).")
    print_setup_dashboard()
    use_defaults = prompt_text("Use default categories? (y/n)", "y").lower() == "y"

    execute("DELETE FROM categories")

    if use_defaults:
        cats = DEFAULT_CATEGORIES
    else:
        cats = []
        print("Enter categories (blank name to finish)")
        while True:
            name = prompt_text("Category name (blank to finish)")
            if not name:
                break
            pct = prompt_float(f"Allocation % for {name}")
            cats.append((name, pct))

    while True:
        total = sum(p for _, p in cats)
        if abs(total - 100.0) <= 0.01 and cats:
            break
        print(f"Allocation total is {total:.2f}%. Update values to total 100%.")
        updated = []
        for name, pct in cats:
            new_pct = prompt_float(f"{name} allocation %", pct)
            updated.append((name, new_pct))
        cats = updated

    for name, pct in cats:
        execute(
            "INSERT INTO categories(name, parent_id, allocation_pct, created_at) VALUES (?, NULL, ?, ?)",
            (name, pct, date.today().isoformat()),
        )
    
    print_setup_dashboard()
    print("✓ Setup complete! Starting main program...\n")

    add_sub = prompt_text("Add subcategories now? (y/n)", "n").lower() == "y"
    if add_sub:
        manage_categories(add_only_subcategories=True)


def list_accounts() -> None:
    rows = fetchall("SELECT * FROM accounts ORDER BY id")
    print("\nAccounts")
    for r in rows:
        print(f"  [{r['id']}] {r['name']} ({r['type']}) ${r['balance']:.2f}")
    if not rows:
        print("  (none)")


def list_debts() -> None:
    rows = fetchall("SELECT * FROM debts ORDER BY id")
    print("\nDebts")
    for r in rows:
        print(f"  [{r['id']}] {r['name']} ({r['type']}) ${r['balance']:.2f}")
    if not rows:
        print("  (none)")


def list_categories() -> None:
    rows = fetchall("SELECT * FROM categories ORDER BY parent_id IS NOT NULL, id")
    print("\nCategories")
    for r in rows:
        prefix = "    " if r["parent_id"] else "  "
        suffix = f" pct={r['allocation_pct']:.2f}" if r["parent_id"] is None else ""
        print(f"{prefix}[{r['id']}] {r['name']} parent={r['parent_id']}{suffix}")
    if not rows:
        print("  (none)")


def add_paycheck_cli() -> None:
    paycheck_date = prompt_date("Paycheck date")
    amount = prompt_float("Paycheck net amount")
    note = prompt_text("Note", "")
    pid = add_paycheck(amount=amount, paycheck_date=paycheck_date, note=note)
    print(f"Paycheck {pid} added and allocated.")


def add_expense_cli() -> None:
    list_categories()
    expense_date = prompt_date("Expense date")
    amount = prompt_float("Expense amount")
    category_id = prompt_int("Category ID")
    note = prompt_text("Note", "")
    tags = prompt_text("Tags (comma-separated optional)", "")
    eid = add_expense(expense_date, amount, int(category_id), note, tags)
    print(f"Expense {eid} added.")


def update_balance(entity_type: str) -> None:
    table = "accounts" if entity_type == "account" else "debts"
    if entity_type == "account":
        list_accounts()
    else:
        list_debts()

    entity_id = prompt_int(f"{entity_type.title()} ID")
    row = fetchone(f"SELECT balance, name FROM {table} WHERE id = ?", (entity_id,))
    if not row:
        print("Not found.")
        return

    old_balance = float(row["balance"])
    new_balance = prompt_float(f"New balance for {row['name']}", old_balance)
    note = prompt_text("Note", "")
    update_date = prompt_date("Update date")

    execute(f"UPDATE {table} SET balance = ? WHERE id = ?", (new_balance, entity_id))
    execute(
        """
        INSERT INTO balance_updates(date, entity_type, entity_id, old_balance, new_balance, note)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (update_date, entity_type, entity_id, old_balance, new_balance, note or None),
    )
    print("Balance updated.")


def manage_categories(add_only_subcategories: bool = False) -> None:
    while True:
        list_categories()
        valid, total = allocation_total_is_valid()
        print(f"Top-level allocation total: {total:.2f}% ({'valid' if valid else 'invalid'})")
        print("\nManage Categories: 1) Add 2) Edit 3) Delete 4) Back")
        choice = prompt_text("Choice", "4")

        if choice == "1":
            name = prompt_text("Category name")
            if not name:
                continue
            parent_id = None
            if add_only_subcategories or prompt_text("Is this a subcategory? (y/n)", "n").lower() == "y":
                parent_id = prompt_int("Parent category ID")
                pct = prompt_float("Allocation pct for subcategory (0 allowed)", 0.0)
            else:
                pct = prompt_float("Allocation pct")
            execute(
                "INSERT INTO categories(name, parent_id, allocation_pct, created_at) VALUES (?, ?, ?, ?)",
                (name, parent_id, pct, date.today().isoformat()),
            )

        elif choice == "2":
            cid = prompt_int("Category ID to edit")
            row = fetchone("SELECT * FROM categories WHERE id = ?", (cid,))
            if not row:
                print("Not found")
                continue
            new_name = prompt_text("New name", row["name"])
            new_pct = prompt_float("New allocation pct", float(row["allocation_pct"]))
            execute("UPDATE categories SET name = ?, allocation_pct = ? WHERE id = ?", (new_name, new_pct, cid))

        elif choice == "3":
            cid = prompt_int("Category ID to delete")
            execute("DELETE FROM categories WHERE parent_id = ?", (cid,))
            execute("DELETE FROM categories WHERE id = ?", (cid,))

        elif choice == "4":
            if add_only_subcategories:
                return
            valid, total = allocation_total_is_valid()
            if not valid:
                print(f"Cannot leave menu. Top-level categories must total 100%. Current {total:.2f}%")
                continue
            return


def manage_accounts() -> None:
    while True:
        list_accounts()
        print("\nManage Accounts: 1) Add 2) Edit 3) Back")
        choice = prompt_text("Choice", "3")
        if choice == "1":
            name = prompt_text("Name")
            if not name:
                continue
            institution = prompt_text("Institution", "")
            typ = prompt_text("Type", "checking")
            balance = prompt_float("Balance")
            interest = prompt_text("Interest rate (optional)", "")
            execute(
                "INSERT INTO accounts(name, institution, type, balance, interest_rate, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (name, institution or None, typ, balance, float(interest) if interest else None, date.today().isoformat()),
            )
        elif choice == "2":
            aid = prompt_int("Account ID")
            row = fetchone("SELECT * FROM accounts WHERE id = ?", (aid,))
            if not row:
                print("Not found")
                continue
            execute(
                "UPDATE accounts SET name = ?, institution = ?, type = ?, interest_rate = ? WHERE id = ?",
                (
                    prompt_text("Name", row["name"]),
                    prompt_text("Institution", row["institution"] or "") or None,
                    prompt_text("Type", row["type"]),
                    float(prompt_text("Interest rate", str(row["interest_rate"] or "")) or 0) or None,
                    aid,
                ),
            )
        elif choice == "3":
            return


def manage_debts() -> None:
    while True:
        list_debts()
        print("\nManage Debts: 1) Add 2) Edit 3) Back")
        choice = prompt_text("Choice", "3")
        if choice == "1":
            name = prompt_text("Name")
            if not name:
                continue
            execute(
                "INSERT INTO debts(name, institution, type, balance, interest_rate, min_payment, due_day, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    name,
                    prompt_text("Institution/person", "") or None,
                    prompt_text("Type", "personal"),
                    prompt_float("Balance"),
                    float(prompt_text("Interest rate", "") or 0) or None,
                    float(prompt_text("Min payment", "") or 0) or None,
                    prompt_int("Due day", allow_blank=True),
                    date.today().isoformat(),
                ),
            )
        elif choice == "2":
            did = prompt_int("Debt ID")
            row = fetchone("SELECT * FROM debts WHERE id = ?", (did,))
            if not row:
                print("Not found")
                continue
            execute(
                "UPDATE debts SET name=?, institution=?, type=?, interest_rate=?, min_payment=?, due_day=? WHERE id=?",
                (
                    prompt_text("Name", row["name"]),
                    prompt_text("Institution/person", row["institution"] or "") or None,
                    prompt_text("Type", row["type"]),
                    float(prompt_text("Interest rate", str(row["interest_rate"] or "")) or 0) or None,
                    float(prompt_text("Min payment", str(row["min_payment"] or "")) or 0) or None,
                    prompt_int("Due day", row["due_day"], allow_blank=True),
                    did,
                ),
            )
        elif choice == "3":
            return


def goals_menu() -> None:
    while True:
        print("\nGoals Menu: 1) List Progress 2) Add 3) Edit 4) Delete 5) Back")
        choice = prompt_text("Choice", "5")

        if choice == "1":
            rows = get_goal_progress()
            if not rows:
                print("No goals yet.")
            for g in rows:
                print(
                    f"[{g['id']}] {g['name']} {g['type']} status={g['status']} remaining=${g['remaining']:.2f} "
                    f"days={g['days_remaining']} daily_needed={g['daily_needed']}"
                )

        elif choice == "2":
            gtype = prompt_text("Goal type (target_balance/contribution_cap/debt_payoff/custom)")
            name = prompt_text("Goal name")
            link_type = prompt_text("Link type account/debt/category or blank", "") or None
            link_id = prompt_int("Link ID (blank if none)", allow_blank=True) if link_type else None
            target_amount = prompt_float("Target amount", 0.0)
            target_date = prompt_date("Target date (blank for none)", default_today=False, allow_blank=True)
            year = prompt_int("Year (for contribution_cap)", allow_blank=True)
            contribution_limit = prompt_float("Contribution limit (for contribution_cap)", 7000.0) if gtype == "contribution_cap" else None
            contributed_so_far = prompt_float("Contributed so far (for contribution_cap)", 0.0) if gtype == "contribution_cap" else None
            current_override = (
                prompt_float("Current amount override (for custom)", 0.0) if gtype == "custom" else None
            )
            gid = add_goal(
                goal_type=gtype,
                name=name,
                link_type=link_type,
                link_id=link_id,
                target_amount=target_amount,
                target_date=target_date,
                year=year,
                contribution_limit=contribution_limit,
                contributed_so_far=contributed_so_far,
                current_amount_override=current_override,
            )
            print(f"Goal {gid} created")

        elif choice == "3":
            raw_rows = list_goals()
            for r in raw_rows:
                print(f"[{r['id']}] {r['name']} ({r['type']})")
            gid = prompt_int("Goal ID to edit")
            row = fetchone("SELECT * FROM goals WHERE id = ?", (gid,))
            if not row:
                print("Goal not found")
                continue
            update_goal(
                gid,
                name=prompt_text("Name", row["name"]),
                target_amount=prompt_float("Target amount", float(row["target_amount"] or 0.0)),
                target_date=prompt_date("Target date", default_today=False, allow_blank=True) or row["target_date"],
                contribution_limit=(
                    prompt_float("Contribution limit", float(row["contribution_limit"] or 0.0))
                    if row["type"] == "contribution_cap"
                    else row["contribution_limit"]
                ),
                contributed_so_far=(
                    prompt_float("Contributed so far", float(row["contributed_so_far"] or 0.0))
                    if row["type"] == "contribution_cap"
                    else row["contributed_so_far"]
                ),
                current_amount_override=(
                    prompt_float("Current amount override", float(row["current_amount_override"] or 0.0))
                    if row["type"] == "custom"
                    else row["current_amount_override"]
                ),
            )
            print("Goal updated")

        elif choice == "4":
            gid = prompt_int("Goal ID to delete")
            delete_goal(gid)
            print("Goal deleted")

        elif choice == "5":
            return


def menu_loop() -> None:
    actions: dict[str, tuple[str, Callable[[], None]]] = {
        "1": ("dashboard", print_dashboard),
        "2": ("add-paycheck", add_paycheck_cli),
        "3": ("add-expense", add_expense_cli),
        "4": ("update-account-balance", lambda: update_balance("account")),
        "5": ("update-debt-balance", lambda: update_balance("debt")),
        "6": ("manage-categories", manage_categories),
        "7": ("manage-accounts", manage_accounts),
        "8": ("manage-debts", manage_debts),
        "9": ("goals", goals_menu),
        "10": ("history", lambda: print_history(prompt_int("Last N records", 10) or 10)),
    }

    while True:
        print(
            "\n=== Personal Budget CLI ===\n"
            "1) dashboard\n"
            "2) add-paycheck\n"
            "3) add-expense\n"
            "4) update-account-balance\n"
            "5) update-debt-balance\n"
            "6) manage-categories\n"
            "7) manage-accounts\n"
            "8) manage-debts\n"
            "9) goals\n"
            "10) history\n"
            "0) exit"
        )
        choice = prompt_text("Select option", "1")

        if choice == "0":
            print("Goodbye.")
            return

        action = actions.get(choice)
        if not action:
            print("Invalid option.")
            continue

        try:
            action[1]()
        except Exception as exc:  # Keep CLI resilient.
            print(f"Error: {exc}")


def main() -> None:
    init_db()
    if not has_initial_data():
        setup_wizard()
    menu_loop()


if __name__ == "__main__":
    main()
