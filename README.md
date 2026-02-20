# Minimal Budget Hub

A simple single-user finance hub: accounts, debts, fixed monthly expenses, transactions, and income allocations.

## Chosen stack
**Option A: FastAPI + server-rendered HTML + Tailwind + HTMX.**

Why: it keeps Python as the core language, ships quickly, and still provides a modern, clean UX with lightweight transitions.

## Features (MVP)
- First-time onboarding wizard (Welcome → Accounts → Debts → Fixed Expenses).
- Dashboard cards: total assets, total debts, net worth, fixed monthly expenses.
- Manual transaction entry:
  - **INCOME**: stores transaction, creates allocation events, applies account/debt balance updates.
  - **EXPENSE**: stores transaction, subtracts from selected/default account.
- Allocation rules must sum to exactly 100%.
- SQLite auto-initialized on app startup.

## Run
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn budget_program.main:app --reload
```
Then open: http://127.0.0.1:8000

## Tests
```bash
pytest
```

## Project notes
- Current app code: `budget_program/`
- Previous CLI implementation was preserved under `legacy/legacy_cli_budget/`.
