import tkinter as tk
from database import connect_db
from insert import AccountManager
from visualization import create_window

def main():
    # Initialize database
    connect_db()
    
    # Create account manager instance (global for access in visualization)
    account_manager = AccountManager()
    
    # Launch GUI
    create_window(account_manager)

if __name__ == "__main__":
    main()
