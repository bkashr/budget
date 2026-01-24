import sqlite3
from typing import List, Dict, Optional

class AccountManager:
    def __init__(self, db_name: str = 'budget.db'):
        self.db_name = db_name
    
    def insert_account(self, account_name: str, account_type: str, subcategory: str, 
                      current_balance: float, interest_rate: float = 0, 
                      monthly_payment: float = 0, due_date: str = "", 
                      institution: str = "", notes: str = "") -> bool:
        """Insert a new financial account into the database"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute("""INSERT INTO financial_accounts 
                    (account_name, account_type, subcategory, current_balance, 
                     interest_rate, monthly_payment, due_date, institution, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (account_name, account_type, subcategory, current_balance, 
                     interest_rate, monthly_payment, due_date, institution, notes))
                conn.commit()
                return True
        except sqlite3.Error as error:
            print(f"Error inserting account: {error}")
            return False
    
    def get_all_accounts(self) -> List[Dict]:
        """Retrieve all accounts from the database"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM financial_accounts")
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as error:
            print(f"Error retrieving accounts: {error}")
            return []
    
    def get_accounts_by_type(self, account_type: str) -> List[Dict]:
        """Retrieve accounts by type (debt, investments, accounts)"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM financial_accounts WHERE account_type = ?", 
                             (account_type,))
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as error:
            print(f"Error retrieving accounts by type: {error}")
            return []
    
    def get_account_by_id(self, account_id: int) -> Optional[Dict]:
        """Retrieve a specific account by ID"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM financial_accounts WHERE id = ?", (account_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except sqlite3.Error as error:
            print(f"Error retrieving account: {error}")
            return None
    
    def update_balance(self, account_id: int, new_balance: float) -> bool:
        """Update the balance of an account"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute("""UPDATE financial_accounts 
                               SET current_balance = ? WHERE id = ?""",
                             (new_balance, account_id))
                conn.commit()
                return True
        except sqlite3.Error as error:
            print(f"Error updating balance: {error}")
            return False
    
    def delete_account(self, account_id: int) -> bool:
        """Delete an account from the database"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM financial_accounts WHERE id = ?", (account_id,))
                conn.commit()
                return True
        except sqlite3.Error as error:
            print(f"Error deleting account: {error}")
            return False
    
    def get_total_by_type(self, account_type: str) -> float:
        """Calculate total balance for accounts of a specific type"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute("""SELECT SUM(current_balance) FROM financial_accounts 
                               WHERE account_type = ?""", (account_type,))
                result = cursor.fetchone()[0]
                return result if result else 0
        except sqlite3.Error as error:
            print(f"Error calculating total: {error}")
            return 0
