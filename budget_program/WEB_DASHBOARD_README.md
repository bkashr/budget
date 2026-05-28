# Budget Program - Web Dashboard

A personal budget app that plans your money by reserving fixed commitments off
the top, then splitting what's left across spending categories by percentage.

## Quick Start

1. Install dependencies (first time only):
   ```bash
   pip install -r requirements.txt
   ```

2. Start the web server:
   ```bash
   python run_web.py
   ```

3. Open your browser to:
   ```
   http://localhost:5000
   ```

4. Complete the 6-step setup wizard, then land on the dashboard.

> A terminal CLI (`python main.py`) also exists and shares the same database,
> but the web app is the primary interface.

## The budgeting model

Money is planned on a **monthly** basis using "reserve off the top":

```
monthly income
  − recurring subscriptions
  − planned goal savings
  = spendable   →  split across your categories by percentage
```

- **Income** can be an optional *expected* amount (e.g. $2,000 every 2 weeks),
  which paces your goals and projects the budget. If your pay is irregular
  (tips, gig work), skip it and just **log income** whenever it lands — the
  budget then works off what you've received this month.
- **Subscriptions** (Netflix, gym, phone, rent) are normalized to a monthly
  cost and reserved first.
- **Goals** (reach $10k in your HYSA, max a Roth IRA, pay off a debt by a date)
  each compute a required monthly contribution that is also reserved.
- **Categories** (groceries, eating out, gas, clothing, supplements, etc.)
  split whatever is left. Their percentages must total 100%.

## Setup wizard (6 steps)

1. **Accounts** — checking, savings, HYSA, Roth IRA, brokerage, cash
2. **Debts** — student loans, car loan, credit cards (optional)
3. **Goals** — what you're working toward (optional)
4. **Subscriptions** — recurring/consistent spending (optional)
5. **Income** — optional expected earnings + cadence
6. **Budget split** — category percentages (must total 100%)

## Dashboard

- **Summary** — total accounts, debts, and net worth
- **Monthly Budget** — income → subscriptions → goal savings → spendable, with
  per-category planned vs. actually spent this month and progress bars
- **Accounts** — click a balance to pay an expense or debt from it
- **Debts**, **Subscriptions**, **Goals**, **Recent Income**, **Recent Expenses**
- Quick actions: + Income, + Expense, + Subscription, + Goal, + Account, + Debt

## File structure

```
budget_program/
├── main.py            # Terminal CLI entry point
├── run_web.py         # Web dashboard entry point
├── web_app.py         # Flask web application + API
├── database.py        # Database helpers and schema
├── requirements.txt   # Python dependencies (Flask)
├── services/
│   ├── budget.py      # Budget engine: income, subscriptions, goal reserves, plan
│   ├── allocations.py # Expense logging + account-to-target payments
│   ├── goals.py       # Goal tracking and progress
│   └── reports.py     # Text dashboard/history (CLI)
├── templates/
│   ├── dashboard.html # Main dashboard page
│   └── setup.html     # 6-step setup wizard
└── budget.db          # SQLite database (created on first run, gitignored)
```

## Tips

- Category percentages must total exactly 100% — they split *spendable* money,
  not your whole paycheck.
- If fixed commitments exceed income, the dashboard warns you that there's
  nothing left to budget.
- All data is local SQLite (`budget.db`) — no cloud sync.

## Troubleshooting

- **Port 5000 in use?** Edit `run_web.py` and change the `port`.
- **Database locked?** Make sure only one instance is running.
