import sqlite3

ACCOUNT_TYPES = ["debt", "investments", "accounts"]
ACCOUNT_SUBCATEGORIES = {
    "debt": ["student_loans", "personal_loans", "mortgages", "credit_cards", "car_loans", "	other_debts"],
    "investments": ["401k", "IRA", "brokerage_accounts", "529_plans", "HSA", "CDs"],
    "accounts": ["checking", "savings", "money_market", "other"]
}

try:
    with sqlite3.connect('budget.db') as conn:
        cursor = conn.cursor()
        cursor.execute("""CREATE TABLE IF NOT EXISTS financial_accounts (
            id INTEGER PRIMARY KEY,
            account_name TEXT,
            account_type TEXT,
            subcategory TEXT,
            current_balance REAL,
            interest_rate REAL,
            monthly_payment REAL,
            due_date TEXT,
            institution TEXT,
            notes TEXT
        )""")
        print("Connected to the database")
except sqlite3.Error as error:
    print(f"Error: {error}")