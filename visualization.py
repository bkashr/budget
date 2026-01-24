import tkinter as tk
from tkinter import ttk, messagebox
from database import ACCOUNT_SUBCATEGORIES

# Budget allocation percentages (can be customized)
BUDGET_ALLOCATIONS = {
    "Groceries": 0.15,
    "Entertainment": 0.10,
    "Clothing": 0.05,
    "Savings": 0.20,
    "Debt/Loans": 0.20,
    "Family/Home": 0.10,
    "Transportation": 0.10,
    "Health/Medical": 0.05,
    "Insurance": 0.03,
    "Other": 0.02
}

class BudgetApp:
    def __init__(self, window, account_manager):
        self.window = window
        self.account_manager = account_manager
        self.create_widgets()
    
    def create_widgets(self):
        """Create all GUI widgets"""
        # Configure columns for responsiveness
        self.window.columnconfigure(0, weight=1)
        self.window.columnconfigure(1, weight=1)
        self.window.columnconfigure(2, weight=1)
        self.window.columnconfigure(3, weight=1)
        self.window.columnconfigure(4, weight=1)
        
        # Main title
        title_label = tk.Label(self.window, text="Budget Tracker", font=("Arial", 20, "bold"))
        title_label.grid(pady=20, row=0, column=2)
        
        # Earnings input section
        self.create_earnings_section()
        
        # Categories display section
        self.create_categories_section()
        
        # Financial overview section
        self.create_overview_section()
    
    def create_earnings_section(self):
        """Create input section for new earnings"""
        earnings_frame = tk.Frame(self.window)
        earnings_frame.grid(row=1, column=0, columnspan=5, pady=20, padx=20, sticky="ew")
        
        tk.Label(earnings_frame, text="New Earnings:", font=("Arial", 12, "bold")).pack(side=tk.LEFT, padx=5)
        
        self.earnings_var = tk.StringVar()
        earnings_entry = tk.Entry(earnings_frame, textvariable=self.earnings_var, width=15, font=("Arial", 12))
        earnings_entry.pack(side=tk.LEFT, padx=5)
        
        allocate_btn = tk.Button(earnings_frame, text="Allocate Funds", command=self.allocate_earnings, 
                                font=("Arial", 11), bg="#4CAF50", fg="white")
        allocate_btn.pack(side=tk.LEFT, padx=5)
    
    def create_categories_section(self):
        """Create budget categories display"""
        categories_label = tk.Label(self.window, text="Budget Categories", font=("Arial", 14, "bold"))
        categories_label.grid(pady=10, row=2, column=2)
        
        # Left column categories
        categories_left = [
            ("Groceries", 0.15),
            ("Entertainment", 0.10),
            ("Clothing", 0.05),
            ("Savings", 0.20),
            ("Debt/Loans", 0.20)
        ]
        
        # Right column categories
        categories_right = [
            ("Family/Home", 0.10),
            ("Transportation", 0.10),
            ("Health/Medical", 0.05),
            ("Insurance", 0.03),
            ("Other", 0.02)
        ]
        
        self.category_labels = {}
        
        for idx, (category, percentage) in enumerate(categories_left, start=3):
            label = tk.Label(self.window, text=category, font=("Arial", 12))
            label.grid(pady=10, row=idx, column=1)
            
            value_label = tk.Label(self.window, text=f"${0:.2f} ({percentage*100:.0f}%)", 
                                   font=("Arial", 11), fg="#2196F3")
            value_label.grid(pady=10, row=idx, column=2)
            self.category_labels[category] = value_label
        
        for idx, (category, percentage) in enumerate(categories_right, start=3):
            label = tk.Label(self.window, text=category, font=("Arial", 12))
            label.grid(pady=10, row=idx, column=3)
            
            value_label = tk.Label(self.window, text=f"${0:.2f} ({percentage*100:.0f}%)", 
                                   font=("Arial", 11), fg="#2196F3")
            value_label.grid(pady=10, row=idx, column=4)
            self.category_labels[category] = value_label
    
    def create_overview_section(self):
        """Create financial overview section"""
        overview_row = 9
        separator = tk.Frame(self.window, height=2, bg="gray")
        separator.grid(row=overview_row, column=0, columnspan=5, sticky="ew", pady=20)
        
        overview_label = tk.Label(self.window, text="Financial Overview", font=("Arial", 14, "bold"))
        overview_label.grid(pady=10, row=overview_row + 1, column=2)
        
        # Overview labels
        tk.Label(self.window, text="Total Savings:", font=("Arial", 11)).grid(row=overview_row + 2, column=1, sticky="e", padx=10)
        self.savings_label = tk.Label(self.window, text="$0.00", font=("Arial", 11, "bold"), fg="#4CAF50")
        self.savings_label.grid(row=overview_row + 2, column=2, sticky="w")
        
        tk.Label(self.window, text="Total Debt:", font=("Arial", 11)).grid(row=overview_row + 3, column=1, sticky="e", padx=10)
        self.debt_label = tk.Label(self.window, text="$0.00", font=("Arial", 11, "bold"), fg="#f44336")
        self.debt_label.grid(row=overview_row + 3, column=2, sticky="w")
        
        tk.Label(self.window, text="Net Worth:", font=("Arial", 11)).grid(row=overview_row + 4, column=1, sticky="e", padx=10)
        self.networth_label = tk.Label(self.window, text="$0.00", font=("Arial", 11, "bold"), fg="#FF9800")
        self.networth_label.grid(row=overview_row + 4, column=2, sticky="w")
        
        # Refresh button
        refresh_btn = tk.Button(self.window, text="Refresh Data", command=self.refresh_overview,
                               font=("Arial", 10), bg="#2196F3", fg="white")
        refresh_btn.grid(row=overview_row + 5, column=2, pady=10)
        
        # Initial refresh
        self.refresh_overview()
    
    def allocate_earnings(self):
        """Allocate new earnings across budget categories"""
        try:
            earnings = float(self.earnings_var.get())
            if earnings <= 0:
                messagebox.showerror("Error", "Earnings must be greater than 0")
                return
            
            # Calculate allocations
            allocations = {}
            for category, percentage in BUDGET_ALLOCATIONS.items():
                allocations[category] = earnings * percentage
            
            # Update display
            for category, amount in allocations.items():
                if category in self.category_labels:
                    percentage = BUDGET_ALLOCATIONS[category]
                    self.category_labels[category].config(
                        text=f"${amount:.2f} ({percentage*100:.0f}%)"
                    )
            
            messagebox.showinfo("Success", f"Earnings of ${earnings:.2f} allocated to budget categories!")
            self.earnings_var.set("")
            self.refresh_overview()
        
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number for earnings")
    
    def refresh_overview(self):
        """Refresh financial overview from database"""
        try:
            savings_total = self.account_manager.get_total_by_type("accounts")
            investments_total = self.account_manager.get_total_by_type("investments")
            debt_total = self.account_manager.get_total_by_type("debt")
            
            total_assets = savings_total + investments_total
            net_worth = total_assets - debt_total
            
            self.savings_label.config(text=f"${total_assets:.2f}")
            self.debt_label.config(text=f"${debt_total:.2f}")
            
            color = "#4CAF50" if net_worth >= 0 else "#f44336"
            self.networth_label.config(text=f"${net_worth:.2f}", fg=color)
        
        except Exception as e:
            print(f"Error refreshing overview: {e}")

def create_window(account_manager):
    """Create and launch the main window"""
    window = tk.Tk()
    window.title("Budget Tracker")
    window.geometry("1000x800")
    window.configure(bg="white")
    
    app = BudgetApp(window, account_manager)
    window.mainloop()