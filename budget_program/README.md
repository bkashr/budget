# Personal Budget CLI (Python 3.12 + SQLite)

A simple CLI-based personal budget program focused on logic and persistence.

## Features (MVP)
- First-run setup wizard for:
  - Accounts and balances
  - Debts and balances
  - Budget categories + allocation percentages (must total 100% for top-level categories)
- Paycheck logging with automatic allocation across top-level categories
- Expense logging by category (category balances can go negative and are flagged)
- Manual account/debt balance updates with update history
- Goals system:
  - `target_balance`
  - `contribution_cap` (e.g., Roth IRA yearly cap)
  - `debt_payoff`
  - `custom`
- Dashboard summary and history views

## Project structure

```
budget_program/
  main.py
  database.py
  services/
    allocations.py
    goals.py
    reports.py
  README.md
  budget.db  # auto-created on first run
```

## Requirements
- Python 3.12 (or Python 3.10+ should also work)
- No external dependencies (stdlib-only)

## Run
From the `budget_program` folder:

```bash
python main.py
```

On first run, it will initialize SQLite schema and launch setup automatically.

## Example workflow
1. Run `python main.py`.
2. Complete setup wizard (accounts, debts, categories summing to 100%).
3. Add paycheck: choose `add-paycheck` and enter date + net amount.
4. Add expense: choose `add-expense` and enter category + amount.
5. Add goals: choose `goals` then `Add`.
6. Check dashboard at any time for:
   - account/debt snapshots
   - category available balances
   - goal progress + per-day needed
7. Exit and rerun; data remains in `budget.db`.

## Notes
- Dates use `YYYY-MM-DD`.
- Top-level category allocation must remain valid at 100%.
- Subcategories are supported via `parent_id` and can have `0%` allocations.
