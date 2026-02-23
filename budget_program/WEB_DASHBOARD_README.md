# Budget Program - Web Dashboard

A modern web-based personal budget management system with an interactive dashboard.

## Quick Start

### Option 1: Web Dashboard (Recommended)

1. Start the web server:
   ```powershell
   python run_web.py
   ```

2. Open your browser and go to:
   ```
   http://localhost:5000
   ```

3. Complete the setup wizard to add your accounts, debts, and budget categories

4. You'll be taken to the main dashboard where you can:
   - View your accounts and net worth
   - Track debts
   - Monitor budget categories
   - Add paychecks
   - Log expenses

### Option 2: Terminal CLI (Legacy)

If you prefer the command-line interface:

```powershell
python main.py
```

## Features

### Dashboard
- **Summary Card**: Shows total accounts, debts, and net worth
- **Accounts**: View all accounts with balances
- **Debts**: Track all debts and their balances
- **Categories**: Monitor spending by budget category with progress bars
- **Goals**: Track savings goals

### Quick Actions
- **Add Account**: Create new bank accounts
- **Add Debt**: Log credit cards, loans, etc.
- **Add Paycheck**: Income is automatically allocated to categories
- **Add Expense**: Track spending against categories

### Setup Wizard
Step-by-step setup with:
1. Bank accounts and savings accounts
2. Debts and credit cards
3. Budget categories with allocation percentages

## Database

The program uses SQLite with the database stored at:
```
budget.db
```

All data is local to your machine - no cloud sync.

## File Structure

```
budget_program/
├── main.py              # Terminal CLI entry point
├── run_web.py          # Web dashboard entry point
├── web_app.py          # Flask web application
├── database.py         # Database helpers and schema
│
├── services/
│   ├── allocations.py  # Paycheck allocation logic
│   ├── goals.py        # Goal tracking
│   └── reports.py      # Report generation
│
├── templates/
│   ├── dashboard.html  # Main dashboard page
│   └── setup.html      # Setup wizard page
│
└── budget.db          # SQLite database (created on first run)
```

## Technology Stack

- **Backend**: Python with Flask
- **Database**: SQLite
- **Frontend**: HTML5 + CSS3 + Vanilla JavaScript
- **No external dependencies for UI** (just Flask for the server)

## Tips

- Categories must total exactly 100% for paychecks to allocate properly
- Income from a paycheck is automatically split according to your category percentages
- Expenses are deducted from category balances
- You can edit categories from the terminal CLI with `option 6`

## Troubleshooting

**Port 5000 already in use?**
Edit `run_web.py` and change `port=5000` to another port like `port=8000`

**Database locked?**
Make sure you only have one instance of the program running

**Styles not loading?**
Clear your browser cache (Ctrl+Shift+Del) and refresh

## Future Enhancements

- Charts and visualizations for spending trends
- Budget vs actual comparisons
- Recurring expense templates
- Mobile-responsive design improvements
- Export to CSV/PDF
- Multi-user support
