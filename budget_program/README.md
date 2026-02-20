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


## GitHub Pages + remote workflow
- This project is a CLI app, so GitHub Pages cannot run the Python program directly.
- The `docs/index.html` page is an interactive **visual prototype** for planning/editing the product UI in-browser.
- Prototype data is browser-only (localStorage) and is separate from your real Python + SQLite app data.
- For remote development without installing VS Code locally, use GitHub Codespaces.

### Recommended setup
1. In GitHub: **Settings → Pages**.
2. Under **Build and deployment**, choose **Deploy from a branch**.
3. Select your branch and the **`/docs`** folder.
4. Open the published Pages site to review/edit the visual prototype behavior.
5. Open **Code → Codespaces** and create a codespace for real app development.
6. In the codespace terminal run:

```bash
python budget_program/main.py
```

If you want the hosted site itself to have full functionality, convert this CLI to a web app (e.g., Streamlit/Flask) and deploy on a Python host such as Render or Railway.
