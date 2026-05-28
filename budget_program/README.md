# Personal Budget CLI (Python 3.12 + SQLite)

A simple CLI-based personal budget program focused on logic and persistence.

## Budgeting model
Money is planned monthly by reserving fixed commitments off the top:

```
monthly income − subscriptions − planned goal savings = spendable
spendable is split across categories by percentage (must total 100%)
```

## Features
- First-run setup wizard for:
  - Accounts and balances
  - Debts and balances
  - Goals
  - Recurring subscriptions
  - Expected income (optional)
  - Budget categories + allocation percentages (must total 100%)
- Income logging (any amount, any time — no fixed cadence required)
- Expense logging by category
- Recurring subscription management (normalized to a monthly cost)
- Manual account/debt balance updates with update history
- Goals system:
  - `target_balance`
  - `contribution_cap` (e.g., Roth IRA yearly cap)
  - `debt_payoff`
  - `custom`
- Dashboard summary and history views

> A Flask web dashboard is the primary interface — see `WEB_DASHBOARD_README.md`.

## Project structure

```
budget_program/
  main.py
  database.py
  services/
    budget.py       # income, subscriptions, goal reserves, monthly plan
    allocations.py
    goals.py
    reports.py
  README.md
  budget.db  # auto-created on first run
```

## Requirements
- Python 3.10+ (developed on 3.11)
- The CLI is stdlib-only. The web dashboard needs Flask (`pip install -r requirements.txt`).

## Run
From the `budget_program` folder:

```bash
python main.py
```

On first run, it will initialize SQLite schema and launch setup automatically.

## Example workflow
1. Run `python main.py`.
2. Complete setup wizard (accounts, debts, goals, subscriptions, income, categories summing to 100%).
3. Log income: choose `add-income` and enter amount + source whenever you get paid.
4. Add expense: choose `add-expense` and enter category + amount.
5. Manage goals/subscriptions/expected income from their menu options.
6. Check dashboard at any time for:
   - account/debt snapshots and net worth
   - the monthly budget plan (income − subscriptions − goal savings = spendable, split by category)
   - goal progress + per-month needed
7. Exit and rerun; data remains in `budget.db`.

## Notes
- Dates use `YYYY-MM-DD`.
- Top-level category allocation must remain valid at 100%.
- Subcategories are supported via `parent_id` and can have `0%` allocations.
