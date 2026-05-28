"""Flask web dashboard for the budget program."""

from datetime import date

from flask import Flask, jsonify, render_template, request

from database import execute, fetchall, init_db
from services.allocations import (
    add_expense as add_expense_service,
    allocate_from_account,
    get_all_categories,
    get_pending_expenses,
    list_recent_expenses,
    update_expense,
)
from services.budget import (
    add_income,
    add_recurring,
    compute_budget_plan,
    delete_recurring,
    get_income_profile,
    list_recent_income,
    list_recurring,
    set_income_profile,
)
from services.goals import add_goal, delete_goal, get_goal_progress

app = Flask(__name__, template_folder="templates")
app.config["JSON_SORT_KEYS"] = False

init_db()


def _to_float(value, default=None):
    if value is None or value == "":
        return default
    return float(value)


def _to_int(value, default=None):
    if value is None or value == "":
        return default
    return int(value)


@app.route("/")
def index():
    return render_template("dashboard.html")


@app.route("/setup")
def setup():
    return render_template("setup.html")


@app.route("/api/dashboard")
def api_dashboard():
    accounts = fetchall("SELECT * FROM accounts ORDER BY type, name")
    debts = fetchall("SELECT * FROM debts ORDER BY type, name")
    plan = compute_budget_plan()
    all_categories = get_all_categories()
    goals = get_goal_progress()

    total_accounts = sum(float(a["balance"]) for a in accounts)
    total_debts = sum(float(d["balance"]) for d in debts)
    net_worth = total_accounts - total_debts

    return jsonify(
        {
            "accounts": [dict(a) for a in accounts],
            "debts": [dict(d) for d in debts],
            "plan": plan,
            "all_categories": all_categories,
            "goals": [dict(g) for g in goals],
            "income_profile": get_income_profile(),
            "recent_income": list_recent_income(limit=20),
            "recent_expenses": list_recent_expenses(limit=50),
            "pending_expenses": get_pending_expenses(limit=50),
            "totals": {
                "accounts": round(total_accounts, 2),
                "debts": round(total_debts, 2),
                "net_worth": round(net_worth, 2),
            },
        }
    )


# --- Accounts & debts --------------------------------------------------------

@app.route("/api/accounts", methods=["POST"])
def add_account():
    data = request.json or {}
    account_id = execute(
        "INSERT INTO accounts(name, institution, type, balance, interest_rate, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (
            data.get("name"),
            data.get("institution") or None,
            data.get("type"),
            _to_float(data.get("balance"), 0.0),
            _to_float(data.get("interest_rate")),
            date.today().isoformat(),
        ),
    )
    return jsonify({"id": account_id}), 201


@app.route("/api/debts", methods=["POST"])
def add_debt():
    data = request.json or {}
    debt_id = execute(
        """
        INSERT INTO debts(name, institution, type, balance, interest_rate, min_payment, due_day, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            data.get("name"),
            data.get("institution") or None,
            data.get("type"),
            _to_float(data.get("balance"), 0.0),
            _to_float(data.get("interest_rate")),
            _to_float(data.get("min_payment")),
            _to_int(data.get("due_day")),
            date.today().isoformat(),
        ),
    )
    return jsonify({"id": debt_id}), 201


# --- Categories --------------------------------------------------------------

@app.route("/api/categories/all")
def get_categories_all():
    return jsonify(get_all_categories())


@app.route("/api/categories", methods=["POST"])
def add_category():
    data = request.json or {}
    cat_id = execute(
        "INSERT INTO categories(name, parent_id, allocation_pct, created_at) VALUES (?, ?, ?, ?)",
        (
            data.get("name"),
            data.get("parent_id"),
            _to_float(data.get("allocation_pct"), 0.0),
            date.today().isoformat(),
        ),
    )
    return jsonify({"id": cat_id}), 201


# --- Income ------------------------------------------------------------------

@app.route("/api/income", methods=["POST"])
def post_income():
    data = request.json or {}
    try:
        income_id = add_income(
            amount=_to_float(data.get("amount"), 0.0),
            income_date=data.get("date") or date.today().isoformat(),
            source=data.get("source", ""),
            note=data.get("note", ""),
        )
        return jsonify({"id": income_id}), 201
    except ValueError as error:
        return jsonify({"error": str(error)}), 400


@app.route("/api/income-profile", methods=["GET", "POST"])
def income_profile():
    if request.method == "GET":
        return jsonify(get_income_profile())
    data = request.json or {}
    try:
        set_income_profile(
            expected_amount=_to_float(data.get("expected_amount")),
            cadence=data.get("cadence", "biweekly"),
        )
        return jsonify({"success": True}), 201
    except ValueError as error:
        return jsonify({"error": str(error)}), 400


# --- Recurring subscriptions -------------------------------------------------

@app.route("/api/recurring", methods=["GET", "POST"])
def recurring():
    if request.method == "GET":
        return jsonify(list_recurring(active_only=True))
    data = request.json or {}
    try:
        recurring_id = add_recurring(
            name=data.get("name", ""),
            amount=_to_float(data.get("amount"), 0.0),
            cadence=data.get("cadence", "monthly"),
            category_id=_to_int(data.get("category_id")),
            due_day=_to_int(data.get("due_day")),
        )
        return jsonify({"id": recurring_id}), 201
    except ValueError as error:
        return jsonify({"error": str(error)}), 400


@app.route("/api/recurring/<int:recurring_id>", methods=["DELETE"])
def remove_recurring(recurring_id: int):
    delete_recurring(recurring_id)
    return jsonify({"success": True})


# --- Goals -------------------------------------------------------------------

@app.route("/api/goals", methods=["GET", "POST"])
def goals():
    if request.method == "GET":
        return jsonify(get_goal_progress())
    data = request.json or {}
    try:
        goal_id = add_goal(
            goal_type=data.get("type", "target_balance"),
            name=data.get("name", ""),
            link_type=data.get("link_type") or None,
            link_id=_to_int(data.get("link_id")),
            target_amount=_to_float(data.get("target_amount"), 0.0),
            target_date=data.get("target_date") or None,
            year=_to_int(data.get("year")),
            contribution_limit=_to_float(data.get("contribution_limit")),
            contributed_so_far=_to_float(data.get("contributed_so_far")),
            current_amount_override=_to_float(data.get("current_amount_override")),
        )
        return jsonify({"id": goal_id}), 201
    except ValueError as error:
        return jsonify({"error": str(error)}), 400


@app.route("/api/goals/<int:goal_id>", methods=["DELETE"])
def remove_goal(goal_id: int):
    delete_goal(goal_id)
    return jsonify({"success": True})


# --- Expenses ----------------------------------------------------------------

@app.route("/api/expense", methods=["POST"])
def add_expense():
    data = request.json or {}
    try:
        expense_id = add_expense_service(
            expense_date=data.get("date") or date.today().isoformat(),
            amount=_to_float(data.get("amount"), 0.0),
            category_id=_to_int(data.get("category_id"), 0),
            note=data.get("note", ""),
            tags=data.get("tags", ""),
        )
        return jsonify({"id": expense_id}), 201
    except ValueError as error:
        return jsonify({"error": str(error)}), 400


@app.route("/api/expenses/recent")
def recent_expenses():
    limit = int(request.args.get("limit", 50))
    return jsonify(list_recent_expenses(limit=limit))


@app.route("/api/expenses/pending")
def pending_expenses():
    limit = int(request.args.get("limit", 50))
    return jsonify(get_pending_expenses(limit=limit))


@app.route("/api/expenses/<int:expense_id>", methods=["PATCH"])
def patch_expense(expense_id: int):
    data = request.json or {}
    try:
        update_expense(
            expense_id=expense_id,
            category_id=_to_int(data["category_id"]) if "category_id" in data and data["category_id"] is not None else None,
            note=data["note"] if "note" in data else None,
            tags=data["tags"] if "tags" in data else None,
        )
        return jsonify({"success": True})
    except ValueError as error:
        return jsonify({"error": str(error)}), 400


@app.route("/api/allocations/account", methods=["POST"])
def allocate_account():
    data = request.json or {}
    try:
        allocation_id = allocate_from_account(
            account_id=_to_int(data.get("account_id"), 0),
            target_type=data.get("target_type", ""),
            target_id=_to_int(data.get("target_id"), 0),
            amount=_to_float(data.get("amount"), 0.0),
            allocation_date=data.get("date") or date.today().isoformat(),
            note=data.get("note", ""),
        )
        return jsonify({"id": allocation_id}), 201
    except ValueError as error:
        return jsonify({"error": str(error)}), 400


# --- Setup wizard (atomic) ---------------------------------------------------

SETUP_CONFIG_TABLES = ("accounts", "debts", "categories", "recurring_expenses", "goals", "income_profile")


@app.route("/api/setup", methods=["POST"])
def complete_setup():
    """Persist the whole onboarding payload in one shot.

    Goals reference accounts/debts by their position in this payload
    (``link_index``) because the rows don't have database ids until inserted.
    """
    data = request.json or {}
    try:
        categories = data.get("categories", [])
        total = sum(float(pct) for _, pct in categories)
        if categories and abs(total - 100.0) > 0.01:
            return jsonify({"error": f"Category percentages must total 100% (got {total:.1f}%)."}), 400

        today = date.today().isoformat()

        for table in SETUP_CONFIG_TABLES:
            execute(f"DELETE FROM {table}")

        account_ids: list[int] = []
        for acc in data.get("accounts", []):
            account_ids.append(
                execute(
                    "INSERT INTO accounts(name, institution, type, balance, interest_rate, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        acc.get("name"),
                        acc.get("institution") or None,
                        acc.get("type"),
                        _to_float(acc.get("balance"), 0.0),
                        _to_float(acc.get("interest_rate")),
                        today,
                    ),
                )
            )

        debt_ids: list[int] = []
        for debt in data.get("debts", []):
            debt_ids.append(
                execute(
                    """
                    INSERT INTO debts(name, institution, type, balance, interest_rate, min_payment, due_day, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        debt.get("name"),
                        debt.get("institution") or None,
                        debt.get("type"),
                        _to_float(debt.get("balance"), 0.0),
                        _to_float(debt.get("interest_rate")),
                        _to_float(debt.get("min_payment")),
                        _to_int(debt.get("due_day")),
                        today,
                    ),
                )
            )

        for name, pct in categories:
            execute(
                "INSERT INTO categories(name, parent_id, allocation_pct, created_at) VALUES (?, NULL, ?, ?)",
                (name, float(pct), today),
            )

        for goal in data.get("goals", []):
            link_type = goal.get("link_type") or None
            link_id = None
            link_index = goal.get("link_index")
            if link_type == "account" and link_index is not None and 0 <= int(link_index) < len(account_ids):
                link_id = account_ids[int(link_index)]
            elif link_type == "debt" and link_index is not None and 0 <= int(link_index) < len(debt_ids):
                link_id = debt_ids[int(link_index)]
            add_goal(
                goal_type=goal.get("type", "target_balance"),
                name=goal.get("name", ""),
                link_type=link_type,
                link_id=link_id,
                target_amount=_to_float(goal.get("target_amount"), 0.0),
                target_date=goal.get("target_date") or None,
                year=_to_int(goal.get("year")),
                contribution_limit=_to_float(goal.get("contribution_limit")),
                contributed_so_far=_to_float(goal.get("contributed_so_far")),
            )

        for sub in data.get("subscriptions", []):
            add_recurring(
                name=sub.get("name", ""),
                amount=_to_float(sub.get("amount"), 0.0),
                cadence=sub.get("cadence", "monthly"),
                category_id=None,
                due_day=_to_int(sub.get("due_day")),
            )

        income = data.get("income")
        if income and income.get("expected_amount") not in (None, ""):
            set_income_profile(
                expected_amount=_to_float(income.get("expected_amount")),
                cadence=income.get("cadence", "biweekly"),
            )

        return jsonify({"success": True}), 201
    except ValueError as error:
        return jsonify({"error": str(error)}), 400


if __name__ == "__main__":
    app.run(debug=True, port=5000)
