"""Flask web dashboard for the budget program."""

from datetime import date

from flask import Flask, jsonify, render_template, request

from database import execute, fetchall, init_db
from services.allocations import (
    add_expense as add_expense_service,
    add_paycheck as add_paycheck_service,
    allocate_from_account,
    get_all_categories,
    get_category_balances,
    get_pending_expenses,
    list_recent_expenses,
    update_expense,
)
from services.goals import get_goal_progress

app = Flask(__name__, template_folder="templates")
app.config["JSON_SORT_KEYS"] = False

# Initialize database on startup
init_db()


@app.route("/")
def index():
    """Main dashboard page."""
    return render_template("dashboard.html")


@app.route("/api/dashboard")
def api_dashboard():
    """Get dashboard data."""
    accounts = fetchall("SELECT * FROM accounts ORDER BY type, name")
    debts = fetchall("SELECT * FROM debts ORDER BY type, name")
    categories = get_category_balances()
    all_categories = get_all_categories()
    goals = get_goal_progress()
    pending_expenses = get_pending_expenses(limit=50)
    recent_expenses = list_recent_expenses(limit=50)

    total_accounts = sum(float(a["balance"]) for a in accounts)
    total_debts = sum(float(d["balance"]) for d in debts)
    net_worth = total_accounts - total_debts

    return jsonify(
        {
            "accounts": [dict(a) for a in accounts],
            "debts": [dict(d) for d in debts],
            "categories": categories,
            "all_categories": all_categories,
            "pending_expenses": pending_expenses,
            "recent_expenses": recent_expenses,
            "goals": [dict(g) for g in goals],
            "totals": {
                "accounts": round(total_accounts, 2),
                "debts": round(total_debts, 2),
                "net_worth": round(net_worth, 2),
            },
        }
    )


@app.route("/api/accounts")
def get_accounts():
    """Get all accounts."""
    accounts = fetchall("SELECT * FROM accounts ORDER BY type, name")
    return jsonify([dict(a) for a in accounts])


@app.route("/api/accounts", methods=["POST"])
def add_account():
    """Add a new account."""
    data = request.json or {}
    account_id = execute(
        "INSERT INTO accounts(name, institution, type, balance, interest_rate, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (
            data.get("name"),
            data.get("institution"),
            data.get("type"),
            float(data.get("balance", 0)),
            float(data.get("interest_rate")) if data.get("interest_rate") else None,
            date.today().isoformat(),
        ),
    )
    return jsonify({"id": account_id}), 201


@app.route("/api/debts")
def get_debts():
    """Get all debts."""
    debts = fetchall("SELECT * FROM debts ORDER BY type, name")
    return jsonify([dict(d) for d in debts])


@app.route("/api/debts", methods=["POST"])
def add_debt():
    """Add a new debt."""
    data = request.json or {}
    debt_id = execute(
        """
        INSERT INTO debts(name, institution, type, balance, interest_rate, min_payment, due_day, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            data.get("name"),
            data.get("institution"),
            data.get("type"),
            float(data.get("balance", 0)),
            float(data.get("interest_rate")) if data.get("interest_rate") else None,
            float(data.get("min_payment")) if data.get("min_payment") else None,
            int(data.get("due_day")) if data.get("due_day") else None,
            date.today().isoformat(),
        ),
    )
    return jsonify({"id": debt_id}), 201


@app.route("/api/categories")
def get_categories():
    """Get all category balances."""
    categories = get_category_balances()
    return jsonify(categories)


@app.route("/api/categories/all")
def get_categories_all():
    """Get all categories for selectors/editing."""
    return jsonify(get_all_categories())


@app.route("/api/categories", methods=["POST"])
def add_category():
    """Add a new category."""
    data = request.json or {}
    cat_id = execute(
        "INSERT INTO categories(name, parent_id, allocation_pct, created_at) VALUES (?, ?, ?, ?)",
        (
            data.get("name"),
            data.get("parent_id"),
            float(data.get("allocation_pct", 0)),
            date.today().isoformat(),
        ),
    )
    return jsonify({"id": cat_id}), 201


@app.route("/api/paycheck", methods=["POST"])
def add_paycheck():
    """Add a paycheck and allocate to categories."""
    data = request.json or {}
    try:
        paycheck_id = add_paycheck_service(
            amount=float(data.get("amount", 0)),
            paycheck_date=data.get("date") or date.today().isoformat(),
            note=data.get("note", ""),
        )
        return jsonify({"id": paycheck_id}), 201
    except ValueError as error:
        return jsonify({"error": str(error)}), 400


@app.route("/api/expense", methods=["POST"])
def add_expense():
    """Add an expense."""
    data = request.json or {}
    try:
        expense_id = add_expense_service(
            expense_date=data.get("date") or date.today().isoformat(),
            amount=float(data.get("amount", 0)),
            category_id=int(data.get("category_id", 0)),
            note=data.get("note", ""),
            tags=data.get("tags", ""),
        )
        return jsonify({"id": expense_id}), 201
    except ValueError as error:
        return jsonify({"error": str(error)}), 400


@app.route("/api/expenses/recent")
def recent_expenses():
    """Get recent expenses with payment state."""
    limit = int(request.args.get("limit", 50))
    return jsonify(list_recent_expenses(limit=limit))


@app.route("/api/expenses/pending")
def pending_expenses():
    """Get unpaid/partially paid expenses."""
    limit = int(request.args.get("limit", 50))
    return jsonify(get_pending_expenses(limit=limit))


@app.route("/api/expenses/<int:expense_id>", methods=["PATCH"])
def patch_expense(expense_id: int):
    """Update expense metadata (category, note, tags)."""
    data = request.json or {}
    try:
        update_expense(
            expense_id=expense_id,
            category_id=int(data["category_id"]) if "category_id" in data and data["category_id"] is not None else None,
            note=data["note"] if "note" in data else None,
            tags=data["tags"] if "tags" in data else None,
        )
        return jsonify({"success": True})
    except ValueError as error:
        return jsonify({"error": str(error)}), 400


@app.route("/api/allocations/account", methods=["POST"])
def allocate_account():
    """Allocate money from an account to an unpaid expense or debt."""
    data = request.json or {}
    try:
        allocation_id = allocate_from_account(
            account_id=int(data.get("account_id", 0)),
            target_type=data.get("target_type", ""),
            target_id=int(data.get("target_id", 0)),
            amount=float(data.get("amount", 0)),
            allocation_date=data.get("date") or date.today().isoformat(),
            note=data.get("note", ""),
        )
        return jsonify({"id": allocation_id}), 201
    except ValueError as error:
        return jsonify({"error": str(error)}), 400


@app.route("/setup")
def setup():
    """Setup wizard page."""
    return render_template("setup.html")


@app.route("/api/setup/categories", methods=["POST"])
def setup_categories():
    """Set up initial categories."""
    data = request.json or {}
    execute("DELETE FROM categories")

    categories = data.get("categories", [])
    for name, pct in categories:
        execute(
            "INSERT INTO categories(name, parent_id, allocation_pct, created_at) VALUES (?, NULL, ?, ?)",
            (name, float(pct), date.today().isoformat()),
        )

    return jsonify({"success": True}), 201


if __name__ == "__main__":
    app.run(debug=True, port=5000)
